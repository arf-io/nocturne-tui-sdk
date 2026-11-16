import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class FlowSinks(unittest.TestCase):
 def setup_scene(self,s):
  for id in [1,2]:s.command(dict(op='surface',id=id))
  s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='basin')]))
 def testReceivedRetainedEvaporatedBalanceAndTail(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='flow-sink',surfaceId=1,flowId=1,fraction=.5,evaporationUs=500000,capacity=1));s.advance_to(1000000)
   q=s.info()['flowSinks'][0];expected=.5*(1-math.exp(-2));self.assertAlmostEqual(q['receivedVolume'],1);self.assertAlmostEqual(q['retainedVolume'],expected,places=5);self.assertAlmostEqual(q['evaporatedVolume'],1-expected,places=5)
   saved=s.snapshot();s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(2000000);self.assertAlmostEqual(s.info()['flowSinks'][0]['retainedVolume'],expected*math.exp(-2),places=5);result=s.snapshot();s.restore(saved);s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(2000000);self.assertEqual(result,s.snapshot())
 def testLateAttachmentStartsWithNoPreviousWater(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(1000000);s.command(dict(op='flow-sink',surfaceId=1,flowId=1,fraction=1,evaporationUs=500000,capacity=1));self.assertEqual(s.info()['flowSinks'][0]['receivedVolume'],0);s.advance_to(2000000);self.assertAlmostEqual(s.info()['flowSinks'][0]['retainedVolume'],1-math.exp(-2),places=5)
 def testOverAllocationAndRebindingRejectAtomically(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='flow-sink',surfaceId=1,flowId=1,fraction=.5,capacity=1));before=s.snapshot()
   for c in [dict(op='flow-sink',surfaceId=2,flowId=1,fraction=.75,capacity=1),dict(op='flow-sink',surfaceId=1,flowId=1,fraction=.25,capacity=1)]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(before,s.snapshot())

 def testWetnessChangesRenderedBasinWithoutChangingAuthoredState(self):
  with NativeScene() as s,NativeScene() as r:
   for x in [s,r]:
    self.setup_scene(x);x.command(dict(op='mesh',triangles=[dict(a=[-4,-2,0],b=[4,-2,0],c=[0,4,0],surfaceId=1,color=0xffffff,alpha=1)]))
   s.command(dict(op='flow-sink',surfaceId=1,flowId=1,fraction=1,capacity=1));s.advance_to(1000000);r.advance_to(1000000);before=s.snapshot();self.assertNotEqual(s.render(),r.render());self.assertEqual(before,s.snapshot())

 def testPreviousSchemaAndCorruptAllocationRestore(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);data=bytearray(s.snapshot());payload=data[24:24+5089680];struct.pack_into('<I',payload,4,0x20261020);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261020,len(payload),zlib.crc32(payload));s.restore(data);self.assertNotIn('flowSinks',s.info())
   s.command(dict(op='flow-sink',surfaceId=1,flowId=1,fraction=.5,capacity=1));before=s.snapshot();bad=bytearray(before);struct.pack_into('<d',bad,24+5089680+8,2);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())
