"""Real native analytic latent heat, mutation epochs and persistence."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import math,struct,zlib,unittest
import test_water_carried_heat as fixture
from nocturne_native import NativeScene
class LatentHeat(unittest.TestCase):
 def setup_scene(self,s,conductance=0):
  fixture.WaterCarriedHeat().setup_scene(s)
  s.command({'op':'surface-water-settings','surfaceId':1,'evaporationUs':1000000})
  s.command({'op':'surface-thermal-settings','triangleIndex':0,'ambientTemperature':100,'conductance':conductance})
  s.command({'op':'surface-water-thermal','triangleIndex':0,'latentHeatPerVolume':100})
 def latent(self,s):return s.info()['surfaceThermal']['cells'][0]['evaporatedEnergy']
 def test_closed_form_zero_equal_unequal_rates_and_purity(self):
  for conductance in [0,100,200,100.000001]:
   with self.subTest(conductance=conductance),NativeScene() as s:
    self.setup_scene(s,conductance);s.advance_to(1000000);saved=s.snapshot();k=conductance/100
    if not k:expected=300-4*(1-math.exp(-1))
    elif abs(k-1)<1e-7:expected=100+200*math.exp(-k)-4*math.exp(-1)
    else:expected=100+200*math.exp(-k)-4*(math.exp(-1)-math.exp(-k))/(k-1)
    self.assertAlmostEqual(s.thermal_sample(0)[0],expected,places=5);self.assertAlmostEqual(self.latent(s),400*(1-math.exp(-1)),places=5)
    s.render();s.info();s.thermal_sample(0);s.water_sample(0);self.assertEqual(s.snapshot(),saved)
 def test_add_rate_power_epochs_and_partition_independence(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(500000);s.command({'op':'surface-water-add','triangleIndex':0,'volume':2});s.command({'op':'surface-water-settings','surfaceId':1,'evaporationUs':2000000});s.command({'op':'surface-thermal-power','triangleIndex':0,'power':100});saved=s.snapshot()
   e1=400*(1-math.exp(-.5));w=4*math.exp(-.5)+2;expected=e1+100*w*(1-math.exp(-.25))
   s.advance_to(1000000);after=s.snapshot();self.assertAlmostEqual(self.latent(s),expected,places=5);self.assertAlmostEqual(s.thermal_sample(0)[1],30000+50-expected,places=5)
   s.restore(saved)
   for t in [550000,600000,750000,1000000]:s.advance_to(t)
   self.assertEqual(s.snapshot(),after)
 def test_transfer_disable_and_mesh_history(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(500000);s.command({'op':'surface-water-transfer','fromTriangle':0,'toTriangle':1,'volume':1})
   s.advance_to(1000000);expected=400*(1-math.exp(-.5))+100*(4*math.exp(-.5)-1)*(1-math.exp(-.5));self.assertAlmostEqual(self.latent(s),expected,places=5)
   s.command({'op':'surface-water-thermal','triangleIndex':0,'latentHeatPerVolume':0});temperature=s.thermal_sample(0)[0];s.advance_to(1500000);self.assertEqual(s.thermal_sample(0)[0],temperature);self.assertAlmostEqual(self.latent(s),expected,places=5)
   s.command({'op':'mesh','triangles':[]});q=s.info()['surfaceThermal'];self.assertAlmostEqual(q['historicalLatentEnergy'],expected,places=5);self.assertAlmostEqual(q['exportedEnergy'],50000-expected,places=5)
 def test_impact_reemission_and_bound_evaporation_epochs(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command({'op':'floor','enabled':False})
   s.command(dict(op='emitter',id=1,effect='weather/rain-threads',count=0,position=[.2,1,.2],extent=[0,0,0],spread=[0,0,0],velocity=[0,-240,0],gravity=[0,0,0],wind=[0,0,0],drag=0,collision=True,colliders={'surfaces':[1]},lifetimeMinMs=10000,lifetimeMaxMs=10000))
   s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='spray')]));s.command(dict(op='flow-spray',flowId=1,emitterId=1,fraction=.5,particleVolume=.1));s.advance_to(100000)
   self.assertAlmostEqual(s.water_sample(0)[1],4.1,places=6);s.command(dict(op='flow-rate',id=1,flux=0));s.command(dict(op='surface-water-reemit',triangleIndex=0,emitterId=1,volume=.04));s.advance_to(400000)
   self.assertAlmostEqual(self.latent(s),100*s.water_sample(0)[6],places=5);self.assertAlmostEqual(s.thermal_sample(0)[1],30000-100*s.water_sample(0)[6],places=5)
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='define',path='/evaporation',value=1000000,binding=dict(family='surface',id=1,field='water.evaporationUs')));s.advance_to(500000);s.command(dict(op='set',path='/evaporation',value=2000000));s.advance_to(1000000)
   expected=400*(1-math.exp(-.75));self.assertAlmostEqual(self.latent(s),expected,places=5);self.assertAlmostEqual(s.thermal_sample(0)[1],30000-expected,places=5)
 def test_invalid_configuration_and_heat_overdraw_rollback(self):
  with NativeScene() as s:
   self.setup_scene(s)
   for value in [-1,1e9+1,'ten',None]:
    before=s.snapshot()
    with self.assertRaises(ValueError):s.command({'op':'surface-water-thermal','triangleIndex':0,'latentHeatPerVolume':value})
    self.assertEqual(s.snapshot(),before)
   s.command({'op':'surface-water-thermal','triangleIndex':0,'latentHeatPerVolume':1e9});before=s.snapshot()
   with self.assertRaises(ValueError):s.advance_to(1000000)
   self.assertEqual(s.snapshot(),before)
  with NativeScene() as s:
   fixture.WaterCarriedHeat().setup_scene(s,target=False);before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'surface-water-thermal','triangleIndex':1,'latentHeatPerVolume':100})
   self.assertEqual(s.snapshot(),before)
 def test_schema42_migration_corruption_and_old_scheduled_feature(self):
  with NativeScene() as s:
   fixture.WaterCarriedHeat().setup_scene(s);old=bytearray(s.snapshot()[:24+13328760])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261042)
   struct.pack_into('<I',old,16,13328760);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff);s.restore(old);promoted=s.snapshot();self.assertEqual(len(promoted),snapshot_size(s));self.assertEqual(promoted[32:24+13328760],old[32:]);self.assertEqual(promoted[24+13328760:24+13497384],bytes(168624))
   self.setup_scene_fresh(s);valid=s.snapshot()
   for offset,value in [(24+13328760,-1),(24+13328768,-1),(24+13328760,float('nan'))]:
    bad=bytearray(valid);struct.pack_into('<d',bad,offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
    with self.assertRaises(ValueError):s.restore(bad)
    self.assertEqual(s.snapshot(),valid)
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'surface-water-thermal','triangleIndex':0,'latentHeatPerVolume':100}]}});before=s.snapshot();old=bytearray(before[:24+13328760])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261042)
   struct.pack_into('<I',old,16,13328760);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),before)
 def setup_scene_fresh(self,s):s.command({'op':'reset'});self.setup_scene(s)
