"""Regression tests for immediate data dispatch and motion scheduling."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'bindings/python'))
from terminal import MotionClock,AnsiWriter
from nocturne import Surface

class SchedulerTests(unittest.TestCase):
    def testThirtySamplesPerSecondWithoutDrift(self):
        clock=MotionClock()
        self.assertEqual(sum(clock.advance(ms) for ms in range(1000)),30)
        self.assertEqual(clock.lastMotionMs,966)
        self.assertTrue(clock.advance(1000))
        self.assertEqual(clock.lastMotionMs,1000)

    def testInputBetweenTicksRendersNow(self):
        clock=MotionClock()
        surface=Surface(layout=1)
        clock.advance(0)
        before=surface.render(clock.lastMotionMs,text='a')
        self.assertFalse(clock.advance(7))
        after=surface.render(clock.lastMotionMs,text='ab')
        self.assertNotEqual(before.tobytes(),after.tobytes())
        self.assertEqual(clock.lastMotionMs,0)

    def testPauseResumeHasNoVisualJump(self):
        clock=MotionClock()
        clock.advance(1000)
        clock.setPlaying(False,1000)
        self.assertFalse(clock.advance(6000))
        clock.setPlaying(True,6000)
        clock.advance(6000)
        self.assertEqual(clock.lastMotionMs,1000)
        clock.advance(6100)
        self.assertEqual(clock.lastMotionMs,1100)

    def testFrameSkippingDoesNotBurst(self):
        clock=MotionClock()
        clock.advance(0)
        self.assertTrue(clock.advance(2345))
        self.assertEqual(clock.lastMotionMs,2333)
        self.assertFalse(clock.advance(2345))

    def testDiffHasNoOutputForSameFrame(self):
        writer=AnsiWriter()
        surface=Surface(width=20,height=8)
        self.assertTrue(writer.encode(surface.render(100)))
        self.assertEqual(writer.encode(surface.render(100)),'')
        self.assertEqual(writer.lastChangedCells,0)

    def testSyncOutputIsOptIn(self):
        surface=Surface(width=3,height=2)
        self.assertNotIn('?2026',AnsiWriter().encode(surface.render(100)))
        encoded=AnsiWriter(True).encode(surface.render(100))
        self.assertTrue(encoded.startswith('\x1b[?2026h'))
        self.assertTrue(encoded.endswith('\x1b[?2026l'))

    def testInvalidFps(self):
        for value in [0,-1,241,30.5,True]:
            with self.assertRaises(ValueError):MotionClock(fps=value)

if __name__=='__main__':unittest.main()
