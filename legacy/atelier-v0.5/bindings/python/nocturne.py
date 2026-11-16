"""Nocturne cell renderer. Python 3.10+, standard library only.

Example:
    with Surface(width=80, height=24, effect=5, stars=1) as surface:
        frame = surface.render(1500, text="Hello, stars")

The library does not touch the terminal. The returned frame owns its storage.
"""
from __future__ import annotations
import ctypes as ct
from dataclasses import dataclass
import json
import os
from pathlib import Path
import struct
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / 'schema.json').read_text())
KEYS = {field['name']: field for field in SCHEMA['fields']}
DEFAULTS = {name: field['default'] for name,field in KEYS.items()}


class NativeConfig(ct.Structure):
    """ABI v1 configuration, always 448 bytes; do not alter field ordering."""
    _fields_ = [('values',ct.c_int32*64),('palette',ct.c_uint32*8),
                ('starPalette',ct.c_uint32*8),('glyphs',ct.c_uint32*32)]


class Cell(ct.Structure):
    """A terminal glyph, packed foreground/background RGB, and reserved flags."""
    _fields_ = [('glyph',ct.c_uint32),('fg',ct.c_uint32),('bg',ct.c_uint32),('flags',ct.c_uint32)]


@dataclass
class Frame:
    """An owned row-major frame. cell() checks coordinates; tobytes() is LE canonical."""
    width: int
    height: int
    cells: object

    def cell(self,x: int,y: int) -> tuple[int,int,int,int]:
        """Return (glyph, fg, bg, flags), raising IndexError outside the frame."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError((x,y))
        c=self.cells[y*self.width+x]
        return c.glyph,c.fg,c.bg,c.flags

    def tobytes(self) -> bytes:
        """Return stable little-endian cell bytes, including on big-endian hosts."""
        if sys.byteorder == 'little':
            return bytes(self.cells)
        return b''.join(struct.pack('<4I',c.glyph,c.fg,c.bg,c.flags) for c in self.cells)

    def plaintext(self) -> str:
        """Return glyphs only, joined by newlines. Does not emit ANSI sequences."""
        return '\n'.join(''.join(chr(self.cells[y*self.width+x].glyph) for x in range(self.width)) for y in range(self.height))


def parseColor(value: str | int) -> int:
    """Parse #RRGGBB or a 24-bit integer. Raise ValueError on invalid input."""
    if type(value) is int and 0 <= value <= 0xffffff:
        return value
    if isinstance(value,str) and len(value)==7 and value[0]=='#':
        try:
            return int(value[1:],16)
        except ValueError:
            pass
    raise ValueError(f'Expected #RRGGBB or a 24-bit integer: {value!r}')


def loadLibrary() -> ct.CDLL:
    """Load the locally built renderer; verify version and struct sizes.

    NOCTURNE_LIBRARY may override the path. Raises OSError with build instructions
    when missing, or RuntimeError for an ABI mismatch.
    """
    name='nocturne.dll' if os.name=='nt' else ('libnocturne.dylib' if sys.platform=='darwin' else 'libnocturne.so')
    path=Path(os.environ.get('NOCTURNE_LIBRARY', str(ROOT/'dist'/name)))
    if not path.exists():
        raise OSError(f'{path} is missing. Run: sh scripts/build.sh')
    lib=ct.CDLL(str(path))
    for name in ['nsAbiVersion','nsConfigSize','nsCellSize']:
        getattr(lib,name).argtypes=[]
        getattr(lib,name).restype=ct.c_uint32
    if (lib.nsAbiVersion(),lib.nsConfigSize(),lib.nsCellSize())!=(1,ct.sizeof(NativeConfig),ct.sizeof(Cell)):
        raise RuntimeError('Nocturne ABI mismatch')
    lib.nsDefaultConfig.argtypes=[ct.POINTER(NativeConfig)]
    lib.nsDefaultConfig.restype=None
    lib.nsValidateConfig.argtypes=[ct.POINTER(NativeConfig)]
    lib.nsValidateConfig.restype=ct.c_int32
    lib.nsRender.argtypes=[ct.POINTER(NativeConfig),ct.c_uint64,ct.POINTER(ct.c_uint32),ct.c_uint32,ct.POINTER(Cell),ct.c_uint32]
    lib.nsRender.restype=ct.c_int32
    lib.nsRowPeriod.argtypes=[ct.POINTER(NativeConfig),ct.c_uint32]
    lib.nsRowPeriod.restype=ct.c_uint64
    lib.nsRowSaturation.argtypes=[ct.POINTER(NativeConfig),ct.c_uint32]
    lib.nsRowSaturation.restype=ct.c_int32
    return lib


class Surface:
    """Own a configuration, not a clock. Concurrent mutation is not supported.

    render() allocates an independent result each time. The renderer has no hidden
    state. Construct separate Surface objects for concurrently configured clients.
    """
    def __init__(self,**configuration: int):
        self.lib=loadLibrary()
        self.config=NativeConfig()
        self.lib.nsDefaultConfig(ct.byref(self.config))
        self.configure(**configuration)

    def __enter__(self):
        return self

    def __exit__(self,*_):
        return False

    def configure(self,**changes: int) -> None:
        """Validate all changes before applying; reject unknown keys and booleans."""
        for name,value in changes.items():
            if name not in KEYS:
                raise ValueError(f'Unknown configuration key: {name}')
            field=KEYS[name]
            if type(value) is not int:
                raise TypeError(f'{name} must be an integer')
            if not field['minimum']<=value<=field['maximum']:
                raise ValueError(f'{name} must be {field["minimum"]}..{field["maximum"]}')
        for name,value in changes.items():
            self.config.values[KEYS[name]['index']]=value

    def settings(self) -> dict[str,int]:
        """Return all named integer settings."""
        return {name:self.config.values[field['index']] for name,field in KEYS.items()}

    def setPalette(self,colors: Iterable[str | int]) -> None:
        """Replace gradient stops with one to eight RGB colors; reject invalid input."""
        self._setPalette(colors,'palette','paletteCount')

    def setStarPalette(self,colors: Iterable[str | int]) -> None:
        """Replace the predefined peak star colors with one to eight RGB colors."""
        self._setPalette(colors,'starPalette','starPaletteCount')

    def _setPalette(self,colors,field,key):
        parsed=[parseColor(color) for color in colors]
        if not 1 <= len(parsed) <= 8:
            raise ValueError('A palette needs 1..8 colors')
        for i,color in enumerate(parsed):
            getattr(self.config,field)[i]=color
        self.configure(**{key:len(parsed)})

    def setGlyphs(self,glyphs: Iterable[str]) -> None:
        """Set 1..32 single-code-point custom stars. Unsafe/wide glyphs become '?'."""
        glyphs=list(glyphs)
        if not 1 <= len(glyphs) <= 32 or any(not isinstance(g,str) or len(g)!=1 for g in glyphs):
            raise ValueError('Expected 1..32 single-code-point glyphs')
        for i,glyph in enumerate(glyphs):
            self.config.glyphs[i]=ord(glyph)
        self.configure(glyphSet=4,glyphCount=len(glyphs))

    def rowPeriod(self,distance: int) -> int:
        """Return effective neighbor period in milliseconds, for distance 0..256."""
        if type(distance) is not int or not 0 <= distance <= 256:
            raise ValueError('Distance must be 0..256')
        return self.lib.nsRowPeriod(ct.byref(self.config),distance)

    def rowSaturation(self,distance: int) -> int:
        """Return effective neighbor saturation, for distance 0..256."""
        if type(distance) is not int or not 0 <= distance <= 256:
            raise ValueError('Distance must be 0..256')
        return self.lib.nsRowSaturation(ct.byref(self.config),distance)

    def render(self,motionMs: int,text: str | None=None,**dataChanges: int) -> Frame:
        """Render immediately at explicit motion time; data changes do not advance time.

        motionMs: unsigned 64-bit integer milliseconds. text: optional demonstration
        prompt/ribbon, limited to 512 code points. Values remain unsmoothed. Raises
        TypeError/ValueError for invalid inputs and RuntimeError for renderer errors.
        """
        if type(motionMs) is not int or not 0 <= motionMs < 2**64:
            raise ValueError('motionMs must be an unsigned 64-bit integer')
        if text is not None and (not isinstance(text,str) or len(text)>512):
            raise ValueError('text must be a string of at most 512 code points')
        self.configure(**dataChanges)
        settings=self.settings()
        width,height=settings['width'],settings['height']
        cells=(Cell*(width*height))()
        textBuffer=None if text is None else (ct.c_uint32*max(1,len(text)))(*[ord(ch) for ch in text])
        result=self.lib.nsRender(ct.byref(self.config),motionMs,textBuffer,0 if text is None else len(text),cells,len(cells))
        if result < 0:
            raise RuntimeError(f'Renderer error {result}')
        return Frame(width,height,cells)
