"""Nocturne Studio: pure cells, explicit time, bounded scenes, no terminal ownership.

Example: Studio(width=80,height=24).render(1200,nodes=[Node('text',2,2,30,1,text='hello')])
All public input is copied and validated. No returned frame aliases native scratch.
"""
from __future__ import annotations
import ctypes as ct
import json
from dataclasses import dataclass,field
from pathlib import Path
from typing import Iterable
from nocturne import Cell,Frame,loadLibrary,parseColor

ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/'studio.schema.json').read_text())
FIELDS={v['name']:v for v in SCHEMA['fields']}
KINDS=['text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge']
NODE_KEYS=['kind','id','x','y','width','height','state','value','fromValue','changedLo','changedHi','durationMs','fg','bg','fgOpacity','bgOpacity','style','textOffset','textLength','dataOffset','dataLength','hueStep','hueSpeed','hueBase','revealMs','reserved','hueSaturation','hueBrightness','colorAnimation','glyph','zoom','reserved2']

class StageConfig(ct.Structure):
    """ABI v2, 704 bytes. Configuration words are integer-valued; see schema units."""
    _fields_=[('values',ct.c_int32*64),('palette',ct.c_uint32*32),('starPalette',ct.c_uint32*32),('glyphs',ct.c_uint32*32),('novaGlyphs',ct.c_uint32*16)]
class NativeNode(ct.Structure):
    _fields_=[('values',ct.c_int32*32)]
class NativeImpulse(ct.Structure):
    _fields_=[('values',ct.c_int32*8)]

def integer(value,minimum,maximum,name):
    """Return an in-range integer; reject booleans, fractions, and wraparound."""
    if type(value) is not int or not minimum<=value<=maximum:raise ValueError(f'{name}: expected integer {minimum}..{maximum}, got {value!r}')
    return value

def timeWords(value):
    value=integer(value,0,2**64-1,'timeMs')
    return ct.c_int32(value&0xffffffff).value,ct.c_int32(value>>32).value

@dataclass
class Impulse:
    """A bounded event at a cell position. atMs is on the same clock as render().

    kind=0 ripple, kind=1 nova. x/y may be fractional cells and are quantized to Q8.
    Example: Impulse(12,4,atMs=1000). Events are immutable by convention.
    """
    x:float
    y:float
    strength:int=1000
    kind:int=0
    atMs:int=0
    id:int=0
    def native(self):
        x=round(self.x*256);y=round(self.y*256)
        lo,hi=timeWords(self.atMs)
        return NativeImpulse((ct.c_int32*8)(integer(x,-1048576,1048576,'x'),integer(y,-1048576,1048576,'y'),integer(self.strength,0,1000,'strength'),integer(self.kind,0,1,'kind'),lo,hi,integer(self.id,0,2147483647,'id'),0))

class Node:
    """One clipped primitive, in array/z order. id=0 is decoration; other IDs hit-test.

    Inputs: kind from KINDS; cell x/y/width/height; text, numeric data, and style
    properties. Unknown fields and non-integer numeric properties raise ValueError.
    Example: Node('progress',2,3,30,1,id=7,value=670,durationMs=400,changedMs=1000).
    """
    def __init__(self,kind:str,x:int,y:int,width:int,height:int,*,text:str='',data:Iterable[int]=(),changedMs:int=0,**options):
        if kind not in KINDS:raise ValueError(f'Unknown node kind {kind}')
        self.kind=kind;self.text=str(text);self.data=list(data)
        self.values=[0]*32
        defaults=dict(kind=KINDS.index(kind),x=x,y=y,width=width,height=height,fg=0xe2d9c9,bg=0x11100e,fgOpacity=1000,bgOpacity=0,hueStep=17,hueSpeed=24,hueSaturation=620,hueBrightness=830,zoom=1)
        defaults.update(options)
        for key,value in defaults.items():
            if key not in NODE_KEYS or key in ('textOffset','textLength','dataOffset','dataLength'):raise ValueError(f'Unknown/reserved node field {key}')
            if key in ('fg','bg'):value=parseColor(value)
            self.values[NODE_KEYS.index(key)]=integer(value,-2147483648,2147483647,key)
        self.values[9],self.values[10]=timeWords(changedMs)
        self.id=self.values[1]
    def asDict(self):
        """Return JSON-serializable semantic configuration, never native addresses."""
        out={k:v for k,v in zip(NODE_KEYS,self.values) if k not in ['kind','textOffset','textLength','dataOffset','dataLength','changedLo','changedHi','reserved','reserved2']}
        return dict(kind=self.kind,text=self.text,data=self.data,changedMs=(self.values[10]&0xffffffff)<<32|(self.values[9]&0xffffffff),**out)

def packNodes(nodes):
    nodes=list(nodes)
    if len(nodes)>512:raise ValueError('maximum 512 nodes')
    records=[];text=[];data=[]
    for node in nodes:
        if not isinstance(node,Node):raise TypeError('nodes must contain Node objects')
        v=node.values.copy();v[17]=len(text);v[18]=len(node.text);v[19]=len(data);v[20]=len(node.data)
        text.extend(map(ord,node.text));data.extend(integer(x,-1000000,1000000,'data') for x in node.data)
        records.append(NativeNode((ct.c_int32*32)(*v)))
    if len(text)>32768 or len(data)>16384:raise ValueError('scene text/data capacity exceeded')
    return (NativeNode*len(records))(*records),(ct.c_uint32*len(text))(*text),(ct.c_int32*len(data))(*data)

_LIB=None
def library():
    global _LIB
    if _LIB is not None:return _LIB
    lib=loadLibrary()
    lib.nsStageConfigSize.restype=ct.c_uint32
    if lib.nsStageConfigSize()!=ct.sizeof(StageConfig):raise RuntimeError('Studio ABI size mismatch')
    lib.nsStageDefaults.argtypes=[ct.POINTER(StageConfig)];lib.nsStageDefaults.restype=None
    lib.nsStageValidate.argtypes=[ct.POINTER(StageConfig)];lib.nsStageValidate.restype=ct.c_int32
    lib.nsStageRender.argtypes=[ct.POINTER(StageConfig),ct.c_uint64,ct.POINTER(NativeImpulse),ct.c_uint32,ct.POINTER(NativeNode),ct.c_uint32,ct.POINTER(ct.c_uint32),ct.c_uint32,ct.POINTER(ct.c_int32),ct.c_uint32,ct.POINTER(Cell),ct.c_uint32]
    lib.nsStageRender.restype=ct.c_int32
    lib.nsStageHit.argtypes=[ct.POINTER(NativeNode),ct.c_uint32,ct.POINTER(ct.c_int32),ct.c_uint32,ct.c_int32,ct.c_int32];lib.nsStageHit.restype=ct.c_int32
    lib.nsStageComposite.argtypes=[ct.POINTER(Cell),ct.c_int32,ct.c_int32,ct.POINTER(Cell),ct.c_int32,ct.c_int32,ct.c_int32,ct.c_int32,ct.c_int32,ct.c_int32];lib.nsStageComposite.restype=ct.c_int32
    lib.nsStageTween.argtypes=[ct.c_int32,ct.c_int32,ct.c_uint64,ct.c_uint32,ct.c_int32];lib.nsStageTween.restype=ct.c_int32
    _LIB=lib;return lib

class Studio:
    """Reusable, deterministic configuration. render() returns an owned Frame.

    Configure is atomic; palettes accept 1..32 #RRGGBB/int colors. Glyphs accept
    1..32 single Unicode scalars (novaGlyphs 1..16). Rendering uses the documented
    narrow single-cell profile, replacing unsupported glyphs with '?'.
    """
    def __init__(self,**configuration):
        self.lib=library();self.config=StageConfig();self.lib.nsStageDefaults(ct.byref(self.config));self.configure(**configuration)
    def get(self,key):return self.config.values[FIELDS[key]['index']]
    def configure(self,**changes):
        temp=StageConfig.from_buffer_copy(self.config)
        arrays={'palette':('paletteCount',32),'starPalette':('starColorCount',32),'glyphs':('starGlyphCount',32),'novaGlyphs':('novaGlyphCount',16)}
        for key,value in changes.items():
            if key in arrays:
                count,limit=arrays[key];items=list(value)
                if not 1<=len(items)<=limit:raise ValueError(f'{key}: 1..{limit} entries required')
                for i,v in enumerate(items):
                    if 'alette' in key:v=parseColor(v)
                    elif isinstance(v,str):
                        if len(v)!=1:raise ValueError('each glyph must be one scalar')
                        v=ord(v)
                    getattr(temp,key)[i]=integer(v,0,0x10ffff if 'lyph' in key else 0xffffff,key)
                temp.values[FIELDS[count]['index']]=len(items)
            else:
                if key not in FIELDS:raise KeyError(key)
                f=FIELDS[key]
                if key in ('baseColor','inkColor'):value=parseColor(value)
                temp.values[f['index']]=integer(value,f['minimum'],f['maximum'],key)
        error=self.lib.nsStageValidate(ct.byref(temp))
        if error:raise ValueError(f'Invalid Studio configuration: field/array {error}')
        self.config=temp
    def render(self,timeMs:int,*,events=(),nodes=()):
        """Evaluate exact time and ordered events/nodes; never advance a clock.

        Raises ValueError on malformed/bounds-exceeding inputs. Example: call again
        at the SAME time with new nodes for an immediate data-only update.
        """
        timeWords(timeMs);events=list(events)
        if len(events)>128:raise ValueError('maximum 128 impulses')
        ev=(NativeImpulse*len(events))(*(e.native() for e in events))
        ns,ts,ds=packNodes(nodes);size=self.get('width')*self.get('height');cells=(Cell*size)()
        n=self.lib.nsStageRender(ct.byref(self.config),timeMs,ev,len(ev),ns,len(ns),ts,len(ts),ds,len(ds),cells,size)
        if n<0:raise ValueError(f'Studio render rejected inputs ({n})')
        return Frame(self.get('width'),self.get('height'),cells)
    def hit(self,nodes,x:int,y:int):
        """Return (node.id,itemIndex), or None. Disabled top nodes block lower hits."""
        nodes=list(nodes);ns,ts,ds=packNodes(nodes)
        n=self.lib.nsStageHit(ns,len(ns),ds,len(ds),integer(x,-4096,4096,'x'),integer(y,-4096,4096,'y'))
        if n<0:raise ValueError('invalid hit-test input')
        return None if n==0 else (nodes[(n>>16)-1].id,(n&65535)-1)
    def composite(self,dest:Frame,src:Frame,*,x=0,y=0,fgOpacity=1000,bgOpacity=1000):
        """Source-over into dest in place. Zero/zero is identity; offsets clip.

        Foreground opacity is ink over composed background, not two glyph masks.
        src and dest must be independently owned Frames.
        """
        for frame in (src,dest):
            if not isinstance(frame,Frame):raise TypeError('expected an owned Frame')
            integer(frame.width,0,512,'frame.width');integer(frame.height,0,256,'frame.height')
            if not isinstance(frame.cells,ct.Array) or frame.cells._type_ is not Cell or len(frame.cells)!=frame.width*frame.height:
                raise ValueError('Frame dimensions must match its owned Cell array')
        sa,da=ct.addressof(src.cells),ct.addressof(dest.cells)
        if src is dest or (len(src.cells) and len(dest.cells) and sa < da+ct.sizeof(dest.cells) and da < sa+ct.sizeof(src.cells)):
            raise ValueError('source and destination must not alias')
        for name,v,lo,hi in [('x',x,-4096,4096),('y',y,-4096,4096),('fgOpacity',fgOpacity,0,1000),('bgOpacity',bgOpacity,0,1000)]:integer(v,lo,hi,name)
        n=self.lib.nsStageComposite(dest.cells,dest.width,dest.height,src.cells,src.width,src.height,x,y,fgOpacity,bgOpacity)
        if n:raise ValueError('invalid composition')

def tween(fromValue:int,toValue:int,elapsedMs:int,durationMs:int,easing:int=1):
    """Clamped scalar interpolation; easing 0 linear,1 smooth,2 sine,3 cubic-out."""
    return library().nsStageTween(integer(fromValue,-2147483648,2147483647,'from'),integer(toValue,-2147483648,2147483647,'to'),integer(elapsedMs,0,2**64-1,'elapsed'),integer(durationMs,0,2**32-1,'duration'),integer(easing,0,3,'easing'))


def fleetInkOpacity(ageMs:int,fadeMs:int,rowQ8:int,bandQ8:int,topMinimum:int=760)->int:
    """Compute pure arrival × horizon opacity in thousandths.

    ageMs/fadeMs are unsigned milliseconds, rowQ8 and bandQ8 are cells×256.
    A zero duration reveals immediately; a zero band disables the spatial fade.
    Raises ValueError outside ABI bounds. Example: fleetInkOpacity(420,420,768,1536)==880.
    """
    values=[integer(ageMs,0,2**32-1,'ageMs'),integer(fadeMs,0,2**32-1,'fadeMs'),
            integer(rowQ8,-2**31,2**31-1,'rowQ8'),integer(bandQ8,0,2**31-1,'bandQ8'),
            integer(topMinimum,0,1000,'topMinimum')]
    lib=library();lib.nsFleetInkOpacity.argtypes=[ct.c_uint32,ct.c_uint32,ct.c_int32,ct.c_int32,ct.c_int32]
    lib.nsFleetInkOpacity.restype=ct.c_int32
    return lib.nsFleetInkOpacity(*values)

def oklchColor(lightness:int,chroma:int,hueMilliDegrees:int)->int:
    """Return gamut-mapped sRGB. L/1000, C/10000, signed h/1000 degrees.

    Chroma is reduced at fixed L/h until the color is in sRGB. Invalid inputs
    raise ValueError; no wall clock, allocation ownership, or retained state.
    Example: oklchColor(700, 1200, 270000).
    """
    lightness=integer(lightness,0,1000,'lightness')
    chroma=integer(chroma,0,4000,'chroma')
    hueMilliDegrees=integer(hueMilliDegrees,-2**31,2**31-1,'hueMilliDegrees')
    lib=loadLibrary();lib.nsOklchColor.argtypes=[ct.c_int32]*3;lib.nsOklchColor.restype=ct.c_int32
    return int(lib.nsOklchColor(lightness,chroma,hueMilliDegrees))

def oklchLightness(color:int)->int:
    """Return Oklab L * 1000 of 24-bit sRGB; invalid RGB raises ValueError."""
    color=integer(color,0,0xffffff,'color');lib=loadLibrary()
    lib.nsOklchLightness.argtypes=[ct.c_uint32];lib.nsOklchLightness.restype=ct.c_int32
    return int(lib.nsOklchLightness(color))
