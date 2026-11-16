"""Reusable ribbon compilation against independently authored geometry."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class Ribbon(unittest.TestCase):
 def testStraightRibbonMatchesIndependentMesh(self):
  with NativeScene(17) as a,NativeScene(17) as b:
   a.command(dict(op='ribbon',points=[[0,0,0],[4,0,0]],width=2,color=0x123456,alpha=.75))
   b.command(dict(op='mesh',triangles=[dict(a=[0,0,-1],b=[0,0,1],c=[4,0,-1],color=0x123456,alpha=.75),dict(a=[0,0,1],b=[4,0,1],c=[4,0,-1],color=0x123456,alpha=.75)]))
   self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(a.render().bytes,b.render().bytes)
 def testRightAngleMiterAndVariableWidths(self):
  with NativeScene(17) as a,NativeScene(17) as b:
   a.command(dict(op='ribbon',points=[[0,0,0],[4,0,0],[4,0,4]],widths=[2,2,4]))
   left=[[0,0,-1],[5,0,-1],[6,0,4]];right=[[0,0,1],[3,0,1],[2,0,4]];triangles=[]
   for i in range(2):
    triangles += [dict(a=left[i],b=right[i],c=left[i+1]),dict(a=right[i],b=right[i+1],c=left[i+1])]
   b.command(dict(op='mesh',triangles=triangles));self.assertEqual(a.snapshot(),b.snapshot())
 def testRejectionIsAtomic(self):
  with NativeScene() as s:
   before=s.snapshot()
   for patch in [dict(points=[]),dict(points=[[0,0,0],[0,0,0]]),dict(points=[[0,0,0],[0,1,0]]),dict(width=0),dict(widths=[1]),dict(up=[0,0,0]),dict(surfaceId=1),dict(points=[[0,0,0],[1,0,0],[0,0,0]]),dict(miterLimit=.5),dict(extra=True),dict(points=[[0,0,0]]*130)]:
    command=dict(op='ribbon',points=[[0,0,0],[4,0,0]],width=2);command.update(patch)
    with self.subTest(patch=patch):
     with self.assertRaises(ValueError):s.command(command)
     self.assertEqual(before,s.snapshot())
 def testClosedSurfaceReplayAndPureRender(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='ribbon',points=[[0,0,0],[4,0,0],[4,0,4],[0,0,4]],width=.5,closed=True,surfaceId=1))
   self.assertEqual(s.info()['geometry']['collisionTriangles'],8)
   before=s.snapshot();s.render();self.assertEqual(before,s.snapshot());s.command(dict(op='reset'));s.restore(before);self.assertEqual(before,s.snapshot())

 def testRibbonSupportsActualParticleContact(self):
  with NativeScene() as s:
   s.command(dict(op='floor',enabled=False));s.command(dict(op='surface',id=1,restitution=1,friction=0))
   s.command(dict(op='ribbon',points=[[-4,0,0],[4,0,0]],width=4,surfaceId=1))
   s.command(dict(op='emitter',id=1,count=1,runningTimeMs=0,shape='point',position=[0,1,0],velocity=[0,-240,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterAmount=0,collision=True,deposit=False,colliders=dict(surfaces=[1])))
   s.advance_to(8333);self.assertEqual(s.particles()[0][7],240*65536)
 def testCustomUpCompilesVerticalRibbon(self):
  with NativeScene(17) as a,NativeScene(17) as b:
   a.command(dict(op='ribbon',points=[[0,0,0],[4,0,0]],width=2,up=[0,0,1]))
   b.command(dict(op='mesh',triangles=[dict(a=[0,1,0],b=[0,-1,0],c=[4,1,0]),dict(a=[0,-1,0],b=[4,-1,0],c=[4,1,0])]))
   self.assertEqual(a.snapshot(),b.snapshot())
 def testAppendPreservesExistingSurfaceAndBuildsCombinedCollisionIndex(self):
  with NativeScene(17) as a,NativeScene(17) as b:
   base=dict(a=[0,-1,0],b=[1,-1,0],c=[0,-1,1],surfaceId=1)
   road=[dict(a=[0,0,-1],b=[0,0,1],c=[4,0,-1],surfaceId=2),dict(a=[0,0,1],b=[4,0,1],c=[4,0,-1],surfaceId=2)]
   for scene in [a,b]:
    scene.command(dict(op='surface',id=1));scene.command(dict(op='surface',id=2));scene.command(dict(op='mesh',triangles=[base]))
   a.command(dict(op='ribbon',points=[[0,0,0],[4,0,0]],width=2,surfaceId=2,append=True))
   b.command(dict(op='mesh',triangles=[base]+road))
   self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(a.info()['geometry']['collisionTriangles'],3)
 def testAppendCapacityAndInvalidFlagAreAtomic(self):
  with NativeScene() as s:
   triangle=dict(a=[0,0,0],b=[1,0,0],c=[0,0,1]);s.command(dict(op='mesh',triangles=[triangle]*255));before=s.snapshot()
   for flag in [True,1]:
    with self.assertRaises(ValueError):s.command(dict(op='ribbon',points=[[0,0,0],[4,0,0]],append=flag))
    self.assertEqual(before,s.snapshot())

 def testAppendPreservesFoamOnExistingTriangles(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='ribbon',points=[[0,0,0],[4,0,0]],width=2,surfaceId=1));s.command(dict(op='surface-waves',surfaceId=1,waves=[[1,1,0,0,0]]));s.command(dict(op='surface-foam',surfaceId=1,sourceRate=2,curvatureThreshold=0));s.advance_to(1000000)
   rows=s.surface_foam(1);self.assertGreater(rows[0][1],0);s.command(dict(op='ribbon',points=[[0,0,5],[4,0,5]],width=2,surfaceId=1,append=True));after=s.surface_foam(1)
   self.assertEqual(after[:2],rows);self.assertEqual(after[2][1:],[0,0,0,0]);held=s.snapshot();s.restore(held);self.assertEqual(s.surface_foam(1),after)
