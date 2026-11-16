import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class GeometryComposition(unittest.TestCase):
 def testMeshAndModelAppendMatchCombinedAuthoredGeometry(self):
  base=dict(a=[0,0,0],b=[2,0,0],c=[0,0,2],surfaceId=1,color=0x123456)
  extra=dict(a=[0,1,0],b=[2,1,0],c=[0,1,2],surfaceId=2,color=0xabcdef,alpha=.5)
  model=dict(op='model-import',schema='nocturne.model/v1',units='meters',coordinates='right-handed-y-up',vertices=[extra[k] for k in ['a','b','c']],materials=[dict(color=extra['color'],alpha=.5)],triangles=[dict(indices=[0,1,2],material=0,surfaceId=2)],append=True)
  for command in [dict(op='mesh',triangles=[extra],append=True),model]:
   with self.subTest(op=command['op']),NativeScene(17) as a,NativeScene(17) as b:
    for s in [a,b]:
     s.command(dict(op='surface',id=1));s.command(dict(op='surface',id=2));s.command(dict(op='mesh',triangles=[base]))
    a.command(command);b.command(dict(op='mesh',triangles=[base,extra]));self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(a.render().bytes,b.render().bytes)
 def testMeshAppendPreservesFoamAndEmptyAppend(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='ribbon',points=[[0,0,0],[4,0,0]],width=2,surfaceId=1));s.command(dict(op='surface-waves',surfaceId=1,waves=[[1,1,0,0,0]]));s.command(dict(op='surface-foam',surfaceId=1,sourceRate=2,curvatureThreshold=0));s.advance_to(1000000);foam=s.surface_foam(1)
   s.command(dict(op='mesh',triangles=[dict(a=[0,1,0],b=[1,1,0],c=[0,1,1],surfaceId=1)],append=True));self.assertEqual(s.surface_foam(1)[:2],foam);self.assertEqual(s.surface_foam(1)[2][1:],[0,0,0,0]);before=s.snapshot();s.command(dict(op='mesh',triangles=[],append=True));self.assertEqual(before,s.snapshot())
 def testCombinedCapacityAndBooleanAreAtomic(self):
  with NativeScene() as s:
   t=dict(a=[0,0,0],b=[1,0,0],c=[0,0,1]);s.command(dict(op='mesh',triangles=[t]*256));before=s.snapshot()
   for c in [dict(op='mesh',triangles=[t],append=True),dict(op='mesh',triangles=[],append=1),dict(op='model-import',schema='nocturne.model/v1',units='meters',coordinates='right-handed-y-up',vertices=[[0,0,0],[1,0,0],[0,0,1]],materials=[dict(color=1)],triangles=[dict(indices=[0,1,2],material=0)],append=True)]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(before,s.snapshot())
