"""Analytic triangular-prism cut and rotation references for oriented planes."""
import ctypes as C
import math,unittest
from test_hull_immersion import BOX,FACES,NativeScene
class HullPlane(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.fn=self.scene._lib.nrHullImmersionPlane
  self.fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_double),C.POINTER(C.c_double),C.POINTER(C.c_double),C.c_uint32];self.fn.restype=C.c_int
 def sample(self,vertices,point,normal):
  v=(C.c_double*24)(*(x for row in vertices for x in row));f=(C.c_uint32*36)(*(x for row in FACES for x in row));p=(C.c_double*3)(*point);n=(C.c_double*3)(*normal);out=(C.c_double*5)(*([777]*5))
  return self.fn(v,8,f,12,p,n,out,5),list(out)
 def test_diagonal_prism_and_complement(self):
  before=self.scene.snapshot()
  for normal,expected in [([-1,1,0],[8,4,1/3,-1/3,0]),([1,-1,0],[8,4,-1/3,1/3,0]),([-10,10,0],[8,4,1/3,-1/3,0])]:
   code,row=self.sample(BOX,[0,0,0],normal);self.assertEqual(code,1)
   for a,b in zip(row,expected):self.assertAlmostEqual(a,b)
  self.assertEqual(self.scene.snapshot(),before)
 def test_rigid_rotation_and_translation_covariance(self):
  q=math.sqrt(.5);shift=[100,20,-50]
  vertices=[[q*x-q*y+100,q*x+q*y+20,z-50] for x,y,z in BOX]
  code,row=self.sample(vertices,shift,[-q,q,0]);self.assertEqual(code,1)
  for a,b in zip(row,[8,4,100+q*.5,20-q*.5,-50]):self.assertAlmostEqual(a,b)
 def test_zero_nonfinite_normal_and_point_reject_atomically(self):
  for p,n in [([0,0,0],[0,0,0]),([0,0,0],[0,float('nan'),0]),([float('inf'),0,0],[0,1,0])]:
   code,row=self.sample(BOX,p,n);self.assertEqual(code,-1);self.assertEqual(row,[777]*5)
