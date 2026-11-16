"""Public retained sphere drag with independent reaction ledgers; deferred gate."""
import math,unittest
from test_hull_immersion import NativeScene

class RetainedPointDrag(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  for command in [dict(op='surface',id=1),dict(op='mesh',triangles=[dict(a=[-20,0,-20],b=[20,0,-20],c=[20,0,20],surfaceId=1),dict(a=[-20,0,-20],b=[20,0,20],c=[-20,0,20],surfaceId=1)]),dict(op='surface-fluid',surfaceId=1,mass=3),dict(op='surface-fluid-angular',surfaceId=1,inertia=3,pivot=[0,-3,0]),dict(op='float-body',id=1,surfaceId=1,mass=2,radius=1,gravity=0,drag=2,position=[0,-2,0],velocity=[1,0,0])]:self.scene.command(command)
 def test_first_step_reciprocal_translation_and_torque_ledgers(self):
  start=self.scene.snapshot();self.scene.advance_to(8334)
  body=self.scene.float_body(1);linear=self.scene.surface_fluid(1);angular=self.scene.surface_fluid_angular(1)
  fraction=-math.expm1(-4/120*(1/2+2/3));impulse=6/7*fraction;lost=3/7*fraction*(2-fraction)
  self.assertAlmostEqual(body[9],1,places=11);self.assertAlmostEqual(body[3],1-impulse/2,places=11);self.assertAlmostEqual(body[0],body[3]/120,places=11)
  self.assertAlmostEqual(linear[1],impulse/3,places=11);self.assertAlmostEqual(linear[10],impulse,places=11);self.assertAlmostEqual(linear[13],lost,places=11)
  self.assertAlmostEqual(angular[3],-impulse/3,places=11);self.assertAlmostEqual(angular[9],-impulse,places=11);self.assertEqual(angular[10],0)
  self.assertAlmostEqual(2*body[3]+3*linear[1],2,places=11)
  self.assertAlmostEqual(-2*body[3]+3*angular[3],-2,places=11)
  self.assertAlmostEqual(body[3]**2+1.5*linear[1]**2+1.5*angular[3]**2+linear[13]+angular[10],1,places=11)
  before=self.scene.snapshot();self.scene.render();self.assertEqual(self.scene.snapshot(),before)
  self.scene.restore(start);self.scene.advance_to(8334);self.assertEqual(self.scene.snapshot(),before)
 def test_partition_and_export_replacement_preserve_reaction_history(self):
  start=self.scene.snapshot();self.scene.advance_to(100000);finish=self.scene.snapshot()
  self.scene.restore(start)
  for time in [13000,51000,100000]:self.scene.advance_to(time)
  self.assertEqual(self.scene.snapshot(),finish)
  self.scene.command(dict(op='export-surface-fluid',surfaceId=1));exported=self.scene.snapshot();self.scene.command(dict(op='export-surface-fluid',surfaceId=1));self.assertEqual(self.scene.snapshot(),exported)
  linear=self.scene.info()['surfaceFluids'][0]['history'];angular=self.scene.info()['surfaceFluidAngular'][0]['history']
  self.assertEqual(linear['exports'],1);self.assertEqual(angular['exports'],1)
  self.scene.command(dict(op='surface-fluid',surfaceId=1,mass=4));self.assertEqual(self.scene.info()['surfaceFluids'][0]['history'],linear);self.assertEqual(self.scene.info()['surfaceFluidAngular'][0]['history'],angular)
  self.scene.restore(exported);self.assertEqual(self.scene.snapshot(),exported)
