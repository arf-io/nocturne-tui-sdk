import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class SurfaceWater(unittest.TestCase):
 def setup_scene(self,s,evaporation=500000):
  s.command(dict(op='surface',id=1));s.command(dict(op='floor',enabled=False));s.command(dict(op='mesh',triangles=[dict(a=[-2,0,-2],b=[2,0,-2],c=[0,0,2],surfaceId=1),dict(a=[8,0,-2],b=[12,0,-2],c=[10,0,2],surfaceId=1)]));s.command(dict(op='surface-water',surfaceId=1,capacity=1,evaporationUs=evaporation))
  s.command(dict(op='emitter',id=1,effect='weather/rain-threads',count=0,position=[0,1,0],extent=[0,0,0],spread=[0,0,0],velocity=[0,-240,0],gravity=[0,0,0],wind=[0,0,0],drag=0,collision=True,colliders={'surfaces':[1]},lifetimeMinMs=10000,lifetimeMaxMs=10000));s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='spray')]));s.command(dict(op='flow-spray',flowId=1,emitterId=1,fraction=.5,particleVolume=.1))
 def testSpatialImpactEvaporationReplayAndMeshExport(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['receivedVolume'],.1);self.assertAlmostEqual(q['cells'][0]['retainedVolume'],.1);self.assertEqual(q['cells'][1]['retainedVolume'],0)
   s.command(dict(op='flow-rate',id=1,flux=0));saved=s.snapshot();s.advance_to(200000);q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['retainedVolume'],.1*math.exp(-.2),places=5);self.assertAlmostEqual(q['receivedVolume'],q['retainedVolume']+q['evaporatedVolume']+q['exportedVolume'],places=6);expected=s.snapshot();s.restore(saved);s.advance_to(200000);self.assertEqual(expected,s.snapshot());before=s.snapshot();s.render();self.assertEqual(before,s.snapshot())
   s.command(dict(op='mesh',triangles=[]));q=s.info()['surfaceWater'][0];self.assertEqual(q['retainedVolume'],0);self.assertAlmostEqual(q['exportedVolume'],.1*math.exp(-.2),places=5)

 def testConfigurationAndRestoreAreAtomic(self):
  import struct,zlib
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));before=s.snapshot()
   for c in [dict(op='surface-water',surfaceId=1,capacity=0),dict(op='surface-water',surfaceId=1,capacity=1,evaporationUs=500),dict(op='surface-water',surfaceId=2,capacity=1)]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(before,s.snapshot())
   data=bytearray(s.snapshot());payload=data[24:24+5124752];struct.pack_into('<I',payload,4,0x20261023);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261023,len(payload),zlib.crc32(payload));s.restore(data);self.assertNotIn('surfaceWater',s.info())
   s.command(dict(op='surface-water',surfaceId=1,capacity=1));before=s.snapshot();bad=bytearray(before);struct.pack_into('<d',bad,24+5124752+8,-1);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())

 def testAppendRetainsCellsAndSpatialWaterChangesFrame(self):
  import struct,zlib
  with NativeScene() as s,NativeScene() as dry:
   self.setup_scene(s);s.advance_to(100000);data=bytearray(s.snapshot());data[24+5124752:24+5140752]=bytes(16000);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));dry.restore(data);self.assertNotEqual(s.render(),dry.render())
   s.command(dict(op='mesh',append=True,triangles=[dict(a=[18,0,-2],b=[22,0,-2],c=[20,0,2],surfaceId=1)]));q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['cells'][0]['retainedVolume'],.1);self.assertEqual(q['cells'][2]['retainedVolume'],0)

 def testTransferConservesWaterAndRejectsOverdraw(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);s.command(dict(op='flow-rate',id=1,flux=0));s.command(dict(op='surface-water-transfer',fromTriangle=0,toTriangle=1,volume=.04));q=s.info()['surfaceWater'][0]
   self.assertAlmostEqual(q['receivedVolume'],.1);self.assertAlmostEqual(q['importedVolume'],.04);self.assertAlmostEqual(q['transferredVolume'],.04);self.assertAlmostEqual(q['cells'][0]['retainedVolume'],.06);self.assertAlmostEqual(q['cells'][1]['retainedVolume'],.04);self.assertAlmostEqual(q['receivedVolume']+q['importedVolume'],q['retainedVolume']+q['evaporatedVolume']+q['exportedVolume']+q['transferredVolume'],places=6)
   before=s.snapshot()
   for c in [dict(op='surface-water-transfer',fromTriangle=0,toTriangle=1,volume=.2),dict(op='surface-water-transfer',fromTriangle=0,toTriangle=0,volume=.01),dict(op='surface-water-transfer',fromTriangle=0,toTriangle=2,volume=.01)]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(before,s.snapshot())
   s.command(dict(op='mesh',triangles=[]));q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['exportedVolume'],.1);self.assertAlmostEqual(q['receivedVolume']+q['importedVolume'],q['evaporatedVolume']+q['exportedVolume']+q['transferredVolume'],places=6)

 def testSchema24PreservesStoredWaterWithoutTransfers(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);data=bytearray(s.snapshot());payload=data[24:24+5133712];struct.pack_into('<I',payload,4,0x20261024);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261024,len(payload),zlib.crc32(payload));s.restore(data);q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['retainedVolume'],.1);self.assertEqual(q['importedVolume'],0)
   before=s.snapshot();bad=bytearray(before);struct.pack_into('<d',bad,24+5133712,float('nan'));struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())

 def testNativeTransportLinkAnalyticDecayAndPartitionReplay(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);s.command(dict(op='flow-rate',id=1,flux=0));s.command(dict(op='surface-water-link',id=1,fromTriangle=0,toTriangle=1,rate=10));saved=s.snapshot();s.advance_to(200000);q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['cells'][0]['retainedVolume'],.1*math.exp(-1.2),places=5);self.assertAlmostEqual(q['cells'][1]['retainedVolume'],.1*math.exp(-.2)*(1-math.exp(-1)),places=5);expected=s.snapshot();s.restore(saved)
   for at in [123456,155555,188888,200000]:s.advance_to(at)
   self.assertEqual(expected,s.snapshot());before=s.snapshot();s.render();self.assertEqual(before,s.snapshot());s.command(dict(op='remove-surface-water-link',id=1));s.advance_to(300000);self.assertAlmostEqual(s.info()['surfaceWater'][0]['cells'][0]['retainedVolume'],.1*math.exp(-1.4),places=5)

 def testLinkPartialEpochAndMeshLifetime(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);s.command(dict(op='flow-rate',id=1,flux=0));s.advance_to(105000);s.command(dict(op='surface-water-link',id=1,fromTriangle=0,toTriangle=1,rate=10));s.advance_to(108333);q=s.info()['surfaceWater'][0];self.assertAlmostEqual(q['cells'][0]['retainedVolume'],.1*math.exp(-2*.008333-10*(13/120-.105)),places=5)
   s.command(dict(op='mesh',append=True,triangles=[dict(a=[18,0,-2],b=[22,0,-2],c=[20,0,2],surfaceId=1)]));self.assertEqual(len(s.info()['waterLinks']),1);s.command(dict(op='mesh',triangles=[]));self.assertNotIn('waterLinks',s.info())
 def testInvalidLinkAndSchema25Migration(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);data=bytearray(s.snapshot());payload=data[24:24+5138064];struct.pack_into('<I',payload,4,0x20261025);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261025,len(payload),zlib.crc32(payload));s.restore(data);self.assertNotIn('waterLinks',s.info());before=s.snapshot()
   for patch in [dict(rate=0),dict(toTriangle=0),dict(toTriangle=2)]:
    with self.assertRaises(ValueError):s.command(dict(op='surface-water-link',id=1,fromTriangle=0,toTriangle=1,rate=10)|patch)
    self.assertEqual(before,s.snapshot())

 def testFanoutAndCycleUseSimultaneousOldCellVolumes(self):
  with NativeScene() as s:
   self.setup_scene(s);s.advance_to(100000);s.command(dict(op='flow-rate',id=1,flux=0));s.command(dict(op='mesh',append=True,triangles=[dict(a=[18,0,-2],b=[22,0,-2],c=[20,0,2],surfaceId=1)]))
   for id,a,b,rate in [(1,0,1,10),(2,0,2,20),(3,1,0,100)]:s.command(dict(op='surface-water-link',id=id,fromTriangle=a,toTriangle=b,rate=rate))
   s.advance_to(108333);cells=s.info()['surfaceWater'][0]['cells'];available=.1*math.exp(-2*.008333);moved=available*(1-math.exp(-.25));self.assertAlmostEqual(cells[0]['retainedVolume'],available-moved,places=5);self.assertAlmostEqual(cells[1]['retainedVolume'],moved/3,places=5);self.assertAlmostEqual(cells[2]['retainedVolume'],moved*2/3,places=5)

 def testWaterReentrainmentReusesVolumeWithoutANewSource(self):
  with NativeScene() as s:
   self.setup_scene(s,evaporation=0);s.advance_to(100000);s.command(dict(op='flow-rate',id=1,flux=0));s.command(dict(op='surface-water-reemit',triangleIndex=0,emitterId=1,volume=.1))
   water=s.info()['surfaceWater'][0];spray=s.info()['flowSprays'][0];self.assertEqual(water['retainedVolume'],0);self.assertAlmostEqual(water['transferredVolume'],.1);self.assertAlmostEqual(spray['reentrainedVolume'],.1);self.assertAlmostEqual(spray['pendingVolume'],.1);saved=s.snapshot();s.advance_to(108333);water=s.info()['surfaceWater'][0];spray=s.info()['flowSprays'][0];self.assertAlmostEqual(water['retainedVolume'],.1);self.assertAlmostEqual(spray['emittedVolume'],.2);self.assertAlmostEqual(spray['flowReceivedVolume'],.1);self.assertAlmostEqual(spray['pendingVolume'],0);self.assertAlmostEqual(water['receivedVolume'],.2);self.assertAlmostEqual(water['receivedVolume']-water['transferredVolume'],spray['flowReceivedVolume']);expected=s.snapshot();s.restore(saved);s.advance_to(108333);self.assertEqual(expected,s.snapshot())

 def testPartialReentrantQuantumAndInvalidTargetRemainAccounted(self):
  with NativeScene() as s:
   self.setup_scene(s,evaporation=0);s.advance_to(100000);s.command(dict(op='flow-rate',id=1,flux=0));before=s.snapshot()
   for c in [dict(op='surface-water-reemit',triangleIndex=0,emitterId=999,volume=.01),dict(op='surface-water-reemit',triangleIndex=0,emitterId=1,volume=.2)]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(before,s.snapshot())
   s.command(dict(op='surface-water-reemit',triangleIndex=0,emitterId=1,volume=.04));s.advance_to(200000);q=s.info()['flowSprays'][0];self.assertAlmostEqual(q['pendingVolume'],.04);self.assertAlmostEqual(q['emittedVolume'],.1);self.assertAlmostEqual(s.info()['surfaceWater'][0]['retainedVolume'],.06)

 def testSchema26AndCorruptReentrainedVolumeRestore(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s,evaporation=0);s.advance_to(100000);data=bytearray(s.snapshot());payload=data[24:24+5140624];struct.pack_into('<I',payload,4,0x20261026);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261026,len(payload),zlib.crc32(payload));s.restore(data);self.assertEqual(s.info()['flowSprays'][0]['reentrainedVolume'],0)
   before=s.snapshot();bad=bytearray(before);struct.pack_into('<d',bad,24+5140624,-1);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())

 def testAuthoredWaterInputPreservesEvaporationAndReceiverAccounting(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));triangle=dict(a=[-2,0,-2],b=[2,0,-2],c=[0,0,2],surfaceId=1)
   s.command(dict(op='mesh',triangles=[triangle,triangle]));s.command(dict(op='surface-water',surfaceId=1,capacity=1,evaporationUs=1000000))
   s.command(dict(op='surface-water-add',triangleIndex=0,volume=.5));s.advance_to(500000);s.command(dict(op='surface-water-add',triangleIndex=0,volume=.25));saved=s.snapshot();s.advance_to(1000000)
   water=s.info()['surfaceWater'][0];expected=.5*math.exp(-1)+.25*math.exp(-.5)
   self.assertAlmostEqual(water['receivedVolume'],.75);self.assertAlmostEqual(water['retainedVolume'],expected,places=6);self.assertAlmostEqual(water['receivedVolume'],water['retainedVolume']+water['evaporatedVolume']+water['exportedVolume'],places=6)
   self.assertEqual(water['cells'][1]['retainedVolume'],0);finish=s.snapshot();s.restore(saved);s.advance_to(1000000);self.assertEqual(s.snapshot(),finish)
   for command in [dict(op='surface-water-add',triangleIndex=0,volume=0),dict(op='surface-water-add',triangleIndex=2,volume=.1),dict(op='surface-water-add',triangleIndex=0,volume=.1,wetness=1)]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(s.snapshot(),finish)
   s.command(dict(op='mesh',triangles=[]));water=s.info()['surfaceWater'][0];self.assertAlmostEqual(water['exportedVolume'],expected,places=6)

 def testPendingAuthoredWaterInputRetainsCancellationAfterMeshRetirement(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='mesh',triangles=[dict(a=[-2,0,-2],b=[2,0,-2],c=[0,0,2],surfaceId=1)]));s.command(dict(op='surface-water',surfaceId=1,capacity=1))
   s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='surface-water-add',triangleIndex=0,volume=.1)));s.command(dict(op='mesh',triangles=[]));blocked=s.snapshot();s.restore(blocked)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);s.restore(blocked);s.command(dict(op='cancel-schedule',id=1));s.advance_to(500000)

 def testWaterResponseSettingsPreserveVolumeAndPriorEvaporation(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));triangle=dict(a=[-2,0,-2],b=[2,0,-2],c=[0,0,2],surfaceId=1)
   s.command(dict(op='mesh',triangles=[triangle,triangle]));s.command(dict(op='surface-water',surfaceId=1,capacity=1,evaporationUs=1000000))
   s.command(dict(op='surface-water-add',triangleIndex=0,volume=.5));s.command(dict(op='surface-water-add',triangleIndex=1,volume=.25));s.advance_to(500000)
   before=s.info()['surfaceWater'][0];s.command(dict(op='surface-water-settings',surfaceId=1,capacity=2,evaporationUs=2000000));after=s.info()['surfaceWater'][0]
   for field in ['receivedVolume','retainedVolume','evaporatedVolume','exportedVolume','importedVolume','transferredVolume']:self.assertAlmostEqual(after[field],before[field],places=6)
   self.assertAlmostEqual(after['cells'][0]['wetness'],before['cells'][0]['wetness']/2,delta=7.6e-7);saved=s.snapshot();s.advance_to(1000000)
   water=s.info()['surfaceWater'][0];self.assertAlmostEqual(water['retainedVolume'],.75*math.exp(-.75),places=6);finish=s.snapshot();s.restore(saved);s.advance_to(1000000);self.assertEqual(s.snapshot(),finish)
   for command in [dict(op='surface-water-settings',surfaceId=1),dict(op='surface-water-settings',surfaceId=1,capacity=0),dict(op='surface-water-settings',surfaceId=1,evaporationUs=500),dict(op='surface-water-settings',surfaceId=1,evaporationUs=1000.5),dict(op='surface-water-settings',surfaceId=2,capacity=2)]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(s.snapshot(),finish)
   s.command(dict(op='surface-water-settings',surfaceId=1,evaporationUs=0));retained=water['retainedVolume'];s.advance_to(2000000);self.assertAlmostEqual(s.info()['surfaceWater'][0]['retainedVolume'],retained,places=6)

 def testRetainedWaterResponseBindingsAndPartitionReplay(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='mesh',triangles=[dict(a=[-2,0,-2],b=[2,0,-2],c=[0,0,2],surfaceId=1)]));s.command(dict(op='surface-water',surfaceId=1,capacity=1,evaporationUs=1000000));s.command(dict(op='surface-water-add',triangleIndex=0,volume=.5))
   for field,value in [('capacity',1),('evaporationUs',1000000)]:s.command(dict(op='define',path='/'+field,value=value,binding=dict(family='surface',id=1,field='water.'+field)))
   s.advance_to(500000);s.command(dict(op='set',path='/capacity',value=2));s.command(dict(op='set',path='/evaporationUs',value=2000000));start=s.snapshot();s.advance_to(1000000);finish=s.snapshot()
   self.assertAlmostEqual(s.info()['surfaceWater'][0]['retainedVolume'],.5*math.exp(-.75),places=6);s.restore(start)
   for time in [600123,700234,800345,900456,1000000]:s.advance_to(time)
   self.assertEqual(s.snapshot(),finish)
   for path,value in [('/capacity',0),('/evaporationUs',500),('/evaporationUs',1000.5)]:
    with self.assertRaises(ValueError):s.command(dict(op='set',path=path,value=value))
    self.assertEqual(s.snapshot(),finish)

 def testSchema34CannotCarryWaterResponseBindings(self):
  import struct,zlib
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='surface-water',surfaceId=1,capacity=1));s.command(dict(op='define',path='/capacity',value=1,binding=dict(family='surface',id=1,field='water.capacity')));before=s.snapshot()
   old=bytearray(before[:24+12508512]);struct.pack_into('<I',old,28,0x20261034);struct.pack_into('<III',old,12,0x20261034,12508512,zlib.crc32(old[24:]))
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),before)

 def testOwnedWaterSampleSeparatesExternalInputAndInternalImports(self):
  import ctypes as C
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));triangle=dict(a=[-2,0,-2],b=[2,0,-2],c=[0,0,2],surfaceId=1);s.command(dict(op='mesh',triangles=[triangle,triangle]));self.assertIsNone(s.water_sample(0));s.command(dict(op='surface-water',surfaceId=1,capacity=1));self.assertEqual(s.water_sample(0),[1,0,0,0,0,0,0,1])
   s.command(dict(op='surface-water-add',triangleIndex=0,volume=.5));s.command(dict(op='surface-water-transfer',fromTriangle=0,toTriangle=1,volume=.2));before=s.snapshot();rows=[s.water_sample(i) for i in range(2)]
   for actual,expected in zip(rows,[[1,.5,.3,.3,0,.2,0,1],[1,0,.2,.2,.2,0,0,1]]):
    for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=8)
    self.assertAlmostEqual(actual[1]+actual[4],actual[2]+actual[5]+actual[6],places=8)
   rows[0][2]=999;self.assertAlmostEqual(s.water_sample(0)[2],.3);self.assertEqual(s.snapshot(),before)
   fn=s._lib.nrWaterSample;out=(C.c_double*8)(*([777]*8))
   for index,capacity in [(2,8),(0,7)]:
    self.assertEqual(fn(s._context,index,out,capacity),-1);self.assertEqual(list(out),[777]*8)
   self.assertEqual(fn(s._context,0,C.cast(s._context,C.POINTER(C.c_double)),8),-1);self.assertEqual(s.snapshot(),before)
