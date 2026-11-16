"""Real C hydraulic/heat recurrence and append-only migration oracles."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import math,struct,zlib,unittest
import test_water_carried_heat as fixture
from nocturne_native import NativeScene
class HydraulicHeat(unittest.TestCase):
 def setup_scene(self,s):
  s.command({'op':'surface','id':1});s.command({'op':'mesh','triangles':[{'a':[i*2,0,0],'b':[i*2+1,0,0],'c':[i*2,0,1],'surfaceId':1} for i in range(3)]})
  s.command({'op':'surface-water','surfaceId':1,'capacity':10,'evaporationUs':0})
  for i,(v,t,c) in enumerate(zip([4,2,0],[300,100,200],[100,200,150])):
   if v:s.command({'op':'surface-water-add','triangleIndex':i,'volume':v})
   s.command({'op':'surface-thermal','triangleIndex':i,'temperature':t,'capacity':c})
 def link(self,i,a,b,rate=1,cp=10):
  row={'op':'surface-water-link','id':i,'fromTriangle':a,'toTriangle':b,'rate':rate}
  if cp is not None:row['heatCapacityPerVolume']=cp
  return row
 def test_simultaneous_network_independent_recurrence_and_replay(self):
  links=[(0,1,1),(0,2,2),(1,0,1)];expected_v=[4.,2.,0.];expected_e=[30000.,20000.,30000.];capacities=[100,200,150]
  for step in range(120):
   dv=[0.,0.,0.];de=[0.,0.,0.]
   for a,b,rate in links:
    total=sum(r for x,y,r in links if x==a);v=expected_v[a]*(-math.expm1(-total/120))*rate/total;e=v*10*expected_e[a]/capacities[a]
    dv[a]-=v;dv[b]+=v;de[a]-=e;de[b]+=e
   expected_v=[x+y for x,y in zip(expected_v,dv)];expected_e=[x+y for x,y in zip(expected_e,de)]
  results=[]
  for reverse in [False,True]:
   with NativeScene() as s:
    self.setup_scene(s)
    for i in (reversed(range(3)) if reverse else range(3)):
     a,b,r=links[i];s.command(self.link(i+1,a,b,r))
    saved=s.snapshot();s.advance_to(1000000);after=s.snapshot()
    cells=s.info()['surfaceWater'][0]['cells'];rows=[s.thermal_sample(i) for i in range(3)]
    for i in range(3):self.assertAlmostEqual(cells[i]['retainedVolume'],expected_v[i],places=6);self.assertAlmostEqual(rows[i][1],expected_e[i],places=5)
    self.assertAlmostEqual(sum(r[1] for r in rows),80000,places=5);self.assertAlmostEqual(sum(c['retainedVolume'] for c in cells),6,places=5) # metadata rounds each cell to six decimals
    s.render();self.assertEqual(s.snapshot(),after);s.restore(saved);s.advance_to(1000000);self.assertEqual(s.snapshot(),after);results.append([r[1] for r in rows])
  for a,b in zip(*results):self.assertAlmostEqual(a,b,places=6)
 def test_invalid_configuration_and_failed_clock_are_atomic(self):
  with NativeScene() as s:
   self.setup_scene(s)
   for cp in [0,-1,1e9+1,'ten']:
    before=s.snapshot()
    with self.assertRaises(ValueError):s.command(self.link(1,0,1,cp=cp))
    self.assertEqual(s.snapshot(),before)
   s.command(self.link(1,0,1,rate=1000,cp=1e9));before=s.snapshot()
   with self.assertRaises(ValueError):s.advance_to(1000000)
   self.assertEqual(s.snapshot(),before)
  with NativeScene() as s:
   fixture.WaterCarriedHeat().setup_scene(s,target=False);before=s.snapshot()
   with self.assertRaises(ValueError):s.command(self.link(1,0,1))
   self.assertEqual(s.snapshot(),before)
 def test_heating_epoch_and_target_overflow(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command({'op':'surface-thermal-power','triangleIndex':0,'power':100});s.command(self.link(1,0,1))
   v=4.;e=30000.;target=20000.
   for step in range(1,121):
    elapsed=(step*1000000//120-(step-1)*1000000//120)/1000000;e+=100*elapsed;q=v*(-math.expm1(-1/120));heat=q*10*e/100;v-=q;e-=heat;target+=heat
   s.advance_to(1000000);self.assertAlmostEqual(s.thermal_sample(0)[1],e,places=5);self.assertAlmostEqual(s.thermal_sample(1)[1],target,places=5)
   self.assertAlmostEqual(s.thermal_sample(0)[3],100,places=6)
  with NativeScene() as s:
   fixture.WaterCarriedHeat().setup_scene(s,target=False);s.command({'op':'surface-thermal','triangleIndex':1,'temperature':9999,'capacity':1});s.command(self.link(1,0,1,rate=1000));before=s.snapshot()
   with self.assertRaises(ValueError):s.advance_to(1000000)
   self.assertEqual(s.snapshot(),before)
 def test_legacy_migration_and_corrupt_append(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(self.link(1,0,1,cp=None));saved=s.snapshot();old=bytearray(saved[:24+13328248])
   for off in [12,28]:struct.pack_into('<I',old,off,0x20261041)
   struct.pack_into('<I',old,16,13328248);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   s.restore(old);promoted=s.snapshot();self.assertEqual(len(promoted),snapshot_size(s));self.assertEqual(promoted[32:24+13328248],old[32:]);self.assertEqual(promoted[24+13328248:24+13497384],bytes(169136))
   s.advance_to(1000000);self.assertEqual(s.thermal_sample(0)[0],300)
   valid=s.snapshot()
   for cp in [-1,float('nan'),1e9+1]:
    bad=bytearray(valid);struct.pack_into('<d',bad,24+13328248,cp);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
    with self.assertRaises(ValueError):s.restore(bad)
    self.assertEqual(s.snapshot(),valid)
 def test_old_schema_cannot_queue_new_heat_contract(self):
  for nested in [False,True]:
   with NativeScene() as s:
    self.setup_scene(s);command=self.link(1,0,1)
    if nested:command={'op':'batch','commands':[command]}
    s.command({'op':'schedule','id':1,'atUs':500000,'command':command})
    before=s.snapshot();s.restore(before);self.assertEqual(s.snapshot(),before);old=bytearray(before[:24+13328248])
    for off in [12,28]:struct.pack_into('<I',old,off,0x20261041)
    struct.pack_into('<I',old,16,13328248);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
    with self.assertRaises(ValueError):s.restore(old)
    self.assertEqual(s.snapshot(),before)
 def test_removal_replacement_and_geometry_append(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(self.link(1,0,1));s.command({'op':'mesh','append':True,'triangles':[]});self.assertEqual(s.info()['waterLinks'][0]['heatCapacityPerVolume'],10)
   s.command({'op':'remove-surface-water-link','id':1});self.assertEqual(s.snapshot()[24+13328248:24+13497384],bytes(169136))
   s.command(self.link(1,0,1));s.command({'op':'mesh','triangles':[]});self.assertEqual(s.snapshot()[24+13328248:24+13497384],bytes(169136))
