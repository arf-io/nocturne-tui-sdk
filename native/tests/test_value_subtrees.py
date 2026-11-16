"""Structured values expose JSON Pointer leaves with retained source ownership."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ValueSubtrees(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close)
 def cmd(self,op,**kw):self.s.command({'op':op,**kw})
 def test_subtrees_numeric_leaves_and_strict_missing_paths(self):
  self.cmd('define',path='/task',value={'title':'NOC 日本','done':3,'total':4,'items':[True,None],'a/b':7})
  for path,value in [('/title',''),('/number',0),('/items',[])]:self.cmd('define',path=path,value=value)
  for target,pointer,expected in [('/title','/title','NOC 日本'),('/number','/a~1b',7),('/items','/items',[True,None])]:
   self.cmd('set',path=target,expression={'path':'/task','pointer':pointer});self.assertEqual(self.s.info()['values'][target],expected)
  self.cmd('set',path='/number',expression={'divide':[{'path':'/task','pointer':'/done'},{'path':'/task','pointer':'/total'}]})
  self.assertEqual(self.s.info()['values']['/number'],.75)
  for pointer in ['/missing','relative','/items/01']:
   before=self.s.snapshot()
   with self.assertRaises(ValueError):self.cmd('set',path='/title',expression={'path':'/task','pointer':pointer})
   self.assertEqual(before,self.s.snapshot())
 def test_retained_subtree_source_uses_prewrite_epoch_and_owns_lifetime(self):
  self.cmd('define',path='/go',value=0);self.cmd('define',path='/task',value={'title':'before'});self.cmd('define',path='/out',value='')
  self.cmd('trigger',id=1,source='/go',target='/task',expression={'literal':{'title':'after'}})
  self.cmd('trigger',id=2,source='/go',target='/out',expression={'path':'/task','pointer':'/title'})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/task')
  self.assertEqual(before,self.s.snapshot());self.cmd('set',path='/go',value=1)
  self.assertEqual(self.s.info()['values']['/out'],'before');saved=self.s.snapshot();self.s.restore(saved);self.assertEqual(saved,self.s.snapshot())
if __name__=='__main__':unittest.main()
