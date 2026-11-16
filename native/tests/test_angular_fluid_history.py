"""Independent angular archive totals; awaiting State/lifecycle wiring."""
import ctypes as C
import unittest
from test_hull_immersion import NativeScene
from test_angular_fluid_record import Record,Vec
class History(C.Structure):_fields_=[('inertia',C.c_double),('energy',C.c_double),('momentum',Vec),('initialMomentum',Vec),('bodyImpulse',Vec),('initialEnergy',C.c_double),('dissipatedEnergy',C.c_double),('exports',C.c_uint64)]
class AngularHistory(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.init=self.scene._lib.nrAngularFluidRecordInit;self.init.argtypes=[C.POINTER(Record),C.c_double,Vec];self.init.restype=C.c_int
  self.archive=self.scene._lib.nrAngularFluidArchive;self.archive.argtypes=[C.POINTER(History),C.POINTER(Record)];self.archive.restype=C.c_int
 def test_independent_multiple_reservoir_totals(self):
  h=History();self.assertEqual(C.sizeof(h),112);a=Record();b=Record();self.init(C.byref(a),3,Vec(1,2,3));self.init(C.byref(b),5,Vec(-1,0,0))
  self.assertEqual(self.archive(C.byref(h),C.byref(a)),1);self.assertEqual(self.archive(C.byref(h),C.byref(b)),1)
  self.assertEqual((h.inertia,h.energy,h.initialEnergy,h.exports),(8,23.5,23.5,2));self.assertEqual((h.momentum.x,h.momentum.y,h.momentum.z),(-2,6,9));self.assertEqual(h.dissipatedEnergy,0)
 def test_invalid_archive_rejects_without_changing_totals(self):
  h=History();a=Record();self.init(C.byref(a),3,Vec(1,2,3));a.bodyImpulse.x=10;before=bytes(h)
  self.assertEqual(self.archive(C.byref(h),C.byref(a)),0);self.assertEqual(bytes(h),before)
