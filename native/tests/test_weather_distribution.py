"""Independent volume and angular moments, not comparison with the C sampler."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

class WeatherDistribution(unittest.TestCase):
    def command(self,**changes):
        c=dict(op='emitter',id=1,effect='weather/autumn-drift',seed=791,
               count=2048,runningTimeMs=0,shape='sphere',distribution='uniform',
               extent=[20,20,20],position=[0,0,0],velocity=[0,0,0],
               spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],
               windVariation=[0,0,0],drag=0,lift=0,flutterAmount=0,
               collision=False,deposit=False)
        c.update(changes);return c

    def testUniformSphereHasVolumeCDFAndIsotropicAngularMoments(self):
        with NativeScene() as scene:
            scene.command(self.command());scene.advance_to(8333)
            points=[[v/65536/10 for v in p[3:6]] for p in scene.particles()]
        self.assertEqual(len(points),2048)
        radii=[math.sqrt(sum(v*v for v in p)) for p in points]
        self.assertLessEqual(max(radii),1.00001)
        for r in (.25,.5,.75):
            self.assertAlmostEqual(sum(x<=r for x in radii)/len(radii),r**3,delta=.035)
        for axis in range(3):
            dirs=[p[axis]/r for p,r in zip(points,radii)]
            self.assertAlmostEqual(sum(dirs)/len(dirs),0,delta=.05)
            self.assertAlmostEqual(sum(d**4 for d in dirs)/len(dirs),.2,delta=.025)

    def testUniformEllipsoidRespectsExtentAndFrame(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(self.command(extent=[2,4,6]));b.command(self.command(extent=[2,4,6],birthOrientation=[0,0,90]))
            a.advance_to(8333);b.advance_to(8333)
            for p,q in zip(a.particles(),b.particles()):
                self.assertLessEqual(sum((v/65536/r)**2 for v,r in zip(p[3:6],(1,2,3))),1.00003)
                self.assertAlmostEqual(q[3],-p[4],delta=2);self.assertAlmostEqual(q[4],p[3],delta=2)

    def testNestedCompilerAndSnapshotReplay(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(self.command(count=20,runningTimeMs=1000))
            b.command(dict(op='weather-author',schema='nocturne.weather-authoring/v1',id=1,effect='weather/autumn-drift',birth=dict(shape='sphere',distribution='uniform')))
            self.assertEqual(b.info()['emitters'][0]['distribution'],'uniform')
            a.advance_to(500000);b.restore(a.snapshot())
            a.advance_to(1000000);b.advance_to(1000000)
            self.assertEqual(a.snapshot(),b.snapshot())

    def testLegacyDefaultAndExplicitLegacyAreIdentical(self):
        with NativeScene() as a,NativeScene() as b:
            c=self.command();del c['distribution'];a.command(c)
            b.command(self.command(distribution='legacy'))
            a.advance_to(8333);b.advance_to(8333)
            self.assertEqual(a.snapshot(),b.snapshot())

    def testInvalidDistributionRejectsAtomically(self):
        with NativeScene() as scene:
            before=scene.snapshot()
            for value in ('gaussian',None,3,{},'Uniform'):
                with self.assertRaises(ValueError):scene.command(self.command(distribution=value))
                self.assertEqual(before,scene.snapshot())
