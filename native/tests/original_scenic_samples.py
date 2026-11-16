"""Original source samples, with an explicit RC2 braille-encoding expectation.

The original whole-cell output must match its retained fixture before deriving
dot coverage from the independent original renderer's eight color samples.
"""
import ctypes as C
import hashlib
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

class OriginalScenicSamples:
    def __init__(self, output):
        library=Path(output)/("original-samples.dylib" if sys.platform=="darwin" else "original-samples.so")
        subprocess.run(["cc","-std=c11","-O2","-shared","-fPIC",
                        "-I",str(ROOT.parent/"include"),str(ROOT.parent/"src/nocturne.c"),
                        "-o",str(library)],check=True,capture_output=True,text=True)
        self.original=C.CDLL(str(library))
        self.original.nsWorldRenderDetailed.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p,C.c_void_p,
                                                      C.c_uint32,C.c_void_p,C.c_void_p,C.c_uint32]
        self.original.nsWorldRenderDetailed.restype=C.c_uint32
        self.original.nsWorldRenderMesh.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p,C.c_uint32,
                                                  C.c_void_p,C.c_uint32,C.c_void_p,C.c_void_p,C.c_uint32]
        self.original.nsWorldRenderMesh.restype=C.c_int32

    def expected(self, frame, archived):
        w,h=frame["width"],frame["height"];count=w*h
        cells=(C.c_uint32*(count*4))();colors=(C.c_uint32*(count*8))();depth=(C.c_int32*(count*8))()
        config=(C.c_int32*24)(*frame["worldQ"]);detail=(C.c_int32*8)(*frame["detailQ"])
        written=self.original.nsWorldRenderDetailed(config,frame["timeMs"],detail,cells,count,colors,depth,count*8)
        if written!=count:raise AssertionError("Original renderer rejected "+frame["id"])
        return self._verified_expected(frame["worldQ"],colors,bytes(cells),archived,
                                       frame["cellsSha256"],frame["id"])

    def expected_model(self, frame, archived, records):
        config=(C.c_int32*24)(*frame["config"]);count=frame["config"][0]*frame["config"][1]
        cells=(C.c_uint32*(count*4))();colors=(C.c_uint32*(count*8))();depth=(C.c_int32*(count*8))()
        if len(records)%40:raise AssertionError("Original model records are incomplete")
        mesh=C.create_string_buffer(records)
        written=self.original.nsWorldRenderMesh(config,0,mesh,len(records)//40,
                                                 cells,count,colors,depth,count*8)
        if written!=count:raise AssertionError("Original renderer rejected "+frame["id"])
        return self._verified_expected(frame["config"],colors,bytes(cells),archived,
                                       frame["sha256"],frame["id"])

    @staticmethod
    def _verified_expected(config, colors, original, archived, archived_sha256, label):
        if hashlib.sha256(archived).hexdigest()!=archived_sha256 or original!=archived:
            raise AssertionError("Original source/immutable frame differs: "+label)
        if not config[23]:return archived
        w,h=config[:2];bg=config[19];rows=[];dots=(1,8,2,16,4,32,64,128)
        for y in range(h):
            for x in range(w):
                pixels=[colors[(y*4+k//2)*(w*2)+x*2+k%2] for k in range(8)]
                occupied=[k for k,v in enumerate(pixels) if v!=bg]
                mask=sum(dots[k] for k in occupied)
                fg=sum((sum((pixels[k]>>shift)&255 for k in occupied)//len(occupied))<<shift
                       for shift in (0,8,16)) if occupied else bg
                rows.append(struct.pack("<4I",0x2800+mask if mask else 32,fg,bg,int(bool(occupied))))
        return b"".join(rows)
