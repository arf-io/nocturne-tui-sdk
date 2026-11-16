"""Owned direct C-ABI binding. No Node, subprocess, terminal, device, or clock ownership."""
from __future__ import annotations
import ctypes as C
from dataclasses import dataclass
import json
import zlib
from pathlib import Path
import sys
from typing import Any
from functools import wraps
from threading import RLock

def _serialized(method):
    """ctypes releases the GIL; borrowed native views require an explicit lock."""
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return call


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    bytes: bytes
    def words(self) -> tuple[tuple[int, int, int, int], ...]:
        """Return canonical glyph/foreground/background/semantic-ID words."""
        import struct
        return tuple(struct.iter_unpack('<IIII', self.bytes))

class NativeScene:
    """A serialized native context. Frames/snapshots own their bytes.

    Args: seed is a uint32; library explicitly overrides the built native library.
    Raises: ValueError on invalid transactions; RuntimeError after close.
    Example: with NativeScene(seed=4) as scene: scene.command({'op':'input','text':'Hi'})
    """
    def __init__(self, seed: int = 2030, library: str | Path | None = None):
        if isinstance(seed,bool) or not isinstance(seed,int) or not 0 <= seed <= 0xffffffff:
            raise ValueError('seed must be uint32')
        self._lock=RLock()
        root=Path(__file__).resolve().parents[2]
        path=Path(library) if library else root/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')
        self._lib=C.CDLL(str(path))
        lib=self._lib
        for name in ('nrContextSize','nrSnapshotSize'):getattr(lib,name).restype=C.c_uint32
        lib.nrInit.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32];lib.nrInit.restype=C.c_int
        lib.nrCommand.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];lib.nrCommand.restype=C.c_int
        for name in ('nrWidth','nrHeight','nrRender'):
            fn=getattr(lib,name);fn.argtypes=[C.c_void_p];fn.restype=C.c_uint32
        lib.nrCells.argtypes=[C.c_void_p];lib.nrCells.restype=C.c_void_p
        lib.nrInspectCharacterCell.argtypes=[C.c_void_p,C.c_int32,C.c_int32,C.c_void_p,C.c_uint32];lib.nrInspectCharacterCell.restype=C.c_int
        for name in ('nrRenderMemorySize','nrRenderMemoryCapacity'):
            fn=getattr(lib,name);fn.argtypes=[C.c_void_p];fn.restype=C.c_uint64
        lib.nrSetRenderMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_uint64];lib.nrSetRenderMemory.restype=C.c_int
        self._render_memory=None;self._prompt_memory=None;self._model_memory=None;self._modal_memory=None
        self._snapshot_size_for=getattr(lib,'nrSnapshotSizeFor',None)
        if self._snapshot_size_for is not None:
            self._snapshot_size_for.argtypes=[C.c_void_p];self._snapshot_size_for.restype=C.c_uint32
        self._prompt_size=getattr(lib,'nrPromptMemorySize',None)
        if self._prompt_size is not None:
            for name in ('nrPromptMemorySize','nrPromptMemoryCapacity'):
                fn=getattr(lib,name);fn.argtypes=[C.c_void_p];fn.restype=C.c_uint64
            lib.nrSetPromptMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_uint64];lib.nrSetPromptMemory.restype=C.c_int
        self._modal_size=getattr(lib,'nrModalMemorySize',None)
        if self._modal_size is not None:
            for name in ('nrModalMemorySize','nrModalMemoryCapacity'):
                fn=getattr(lib,name);fn.argtypes=[C.c_void_p];fn.restype=C.c_uint64
            lib.nrSetModalMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_uint64];lib.nrSetModalMemory.restype=C.c_int
        self._model_size=getattr(lib,'nrModelMemorySize',None)
        if self._model_size is not None:
            for name in ('nrModelMemorySize','nrModelMemoryCapacity'):
                fn=getattr(lib,name);fn.argtypes=[C.c_void_p];fn.restype=C.c_uint64
            lib.nrSetModelMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_uint64];lib.nrSetModelMemory.restype=C.c_int
            lib.nrModelSet.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];lib.nrModelSet.restype=C.c_int
            lib.nrModelTriangleCount.argtypes=[C.c_void_p];lib.nrModelTriangleCount.restype=C.c_uint32
            lib.nrModelCopy.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];lib.nrModelCopy.restype=C.c_int
        for name in ('nrInfo','nrError'):
            fn=getattr(lib,name);fn.argtypes=[C.c_void_p];fn.restype=C.c_char_p
        self._info_page=getattr(lib,'nrInfoPage',None)
        if self._info_page is not None:
            self._info_page.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32]
            self._info_page.restype=C.c_int
        lib.nrCatalogue.restype=C.c_char_p
        lib.nrSave.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];lib.nrSave.restype=C.c_int
        lib.nrLoad.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];lib.nrLoad.restype=C.c_int
        lib.nrParticle.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32];lib.nrParticle.restype=C.c_int
        lib.nrParticleMotion.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];lib.nrParticleMotion.restype=C.c_int
        lib.nrOklch.argtypes=[C.c_int32,C.c_int32,C.c_int32];lib.nrOklch.restype=C.c_uint32
        lib.nrComposite.argtypes=[C.c_uint32]*7+[C.POINTER(C.c_uint32)];lib.nrComposite.restype=C.c_int
        lib.nrCompositeInSpace.argtypes=[C.c_uint32]*8+[C.POINTER(C.c_uint32)];lib.nrCompositeInSpace.restype=C.c_int
        lib.nrTextSample.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32]
        lib.nrTextSample.restype=C.c_int
        lib.nrTextClusterSample.argtypes=lib.nrTextSample.argtypes
        lib.nrTextClusterSample.restype=C.c_int
        lib.nrTextTrailSample.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32]
        lib.nrTextTrailSample.restype=C.c_int
        lib.nrWindowSample.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32]
        lib.nrWindowSample.restype=C.c_int
        self._capacity=int(lib.nrContextSize());self._memory=C.create_string_buffer(self._capacity+8)
        self._context=C.c_void_p((C.addressof(self._memory)+7)&~7)
        self._closed=False
        if lib.nrInit(self._context,self._capacity,seed):raise RuntimeError('Native initialization failed')
    @_serialized
    def source_stage_oklch(self,lightness:int,chroma:int,hue:int)->int:
        self._check()
        if any(type(v) is not int for v in (lightness,chroma,hue)) or not 0<=lightness<=1000 or not 0<=chroma<=4000 or not -2147483648<=hue<=2147483647:raise ValueError('Original source color domain')
        fn=self._lib.nrSourceStageOklch;fn.argtypes=[C.c_int32]*3;fn.restype=C.c_uint32
        return fn(lightness,chroma,hue)
    @_serialized
    def source_stage_tween(self,from_value:int,to_value:int,elapsed_ms:int,duration_ms:int,easing:int=1)->int:
        """Original Stage scalar interpolation; explicit clock and owned scalar."""
        self._check()
        values=[from_value,to_value,elapsed_ms,duration_ms,easing]
        bounds=[(-2147483648,2147483647)]*2+[(0,18446744073709551615),(0,4294967295),(0,3)]
        if any(isinstance(v,bool) or not isinstance(v,int) or not lo<=v<=hi for v,(lo,hi) in zip(values,bounds)):raise ValueError('Source Stage tween bounds')
        fn=self._lib.nrSourceStageTween;fn.argtypes=[C.c_int32,C.c_int32,C.c_uint64,C.c_uint32,C.c_int32];fn.restype=C.c_int32
        return int(fn(*values))
    @_serialized
    def source_stage_ink_opacity(self,age_ms:int,fade_ms:int,row_q8:int,band_q8:int,top_minimum:int)->int:
        self._check();values=[age_ms,fade_ms,row_q8,band_q8,top_minimum];bounds=[(0,4294967295)]*2+[(-2147483648,2147483647),(0,2147483647),(0,1000)]
        if any(isinstance(v,bool) or not isinstance(v,int) or not lo<=v<=hi for v,(lo,hi) in zip(values,bounds)):raise ValueError('Source Stage opacity bounds')
        fn=self._lib.nrSourceStageInkOpacity;fn.argtypes=[C.c_uint32,C.c_uint32,C.c_int32,C.c_int32,C.c_int32];fn.restype=C.c_int32
        return int(fn(*values))
    @_serialized
    def source_stage_hit(self,x:int,y:int)->dict[str,int]|None:
        self._check()
        if any(isinstance(v,bool) or not isinstance(v,int) or not -4096<=v<=4096 for v in [x,y]):raise ValueError('Source Stage hit coordinates')
        fn=self._lib.nrSourceStageHit;fn.argtypes=[C.c_void_p,C.c_int32,C.c_int32,C.POINTER(C.c_int32),C.c_uint32];fn.restype=C.c_int32
        row=(C.c_int32*2)();status=fn(self._context,x,y,row,2)
        if status<0:raise ValueError('Source Stage hit rejected')
        return {'id':int(row[0]),'item':int(row[1])} if status else None
    @_serialized
    def negotiate_shortcuts(self,actions,candidates,host):
        """Owned [action,key,modifiers,assigned] rows from host capability tables."""
        def words(rows,width,limit):
            if len(rows)>limit:raise ValueError('Shortcut table capacity')
            flat=[]
            for row in rows:
                row=[row] if width==1 else row
                if len(row)!=width or any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=0xffffffff for v in row):raise ValueError('Shortcut uint32 rows required')
                flat.extend(row)
            return (C.c_uint32*len(flat))(*flat)
        a=words(actions,1,64);c=words(candidates,3,256);h=words(host,3,256);out=(C.c_uint32*(len(actions)*4))()
        fn=self._lib.nrNegotiateShortcuts;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        n=fn(a,len(actions),c,len(candidates),h,len(host),out,len(actions))
        if n<0:raise ValueError('Invalid shortcut capabilities/preferences')
        return [list(out[i*4:i*4+4]) for i in range(n)]

    def _check(self) -> None:
        if self._closed:raise RuntimeError('NativeScene is closed')
    def _ensure_render_memory(self):
        required=self._lib.nrRenderMemorySize(self._context)
        if required>self._lib.nrRenderMemoryCapacity(self._context):
            memory=C.create_string_buffer(required+8)
            pointer=C.c_void_p((C.addressof(memory)+7)&~7)
            if self._lib.nrSetRenderMemory(self._context,pointer,required):raise RuntimeError('Viewport render memory rejected')
            self._render_memory=memory
    def _ensure_prompt_memory(self):
        if self._prompt_size is None:raise RuntimeError('Core lacks dynamic prompt storage')
        required=self._prompt_size(self._context);current=self._lib.nrPromptMemoryCapacity(self._context)
        if required<=current:raise RuntimeError('Prompt storage request made no progress')
        memory=C.create_string_buffer(required+8)
        pointer=C.c_void_p((C.addressof(memory)+7)&~7)
        if self._lib.nrSetPromptMemory(self._context,pointer,required):raise RuntimeError('Prompt storage rejected')
        self._prompt_memory=memory
    def _ensure_model_memory(self):
        if self._model_size is None:raise RuntimeError('Core lacks model storage')
        required=self._model_size(self._context);current=self._lib.nrModelMemoryCapacity(self._context)
        if required<=current:raise RuntimeError('Model storage request made no progress')
        memory=C.create_string_buffer(required+8)
        pointer=C.c_void_p((C.addressof(memory)+7)&~7)
        if self._lib.nrSetModelMemory(self._context,pointer,required):raise RuntimeError('Model storage rejected')
        self._model_memory=memory
    def _ensure_modal_memory(self):
        if self._modal_size is None:raise RuntimeError('Core lacks modal storage')
        required=self._modal_size(self._context);current=self._lib.nrModalMemoryCapacity(self._context)
        if required<=current:raise RuntimeError('Modal storage request made no progress')
        memory=C.create_string_buffer(required+8)
        pointer=C.c_void_p((C.addressof(memory)+7)&~7)
        if self._lib.nrSetModalMemory(self._context,pointer,required):raise RuntimeError('Modal storage rejected')
        self._modal_memory=memory
    @_serialized
    def set_model_records(self, data: bytes) -> None:
        """Atomically replace original visual mesh geometry using owned 40-byte records.

        Each little-endian record contains nine signed Q8 coordinates and RGB.
        This direct resource upload is separate from JSON command transactions.
        """
        self._check()
        if self._model_size is None:raise RuntimeError('Core lacks model storage')
        data=bytes(data)
        if len(data)%40 or len(data)>0xffffffff:raise ValueError('Model record length')
        storage=C.create_string_buffer(data)
        result=self._lib.nrModelSet(self._context,storage,len(data)//40)
        while result<0 and self._lib.nrError(self._context)==b'Model storage required':
            self._ensure_model_memory();result=self._lib.nrModelSet(self._context,storage,len(data)//40)
        if result:raise ValueError(self._lib.nrError(self._context).decode('utf-8','strict'))
    @_serialized
    def model_records(self) -> bytes:
        """Return an owned canonical geometry copy; never borrow the arena."""
        self._check()
        if self._model_size is None:raise RuntimeError('Core lacks model storage')
        count=self._lib.nrModelTriangleCount(self._context);storage=C.create_string_buffer(count*40)
        if self._lib.nrModelCopy(self._context,storage,count)!=count:raise RuntimeError('Model copy rejected')
        return storage.raw
    @_serialized
    def command_raw(self, text: bytes) -> int:
        """Apply bounded UTF-8 JSON. Rejection preserves authoritative state."""
        self._check()
        if len(text)>0x7fffffff:raise ValueError('Command exceeds native addressable length')
        code=self._lib.nrCommand(self._context,text,len(text))
        while code<0 and self._lib.nrError(self._context) in (b'Prompt storage required',b'Modal storage required'):
            if self._lib.nrError(self._context)==b'Modal storage required':self._ensure_modal_memory()
            else:self._ensure_prompt_memory()
            code=self._lib.nrCommand(self._context,text,len(text))
        if code<0 and self._lib.nrError(self._context)==b'Viewport render memory required':
            self._ensure_render_memory();code=self._lib.nrCommand(self._context,text,len(text))
        if code<0:raise ValueError(self._lib.nrError(self._context).decode('utf-8','strict'))
        return code
    @_serialized
    def command(self, value: dict[str, Any]) -> int:
        """Apply one transaction. Return 1 for pending bounded catch-up, else 0."""
        return self.command_raw(json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())
    @_serialized
    def advance_to(self,time_us: int,budget: int=240) -> None:
        """Catch up synchronously. Interactive hosts should yield between batches."""
        if isinstance(time_us,bool) or not isinstance(time_us,int) or time_us<0:raise ValueError('Integer microseconds required')
        while self.command({'op':'time','timeUs':time_us,'budget':budget})==1:pass
    @_serialized
    def render(self) -> Frame:
        """Pure presentation. Return owned little-endian cells."""
        self._check();self._ensure_render_memory();n=self._lib.nrRender(self._context)
        if not n:raise RuntimeError('Native rendering failed')
        return Frame(self._lib.nrWidth(self._context),self._lib.nrHeight(self._context),C.string_at(self._lib.nrCells(self._context),n*16))
    @_serialized
    def inspect_character_cell(self,x:int,y:int) -> dict[str,Any]:
        """Copy semantic metadata from the latest render; never render implicitly."""
        self._check()
        if any(isinstance(v,bool) or not isinstance(v,int) or not -2147483648<=v<=2147483647 for v in [x,y]):raise ValueError('Cell coordinates')
        out=C.create_string_buffer(408);status=self._lib.nrInspectCharacterCell(self._context,x,y,out,408)
        if status==-2:raise RuntimeError('Render required before cell inspection')
        if status:raise ValueError('Cell inspection rejected')
        raw=out.raw;names=['glyph','foreground','background','id','index']
        result={name:int.from_bytes(raw[i*4:i*4+4],'little') for i,name in enumerate(names)}
        for name,start,length in [('role',20,129),('state',149,129),('path',278,128)]:result[name]=raw[start:start+length].split(b'\0',1)[0].decode('utf-8','strict')
        return result
    @_serialized
    def info(self) -> dict[str, Any]:
        self._check();return json.loads(self._lib.nrInfo(self._context))
    @_serialized
    def info_complete(self, max_bytes: int | None = None) -> dict[str, Any]:
        """Recover complete JSON on demand; not an animation-frame polling API.

        None leaves the size to native u32 addressability and available memory.
        A positive max_bytes is an explicit caller limit.
        Holds the context lock over all 64 KiB pages; concatenates before strict
        UTF-8 decoding. Older cores lacking nrInfoPage fail explicitly. CRC32 is
        accidental consistency detection, not authentication. Legacy info is unchanged.
        """
        self._check()
        if max_bytes is not None and (isinstance(max_bytes,bool) or not isinstance(max_bytes,int) or not 1<=max_bytes<=0xffffffff):
            raise ValueError('Metadata recovery limit must be None or an integer in 1..4294967295')
        if self._info_page is None:raise RuntimeError('Native core lacks nrInfoPage')
        out=C.create_string_buffer(65536);words=(C.c_uint32*4)();data=bytearray()
        offset=0;identity=None
        while True:
            status=self._info_page(self._context,offset,out,65536,words,4)
            if status not in (0,1):raise RuntimeError('Metadata page rejected')
            total,written,next_offset,checksum=words
            if max_bytes is not None and total>max_bytes:raise ValueError('Complete metadata exceeds recovery limit')
            if total<offset or written!=min(65536,total-offset) or next_offset!=offset+written or status!=int(next_offset<total):
                raise RuntimeError('Invalid metadata page progress')
            current=(total,checksum)
            if identity is not None and identity!=current:raise RuntimeError('Metadata changed during recovery')
            identity=current;data.extend(out.raw[:written]);offset=next_offset
            if status==0:break
        if len(data)!=total or zlib.crc32(data)!=checksum:raise RuntimeError('Metadata recovery checksum mismatch')
        return json.loads(data.decode('utf-8','strict'))
    @_serialized
    def snapshot(self) -> bytes:
        self._check();n=self._snapshot_size_for(self._context) if self._snapshot_size_for else self._lib.nrSnapshotSize();b=C.create_string_buffer(n)
        if self._lib.nrSave(self._context,b,n):raise RuntimeError('Snapshot failed')
        return b.raw
    @_serialized
    def restore(self,data: bytes) -> None:
        self._check()
        data=bytes(data)
        if len(data)<24 or len(data)>0xffffffff or int.from_bytes(data[16:20],'little')!=len(data)-24:raise ValueError('Snapshot length')
        result=self._lib.nrLoad(self._context,data,len(data))
        while result<0:
            error=self._lib.nrError(self._context)
            if error==b'Prompt storage required':self._ensure_prompt_memory()
            elif error==b'Model storage required':self._ensure_model_memory()
            elif error==b'Modal storage required':self._ensure_modal_memory()
            else:break
            result=self._lib.nrLoad(self._context,data,len(data))
        if result:raise ValueError('Snapshot rejected')
    @_serialized
    def particles(self) -> list[tuple[int, ...]]:
        self._check();out=[];words=(C.c_int32*12)()
        for i in range(2048):
            if self._lib.nrParticle(self._context,i,words,12)>0:out.append(tuple(words))
        return out
    @_serialized
    def surface_foam(self, ident: int) -> list[list[float]]:
        self._check()
        if not isinstance(ident,int) or not 1<=ident<=16:raise ValueError('Surface id')
        fn=self._lib.nrSurfaceFoam;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*(256*5))();count=fn(self._context,ident,out,256)
        if count<0:raise ValueError('Invalid surface foam query')
        return [list(out[i*5:i*5+5]) for i in range(count)]

    @_serialized
    def hull_immersion(self, vertices, faces, height: float) -> list[float]:
        self._check()
        if not 4<=len(vertices)<=128 or not 4<=len(faces)<=256:raise ValueError('Hull size')
        if any(len(row)!=3 for row in vertices) or any(len(row)!=3 for row in faces):raise ValueError('Hull rows require three entries')
        if any(type(x) is not int or not 0<=x<len(vertices) for row in faces for x in row):raise ValueError('Hull index')
        v=(C.c_double*(3*len(vertices)))(*(x for row in vertices for x in row))
        f=(C.c_uint32*(3*len(faces)))(*(x for row in faces for x in row));out=(C.c_double*5)()
        fn=self._lib.nrHullImmersion;fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.c_double,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        if fn(v,len(vertices),f,len(faces),height,out,5)!=1:raise ValueError('Invalid convex hull')
        return list(out)

    @_serialized
    def surface_fluid_angular(self,ident:int) -> list[float] | None:
        self._check()
        if type(ident) is not int or not 1<=ident<=16:raise ValueError('Surface id')
        fn=self._lib.nrSurfaceFluidAngular;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*12)();result=fn(self._context,ident,out,12)
        if result<0:raise ValueError('Invalid angular fluid query')
        return list(out) if result else None

    @_serialized
    def angular_drag_exchange(self,body_inertia,water_inertia,conductance,seconds,body_omega,water_omega) -> list[float]:
        """Owned diagonal exchange in an explicit shared principal frame."""
        self._check();rows=(body_inertia,water_inertia,conductance,body_omega,water_omega)
        if any(len(row)!=3 for row in rows):raise ValueError('Angular exchange rows require three entries')
        vectors=[(C.c_double*3)(*row) for row in rows];out=(C.c_double*10)()
        fn=self._lib.nrAngularDragExchange;fn.argtypes=[C.POINTER(C.c_double)]*3+[C.c_double]+[C.POINTER(C.c_double)]*3+[C.c_uint32];fn.restype=C.c_int
        if fn(*vectors[:3],seconds,*vectors[3:],out,10)!=1:raise ValueError('Invalid finite-inertia angular exchange')
        return list(out)

    @_serialized
    def fluid_drag_exchange(self,body_mass,water_mass,conductance,seconds,body_velocity,water_velocity) -> list[float]:
        """Owned final velocities, water impulse XYZ and dissipated energy."""
        self._check()
        if len(body_velocity)!=3 or len(water_velocity)!=3:raise ValueError('Velocity rows require three entries')
        body=(C.c_double*3)(*body_velocity);water=(C.c_double*3)(*water_velocity);out=(C.c_double*10)()
        fn=self._lib.nrFluidDragExchange;fn.argtypes=[C.c_double]*4+[C.POINTER(C.c_double)]*3+[C.c_uint32];fn.restype=C.c_int
        if fn(body_mass,water_mass,conductance,seconds,body,water,out,10)!=1:raise ValueError('Invalid finite-mass drag parameters')
        return list(out)

    @_serialized
    def hull_immersion_plane(self,vertices,faces,point,normal) -> list[float]:
        """Owned volume/centroid row for an explicit oriented water half-space."""
        return self._hull_plane_query(vertices,faces,point,normal)

    @_serialized
    def hull_buoyancy_plane(self,vertices,faces,point,normal,*,density,gravity,mass,center_of_mass) -> list[float]:
        """Owned immersion, net force and torque; native lift remains vertical."""
        return self._hull_plane_query(vertices,faces,point,normal,(density,gravity,mass,center_of_mass))

    def _hull_plane_query(self,vertices,faces,point,normal,wrench=None):
        self._check()
        if not 4<=len(vertices)<=128 or not 4<=len(faces)<=256:raise ValueError('Hull size')
        if any(len(row)!=3 for row in vertices) or any(len(row)!=3 for row in faces) or len(point)!=3 or len(normal)!=3:raise ValueError('Hull and plane rows require three entries')
        if any(type(index) is not int or not 0<=index<len(vertices) for row in faces for index in row):raise ValueError('Hull index')
        v=(C.c_double*(3*len(vertices)))(*(value for row in vertices for value in row));f=(C.c_uint32*(3*len(faces)))(*(index for row in faces for index in row))
        p=(C.c_double*3)(*point);n=(C.c_double*3)(*normal);pointer=C.POINTER(C.c_double)
        signature=[pointer,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,pointer,pointer]
        args=[v,len(vertices),f,len(faces),p,n];words=5
        if wrench is not None:
            density,gravity,mass,center=wrench
            if len(center)!=3:raise ValueError('Center of mass requires three entries')
            center=(C.c_double*3)(*center);signature.extend([C.c_double,C.c_double,C.c_double,pointer]);args.extend([density,gravity,mass,center]);words=11
        out=(C.c_double*words)();fn=getattr(self._lib,'nrHullBuoyancyPlane' if wrench is not None else 'nrHullImmersionPlane')
        fn.argtypes=signature+[pointer,C.c_uint32];fn.restype=C.c_int
        if fn(*args,out,words)!=1:raise ValueError('Invalid convex hull or plane parameters')
        return list(out)

    @_serialized
    def hull_mesh_immersion(self, vertices, faces, water) -> list[float]:
        self._check()
        if not 4<=len(vertices)<=128 or not 4<=len(faces)<=256 or not 1<=len(water)<=256:raise ValueError('Hull/surface size')
        if any(len(row)!=3 for row in vertices) or any(len(row)!=3 for row in faces) or any(len(row)!=9 for row in water):raise ValueError('Hull/surface row size')
        if any(type(x) is not int or not 0<=x<len(vertices) for row in faces for x in row):raise ValueError('Hull index')
        v=(C.c_double*(3*len(vertices)))(*(x for row in vertices for x in row));f=(C.c_uint32*(3*len(faces)))(*(x for row in faces for x in row));w=(C.c_double*(9*len(water)))(*(x for row in water for x in row));out=(C.c_double*5)()
        fn=self._lib.nrHullMeshImmersion;fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        if fn(v,len(vertices),f,len(faces),w,len(water),out,5)!=1:raise ValueError('Invalid hull/surface mesh')
        return list(out)

    @_serialized
    def prompt_layout(self) -> list[list[float]]:
        self._check();fn=self._lib.nrPromptLayout;fn.argtypes=[C.c_void_p,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        n=fn(self._context,None,0)
        if n<0:raise ValueError("Invalid prompt layout")
        if not n:return []
        out=(C.c_double*(8*n))()
        if fn(self._context,out,n)!=n:raise ValueError("Invalid prompt layout")
        return [list(out[i*8:i*8+8]) for i in range(n)]

    @_serialized
    def prompt_visual_layout(self) -> list[list[float]]:
        self._check();fn=self._lib.nrPromptVisualLayout;fn.argtypes=[C.c_void_p,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        n=fn(self._context,None,0)
        if n<0:raise ValueError("Invalid prompt layout")
        if not n:return []
        out=(C.c_double*(10*n))()
        if fn(self._context,out,n)!=n:raise ValueError("Invalid prompt layout")
        return [list(out[i*10:i*10+10]) for i in range(n)]

    @_serialized
    def area_geometry(self, ident: int) -> list[float] | None:
        self._check()
        if type(ident) is not int or not 1<=ident<=65535:raise ValueError('Area id')
        fn=self._lib.nrAreaGeometry;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*12)();result=fn(self._context,ident,out,12)
        if result<0:raise ValueError('Invalid area geometry')
        return list(out) if result else None

    @_serialized
    def field_sample(self, ident: int, x: float, y: float) -> list[float] | None:
        self._check()
        if type(ident) is not int or not 1<=ident<0xffffffff:raise ValueError('Field id')
        fn=self._lib.nrFieldSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_double,C.c_double,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*4)();result=fn(self._context,ident,x,y,out,4)
        if result<0:raise ValueError('Invalid field sample')
        return list(out) if result else None

    @_serialized
    def water_sample(self, triangle_index: int) -> list[float] | None:
        self._check()
        if type(triangle_index) is not int or not 0<=triangle_index<256:raise ValueError('Triangle index')
        fn=self._lib.nrWaterSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*8)();result=fn(self._context,triangle_index,out,8)
        if result<0:raise ValueError('Invalid water sample')
        return list(out) if result else None

    @_serialized
    def thermal_sample(self, triangle_index: int) -> list[float] | None:
        self._check()
        if type(triangle_index) is not int or not 0<=triangle_index<256:raise ValueError('Triangle index')
        fn=self._lib.nrThermalSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*10)();result=fn(self._context,triangle_index,out,10)
        if result<0:raise ValueError('Invalid thermal sample')
        return list(out) if result else None

    @_serialized
    def surface_foam_transport(self, ident: int) -> list[list[float]]:
        self._check()
        if not isinstance(ident,int) or not 1<=ident<=16:raise ValueError('Surface id')
        fn=self._lib.nrSurfaceFoamTransport;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*(256*7))();count=fn(self._context,ident,out,256)
        if count<0:raise ValueError('Invalid surface foam query')
        return [list(out[i*7:i*7+7]) for i in range(count)]

    @_serialized
    def flow_thickness(self, ident: int) -> list[float] | None:
        self._check()
        if not isinstance(ident,int) or not 1<=ident<=16:raise ValueError('Surface id')
        fn=self._lib.nrFlowThickness;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*6)();result=fn(self._context,ident,out,6)
        if result<0:raise ValueError('Invalid flow thickness query')
        return list(out) if result else None
    @_serialized
    def surface_triangles(self, ident: int) -> list[list[float]]:
        self._check()
        if not isinstance(ident,int) or not 1<=ident<=16:raise ValueError('Surface id')
        fn=self._lib.nrSurfaceTriangles;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*(256*12))();count=fn(self._context,ident,out,256)
        if count<0:raise ValueError('Invalid surface geometry query')
        return [list(out[i*12:i*12+12]) for i in range(count)]

    @_serialized
    def surface_fluid(self, ident: int) -> list[float] | None:
        self._check()
        if type(ident) is not int or not 1<=ident<=16:raise ValueError('Surface id')
        fn=self._lib.nrSurfaceFluid;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*15)();result=fn(self._context,ident,out,15)
        if result<0:raise ValueError('Invalid finite water query')
        return list(out) if result else None

    @_serialized
    def float_hull(self, ident: int) -> list[float] | None:
        self._check()
        if type(ident) is not int or not 1<=ident<=65535:raise ValueError('Float body id')
        fn=self._lib.nrFloatHull;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*14)();result=fn(self._context,ident,out,14)
        if result<0:raise ValueError('Invalid hull query')
        return list(out) if result else None

    @_serialized
    def float_body(self, ident: int) -> list[float] | None:
        self._check()
        if not isinstance(ident,int) or not 1<=ident<=65535:raise ValueError('Float body id')
        fn=self._lib.nrFloatBody;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*12)();result=fn(self._context,ident,out,12)
        if result<0:raise ValueError('Invalid float body query')
        return list(out) if result else None

    @_serialized
    def surface_wave_sample(self, surface_id: int, x: float, z: float) -> list[float]:
        self._check()
        if not isinstance(surface_id,int) or not 1<=surface_id<=16:raise ValueError('Surface id')
        fn=self._lib.nrSurfaceWaveSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_double,C.c_double,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        out=(C.c_double*6)()
        if fn(self._context,surface_id,x,z,out,6)!=1:raise ValueError('Invalid or missing surface wave field')
        return list(out)

    @_serialized
    def path_sample(self, points, distance: float, *, closed=False, mode='clamp') -> list[float]:
        self._check()
        if not isinstance(closed,bool) or mode not in ('clamp','loop','reverse') or not 2<=len(points)<=129 or any(len(row)!=3 for row in points):raise ValueError('Invalid path shape or mode')
        source=(C.c_double*(len(points)*3))(*[float(v) for row in points for v in row]);out=(C.c_double*8)()
        fn=self._lib.nrPathSample;fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.c_int,C.c_int,C.c_double,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        if fn(source,len(points),int(closed),('clamp','loop','reverse').index(mode),distance,out,8)!=1:raise ValueError('Invalid path parameters')
        return list(out)

    @_serialized
    def wave_sample(self, waves, x: float, z: float, seconds: float) -> list[float]:
        """Sample a shared native analytic height field; row units are world/radians/seconds."""
        self._check()
        if len(waves)>32 or any(len(row)!=5 for row in waves):
            raise ValueError('Wave field requires at most 32 five-value rows')
        values=[float(value) for row in waves for value in row]
        source=(C.c_double*len(values))(*values);output=(C.c_double*6)()
        fn=self._lib.nrWaveSample
        fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.c_double,C.c_double,C.c_double,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
        if fn(source,len(waves),x,z,seconds,output,6)!=1:
            raise ValueError('Invalid wave field parameters')
        return list(output)

    @_serialized
    def script_runs(self,text: str) -> list[tuple[int,int,str]]:
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Script capacity')
        fn=self._lib.nrScriptRuns;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*3))();count=fn(values,len(text),out,len(text))
        if count<0:raise ValueError('Invalid Unicode scalar')
        return [(out[3*i],out[3*i+1],int(out[3*i+2]).to_bytes(4,'big').decode('ascii')) for i in range(count)]

    @_serialized
    def line_breaks(self,text: str) -> list[int]:
        """Candidate Unicode 17 line-break opportunities as owned scalar offsets."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Line-break capacity')
        fn=self._lib.nrLineBreaks
        fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(len(text)+1))()
        count=fn(values,len(text),out,len(out))
        if count<0:raise ValueError('Invalid Unicode scalar')
        return list(out[:count])
    @_serialized
    def line_break_details(self,text: str) -> list[list[int]]:
        """Owned candidate [scalar offset, mandatory flag] line-break rows."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Line-break capacity')
        fn=self._lib.nrLineBreakDetails
        fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*((len(text)+1)*2))()
        count=fn(values,len(text),out,len(text)+1)
        if count<0:raise ValueError('Invalid Unicode scalar')
        return [list(out[i*2:i*2+2]) for i in range(count)]
    @_serialized
    def grapheme_boundaries(self,text: str) -> list[int]:
        """Unicode 17 extended grapheme boundaries as owned scalar offsets."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Grapheme capacity')
        fn=self._lib.nrGraphemeBreaks
        fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(len(text)+1))()
        count=fn(values,len(text),out,len(out))
        if count<0:raise ValueError('Invalid Unicode scalar')
        return list(out[:count])
    @_serialized
    def grapheme_widths(self,text: str,ambiguous: int=1) -> list[list[int]]:
        """Owned [start, end, columns] scalar rows under nr-grapheme-cell-width-v1."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Ambiguous width must be 1 or 2')
        if len(text)>2048:raise ValueError('Grapheme capacity')
        fn=self._lib.nrGraphemeWidths
        fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*3))()
        count=fn(values,len(text),ambiguous,out,len(text))
        if count<0:raise ValueError('Invalid Unicode scalar')
        return [list(out[i*3:i*3+3]) for i in range(count)]
    @_serialized
    def grapheme_layout(self,text: str,columns: int,ambiguous: int=1) -> list[list[int]]:
        """Owned [start, end, column, row, width] under nr-grapheme-layout-v1."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Ambiguous width must be 1 or 2')
        if len(text)>2048:raise ValueError('Grapheme capacity')
        if type(columns) is not int or not 1<=columns<=0xffffffff:raise ValueError('Positive uint32 columns required')
        fn=self._lib.nrGraphemeLayout
        fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*5))()
        count=fn(values,len(text),ambiguous,columns,out,len(text))
        if count<0:raise ValueError('Invalid Unicode scalar')
        return [list(out[i*5:i*5+5]) for i in range(count)]
    @_serialized
    def text_run_source(self,kind: int,id: int) -> str:
        self._check()
        if type(kind) is not int or kind not in range(4) or type(id) is not int or not 0<=id<=65535:raise ValueError('Invalid text run key')
        fn=self._lib.nrTextRunSource;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        n=fn(self._context,kind,id,None,0)
        if n<0:raise ValueError('Missing or invalid text run')
        if n==0:return ''
        out=(C.c_uint32*n)();written=fn(self._context,kind,id,out,n)
        if written!=n:raise RuntimeError('Text source changed during read')
        return ''.join(chr(c) for c in out[:n])
    @_serialized
    def text_run_clusters(self,kind: int,id: int) -> list[list[int]]:
        self._check()
        if type(kind) is not int or kind not in range(4) or type(id) is not int or not 0<=id<=65535:raise ValueError('Invalid text run key')
        fn=self._lib.nrTextRunClusters;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        n=fn(self._context,kind,id,None,0)
        if n<0:raise ValueError("Missing or invalid text run")
        out=(C.c_uint32*(n*4))();written=fn(self._context,kind,id,out,n)
        if written!=n:raise RuntimeError("Text source changed during read")
        if n<0:raise ValueError('Missing or invalid text run')
        return [list(out[i*4:i*4+4]) for i in range(n)]
    @_serialized
    def text_run_layout(self,kind: int,id: int,columns: int,ambiguous: int=1) -> list[list[int]]:
        self._check()
        if type(kind) is not int or kind not in range(4) or type(id) is not int or not 0<=id<=65535:raise ValueError('Invalid text run key')
        if type(columns) is not int or not 1<=columns<=0xffffffff or type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Invalid text layout policy')
        fn=self._lib.nrTextRunLayout;fn.argtypes=[C.c_void_p]+[C.c_uint32]*4+[C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        n=fn(self._context,kind,id,ambiguous,columns,None,0)
        if n<0:raise ValueError("Missing or invalid text run")
        out=(C.c_uint32*(n*7))();written=fn(self._context,kind,id,ambiguous,columns,out,n)
        if written!=n:raise RuntimeError("Text source changed during read")
        if n<0:raise ValueError('Missing or invalid text run')
        return [list(out[i*7:i*7+7]) for i in range(n)]
    @_serialized
    def text_run_hit(self,kind: int,id: int,columns: int,column: int,row: int,ambiguous: int=1) -> int:
        self._check()
        if type(kind) is not int or kind not in range(4) or type(id) is not int or not 0<=id<=65535:raise ValueError('Invalid text run key')
        if type(columns) is not int or not 1<=columns<=0xffffffff or type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Invalid text layout policy')
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in (column,row)):raise ValueError('Uint32 pointer coordinates required')
        fn=self._lib.nrTextRunHit;fn.argtypes=[C.c_void_p]+[C.c_uint32]*6;fn.restype=C.c_int
        n=fn(self._context,kind,id,ambiguous,columns,column,row)
        if n<0:raise ValueError('Missing or invalid text run')
        return n
    @_serialized
    def text_run_clip(self,kind: int,id: int,columns: int,x: int,y: int,width: int,height: int,ambiguous: int=1) -> list[list[int]]:
        self._check()
        if type(kind) is not int or kind not in range(4) or type(id) is not int or not 0<=id<=65535:raise ValueError('Invalid text run key')
        if type(columns) is not int or not 1<=columns<=0xffffffff or type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Invalid text layout policy')
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in (x,y,width,height)):raise ValueError('Uint32 viewport required')
        fn=self._lib.nrTextRunClip;fn.argtypes=[C.c_void_p]+[C.c_uint32]*8+[C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        n=fn(self._context,kind,id,ambiguous,columns,x,y,width,height,None,0)
        if n<0:raise ValueError("Missing or invalid text run")
        out=(C.c_uint32*(n*9))();written=fn(self._context,kind,id,ambiguous,columns,x,y,width,height,out,n)
        if written!=n:raise RuntimeError("Text source changed during read")
        if n<0:raise ValueError('Missing or invalid text run')
        return [list(out[i*9:i*9+9]) for i in range(n)]
    @_serialized
    def bidi_visual(self,text: str,direction: int=0) -> list[list[int]]:
        """Owned scalar visual [source index, class, level, mapped scalar] rows."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Bidi capacity')
        if type(direction) is not int or direction not in (0,1,2):raise ValueError('Direction must be 0, 1 or 2')
        fn=self._lib.nrBidiVisual;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*4))();n=fn(values,len(text),direction,out,len(text))
        if n<0:raise ValueError('Invalid Unicode scalar')
        return [list(out[i*4:i*4+4]) for i in range(n)]
    @_serialized
    def bidi_lines(self,text: str,ends,direction: int=2) -> list[list[int]]:
        """Owned whole-cluster visual rows for explicit font-selected line ends."""
        self._check();ends=tuple(ends)
        if not isinstance(text,str) or len(text)>2048 or len(ends)>2048:raise ValueError('Invalid explicit line input')
        if type(direction) is not int or direction not in (0,1,2):raise ValueError('Invalid bidi direction')
        if any(type(end) is not int or not 0<end<=len(text) for end in ends):raise ValueError('Invalid line ends')
        source=(C.c_uint32*max(1,len(text)))(*map(ord,text));lines=(C.c_uint32*max(1,len(ends)))(*ends);out=(C.c_uint32*(max(1,len(text))*7))()
        fn=self._lib.nrBidiClusterLines;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        count=fn(source,len(text),lines,len(ends),direction,out,len(text))
        if count<0:raise ValueError('Invalid grapheme or hard-break line boundary')
        return [list(out[i*7:i*7+7]) for i in range(count)]

    @_serialized
    def document_layout(self,text: str,columns: int,direction: int=2,ambiguous: int=1) -> list[list[int]]:
        """Whole-document native bidi rows with caller-owned growing workspace."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>0x7fffffff:raise ValueError('Native scalar addressability')
        if type(direction) is not int or direction not in (0,1,2):raise ValueError('Invalid bidi direction')
        if type(columns) is not int or not 1<=columns<=0xffffffff or type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Invalid text layout policy')
        count=len(text);source=(C.c_uint32*max(1,count))(*map(ord,text));out=(C.c_uint32*(max(1,count)*7))();words=40*(count+1);scratch=(C.c_uint32*words)()
        fn=self._lib.nrDocumentBidiClusterLayout;fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*4+[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint64];fn.restype=C.c_int
        n=fn(source,count,ambiguous,columns,direction,out,count,scratch,words)
        if n<0:raise ValueError('Invalid Unicode scalar or document layout')
        return [list(out[i*7:i*7+7]) for i in range(n)]
    @_serialized
    def document_boundaries(self,text: str) -> list[int]:
        """All native grapheme boundaries, including bidi-hidden controls."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>0x7fffffff:raise ValueError('Native scalar addressability')
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(len(text)+1))()
        fn=self._lib.nrGraphemeBreaks;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        n=fn(values,len(text),out,len(out))
        if n<0:raise ValueError('Invalid Unicode scalar')
        return list(out[:n])
    @staticmethod
    def _document_edge(text,row,end):
        newline=ord(text[row[0]]) in (10,11,12,13,0x85,0x2028,0x2029)
        x=(0 if end else row[2]) if newline else row[2]+(row[4] if (not end if row[5]&1 else end) else 0)
        return [x,row[3]+int(bool(end and newline)),row[5]]
    @_serialized
    def document_hit(self,text: str,columns: int,column: int,row: int,direction: int=2,ambiguous: int=1) -> int:
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in (column,row)):raise ValueError('Uint32 coordinates required')
        rows=self.document_layout(text,columns,direction,ambiguous);selected=0;best=None
        for value in rows:
            for end in (0,1):
                edge=self._document_edge(text,value,end);key=(abs(edge[1]-row),abs(edge[0]-column),-value[end])
                if best is None or key<best:best=key;selected=value[end]
        return selected
    @_serialized
    def document_caret(self,text: str,columns: int,offset: int,affinity: int=1,direction: int=2,ambiguous: int=1) -> list[int]:
        rows=self.document_layout(text,columns,direction,ambiguous)
        if type(offset) is not int or not 0<=offset<=len(text) or type(affinity) is not int or affinity not in (0,1) or offset not in self.document_boundaries(text):raise ValueError('Invalid caret offset or affinity')
        chosen=[0,0,int(direction==1)];found=False
        for value in rows:
            for end in (0,1):
                if value[end]==offset:
                    chosen=self._document_edge(text,value,end);found=True
                    if end==int(affinity==0):return chosen
        if rows and not found:raise ValueError('Invalid Unicode or caret boundary')
        return chosen

    @_serialized
    def bidi_layout(self,text: str,columns: int,direction: int=2,ambiguous: int=1) -> list[list[int]]:
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Bidi capacity')
        if type(direction) is not int or direction not in (0,1,2):raise ValueError('Invalid bidi direction')
        if type(columns) is not int or not 1<=columns<=0xffffffff or type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Invalid text layout policy')
        fn=self._lib.nrBidiClusterLayout;fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*4+[C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*7))();n=fn(values,len(text),ambiguous,columns,direction,out,len(text))
        if n<0:raise ValueError('Invalid Unicode scalar')
        return [list(out[i*7:i*7+7]) for i in range(n)]
    def _bidi_mapping_input(self,text,columns,direction,ambiguous):
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Bidi capacity')
        if type(direction) is not int or direction not in (0,1,2):raise ValueError('Invalid bidi direction')
        if type(columns) is not int or not 1<=columns<=0xffffffff or type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Invalid text layout policy')
        return (C.c_uint32*max(1,len(text)))(*map(ord,text))
    @_serialized
    def bidi_hit(self,text: str,columns: int,column: int,row: int,direction: int=2,ambiguous: int=1) -> int:
        values=self._bidi_mapping_input(text,columns,direction,ambiguous)
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in (column,row)):raise ValueError('Uint32 coordinates required')
        fn=self._lib.nrBidiClusterHit;fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*6;fn.restype=C.c_int
        n=fn(values,len(text),ambiguous,columns,direction,column,row)
        if n<0:raise ValueError('Invalid Unicode scalar')
        return n
    @_serialized
    def bidi_caret(self,text: str,columns: int,offset: int,affinity: int=1,direction: int=2,ambiguous: int=1) -> list[int]:
        values=self._bidi_mapping_input(text,columns,direction,ambiguous)
        if type(offset) is not int or not 0<=offset<=len(text) or type(affinity) is not int or affinity not in (0,1):raise ValueError('Invalid caret offset or affinity')
        fn=self._lib.nrBidiCaret;fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*6+[C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        out=(C.c_uint32*3)()
        if fn(values,len(text),ambiguous,columns,direction,offset,affinity,out,3)<0:raise ValueError('Invalid Unicode or caret boundary')
        return list(out)
    @_serialized
    def selected_text(self) -> str | None:
        """Copy the native selected source, or None when absent or not owned."""
        self._check();fn=self._lib.nrPromptSelection
        fn.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        count=fn(self._context,None,0)
        if count<0:raise ValueError("Invalid selection export")
        out=(C.c_uint32*count)();written=fn(self._context,out,count)
        if written!=count:raise RuntimeError("Selection changed during read")
        if count<0:raise ValueError('Invalid selection export')
        return ''.join(chr(c) for c in out[:count]) if count else None
    @_serialized
    def grapheme_hit(self,text: str,columns: int,column: int,row: int,ambiguous: int=1) -> int:
        """Nearest complete scalar-source boundary under nr-grapheme-hit-v1."""
        self._check()
        if not isinstance(text,str):raise TypeError('Unicode string required')
        if len(text)>2048:raise ValueError('Grapheme capacity')
        if type(ambiguous) is not int or ambiguous not in (1,2):raise ValueError('Ambiguous width must be 1 or 2')
        if type(columns) is not int or not 1<=columns<=0xffffffff:raise ValueError('Positive uint32 columns required')
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in (column,row)):raise ValueError('Uint32 pointer coordinates required')
        fn=self._lib.nrGraphemeHit
        fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*5;fn.restype=C.c_int
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text))
        result=fn(values,len(text),ambiguous,columns,column,row)
        if result<0:raise ValueError('Invalid Unicode scalar')
        return result
    @_serialized
    def particle_motions(self):
        self._check();out=[];values=(C.c_double*6)();words=(C.c_int32*12)()
        for i in range(2048):
            if self._lib.nrParticleMotion(self._context,i,values,6)>0:
                self._lib.nrParticle(self._context,i,words,12);out.append((words[0]&0xffffffff,*tuple(values)))
        return out
    @_serialized
    def catalogue(self) -> list[dict[str, Any]]:
        return json.loads(self._lib.nrCatalogue())
    @_serialized
    def oklch(self,l:float,c:float,h:float) -> int:
        if not(0<=l<=1 and 0<=c<=.5 and -36000<=h<=36000):raise ValueError('Color bounds')
        def rnd(x):return int(x+.5) if x>=0 else int(x-.5)
        v=self._lib.nrOklch(rnd(l*1e6),rnd(c*1e6),rnd(h*1000))
        if v==0xffffffff:raise ValueError('Color rejected')
        return v
    @_serialized
    def composite(self,base:int,source:int,base_alpha:int=65535,source_alpha:int=65535,blend:int=0,operation:int=0,seed:int=0) -> tuple[int,int]:
        values=[base,source,base_alpha,source_alpha,blend,operation,seed]
        limits=[0xffffff,0xffffff,65535,65535,27,12,0xffffffff]
        if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=limit for v,limit in zip(values,limits)):raise ValueError('Composite bounds')
        out=(C.c_uint32*2)()
        if self._lib.nrComposite(*values,out):raise ValueError('Composite rejected')
        return tuple(out)
    @_serialized
    def composite_in_space(self,base:int,source:int,space:int,base_alpha:int=65535,source_alpha:int=65535,blend:int=0,operation:int=0,seed:int=0) -> tuple[int,int]:
        """Pure composition: 0 sRGB, 1 linear sRGB, 2 OKLab, 3 OKLCh."""
        self._check();values=[base,source,base_alpha,source_alpha,blend,operation,seed,space]
        limits=[0xffffff,0xffffff,65535,65535,27,12,0xffffffff,3]
        if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=limit for v,limit in zip(values,limits)):raise ValueError('Composite bounds')
        out=(C.c_uint32*2)()
        if self._lib.nrCompositeInSpace(*values,out):raise ValueError('Composite rejected')
        return tuple(out)
    @_serialized
    def text_sample(self, identity: int, index: int) -> tuple[int, ...]:
        """Display/source scalar, stable ID, XY Q16, alpha/1e6, hue/1e3, settled."""
        self._check()
        if any(isinstance(x,bool) or not isinstance(x,int) for x in (identity,index)) or not 1<=identity<=65535 or not 0<=index<2048:
            raise ValueError('Text identity/index bounds')
        out=(C.c_int32*8)()
        if self._lib.nrTextSample(self._context,identity,index,out,8):raise ValueError('Text run or index not found')
        values=list(out);values[2]&=0xffffffff
        return tuple(values)
    @_serialized
    def text_cluster_sample(self, identity: int, index: int) -> tuple[int, ...]:
        """Whole-grapheme ID, source span, anchor XY, alpha, hue, settled."""
        self._check()
        if any(isinstance(x,bool) or not isinstance(x,int) for x in (identity,index)) or not 1<=identity<=65535 or not 0<=index<2048:
            raise ValueError('Text cluster identity/index bounds')
        out=(C.c_int32*8)()
        if self._lib.nrTextClusterSample(self._context,identity,index,out,8):raise ValueError('Text cluster not found')
        values=list(out);values[0]&=0xffffffff
        return tuple(values)
    @_serialized
    def text_trail_sample(self, identity: int, index: int, trail_index: int) -> list[int]:
        """Owned source ID, glyph, ordinal, XY Q16, alpha/1e6, hue/1e3, settled."""
        self._check()
        values=(identity,index,trail_index)
        if any(isinstance(x,bool) or not isinstance(x,int) for x in values) or not 1<=identity<=65535 or not 0<=index<2048 or not 0<=trail_index<8:
            raise ValueError('Text trail identity/index bounds')
        out=(C.c_int32*8)()
        if self._lib.nrTextTrailSample(self._context,identity,index,trail_index,out,8):raise ValueError('Text trail not found')
        values=list(out);values[0]&=0xffffffff
        return values
    @_serialized
    def window_sample(self, identity: int, u: float, v: float, visibility: float) -> tuple[int, ...]:
        """Pure local XYZ Q16, alpha/1e6, inside mask. UV and visibility in [0,1]."""
        self._check()
        if isinstance(identity,bool) or not isinstance(identity,int) or not 1<=identity<=65535 or not all(isinstance(x,(int,float)) and not isinstance(x,bool) and 0<=x<=1 for x in (u,v,visibility)):
            raise ValueError('Window sample bounds')
        out=(C.c_int32*5)()
        if self._lib.nrWindowSample(self._context,identity,int(u*1e6+.5),int(v*1e6+.5),int(visibility*1e6+.5),out,5):raise ValueError('Window not found')
        return tuple(out)
    def batch(self, commands: list[dict[str, Any]]) -> None:
        """Commit a bounded set of scene edits together, or reject all edits."""
        self.command({'op':'batch', 'commands':commands})
    def schedule(self, identity: int, at_us: int, command: dict[str, Any]) -> None:
        """Queue a validated edit for a simulation boundary; save includes it."""
        self.command({'op':'schedule','id':identity,'atUs':at_us,'command':command})
    def cancel_scheduled(self, identity: int) -> None:
        self.command({'op':'cancel-schedule','id':identity})
    def set_accessibility(self, *, reduced_motion: bool = False, screen_reader: bool = False) -> None:
        self.command({'op':'accessibility','reducedMotion':reduced_motion,'screenReader':screen_reader})
    @_serialized
    def close(self) -> None:
        """Release owned context; idempotent."""
        self._closed=True;self._context=None;self._memory=None;self._render_memory=None;self._prompt_memory=None;self._model_memory=None;self._modal_memory=None
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
