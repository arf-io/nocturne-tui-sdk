"""Explicit binding replacement preserves value identity and old authored properties."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ValueRebinding(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene(42);self.addCleanup(self.s.close)
  for identity in [1,2]:self.cmd('widget',id=identity,kind='progress',value=0)
  self.cmd('define',path='/control',value=.5,binding={'family':'widget','id':1,'field':'value'})
 def cmd(self,op,**kw):self.s.command({'op':op,**kw})
 def test_rebinding_is_explicit_and_preserves_old_property(self):
  self.cmd('bind',path='/control',binding={'family':'widget','id':2,'field':'value'})
  self.cmd('set',path='/control',value=.8)
  values={w['id']:w['value'] for w in self.s.info()['widgets']}
  self.assertEqual(values,{1:.5,2:.8});self.assertEqual(self.s.info()['values']['/control'],.8)
  self.cmd('bind',path='/control',binding=None);self.cmd('set',path='/control',value=.2)
  self.assertEqual({w['id']:w['value'] for w in self.s.info()['widgets']},values)
 def test_failed_rebinding_preserves_entire_source(self):
  for binding in [{'family':'widget','id':99,'field':'value'},
   {'family':'widget','id':1,'field':'width'},{'family':'camera','field':'fov'},
   {'family':'widget','id':2,'field':'missing'}]:
   before=self.s.snapshot()
   with self.subTest(binding=binding),self.assertRaises(ValueError):self.cmd('bind',path='/control',binding=binding)
   self.assertEqual(before,self.s.snapshot())
 def test_existing_formula_references_survive_rebinding_and_replay(self):
  self.cmd('define',path='/go',value=0);self.cmd('define',path='/out',value=0)
  self.cmd('trigger',id=1,source='/go',target='/out',expression={'path':'/control'})
  self.cmd('bind',path='/control',binding=None)
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/control')
  self.cmd('schedule',id=1,atUs=500000,command={'op':'bind','path':'/control','binding':{'family':'widget','id':2,'field':'value'}})
  start=self.s.snapshot();self.s.advance_to(1000000);finish=self.s.snapshot()
  self.s.render();self.assertEqual(finish,self.s.snapshot());self.s.restore(start);self.s.advance_to(1000000);self.assertEqual(finish,self.s.snapshot())
 def test_detaching_supported_large_geometry_preserves_value_and_narrow_guard(self):
  self.cmd('define',path='/large',value=2147483647,binding={'family':'widget','id':1,'field':'width'})
  self.cmd('bind',path='/large',binding=None)
  self.assertEqual(self.s.info()['values']['/large'],2147483647)
  self.assertEqual(self.s.info()['widgets'][0]['width'],2147483647)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('bind',path='/large',binding={'family':'widget','id':1,'field':'alpha'})
  self.assertEqual(before,self.s.snapshot());self.cmd('set',path='/large',value=1000)
  self.assertEqual(self.s.info()['widgets'][0]['width'],2147483647)
 def test_field_expiry_cannot_redirect_binding_to_reused_slot(self):
  self.cmd('field',x=10,y=10,lifeMs=100)
  self.cmd('define',path='/field',value=2,binding={'family':'field','id':1,'field':'width'})
  self.s.advance_to(200000);self.cmd('field',x=10,y=10,lifeMs=1000)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('set',path='/field',value=3)
  self.assertEqual(before,self.s.snapshot())
  self.cmd('bind',path='/field',binding={'family':'field','id':2,'field':'width'})
  self.assertEqual(self.s.info()['fields'][0]['width'],2)
 def test_pending_rebinding_protects_value_until_cancelled(self):
  self.cmd('schedule',id=1,atUs=500000,command={'op':'bind','path':'/control','binding':None})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/control')
  self.assertEqual(before,self.s.snapshot());self.cmd('cancel-schedule',id=1);self.cmd('remove-value',path='/control')
if __name__=='__main__':unittest.main()
