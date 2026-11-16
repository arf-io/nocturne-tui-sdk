import math,sys,unittest,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class SurfaceWaves(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene(2030);self.scene.command(dict(op='surface',id=1));self.scene.command(dict(op='environment',stars=0))
 def tearDown(self):self.scene.close()
 def testRetainedFieldUsesSimulationClockAndRestores(self):
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[2,0,0,1,0]]))
  self.assertAlmostEqual(self.scene.surface_wave_sample(1,0,0)[0],2)
  self.scene.advance_to(1000000);sample=self.scene.surface_wave_sample(1,0,0)
  self.assertAlmostEqual(sample[0],2*math.cos(self.scene.info()['clock']['timeUs']/1e6),places=10)
  saved=self.scene.snapshot();self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[]));self.scene.restore(saved)
  self.assertEqual(sample,self.scene.surface_wave_sample(1,0,0));before=self.scene.snapshot();self.scene.render();self.assertEqual(before,self.scene.snapshot())
 def testRejectedFieldPreservesWholeState(self):
  before=self.scene.snapshot()
  for cmd in [dict(op='surface-waves',surfaceId=2,waves=[]),dict(op='surface-waves',surfaceId=1,waves=[[300,0,0,0,0]]),dict(op='surface-waves',surfaceId=1,waves=[[1,2]])]:
   with self.assertRaises(Exception):self.scene.command(cmd)
   self.assertEqual(before,self.scene.snapshot())
 def testSchema08MigratesWithNoWaveDisplacement(self):
  saved=bytearray(self.scene.snapshot());payload=saved[24:24+4758616];struct.pack_into('<I',payload,4,0x20261008)
  saved=saved[:24]+payload;struct.pack_into('<III',saved,12,0x20261008,len(payload),zlib.crc32(payload));self.scene.restore(saved)
  self.assertEqual(self.scene.surface_wave_sample(1,0,0),[0,0,1,0,0,0])
 def testRenderingAndCollisionUseTheDisplacedMesh(self):
  self.scene.command(dict(op='floor',enabled=False))
  self.scene.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
  baseline=self.scene.render().bytes
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[2,0,0,0,0]]))
  displaced=self.scene.render().bytes;self.assertNotEqual(baseline,displaced)
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,3,0],velocity=[0,-240,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
  self.scene.advance_to(8333);particle=self.scene.particles()[0]
  self.assertEqual(particle[7],240*65536);self.assertGreater(particle[4]/65536,2)
  self.assertEqual(self.scene.info()['contacts'][0]['surfaceId'],1)
 def testRestitutionUsesVelocityRelativeToWaveSurface(self):
  self.scene.command(dict(op='floor',enabled=False))
  self.scene.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,0,0,1,math.pi/2]]))
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,1,0],velocity=[0,-240,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
  self.scene.advance_to(8333)
  low,high=0,1/120
  for _ in range(60):
   mid=(low+high)/2
   if 1-240*mid>math.sin(mid):low=mid
   else:high=mid
  self.assertAlmostEqual(self.scene.particles()[0][7]/65536,240+2*math.cos((low+high)/2),delta=2/65536)
  saved=self.scene.snapshot();self.scene.advance_to(16666);expected=self.scene.snapshot()
  self.scene.restore(saved);self.scene.advance_to(16666);self.assertEqual(expected,self.scene.snapshot())
 def testRisingWaterSweepsStationaryParticleAtContactTime(self):
  self.scene.command(dict(op='floor',enabled=False));self.scene.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,0,0,1,math.pi/2]]))
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,.004,0],velocity=[0,0,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
  self.scene.advance_to(8333);particle=self.scene.particles()[0]
  y0=round(.004*65536)/65536;impact=math.asin(y0);velocity=2*math.cos(impact)
  self.assertAlmostEqual(particle[7]/65536,velocity,delta=2/65536)
  self.assertAlmostEqual(particle[4]/65536,y0+.001+velocity*(1/120-impact),delta=3/65536)
 def testSolverExhaustionRollsBackTimeAndParticles(self):
  self.scene.command(dict(op='floor',enabled=False))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,0,0,1000000,0],[-1,0,0,1000000,0]]))
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,.01,0],velocity=[0,0,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
  before=self.scene.snapshot()
  with self.assertRaisesRegex(ValueError,'solver budget exhausted'):self.scene.advance_to(8333)
  self.assertEqual(before,self.scene.snapshot())
 def testMidStepPeakCannotBeMissedFromEqualEndpoints(self):
  self.scene.command(dict(op='floor',enabled=False));self.scene.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[-10,0,-10],b=[10,0,-10],c=[0,0,10],surfaceId=1)]))
  omega=240*math.pi
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,0,0,omega,math.pi/2]]))
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,.5,0],velocity=[0,0,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
  self.scene.advance_to(8333)
  self.assertAlmostEqual(self.scene.particles()[0][7]/65536,2*omega*math.sqrt(.75),delta=3/65536)
 def testVerticalTriangleUsesActualContactPhaseForFriction(self):
  self.scene.command(dict(op='floor',enabled=False));self.scene.command(dict(op='surface',id=1,restitution=1,friction=.5,settleSpeed=0))
  self.scene.command(dict(op='mesh',triangles=[dict(a=[0,-10,-10],b=[0,10,-10],c=[0,0,10],surfaceId=1)]))
  self.scene.command(dict(op='surface-waves',surfaceId=1,waves=[[1,0,0,1,math.pi/2]]))
  self.scene.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[1,0,0],velocity=[-240,0,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
  self.scene.advance_to(8333);particle=self.scene.particles()[0]
  self.assertEqual(particle[6],240*65536)
  self.assertAlmostEqual(particle[7]/65536,.5*math.cos(1/240),delta=2/65536)
