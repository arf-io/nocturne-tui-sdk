"""Real C oracle for atomic water/heat transfer; no mocks."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class WaterCarriedHeat(unittest.TestCase):
 def setup_scene(self,s,temperature=300,target=True):
  s.command({'op':'surface','id':1})
  s.command({'op':'mesh','triangles':[{'a':[0,0,0],'b':[1,0,0],'c':[0,0,1],'surfaceId':1},{'a':[2,0,0],'b':[3,0,0],'c':[2,0,1],'surfaceId':1}]})
  s.command({'op':'surface-water','surfaceId':1,'capacity':10,'evaporationUs':0})
  s.command({'op':'surface-water-add','triangleIndex':0,'volume':4})
  s.command({'op':'surface-thermal','triangleIndex':0,'temperature':temperature,'capacity':100})
  if target:s.command({'op':'surface-thermal','triangleIndex':1,'temperature':100,'capacity':200})
 def transfer(self,cp=10):return {'op':'surface-water-transfer','fromTriangle':0,'toTriangle':1,'volume':2,'heatCapacityPerVolume':cp}
 def test_independent_conservation_purity_and_replay(self):
  with NativeScene() as s:
   self.setup_scene(s);before=s.snapshot();s.command(self.transfer());after=s.snapshot()
   a,b=s.thermal_sample(0),s.thermal_sample(1)
   self.assertEqual((a[0],b[0]),(240,130));self.assertEqual(a[6],6000);self.assertEqual(b[5],6000);self.assertEqual(a[1]+b[1],50000)
   cells=s.info()['surfaceWater'][0]['cells'];self.assertEqual([x['retainedVolume'] for x in cells],[2,2])
   s.render();self.assertEqual(after,s.snapshot());s.restore(before);s.command(self.transfer());self.assertEqual(after,s.snapshot())
 def test_current_heating_epoch_and_water_overdraw(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command({'op':'surface-thermal-power','triangleIndex':0,'power':100});s.advance_to(1000000)
   s.command(self.transfer());a,b=s.thermal_sample(0),s.thermal_sample(1)
   self.assertAlmostEqual(a[0],240.8);self.assertAlmostEqual(b[0],130.1);self.assertAlmostEqual(a[3],100);self.assertAlmostEqual(a[6],6020)
   before=s.snapshot();bad=self.transfer();bad['volume']=3
   with self.assertRaises(ValueError):s.command(bad)
   self.assertEqual(before,s.snapshot())
 def test_target_temperature_limit_is_atomic(self):
  with NativeScene() as s:
   self.setup_scene(s,target=False);s.command({'op':'surface-thermal','triangleIndex':1,'temperature':9999,'capacity':1})
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(self.transfer())
   self.assertEqual(before,s.snapshot())
 def test_legacy_volume_only_does_not_move_heat(self):
  with NativeScene() as s:
   self.setup_scene(s);command=self.transfer();del command['heatCapacityPerVolume'];s.command(command)
   self.assertEqual((s.thermal_sample(0)[0],s.thermal_sample(1)[0]),(300,100))
 def test_overdraw_and_invalid_coefficients_are_atomic(self):
  with NativeScene() as s:
   self.setup_scene(s)
   for cp in (0,-1,1e9+1,1000,'ten',None):
    before=s.snapshot()
    with self.assertRaises(ValueError):s.command(self.transfer(cp))
    self.assertEqual(before,s.snapshot())
 def test_missing_reservoir_rejects_and_cold_water_transfers(self):
  with NativeScene() as s:
   self.setup_scene(s,target=False);before=s.snapshot()
   with self.assertRaises(ValueError):s.command(self.transfer())
   self.assertEqual(before,s.snapshot())
  with NativeScene() as s:
   self.setup_scene(s,temperature=0);s.command(self.transfer());self.assertEqual(s.thermal_sample(1)[0],100)
if __name__=='__main__':unittest.main()
