"""Next retained angular implementation contract; intentionally unimplemented.

Run only at the combined gate after storage, lifecycle and tick integration join
the batch. Passing pure angular-helper tests cannot satisfy these requirements.
"""
import math,unittest
from test_hull_immersion import NativeScene,BOX,FACES

class RetainedAngularFluid(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.scene.command(dict(op='surface',id=1))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-20,0,-20],b=[20,0,-20],c=[20,0,20],surfaceId=1),dict(a=[-20,0,-20],b=[20,0,20],c=[-20,0,20],surfaceId=1)]))
  self.scene.command(dict(op='surface-fluid',surfaceId=1,mass=3))
  self.scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[0,0,0]))
  self.scene.command(dict(op='float-body',id=1,surfaceId=1,mass=2,gravity=0,drag=2,position=[0,-2,0]))
  self.scene.command(dict(op='float-hull',id=1,vertices=BOX,faces=FACES,inertia=[2,2,2],angularVelocity=[0,1,0]))
 def test_reciprocal_rotation_with_independent_first_step_ledger(self):
  start=self.scene.snapshot();self.scene.advance_to(8334)
  body=self.scene.float_hull(1);water=self.scene.surface_fluid_angular(1)
  fraction=-math.expm1(-4/120*(1/2+1/3))
  self.assertAlmostEqual(body[5],1-.6*fraction,places=9)
  self.assertAlmostEqual(water[2],.4*fraction,places=9)
  self.assertAlmostEqual(water[8],1.2*fraction,places=9)
  self.assertAlmostEqual(water[10],.6*fraction*(2-fraction),places=9)
  self.assertAlmostEqual(2*body[5]+3*water[2],2,places=9)
  self.assertAlmostEqual(body[5]**2+1.5*water[2]**2+water[10],1,places=9)
  metadata=self.scene.info()['surfaceFluidAngular'][0];self.assertTrue(metadata['active']);self.assertFalse(metadata['exported']);self.assertAlmostEqual(metadata['omega'][1],water[2],delta=5.1e-7);self.assertEqual(metadata['history']['exports'],0)
  before=self.scene.snapshot();self.scene.render();self.assertEqual(self.scene.snapshot(),before)
  self.scene.restore(start);self.assertEqual(self.scene.surface_fluid_angular(1),[3,0,0,0,0,0,0,0,0,0,0,0])
 def test_host_partition_and_snapshot_replay_preserve_angular_state(self):
  start=self.scene.snapshot();self.scene.advance_to(250000);finish=self.scene.snapshot()
  self.scene.restore(start)
  for time in [13000,51000,119000,187000,250000]:self.scene.advance_to(time)
  self.assertEqual(self.scene.snapshot(),finish)
 def test_rotated_water_normal_remains_in_snapshot_numeric_domain(self):
  # Tick six previously rounded an axis normal above +1, rolling back motion.
  for time in range(8334,250001,8334):
   self.scene.advance_to(time)
   normal=self.scene.float_body(1)[6:9]
   self.assertTrue(all(-1<=component<=1 for component in normal),normal)
   self.assertAlmostEqual(sum(component*component for component in normal),1,places=12)
  saved=self.scene.snapshot();self.scene.restore(saved)
  self.assertEqual(self.scene.snapshot(),saved)
 def test_stop_freezes_angular_reservoir_and_invalid_edits_are_atomic(self):
  self.scene.advance_to(8334);record=self.scene.surface_fluid_angular(1)
  self.scene.command(dict(op='stop-surface-fluid',surfaceId=1));stopped=self.scene.snapshot()
  self.scene.advance_to(250000);self.assertEqual(self.scene.surface_fluid_angular(1),record)
  self.scene.restore(stopped);self.assertEqual(self.scene.surface_fluid_angular(1),record)
  before=self.scene.snapshot()
  with self.assertRaises(ValueError):self.scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=0))
  self.assertEqual(self.scene.snapshot(),before)
 def test_export_archives_once_and_replacement_clears_live_angular_state(self):
  from test_angular_fluid_history import History
  self.scene.advance_to(8334);record=self.scene.surface_fluid_angular(1)
  self.scene.command(dict(op='export-surface-fluid',surfaceId=1));exported=self.scene.snapshot()
  metadata=self.scene.info()['surfaceFluidAngular'][0];self.assertTrue(metadata['exported']);self.assertFalse(metadata['active']);self.assertEqual(metadata['history']['exports'],1)
  history=History.from_buffer_copy(exported[24+13325432:24+13325432+112])
  self.assertEqual(history.exports,1);self.assertEqual(history.inertia,record[0]);self.assertAlmostEqual(history.energy,.5*record[0]*sum(x*x for x in record[1:4]));self.assertAlmostEqual(history.momentum.y,record[0]*record[2]);self.assertAlmostEqual(history.bodyImpulse.y,record[8]);self.assertAlmostEqual(history.dissipatedEnergy,record[10])
  self.scene.command(dict(op='export-surface-fluid',surfaceId=1));self.assertEqual(self.scene.snapshot(),exported)
  self.scene.command(dict(op='surface-fluid',surfaceId=1,mass=5));self.assertIsNone(self.scene.surface_fluid_angular(1))
  self.assertFalse(self.scene.info()['surfaceFluidAngular'][0]['recordPresent']);self.assertEqual(self.scene.info()['surfaceFluidAngular'][0]['history']['exports'],1)
  self.assertEqual(self.scene.snapshot()[24+13325432:24+13325432+112],exported[24+13325432:24+13325432+112])
  self.scene.restore(exported);self.assertEqual(self.scene.surface_fluid_angular(1),record)
 def test_blocked_angular_creation_survives_restore_and_can_be_cancelled(self):
  self.scene.command(dict(op='surface',id=2));self.scene.command(dict(op='surface-fluid',surfaceId=2,mass=4))
  self.scene.command(dict(op='schedule',id=1,atUs=1000000,command=dict(op='surface-fluid-angular',surfaceId=2,inertia=3)))
  self.scene.command(dict(op='surface-fluid-angular',surfaceId=2,inertia=4));blocked=self.scene.snapshot()
  self.scene.restore(blocked)
  with self.assertRaises(ValueError):self.scene.advance_to(1000000)
  self.assertEqual(self.scene.snapshot(),blocked)
  self.scene.command(dict(op='cancel-schedule',id=1));self.scene.advance_to(1000000);self.assertEqual(self.scene.surface_fluid_angular(2)[0],4)
