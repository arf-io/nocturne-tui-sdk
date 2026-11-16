"""Real shared-core mesh collision, surface response and ownership contracts."""
import gzip
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


class SurfaceGeometry(unittest.TestCase):
    def setUp(self):
        self.scene = NativeScene(8192)
        self.scene.command({'op': 'floor', 'enabled': False})
        self.scene.command({'op': 'environment', 'stars': 0, 'style': 'solid'})

    def tearDown(self):
        self.scene.close()

    def surface(self, ident=1, **patch):
        command = dict(op='surface', id=ident, restitution=1, friction=0,
                       evaporation=0, cooling=0, thermalEvaporation=0,
                       reentrainWindSpeed=0)
        command.update(patch)
        self.scene.command(command)

    def mesh(self, triangles):
        self.scene.command({'op': 'mesh', 'triangles': triangles})

    def wall(self, x=0, surface=1, reverse=False):
        points = [[x, -10, -10], [x, 10, -10], [x, 0, 10]]
        if reverse:
            points[1], points[2] = points[2], points[1]
        return dict(a=points[0], b=points[1], c=points[2], surfaceId=surface)

    def particle(self, **patch):
        command = dict(op='emitter', id=1, effect='weather/autumn-drift',
                       count=1, runningTimeMs=0, shape='point', position=[1, 0, 0],
                       velocity=[-240, 0, 0], extent=[0, 0, 0], spread=[0, 0, 0],
                       gravity=[0, 0, 0], wind=[0, 0, 0], windVariation=[0, 0, 0],
                       drag=0, lift=0, flutterHz=0, flutterAmount=0,
                       tumble=[0, 0, 0], deposit=False, collision=True,
                       lifetimeMinMs=10000, lifetimeMaxMs=10000,
                       sizeMin=.1, sizeMax=.1, colliders={'surfaces': [1]})
        command.update(patch)
        if command.get('colliders') is None:
            del command['colliders']
        self.scene.command(command)

    def state(self, ident=1):
        return next(s for s in self.scene.info()['surfaces'] if s['id'] == ident)

    def one(self):
        values = self.scene.particles()
        self.assertEqual(len(values), 1)
        return values[0]

    def testSweptWallContactCannotTunnelAndUsesRemainingStep(self):
        self.surface(); self.mesh([self.wall()]); self.particle()
        self.scene.advance_to(8333)
        p = self.one()
        self.assertAlmostEqual(p[3] / 65536, 1.001, delta=2/65536)
        self.assertEqual(p[6:9], (240*65536, 0, 0))
        contact = self.scene.info()['contacts'][0]
        self.assertEqual(contact['surfaceId'], 1)
        self.assertEqual(contact['normal'], [1, 0, 0])
        self.assertEqual(self.state()['impacts'], 1)

    def testBothWindingsAndBackSideReflectAgainstArrival(self):
        for reverse in (False, True):
            for sign in (-1, 1):
                with self.subTest(reverse=reverse, sign=sign):
                    self.scene.command({'op':'reset','seed':8192})
                    self.scene.command({'op':'floor','enabled':False})
                    self.surface(); self.mesh([self.wall(reverse=reverse)])
                    self.particle(position=[sign,0,0],velocity=[-240*sign,0,0])
                    self.scene.advance_to(8333)
                    self.assertEqual(self.one()[6],240*sign*65536)
                    self.assertEqual(self.scene.info()['contacts'][0]['normal'],[sign,0,0])

    def testObliqueNormalReflectionAndTangentialFriction(self):
        self.surface(restitution=.5, friction=.25)
        self.mesh([dict(a=[-10,-10,-10], b=[10,10,-10], c=[0,0,10], surfaceId=1)])
        self.particle(position=[0,1,0], velocity=[0,-240,120])
        self.scene.advance_to(8333)
        p = self.one()
        # n=(-1,1,0)/sqrt(2): tangent=(-120,-120,120), normal velocity=(120,-120,0).
        self.assertAlmostEqual(p[6]/65536, -150, delta=3/65536)
        self.assertAlmostEqual(p[7]/65536, -30, delta=3/65536)
        self.assertAlmostEqual(p[8]/65536, 90, delta=3/65536)
        n = self.scene.info()['contacts'][0]['normal']
        self.assertAlmostEqual(n[0], -math.sqrt(.5), places=5)
        self.assertAlmostEqual(n[1], math.sqrt(.5), places=5)

    def testNearestTriangleWinsIndependentOfArrayOrder(self):
        self.surface(); self.surface(2)
        self.mesh([self.wall(-.5, 2), self.wall(0, 1)])
        self.particle(colliders={'surfaces': [1, 2]})
        self.scene.advance_to(8333)
        self.assertEqual(self.state(1)['impacts'], 1)
        self.assertEqual(self.state(2)['impacts'], 0)

    def testEqualTimeSharedEdgeUsesTriangleOrder(self):
        self.surface(); self.surface(2)
        self.mesh([dict(a=[0,-2,-2], b=[0,2,2], c=[0,2,-2], surfaceId=2),
                   dict(a=[0,-2,-2], b=[0,-2,2], c=[0,2,2], surfaceId=1)])
        self.particle(colliders={'surfaces': [1, 2]})
        self.scene.advance_to(8333)
        self.assertEqual(self.scene.info()['contacts'][0]['triangleIndex'], 0)
        self.assertEqual(self.state(2)['impacts'], 1)
        self.assertEqual(self.state(1)['impacts'], 0)

    def testRenderingAndCollisionFlagsAreIndependent(self):
        self.surface(renderVisible=False); self.mesh([self.wall()]); self.particle()
        self.scene.command({'op':'camera','position':[30,0,0],'yaw':-90,'pitch':0})
        before = self.scene.snapshot(); invisible = self.scene.render().bytes
        self.assertEqual(before, self.scene.snapshot())
        self.scene.command({'op':'surface','id':1,'renderVisible':True})
        self.assertTrue(invisible != self.scene.render().bytes, 'A side-facing camera must see the enabled wall surface')
        self.scene.command({'op':'surface','id':1,'renderVisible':False})
        self.scene.advance_to(8333)
        self.assertEqual(self.one()[6], 240*65536)
        self.scene.command({'op':'clear','scope':'weather'})
        self.scene.command({'op':'surface','id':1,'collisionEnabled':False})
        self.particle(); self.scene.advance_to(16666)
        self.assertEqual(self.one()[6], -240*65536)

    def testLegacyDefaultAndRenderingOnlyMeshNeverAcquireCollisions(self):
        self.surface(); self.mesh([self.wall()]); self.particle(colliders=None)
        self.scene.advance_to(8333)
        self.assertEqual(self.one()[6], -240*65536)
        self.assertEqual(self.state()['impacts'], 0)
        self.scene.command({'op':'clear','scope':'weather'})
        self.mesh([self.wall(surface=0)]); self.particle()
        self.scene.advance_to(16666)
        self.assertEqual(self.one()[6], -240*65536)

    def testColliderEditPreservesIdentityAndClock(self):
        self.surface(); self.mesh([self.wall()]); self.particle(velocity=[-1,0,0], colliders={})
        self.scene.advance_to(8333); before = self.scene.particles(); clock = self.scene.info()['clock']
        self.scene.command({'op':'emitter-colliders','id':1,'colliders':{'surfaces':[1]}})
        self.assertEqual(before, self.scene.particles())
        self.assertEqual(clock, self.scene.info()['clock'])
        self.scene.advance_to(1100000)
        self.assertGreater(self.one()[6], 0)

    def testRainResponseIsPerSurfaceAndRingUsesContactNormal(self):
        self.surface(wetnessGain=.5); self.surface(2)
        self.mesh([self.wall()]); self.particle(effect='weather/silver-squall', sizeMin=.2,sizeMax=.2)
        self.scene.advance_to(8333)
        self.assertEqual(self.one()[2], 2)
        self.assertAlmostEqual(self.state()['wetness'], .1, places=8)
        self.assertEqual(self.state(2)['wetness'], 0)
        self.assertEqual(self.scene.info()['contacts'][0]['normal'], [1,0,0])
        snapshot = self.scene.snapshot()
        self.scene.render(); self.scene.render(); self.scene.info()
        self.assertEqual(snapshot, self.scene.snapshot())

    def testRainEvaporationAndCinderHeatHaveExplicitRates(self):
        self.surface(wetnessGain=.5, heatGain=.5)
        self.mesh([self.wall()])
        self.particle(effect='weather/silver-squall', sizeMin=.2, sizeMax=.2)
        self.particle(id=2, effect='weather/thermal-cinders', heat=0, sizeMin=.2, sizeMax=.2)
        self.scene.advance_to(8333)
        self.assertAlmostEqual(self.state()['wetness'], .1, places=8)
        self.assertAlmostEqual(self.state()['heat'], .1, places=8)
        self.scene.command({'op':'clear','scope':'weather'})
        self.scene.command({'op':'surface','id':1,'evaporation':.06,'cooling':.12})
        self.scene.advance_to(508333)
        self.assertAlmostEqual(self.state()['wetness'], .07, places=8)
        self.assertAlmostEqual(self.state()['heat'], .04, places=8)

    def testThermalEvaporationCouplesResponseWithoutRenderMutation(self):
        self.surface(wetnessGain=1, heatGain=1)
        self.mesh([self.wall()])
        self.particle(effect='weather/silver-squall',sizeMin=.2,sizeMax=.2)
        self.particle(id=2,effect='weather/thermal-cinders',heat=0,sizeMin=.2,sizeMax=.2)
        self.scene.advance_to(8333); self.scene.command({'op':'clear','scope':'weather'})
        self.scene.command({'op':'surface','id':1,'thermalEvaporation':1})
        self.scene.advance_to(508333)
        self.assertAlmostEqual(self.state()['wetness'], .1, places=8)
        self.assertAlmostEqual(self.state()['heat'], .2, places=8)

    def testSurfaceNormalDepositsKeepIdentityAfterEmitterRemoval(self):
        self.surface(); self.mesh([self.wall()]); self.particle(deposit=True)
        self.scene.advance_to(8333)
        deposit = self.scene.info()['deposits'][0]
        self.assertEqual(deposit['surfaceId'], 1)
        self.assertEqual(deposit['normal'], [1,0,0])
        self.assertAlmostEqual(deposit['position'][0], .02, places=5)
        self.assertEqual(deposit['position'][1], 0)
        self.scene.command({'op':'clear-instance','id':1})
        self.assertEqual(self.scene.info()['deposits'][0], deposit)

    def testRetentionAndClearAreScopedToSurface(self):
        self.surface(retentionMs=100); self.surface(2)
        self.mesh([self.wall(), self.wall(-1,2)])
        self.particle(deposit=True)
        self.particle(id=2,position=[-2,0,0],velocity=[240,0,0],deposit=True,colliders={'surfaces':[2]})
        self.scene.advance_to(8333)
        self.assertEqual(len(self.scene.info()['deposits']),2)
        self.scene.advance_to(108333)
        self.assertEqual([d['surfaceId'] for d in self.scene.info()['deposits']],[2])
        self.scene.command({'op':'clear-surface','id':2,'scope':'deposits'})
        self.assertEqual(self.scene.info()['deposits'],[])

    def testBoundedSurfaceAggregationAndRejectionAccountForEveryDeposit(self):
        self.surface(maxIndividual=1,maxTiles=1,overflow='merge-to-field')
        self.mesh([self.wall()]); self.particle(count=5,deposit=True)
        self.scene.advance_to(8333)
        state = self.state()
        self.assertEqual(state['individualDeposits'],1)
        self.assertEqual(state['aggregateDeposits'],4)
        self.assertEqual(state['rejectedDeposits'],0)
        self.scene.command({'op':'surface','id':1,'overflow':'reject-new'})
        self.particle(id=2,count=2,deposit=True); self.scene.advance_to(16666)
        self.assertEqual(self.state()['rejectedDeposits'],2)

    def testReentrainmentUsesSurfaceTangentAndOriginalGeneration(self):
        self.surface(reentrainWindSpeed=1); self.mesh([self.wall()]); self.particle(deposit=True)
        self.scene.advance_to(8333); identity=self.scene.info()['deposits'][0]['id']
        self.scene.command({'op':'forces','id':1,'wind':[0,5,0]})
        self.scene.advance_to(208333)
        self.assertEqual(self.scene.info()['deposits'],[])
        self.assertEqual(self.one()[0],identity)
        self.assertGreater(self.one()[6],0)

    def testMeshReplacementPreservesCapturedDepositAndAggregateGeometry(self):
        self.surface(maxIndividual=1,maxTiles=1,overflow='merge-to-field')
        self.mesh([self.wall()]); self.particle(count=3,deposit=True); self.scene.advance_to(8333)
        deposits=self.scene.info()['deposits']; state=self.state()
        self.mesh([self.wall(20)])
        self.assertEqual(self.scene.info()['deposits'],deposits)
        self.assertEqual(self.state()['aggregateDeposits'],state['aggregateDeposits'])

    def testMalformedSurfaceReferencesAndPoliciesRollbackWholeTransaction(self):
        self.surface(); before=self.scene.snapshot()
        invalid=[{'op':'surface','id':17}, {'op':'surface','id':1,'friction':1.01},
                 {'op':'surface','id':1,'unknown':True},
                 {'op':'surface','id':1,'maxTiles':0,'overflow':'merge-to-field'},
                 {'op':'surface','id':1,'retentionMs':10,'fadeMs':20},
                 {'op':'surface','id':1,'heatColor':16777216},
                 {'op':'mesh','triangles':[self.wall(surface=2)]},
                 {'op':'mesh','triangles':[dict(a=[0,0,0],b=[0,0,0],c=[1,1,1],surfaceId=1)]},
                 {'op':'clear-surface','id':2,'scope':'all'},
                 {'op':'clear-surface','id':1,'scope':'unbounded'}]
        for command in invalid:
            with self.subTest(command=command),self.assertRaises(ValueError):
                self.scene.command({'op':'batch','commands':[{'op':'input','text':'must roll back'},command]})
            self.assertEqual(before,self.scene.snapshot())
        for colliders in ({'surfaces':[2]}, {'surfaces':[1,1]}, {'surfaces':[0]},
                          {'surfaces':[1.5]}, {'floor':1}, {'unknown':1}, []):
            with self.subTest(colliders=colliders),self.assertRaises(ValueError):
                self.particle(colliders=colliders)
            self.assertEqual(before,self.scene.snapshot())

    def testDegenerateNearParallelAndMissSegmentsDoNotCollide(self):
        self.surface(); self.mesh([self.wall()])
        self.particle(position=[1,20,0])
        self.particle(id=2,position=[1,0,0],velocity=[0,240,0])
        self.particle(id=3,position=[0,0,0],velocity=[0,0,240])
        self.scene.advance_to(8333)
        self.assertEqual(self.state()['impacts'],0)

    def testNearDegenerateValidTriangleStillCollidesAndSmallerOneRejects(self):
        self.surface()
        self.mesh([dict(a=[0,0,0],b=[0,.0002,0],c=[0,0,.0001],surfaceId=1)])
        self.particle(position=[1,.00005,.000025])
        self.scene.advance_to(8333)
        self.assertEqual(self.one()[6],240*65536)
        before=self.scene.snapshot()
        with self.assertRaises(ValueError):
            self.mesh([dict(a=[0,0,0],b=[0,.00001,0],c=[0,0,.00001],surfaceId=1)])
        self.assertEqual(before,self.scene.snapshot())

    def testSelectedFloorWinsAnExactTriangleTie(self):
        self.surface();self.scene.command({'op':'floor','enabled':True,'restitution':.5,'friction':0})
        self.mesh([dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)])
        self.particle(position=[0,1,0],velocity=[0,-240,0],colliders={'floor':True,'surfaces':[1]})
        self.scene.advance_to(8333)
        self.assertEqual(self.one()[7],120*65536)
        self.assertEqual(self.scene.info()['contacts'][0]['surfaceId'],0)
        self.assertEqual(self.state()['impacts'],0)

    def testSnapshotReplayAndFrameRateDoNotAffectCollisionResponse(self):
        self.surface(); self.mesh([self.wall()]); self.particle(count=4,velocity=[-3,0,0],deposit=True)
        self.scene.advance_to(100000); before=self.scene.snapshot()
        for i in range(4,31):
            self.scene.advance_to(i*1000000//30); self.scene.render()
        expected=self.scene.snapshot(); expectedFrame=self.scene.render().bytes
        self.scene.restore(before)
        for i in range(7,61):
            self.scene.advance_to(i*1000000//60); self.scene.render()
        self.assertEqual(expected,self.scene.snapshot())
        self.assertEqual(expectedFrame,self.scene.render().bytes)

    def testPriorUnionSchema05LoadsWithoutAcquiringMeshCollisions(self):
        fixture=ROOT/'tests/fixtures/schema-20261005-geometry-baseline.snapshot.gz'
        original=gzip.decompress(fixture.read_bytes())
        self.assertEqual(int.from_bytes(original[12:16],'little'),0x20261005)
        self.scene.restore(original)
        self.assertEqual(self.scene.info()['surfaces'],[])
        self.assertEqual(self.scene.info()['emitters'][0]['colliders'],{'floor':True,'surfaces':[]})
        self.assertEqual(self.scene.info()['prompt']['text'],'geometry baseline retained')
        self.scene.advance_to(100000)
        self.assertLess(self.scene.particles()[0][6],0)


if __name__ == '__main__':
    unittest.main()
