import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class FloatBodies(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene(2030);self.scene.command(dict(op='surface',id=1));self.scene.command(dict(op='floor',enabled=False));self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
 def tearDown(self):self.scene.close()
 def body(self,**kw):
  c=dict(op='float-body',id=1,surfaceId=1,position=[0,0,0],radius=1,mass=1000,fluidDensity=1000,gravity=9.81,drag=0);c.update(kw);self.scene.command(c)
 def testHalfSubmergedSphereIsInHydrostaticEquilibrium(self):
  mass=1000*2*math.pi/3;self.body(mass=mass);self.scene.advance_to(1000000);b=self.scene.float_body(1)
  self.assertAlmostEqual(b[1],0,places=10);self.assertAlmostEqual(b[4],0,places=10);self.assertAlmostEqual(b[9],.5,places=10)
 def testFullySubmergedSphereUsesArchimedesForce(self):
  self.body(position=[0,-2,0]);self.scene.advance_to(8333);b=self.scene.float_body(1)
  force=1000*9.81*4*math.pi/3;velocity=(force/1000-9.81)/120
  self.assertAlmostEqual(b[10],force,places=8);self.assertAlmostEqual(b[4],velocity,places=10);self.assertAlmostEqual(b[1],-2+velocity/120,places=10)
 def testWaveFieldReplayAndPureRender(self):
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[.2,.1,0,2,0]]));self.body(drag=2)
  before=self.scene.snapshot();self.scene.render();self.assertEqual(before,self.scene.snapshot())
  self.scene.advance_to(500000);saved=self.scene.snapshot();self.scene.advance_to(1000000);expected=self.scene.snapshot();self.scene.restore(saved);self.scene.advance_to(1000000);self.assertEqual(expected,self.scene.snapshot())
 def testRemovalAndAtomicRejection(self):
  self.body();before=self.scene.snapshot()
  with self.assertRaises(ValueError):self.body(mass=0)
  self.assertEqual(before,self.scene.snapshot());self.scene.command(dict(op='remove-float-body',id=1));self.assertIsNone(self.scene.float_body(1))
 def testSchema09RetainsWavesAndStartsWithoutBodies(self):
  import struct,zlib
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[.2,.1,0,2,0]]));self.body()
  saved=bytearray(self.scene.snapshot());payload=saved[24:24+4779224];struct.pack_into('<I',payload,4,0x20261009)
  saved=saved[:24]+payload;struct.pack_into('<III',saved,12,0x20261009,len(payload),zlib.crc32(payload));self.scene.restore(saved)
  self.assertIsNone(self.scene.float_body(1));self.assertAlmostEqual(self.scene.surface_wave_sample(1,0,0)[0],.2)
 def testNamedBodyMetadataMatchesOwnedQuery(self):
  self.body();self.scene.advance_to(8333);b=self.scene.float_body(1);metadata=self.scene.info()['floatBodies'][0]
  self.assertEqual(metadata['id'],1);self.assertEqual(metadata['surfaceId'],1)
  for a,value in zip(metadata['position'],b[:3]):self.assertAlmostEqual(a,value,places=5)
 def testNumericalOverflowRollsBackFullTimeCommand(self):
  self.body(position=[0,-100,0],radius=64,mass=.001,fluidDensity=100000,gravity=256)
  before=self.scene.snapshot()
  with self.assertRaisesRegex(ValueError,'Floating body numeric range exceeded'):self.scene.advance_to(8333)
  self.assertEqual(before,self.scene.snapshot())
 def testRawAbsentAndShortQueriesLeaveOutputUntouched(self):
  import ctypes as C
  self.body();self.scene.float_body(1);fn=self.scene._lib.nrFloatBody;out=(C.c_double*12)(*([123]*12))
  self.assertEqual(fn(self.scene._context,2,out,12),0);self.assertEqual(list(out),[123]*12)
  self.assertEqual(fn(self.scene._context,1,out,11),-1);self.assertEqual(list(out),[123]*12)
