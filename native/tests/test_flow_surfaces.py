import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class FlowSurfaces(unittest.TestCase):
 def setup_scene(self,s):
  s.command(dict(op='surface',id=1))
  s.command(dict(op='mesh',triangles=[dict(a=[-4,-2,0],b=[4,-2,0],c=[0,4,0],surfaceId=1,alpha=1,color=0xffffff)]))
  s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='sheet',delayUs=500000)]))
 def testDelayedVisibilityAndPureReplay(self):
  with NativeScene() as s, NativeScene() as ref:
   self.setup_scene(s);self.setup_scene(ref)
   ref.command(dict(op='mesh',triangles=[]))
   s.command(dict(op='flow-surface',flowId=1,stage='sheet',surfaceId=1,referenceFlux=2))
   before=s.snapshot();self.assertEqual(s.render(),ref.render());self.assertEqual(before,s.snapshot())
   s.advance_to(500000);ref.advance_to(500000);self.assertNotEqual(s.render(),ref.render())
   visible=s.snapshot();frame=s.render();s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(1000000);ref.advance_to(1000000)
   self.assertEqual(s.render(),ref.render());s.restore(visible);self.assertEqual(frame,s.render())
 def testInvalidBindingIsAtomic(self):
  with NativeScene() as s:
   self.setup_scene(s);before=s.snapshot()
   base=dict(op='flow-surface',flowId=1,stage='sheet',surfaceId=1,referenceFlux=2)
   for patch in [dict(flowId=999),dict(stage='absent'),dict(surfaceId=2),dict(referenceFlux=0)]:
    with self.assertRaises(ValueError):s.command(base|patch)
    self.assertEqual(before,s.snapshot())

 def testSchema19PreservesFlowsWithoutBindings(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);baseline=s.render();data=bytearray(s.snapshot());payload=data[24:24+5089424]
   struct.pack_into('<I',payload,4,0x20261019);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261019,len(payload),zlib.crc32(payload))
   s.restore(data);self.assertEqual(baseline,s.render());self.assertEqual(s.info()['flows'][0]['flux'],2)
