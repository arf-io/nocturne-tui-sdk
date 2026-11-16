"""Independent emission-clock suspension, ownership and resume boundaries."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class EmitterResume(unittest.TestCase):
    def emitter(self,s,**patch):
        c=dict(op='emitter',id=1,rate=4,runningTimeMs=0,lifetimeMinMs=5000,lifetimeMaxMs=5000,collision=False,deposit=False)
        c.update(patch);s.command(c)
    def stop(self,s):s.command(dict(op='stop',id=1,style='drain'))
    def resume(self,s):s.command(dict(op='resume',id=1))
    def testRemainingRateIntervalAndIdentityArePreserved(self):
        with NativeScene() as s:
            self.emitter(s);s.advance_to(250000);self.stop(s);s.advance_to(1000000)
            old=s.particles();self.resume(s);self.assertEqual(old,s.particles())
            s.advance_to(1241666);self.assertEqual(len(s.particles()),1)
            s.advance_to(1250000);self.assertEqual([p[0] for p in s.particles()],[1,2])
    def testScheduledStartRetainsRemainingDelay(self):
        with NativeScene() as s:
            self.emitter(s,startTimeUs=1000000);self.stop(s);s.advance_to(500000);self.resume(s)
            s.advance_to(1741666);self.assertEqual(s.particles(),[])
            s.advance_to(1750000);self.assertEqual(len(s.particles()),1)
    def testRepeatedResumeAndStopAreIdempotent(self):
        with NativeScene() as s:
            self.emitter(s);self.stop(s);s.advance_to(250000);saved=s.snapshot();self.stop(s);self.assertEqual(saved,s.snapshot())
            self.resume(s);saved=s.snapshot();self.resume(s);self.assertEqual(saved,s.snapshot())
            s.advance_to(500000);self.assertEqual(len(s.particles()),1)
    def testParticleLifetimeContinuesDuringStoppedEmission(self):
        with NativeScene() as s:
            self.emitter(s,lifetimeMinMs=300,lifetimeMaxMs=300);s.advance_to(250000);self.stop(s)
            s.advance_to(1000000);self.assertEqual(s.particles(),[]);self.resume(s)
            s.advance_to(1250000);self.assertEqual([p[0] for p in s.particles()],[2])
    def testDestructiveTailCannotBeUndoneByResume(self):
        with NativeScene() as s:
            self.emitter(s);s.advance_to(250000);s.command(dict(op='stop',id=1,style='dissolve',tailMs=1000));saved=s.snapshot()
            with self.assertRaises(ValueError):self.resume(s)
            self.assertEqual(saved,s.snapshot())
    def testSnapshotReplayAndRenderingDoNotChangeSuspendedClock(self):
        with NativeScene() as a,NativeScene() as b:
            self.emitter(a);a.advance_to(250000);self.stop(a);a.advance_to(500000);b.restore(a.snapshot())
            saved=a.snapshot();a.render();a.info_complete();self.assertEqual(saved,a.snapshot())
            for s in (a,b):s.advance_to(1000000);self.resume(s);s.advance_to(1500000)
            self.assertEqual(a.snapshot(),b.snapshot())
    def testShiftBeyondSupportedScheduleRangeIsAtomicRejection(self):
        with NativeScene() as s:
            self.emitter(s,startTimeUs=86400000000);self.stop(s);s.advance_to(8333);saved=s.snapshot()
            with self.assertRaises(ValueError):self.resume(s)
            self.assertEqual(saved,s.snapshot())
    def testFiniteScheduleHasNoCatchupOrOrdinalReset(self):
        with NativeScene() as s:
            s.command(dict(op='emitter',id=1,count=4,runningTimeMs=1000,cycles=2,gapMs=500,lifetimeMinMs=5000,lifetimeMaxMs=5000,collision=False,deposit=False))
            s.advance_to(250000);self.assertEqual(len(s.particles()),2);self.stop(s);s.advance_to(1250000);self.resume(s)
            s.advance_to(1491666);self.assertEqual(len(s.particles()),2)
            s.advance_to(1500000);self.assertEqual(len(s.particles()),3)
            s.advance_to(4000000);self.assertEqual(s.info()['emitters'][0]['attemptedBirths'],8)
