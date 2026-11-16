import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class SurfaceFoam(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene(2030);self.scene.command(dict(op='surface',id=1));self.scene.command(dict(op='floor',enabled=False));self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
 def tearDown(self):self.scene.close()
 def configure(self,**patch):
  c=dict(op='surface-foam',surfaceId=1,sourceRate=2,curvatureThreshold=0,decay=1,impactGain=0);c.update(patch);self.scene.command(c)
 def testWaveDrivenSourceDecayAndExplicitBalance(self):
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,1,0,0,0]]));self.configure();self.scene.advance_to(8333);r=self.scene.surface_foam(1)[0]
  self.assertEqual(r[0],0);self.assertAlmostEqual(r[1],1/121,places=12);self.assertAlmostEqual(r[2],1/120,places=12);self.assertAlmostEqual(r[3],1/120-1/121,places=12);self.assertEqual(r[4],0)
  self.scene.advance_to(2000000);r=self.scene.surface_foam(1)[0];self.assertAlmostEqual(r[2],r[1]+r[3]+r[4],places=10)
 def testStoppedSourceRetainsDecayTailAndPureRender(self):
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,1,0,0,0]]));self.configure();self.scene.advance_to(1000000);initial=self.scene.surface_foam(1)[0][1]
  self.scene.command(dict(op='surface-foam',surfaceId=1,enabled=False));before=self.scene.snapshot();self.scene.render();self.assertEqual(before,self.scene.snapshot())
  self.scene.advance_to(2000000);self.assertAlmostEqual(self.scene.surface_foam(1)[0][1],initial/(1+1/120)**120,places=10)
 def testSaturationReplayAndMeshLifetime(self):
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,1,0,0,0]]));self.configure(sourceRate=1000,decay=0);self.scene.advance_to(8333);r=self.scene.surface_foam(1)[0];self.assertEqual(r[1],1);self.assertGreater(r[4],0)
  saved=self.scene.snapshot();self.scene.advance_to(1000000);expected=self.scene.snapshot();self.scene.restore(saved);self.scene.advance_to(1000000);self.assertEqual(expected,self.scene.snapshot())
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]));self.assertEqual(self.scene.surface_foam(1)[0][1:],[0,0,0,0])
 def testSchema10MigratesPendingSurfaceChangesWithoutFoam(self):
  import struct,zlib
  self.scene.command(dict(op='schedule',id=1,atUs=8333,command=dict(op='surface',id=1,friction=.2)))
  data=bytearray(self.scene.snapshot());payload=data[24:24+4788952];struct.pack_into('<I',payload,4,0x20261010)
  data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261010,len(payload),zlib.crc32(payload));self.scene.restore(data)
  self.assertEqual(self.scene.surface_foam(1)[0][1:],[0,0,0,0]);self.scene.advance_to(8333)
  self.assertEqual(self.scene.info()['surfaces'][0]['friction'],.2)
 def testImpactGeneratesFoamAtTheContactTriangle(self):
  self.configure(sourceRate=0,decay=0,impactGain=.001)
  self.scene.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,1,0],velocity=[0,-240,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=1,sizeMax=1,colliders={'surfaces':[1]}))
  self.scene.advance_to(8333);r=self.scene.surface_foam(1)[0];self.assertAlmostEqual(r[1],.24,places=12);self.assertAlmostEqual(r[2],.24,places=12)

 def testInvalidEditAndShortOutputAreAtomic(self):
  import ctypes as C
  self.configure();before=self.scene.snapshot()
  with self.assertRaises(ValueError):self.configure(decay=-1)
  self.assertEqual(before,self.scene.snapshot());self.scene.surface_foam(1)
  fn=self.scene._lib.nrSurfaceFoam;out=(C.c_double*5)(*([123]*5))
  self.assertEqual(fn(self.scene._context,1,None,0),1)
  self.assertEqual(fn(self.scene._context,1,out,0),-1);self.assertEqual(list(out),[123]*5)
