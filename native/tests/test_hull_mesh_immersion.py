"""Independent integrals for disjoint piecewise water columns."""
import ctypes as C
import unittest
from test_hull_immersion import BOX,FACES,NativeScene
class HullMeshImmersion(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.fn=self.scene._lib.nrHullMeshImmersion
  self.fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_double),C.c_uint32];self.fn.restype=C.c_int
 def sample(self,water):
  v=(C.c_double*24)(*(x for p in BOX for x in p));f=(C.c_uint32*36)(*(x for p in FACES for x in p));w=(C.c_double*(9*len(water)))(*(x for t in water for p in t for x in p));out=(C.c_double*5)(*([777]*5))
  return self.fn(v,8,f,12,w,len(water),out,5),list(out)
 def region(self,x0,x1,height):
  a=[x0,height(x0),-2];b=[x1,height(x1),-2];c=[x1,height(x1),2];d=[x0,height(x0),2];return [[a,b,c],[a,c,d]]
 def test_flat_split_surface_matches_box_half(self):
  before=self.scene.snapshot();code,row=self.sample(self.region(-2,2,lambda x:0));self.assertEqual(code,1)
  for a,b in zip(row,[8,4,0,-.5,0]):self.assertAlmostEqual(a,b)
  self.assertEqual(self.scene.snapshot(),before)
 def test_discontinuous_heights_exact_weighted_moment(self):
  code,row=self.sample(self.region(-2,0,lambda x:0)+self.region(0,2,lambda x:.5));self.assertEqual(code,1)
  for a,b in zip(row,[8,5,.1,-.35,0]):self.assertAlmostEqual(a,b)
 def test_v_surface_integral_and_partial_coverage(self):
  water=self.region(-2,0,lambda x:-x)+self.region(0,2,lambda x:x);code,row=self.sample(water);self.assertEqual(code,1)
  for a,b in zip(row,[8,6,0,-2/9,0]):self.assertAlmostEqual(a,b)
  code,row=self.sample(self.region(-2,0,lambda x:0));self.assertEqual(code,1)
  for a,b in zip(row,[8,2,-.5,-.5,0]):self.assertAlmostEqual(a,b)
 def test_overlapping_and_vertical_surface_reject_atomically(self):
  water=self.region(-2,2,lambda x:0)
  for bad in [water+water,[[[0,0,0],[0,1,0],[0,0,1]]]]:
   code,row=self.sample(bad);self.assertEqual(code,-1);self.assertEqual(row,[777]*5)

 def test_owned_binding_and_reversed_water_winding(self):
  water=self.region(-2,0,lambda x:-x)+self.region(0,2,lambda x:x);flat=[sum(t,[]) for t in water]
  before=self.scene.snapshot();row=self.scene.hull_mesh_immersion(BOX,FACES,flat)
  for a,b in zip(row,[8,6,0,-2/9,0]):self.assertAlmostEqual(a,b)
  row[1]=999;self.assertAlmostEqual(self.scene.hull_mesh_immersion(BOX,FACES,flat)[1],6)
  reversed_rows=[sum(list(reversed(t)),[]) for t in water]
  for a,b in zip(self.scene.hull_mesh_immersion(BOX,FACES,reversed_rows),[8,6,0,-2/9,0]):self.assertAlmostEqual(a,b)
  self.assertEqual(self.scene.snapshot(),before)
