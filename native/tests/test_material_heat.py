"""Owned heat through real contacts, deposits, aggregates and re-entrainment."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import math,struct,zlib,unittest
import test_surface_geometry as geometry
from nocturne_native import NativeScene
class MaterialHeat(unittest.TestCase):
 def setup_scene(self,s,fraction=1,conductance=0,**surface):
  g=geometry.SurfaceGeometry();g.scene=s;s.command({'op':'floor','enabled':False});g.surface(**surface);g.mesh([g.wall()]);s.command({'op':'surface-thermal','triangleIndex':0,'temperature':300,'capacity':100});s.command({'op':'material','id':1});s.command({'op':'material-thermal','id':1,'temperature':500,'capacity':10,'contactFraction':fraction,'conductance':conductance});return g
 def info(self,s):return s.info()['materialThermal']
 def balance(self,s):
  q=self.info(s);self.assertAlmostEqual(q['initialEnergy']+q['importedEnergy'],q['liveEnergy']+q['transferredEnergy']+q['exportedEnergy'],places=5)
 def test_independent_contact_fractions_conservation_purity_replay(self):
  for fraction in [0,.25,1]:
   with self.subTest(fraction=fraction),NativeScene() as s:
    g=self.setup_scene(s,fraction);g.particle(material=1);saved=s.snapshot();s.advance_to(8333);done=s.snapshot();heat=fraction*200*10*100/110;row=self.info(s)['particles'][0]
    self.assertAlmostEqual(row['temperature'],500-heat/10,places=5);self.assertAlmostEqual(s.thermal_sample(0)[0],300+heat/100,places=5);self.balance(s);s.render();self.assertEqual(s.snapshot(),done);s.restore(saved);s.advance_to(8333);self.assertEqual(s.snapshot(),done)
 def test_retained_deposit_continuous_star_reference(self):
  with NativeScene() as s:
   g=self.setup_scene(s,0,100);g.particle(material=1,deposit=True);s.advance_to(8333);identity=s.info()['deposits'][0]['id'];s.advance_to(1000000);equilibrium=35000/110;d=(1/(1+100/120*(1/10+1/100)))**119
   self.assertAlmostEqual(s.thermal_sample(0)[0],equilibrium+(300-equilibrium)*d,places=5);row=self.info(s)['deposits'][0];self.assertEqual(row['id'],identity);self.assertAlmostEqual(row['temperature'],equilibrium+(500-equilibrium)*d,places=5);self.balance(s)
 def test_aggregate_capacity_energy_and_explicit_clear(self):
  with NativeScene() as s:
   g=self.setup_scene(s,0,0,maxIndividual=1,maxTiles=1,overflow='merge-to-field');g.particle(material=1,count=5,deposit=True);s.advance_to(8333);q=self.info(s);self.assertEqual(q['initialEnergy'],25000);self.assertEqual(q['liveEnergy'],25000);self.assertEqual(q['aggregates'][0]['capacity'],40);self.assertEqual(q['aggregates'][0]['temperature'],500);self.balance(s)
   s.command({'op':'clear-deposits'});q=self.info(s);self.assertEqual(q['liveEnergy'],0);self.assertEqual(q['exportedEnergy'],25000);self.balance(s)
 def test_reentrainment_keeps_captured_heat_and_identity(self):
  with NativeScene() as s:
   g=self.setup_scene(s,0,0,reentrainWindSpeed=1);g.particle(material=1,deposit=True);s.advance_to(8333);identity=s.info()['deposits'][0]['id'];s.command({'op':'material-thermal','id':1,'temperature':800,'capacity':20});s.command({'op':'forces','id':1,'wind':[0,5,0]});s.advance_to(208333);row=self.info(s)['particles'][0];self.assertEqual(row['id'],identity);self.assertEqual(row['capacity'],10);self.assertEqual(row['temperature'],500);self.assertEqual(self.info(s)['initialEnergy'],5000);self.balance(s)
 def test_expiry_clear_and_missing_receiver_export(self):
  for clear in ['expiry','clear-instance','clear']:
   with self.subTest(clear=clear),NativeScene() as s:
    g=self.setup_scene(s);g.particle(material=1,collision=False,lifetimeMinMs=10,lifetimeMaxMs=10);s.advance_to(8333)
    if clear=='expiry':s.advance_to(16666)
    else:s.command({'op':'clear-instance','id':1} if clear=='clear-instance' else {'op':'clear','scope':'weather'})
    self.assertEqual(self.info(s)['exportedEnergy'],5000);self.assertEqual(self.info(s)['liveEnergy'],0);self.balance(s)
 def test_negative_authoring_and_future_only_removal(self):
  with NativeScene() as s:
   g=self.setup_scene(s);g.particle(material=1,collision=False);s.advance_to(8333)
   for field,value in [('capacity',0),('temperature',10001),('temperature',-1),('contactFraction',1.1),('conductance',-1),('capacity','ten')]:
    bad={'op':'material-thermal','id':1,'temperature':500,'capacity':10,field:value};before=s.snapshot()
    with self.assertRaises(ValueError):s.command(bad)
    self.assertEqual(s.snapshot(),before)
   s.command({'op':'remove-material-thermal','id':1});self.assertEqual(self.info(s)['liveEnergy'],5000);self.balance(s)
 def test_mesh_append_preserves_and_replacement_detaches_deposit_heat(self):
  with NativeScene() as s:
   g=self.setup_scene(s,0,100);g.particle(material=1,deposit=True);s.advance_to(8333);s.command({'op':'mesh','append':True,'triangles':[g.wall(20)]});s.advance_to(16666);self.assertGreater(s.thermal_sample(0)[0],300);g.mesh([g.wall(20)]);s.command({'op':'surface-thermal','triangleIndex':0,'temperature':300,'capacity':100});s.advance_to(25000);self.assertEqual(s.thermal_sample(0)[0],300);self.balance(s);s.command({'op':'mesh','append':True,'triangles':[g.wall(40)]});s.advance_to(33333);self.assertEqual(s.thermal_sample(0)[0],300)
 def test_zero_temperature_capture_remains_visible_after_authoring_removed(self):
  with NativeScene() as s:
   g=self.setup_scene(s);s.command({'op':'material-thermal','id':1,'temperature':0,'capacity':10});g.particle(material=1,collision=False);s.advance_to(8333);s.command({'op':'remove-material-thermal','id':1});row=self.info(s)['particles'][0];self.assertEqual(row['temperature'],0);self.assertEqual(row['capacity'],10);self.balance(s)
 def test_aggregate_and_individual_share_one_continuous_energy_solution(self):
  with NativeScene() as s:
   g=self.setup_scene(s,0,100,maxIndividual=1,maxTiles=1,overflow='merge-to-field');g.particle(material=1,count=5,deposit=True);s.advance_to(1000000);equilibrium=55000/150;d=(1/(1+500/120*(1/50+1/100)))**119
   self.assertAlmostEqual(s.thermal_sample(0)[0],equilibrium+(300-equilibrium)*d,places=5);q=self.info(s)
   for row in q['deposits']+q['aggregates']:self.assertAlmostEqual(row['temperature'],equilibrium+(500-equilibrium)*d,places=5)
   self.balance(s)
 def test_whole_thermal_block_independent_combined_recurrence(self):
  with NativeScene() as s:
   g=self.setup_scene(s,0,100);s.command({'op':'mesh','append':True,'triangles':[g.wall(20)]});s.command({'op':'surface-thermal','triangleIndex':1,'temperature':100,'capacity':200});s.command({'op':'surface-water','surfaceId':1,'capacity':10,'evaporationUs':1000000});s.command({'op':'surface-water-add','triangleIndex':0,'volume':4})
   for i in [0,1]:s.command({'op':'surface-water-thermal','triangleIndex':i,'latentHeatPerVolume':100})
   s.command({'op':'surface-thermal-link','id':1,'fromTriangle':0,'toTriangle':1,'conductance':10});s.command({'op':'surface-water-link','id':1,'fromTriangle':0,'toTriangle':1,'rate':1,'heatCapacityPerVolume':10});g.particle(material=1,deposit=True)
   source,target,body,water0,water1=300.,100.,500.,4.,0.
   for step in range(1,121):
    dt=(step*1000000//120-(step-1)*1000000//120)/1000000;wet0=water0*math.exp(-dt);wet1=water1*math.exp(-dt);source-=(water0-wet0);target-=(water1-wet1)/2
    q=(10/120)*(source-target)/(1+(10/120)*(1/100+1/200));source-=q/100;target+=q/200
    if step>1:q=(100/120)*(body-source)/(1+(100/120)*(1/10+1/100));source+=q/100;body-=q/10
    volume=wet0*(-math.expm1(-1/120));energy=volume*10*source;source-=energy/100;target+=energy/200;water0=wet0-volume;water1=wet1+volume
   saved=s.snapshot();s.advance_to(1000000);done=s.snapshot();self.assertAlmostEqual(s.thermal_sample(0)[0],source,places=5);self.assertAlmostEqual(s.thermal_sample(1)[0],target,places=5);self.assertAlmostEqual(self.info(s)['deposits'][0]['temperature'],body,places=5)
   self.assertAlmostEqual(s.water_sample(0)[2]+s.water_sample(1)[2],4*math.exp(-1),places=6);self.assertAlmostEqual(s.thermal_sample(0)[1]+s.thermal_sample(1)[1]+self.info(s)['liveEnergy'],55000-400*(1-math.exp(-1)),places=5);self.balance(s);s.render();self.assertEqual(s.snapshot(),done);s.restore(saved);s.advance_to(1000000);self.assertEqual(s.snapshot(),done)
 def test_historical_migration_corrupt_owned_id_and_queued_feature(self):
  with NativeScene() as s:
   g=self.setup_scene(s);g.particle(material=1,collision=False);s.advance_to(8333);before=s.snapshot();old=bytearray(before[:24+13332864])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261043)
   struct.pack_into('<I',old,16,13332864);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff);s.restore(old);promoted=s.snapshot();self.assertEqual(len(promoted),snapshot_size(s));self.assertEqual(promoted[32:24+13332864],old[32:]);self.assertEqual(promoted[24+13332864:24+13497384],bytes(164520))
   self.assertEqual(struct.unpack_from('<I',promoted,12)[0],current_schema());self.assertEqual(promoted[24+13497384:24+13497392],struct.pack('<ii',0,1))
   s.restore(before);bad=bytearray(before);struct.pack_into('<I',bad,24+13332864+640,999);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(s.snapshot(),before)
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'material-thermal','id':1,'temperature':500,'capacity':10}]}});current=s.snapshot();old=bytearray(current[:24+13332864])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261043)
   struct.pack_into('<I',old,16,13332864);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),current)
