"""Retained pose lifecycle and frozen schema-40 migration; deferred scenic gate."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import ctypes as C
import math,struct,unittest,zlib
from test_hull_immersion import NativeScene
from test_surface_pose import Vec

POSE=24+13327224
class Triangle(C.Structure):
 _fields_=[('a',Vec),('b',Vec),('c',Vec),('color',C.c_uint32),('alpha',C.c_double)]
class Hit(C.Structure):
 _fields_=[('surfaceId',C.c_int),('triangleIndex',C.c_int),('fraction',C.c_double),('position',Vec),('normal',Vec),('surfaceVelocity',Vec)]
class RetainedSurfacePose(unittest.TestCase):
 def setup_scene(self,scene):
  for command in [dict(op='surface',id=1),dict(op='surface-fluid',surfaceId=1,mass=3),dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[0,0,math.pi])]:scene.command(command)
 def row(self,scene):return struct.unpack_from('<II7d',scene.snapshot(),POSE)
 def test_rotated_rising_flow_vertex_velocities_match_timed_contact_frame(self):
  from test_flow_thickness import setup
  with NativeScene() as scene:
   setup(scene,tail=10000);scene.command(dict(op='surface-fluid',surfaceId=1,mass=3,velocity=[.1,.2,.3]));scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[0,0,.25],orientation=[0,0,math.sqrt(.5),math.sqrt(.5)]));scene.advance_to(8334);before=scene.snapshot()
   state=C.create_string_buffer(before[24:]);sample=scene._lib.nrSurfaceTriangleAtTime;sample.argtypes=[C.c_void_p,C.c_int,C.c_double,C.POINTER(Triangle),C.POINTER(Vec)];sample.restype=C.c_int
   velocity=scene._lib.nrSurfaceTriangleVelocity;velocity.argtypes=[C.c_void_p,C.c_int,Vec];velocity.restype=Vec
   # Current clock is retained in integer microseconds; the timed endpoint and
   # owned geometry query must describe the same vertices and material rates.
   seconds=scene.info()['clock']['timeUs']/1000000
   for row in scene.surface_triangles(1):
    triangle=Triangle();rates=(Vec*3)();self.assertEqual(sample(state,int(row[0]),seconds,C.byref(triangle),rates),1)
    for point,rate,offset in zip([triangle.a,triangle.b,triangle.c],rates,[1,4,7]):
     for actual,expected in zip([point.x,point.y,point.z],row[offset:offset+3]):self.assertAlmostEqual(actual,expected,places=10)
     material=velocity(state,int(row[0]),point)
     for actual,expected in zip([material.x,material.y,material.z],[rate.x,rate.y,rate.z]):self.assertAlmostEqual(actual,expected,places=8)
   self.assertEqual(scene.snapshot(),before)
 def test_buoyancy_height_and_posed_query_share_edge_tolerance_and_velocity(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]));before=scene.snapshot()
   state=C.create_string_buffer(before[24:]);query=scene._lib.nrWaterHeight;query.argtypes=[C.c_void_p,C.c_int,C.c_double,C.c_double,C.POINTER(C.c_double)];query.restype=C.c_int
   for x,z in [(.5,.5),(-1e-11,.5),(1,1)]:
    output=(C.c_double*5)();self.assertEqual(query(state,1,x,z,output),1)
    self.assertEqual(list(output),scene.surface_wave_sample(1,x,z)[:5])
   output=(C.c_double*5)(*([777]*5));self.assertEqual(query(state,1,10,10,output),0);self.assertEqual(list(output),[777]*5);self.assertEqual(scene.snapshot(),before)
 def test_wave_query_invalid_and_uncovered_outputs_are_atomic(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]))
   query=scene._lib.nrSurfaceWaveSample;query.argtypes=[C.c_void_p,C.c_uint32,C.c_double,C.c_double,C.POINTER(C.c_double),C.c_uint32];query.restype=C.c_int
   output=(C.c_double*6)(*([777]*6));before=scene.snapshot()
   for x,z,capacity in [(10,10,6),(float('nan'),0,6),(.5,.5,5)]:
    self.assertEqual(query(scene._context,1,x,z,output,capacity),-1);self.assertEqual(list(output),[777]*6)
   self.assertEqual(scene.snapshot(),before)
 def test_grazing_edge_tolerance_and_nearby_miss_preserve_outputs(self):
  with NativeScene() as scene:
   scene.command(dict(op='surface',id=1));scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]));scene.command(dict(op='surface-fluid',surfaceId=1,mass=3));scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3))
   state=C.create_string_buffer(scene.snapshot()[24:]);query=scene._lib.nrRotatingSurfaceHit
   query.argtypes=[C.c_void_p,C.c_int,Vec,Vec,C.c_double,C.c_double,C.c_double,C.POINTER(Hit)];query.restype=C.c_int
   hit=Hit();self.assertEqual(query(state,0,Vec(-1,0,0),Vec(1,0,0),0,1,1,C.byref(hit)),1);self.assertAlmostEqual(hit.fraction,.5,places=7)
   previous=bytes(hit)
   self.assertEqual(query(state,0,Vec(-1,1e-5,0),Vec(1,1e-5,0),0,1,1,C.byref(hit)),0);self.assertEqual(bytes(hit),previous)
   self.assertEqual(query(state,0,Vec(0,1,0),Vec(0,-1,0),0,1,1,C.byref(hit)),1);self.assertAlmostEqual(hit.fraction,.5,places=7)
   previous=bytes(hit);self.assertEqual(query(state,0,Vec(),Vec(),0,0,1,C.byref(hit)),-1);self.assertEqual(bytes(hit),previous)
 def test_contact_invalid_vectors_times_and_alignment_leave_output_unchanged(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]));before=scene.snapshot()
   state=C.create_string_buffer(before[24:]);query=scene._lib.nrRotatingSurfaceHit
   query.argtypes=[C.c_void_p,C.c_int,Vec,Vec,C.c_double,C.c_double,C.c_double,C.POINTER(Hit)];query.restype=C.c_int
   hit=Hit();C.memset(C.byref(hit),0xaa,C.sizeof(hit));previous=bytes(hit)
   valid=(Vec(.5,1,.5),Vec(.5,-1,.5),0,1,1)
   for invalid in [float('nan'),float('inf'),-float('inf')]:
    for vector in [0,1]:
     for axis in ['x','y','z']:
      args=[Vec(.5,1,.5),Vec(.5,-1,.5),0,1,1];setattr(args[vector],axis,invalid)
      self.assertEqual(query(state,0,*args,C.byref(hit)),-1);self.assertEqual(bytes(hit),previous)
    for field in [2,3,4]:
     args=list(valid);args[field]=invalid;self.assertEqual(query(state,0,*args,C.byref(hit)),-1);self.assertEqual(bytes(hit),previous)
   for start,duration in [(1000000,1),(999999,2)]:
    self.assertEqual(query(state,0,valid[0],valid[1],start,duration,1,C.byref(hit)),-1);self.assertEqual(bytes(hit),previous)
   raw=(C.c_ubyte*(C.sizeof(Hit)+1))(*([0xaa]*(C.sizeof(Hit)+1)));misaligned=C.cast(C.addressof(raw)+1,C.POINTER(Hit));saved=bytes(raw)
   self.assertEqual(query(state,0,*valid,misaligned),-1);self.assertEqual(bytes(raw),saved);self.assertEqual(scene.snapshot(),before)
 def test_authored_pivot_and_orientation_transform_shared_geometry(self):
  with NativeScene() as scene:
   scene.command(dict(op='surface',id=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=3))
   scene.command(dict(op='mesh',triangles=[dict(a=[12,20,30],b=[13,20,30],c=[12,20,31],surfaceId=1)]))
   scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3,pivot=[10,20,30],orientation=[0,0,math.sqrt(.5),math.sqrt(.5)]))
   expected=[10,22,30,10,23,30,10,22,31]
   for actual,reference in zip(scene.surface_triangles(1)[0][1:10],expected):self.assertAlmostEqual(actual,reference,places=10)
   saved=scene.snapshot();scene.restore(saved);self.assertEqual(scene.snapshot(),saved);self.assertEqual(scene.info()['surfaceFluidAngular'][0]['pose']['pivot'],[10,20,30])
   scene.command(dict(op='export-surface-fluid',surfaceId=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=4))
   for actual,reference in zip(scene.surface_triangles(1)[0][1:10],[12,20,30,13,20,30,12,20,31]):self.assertAlmostEqual(actual,reference,places=10)
   replaced=scene.snapshot();scene.restore(replaced);self.assertEqual(scene.snapshot(),replaced)
   scene.restore(saved);self.assertEqual(scene.snapshot(),saved)
 def test_invalid_pose_authoring_is_atomic(self):
  for fields in [dict(pivot=[1,2]),dict(pivot=[0,0,float('inf')]),dict(orientation=[0,0,0,2]),dict(orientation=[0,0,1]),dict(pivot=[16001,0,0])]:
   with self.subTest(fields=fields),NativeScene() as scene:
    scene.command(dict(op='surface',id=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=3));before=scene.snapshot()
    with self.assertRaises(ValueError):scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3,**fields))
    self.assertEqual(scene.snapshot(),before)
 def test_schema_40_rejects_pending_explicit_pose_fields(self):
  with NativeScene() as scene:
   scene.command(dict(op='surface',id=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=3))
   scene.command(dict(op='schedule',id=1,atUs=1000000,command=dict(op='batch',commands=[dict(op='surface-fluid-angular',surfaceId=1,inertia=3,pivot=[0,0,0])])))
   valid=scene.snapshot();old=bytearray(valid[:POSE]);struct.pack_into('<I',old,12,0x20261040);struct.pack_into('<I',old,16,13327224);struct.pack_into('<I',old,28,0x20261040);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   with self.assertRaises(ValueError):scene.restore(old)
   self.assertEqual(scene.snapshot(),valid)
 def test_pose_metadata_is_owned_and_matches_retained_orientation(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.advance_to(250000);before=scene.snapshot();pose=scene.info()['surfaceFluidAngular'][0]['pose']
   contract=scene.info()['contract']['queryContracts']['nrSurfaceWaveSample'];self.assertEqual(contract['rowWords'],6);self.assertEqual(contract['modeSelector'],'surfaceFluidAngular[].pose');self.assertEqual(contract['posedMode']['verticalVelocity'],'material-world-y');self.assertEqual(contract['posedMode']['coverage'],'topmost-world-facet');self.assertEqual(contract['analyticMode']['laplacian'],'analytic-authored-xz');self.assertTrue(contract['invalidOutputUnchanged'])
   for actual,reference in zip(pose['orientation'],self.row(scene)[2:6]):self.assertAlmostEqual(actual,reference,delta=5.1e-7)
   self.assertEqual(pose['pivot'],[0,0,0]);pose['orientation'][0]=999
   self.assertEqual(scene.info()['surfaceFluidAngular'][0]['pose']['orientation'][0],0);self.assertEqual(scene.snapshot(),before)
   scene.command(dict(op='export-surface-fluid',surfaceId=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=4));self.assertIsNone(scene.info()['surfaceFluidAngular'][0]['pose'])
 def test_complete_revolution_and_constant_wave_interior_contacts(self):
  for wave in [False,True]:
   with self.subTest(wave=wave),NativeScene() as scene:
    scene.command(dict(op='surface',id=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=3));scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[0,0,2*math.pi]))
    scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]))
    if wave:scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,0,0,0,0]]))
    scene.advance_to(1000000);before=scene.snapshot();state=C.create_string_buffer(before[24:]);query=scene._lib.nrRotatingSurfaceHit
    query.argtypes=[C.c_void_p,C.c_int,Vec,Vec,C.c_double,C.c_double,C.c_double,C.POINTER(Hit)];query.restype=C.c_int
    point=Vec(.5,1.5 if wave else .5,.5);hit=Hit()
    self.assertEqual(query(state,0,point,point,0,1,1,C.byref(hit)),1)
    angle=math.acos(1/math.sqrt(2.5))-math.atan(1/3) if wave else math.pi/4
    self.assertAlmostEqual(hit.fraction,angle/(2*math.pi),places=7);self.assertEqual(scene.snapshot(),before)
    # Explicit initial edge overlap is reported at zero time.
    if not wave:
     point=Vec(2,0,0);self.assertEqual(query(state,0,point,point,0,1,1,C.byref(hit)),1);self.assertEqual(hit.fraction,0)
 def test_rotating_contact_search_finds_independent_stationary_point_crossing(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]));scene.advance_to(500000)
   before=scene.snapshot();state=C.create_string_buffer(before[24:]);query=scene._lib.nrRotatingSurfaceHit
   query.argtypes=[C.c_void_p,C.c_int,Vec,Vec,C.c_double,C.c_double,C.c_double,C.POINTER(Hit)];query.restype=C.c_int
   hit=Hit();point=Vec(.5,.5,.5)
   self.assertEqual(query(state,0,point,point,0,.5,1,C.byref(hit)),1)
   self.assertAlmostEqual(hit.fraction,.5,places=7);self.assertEqual(hit.surfaceId,1);self.assertEqual(hit.triangleIndex,0)
   for actual,reference in zip([hit.normal.x,hit.normal.y,hit.normal.z],[-math.sqrt(.5),math.sqrt(.5),0]):self.assertAlmostEqual(actual,reference,places=7)
   self.assertAlmostEqual(hit.surfaceVelocity.x,-math.pi*.5,places=7);self.assertAlmostEqual(hit.surfaceVelocity.y,math.pi*.5,places=7)
   previous=bytes(hit);self.assertEqual(query(state,0,point,point,0,.5,.49,C.byref(hit)),0);self.assertEqual(bytes(hit),previous)
   self.assertEqual(query(state,0,Vec(10,10,10),Vec(10,10,10),0,.5,1,C.byref(hit)),0);self.assertEqual(bytes(hit),previous);self.assertEqual(scene.snapshot(),before)
 def test_collision_time_frame_extrapolates_rotation_and_vertex_velocity(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.command(dict(op='mesh',triangles=[dict(a=[1,0,0],b=[2,0,0],c=[1,0,1],surfaceId=1)]));scene.advance_to(500000)
   before=scene.snapshot();state=C.create_string_buffer(before[24:]);original=bytes(state)
   query=scene._lib.nrSurfaceTriangleAtTime;query.argtypes=[C.c_void_p,C.c_int,C.c_double,C.POINTER(Triangle),C.POINTER(Vec)];query.restype=C.c_int
   triangle=Triangle();velocities=(Vec*3)()
   for time in [0,.25,.5]:
    self.assertEqual(query(state,0,time,C.byref(triangle),velocities),1)
    sine=math.sin(math.pi*time);cosine=math.cos(math.pi*time)
    for vertex,velocity,radius,z in [(triangle.a,velocities[0],1,0),(triangle.b,velocities[1],2,0),(triangle.c,velocities[2],1,1)]:
     for actual,reference in zip([vertex.x,vertex.y,vertex.z,velocity.x,velocity.y,velocity.z],[radius*cosine,radius*sine,z,-math.pi*radius*sine,math.pi*radius*cosine,0]):self.assertAlmostEqual(actual,reference,places=10)
   self.assertEqual(bytes(state),original);self.assertEqual(scene.snapshot(),before)
   oldTriangle=bytes(triangle);oldVelocities=bytes(velocities)
   self.assertEqual(query(state,999,.25,C.byref(triangle),velocities),-1);self.assertEqual(bytes(triangle),oldTriangle);self.assertEqual(bytes(velocities),oldVelocities)
 def test_rotated_height_query_uses_topmost_facet_and_world_velocity(self):
  with NativeScene() as scene:
   self.setup_scene(scene)
   scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1)]))
   scene.advance_to(250000);before=scene.snapshot();row=scene.surface_wave_sample(1,.5,.5)
   self.assertAlmostEqual(row[0],.5,places=10)
   for actual,reference in zip(row[1:4],[-math.sqrt(.5),math.sqrt(.5),0]):self.assertAlmostEqual(actual,reference,places=10)
   self.assertAlmostEqual(row[4],math.pi*.5,places=10);self.assertEqual(row[5],0);self.assertEqual(scene.snapshot(),before)
   with self.assertRaises(ValueError):scene.surface_wave_sample(1,10,10)
   scene.advance_to(500000)
   with self.assertRaises(ValueError):scene.surface_wave_sample(1,0,.5)
 def test_projected_overlap_selects_highest_surface(self):
  with NativeScene() as scene:
   self.setup_scene(scene)
   scene.command(dict(op='mesh',triangles=[dict(a=[0,y,0],b=[2,y,0],c=[0,y,2],surfaceId=1) for y in [1,3]]))
   self.assertAlmostEqual(scene.surface_wave_sample(1,.5,.5)[0],3)
 def test_world_contact_velocity_includes_rotation_and_freezes_after_stop(self):
  with NativeScene() as scene:
   self.setup_scene(scene);scene.command(dict(op='mesh',triangles=[dict(a=[1,0,0],b=[2,0,0],c=[1,0,1],surfaceId=1)]));scene.advance_to(500000)
   query=scene._lib.nrSurfaceTriangleVelocity;query.argtypes=[C.c_void_p,C.c_int,Vec];query.restype=Vec
   before=scene.snapshot();state=C.create_string_buffer(before[24:]);value=query(state,0,Vec(0,1,0))
   self.assertAlmostEqual(value.x,-math.pi,places=11);self.assertAlmostEqual(value.y,0,places=11);self.assertAlmostEqual(value.z,0,places=11);self.assertEqual(scene.snapshot(),before)
   scene.command(dict(op='stop-surface-fluid',surfaceId=1));state=C.create_string_buffer(scene.snapshot()[24:]);value=query(state,0,Vec(0,1,0));self.assertEqual((value.x,value.y,value.z),(0,0,0))
 def test_shared_triangle_geometry_rotates_authored_vertices(self):
  with NativeScene() as scene:
   self.setup_scene(scene)
   scene.command(dict(op='mesh',triangles=[dict(a=[1,0,0],b=[2,0,0],c=[1,0,1],surfaceId=1)]))
   start=scene.snapshot();scene.advance_to(500000);before=scene.snapshot();rows=scene.surface_triangles(1)
   self.assertEqual(len(rows),1)
   # The query prefixes the source triangle index; coordinate layout is
   # pinned by the native surface-triangle query contract.
   for actual,reference in zip(rows[0][1:10],[0,1,0,0,2,0,0,1,1]):self.assertAlmostEqual(actual,reference,places=10)
   self.assertEqual(scene.snapshot(),before)
   scene.restore(start);scene.advance_to(500000);self.assertEqual(scene.surface_triangles(1),rows)
 def test_rotation_partition_replay_and_freeze(self):
  with NativeScene() as scene:
   self.setup_scene(scene);start=scene.snapshot();self.assertEqual(self.row(scene),(1,0,0,0,0,1,0,0,0))
   scene.advance_to(500000);finish=scene.snapshot();row=self.row(scene)
   for actual,reference in zip(row[2:6],[0,0,math.sqrt(.5),math.sqrt(.5)]):self.assertAlmostEqual(actual,reference,places=11)
   scene.render();self.assertEqual(scene.snapshot(),finish)
   scene.restore(start)
   for time in [13000,170000,251000,500000]:scene.advance_to(time)
   self.assertEqual(scene.snapshot(),finish)
   scene.command(dict(op='stop-surface-fluid',surfaceId=1));stopped=self.row(scene);scene.advance_to(1000000);self.assertEqual(self.row(scene),stopped)
   scene.command(dict(op='export-surface-fluid',surfaceId=1));exported=self.row(scene);scene.advance_to(1500000);self.assertEqual(self.row(scene),exported)
   scene.command(dict(op='surface-fluid',surfaceId=1,mass=4));self.assertEqual(scene.snapshot()[POSE:POSE+64],bytes(64))
 def test_schema_40_promotes_identity_pose_without_altering_source_prefix(self):
  with NativeScene() as scene:
   self.setup_scene(scene);old=bytearray(scene.snapshot()[:POSE]);struct.pack_into('<I',old,12,0x20261040);struct.pack_into('<I',old,16,13327224);struct.pack_into('<I',old,28,0x20261040);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   scene.restore(old);promoted=scene.snapshot();self.assertEqual(len(promoted),snapshot_size(scene));self.assertEqual(promoted[32:POSE],old[32:]);self.assertEqual(self.row(scene),(1,0,0,0,0,1,0,0,0));self.assertEqual(promoted[POSE+64:24+13497384],bytes(170096))
 def test_checksum_correct_invalid_pose_rejects_atomically(self):
  with NativeScene() as scene:
   self.setup_scene(scene);valid=scene.snapshot()
   for offset,fmt,value in [(POSE,'I',2),(POSE+4,'I',1),(POSE+8,'d',float('nan')),(POSE+32,'d',2),(POSE+40,'d',float('inf'))]:
    bad=bytearray(valid);struct.pack_into('<'+fmt,bad,offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
    with self.assertRaises(ValueError):scene.restore(bad)
    self.assertEqual(scene.snapshot(),valid)
