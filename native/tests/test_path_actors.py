import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class PathActors(unittest.TestCase):
 def testClockMovesEmitterAndReplaysPurely(self):
  with NativeScene() as s:
   s.command(dict(op='emitter',id=1,count=0,position=[0,0,0]))
   s.command(dict(op='path-travel',id=1,target={'family':'emitter','id':1},points=[[0,0,0],[3,0,0],[3,4,0]],speed=5))
   s.advance_to(1000000);self.assertEqual(s.info()['pathActors'][0]['position'],[3,2,0])
   before=s.snapshot();s.render();self.assertEqual(before,s.snapshot());s.advance_to(2000000);expected=s.snapshot();s.restore(before);s.advance_to(2000000);self.assertEqual(expected,s.snapshot())
 def testRemovalFreezesPosition(self):
  with NativeScene() as s:
   s.command(dict(op='path-travel',id=1,target={'family':'camera','id':0},points=[[0,0,0],[10,0,0]],speed=2))
   s.advance_to(1000000);s.command(dict(op='remove-path-travel',id=1));s.advance_to(2000000);self.assertEqual(s.info()['camera']['position'],[2,0,0])
 def testInvalidAndDuplicateOwnershipAreAtomic(self):
  with NativeScene() as s:
   c=dict(op='path-travel',id=1,target={'family':'camera','id':0},points=[[0,0,0],[4,0,0]],speed=1)
   s.command(c);before=s.snapshot()
   for patch in [dict(id=2),dict(speed=float('inf')),dict(points=[[0,0,0],[0,0,0]]),dict(target={'family':'emitter','id':999}),dict(mode='other')]:
    with self.assertRaises(ValueError):s.command(c|patch)
    self.assertEqual(before,s.snapshot())

 def testWindowAndGraphNodeTravel(self):
  with NativeScene() as s:
   for family in ['window','node']:
    s.command(dict(op=family,id=1));s.command(dict(op='path-travel',id=1 if family=='window' else 2,target={'family':family,'id':1},points=[[0,0,0],[4,0,0]],speed=2))
   s.advance_to(1000000);info=s.info();self.assertEqual(info['windows'][0]['position'],[2,0,0]);self.assertEqual(info['nodes'][0]['position'],[2,0,0])
 def testEmitterGenerationCannotBeRebound(self):
  with NativeScene() as s:
   s.command(dict(op='emitter',id=1,count=0));s.command(dict(op='path-travel',id=1,target={'family':'emitter','id':1},points=[[0,0,0],[10,0,0]],speed=2));s.command(dict(op='clear-instance',id=1));s.command(dict(op='emitter',id=1,count=0,position=[7,0,0]));s.advance_to(1000000)
   self.assertIsNone(s.info()['pathActors'][0]['position'])
 def testPreviousFoamSchemaPromotesAndScheduledTravelWorks(self):
  import struct,zlib
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='surface-foam',surfaceId=1,decay=2))
   s.command(dict(op='schedule',id=1,atUs=8333,command=dict(op='path-travel',id=1,target={'family':'camera','id':0},points=[[0,0,0],[4,0,0]],speed=2)))
   data=bytearray(s.snapshot());payload=data[24:24+4797920];struct.pack_into('<I',payload,4,0x20261011);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261011,len(payload),zlib.crc32(payload));s.restore(data);s.advance_to(1000000)
   self.assertAlmostEqual(s.info()['camera']['position'][0],2*(1-.008333),places=8)

 def testCorruptActorRestoreIsAtomic(self):
  import struct,zlib
  with NativeScene() as s:
   s.command(dict(op='path-travel',id=1,target={'family':'camera','id':0},points=[[0,0,0],[4,0,0]],speed=2));before=s.snapshot();bad=bytearray(before)
   struct.pack_into('<i',bad,24+4797920+12,2);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())
