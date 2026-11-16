"""Independent reciprocal drag solution, momentum and energy references."""
import ctypes as C
import math,unittest
from test_hull_immersion import NativeScene
class FluidDragExchange(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.fn=self.scene._lib.nrFluidDragExchange
  self.fn.argtypes=[C.c_double,C.c_double,C.c_double,C.c_double,C.POINTER(C.c_double),C.POINTER(C.c_double),C.POINTER(C.c_double),C.c_uint32];self.fn.restype=C.c_int
 def sample(self,m1,m2,k,dt,a,b):
  va=(C.c_double*3)(*a);vb=(C.c_double*3)(*b);out=(C.c_double*10)(*([777]*10));return self.fn(m1,m2,k,dt,va,vb,out,10),list(out)
 def test_exact_unequal_mass_exchange_and_energy(self):
  before=self.scene.snapshot();code,row=self.sample(2,3,4,.5,[5,-2,1],[-1,3,0]);self.assertEqual(code,1)
  fraction=-math.expm1(-4*.5*(1/2+1/3));mu=6/5;relative=[6,-5,1];impulse=[mu*fraction*x for x in relative]
  expected=[5-impulse[0]/2,-2-impulse[1]/2,1-impulse[2]/2,-1+impulse[0]/3,3+impulse[1]/3,impulse[2]/3]+impulse+[.5*mu*sum(x*x for x in relative)*fraction*(2-fraction)]
  for a,b in zip(row,expected):self.assertAlmostEqual(a,b,places=9)
  for i in range(3):self.assertAlmostEqual(2*row[i]+3*row[i+3],2*[5,-2,1][i]+3*[-1,3,0][i])
  before_energy=.5*2*30+.5*3*10;after_energy=.5*2*sum(x*x for x in row[:3])+.5*3*sum(x*x for x in row[3:6]);self.assertAlmostEqual(before_energy-after_energy,row[9])
  self.assertEqual(self.scene.snapshot(),before)
 def test_owned_binding_conserves_momentum_and_rejects_invalid_mass(self):
  before=self.scene.snapshot();row=self.scene.fluid_drag_exchange(2,3,4,.5,[1,0,0],[0,0,0])
  fraction=-math.expm1(-4*.5*(1/2+1/3));self.assertAlmostEqual(row[0],1-.6*fraction);self.assertAlmostEqual(row[3],.4*fraction);self.assertAlmostEqual(2*row[0]+3*row[3],2)
  row[0]=999;self.assertAlmostEqual(self.scene.fluid_drag_exchange(2,3,4,.5,[1,0,0],[0,0,0])[0],1-.6*fraction)
  with self.assertRaises(ValueError):self.scene.fluid_drag_exchange(0,3,4,.5,[1,0,0],[0,0,0])
  self.assertEqual(self.scene.snapshot(),before)
 def test_runtime_contract_declares_owned_exchange_fields(self):
  before=self.scene.snapshot();query=self.scene.info()['contract']['queryContracts']['nrFluidDragExchange']
  self.assertEqual(query['fields'],['bodyVelocity.x','bodyVelocity.y','bodyVelocity.z','waterVelocity.x','waterVelocity.y','waterVelocity.z','waterImpulse.x','waterImpulse.y','waterImpulse.z','dissipatedEnergy'])
  self.assertEqual((query['rowWords'],query['alignmentBytes'],query['capacityUnit']),(10,8,'double'));self.assertTrue(query['pure']);self.assertTrue(query['ownedBindings']);self.assertEqual(self.scene.snapshot(),before)
 def test_partition_small_rate_and_equilibrium(self):
  a=[1,2,3];b=[-2,0,4];_,full=self.sample(2,3,4,1,a,b);_,half=self.sample(2,3,4,.5,a,b);_,second=self.sample(2,3,4,.5,half[:3],half[3:6])
  for x,y in zip(full[:6],second[:6]):self.assertAlmostEqual(x,y,places=10)
  self.assertAlmostEqual(full[9],half[9]+second[9],places=10)
  _,tiny=self.sample(2,3,1e-12,1,[1,0,0],[0,0,0]);self.assertGreater(tiny[6],0);self.assertGreater(tiny[9],0)
  _,same=self.sample(2,3,100,1,a,a);self.assertEqual(same,a+a+[0,0,0,0])
  _,zero=self.sample(2,3,0,1,a,b);self.assertEqual(zero,a+b+[0,0,0,0])
 def test_invalid_inputs_short_output_and_aliasing(self):
  for m1,m2,k,dt in [(0,3,4,1),(2,-1,4,1),(2,3,-1,1),(2,3,4,float('nan'))]:
   code,row=self.sample(m1,m2,k,dt,[1,0,0],[0,0,0]);self.assertEqual(code,-1);self.assertEqual(row,[777]*10)
  data=(C.c_double*10)(1,0,0,0,0,0,777,777,777,777);other=C.cast(C.byref(data,24),C.POINTER(C.c_double));saved=list(data)
  self.assertEqual(self.fn(2,3,4,1,data,other,data,9),-1);self.assertEqual(list(data),saved)
  _,reference=self.sample(2,3,4,1,[1,0,0],[0,0,0]);self.assertEqual(self.fn(2,3,4,1,data,other,data,10),1)
  for x,y in zip(data,reference):self.assertAlmostEqual(x,y)
