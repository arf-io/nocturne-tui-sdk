"""Structured native results retain cached subtrees and replay without host assembly."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class StructuredExpressions(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close);self.cmd('define',path='/out',type='json',value={})
 def cmd(self,op,**kw):self.s.command({'op':op,**kw})
 def test_arrays_objects_empty_containers_and_unicode_keys(self):
  self.cmd('define',path='/title',value='NOC 日本');self.cmd('define',path='/ready',value=True)
  expression={'object':{'title':{'path':'/title'},'日本/a~b':{'array':[{'path':'/ready'},None,{'literal':{'nested':[1,2]}}]},'empty':{'object':{}}}}
  self.cmd('set',path='/out',expression=expression)
  self.assertEqual(self.s.info()['values']['/out'],{'title':'NOC 日本','日本/a~b':[True,None,{'nested':[1,2]}],'empty':{}})
  self.cmd('set',path='/out',expression={'array':[]});self.assertEqual(self.s.info()['values']['/out'],[])
  saved=self.s.snapshot();self.s.render();self.assertEqual(saved,self.s.snapshot());self.s.restore(saved);self.assertEqual(saved,self.s.snapshot())
 def test_retained_structured_action_selects_exact_event_and_owns_copy(self):
  self.cmd('define',path='/go',value=1)
  self.cmd('trigger',id=1,source='/go',target='/out',event='/host/task',debounceMs=500,
   expression={'object':{'task':{'intentPath':'/task'},'ready':{'equal':[{'intentPath':'/status'},'ready']}}})
  self.cmd('emit-intent',event='/host/task',payload={'task':{'id':'noc-1','items':[True,None]},'status':'ready'})
  start=self.s.snapshot();self.s.advance_to(500000);finish=self.s.snapshot()
  self.assertEqual(self.s.info()['values']['/out'],{'task':{'id':'noc-1','items':[True,None]},'ready':True})
  self.s.restore(start);self.s.advance_to(500000);self.assertEqual(finish,self.s.snapshot());self.cmd('ack-intent',id=1)
  self.assertEqual(self.s.info()['values']['/out']['task']['id'],'noc-1')
 def test_bounds_and_missing_subtrees_roll_back_atomically(self):
  self.cmd('define',path='/long',value='x'*3000)
  for expression in [{'array':[{'path':'/long'},{'path':'/long'}]},{'object':{'task':{'path':'/missing'}}},{'array':list(range(17))}]:
   before=self.s.snapshot()
   with self.subTest(expression=expression),self.assertRaises(ValueError):self.cmd('set',path='/out',expression=expression)
   self.assertEqual(before,self.s.snapshot())
 def test_wrapping_maximum_depth_subtree_rejects_without_commit(self):
  value=1
  for _ in range(7):value=[value]
  self.cmd('define',path='/deep',type='json',value=value);before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('set',path='/out',expression={'array':[{'path':'/deep'}]})
  self.assertEqual(before,self.s.snapshot())
if __name__=='__main__':unittest.main()
