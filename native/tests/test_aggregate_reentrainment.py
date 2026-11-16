"""Real aggregate material lifecycle; independent count/heat and provenance oracles."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import struct,zlib,unittest
import test_surface_geometry as geometry
from nocturne_native import NativeScene

class AggregateReentrainment(unittest.TestCase):
 def setup(self,s,heat=True,**surface):
  g=geometry.SurfaceGeometry();g.scene=s;s.command({'op':'floor','enabled':False});g.surface(maxIndividual=1,maxTiles=4,overflow='merge-to-field',**surface);g.mesh([g.wall()]);s.command({'op':'material','id':1})
  if heat:s.command({'op':'material-thermal','id':1,'temperature':500,'capacity':10,'contactFraction':.25,'conductance':20})
  g.particle(material=1,count=5,deposit=True,initialOrientation=[10,20,30],angularVelocity=[1,2,3]);s.advance_to(8333);return g
 def tiles(self,s):return s.info().get('aggregateMaterials',[])
 def reemit(self,s,n=2,**patch):s.command(dict(op='aggregate-reemit',tileIndex=0,count=n,velocity=[240,0,0],**patch))
 def balance(self,s):
  q=s.info_complete()['materialThermal'];self.assertAlmostEqual(q['initialEnergy']+q['importedEnergy'],q['liveEnergy']+q['transferredEnergy']+q['exportedEnergy'],places=5)
 def test_alone_and_application_count_heat_identity_and_prospective_capture(self):
  for application in [False,True]:
   with self.subTest(application=application),NativeScene() as s:
    self.setup(s)
    if application:
     s.command({'op':'window','id':90,'position':[10,4,-4],'width':32,'height':15,'title':'Owned aggregate cycle','text':'Retained matter returns'});s.command({'op':'text','id':90,'text':'Retained matter returns','x':3,'y':3});s.command({'op':'prompt','active':True});s.command({'op':'indicator','id':90,'x':4,'y':32,'sequence':'◐◓◑◒','stepMs':150})
    self.assertEqual(self.tiles(s)[0]['count'],4);births=s.info()['particles']['born'];initial=s.info()['materialThermal']['initialEnergy'];old_ids={d['id'] for d in s.info()['deposits']};s.command({'op':'material-thermal','id':1,'temperature':900,'capacity':100});before=s.snapshot();self.reemit(s);done=s.snapshot();q=s.info();self.assertEqual(q['particles']['born'],births);self.assertEqual(q['aggregateReemittedCount'],2);self.assertEqual(self.tiles(s)[0]['count'],2)
    rows=q['materialThermal']['particles'];self.assertEqual(len(rows),2);self.assertEqual(q['materialThermal']['initialEnergy'],initial)
    for row in rows:self.assertEqual(row['capacity'],10);self.assertEqual(row['temperature'],500);self.assertNotIn(row['id'],old_ids);self.assertEqual(row['contactFraction'],.25);self.assertEqual(row['conductance'],20)
    self.assertEqual(len({r['id'] for r in rows}),2);self.balance(s);s.render();s.info();self.assertEqual(s.snapshot(),done);s.restore(before);self.reemit(s);self.assertEqual(s.snapshot(),done);self.reemit(s);self.assertEqual(self.tiles(s),[]);self.assertEqual(s.info()['aggregateReemittedCount'],4);self.balance(s)
 def test_atomic_negative_count_fields_and_changed_or_removed_emitter(self):
  with NativeScene() as s:
   g=self.setup(s)
   for patch in [{'count':5},{'count':0},{'count':1.5},{'tileIndex':256},{'velocity':[1,2]},{'velocity':[2001,0,0]},{'surprise':1}]:
    cmd={'op':'aggregate-reemit','tileIndex':0,'count':1,'velocity':[240,0,0],**patch};before=s.snapshot()
    with self.assertRaises(ValueError):s.command(cmd)
    self.assertEqual(s.snapshot(),before)
   s.command({'op':'clear-instance','id':1});g.particle(material=1,count=1,deposit=True);before=s.snapshot()
   with self.assertRaises(ValueError):self.reemit(s)
   self.assertEqual(s.snapshot(),before);s.command({'op':'clear-instance','id':1});before=s.snapshot()
   with self.assertRaises(ValueError):self.reemit(s)
   self.assertEqual(s.snapshot(),before)
 def test_geometry_append_preserves_replacement_rejects_and_clear_is_clean(self):
  with NativeScene() as s:
   g=self.setup(s);s.command({'op':'mesh','append':True,'triangles':[g.wall(20)]});self.reemit(s,1);self.balance(s);g.mesh([g.wall(20)]);before=s.snapshot()
   with self.assertRaises(ValueError):self.reemit(s,1)
   self.assertEqual(s.snapshot(),before);s.command({'op':'clear-deposits'});self.assertEqual(self.tiles(s),[]);self.balance(s)
 def test_scheduled_partition_replay_preserves_source_counts(self):
  with NativeScene() as s:
   self.setup(s,heat=False);s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'aggregate-reemit','tileIndex':0,'count':3,'velocity':[240,0,0]}});start=s.snapshot();s.advance_to(1000000);done=s.snapshot();self.assertEqual(self.tiles(s)[0]['count'],1);self.assertEqual(s.info()['aggregateReemittedCount'],3);self.assertEqual(s.info()['particles']['born'],5);s.restore(start)
   for t in [100000,499999,500000,700000,1000000]:s.advance_to(t)
   self.assertEqual(s.snapshot(),done)
 def test_no_particle_slots_rejects_before_withdrawal(self):
  with NativeScene() as s:
   g=self.setup(s);g.particle(id=2,count=2048,position=[20,0,0],velocity=[0,0,0],collision=False,material=1);s.advance_to(16666);before=s.snapshot()
   with self.assertRaises(ValueError):self.reemit(s,2)
   self.assertEqual(s.snapshot(),before);self.balance(s)
 def test_stopped_source_captured_motion_and_thermal_mixture_survive(self):
  with NativeScene() as s:
   self.setup(s);s.command({'op':'surface-thermal','triangleIndex':0,'temperature':300,'capacity':100});s.advance_to(1000000);before_heat=s.info()['materialThermal'];aggregate=before_heat['aggregates'][0];s.command({'op':'stop','id':1});self.reemit(s,2);q=s.info()['materialThermal'];self.assertEqual(q['initialEnergy'],25000);self.assertAlmostEqual(q['liveEnergy'],before_heat['liveEnergy'],places=5)
   for row in q['particles']:self.assertAlmostEqual(row['temperature'],aggregate['temperature'],places=6);self.assertEqual(row['capacity'],10)
   for row in s.particle_motions():self.assertEqual(row[1:],(10,20,30,1,2,3))
   self.balance(s)
 def test_floor_aggregate_cycle_and_retention_do_not_create_input(self):
  with NativeScene() as s:
   s.command({'op':'floor','enabled':True,'maxIndividual':1,'maxTiles':4,'overflow':'merge-to-field','reentrainWindSpeed':0,'retentionMs':100});g=geometry.SurfaceGeometry();g.scene=s;g.particle(position=[0,1,0],velocity=[0,-240,0],count=4,deposit=True,colliders=None);s.advance_to(8333);self.reemit(s,1);self.assertEqual(self.tiles(s)[0]['count'],2);self.assertEqual(s.info()['particles']['born'],4);s.advance_to(150000);self.assertEqual(self.tiles(s),[])
 def test_legacy_provenance_corruption_and_nested_queued_feature(self):
  with NativeScene() as s:
   self.setup(s);current=s.snapshot();self.assertEqual(len(current),snapshot_size(s));old=bytearray(current[:24+13446176])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261044)
   struct.pack_into('<I',old,16,13446176);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff);s.restore(old);migrated=s.snapshot();self.assertEqual(migrated[24+13446176:24+13497384],bytes(51208))
   self.assertEqual(struct.unpack_from('<I',migrated,12)[0],current_schema());self.assertEqual(migrated[24+13497384:24+13497392],struct.pack('<ii',0,1))
   with self.assertRaises(ValueError):self.reemit(s)
   self.assertEqual(s.snapshot(),migrated);s.restore(current);bad=bytearray(current);struct.pack_into('<I',bad,24+13446176,0xffffffff);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(s.snapshot(),current);s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'aggregate-reemit','tileIndex':0,'count':1,'velocity':[240,0,0]}]}});current=s.snapshot();old=bytearray(current[:24+13446176])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261044)
   struct.pack_into('<I',old,16,13446176);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),current)
 def test_legacy_tiles_still_accept_legacy_merge_without_inventing_provenance(self):
  with NativeScene() as s:
   g=self.setup(s,heat=False);old=bytearray(s.snapshot()[:24+13446176])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261044)
   struct.pack_into('<I',old,16,13446176);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff);s.restore(old);s.command({'op':'clear-instance','id':1});g.particle(material=1,count=2,deposit=True);s.advance_to(16666);self.assertEqual(self.tiles(s)[0]['count'],6);self.assertFalse(self.tiles(s)[0]['canReemit'])
   before=s.snapshot()
   with self.assertRaises(ValueError):self.reemit(s)
   self.assertEqual(s.snapshot(),before)
 def test_new_generations_and_thermal_templates_do_not_mix_provenance(self):
  with NativeScene() as s:
   g=self.setup(s);s.command({'op':'clear-instance','id':1});s.command({'op':'material-thermal','id':1,'temperature':800,'capacity':20});g.particle(material=1,count=2,deposit=True);s.advance_to(16666);rows=self.tiles(s);self.assertEqual([r['count'] for r in rows],[4,2]);self.assertFalse(rows[0]['canReemit']);self.assertTrue(rows[1]['canReemit']);s.command({'op':'aggregate-reemit','tileIndex':1,'count':1,'velocity':[240,0,0]});q=s.info()['materialThermal'];self.assertEqual(q['particles'][0]['capacity'],20);self.assertEqual(q['particles'][0]['temperature'],800);self.balance(s)
 def test_identity_capacity_rejects_without_count_or_heat_withdrawal(self):
  with NativeScene() as s:
   self.setup(s);data=bytearray(s.snapshot());struct.pack_into('<I',data,24+28,0xfffffffe);struct.pack_into('<I',data,20,zlib.crc32(data[24:])&0xffffffff);s.restore(data);before=s.snapshot()
   with self.assertRaises(ValueError):self.reemit(s,2)
   self.assertEqual(s.snapshot(),before);self.balance(s)
