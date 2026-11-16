"""Finite water storage/query/migration contracts; motion integration is next."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import ctypes as C
import math,struct,zlib,unittest
from test_hull_immersion import NativeScene
class SurfaceFluid(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.scene.command({'op':'surface','id':1});self.fn=self.scene._lib.nrSurfaceFluid
  self.fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];self.fn.restype=C.c_int
 def test_finite_mass_record_initial_momentum_and_owned_copy(self):
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3,'velocity':[1,2,3]});before=self.scene.snapshot();out=(C.c_double*15)();self.assertEqual(self.fn(self.scene._context,1,out,15),1);self.assertEqual(list(out),[3,1,2,3,0,0,0,3,6,9,0,0,0,0,21]);out[0]=999;self.assertEqual(self.scene.snapshot(),before);self.scene.restore(before);self.assertEqual(self.fn(self.scene._context,1,out,15),1);self.assertEqual(out[0],3)
 def test_invalid_and_reconfiguration_are_atomic(self):
  before=self.scene.snapshot()
  for command in [{'op':'surface-fluid','surfaceId':1,'mass':0},{'op':'surface-fluid','surfaceId':2,'mass':3},{'op':'surface-fluid','surfaceId':1,'mass':3,'velocity':[1,2]},{'op':'surface-fluid','surfaceId':1,'mass':3,'unexpected':True}]:
   with self.assertRaises(ValueError):self.scene.command(command)
   self.assertEqual(self.scene.snapshot(),before)
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3});before=self.scene.snapshot()
  with self.assertRaises(ValueError):self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':4})
  self.assertEqual(self.scene.snapshot(),before)
  out=(C.c_double*15)(*([777]*15));self.assertEqual(self.fn(self.scene._context,1,out,14),-1);self.assertEqual(list(out),[777]*15)
  self.assertEqual(self.fn(self.scene._context,1,C.cast(self.scene._context,C.POINTER(C.c_double)),15),-1);self.assertEqual(self.scene.snapshot(),before)
 def test_schema_36_migrates_empty_fluid_footer(self):
  old=bytearray(self.scene.snapshot()[:24+13319928]);struct.pack_into('<I',old,12,0x20261036);struct.pack_into('<I',old,16,len(old)-24);struct.pack_into('<I',old,28,0x20261036);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
  self.scene.restore(old);new=self.scene.snapshot();self.assertEqual(len(new),snapshot_size(self.scene));self.assertEqual(new[24+13319928:24+13497384],bytes(177456));self.assertEqual(struct.unpack_from('<I',new,12)[0],current_schema())
  self.assertEqual(new[24+13497384:24+13497392],struct.pack('<ii',0,1))

 def test_reciprocal_hull_exchange_geometry_motion_and_replay(self):
  from test_hull_immersion import BOX,FACES
  self.scene.command({'op':'mesh','triangles':[{'a':[-20,0,-20],'b':[20,0,-20],'c':[20,0,20],'surfaceId':1},{'a':[-20,0,-20],'b':[20,0,20],'c':[-20,0,20],'surfaceId':1}]})
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3});self.scene.command({'op':'float-body','id':1,'surfaceId':1,'mass':2,'gravity':0,'drag':2,'velocity':[1,0,0]});self.scene.command({'op':'float-hull','id':1,'vertices':BOX,'faces':FACES,'inertia':[1,1,1]});start=self.scene.snapshot();self.scene.advance_to(8334)
  body=self.scene.float_body(1);out=(C.c_double*15)();self.assertEqual(self.fn(self.scene._context,1,out,15),1);f=-math.expm1(-2/120*(1/2+1/3));self.assertAlmostEqual(body[3],1-.6*f,places=9);self.assertAlmostEqual(out[1],.4*f,places=9);self.assertAlmostEqual(out[10],1.2*f,places=9);self.assertAlmostEqual(out[13],.6*f*(2-f),places=9);self.assertAlmostEqual(2*body[3]+3*out[1],2)
  self.scene.advance_to(16667);self.assertEqual(self.fn(self.scene._context,1,out,15),1);self.assertGreater(out[4],0)
  geometry=self.scene.surface_triangles(1);self.assertAlmostEqual(geometry[0][1],-20+out[4]);before=self.scene.snapshot();self.scene.render();self.assertEqual(self.scene.snapshot(),before)
  self.scene.restore(start);self.scene.advance_to(250000);finish=self.scene.snapshot();self.scene.restore(start)
  for t in [13000,51000,119000,187000,250000]:self.scene.advance_to(t)
  self.assertEqual(self.scene.snapshot(),finish)

 def test_owned_binding_is_pure(self):
  self.assertIsNone(self.scene.surface_fluid(1));self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3,'velocity':[1,2,3]});before=self.scene.snapshot()
  row=self.scene.surface_fluid(1);self.assertEqual(row,[3,1,2,3,0,0,0,3,6,9,0,0,0,0,21]);row[0]=999;self.assertEqual(self.scene.surface_fluid(1)[0],3);self.assertEqual(self.scene.snapshot(),before)
 def test_stop_freezes_pose_and_preserves_momentum_ledger(self):
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3,'velocity':[1,2,3]});self.scene.advance_to(250000);record=self.scene.surface_fluid(1);self.scene.command({'op':'stop-surface-fluid','surfaceId':1});stopped=self.scene.snapshot();self.assertFalse(self.scene.info()['surfaceFluids'][0]['active']);self.assertEqual(self.scene.surface_fluid(1),record)
  self.scene.advance_to(500000);self.assertEqual(self.scene.surface_fluid(1),record);self.scene.restore(stopped);self.assertFalse(self.scene.info()['surfaceFluids'][0]['active']);self.scene.advance_to(500000);self.assertEqual(self.scene.surface_fluid(1),record)
  before=self.scene.snapshot()
  with self.assertRaises(ValueError):self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':4})
  self.assertEqual(self.scene.snapshot(),before)

 def test_runtime_discovery_contract_is_pure(self):
  before=self.scene.snapshot();contract=self.scene.info()['contract'];self.assertEqual(contract['queryContracts']['nrSurfaceFluid'],{'capacityUnit': 'double', 'rowWords': 15, 'alignmentBytes': 8, 'ownedBindings': True, 'pure': True, 'absentReturn': 0, 'presentReturn': 1, 'invalidReturn': -1, 'contextOverlapAllowed': False, 'fields': ['mass', 'velocity.x', 'velocity.y', 'velocity.z', 'offset.x', 'offset.y', 'offset.z', 'initialMomentum.x', 'initialMomentum.y', 'initialMomentum.z', 'bodyImpulse.x', 'bodyImpulse.y', 'bodyImpulse.z', 'dissipatedEnergy', 'initialEnergy'], 'lifecycleProperty': 'surfaceFluids[].active', 'stoppedRecordPresent': True})
  for feature in ['finite-water-motion','reciprocal-fluid-drag','finite-water-ledger']:self.assertIn(feature,contract['features'])
  self.assertEqual(self.scene.snapshot(),before)

 def test_export_once_and_replacement_preserve_history_and_pose(self):
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3,'velocity':[1,2,3]});self.scene.advance_to(250000);offset=self.scene.surface_fluid(1)[4:7];self.scene.command({'op':'export-surface-fluid','surfaceId':1});exported=self.scene.snapshot();metadata=self.scene.info()['surfaceFluids'][0];self.assertTrue(metadata['exported']);self.assertFalse(metadata['active']);history=metadata['history'];self.assertEqual(history,{'mass':3,'energy':21,'momentum':[3,6,9],'initialMomentum':[3,6,9],'bodyImpulse':[0,0,0],'initialEnergy':21,'dissipatedEnergy':0,'exports':1})
  self.scene.command({'op':'export-surface-fluid','surfaceId':1});self.assertEqual(self.scene.info()['surfaceFluids'][0]['history'],history)
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':5,'velocity':[-1,0,0]});self.assertEqual(self.scene.surface_fluid(1)[4:7],offset);self.assertEqual(self.scene.info()['surfaceFluids'][0]['history'],history);self.assertFalse(self.scene.info()['surfaceFluids'][0]['exported'])
  self.scene.command({'op':'export-surface-fluid','surfaceId':1});final=self.scene.snapshot();combined=self.scene.info()['surfaceFluids'][0]['history'];self.assertEqual(combined['mass'],8);self.assertEqual(combined['energy'],23.5);self.assertEqual(combined['momentum'],[-2,6,9]);self.assertEqual(combined['exports'],2)
  self.scene.restore(exported);self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':5,'velocity':[-1,0,0]});self.scene.command({'op':'export-surface-fluid','surfaceId':1});self.assertEqual(self.scene.snapshot(),final)
 def test_schema_37_migrates_empty_history(self):
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3,'velocity':[1,2,3]});old=bytearray(self.scene.snapshot()[:24+13321976]);struct.pack_into('<I',old,12,0x20261037);struct.pack_into('<I',old,16,len(old)-24);struct.pack_into('<I',old,28,0x20261037);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
  self.scene.restore(old);new=self.scene.snapshot();self.assertEqual(len(new),snapshot_size(self.scene));self.assertEqual(new[24+13321976:24+13497384],bytes(175408));self.assertEqual(self.scene.info()['surfaceFluids'][0]['history']['exports'],0)
  self.assertEqual(struct.unpack_from('<I',new,12)[0],current_schema())
  self.assertEqual(new[24+13497384:24+13497392],struct.pack('<ii',0,1))
 def test_creation_blocked_by_later_configuration_can_restore_and_cancel(self):
  self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'surface-fluid','surfaceId':1,'mass':3}});self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':4});blocked=self.scene.snapshot();self.scene.restore(blocked)
  with self.assertRaises(ValueError):self.scene.advance_to(500000)
  self.assertEqual(self.scene.snapshot(),blocked);self.scene.restore(blocked);self.scene.command({'op':'cancel-schedule','id':1});self.scene.advance_to(500000);self.assertEqual(self.scene.surface_fluid(1)[0],4)
 def test_blocked_recovery_rejects_malformed_queued_mass(self):
  self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'surface-fluid','surfaceId':1,'mass':3}});self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':4});before=self.scene.snapshot();bad=bytearray(before);needle=b'"mass":3';at=bad.find(needle);self.assertGreater(at,24);bad[at:at+len(needle)]=b'"mass":0';struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
  with self.assertRaises(ValueError):self.scene.restore(bad)
  self.assertEqual(self.scene.snapshot(),before)
 def test_export_queue_rejects_checksum_correct_pre_history_schema(self):
  self.scene.command({'op':'surface-fluid','surfaceId':1,'mass':3});self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'export-surface-fluid','surfaceId':1}});before=self.scene.snapshot();old=bytearray(before[:24+13321976]);struct.pack_into('<I',old,12,0x20261037);struct.pack_into('<I',old,16,len(old)-24);struct.pack_into('<I',old,28,0x20261037);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
  with self.assertRaises(ValueError):self.scene.restore(old)
  self.assertEqual(self.scene.snapshot(),before)
