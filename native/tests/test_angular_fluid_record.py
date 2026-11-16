"""Internal retained-record invariants, authored before State integration."""
import ctypes as C
import math,unittest
from test_hull_immersion import NativeScene
class Vec(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Record(C.Structure):_fields_=[('used',C.c_uint32),('padding',C.c_uint32),('inertia',C.c_double),('omega',Vec),('initialMomentum',Vec),('bodyImpulse',Vec),('dissipatedEnergy',C.c_double),('initialEnergy',C.c_double)]
class AngularRecord(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.valid=self.scene._lib.nrAngularFluidRecordValid;self.valid.argtypes=[C.POINTER(Record)];self.valid.restype=C.c_int
  self.init=self.scene._lib.nrAngularFluidRecordInit;self.init.argtypes=[C.POINTER(Record),C.c_double,Vec];self.init.restype=C.c_int
  self.exchange=self.scene._lib.nrAngularFluidRecordExchange;self.exchange.argtypes=[C.POINTER(Record),Vec,Vec,Vec,C.c_double,C.POINTER(C.c_double),C.POINTER(Vec)];self.exchange.restype=C.c_int
 def test_initial_world_momentum_and_energy(self):
  record=Record();self.assertEqual(C.sizeof(record),104);self.assertEqual(self.init(C.byref(record),3,Vec(1,2,3)),1)
  self.assertEqual((record.initialMomentum.x,record.initialMomentum.y,record.initialMomentum.z),(3,6,9));self.assertEqual(record.initialEnergy,21);self.assertEqual(self.valid(C.byref(record)),1)
  record.bodyImpulse.x=3;self.assertEqual(self.valid(C.byref(record)),0);record.omega.x=2;self.assertEqual(self.valid(C.byref(record)),1)
 def test_empty_padding_and_atomic_invalid_initialization(self):
  record=Record();self.assertEqual(self.valid(C.byref(record)),1);record.padding=1;self.assertEqual(self.valid(C.byref(record)),0)
  before=bytes(record);self.assertEqual(self.init(C.byref(record),0,Vec(1,2,3)),0);self.assertEqual(bytes(record),before)
  record=Record();self.init(C.byref(record),3,Vec(0,0,0));record.dissipatedEnergy=float('nan');self.assertEqual(self.valid(C.byref(record)),0)
 def test_rotated_anisotropic_body_exchanges_world_angular_momentum(self):
  record=Record();self.init(C.byref(record),3,Vec(0,0,0));q=(C.c_double*4)(0,0,math.sqrt(.5),math.sqrt(.5));out=Vec()
  self.assertEqual(self.exchange(C.byref(record),Vec(2,4,8),Vec(1,0,0),Vec(4,0,0),.5,q,C.byref(out)),1)
  f=-math.expm1(-4*.5*(1/2+1/3));self.assertAlmostEqual(out.x,1-.6*f);self.assertAlmostEqual(record.omega.y,.4*f);self.assertAlmostEqual(record.bodyImpulse.y,1.2*f)
  self.assertAlmostEqual(2*out.x+3*record.omega.y,2);self.assertAlmostEqual(out.x**2+1.5*record.omega.y**2+record.dissipatedEnergy,1);self.assertEqual(self.valid(C.byref(record)),1)
 def test_invalid_exchange_leaves_both_outputs_untouched(self):
  record=Record();self.init(C.byref(record),3,Vec(0,0,0));before=bytes(record);out=Vec(777,777,777);q=(C.c_double*4)(0,0,0,1)
  self.assertEqual(self.exchange(C.byref(record),Vec(2,4,0),Vec(1,0,0),Vec(4,0,0),.5,q,C.byref(out)),0)
  self.assertEqual(bytes(record),before);self.assertEqual((out.x,out.y,out.z),(777,777,777))
