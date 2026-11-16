"""Independent frozen-radius reciprocal drag references; deferred scenic gate."""
import ctypes as C
import math,unittest
from test_hull_immersion import NativeScene
from test_surface_pose import Vec
class FluidPointDrag(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.query=self.scene._lib.nrFluidPointDragExchange
  self.query.argtypes=[C.c_double]*5+[Vec]*4+[C.POINTER(C.c_double)];self.query.restype=C.c_int
 def test_off_center_impulse_conserves_translation_rotation_and_energy(self):
  before=self.scene.snapshot();out=(C.c_double*13)()
  self.assertEqual(self.query(2,3,3,4,.5,Vec(1,0,0),Vec(),Vec(),Vec(0,1,0),out),1)
  fraction=-math.expm1(-4*.5*(1/2+2/3));impulse=6/7*fraction;expected=[1-impulse/2,0,0,impulse/3,0,0,0,0,-impulse/3,impulse,0,0,3/7*fraction*(2-fraction)]
  for actual,reference in zip(out,expected):self.assertAlmostEqual(actual,reference,places=11)
  self.assertAlmostEqual(2*out[0]+3*out[3],2,places=11)
  self.assertAlmostEqual(-2*out[0]+3*out[8],-2,places=11)
  self.assertAlmostEqual(out[0]**2+1.5*out[3]**2+1.5*out[8]**2+out[12],1,places=11);self.assertEqual(self.scene.snapshot(),before)
 def test_parallel_contact_has_no_reaction_torque(self):
  out=(C.c_double*13)();self.assertEqual(self.query(2,3,3,4,.5,Vec(0,1,0),Vec(),Vec(),Vec(0,1,0),out),1)
  fraction=-math.expm1(-4*.5*(1/2+1/3));self.assertAlmostEqual(out[1],1-.6*fraction,places=11);self.assertAlmostEqual(out[4],.4*fraction,places=11);self.assertEqual(list(out[6:9]),[0,0,0])
 def test_small_derived_effective_mass_retains_response(self):
  out=(C.c_double*13)();radius=32760
  self.assertEqual(self.query(2,3,.001,4,.5,Vec(1,0,0),Vec(),Vec(),Vec(0,radius,0),out),1)
  reduced=1/(1/2+1/3+radius**2/.001)
  self.assertAlmostEqual(out[9]/reduced,1,places=12);self.assertAlmostEqual(out[8]/(-radius*reduced/.001),1,places=12);self.assertAlmostEqual(out[12]/(.5*reduced),1,places=12)
 def test_invalid_parameters_preserve_output(self):
  out=(C.c_double*13)(*([777]*13))
  for conductance,seconds in [(float('nan'),.5),(4,-1),(float('inf'),1)]:
   self.assertEqual(self.query(2,3,3,conductance,seconds,Vec(1,0,0),Vec(),Vec(),Vec(0,1,0),out),0);self.assertEqual(list(out),[777]*13)
 def test_frozen_radius_exchange_partitions_with_owned_input_state(self):
  body=Vec(1,2,3);water=Vec(-1,0,1);omega=Vec(.2,-.3,.4);radius=Vec(0,1,0);whole=(C.c_double*13)();split=(C.c_double*13)()
  self.assertEqual(self.query(2,3,3,4,1,body,water,omega,radius,whole),1)
  lost=0
  for _ in range(120):
   self.assertEqual(self.query(2,3,3,4,1/120,body,water,omega,radius,split),1)
   body=Vec(*split[:3]);water=Vec(*split[3:6]);omega=Vec(*split[6:9]);lost+=split[12]
  for actual,reference in zip(split[:9],whole[:9]):self.assertAlmostEqual(actual,reference,places=11)
  self.assertAlmostEqual(lost,whole[12],places=11)
