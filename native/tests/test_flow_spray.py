"""Spray is allocated outlet water; capacity pressure must retain pending volume."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class FlowSpray(unittest.TestCase):
 def setup_scene(self,s,volume=.1):
  s.command(dict(op='emitter',id=1,effect='weather/rain-threads',count=0,lifetimeMinMs=10000,lifetimeMaxMs=10000))
  s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='spray',delayUs=250000)]))
  s.command(dict(op='flow-spray',flowId=1,emitterId=1,fraction=.5,particleVolume=volume))
 def testDelayedBirthsAndVolumeLedger(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(200000);self.assertEqual(s.info()['particles']['born'],0)
   s.advance_to(1000000);q=s.info()['flowSprays'][0];self.assertAlmostEqual(q['receivedVolume'],.75);self.assertAlmostEqual(q['emittedVolume'],.7);self.assertAlmostEqual(q['pendingVolume'],.05);self.assertEqual(s.info()['particles']['born'],7)
   saved=s.snapshot();s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(1500000);q=s.info()['flowSprays'][0];self.assertAlmostEqual(q['receivedVolume'],1);self.assertAlmostEqual(q['emittedVolume'],1);self.assertAlmostEqual(q['pendingVolume'],0);expected=s.snapshot();s.restore(saved);s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(1500000);self.assertEqual(expected,s.snapshot())
 def testFullParticleCapacityRetainsUnemittedWater(self):
  with NativeScene() as s:
   self.setup_scene(s,volume=.0001);s.advance_to(1000000);q=s.info()['flowSprays'][0]
   self.assertEqual(s.info()['particles']['active'],2048)
   self.assertAlmostEqual(q['receivedVolume'],q['emittedVolume']+q['pendingVolume'],places=6)
   self.assertGreater(q['pendingVolume'],.5)
 def testBasinAndSprayCannotOverAllocateTheOutlet(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface',id=1));before=s.snapshot()
   with self.assertRaises(ValueError):s.command(dict(op='flow-sink',flowId=1,surfaceId=1,fraction=.75,capacity=1))
   self.assertEqual(before,s.snapshot())

 def testClearCannotEraseAllocatedWater(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(1000000);before=s.snapshot()
   for c in [dict(op='clear-instance',id=1),dict(op='clear',scope='weather')]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(before,s.snapshot())
 def testPreviousSchemaAndCorruptOrdinalRestore(self):
  import struct,zlib
  with NativeScene() as s:
   data=bytearray(s.snapshot());payload=data[24:24+5090576];struct.pack_into('<I',payload,4,0x20261021);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261021,len(payload),zlib.crc32(payload));s.restore(data);self.assertNotIn('flowSprays',s.info())
   self.setup_scene(s);s.advance_to(1000000);before=s.snapshot();bad=bytearray(before);struct.pack_into('<i',bad,24+5090576+48,999);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())

 def testExpiredParticlesRetainOwnedVolumeInLedger(self):
  with NativeScene() as s:
   s.command(dict(op='emitter',id=1,effect='weather/rain-threads',count=0,lifetimeMinMs=100,lifetimeMaxMs=100,collision=False))
   s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='spray')]))
   s.command(dict(op='flow-spray',flowId=1,emitterId=1,fraction=.5,particleVolume=.1));s.advance_to(1000000)
   q=s.info()['flowSprays'][0];self.assertGreater(q['expiredVolume'],0);self.assertAlmostEqual(q['emittedVolume'],q['liveVolume']+q['expiredVolume']+q['impactedVolume']+q['exportedVolume'],places=6)

 def testImpactTransfersWaterOutOfVisualPressureShell(self):
  with NativeScene() as s:
   s.command(dict(op='floor',enabled=True,height=0));s.command(dict(op='emitter',id=1,effect='weather/rain-threads',count=0,position=[0,1,0],extent=[0,0,0],velocity=[0,-10,0],gravity=[0,0,0],collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000));s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='spray')]));s.command(dict(op='flow-spray',flowId=1,emitterId=1,fraction=.5,particleVolume=.1));s.advance_to(1000000)
   q=s.info()['flowSprays'][0];self.assertGreater(q['impactedVolume'],0);self.assertAlmostEqual(q['emittedVolume'],q['liveVolume']+q['expiredVolume']+q['impactedVolume']+q['exportedVolume'],places=6)
 def testSchema22EmissionHistoryMigratesAsUnresolved(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(1000000);data=bytearray(s.snapshot());payload=data[24:24+5091472];struct.pack_into('<I',payload,4,0x20261022);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261022,len(payload),zlib.crc32(payload));s.restore(data)
   q=s.info()['flowSprays'][0];self.assertAlmostEqual(q['legacyUnresolvedVolume'],.7);self.assertEqual(q['liveVolume'],0);s.advance_to(1100000);q=s.info()['flowSprays'][0];self.assertAlmostEqual(q['emittedVolume'],q['liveVolume']+q['expiredVolume']+q['impactedVolume']+q['exportedVolume']+q['legacyUnresolvedVolume'],places=6)
