import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class WaterfallAssembly(unittest.TestCase):
 def setup_scene(self,s):
  for id in [1,2]:s.command(dict(op='surface',id=id))
  s.command(dict(op='ribbon',points=[[0,3,-2],[0,3,0]],width=2,surfaceId=1,color=0x809caa))
  s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='channel',delayUs=250000),dict(name='sheet',delayUs=250000)]))
 def testAssemblyMatchesSharedLipReferenceAndReplays(self):
  with NativeScene() as s,NativeScene() as ref:
   self.setup_scene(s);self.setup_scene(ref)
   s.command(dict(op='waterfall',channelSurfaceId=1,sheetSurfaceId=2,flowId=1,channelStage='channel',sheetStage='sheet',referenceFlux=2,drop=3))
   ref.command(dict(op='mesh',append=True,triangles=[dict(a=[1,3,0],b=[-1,3,0],c=[1,0,0],surfaceId=2,color=0x809caa,alpha=1),dict(a=[-1,3,0],b=[-1,0,0],c=[1,0,0],surfaceId=2,color=0x809caa,alpha=1)]))
   for surface,stage in [(1,'channel'),(2,'sheet')]:ref.command(dict(op='flow-surface',surfaceId=surface,flowId=1,stage=stage,referenceFlux=2))
   self.assertEqual(s.snapshot(),ref.snapshot())
   s.advance_to(750000);saved=s.snapshot();s.render();self.assertEqual(saved,s.snapshot());s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(1500000);expected=s.snapshot();s.restore(saved);s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(1500000);self.assertEqual(expected,s.snapshot())
 def testInvalidAssemblyDoesNotPartiallyAddSheet(self):
  with NativeScene() as s:
   self.setup_scene(s);before=s.snapshot();c=dict(op='waterfall',channelSurfaceId=1,sheetSurfaceId=2,flowId=1,channelStage='channel',sheetStage='sheet',referenceFlux=2,drop=3)
   for patch in [dict(drop=0),dict(sheetStage='absent'),dict(sheetSurfaceId=1),dict(flowId=999)]:
    with self.assertRaises(ValueError):s.command(c|patch)
    self.assertEqual(before,s.snapshot())
