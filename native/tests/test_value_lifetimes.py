"""Explicit teardown must never alias retained consumers to reused value slots."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ValueLifetimes(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close)
 def command(self,op,**args):return self.s.command({'op':op,**args})
 def define(self,path,value=0,**args):self.command('define',path=path,value=value,**args)
 def removal_refuses(self,path):
  saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.command('remove-value',path=path)
  self.assertEqual(self.s.snapshot(),saved)
 def test_binding_removal_keeps_authored_property_and_reuses_capacity(self):
  self.command('widget',id=1,kind='progress',value=.5)
  self.define('/bound',.7,binding={'family':'widget','id':1,'field':'value'});frame=self.s.render().bytes
  self.command('remove-value',path='/bound');self.assertEqual(self.s.render().bytes,frame);self.assertNotIn('/bound',self.s.info()['values'])
  self.command('remove-value',path='/bound')
  for i in range(128):self.define('/temporary',i);self.command('remove-value',path='/temporary')
  self.assertEqual(self.s.info()['values'],{})
 def test_trigger_source_and_target_require_explicit_teardown(self):
  self.define('/source');self.define('/target');self.command('trigger',id=1,source='/source',target='/target',threshold=0,value=1)
  self.removal_refuses('/source');self.removal_refuses('/target');self.command('remove-trigger',id=1);self.command('remove-trigger',id=1)
  self.command('remove-value',path='/source');self.define('/replacement',99);self.command('set',path='/replacement',value=100)
  self.assertEqual(self.s.info()['values']['/target'],0);self.assertEqual(self.s.info()['triggers'],[])
 def test_disabled_style_maps_and_guards_still_own_references(self):
  self.define('/source');self.command('widget',id=1,kind='button')
  for configuration in [{'style':{'alpha':{'path':'/source','inputMin':0,'inputMax':1,'outputMin':.1,'outputMax':.9}}},{'style':{'alpha':.5},'when':{'path':'/source','comparison':'above','value':1}}]:
   self.command('style-rule',id=1,selector={'family':'widget'},enabled=False,**configuration);self.removal_refuses('/source');self.command('remove-style-rule',id=1)
  self.command('remove-value',path='/source');self.define('/new',1);self.assertEqual(self.s.info()['styleRules'],[])
 def test_pending_target_and_formula_references_require_cancellation(self):
  self.define('/source',2);self.define('/target')
  self.command('schedule',id=1,atUs=1000000,command={'op':'set','path':'/target','expression':{'multiply':[{'path':'/source'},3]}})
  self.removal_refuses('/source');self.removal_refuses('/target');self.command('cancel-schedule',id=1)
  self.command('remove-value',path='/source');self.command('remove-value',path='/target')
 def test_pending_style_and_trigger_references_are_preserved(self):
  self.define('/source');self.define('/target');self.command('widget',id=1,kind='button')
  commands=[{'op':'trigger','id':1,'source':'/source','target':'/target','value':1},{'op':'style-rule','id':1,'selector':{'family':'widget'},'style':{'alpha':{'path':'/source','inputMin':0,'inputMax':1,'outputMin':.1,'outputMax':.9}}}]
  for command in commands:
   self.command('schedule',id=1,atUs=1000000,command=command);self.removal_refuses('/source');self.command('cancel-schedule',id=1)
 def test_component_paths_do_not_become_value_dependencies(self):
  self.define('/shared');self.command('widget',id=1,kind='button')
  self.command('schedule',id=1,atUs=1000000,command={'op':'state-register','id':1,'path':'/shared','role':'control','target':{'family':'widget','id':1}})
  self.command('schedule',id=2,atUs=1000000,command={'op':'style-rule','id':1,'selector':{'family':'widget','path':'/shared'},'style':{'alpha':.5}})
  self.command('remove-value',path='/shared');self.s.advance_to(1000000);self.assertEqual(self.s.info()['registeredStates'][0]['path'],'/shared')
 def test_subscription_removal_preserves_intents_and_recreation_is_fresh(self):
  self.define('/enabled',1);self.define('/out')
  trigger={'op':'trigger','id':1,'source':'/enabled','threshold':0,'target':'/out','event':'/task/approved','valueFrom':'intentValue'}
  self.s.command(trigger);self.command('status',id=7,area=0,text='Action',durationMs=0,actions=[{'id':1,'label':'Confirm','event':'/task/approved','value':.5}]);self.command('notification-action',id=7,actionId=1)
  intents=self.s.info()['intents'];self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],1)
  self.command('remove-trigger',id=1);self.assertEqual(self.s.info()['intents'],intents);self.s.command(trigger);self.command('set',path='/enabled',value=1)
  self.assertEqual(self.s.info()['triggers'][0]['fireCount'],1);self.assertEqual(self.s.info()['intents'],intents)
 def test_batch_teardown_rolls_back_and_scheduled_removal_replays(self):
  self.define('/source');self.define('/target');self.command('trigger',id=1,source='/source',target='/target');saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.command('batch',commands=[{'op':'remove-trigger','id':1},{'op':'remove-value','path':'/source'},{'op':'unknown'}])
  self.assertEqual(self.s.snapshot(),saved)
  self.command('batch',commands=[{'op':'remove-trigger','id':1},{'op':'remove-value','path':'/source'}])
  self.command('schedule',id=1,atUs=1000000,command={'op':'remove-value','path':'/target'});start=self.s.snapshot();self.s.advance_to(1000000);finish=self.s.snapshot();self.assertEqual(self.s.info()['values'],{})
  self.s.restore(start);self.s.advance_to(1000000);self.assertEqual(self.s.snapshot(),finish)
if __name__=='__main__':unittest.main()
