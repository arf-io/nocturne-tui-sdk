"""Ordered predicates inspect numeric values and exact payload operands without coercion."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class DataOrdering(unittest.TestCase):
 def test_all_ordering_operators_boundary_truth_and_strict_types(self):
  operators={'lessThan':lambda a,b:a<b,'lessOrEqual':lambda a,b:a<=b,'greaterThan':lambda a,b:a>b,'greaterOrEqual':lambda a,b:a>=b}
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/truth','value':False})
   for operator,oracle in operators.items():
    for left,right in [(1,2),(2,2),(3,2),(-1,0),(.1,.2)]:
     s.command({'op':'set','path':'/truth','expression':{operator:[left,right]}});self.assertEqual(s.info()['values']['/truth'],oracle(left,right))
    for operand in [True,None,'2',{'literal':[]},{'literal':{}}]:
     before=s.snapshot()
     with self.subTest(operator=operator,operand=operand),self.assertRaises(ValueError):s.command({'op':'set','path':'/truth','expression':{operator:[operand,2]}})
     self.assertEqual(before,s.snapshot())
 def test_retained_event_threshold_guard_and_replay(self):
  with NativeScene(42) as s:
   for command in [{'op':'define','path':'/out','value':0},{'op':'define','path':'/threshold','value':3},
    {'op':'trigger','id':1,'target':'/out','event':'/host/metric','debounceMs':500,'whenExpression':{'greaterOrEqual':[{'intentPath':'/metric'},{'path':'/threshold'}]},'value':7},
    {'op':'emit-intent','event':'/host/metric','payload':{'metric':4}}]:s.command(command)
   start=s.snapshot();s.advance_to(500000);self.assertEqual(s.info()['values']['/out'],7);self.assertEqual(len(s.info()['intents']),1)
   finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(500000);self.assertEqual(finish,s.snapshot())
if __name__=='__main__':unittest.main()
