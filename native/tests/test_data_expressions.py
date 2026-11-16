"""Compiled typed actions/guards preserve event ownership and one read epoch."""
from pathlib import Path
import sys,unittest,struct,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class DataExpressions(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close)
 def cmd(self,op,**kw):self.s.command({'op':op,**kw})
 def test_direct_operators_and_semantic_json_equality(self):
  for path,value in [('/name','NOC'),('/ready',True),('/flag',False),('/out',''),('/task',{})]:self.cmd('define',path=path,value=value)
  self.cmd('set',path='/out',expression={'concat':[{'path':'/name'},{'literal':' 日本 "quoted"'}]})
  self.assertEqual(self.s.info()['values']['/out'],'NOC 日本 "quoted"')
  for expression,expected in [({'and':[{'path':'/ready'},{'not':{'path':'/flag'}}]},True),({'or':[{'literal':False},{'literal':False}]},False),
   ({'equal':[{'literal':{'a':[True,None,1],'b':'日'}},{'literal':{'b':'日','a':[True,None,1]}}]},True),
   ({'equal':[{'literal':True},{'literal':1}]},False)]:
   self.cmd('set',path='/flag',expression=expression);self.assertIs(self.s.info()['values']['/flag'],expected)
  self.cmd('set',path='/out',expression={'if':{'condition':{'path':'/ready'},'then':{'literal':'ready'},'else':{'intentPath':'/missing'}}})
  self.assertEqual(self.s.info()['values']['/out'],'ready')
 def test_retained_typed_action_and_guard_debounce_replay(self):
  self.cmd('define',path='/name',value='');self.cmd('define',path='/enabled',value=True)
  self.cmd('trigger',id=1,target='/name',event='/host/task',debounceMs=500,
   whenExpression={'and':[{'path':'/enabled'},{'equal':[{'intentPath':'/task/status'},{'literal':'ready'}]}]},
   expression={'concat':[{'literal':'Task: '},{'intentPath':'/task/title'}]})
  self.cmd('emit-intent',event='/host/task',payload={'task':{'status':'ready','title':'NOC 日本'}})
  start=self.s.snapshot();self.s.advance_to(500000);finish=self.s.snapshot()
  self.assertEqual(self.s.info()['values']['/name'],'Task: NOC 日本');self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],1)
  self.s.render();self.assertEqual(finish,self.s.snapshot());self.s.restore(start);self.s.advance_to(500000);self.assertEqual(finish,self.s.snapshot())
 def test_guard_source_and_action_sources_share_prewrite_epoch(self):
  for path,value in [('/go',0),('/a','before'),('/out',''),('/flag',False)]:self.cmd('define',path=path,value=value)
  self.cmd('trigger',id=1,source='/go',target='/a',expression={'literal':'after'})
  self.cmd('trigger',id=2,source='/go',target='/out',expression={'path':'/a'})
  self.cmd('trigger',id=3,target='/flag',whenExpression={'equal':[{'path':'/a'},{'literal':'before'}]},expression={'literal':True})
  self.cmd('set',path='/go',value=1)
  self.assertEqual(self.s.info()['values']['/a'],'after');self.assertEqual(self.s.info()['values']['/out'],'before');self.assertIs(self.s.info()['values']['/flag'],True)
 def test_lifetime_and_action_type_fault_rollback(self):
  self.cmd('define',path='/go',value=0);self.cmd('define',path='/out',value='');self.cmd('define',path='/name',value='NOC')
  self.cmd('trigger',id=1,source='/go',target='/out',expression={'path':'/name'});before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/name')
  self.assertEqual(before,self.s.snapshot());self.cmd('remove-trigger',id=1);self.cmd('remove-value',path='/name')
  self.cmd('trigger',id=1,source='/go',target='/out',expression={'literal':True});before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('set',path='/go',value=1)
  self.assertEqual(before,self.s.snapshot())
 def test_guard_fault_and_string_overflow_are_atomic(self):
  self.cmd('define',path='/ready',value=False);self.cmd('define',path='/long',value='x'*3000);self.cmd('define',path='/out',value='')
  for command in [dict(op='set',path='/ready',expression={'and':[{'literal':True},{'literal':1}]}),
   dict(op='set',path='/out',expression={'concat':[{'path':'/long'},{'path':'/long'}]})]:
   before=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command(command)
   self.assertEqual(before,self.s.snapshot())
 def test_same_event_reauthor_preserves_watermark_and_explicit_teardown(self):
  self.cmd('define',path='/out',value='');self.cmd('define',path='/ready',value=True)
  rule={'op':'trigger','id':1,'target':'/out','event':'/host/task','whenExpression':{'path':'/ready'},'expression':{'intentPath':'/title'}}
  self.s.command(rule);self.cmd('emit-intent',event='/host/task',payload={'title':'first'});self.assertEqual(self.s.info()['values']['/out'],'first')
  self.s.command(rule);self.cmd('set',path='/out',value='manual');self.assertEqual(self.s.info()['values']['/out'],'manual')
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/ready')
  self.assertEqual(before,self.s.snapshot());self.cmd('remove-trigger',id=1);self.cmd('remove-value',path='/ready')
 def test_crc_correct_hostile_compiled_data_formula_rejects_atomically(self):
  self.cmd('define',path='/go',value=0);self.cmd('define',path='/out',value='')
  self.cmd('trigger',id=1,source='/go',target='/out',expression={'literal':'NOC'})
  before=self.s.snapshot();base=24+6483424
  for offset,fmt,value in [(base,'i',32),(base+8,'i',99),(base+12,'i',127),(base+5216,'I',4096),(base+13416,'i',1)]:
   bad=bytearray(before);struct.pack_into('<'+fmt,bad,offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.subTest(offset=offset),self.assertRaises(ValueError):self.s.restore(bad)
   self.assertEqual(before,self.s.snapshot())
 def test_typed_style_guard_is_reversible_pure_and_owns_sources(self):
  self.cmd('widget',id=1,kind='button',text='NOC',alpha=.2)
  self.cmd('state-register',id=1,path='/app/button',role='control',target={'family':'widget','id':1})
  self.cmd('define',path='/status',value='waiting')
  self.cmd('style-rule',id=1,selector={'family':'widget','id':1},whenExpression={'equal':[{'path':'/status'},{'literal':'ready'}]},style={'alpha':.8})
  self.assertEqual(self.s.info()['registeredStates'][0]['effective']['alpha'],.2)
  self.cmd('set',path='/status',value='ready');before=self.s.snapshot();self.assertEqual(self.s.info()['registeredStates'][0]['effective']['alpha'],.8)
  self.s.render();self.assertEqual(before,self.s.snapshot())
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/status')
  self.assertEqual(before,self.s.snapshot());self.cmd('set',path='/status',value='waiting')
  self.assertEqual(self.s.info()['registeredStates'][0]['effective']['alpha'],.2)
  self.cmd('remove-style-rule',id=1);self.cmd('remove-value',path='/status')
 def test_numeric_units_compose_inside_typed_predicates(self):
  self.cmd('define',path='/seconds',value=2);self.cmd('define',path='/ready',value=False)
  expression={'equal':[{'convert':{'value':{'path':'/seconds'},'from':'seconds','to':'milliseconds'}},2000]}
  self.cmd('set',path='/ready',expression=expression);self.assertIs(self.s.info()['values']['/ready'],True)
  self.cmd('trigger',id=1,target='/ready',whenExpression=expression,expression={'literal':False})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/seconds')
  self.assertEqual(before,self.s.snapshot());self.cmd('remove-trigger',id=1);self.cmd('remove-value',path='/seconds')
 def test_typed_conditionals_can_return_numeric_results_without_coercion(self):
  self.cmd('define',path='/ready',value=True);self.cmd('define',path='/seconds',value=2);self.cmd('define',path='/out',value=0)
  expression={'if':{'condition':{'path':'/ready'},'then':{'convert':{'value':{'path':'/seconds'},'from':'seconds','to':'milliseconds'}},'else':{'divide':[1,0]}}}
  self.cmd('set',path='/out',expression=expression);self.assertEqual(self.s.info()['values']['/out'],2000)
  self.cmd('define',path='/go',value=0);self.cmd('trigger',id=1,source='/go',target='/out',expression=expression,action='increment')
  self.cmd('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/out'],4000)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/ready')
  self.assertEqual(before,self.s.snapshot())
 def test_oldest_typed_guard_candidate_blocks_later_event_until_acknowledged(self):
  self.cmd('define',path='/out',value='')
  self.cmd('trigger',id=1,target='/out',event='/host/task',whenExpression={'equal':[{'intentPath':'/status'},'ready']},expression={'intentPath':'/title'})
  self.cmd('emit-intent',event='/host/task',payload={'status':'waiting','title':'first'})
  self.cmd('emit-intent',event='/host/task',payload={'status':'ready','title':'second'})
  self.assertEqual(self.s.info()['values']['/out'],'');self.assertEqual(self.s.info()['triggers'][0]['intentCandidate']['id'],1)
  self.cmd('ack-intent',id=1);self.s.advance_to(100000)
  self.assertEqual(self.s.info()['values']['/out'],'second');self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],2)
  self.assertEqual([i['id'] for i in self.s.info()['intents']],[2])
 def test_queued_typed_guards_protect_sources_and_atomic_selected_guard_fault(self):
  self.cmd('define',path='/ready',value=True);self.cmd('define',path='/out',value='')
  self.cmd('schedule',id=1,atUs=500000,command={'op':'trigger','id':1,'target':'/out','whenExpression':{'path':'/ready'},'expression':'Ready'})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('remove-value',path='/ready')
  self.assertEqual(before,self.s.snapshot());self.cmd('cancel-schedule',id=1);self.cmd('remove-value',path='/ready')
  self.cmd('trigger',id=1,target='/out',event='/host/task',whenExpression={'intentPath':'/ready'},expression={'intentPath':'/title'})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('emit-intent',event='/host/task',payload={'ready':1,'title':'bad guard type'})
  self.assertEqual(before,self.s.snapshot());self.cmd('emit-intent',event='/host/task',payload={'ready':True,'title':'Ready'})
  self.assertEqual(self.s.info()['values']['/out'],'Ready');self.assertEqual(self.s.info()['intents'][0]['id'],1)
if __name__=='__main__':unittest.main()
