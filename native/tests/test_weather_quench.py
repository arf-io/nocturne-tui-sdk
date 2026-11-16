"""Quenching stops heat acceleration, preserves momentum and rejects unsupported use."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class WeatherQuench(unittest.TestCase):
    def emitter(self,**changes):
        c=dict(op='emitter',id=1,effect='weather/thermal-cinders',count=1,runningTimeMs=0,shape='point',position=[0,0,0],extent=[0,0,0],velocity=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,heat=12,radius=100,collision=False,deposit=False,lifetimeMinMs=10000,lifetimeMaxMs=10000)
        c.update(changes);return c
    def testQuenchStopsHeatAccelerationWithoutResettingPositionOrVelocity(self):
        with NativeScene() as s:
            s.command(self.emitter());s.advance_to(500000);p=s.particles()[0]
            s.command(dict(op='stop',id=1,style='quench',tailMs=1000))
            self.assertEqual(p,s.particles()[0]);s.advance_to(750000);q=s.particles()[0]
            self.assertEqual(p[6:9],q[6:9]);self.assertGreater(q[4],p[4])
    def testDissolveRetainsThermalAscentAndDiffersFromQuench(self):
        with NativeScene() as a,NativeScene() as b:
            for s in (a,b):s.command(self.emitter());s.advance_to(500000)
            a.command(dict(op='stop',id=1,style='quench',tailMs=1000));b.command(dict(op='stop',id=1,style='dissolve',tailMs=1000))
            for s in (a,b):s.advance_to(750000)
            self.assertLess(a.particles()[0][7],b.particles()[0][7])
    def testQuenchRejectsUnsupportedEffectAtCreationAndStop(self):
        with NativeScene() as s:
            before=s.snapshot()
            with self.assertRaises(ValueError):s.command(self.emitter(effect='weather/autumn-drift',endStyle='quench'))
            self.assertEqual(before,s.snapshot());s.command(self.emitter(effect='weather/autumn-drift'))
            before=s.snapshot()
            with self.assertRaises(ValueError):s.command(dict(op='stop',id=1,style='quench',tailMs=1000))
            self.assertEqual(before,s.snapshot())
    def testQuenchReplayDeadlineAndIdempotentStop(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(self.emitter());a.advance_to(500000)
            stop=dict(op='stop',id=1,style='quench',tailMs=1000);a.command(stop);a.advance_to(750000)
            before=a.snapshot();a.command(stop);self.assertEqual(before,a.snapshot());b.restore(before)
            for s in (a,b):s.advance_to(1500000)
            self.assertEqual(a.particles(),[]);self.assertEqual(a.snapshot(),b.snapshot())
