"""Acceptance tests written before the renderer implementation."""
import ctypes as ct
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings' / 'python'))
from nocturne import Surface, DEFAULTS, KEYS


class CoreTests(unittest.TestCase):
    def testRepeatedFrameIsIdentical(self):
        with Surface(width=67, height=23, stars=1, effect=5, seed=414) as surface:
            self.assertEqual(surface.render(1973).tobytes(), surface.render(1973).tobytes())

    def testNoHiddenFrameHistory(self):
        with Surface(width=49, height=19, stars=1, effect=5) as first, Surface(width=49, height=19, stars=1, effect=5) as second:
            first.render(0)
            first.render(19)
            first.render(99876)
            self.assertEqual(first.render(12345).tobytes(), second.render(12345).tobytes())

    def testStarsSurviveGrowth(self):
        with Surface(width=23, height=9, layout=0, effect=0, stars=1, densityPermille=800) as small, Surface(width=45, height=18, layout=0, effect=0, stars=1, densityPermille=800) as large:
            a, b = small.render(17231), large.render(17231)
            for y in range(9):
                for x in range(23):
                    self.assertEqual(a.cell(x,y), b.cell(x,y))

    def testOriginSupportsWorldAnchoring(self):
        with Surface(width=48,height=20,layout=0,effect=0,stars=1) as big, Surface(width=21,height=7,originX=5,originY=8,layout=0,effect=0,stars=1) as part:
            a,b=big.render(2000),part.render(2000)
            for y in range(7):
                for x in range(21):
                    self.assertEqual(a.cell(x+5,y+8),b.cell(x,y))

    def testDifferentSeedsDiffer(self):
        with Surface(width=64,height=24,seed=1,densityPermille=500) as a, Surface(width=64,height=24,seed=2,densityPermille=500) as b:
            self.assertNotEqual(a.render(1000).tobytes(),b.render(1000).tobytes())

    def testDataCanChangeAtFrozenMotionTime(self):
        with Surface(width=82,height=26,layout=2,effect=5,stars=1) as surface:
            before=surface.render(5000,text='before',valuePermille=200)
            after=surface.render(5000,text='after',valuePermille=900)
            self.assertNotEqual(before.tobytes(),after.tobytes())
            self.assertEqual(before.cell(2,2),after.cell(2,2))

    def testPauseDoesNotFreezeData(self):
        with Surface(layout=1,motion=0,effect=5,stars=1) as surface:
            self.assertEqual(surface.render(123,text='x').tobytes(),surface.render(99494,text='x').tobytes())
            self.assertNotEqual(surface.render(123,text='x').tobytes(),surface.render(123,text='z').tobytes())

    def testGradientPeriod(self):
        for effect in range(1,6):
            with Surface(layout=0,stars=0,effect=effect,gradientPeriodMs=2700) as surface:
                self.assertEqual(surface.render(511).tobytes(),surface.render(3211).tobytes(),effect)

    def testNeighborSpeedAndSaturation(self):
        with Surface() as surface:
            self.assertEqual([surface.rowPeriod(d) for d in range(5)],[3200,6400,12800,25600,51200])
            self.assertEqual([surface.rowSaturation(d) for d in range(4)],[700,434,269,166])

    def testAllLayoutsAndMaterialsHaveValidCells(self):
        for layout in range(5):
            for effect in range(6):
                with Surface(width=71,height=25,layout=layout,effect=effect,stars=1,pixelMode=effect%5) as surface:
                    frame=surface.render(6789,text='safe text',valuePermille=810)
                    self.assertEqual(len(frame.cells),71*25)
                    for cell in frame.cells:
                        self.assertLessEqual(cell.fg,0xffffff)
                        self.assertLessEqual(cell.bg,0xffffff)
                        self.assertTrue(32 <= cell.glyph <= 0x10ffff)

    def testTinyAndEmptySurfaces(self):
        for w,h in [(0,0),(0,10),(1,1),(2,2),(1,20),(512,1),(1,256)]:
            with Surface(width=w,height=h,layout=2,modalOpen=1) as surface:
                self.assertEqual(len(surface.render(330).cells),w*h)

    def testInvalidConfigIsRejected(self):
        for changes in [dict(width=-1),dict(width=513),dict(height=257),dict(densityPermille=1001),dict(gradientPeriodMs=0),dict(effect=9),dict(foo=1),dict(width=1.5),dict(seed=True)]:
            with self.assertRaises((ValueError,TypeError)):
                Surface(**changes)

    def testUnsafeTextDoesNotEscape(self):
        with Surface(layout=1) as surface:
            frame=surface.render(100,text='hello\x1b[31m\n\r\t世界')
            self.assertNotIn('\x1b',frame.plaintext())
            self.assertNotIn('\r',frame.plaintext())

    def testCustomPalettesAndGlyphs(self):
        with Surface(width=80,height=30,layout=0,effect=0,stars=1,densityPermille=1000,starFloorPermille=1000) as surface:
            surface.setStarPalette(['#998877'])
            surface.setGlyphs(['.'])
            frame=surface.render(12345)
            self.assertTrue(any(c.glyph==46 for c in frame.cells))
            self.assertTrue(all(c.glyph in (32,46) for c in frame.cells))

    def testHueStepIsConfigurable(self):
        with Surface(layout=3,hueStepDegrees=0,hueSaturationPermille=600) as surface:
            a=surface.render(1000,text='COLOR')
            surface.configure(hueStepDegrees=41)
            self.assertNotEqual(a.tobytes(),surface.render(1000,text='COLOR').tobytes())

    def testNoStarsMeansNoStarGlyphs(self):
        with Surface(layout=0,effect=0,stars=0) as surface:
            self.assertTrue(all(c.glyph==32 for c in surface.render(99).cells))

    def testReturnFramesDoNotAliasScratchMemory(self):
        with Surface(width=16,height=8) as surface:
            first=surface.render(100)
            saved=first.tobytes()
            surface.render(2099)
            self.assertEqual(first.tobytes(),saved)

    def testAllFivePixelModesDiffer(self):
        hashes=[]
        for mode in range(5):
            with Surface(layout=0,effect=5,stars=0,pixelMode=mode) as surface:
                hashes.append(hashlib.sha256(surface.render(900).tobytes()).hexdigest())
        self.assertEqual(len(set(hashes)),5)

if __name__ == '__main__':
    unittest.main()
