"""Retained hull authoring, ownership and exact schema-35 migration contracts."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import ctypes as C
import struct,zlib,unittest
from test_hull_immersion import BOX,FACES,NativeScene
class RetainedFloatHulls(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.scene.command({'op':'surface','id':1});self.scene.command({'op':'float-body','id':1,'surfaceId':1})
 def hull(self,**changes):return dict(op='float-hull',id=1,vertices=BOX,faces=FACES,inertia=[100,100,100],**changes)
 def test_retained_snapshot_replay_and_atomic_geometry_rejection(self):
  before=self.scene.snapshot();self.scene.command(self.hull());saved=self.scene.snapshot();self.assertNotEqual(saved,before)
  self.scene.restore(saved);self.assertEqual(self.scene.snapshot(),saved)
  for changes in [{'faces':FACES[:-1]},{'orientation':[0,0,0,0]},{'inertia':[0,100,100]}]:
   command=self.hull();command.update(changes)
   with self.assertRaises(ValueError):self.scene.command(command)
   self.assertEqual(self.scene.snapshot(),saved)
  self.scene.command({'op':'remove-float-body','id':1});self.scene.restore(self.scene.snapshot())
 def test_old_prefix_migrates_empty_hull_footer(self):
  old=bytearray(self.scene.snapshot()[:24+12918520]);struct.pack_into('<I',old,12,0x20261035);struct.pack_into('<I',old,16,len(old)-24);struct.pack_into('<I',old,28,0x20261035);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
  self.scene.restore(old);new=self.scene.snapshot();self.assertEqual(len(new),snapshot_size(self.scene));self.assertEqual(struct.unpack_from('<I',new,12)[0],current_schema())
  self.assertEqual(new[24+12918520:24+13497384],bytes(578864))
  self.assertEqual(new[24+13497384:24+13497392],struct.pack('<ii',0,1))

 def water(self):
  self.scene.command({'op':'mesh','triangles':[{'a':[-20,0,-20],'b':[20,0,-20],'c':[20,0,20],'surfaceId':1},{'a':[-20,0,-20],'b':[20,0,20],'c':[-20,0,20],'surfaceId':1}]})
  self.scene.command({'op':'float-body','id':1,'surfaceId':1,'mass':4000,'gravity':10,'drag':0})
 def test_flow_prism_immersion_uses_free_surface_with_retained_rotation(self):
  import math
  from test_flow_thickness import setup
  for angle in [0,math.pi/4]:
   with self.subTest(angle=angle),NativeScene() as scene:
    setup(scene);q=[0,0,math.sin(angle/2),math.cos(angle/2)]
    if angle:
     scene.command(dict(op='surface-fluid',surfaceId=1,mass=3));scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3,orientation=q))
    scene.command(dict(op='float-body',id=1,surfaceId=1,position=[-.5*math.sin(angle),.5*math.cos(angle),-1],mass=2,gravity=0,drag=0))
    scene.command(dict(op='float-hull',id=1,vertices=[[.2*v for v in vertex] for vertex in BOX],faces=FACES,inertia=[100,100,100],orientation=q))
    start=scene.snapshot();scene.advance_to(8334);body=scene.float_body(1);self.assertAlmostEqual(body[9],.5,places=8)
    end=scene.snapshot();scene.render();self.assertEqual(scene.snapshot(),end);scene.restore(start);scene.advance_to(8334);self.assertEqual(scene.snapshot(),end)
 def test_neutral_box_uses_hull_volume_and_pure_render(self):
  self.water();self.scene.command(self.hull());self.scene.advance_to(500000)
  body=self.scene.float_body(1)
  for actual,expected in zip(body,[0,0,0,0,0,0,0,1,0,.5,40000,4000]):self.assertAlmostEqual(actual,expected)
  before=self.scene.snapshot();self.scene.render();self.assertEqual(self.scene.snapshot(),before)
 def test_off_axis_torque_first_step_and_partition_replay(self):
  self.water();self.scene.command(self.hull(centerOfMass=[.25,0,.5]));start=self.scene.snapshot();self.scene.advance_to(8334)
  h=self.scene.info()['floatBodies'][0]['hull']
  # Translating geometry by -centerOfMass moves the cut centroid by the same XZ.
  self.assertAlmostEqual(h['angularVelocity'][0],20000/100/120,places=5)
  self.assertAlmostEqual(h['angularVelocity'][2],-10000/100/120,places=5)
  self.assertNotEqual(h['orientation'],[0,0,0,1])
  self.scene.restore(start);self.scene.advance_to(250000);end=self.scene.snapshot();self.scene.restore(start)
  for t in [17000,43000,91000,153000,250000]:self.scene.advance_to(t)
  self.assertEqual(self.scene.snapshot(),end)

 def test_owned_pose_query_and_raw_output_guards(self):
  self.assertIsNone(self.scene.float_hull(1));self.scene.command(self.hull());before=self.scene.snapshot()
  expected=[0,0,0,1,0,0,0,100,100,100,0,0,0,8];row=self.scene.float_hull(1);self.assertEqual(row,expected);row[-1]=999;self.assertEqual(self.scene.float_hull(1),expected)
  fn=self.scene._lib.nrFloatHull;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_double),C.c_uint32];fn.restype=C.c_int
  out=(C.c_double*14)(*([777]*14));self.assertEqual(fn(self.scene._context,1,out,13),-1);self.assertEqual(list(out),[777]*14)
  self.assertEqual(fn(self.scene._context,1,C.cast(self.scene._context,C.POINTER(C.c_double)),14),-1);self.assertEqual(self.scene.snapshot(),before)
  self.scene.command({'op':'remove-float-hull','id':1});self.assertIsNone(self.scene.float_hull(1));self.assertEqual(fn(self.scene._context,1,out,14),0);self.assertEqual(list(out),[777]*14)
 def test_missing_body_queue_restores_and_cancels_but_live_execution_rejects(self):
  self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':self.hull()});self.scene.command({'op':'remove-float-body','id':1});blocked=self.scene.snapshot();self.scene.restore(blocked)
  with self.assertRaises(ValueError):self.scene.advance_to(500000)
  self.assertEqual(self.scene.snapshot(),blocked);self.scene.restore(blocked);self.scene.command({'op':'cancel-schedule','id':1});self.scene.advance_to(500000)
 def test_queued_hull_is_rejected_in_checksum_correct_pre_hull_schema(self):
  self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':self.hull()});before=self.scene.snapshot()
  old=bytearray(before[:24+12918520]);struct.pack_into('<I',old,12,0x20261035);struct.pack_into('<I',old,16,len(old)-24);struct.pack_into('<I',old,28,0x20261035);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
  with self.assertRaises(ValueError):self.scene.restore(old)
  self.assertEqual(self.scene.snapshot(),before)
 def test_recovery_does_not_accept_malformed_queued_inertia(self):
  self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':self.hull()});self.scene.command({'op':'remove-float-body','id':1});before=self.scene.snapshot()
  bad=bytearray(before);needle=b'"inertia":[100,100,100]';at=bad.find(needle);self.assertGreater(at,24);bad[at:at+len(needle)]=b'"inertia":[-10,100,100]';struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
  with self.assertRaises(ValueError):self.scene.restore(bad)
  self.assertEqual(self.scene.snapshot(),before)
 def test_nonplanar_v_surface_drives_shared_mesh_displacement(self):
  triangles=[]
  for x0,x1 in [(-2,0),(0,2)]:
   a=[x0,abs(x0),-2];b=[x1,abs(x1),-2];c=[x1,abs(x1),2];d=[x0,abs(x0),2]
   triangles.extend([{'a':a,'b':b,'c':c,'surfaceId':1},{'a':a,'b':c,'c':d,'surfaceId':1}])
  self.scene.command({'op':'mesh','triangles':triangles});self.scene.command({'op':'float-body','id':1,'mass':6000,'gravity':10,'drag':0});self.scene.command(self.hull());self.scene.advance_to(8334)
  body=self.scene.float_body(1);self.assertAlmostEqual(body[9],.75);self.assertAlmostEqual(body[10],60000);self.assertAlmostEqual(body[1],0);self.assertAlmostEqual(body[4],0)
 def test_hull_value_bindings_domains_and_dormant_recovery(self):
  self.scene.command(self.hull())
  for field,value,index in [('hull.angularVelocity.x',2,4),('hull.angularVelocity.y',-3,5),('hull.angularVelocity.z',4,6),('hull.inertia.x',1e10,7),('hull.inertia.y',200,8),('hull.inertia.z',300,9)]:
   path='/'+field;self.scene.command({'op':'define','path':path,'value':value,'binding':{'family':'float-body','id':1,'field':field}});self.assertEqual(self.scene.float_hull(1)[index],value)
   before=self.scene.snapshot()
   with self.assertRaises(ValueError):self.scene.command({'op':'set','path':path,'value':1001 if 'angularVelocity' in field else 0})
   self.assertEqual(self.scene.snapshot(),before)
   if value>1000000:self.scene.command({'op':'set','path':path,'value':500})
  self.scene.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'set','path':'/hull.inertia.x','value':500}});self.scene.command({'op':'remove-float-hull','id':1});blocked=self.scene.snapshot();self.scene.restore(blocked)
  with self.assertRaises(ValueError):self.scene.advance_to(500000)
  self.assertEqual(self.scene.snapshot(),blocked);self.scene.command({'op':'cancel-schedule','id':1})
  for field in ['hull.angularVelocity.x','hull.angularVelocity.y','hull.angularVelocity.z','hull.inertia.x','hull.inertia.y','hull.inertia.z']:self.scene.command({'op':'bind','path':'/'+field,'binding':None})
  self.scene.command({'op':'set','path':'/hull.inertia.x','value':1});self.scene.advance_to(500000)
 def test_pre_hull_binding_rejected_before_snapshot_promotion(self):
  self.scene.command(self.hull());self.scene.command({'op':'define','path':'/inertia','value':100,'binding':{'family':'float-body','id':1,'field':'hull.inertia.x'}});before=self.scene.snapshot()
  old=bytearray(before[:24+12918520]);struct.pack_into('<I',old,12,0x20261035);struct.pack_into('<I',old,16,len(old)-24);struct.pack_into('<I',old,28,0x20261035);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
  with self.assertRaises(ValueError):self.scene.restore(old)
  self.assertEqual(self.scene.snapshot(),before)
 def test_runtime_hull_contract_is_pure_and_explicit(self):
  before=self.scene.snapshot();contract=self.scene.info()['contract'];query=contract['queryContracts']['nrFloatHull']
  self.assertEqual(query,{'capacityUnit':'double','rowWords':14,'alignmentBytes':8,'ownedBindings':True,'pure':True,'absentReturn':0,'presentReturn':1,'invalidReturn':-1,'contextOverlapAllowed':False,'fields':['orientation.x','orientation.y','orientation.z','orientation.w','angularVelocity.x','angularVelocity.y','angularVelocity.z','inertia.x','inertia.y','inertia.z','centerOfMass.x','centerOfMass.y','centerOfMass.z','volume']})
  for feature in ['retained-convex-hulls','hull-pose-inspection','hull-value-bindings']:self.assertIn(feature,contract['features'])
  self.assertEqual(self.scene.snapshot(),before)
