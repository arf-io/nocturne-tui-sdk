"""The shared gallery recipe executes actual native surfaces and persistent state."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene


class SurfaceLab(unittest.TestCase):
    def setUp(self):
        recipes=json.loads((ROOT/'recipes.json').read_text())
        self.recipe=next((r for r in recipes if r['id']=='surface-lab'),None)
        self.assertIsNotNone(self.recipe,'The shared surface-lab recipe is absent')
        self.scene=NativeScene(2030);self.addCleanup(self.scene.close)
        self.scene.command({'op':'resize','width':120,'height':44})
        for command in self.recipe['commands']:self.scene.command(command)
        self.scene.advance_to(4000000)

    def testBothSlopesReceiveRainAndPersistentOrientedLeaves(self):
        info=self.scene.info();surfaces=info['surfaces']
        self.assertEqual([s['id'] for s in surfaces],[1,2])
        self.assertEqual([s['renderVisible'] for s in surfaces],[True,False])
        self.assertEqual(info['geometry']['collisionTriangles'],4)
        for surface in surfaces:
            self.assertGreater(surface['wetness'],0)
            self.assertEqual(surface['individualDeposits'],8)
            self.assertGreater(surface['aggregateDeposits'],0)
            self.assertLessEqual(surface['aggregateTiles'],surface['maxTiles'])
        self.assertGreater(surfaces[0]['heat'],0)
        self.assertEqual({d['surfaceId'] for d in info['deposits']},{1,2})
        for deposit in info['deposits']:
            self.assertGreater(abs(deposit['normal'][0]),.2)
            self.assertGreater(deposit['normal'][1],.9)

    def testRepeatedRenderIsPureAndHiddenCollectorHasIndependentVisibility(self):
        snapshot=self.scene.snapshot();hidden=self.scene.render().bytes
        self.scene.render();self.scene.info()
        self.assertTrue(snapshot==self.scene.snapshot(),'Rendering mutated the surface-lab scene')
        particles=self.scene.particles()
        self.scene.command({'op':'surface','id':2,'renderVisible':True})
        self.assertEqual(particles,self.scene.particles())
        self.assertTrue(hidden!=self.scene.render().bytes,'Revealing the second collector must affect the frame')
        before=self.scene.snapshot();self.scene.render()
        self.assertTrue(before==self.scene.snapshot(),'Rendering the revealed collector mutated state')

    def testStoppingWeatherPreservesResponseAndScopedDepositOwnership(self):
        before=self.scene.info()
        self.scene.command({'op':'clear','scope':'weather'})
        self.assertEqual(self.scene.particles(),[])
        self.assertEqual(self.scene.info()['deposits'],before['deposits'])
        self.assertEqual(self.scene.info()['surfaces'],before['surfaces'])
        self.scene.command({'op':'clear-surface','id':2,'scope':'all'})
        after=self.scene.info()
        self.assertEqual(after['surfaces'][0],before['surfaces'][0])
        self.assertEqual(after['surfaces'][1]['wetness'],0)
        self.assertEqual({d['surfaceId'] for d in after['deposits']},{1})


if __name__=='__main__':unittest.main()
