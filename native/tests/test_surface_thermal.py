import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class SurfaceThermal(unittest.TestCase):
 def setup_scene(self,s):s.command(dict(op='mesh',triangles=[dict(a=[-2,-2,0],b=[2,-2,0],c=[0,2,0])]))
 def testIndependentHeatingEnergyAndPureReplay(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=293,capacity=2,power=4));s.advance_to(500000);q=s.info()['surfaceThermal']['cells'][0];self.assertAlmostEqual(q['temperature'],294);self.assertAlmostEqual(q['energy'],588);self.assertAlmostEqual(q['energy'],q['initialEnergy']+q['appliedEnergy']+q['environmentEnergy']);saved=s.snapshot();s.render();self.assertEqual(saved,s.snapshot());s.command(dict(op='surface-thermal-power',triangleIndex=0,power=0));s.advance_to(1000000);expected=s.snapshot();s.restore(saved);s.command(dict(op='surface-thermal-power',triangleIndex=0,power=0));s.advance_to(1000000);self.assertEqual(expected,s.snapshot())
 def testCoolingAnalyticReferenceAndMeshExport(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,ambientTemperature=300,conductance=4,power=0));s.advance_to(500000);q=s.info()['surfaceThermal']['cells'][0];expected=300+100*math.exp(-1);self.assertAlmostEqual(q['temperature'],expected,places=5);self.assertAlmostEqual(q['energy'],q['initialEnergy']+q['appliedEnergy']+q['environmentEnergy'],places=5);s.command(dict(op='mesh',triangles=[]));self.assertAlmostEqual(s.info()['surfaceThermal']['exportedEnergy'],2*expected,places=5)

 def testTinyConductanceHasStableHeatingLimit(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=293,capacity=2,power=4,conductance=1e-20));s.advance_to(500000);self.assertAlmostEqual(s.info()['surfaceThermal']['cells'][0]['temperature'],294)

 def testThermalAppearanceAndInvalidCoolingAreAtomic(self):
  import struct,zlib
  with NativeScene() as s,NativeScene() as plain:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,ambientTemperature=300));data=bytearray(s.snapshot());data[24+5140752:24+5161264]=bytes(20512);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));plain.restore(data);self.assertNotEqual(s.render(),plain.render())
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=1,capacity=1,power=-100));before=s.snapshot()
   with self.assertRaises(ValueError):s.advance_to(100000)
   self.assertEqual(before,s.snapshot())
 def testSchema27MigrationAndCorruptCapacityRestore(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);data=bytearray(s.snapshot());payload=data[24:24+5140752];struct.pack_into('<I',payload,4,0x20261027);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261027,len(payload),zlib.crc32(payload));s.restore(data);self.assertNotIn('surfaceThermal',s.info());s.command(dict(op='surface-thermal',triangleIndex=0,temperature=300,capacity=1));before=s.snapshot();bad=bytearray(before);struct.pack_into('<d',bad,24+5140752+16,0);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())
 def testIntercellHeatTransferConservesEnergy(self):
  with NativeScene() as s:
   s.command(dict(op='mesh',triangles=[dict(a=[-2,-2,0],b=[2,-2,0],c=[0,2,0]),dict(a=[8,-2,0],b=[12,-2,0],c=[10,2,0])]))
   s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2));s.command(dict(op='surface-thermal',triangleIndex=1,temperature=300,capacity=4));s.command(dict(op='surface-thermal-transfer',fromTriangle=0,toTriangle=1,energy=100));cells=s.info()['surfaceThermal']['cells'];self.assertEqual(cells[0]['temperature'],350);self.assertEqual(cells[1]['temperature'],325);self.assertEqual(sum(q['energy'] for q in cells),2000)
   for q in cells:self.assertAlmostEqual(q['energy'],q['initialEnergy']+q['appliedEnergy']+q['environmentEnergy']+q['importedEnergy']-q['transferredEnergy'])
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(dict(op='surface-thermal-transfer',fromTriangle=0,toTriangle=1,energy=1000))
   self.assertEqual(before,s.snapshot());s.command(dict(op='mesh',triangles=[]));self.assertEqual(s.info()['surfaceThermal']['exportedEnergy'],2000)

 def testTransferFollowedByCoolingRetainsSeparateEnergyTerms(self):
  with NativeScene() as s:
   s.command(dict(op='mesh',triangles=[dict(a=[-2,-2,0],b=[2,-2,0],c=[0,2,0]),dict(a=[8,-2,0],b=[12,-2,0],c=[10,2,0])]))
   s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,power=4));s.command(dict(op='surface-thermal',triangleIndex=1,temperature=300,capacity=4,ambientTemperature=300,conductance=4));s.command(dict(op='surface-thermal-transfer',fromTriangle=0,toTriangle=1,energy=100));s.advance_to(500000);cells=s.info()['surfaceThermal']['cells'];self.assertEqual(cells[0]['temperature'],351);self.assertAlmostEqual(cells[1]['temperature'],300+25*math.exp(-.5),places=5)
   for q in cells:self.assertAlmostEqual(q['energy'],q['initialEnergy']+q['appliedEnergy']+q['environmentEnergy']+q['importedEnergy']-q['transferredEnergy'],places=5)

 def testSchema28AndCorruptTransferHistoryRestore(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=300,capacity=1));data=bytearray(s.snapshot());payload=data[24:24+5161264];struct.pack_into('<I',payload,4,0x20261028);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261028,len(payload),zlib.crc32(payload));s.restore(data);self.assertEqual(s.info()['surfaceThermal']['cells'][0]['importedEnergy'],0);before=s.snapshot();bad=bytearray(before);struct.pack_into('<d',bad,24+5161264,float('nan'));struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())
 def testNativeConductionMatchesIndependentImplicitPair(self):
  with NativeScene() as s:
   s.command(dict(op='mesh',triangles=[dict(a=[-2,-2,0],b=[2,-2,0],c=[0,2,0]),dict(a=[8,-2,0],b=[12,-2,0],c=[10,2,0])]))
   s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2));s.command(dict(op='surface-thermal',triangleIndex=1,temperature=300,capacity=4));s.command(dict(op='surface-thermal-link',id=1,fromTriangle=0,toTriangle=1,conductance=3));saved=s.snapshot();s.advance_to(500000);cells=s.info()['surfaceThermal']['cells'];difference=100/(1+2.25/120)**60;mean=2000/6;self.assertAlmostEqual(cells[0]['temperature'],mean+2*difference/3,places=5);self.assertAlmostEqual(cells[1]['temperature'],mean-difference/3,places=5);self.assertAlmostEqual(sum(q['energy'] for q in cells),2000,places=5);expected=s.snapshot();s.restore(saved)
   for at in [123456,250000,333333,500000]:s.advance_to(at)
   self.assertEqual(expected,s.snapshot())

 def testStiffConductionPreservesEnergyAndMeshLifetime(self):
  with NativeScene() as s:
   t=dict(a=[-2,-2,0],b=[2,-2,0],c=[0,2,0]);s.command(dict(op='mesh',triangles=[t,t]));s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=.000001));s.command(dict(op='surface-thermal',triangleIndex=1,temperature=300,capacity=.000001));s.command(dict(op='surface-thermal-link',id=1,fromTriangle=0,toTriangle=1,conductance=1000000));s.advance_to(8333);cells=s.info()['surfaceThermal']['cells'];self.assertAlmostEqual(cells[0]['temperature'],350,places=5);self.assertAlmostEqual(cells[1]['temperature'],350,places=5);self.assertAlmostEqual(sum(q['energy'] for q in cells),.0007,places=7);s.command(dict(op='mesh',append=True,triangles=[t]));self.assertEqual(len(s.info()['thermalLinks']),1);s.command(dict(op='mesh',triangles=[]));self.assertNotIn('thermalLinks',s.info())

 def testOwnedThermalSampleIndependentEnergyAndBufferRejection(self):
  import ctypes as C
  with NativeScene() as s:
   self.setup_scene(s);self.assertIsNone(s.thermal_sample(0))
   s.command(dict(op='surface-thermal',triangleIndex=0,temperature=293,capacity=2,power=4));s.advance_to(500000);saved=s.snapshot();row=s.thermal_sample(0)
   expected=[294,588,586,2,0,0,0,2,4,293]
   for a,b in zip(row,expected):self.assertAlmostEqual(a,b,places=6)
   self.assertAlmostEqual(row[1],row[2]+row[3]+row[4]+row[5]-row[6]);row[0]=999;self.assertAlmostEqual(s.thermal_sample(0)[0],294);self.assertEqual(s.snapshot(),saved)
   fn=s._lib.nrThermalSample;out=(C.c_double*10)(*([777]*10))
   for index,capacity in [(1,10),(0,9)]:
    self.assertEqual(fn(s._context,index,out,capacity),-1);self.assertEqual(list(out),[777]*10)
   self.assertEqual(fn(s._context,0,C.cast(s._context,C.POINTER(C.c_double)),10),-1);self.assertEqual(s.snapshot(),saved)
   with self.assertRaises(ValueError):s.thermal_sample(True)
   s.command(dict(op='mesh',triangles=[]))
   with self.assertRaises(ValueError):s.thermal_sample(0)

 def testThermalSettingsPreserveLedgerAndPiecewiseAnalyticResponse(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,power=4));s.advance_to(500000)
   before=s.thermal_sample(0);s.command(dict(op='surface-thermal-settings',triangleIndex=0,ambientTemperature=300,conductance=4,power=0));after=s.thermal_sample(0)
   self.assertEqual(before[:8],after[:8]);saved=s.snapshot();s.advance_to(1000000);row=s.thermal_sample(0)
   self.assertAlmostEqual(row[0],300+101*math.exp(-1),places=5);self.assertAlmostEqual(row[1],row[2]+row[3]+row[4]+row[5]-row[6],places=5)
   finish=s.snapshot();s.restore(saved)
   for at in [600000,700000,800000,900000,1000000]:s.advance_to(at)
   self.assertEqual(finish,s.snapshot())
   for command in [dict(op='surface-thermal-settings',triangleIndex=0),dict(op='surface-thermal-settings',triangleIndex=0,conductance=-1),dict(op='surface-thermal-settings',triangleIndex=0,power=0,temperature=500),dict(op='surface-thermal-settings',triangleIndex=1,power=0)]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(finish,s.snapshot())

 def testQueuedThermalSettingsRecoverAfterMeshRetirement(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=293,capacity=2))
   s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='surface-thermal-settings',triangleIndex=0,power=4)))
   s.command(dict(op='mesh',triangles=[]));blocked=s.snapshot();s.restore(blocked)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);s.restore(blocked);s.command(dict(op='cancel-schedule',id=1));s.advance_to(500000)

 def testRetainedThermalBindingsMatchDirectSettingsAndDormantRecovery(self):
  with NativeScene() as s,NativeScene() as oracle:
   for scene in [s,oracle]:
    self.setup_scene(scene);scene.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,ambientTemperature=300,conductance=2,power=4))
   for field,value in [('power',4),('ambientTemperature',300),('conductance',2)]:
    s.command(dict(op='define',path='/'+field,value=value,binding=dict(family='triangle',id=0,field='thermal.'+field)))
   for scene in [s,oracle]:scene.advance_to(500000)
   for field,value in [('power',0),('ambientTemperature',250),('conductance',4)]:
    s.command(dict(op='set',path='/'+field,value=value));oracle.command(dict(op='surface-thermal-settings',triangleIndex=0,**{field:value}))
   for scene in [s,oracle]:scene.advance_to(1000000)
   for a,b in zip(s.thermal_sample(0),oracle.thermal_sample(0)):self.assertAlmostEqual(a,b,places=6)
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(dict(op='set',path='/conductance',value=-1))
   self.assertEqual(s.snapshot(),before)
   s.command(dict(op='schedule',id=1,atUs=1500000,command=dict(op='set',path='/power',value=8)));s.command(dict(op='mesh',triangles=[]));blocked=s.snapshot();s.restore(blocked)
   with self.assertRaises(ValueError):s.advance_to(1500000)
   self.assertEqual(s.snapshot(),blocked);s.restore(blocked);s.command(dict(op='cancel-schedule',id=1));s.command(dict(op='bind',path='/power',binding=None));s.command(dict(op='set',path='/power',value=8));s.advance_to(1500000)

 def testSchema34CannotCarryThermalBindingFields(self):
  import struct,zlib
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=293,capacity=2))
   s.command(dict(op='define',path='/power',value=4,binding=dict(family='triangle',id=0,field='thermal.power')));before=s.snapshot()
   old=bytearray(before[:24+12508512]);struct.pack_into('<I',old,28,0x20261034);struct.pack_into('<III',old,12,0x20261034,12508512,zlib.crc32(old[24:]))
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),before)

 def testPowerEditWithConductionMatchesIndependentTwoCellNetwork(self):
  with NativeScene() as s:
   triangle=dict(a=[-2,-2,0],b=[2,-2,0],c=[0,2,0]);s.command(dict(op='mesh',triangles=[triangle,triangle]))
   s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,power=4));s.command(dict(op='surface-thermal',triangleIndex=1,temperature=300,capacity=4))
   s.command(dict(op='surface-thermal-link',id=1,fromTriangle=0,toTriangle=1,conductance=3));start=s.snapshot()
   expected=[400.0,300.0];previous=0
   for step in range(1,121):
    now=step*1000000//120;elapsed=(now-previous)/1e6;previous=now
    free_a=expected[0]+(4 if step<=60 else 0)*elapsed/2;free_b=expected[1];k=3/120
    denominator=8+6*k
    expected=[(2*free_a*(4+k)+4*k*free_b)/denominator,(4*free_b*(2+k)+2*k*free_a)/denominator]
    if step==60:
     s.advance_to(500000);before=[s.thermal_sample(i) for i in range(2)];s.command(dict(op='surface-thermal-settings',triangleIndex=0,power=0))
     self.assertEqual(before[0][:8],s.thermal_sample(0)[:8]);self.assertEqual(before[1],s.thermal_sample(1))
   s.advance_to(1000000);rows=[s.thermal_sample(i) for i in range(2)]
   for row,temperature in zip(rows,expected):
    self.assertAlmostEqual(row[0],temperature,places=5);self.assertAlmostEqual(row[1],row[2]+row[3]+row[4]+row[5]-row[6],places=5)
   self.assertAlmostEqual(sum(r[1] for r in rows),2002,places=5);self.assertAlmostEqual(sum(r[5]-r[6] for r in rows),0,places=5)
   final=s.snapshot();s.restore(start)
   for time in [123456,250000,500000]:s.advance_to(time)
   s.command(dict(op='surface-thermal-settings',triangleIndex=0,power=0))
   for time in [666666,750000,1000000]:s.advance_to(time)
   self.assertEqual(s.snapshot(),final)

 def testUnchangedThermalBindingsDoNotRebaseEpochAcrossHostPartitions(self):
  with NativeScene() as s:
   self.setup_scene(s);s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,ambientTemperature=300,conductance=2,power=4))
   for field,value in [('power',4),('ambientTemperature',300),('conductance',2)]:s.command(dict(op='define',path='/'+field,value=value,binding=dict(family='triangle',id=0,field='thermal.'+field)))
   start=s.snapshot();s.advance_to(1000000);finish=s.snapshot();s.restore(start)
   for time in [123456,250001,500123,750456,1000000]:s.advance_to(time)
   self.assertEqual(s.snapshot(),finish)
