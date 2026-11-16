"""Queued ABI contracts: scenic outputs cannot overwrite native authority."""
import ctypes as C,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'tests'))
from nocturne_native import NativeScene
from test_flow_thickness import setup
class ScenicOutputRanges(unittest.TestCase):
 def test_context_alias_and_wrapping_ranges_reject_without_writes(self):
  with NativeScene() as s:
   setup(s);s.command(dict(op='float-body',id=1,surfaceId=1,position=[0,0,0],radius=1,mass=1000))
   signatures=[('nrFlowThickness',6,False),('nrSurfaceTriangles',12,False),('nrSurfaceFoam',12,False),('nrSurfaceFoamTransport',12,False),('nrFloatBody',12,False),('nrSurfaceWaveSample',6,True)]
   pointer=C.cast(s._context,C.POINTER(C.c_double));wrapped=C.cast(C.c_void_p((1<<(C.sizeof(C.c_void_p)*8))-8),C.POINTER(C.c_double))
   before=s.snapshot();size=s._lib.nrContextSize();context_before=C.string_at(s._context,size)
   for name,capacity,wave in signatures:
    fn=getattr(s._lib,name);fn.restype=C.c_int;fn.argtypes=[C.c_void_p,C.c_uint32]+([C.c_double,C.c_double] if wave else [])+[C.POINTER(C.c_double),C.c_uint32]
    for out in [pointer,wrapped]:
     args=[s._context,1]+([0.,0.] if wave else [])+[out,capacity]
     self.assertEqual(fn(*args),-1,name);self.assertEqual(C.string_at(s._context,size),context_before,name);self.assertEqual(s.snapshot(),before,name)
 def test_valid_owned_buffers_still_accept(self):
  with NativeScene() as s:
   setup(s);self.assertEqual(len(s.surface_triangles(1)),12);self.assertEqual(len(s.surface_foam(1)),12);self.assertEqual(len(s.surface_foam_transport(1)),12);self.assertEqual(s.flow_thickness(1)[1],.5)
