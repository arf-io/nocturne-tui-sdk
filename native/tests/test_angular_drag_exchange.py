"""Independent diagonal angular momentum/energy references; deferred gate."""
import ctypes as C
import math,unittest
from test_hull_immersion import NativeScene
class AngularExchange(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.fn=self.scene._lib.nrAngularDragExchange
  self.fn.argtypes=[C.POINTER(C.c_double)]*3+[C.c_double]+[C.POINTER(C.c_double)]*3+[C.c_uint32];self.fn.restype=C.c_int
 def sample(self,i,j,k,t,a,b):
  vectors=[(C.c_double*3)(*row) for row in (i,j,k,a,b)];out=(C.c_double*10)(*([777]*10))
  code=self.fn(*vectors[:3],t,*vectors[3:],out,10);return code,list(out)
 def test_unequal_axis_inertias_momentum_energy_and_partition(self):
  before=self.scene.snapshot();i=[2,4,8];j=[3,5,7];k=[4,0,2];a=[5,-2,1];b=[-1,3,0]
  code,row=self.sample(i,j,k,.5,a,b);self.assertEqual(code,1);energy=0
  for axis in range(3):
   reduced=i[axis]*j[axis]/(i[axis]+j[axis]);fraction=-math.expm1(-k[axis]*.5*(1/i[axis]+1/j[axis]));impulse=reduced*fraction*(a[axis]-b[axis])
   self.assertAlmostEqual(row[axis],a[axis]-impulse/i[axis]);self.assertAlmostEqual(row[axis+3],b[axis]+impulse/j[axis]);self.assertAlmostEqual(row[axis+6],impulse)
   self.assertAlmostEqual(i[axis]*row[axis]+j[axis]*row[axis+3],i[axis]*a[axis]+j[axis]*b[axis])
   energy+=.5*i[axis]*(a[axis]**2-row[axis]**2)+.5*j[axis]*(b[axis]**2-row[axis+3]**2)
  self.assertAlmostEqual(row[9],energy)
  _,second=self.sample(i,j,k,.5,row[:3],row[3:6]);_,full=self.sample(i,j,k,1,a,b)
  for x,y in zip(second[:6],full[:6]):self.assertAlmostEqual(x,y)
  self.assertAlmostEqual(row[9]+second[9],full[9]);self.assertEqual(self.scene.snapshot(),before)
 def test_atomic_invalid_later_axis_and_alias(self):
  code,row=self.sample([2,3,0],[4,5,6],[1,1,1],1,[1,2,3],[0,0,0]);self.assertEqual(code,-1);self.assertEqual(row,[777]*10)
  inertia=(C.c_double*3)(2,3,4);water=(C.c_double*3)(5,6,7);k=(C.c_double*3)(1,2,3);a=(C.c_double*10)(1,2,3);b=(C.c_double*3)(0,0,0)
  _,expected=self.sample(list(inertia),list(water),list(k),1,[1,2,3],[0,0,0])
  self.assertEqual(self.fn(inertia,water,k,1,a,b,a,10),1);self.assertEqual(list(a),expected)
 def test_owned_binding_and_zero_conductance_axis(self):
  before=self.scene.snapshot();row=self.scene.angular_drag_exchange([2,4,8],[3,5,7],[4,0,2],.5,[5,-2,1],[-1,3,0])
  contract=self.scene.info()['contract']['queryContracts']['nrAngularDragExchange'];self.assertEqual(contract['frame'],'explicit-shared-principal');self.assertEqual(contract['rowWords'],10);self.assertTrue(contract['ownedBindings']);self.assertEqual(contract['fields'][6],'waterAngularImpulse.x')
  fraction=-math.expm1(-4*.5*(1/2+1/3));self.assertAlmostEqual(row[0],5-3.6*fraction);self.assertEqual(row[1],-2);self.assertEqual(row[4],3)
  row[0]=999;fresh=self.scene.angular_drag_exchange([2,4,8],[3,5,7],[4,0,2],.5,[5,-2,1],[-1,3,0]);self.assertAlmostEqual(fresh[0],5-3.6*fraction)
  with self.assertRaises(ValueError):self.scene.angular_drag_exchange([2,4,0],[3,5,7],[4,0,2],.5,[5,-2,1],[-1,3,0])
  self.assertEqual(self.scene.snapshot(),before)
 def test_short_and_misaligned_outputs_are_atomic(self):
  i=(C.c_double*3)(2,4,8);j=(C.c_double*3)(3,5,7);k=(C.c_double*3)(4,0,2);a=(C.c_double*3)(5,-2,1);b=(C.c_double*3)(-1,3,0);out=(C.c_double*10)(*([777]*10))
  self.assertEqual(self.fn(i,j,k,.5,a,b,out,9),-1);self.assertEqual(list(out),[777]*10)
  raw=(C.c_ubyte*88)(*([123]*88));misaligned=C.cast(C.byref(raw,1),C.POINTER(C.c_double))
  self.assertEqual(self.fn(i,j,k,.5,a,b,misaligned,10),-1);self.assertEqual(list(raw),[123]*88)
  self.assertEqual(self.fn(i,j,k,float('nan'),a,b,out,10),-1);self.assertEqual(list(out),[777]*10)
 def test_aliasing_inertia_is_consumed_before_any_output_write(self):
  i=(C.c_double*10)(2,4,8);j=(C.c_double*3)(3,5,7);k=(C.c_double*3)(4,0,2);a=(C.c_double*3)(5,-2,1);b=(C.c_double*3)(-1,3,0)
  _,expected=self.sample([2,4,8],list(j),list(k),.5,list(a),list(b))
  self.assertEqual(self.fn(i,j,k,.5,a,b,i,10),1);self.assertEqual(list(i),expected)
