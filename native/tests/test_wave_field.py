"""Analytic shared-field equations, not renderer-derived reference values."""
import ctypes as C,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class WaveField(unittest.TestCase):
 def setUp(self):self.scene=NativeScene(2030)
 def tearDown(self):self.scene.close()
 def testAnalyticHeightNormalVelocityAndCurvature(self):
  waves=[[2,3,4,5,.2]];x,z,t=.1,.2,.3;phase=3*x+4*z-5*t+.2
  v=self.scene.wave_sample(waves,x,z,t)
  h=2*math.cos(phase);dx=-6*math.sin(phase);dz=-8*math.sin(phase);norm=math.sqrt(1+dx*dx+dz*dz)
  expected=[h,-dx/norm,1/norm,-dz/norm,10*math.sin(phase),-50*math.cos(phase)]
  for a,b in zip(v,expected):self.assertAlmostEqual(a,b,places=11)
 def testSharedSamplingAndDerivativeConsistency(self):
  waves=[[.3,1,.2,2,0],[.2,-.5,1,3,.4]];eps=1e-5
  before=self.scene.snapshot();v=self.scene.wave_sample(waves,.2,.4,.6)
  dx=(self.scene.wave_sample(waves,.2+eps,.4,.6)[0]-self.scene.wave_sample(waves,.2-eps,.4,.6)[0])/(2*eps)
  dt=(self.scene.wave_sample(waves,.2,.4,.6+eps)[0]-self.scene.wave_sample(waves,.2,.4,.6-eps)[0])/(2*eps)
  self.assertAlmostEqual(dx,-v[1]/v[2],places=8);self.assertAlmostEqual(dt,v[4],places=8)
  self.assertEqual(before,self.scene.snapshot());self.assertEqual(v,self.scene.wave_sample(waves,.2,.4,.6))
 def testFlatFieldAndRejectedInput(self):
  self.assertEqual(self.scene.wave_sample([],0,0,0),[0,0,1,0,0,0])
  for waves in [[[1,2]],[[float('nan'),0,0,0,0]],[[1,0,0,0,0]]*33]:
   with self.assertRaises(ValueError):self.scene.wave_sample(waves,0,0,0)
 def testRawFailureDoesNotTouchCallerOutput(self):
  self.scene.wave_sample([],0,0,0)
  fn=self.scene._lib.nrWaveSample;out=(C.c_double*6)(*([123]*6))
  waves=(C.c_double*10)(1,1,1,1,1,float('nan'),1,1,1,1)
  self.assertEqual(fn(waves,2,0,0,0,out,6),-1);self.assertEqual(list(out),[123]*6)
  self.assertEqual(fn(waves,1,0,0,0,out,5),-1);self.assertEqual(list(out),[123]*6)
