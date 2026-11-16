import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class PathTravel(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def testArcLengthAndOutgoingCornerDirection(self):
  points=[[0,0,0],[3,0,0],[3,4,0]]
  self.assertEqual(self.s.path_sample(points,5),[3,2,0,0,1,0,7,5])
  self.assertEqual(self.s.path_sample(points,3),[3,0,0,0,1,0,7,3])
  self.assertEqual(self.s.path_sample(points,20),[3,4,0,0,1,0,7,7])
 def testLoopReverseAndNegativeDistances(self):
  points=[[0,0,0],[3,0,0]]
  self.assertEqual(self.s.path_sample(points,4,mode='loop'),[1,0,0,1,0,0,3,1])
  self.assertEqual(self.s.path_sample(points,-1,mode='loop'),[2,0,0,1,0,0,3,2])
  self.assertEqual(self.s.path_sample(points,4,mode='reverse'),[2,0,0,-1,0,0,3,2])
 def testClosedPathIncludesClosingSegmentAndPure(self):
  before=self.s.snapshot();row=self.s.path_sample([[0,0,0],[3,0,0],[3,4,0]],9,closed=True)
  self.assertAlmostEqual(row[0],1.8);self.assertAlmostEqual(row[1],2.4);self.assertEqual(row[6:], [12,9]);self.assertEqual(before,self.s.snapshot())
 def testInvalidPathsAndUntouchedOutput(self):
  for points in [[],[[0,0,0]],[[0,0,0],[0,0,0]],[[0,0,0],[float('nan'),0,0]],[[0,0,0],[16001,0,0]]]:
   with self.assertRaises(ValueError):self.s.path_sample(points,0)
  import ctypes as C
  self.s.path_sample([[0,0,0],[1,0,0]],0);fn=self.s._lib.nrPathSample;source=(C.c_double*6)(0,0,0,1,0,0);out=(C.c_double*8)(*([123]*8))
  self.assertEqual(fn(source,2,0,0,0,out,7),-1);self.assertEqual(list(out),[123]*8)

 def testHugeDistanceOnTinyPathIsFiniteAndInRange(self):
  import math
  row=self.s.path_sample([[0,0,0],[1e-8,0,0]],1e12,mode='loop')
  self.assertTrue(all(map(math.isfinite,row)));self.assertGreaterEqual(row[7],0);self.assertLess(row[7],row[6])
