"""Lifecycle phases reflect pending work and stopped ownership, without rendering."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class EmitterPhase(unittest.TestCase):
    def emitter(self,s,**patch):
        c=dict(op='emitter',id=1,count=1,runningTimeMs=0,collision=False,deposit=False);c.update(patch);s.command(c)
    def phase(self,s):return s.info()['emitters'][0]['phase']
    def testImmediateBurstWithPendingBirthIsEmitting(self):
        with NativeScene() as s:
            self.emitter(s);self.assertEqual(self.phase(s),'emitting')
            s.advance_to(8333);self.assertEqual(self.phase(s),'draining');self.assertEqual(len(s.particles()),1)
    def testStoppedFutureEmitterIsImmediatelyTerminal(self):
        with NativeScene() as s:
            self.emitter(s,startTimeUs=1000000);self.assertEqual(self.phase(s),'scheduled')
            s.command(dict(op='stop',id=1,style='drain'));self.assertEqual(self.phase(s),'terminal')
            saved=s.snapshot();s.render();s.info_complete();self.assertEqual(saved,s.snapshot())
    def testStoppedFutureEmitterNeverResurrectsAcrossStartOrCameraEdits(self):
        with NativeScene() as s:
            self.emitter(s,startTimeUs=1000000);s.command(dict(op='stop',id=1,style='drain'))
            s.command(dict(op='camera',position=[1000,1000,1000]))
            for time in (500000,1000000,2000000):
                s.advance_to(time);self.assertEqual(self.phase(s),'terminal');self.assertEqual(s.particles(),[])
    def testEmptyImmediateBurstIsTerminal(self):
        with NativeScene() as s:
            self.emitter(s,count=0);self.assertEqual(self.phase(s),'terminal')
    def testSnapshotReplayRetainsStoppedFuturePhase(self):
        with NativeScene() as a,NativeScene() as b:
            self.emitter(a,startTimeUs=1000000);a.command(dict(op='stop',id=1,style='dissolve',tailMs=500))
            b.restore(a.snapshot());self.assertEqual(self.phase(b),'terminal')
            for s in (a,b):s.advance_to(1500000)
            self.assertEqual(a.snapshot(),b.snapshot())
