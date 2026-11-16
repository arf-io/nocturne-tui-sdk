"""Actual native fine physical cells, independent barycentric geometry and ledgers."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import math,struct,zlib,unittest
import test_surface_geometry as geometry
from nocturne_native import NativeScene
PARENT={'a':[0,0,0],'b':[8,0,0],'c':[0,0,8],'surfaceId':1,'color':0x5599cc,'alpha':.7}
def expected(n):
 def p(i,j):return [8*i/n,0,8*j/n]
 faces=[]
 for i in range(n):
  for j in range(n-i):
   faces.append([p(i,j),p(i+1,j),p(i,j+1)])
   if i+j<n-1:faces.append([p(i+1,j),p(i+1,j+1),p(i,j+1)])
 return faces
class MeshSubdivision(unittest.TestCase):
 def setup(self,s):
  s.command({'op':'floor','enabled':False});s.command({'op':'surface','id':1,'reentrainWindSpeed':0,'evaporation':0,'cooling':0,'thermalEvaporation':0})
 def mesh(self,s,n=2,**patch):s.command({'op':'mesh','triangles':[PARENT],'subdivisions':n,**patch})
 def test_independent_lattice_area_winding_and_default_exact_compatibility(self):
  for n in [1,2,3,4,16]:
   with self.subTest(n=n),NativeScene() as s:
    self.setup(s);self.mesh(s,n);rows=s.surface_triangles(1);self.assertEqual(len(rows),n*n);total=0
    for row,face in zip(rows,expected(n)):
     self.assertEqual(row[0],rows.index(row));self.assertEqual(row[10:],[0x5599cc,.7])
     for a,b in zip(row[1:10],sum(face,[])):self.assertAlmostEqual(a,b,places=12)
     a,b,c=[row[k:k+3] for k in [1,4,7]];cross=(b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]);self.assertLess(cross,0);self.assertAlmostEqual(-cross/2,32/(n*n),places=11);total-=cross/2
    self.assertAlmostEqual(total,32,places=10);before=s.snapshot();s.render();s.surface_triangles(1);self.assertEqual(s.snapshot(),before)
  with NativeScene() as a,NativeScene() as b:
   for s in [a,b]:self.setup(s)
   a.command({'op':'mesh','triangles':[PARENT]});self.mesh(b,1);self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(a.render().bytes,b.render().bytes)
 def test_reverse_adjacent_edges_have_identical_lattice_vertices(self):
  with NativeScene() as s:
   self.setup(s);other={'a':[8,0,0],'b':[0,0,0],'c':[8,0,-8],'surfaceId':1};s.command({'op':'mesh','triangles':[PARENT,other],'subdivisions':3});rows=s.surface_triangles(1);sets=[]
   for group in [rows[:9],rows[9:]]:sets.append({tuple(row[k:k+3]) for row in group for k in [1,4,7] if row[k+2]==0})
   self.assertEqual(sets[0],sets[1]);self.assertEqual(len(sets[0]),4)
 def test_centroid_contacts_reach_distinct_physical_thermal_cells(self):
  with NativeScene() as s:
   self.setup(s);wall={'a':[0,0,0],'b':[0,8,0],'c':[0,0,8],'surfaceId':1};s.command({'op':'mesh','triangles':[wall],'subdivisions':2});s.command({'op':'material','id':1});s.command({'op':'material-thermal','id':1,'temperature':500,'capacity':10});g=geometry.SurfaceGeometry();g.scene=s
   for i,row in enumerate(s.surface_triangles(1)):
    s.command({'op':'surface-thermal','triangleIndex':i,'temperature':200+50*i,'capacity':25});y=sum(row[k] for k in [2,5,8])/3;z=sum(row[k] for k in [3,6,9])/3;g.particle(id=i+1,material=1,position=[1,y,z],deposit=True)
   s.advance_to(8333);deposits=s.info()['deposits'];self.assertEqual(len(deposits),4)
   for deposit in deposits:
    face=expected(2)[deposit['emitterId']-1];y=sum(p[0] for p in face)/3;z=sum(p[2] for p in face)/3;self.assertAlmostEqual(deposit['position'][0],.02,places=5);self.assertAlmostEqual(deposit['position'][1],y,delta=.001);self.assertAlmostEqual(deposit['position'][2],z,delta=.001)
   for i in range(4):self.assertAlmostEqual(s.thermal_sample(i)[0],200+50*i+(500-200-50*i)*10/35,places=5)
   q=s.info()['materialThermal'];self.assertAlmostEqual(q['initialEnergy']+q['importedEnergy'],q['liveEnergy']+q['transferredEnergy']+q['exportedEnergy'],places=5)
 def test_append_preserves_ownership_and_replacement_accounts_retirement(self):
  with NativeScene() as s:
   self.setup(s);self.mesh(s,1);s.command({'op':'surface-water','surfaceId':1,'capacity':1});s.command({'op':'surface-water-add','triangleIndex':0,'volume':.5});s.command({'op':'surface-thermal','triangleIndex':0,'temperature':300,'capacity':100});before=s.water_sample(0);self.mesh(s,2,append=True);self.assertEqual(s.water_sample(0),before);self.assertEqual(s.thermal_sample(0)[1],30000)
   for i in range(1,5):self.assertEqual(s.water_sample(i)[2],0);self.assertIsNone(s.thermal_sample(i))
   self.mesh(s,4);info=s.info();self.assertAlmostEqual(info['surfaceWater'][0]['exportedVolume'],.5);self.assertEqual(info['surfaceThermal']['exportedEnergy'],30000)
 def test_expanded_capacity_invalid_precision_and_sampling_rollback(self):
  with NativeScene() as s:
   self.setup(s);self.mesh(s,1);before=s.snapshot()
   for command in [{'op':'mesh','triangles':[PARENT],'subdivisions':v} for v in [0,-1,1.5,17,'two']]+[{'op':'mesh','triangles':[PARENT,PARENT],'subdivisions':16},{'op':'mesh','triangles':[PARENT],'subdivisions':16,'append':True},{'op':'mesh','sampling':'braille','subdivisions':2},{'op':'mesh','triangles':[{'a':[0,0,0],'b':[.001,0,0],'c':[0,0,.001]}],'subdivisions':16}]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(s.snapshot(),before)
   s.command({'op':'mesh','sampling':'braille'});self.assertEqual(len(s.surface_triangles(1)),1)
 def test_scheduler_partition_replay_and_old_queued_feature_guard(self):
  with NativeScene() as s:
   self.setup(s);s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'mesh','triangles':[PARENT],'subdivisions':3}]}});start=s.snapshot();s.advance_to(1000000);done=s.snapshot();self.assertEqual(len(s.surface_triangles(1)),9);s.restore(start)
   for t in [100000,499999,500000,750000,1000000]:s.advance_to(t)
   self.assertEqual(s.snapshot(),done);old=bytearray(start[:13478976]);struct.pack_into('<I',old,16,13478952)
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261045)
   struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),done)
   old=bytearray(done[:13478976]);struct.pack_into('<I',old,16,13478952)
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261045)
   struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff);s.restore(old);self.assertEqual(s.snapshot()[32:13478976],done[32:13478976]);self.assertEqual(len(s.snapshot()),snapshot_size(s))
