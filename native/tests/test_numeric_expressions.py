"""Native formulas over registered values and exact retained intention fields."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class NumericExpressions(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene(42);self.addCleanup(self.s.close)
  for path,value in [('/out',0),('/scale',2),('/offset',3)]:self.s.command({'op':'define','path':path,'value':value})
 def evaluate(self,expression,**extra):self.s.command({'op':'set','path':'/out','expression':expression,**extra});return self.s.info()['values']['/out']
 def test_operators_and_value_paths_have_independent_results(self):
  for expr,expected in [(4,4),({'path':'/scale'},2),({'add':[1,2,3]},6),({'subtract':[10,3]},7),({'multiply':[2,3,4]},24),({'divide':[7,2]},3.5),({'min':[7,2,5]},2),({'max':[7,2,5]},7),({'negate':3},-3),({'abs':-3},3),({'clamp':{'value':8,'min':2,'max':5}},5),({'clamp':{'value':-8,'min':2,'max':5}},2),({'add':[{'multiply':[{'path':'/scale'},4]},{'path':'/offset'}]},11)]:
   with self.subTest(expression=expr):self.assertEqual(self.evaluate(expr),expected)
 def test_retained_fields_use_exact_intent_and_do_not_consume_it(self):
  for ident,value in [(1,99),(2,7)]:
   self.s.command({'op':'status','id':ident,'area':0,'text':'Action','durationMs':0,'actions':[{'id':1,'label':'Confirm','event':'/task/approved','value':value}]});self.s.command({'op':'notification-action','id':ident,'actionId':1})
  before=self.s.info()['intents']
  for field,value in [('value',7),('id',2),('messageId',2),('actionId',1),('messageSequence',2),('atUs',0)]:self.assertEqual(self.evaluate({'intentField':field},intentId=2),value)
  expr={'subtract':[{'add':[{'multiply':[2,{'intentField':'value'}]},{'intentField':'actionId'}]},{'path':'/offset'}]}
  self.assertEqual(self.evaluate(expr,intentId=2),12);self.assertEqual(self.s.info()['intents'],before)
  self.s.command({'op':'ack-intent','id':2});saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.evaluate(expr,intentId=2)
  self.assertEqual(self.s.snapshot(),saved)
 def test_bad_shapes_missing_references_and_arithmetic_are_atomic(self):
  bad=[{'path':'/missing'},{'intentField':'value'},{'intentField':'event'},{'add':[]},{'add':[1]},{'subtract':[1,2,3]},{'divide':[1,0]},{'multiply':[1e12,2]},{'clamp':{'value':1,'min':2,'max':0}},{'add':[1,2],'abs':3},{'path':'/scale','extra':1},True,'2',{'add':[1]*17}]
  for expr in bad:
   saved=self.s.snapshot()
   with self.subTest(expression=expr),self.assertRaises(ValueError):self.evaluate(expr)
   self.assertEqual(self.s.snapshot(),saved)
  # Schema56 expands the unbound domain; the former1000001 rejection remains
  # covered as checksum-correct schema55 import in test_wide_unbound_values.
  for command in [{'op':'set','path':'/out','expression':2,'value':3},{'op':'set','path':'/out','value':3,'intentId':1},{'op':'set','path':'/out','expression':2,'intentId':999},{'op':'set','path':'/out','expression':1e12+1}]:
   saved=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command(command)
   self.assertEqual(self.s.snapshot(),saved)
 def test_depth_node_limits_and_self_reference(self):
  expr=1
  for _ in range(7):expr={'negate':expr}
  self.assertEqual(self.evaluate(expr),-1)
  with self.assertRaises(ValueError):self.evaluate({'negate':expr})
  self.assertEqual(self.evaluate({'add':[{'negate':-1} for _ in range(15)]}),15)
  with self.assertRaises(ValueError):self.evaluate({'add':[{'negate':-1} for _ in range(16)]})
  self.assertEqual(self.evaluate({'add':[{'path':'/out'},1]}),16)
 def test_batch_and_bound_target_failure_roll_back_entire_input(self):
  self.s.command({'op':'define','path':'/fov','value':60,'binding':{'family':'camera','field':'fov'}});saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.command({'op':'batch','commands':[{'op':'set','path':'/scale','value':4},{'op':'set','path':'/fov','expression':{'multiply':[{'path':'/scale'},100]}}]})
  self.assertEqual(self.s.snapshot(),saved)
 def test_scheduled_formula_uses_execution_values_and_replays(self):
  self.s.command({'op':'schedule','id':1,'atUs':1000000,'command':{'op':'set','path':'/out','expression':{'multiply':[{'path':'/scale'},4]}}});self.s.command({'op':'set','path':'/scale','value':3});start=self.s.snapshot()
  self.s.advance_to(1000000);self.assertEqual(self.s.info()['values']['/out'],12);finish=self.s.snapshot();self.s.render();self.assertEqual(self.s.snapshot(),finish)
  self.s.restore(start);self.s.advance_to(1000000);self.assertEqual(self.s.snapshot(),finish)
if __name__=='__main__':unittest.main()
