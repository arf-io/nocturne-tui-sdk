"""Independent analytic submerged-volume references for native convex hulls."""
import ctypes as C
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
BOX=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
FACES=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]]
class HullImmersion(unittest.TestCase):
 def test_owned_oriented_plane_and_buoyancy_binding(self):
  before=self.scene.snapshot()
  queries=self.scene.info()['contract']['queryContracts'];self.assertEqual(queries['nrHullImmersionPlane']['rowWords'],5);self.assertEqual(queries['nrHullBuoyancyPlane']['rowWords'],11);self.assertEqual(queries['nrHullBuoyancyPlane']['liftDirection'],'vertical')
  expected=[8,4,1/3,-1/3,0]
  row=self.scene.hull_immersion_plane(BOX,FACES,[0,0,0],[-1,1,0])
  for a,b in zip(row,expected):self.assertAlmostEqual(a,b)
  row[1]=999
  fresh=self.scene.hull_immersion_plane(BOX,FACES,[0,0,0],[-10,10,0])
  for a,b in zip(fresh,expected):self.assertAlmostEqual(a,b)
  wrench=self.scene.hull_buoyancy_plane(BOX,FACES,[0,0,0],[-1,1,0],density=1000,gravity=10,mass=4000,center_of_mass=[0,0,0])
  for a,b in zip(wrench,expected+[0,0,0,0,0,40000/3]):self.assertAlmostEqual(a,b)
  with self.assertRaises(ValueError):self.scene.hull_immersion_plane(BOX,FACES,[0,0,0],[0,0,0])
  with self.assertRaises(ValueError):self.scene.hull_buoyancy_plane(BOX,FACES,[0,0,0],[-1,1,0],density=1000,gravity=10,mass=0,center_of_mass=[0,0,0])
  self.assertEqual(self.scene.snapshot(),before)
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.fn=self.scene._lib.nrHullImmersion;self.fn.argtypes=[C.POINTER(C.c_double),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.c_double,C.POINTER(C.c_double),C.c_uint32];self.fn.restype=C.c_int
 def sample(self,vertices,faces,height):
  v=(C.c_double*(3*len(vertices)))(*(x for p in vertices for x in p));f=(C.c_uint32*(3*len(faces)))(*(x for p in faces for x in p));out=(C.c_double*5)(*([777]*5));result=self.fn(v,len(vertices),f,len(faces),height,out,5);return result,list(out)
 def test_box_empty_half_full_and_translation(self):
  before=self.scene.snapshot()
  for height,volume,center in [(-2,0,[0,0,0]),(0,4,[0,-.5,0]),(2,8,[0,0,0])]:
   result,row=self.sample(BOX,FACES,height);self.assertEqual(result,1);self.assertAlmostEqual(row[0],8);self.assertAlmostEqual(row[1],volume)
   for a,b in zip(row[2:],center):self.assertAlmostEqual(a,b)
  vertices=[[x+100,y+20,z-50] for x,y,z in BOX];result,row=self.sample(vertices,FACES,20);self.assertEqual(result,1)
  for a,b in zip(row,[8,4,100,19.5,-50]):self.assertAlmostEqual(a,b)
  self.assertEqual(self.scene.snapshot(),before)
 def test_tetrahedron_cut_matches_similar_volume_and_centroid(self):
  vertices=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]];faces=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]]
  result,row=self.sample(vertices,faces,.5);self.assertEqual(result,1);self.assertAlmostEqual(row[0],1/6);self.assertAlmostEqual(row[1],7/48)
  # Remove the top tetrahedron: volume 1/48 and centroid (1/8,5/8,1/8).
  for a,b in zip(row[2:],[15/56,11/56,15/56]):self.assertAlmostEqual(a,b)
 def test_open_reversed_nonfinite_and_short_outputs_reject_atomically(self):
  for vertices,faces,height in [(BOX,FACES[:-1],0),(BOX,[list(reversed(f)) for f in FACES],0),(BOX,FACES,float('nan'))]:
   result,row=self.sample(vertices,faces,height);self.assertEqual(result,-1);self.assertEqual(row,[777]*5)
  v=(C.c_double*24)(*(x for p in BOX for x in p));f=(C.c_uint32*36)(*(x for p in FACES for x in p));out=(C.c_double*5)(*([777]*5));self.assertEqual(self.fn(v,8,f,12,0,out,4),-1);self.assertEqual(list(out),[777]*5)

 def test_owned_binding_and_input_alias(self):
  before=self.scene.snapshot();row=self.scene.hull_immersion(BOX,FACES,0)
  self.assertEqual(row,[8,4,0,-.5,0]);row[0]=999
  self.assertEqual(self.scene.hull_immersion(BOX,FACES,0),[8,4,0,-.5,0])
  with self.assertRaises(ValueError):self.scene.hull_immersion(BOX,[[0,1,-1]]*4,0)
  v=(C.c_double*24)(*(x for p in BOX for x in p));f=(C.c_uint32*36)(*(x for p in FACES for x in p))
  self.assertEqual(self.fn(v,8,f,12,0,v,5),1);self.assertEqual(list(v[:5]),[8,4,0,-.5,0])
  self.assertEqual(self.scene.snapshot(),before)
