"""Independent force and torque references; qualification deferred to Gate 2."""
import ctypes as C
import unittest
from test_hull_immersion import BOX,FACES,NativeScene
class HullBuoyancy(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.wrench=self.scene._lib.nrHullBuoyancy
  self.wrench.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.c_double,C.c_double,C.c_double,C.c_double,C.POINTER(C.c_double),C.POINTER(C.c_double),C.c_uint32];self.wrench.restype=C.c_int
 def force(self,center,density=1000,gravity=10,mass=4000):
  v=(C.c_double*24)(*(x for row in BOX for x in row));f=(C.c_uint32*36)(*(x for row in FACES for x in row));c=(C.c_double*3)(*center);out=(C.c_double*11)(*([777]*11))
  return self.wrench(v,8,f,12,0,density,gravity,mass,c,out,11),list(out)
 def test_neutral_mass_and_off_axis_torque(self):
  before=self.scene.snapshot();code,row=self.force([0,0,0]);self.assertEqual(code,1)
  self.assertEqual(row,[8,4,0,-.5,0,0,0,0,0,0,0])
  code,row=self.force([.25,0,.5]);self.assertEqual(code,1)
  # r=(-.25,-.5,-.5); F=(0,40000,0); r cross F=(20000,0,-10000).
  self.assertEqual(row[5:],[0,0,0,20000,0,-10000]);self.assertEqual(self.scene.snapshot(),before)
 def test_density_and_gravity_zero_and_heavy_mass(self):
  code,row=self.force([0,0,0],mass=5000);self.assertEqual(code,1);self.assertEqual(row[5:8],[0,-10000,0])
  code,row=self.force([0,0,0],density=0);self.assertEqual(code,1);self.assertEqual(row[5:8],[0,-40000,0])
  code,row=self.force([1,0,1],gravity=0);self.assertEqual(code,1);self.assertEqual(row[5:],[0]*6)
 def test_invalid_material_and_center_are_atomic(self):
  for args in [([0,0,0],-1,10,4000),([0,0,0],1000,float('nan'),4000),([float('inf'),0,0],1000,10,4000),([0,0,0],1000,10,0)]:
   code,row=self.force(*args);self.assertEqual(code,-1);self.assertEqual(row,[777]*11)

 def test_oriented_plane_vertical_lift_and_centroid_torque(self):
  fn=self.scene._lib.nrHullBuoyancyPlane
  fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_double),C.POINTER(C.c_double),C.c_double,C.c_double,C.c_double,C.POINTER(C.c_double),C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
  v=(C.c_double*24)(*(x for row in BOX for x in row));f=(C.c_uint32*36)(*(x for row in FACES for x in row));p=(C.c_double*3)(0,0,0);n=(C.c_double*3)(-1,1,0);c=(C.c_double*3)(0,0,0);out=(C.c_double*11)()
  before=self.scene.snapshot();self.assertEqual(fn(v,8,f,12,p,n,1000,10,4000,c,out,11),1)
  for a,b in zip(out,[8,4,1/3,-1/3,0,0,0,0,0,0,40000/3]):self.assertAlmostEqual(a,b)
  # Reversing the wet half-space reverses its centroid and moment.
  n[0]=1;n[1]=-1;self.assertEqual(fn(v,8,f,12,p,n,1000,10,4000,c,out,11),1);self.assertAlmostEqual(out[10],-40000/3)
  n[0]=n[1]=0
  for i in range(11):out[i]=777
  self.assertEqual(fn(v,8,f,12,p,n,1000,10,4000,c,out,11),-1);self.assertEqual(list(out),[777]*11)
  self.assertEqual(self.scene.snapshot(),before)
