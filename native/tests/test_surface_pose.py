"""Independent rigid-frame references; authored for the combined scenic gate."""
import ctypes as C
import math
import unittest
from test_hull_immersion import NativeScene

class Vec(C.Structure):
 _fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]

class SurfacePose(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.advance=self.scene._lib.nrSurfacePoseAdvance
  self.advance.argtypes=[C.POINTER(C.c_double),Vec,C.c_double,C.POINTER(C.c_double)];self.advance.restype=C.c_int
  self.motion=self.scene._lib.nrSurfacePoseMotion
  self.motion.argtypes=[C.POINTER(C.c_double),Vec,Vec,Vec,Vec,Vec,C.POINTER(C.c_double)];self.motion.restype=C.c_int
  self.inverse=self.scene._lib.nrSurfacePoseInverse
  self.inverse.argtypes=[C.POINTER(C.c_double),Vec,Vec,Vec,Vec,Vec,Vec,C.POINTER(C.c_double)];self.inverse.restype=C.c_int
  self.bounds=self.scene._lib.nrSurfacePoseBounds
  self.bounds.argtypes=[C.POINTER(C.c_double),Vec,Vec,Vec,Vec,C.POINTER(C.c_double),C.c_uint32,C.c_double,C.POINTER(C.c_double)];self.bounds.restype=C.c_int
 def test_rotating_sweep_encloses_interior_extrema_and_translation(self):
  q=(C.c_double*4)(0,0,0,1);points=(C.c_double*9)(12,20,30,10,23,30,10,20,31);out=(C.c_double*6)()
  for seconds in [1,-1]:
   self.assertEqual(self.bounds(q,Vec(10,20,30),Vec(1,2,3),Vec(0,0,math.pi),Vec(2,-3,4),points,3,seconds,out),1)
   # Independent analytic paths sample the interior half-turn extrema.
   for step in range(201):
    t=seconds*step/200;angle=math.pi*t
    for x,y,z in [(2,0,0),(0,3,0),(0,0,1)]:
     world=[11+2*t+x*math.cos(angle)-y*math.sin(angle),22-3*t+x*math.sin(angle)+y*math.cos(angle),33+4*t+z]
     for axis in range(3):self.assertGreaterEqual(world[axis],out[axis]-1e-12);self.assertLessEqual(world[axis],out[3+axis]+1e-12)
 def test_static_rotation_translation_bounds_are_tight_and_owned(self):
  q=(C.c_double*4)(0,0,math.sqrt(.5),math.sqrt(.5));points=(C.c_double*6)(12,20,30,10,23,31)
  self.assertEqual(self.bounds(q,Vec(10,20,30),Vec(1,2,3),Vec(),Vec(2,-3,4),points,2,1,points),1)
  for actual,expected in zip(points,[8,19,33,13,24,38]):self.assertAlmostEqual(actual,expected,places=12)
 def test_sweep_late_invalid_point_and_invalid_count_are_atomic(self):
  q=(C.c_double*4)(0,0,0,1);points=(C.c_double*6)(0,0,0,1,float('nan'),0);out=(C.c_double*6)(*([777]*6))
  self.assertEqual(self.bounds(q,Vec(),Vec(),Vec(0,1,0),Vec(),points,2,1,out),0);self.assertEqual(list(out),[777]*6)
  for count in [0,769]:
   self.assertEqual(self.bounds(q,Vec(),Vec(),Vec(),Vec(),points,count,1,out),0);self.assertEqual(list(out),[777]*6)
 def test_arbitrary_axis_small_steps_and_backward_extrapolation(self):
  identity=(C.c_double*4)(0,0,0,1);whole=(C.c_double*4)();split=(C.c_double*4)(0,0,0,1);omega=Vec(.13,-.27,.41)
  self.assertEqual(self.advance(identity,omega,10,whole),1)
  speed=math.sqrt(.13**2+.27**2+.41**2)
  expected=[x*math.sin(speed*5)/speed for x in [.13,-.27,.41]]+[math.cos(speed*5)]
  for actual,reference in zip(whole,expected):self.assertAlmostEqual(actual,reference,places=12)
  for _ in range(1200):self.assertEqual(self.advance(split,omega,1/120,split),1)
  for actual,reference in zip(split,whole):self.assertAlmostEqual(actual,reference,places=11)
  self.assertEqual(self.advance(whole,omega,-10,whole),1)
  for actual,reference in zip(whole,identity):self.assertAlmostEqual(actual,reference,places=12)
 def test_frame_inverse_removes_rigid_velocity_and_preserves_local_motion(self):
  q=(C.c_double*4)(0,0,math.sqrt(.5),math.sqrt(.5));out=(C.c_double*6)()
  # Rotated radius (0,2,0), rigid velocity (0,5,6), plus rotated
  # authored local velocity (1,2,3) -> world velocity (-2,6,9).
  self.assertEqual(self.inverse(q,Vec(10,20,30),Vec(1,2,3),Vec(0,0,2),Vec(4,5,6),Vec(11,24,33),Vec(-2,6,9),out),1)
  for actual,reference in zip(out,[12,20,30,1,2,3]):self.assertAlmostEqual(actual,reference,places=12)
 def test_point_velocity_matches_independent_position_derivative(self):
  q=(C.c_double*4)(0,0,0,1);omega=Vec(.13,-.27,.41);velocity=Vec(2,-3,4);pivot=Vec(10,20,30);point=Vec(12,17,34)
  row=(C.c_double*6)();self.assertEqual(self.motion(q,pivot,Vec(),omega,velocity,point,row),1)
  sides=[];epsilon=1e-5
  for seconds in [-epsilon,epsilon]:
   turned=(C.c_double*4)();self.assertEqual(self.advance(q,omega,seconds,turned),1)
   result=(C.c_double*6)();self.assertEqual(self.motion(turned,pivot,Vec(2*seconds,-3*seconds,4*seconds),omega,velocity,point,result),1);sides.append(list(result))
  for axis in range(3):self.assertAlmostEqual((sides[1][axis]-sides[0][axis])/(2*epsilon),row[3+axis],places=8)
 def test_world_rotation_composition_partition_and_input_alias(self):
  before=self.scene.snapshot();q=(C.c_double*4)(0,0,0,1);out=(C.c_double*4)()
  self.assertEqual(self.advance(q,Vec(0,0,math.pi),.5,out),1)
  for actual,expected in zip(out,[0,0,math.sqrt(.5),math.sqrt(.5)]):self.assertAlmostEqual(actual,expected,places=6)
  split=(C.c_double*4)(0,0,0,1)
  for _ in range(60):self.assertEqual(self.advance(split,Vec(0,0,math.pi),1/120,split),1)
  for actual,expected in zip(split,out):self.assertAlmostEqual(actual,expected,places=6)
  # World Z rotation composed after existing X rotation: qz*qx has +Y.
  q=(C.c_double*4)(math.sqrt(.5),0,0,math.sqrt(.5))
  self.assertEqual(self.advance(q,Vec(0,0,math.pi),.5,q),1)
  for actual in q:self.assertAlmostEqual(actual,.5,places=6)
  self.assertEqual(self.scene.snapshot(),before)
 def test_explicit_pivot_and_tangential_velocity(self):
  q=(C.c_double*6)(0,0,math.sqrt(.5),math.sqrt(.5),777,777)
  self.assertEqual(self.motion(q,Vec(10,20,30),Vec(1,2,3),Vec(0,0,2),Vec(4,5,6),Vec(12,20,30),q),1)
  for actual,expected in zip(q,[11,24,33,0,5,6]):self.assertAlmostEqual(actual,expected)
 def test_invalid_inputs_leave_output_untouched(self):
  out=(C.c_double*6)(*([777]*6));q=(C.c_double*4)(0,0,0,1)
  for omega,seconds in [(Vec(0,0,float('nan')),1),(Vec(0,0,1),float('inf'))]:
   self.assertEqual(self.advance(q,omega,seconds,out),0);self.assertEqual(list(out),[777]*6)
  bad=(C.c_double*4)(0,0,0,2)
  self.assertEqual(self.motion(bad,Vec(),Vec(),Vec(),Vec(),Vec(),out),0);self.assertEqual(list(out),[777]*6)
  self.assertEqual(self.inverse(q,Vec(),Vec(),Vec(),Vec(),Vec(),Vec(float('nan'),0,0),out),0);self.assertEqual(list(out),[777]*6)
