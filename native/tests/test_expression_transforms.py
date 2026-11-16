"""Shared direct/retained transforms, explicit dimensional conversions and rollback."""
from pathlib import Path
import sys, unittest
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

CASES=[({'floor':-1.2},-2),({'ceil':-1.2},-1),({'round':-1.5},-1),
 ({'round':1.5},2),({'lerp':{'from':2,'to':10,'amount':.25}},4),
 ({'lerp':{'from':2,'to':10,'amount':2}},18),
 ({'remap':{'value':15,'inMin':10,'inMax':20,'outMin':0,'outMax':1}},.5),
 ({'remap':{'value':15,'inMin':20,'inMax':10,'outMin':0,'outMax':1}},.5),
 ({'convert':{'value':2,'from':'seconds','to':'milliseconds'}},2000),
 ({'convert':{'value':120,'from':'minutes','to':'hours'}},2),
 ({'convert':{'value':250,'from':'centimeters','to':'meters'}},2.5),
 ({'convert':{'value':180,'from':'degrees','to':'radians'}},3.141592653589793),
 ({'convert':{'value':32,'from':'fahrenheit','to':'celsius'}},0),
 ({'convert':{'value':100,'from':'celsius','to':'fahrenheit'}},212),
 ({'convert':{'value':273.15,'from':'kelvin','to':'celsius'}},0)]

class ExpressionTransforms(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene(42);self.addCleanup(self.s.close)
  for p,v in [('/go',0),('/out',0),('/input',15)]:self.cmd('define',path=p,value=v)
 def cmd(self,op,**kw):self.s.command({'op':op,**kw})
 def test_direct_and_retained_results_share_contract(self):
  for expression,expected in CASES:
   with self.subTest(expression=expression):
    self.cmd('set',path='/out',expression=expression)
    self.assertAlmostEqual(self.s.info()['values']['/out'],expected,places=10)
    self.cmd('set',path='/go',value=0)
    self.cmd('trigger',id=1,source='/go',threshold=0,target='/out',expression=expression)
    self.cmd('set',path='/go',value=1)
    self.assertAlmostEqual(self.s.info()['values']['/out'],expected,places=10)
 def test_dimension_and_shape_errors_reject_registration_and_direct_atomically(self):
  bad=[{'convert':{'value':1,'from':'meters','to':'seconds'}},
   {'convert':{'value':1,'from':'pixels','to':'meters'}},
   {'convert':{'value':1,'from':'seconds','to':'seconds','extra':1}},
   {'lerp':{'from':0,'to':1}}, {'remap':{'value':1,'inMin':0,'inMax':1,'outMin':0}},
   {'floor':1,'ceil':1}]
  for expr in bad:
   for command in [dict(op='set',path='/out',expression=expr),
    dict(op='trigger',id=1,source='/go',target='/out',expression=expr)]:
    saved=self.s.snapshot()
    with self.subTest(command=command),self.assertRaises(ValueError):self.s.command(command)
    self.assertEqual(saved,self.s.snapshot())
 def test_zero_input_span_is_runtime_fault_and_rolls_back_trigger(self):
  expr={'remap':{'value':1,'inMin':0,'inMax':0,'outMin':0,'outMax':1}}
  saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('set',path='/out',expression=expr)
  self.assertEqual(saved,self.s.snapshot())
  self.cmd('trigger',id=1,source='/go',target='/out',expression=expr);saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('set',path='/go',value=1)
  self.assertEqual(saved,self.s.snapshot())
 def test_nested_transform_source_is_owned_and_replay_is_pure(self):
  expr={'remap':{'value':{'path':'/input'},'inMin':10,'inMax':20,'outMin':0,'outMax':1}}
  self.cmd('trigger',id=1,source='/go',target='/out',expression=expr,debounceMs=500)
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/input')
  self.cmd('set',path='/go',value=1);self.cmd('set',path='/input',value=18)
  start=self.s.snapshot();self.s.advance_to(500000)
  self.assertAlmostEqual(self.s.info()['values']['/out'],.8)
  end=self.s.snapshot();self.s.render();self.assertEqual(end,self.s.snapshot())
  self.s.restore(start);self.s.advance_to(500000);self.assertEqual(end,self.s.snapshot())
 def test_all_same_dimension_unit_pairs_against_decimal_oracle(self):
  groups=[
   [('seconds','1','0'),('milliseconds','.001','0'),('microseconds','.000001','0'),('nanoseconds','.000000001','0'),('minutes','60','0'),('hours','3600','0')],
   [('meters','1','0'),('centimeters','.01','0'),('millimeters','.001','0'),('kilometers','1000','0')],
   [('degrees','.017453292519943295','0'),('radians','1','0')],
   [('celsius','1','273.15'),('fahrenheit',str(Decimal(5)/9),str(Decimal('273.15')-Decimal(32)*Decimal(5)/9)),('kelvin','1','0')]]
  for group in groups:
   for source,scale,offset in group:
    for target,target_scale,target_offset in group:
     # Inputs keep every time and distance pair within the unbound ValueStore domain.
     value=Decimal('.0000001') if source in [r[0] for r in groups[0]] else Decimal('.25')
     expected=float((value*Decimal(scale)+Decimal(offset)-Decimal(target_offset))/Decimal(target_scale))
     expression={'convert':{'value':float(value),'from':source,'to':target}}
     with self.subTest(source=source,target=target):
      self.cmd('set',path='/out',expression=expression)
      self.assertAlmostEqual(self.s.info()['values']['/out'],expected,delta=max(1e-10,abs(expected)*1e-12))
      self.cmd('set',path='/go',value=0)
      self.cmd('trigger',id=1,source='/go',target='/out',expression=expression)
      self.cmd('set',path='/go',value=1)
      self.assertAlmostEqual(self.s.info()['values']['/out'],expected,delta=max(1e-10,abs(expected)*1e-12))

if __name__=='__main__':unittest.main()
