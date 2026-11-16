"""Explicit destructive cancellation preserves ownership and follows tail clock."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class EmitterCancel(unittest.TestCase):
    def emitter(self,s,**patch):
        c=dict(op='emitter',id=1,rate=4,runningTimeMs=0,lifetimeMinMs=5000,lifetimeMaxMs=5000,tailMs=500,collision=False,deposit=False)
        c.update(patch);s.command(c)
    def testDefaultCancelUsesDissolveTailWithoutImmediateParticleChange(self):
        with NativeScene() as s:
            self.emitter(s);s.advance_to(250000);old=s.particles();s.command(dict(op='cancel',id=1));self.assertEqual(old,s.particles())
            s.advance_to(500000);self.assertEqual(len(s.particles()),1)
            s.advance_to(750000);self.assertEqual(s.particles(),[]);self.assertEqual(s.info()['emitters'][0]['attemptedBirths'],1)
    def testCancelPreservesAuthoredNonDrainStyleAndRepeatedDeadline(self):
        with NativeScene() as a,NativeScene() as b:
            for s in (a,b):
                self.emitter(s,endStyle='gust');s.advance_to(250000)
            a.command(dict(op='cancel',id=1));b.command(dict(op='stop',id=1,style='gust'))
            self.assertEqual(a.snapshot(),b.snapshot());a.advance_to(500000);saved=a.snapshot();a.command(dict(op='cancel',id=1));self.assertEqual(saved,a.snapshot())
            a.advance_to(750000);self.assertEqual(a.particles(),[])
    def testDrainAndResumeAreRejectedAtomically(self):
        with NativeScene() as s:
            self.emitter(s);saved=s.snapshot()
            with self.assertRaises(ValueError):s.command(dict(op='cancel',id=1,style='drain'))
            self.assertEqual(saved,s.snapshot());s.command(dict(op='cancel',id=1))
            saved=s.snapshot()
            with self.assertRaises(ValueError):s.command(dict(op='resume',id=1))
            self.assertEqual(saved,s.snapshot())
    def testCancelAndClearLeaveSceneOwnedDeposits(self):
        with NativeScene() as s:
            s.command(dict(op='emitter',id=1,count=3,runningTimeMs=0,position=[0,.1,0],extent=[0,0,0],velocity=[0,-3,0],collision=True,deposit=True))
            s.advance_to(200000);self.assertEqual(s.info()['particles']['deposited'],3)
            s.command(dict(op='cancel',id=1,tailMs=100));s.advance_to(400000)
            self.assertEqual(s.info()['particles']['deposited'],3);s.command(dict(op='clear-instance',id=1));self.assertEqual(s.info()['particles']['deposited'],3)
    def testUnsupportedCancelAndUnknownFieldsPreserveState(self):
        with NativeScene() as s:
            self.emitter(s)
            for patch in ({'style':'quench'},{'unexpected':True},{'id':2}):
                saved=s.snapshot();c=dict(op='cancel',id=1);c.update(patch)
                with self.assertRaises(ValueError):s.command(c)
                self.assertEqual(saved,s.snapshot())
    def testCancelAfterDrainStopStartsSeparateEndingClock(self):
        with NativeScene() as s:
            self.emitter(s);s.advance_to(250000);s.command(dict(op='stop',id=1,style='drain'));s.advance_to(1000000)
            s.command(dict(op='cancel',id=1,tailMs=500));s.advance_to(1250000);self.assertEqual(len(s.particles()),1)
            s.advance_to(1500000);self.assertEqual(s.particles(),[])
