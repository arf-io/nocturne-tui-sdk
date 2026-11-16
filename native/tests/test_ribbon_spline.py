import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class RibbonSpline(unittest.TestCase):
 def testCatmullRomMatchesIndependentSampledPath(self):
  with NativeScene() as s,NativeScene() as r:
   base=dict(op='ribbon',width=1,color=0x123456)
   s.command(base|dict(points=[[0,0,0],[2,0,0],[2,0,2]],interpolation='catmull-rom',subdivisions=2))
   r.command(base|dict(points=[[0,0,0],[1,0,-.125],[2,0,0],[2.125,0,1],[2,0,2]]))
   self.assertEqual(s.snapshot(),r.snapshot())
 def testSplineCapacityAndBadOptionsAreAtomic(self):
  with NativeScene() as s:
   before=s.snapshot();base=dict(op='ribbon',points=[[i,0,0] for i in range(10)],interpolation='catmull-rom')
   for patch in [dict(subdivisions=16),dict(subdivisions=0),dict(interpolation='unknown'),dict(subdivisions=2.5)]:
    with self.assertRaises(ValueError):s.command(base|patch)
    self.assertEqual(before,s.snapshot())

 def testClosedSplineAndInterpolatedWidths(self):
  with NativeScene() as s,NativeScene() as r:
   base=dict(op='ribbon',closed=True)
   s.command(base|dict(points=[[0,0,0],[2,0,0],[2,0,2],[0,0,2]],widths=[1,2,3,4],interpolation='catmull-rom',subdivisions=2))
   r.command(base|dict(points=[[0,0,0],[1,0,-.25],[2,0,0],[2.25,0,1],[2,0,2],[1,0,2.25],[0,0,2],[-.25,0,1]],widths=[1,1.5,2,2.5,3,3.5,4,2.5]))
   self.assertEqual(s.snapshot(),r.snapshot())
