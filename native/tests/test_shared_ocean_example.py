"""Public SDK scene integration: one field drives geometry, impacts and bodies."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'examples'),str(ROOT/'bindings/python')]
from nocturne_native import NativeScene
from shared_ocean import build_scene
class SharedOceanExample(unittest.TestCase):
 def testCombinedSceneActuallyAdvancesItsComponents(self):
  with NativeScene(2030) as scene:
   build_scene(scene);initial=scene.snapshot();bodies=scene.info()['floatBodies'];scene.advance_to(1000000);info=scene.info()
   self.assertEqual(info['geometry']['triangles'],138);self.assertEqual(len(info['floatBodies']),3)
   self.assertGreater(sum(r[2] for r in scene.surface_foam(1)),0)
   self.assertGreater(info['surfaces'][0]['impacts'],0)
   self.assertNotEqual(bodies[0]['position'],info['floatBodies'][0]['position']);self.assertEqual(info['nodes'][0]['position'],[-3,2,-6])
   for row in scene.surface_foam(1):self.assertAlmostEqual(row[2],sum(row[i] for i in [1,3,4]),places=10)
   self.assertNotEqual(initial,scene.snapshot());before=scene.snapshot();scene.render();self.assertEqual(before,scene.snapshot())
   scene.advance_to(2000000);expected=scene.snapshot();scene.restore(before);scene.advance_to(2000000);self.assertEqual(expected,scene.snapshot())
