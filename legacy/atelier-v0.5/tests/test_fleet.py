"""Fleet additive helper and native cross-binding scene acceptance."""
import unittest,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from studio import fleetInkOpacity
from fleet_scene import renderFleetScene
class FleetTests(unittest.TestCase):
    def testNativeScenes(self):
        for f in json.loads((ROOT/'tests/fleet/fixtures.json').read_text())['fixtures']:
            with self.subTest(f['name']):self.assertEqual(hashlib.sha256(renderFleetScene(f['scene']).tobytes()).hexdigest(),f['sha256'])
    def testSharedOpacityCases(self):
        for c in json.loads((ROOT/'tests/fleet/fixtures.json').read_text())['fades']:
            with self.subTest(c['args']):self.assertEqual(fleetInkOpacity(*c['args']),c['value'])
    def testRejectBadOpacity(self):
        for args in [(-1,520,0,1536,760),(0,0,0,-1,760),(0,0,0,0,1001),(True,0,0,0,760)]:
            with self.assertRaises(ValueError):fleetInkOpacity(*args)
    def testSceneVersion(self):
        with self.assertRaises(ValueError):renderFleetScene({'version':2})
