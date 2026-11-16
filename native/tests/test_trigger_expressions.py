"""Retained native formulas: event ownership, one read epoch and safe teardown."""
from pathlib import Path
import sys,unittest,gzip,struct,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TriggerExpressions(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close)
 def command(self,op,**args):return self.s.command({'op':op,**args})
 def define(self,path,value=0,**args):self.command('define',path=path,value=value,**args)
 def trigger(self,expression,**extra):self.command('trigger',id=1,source='/go',threshold=0,target='/out',expression=expression,**extra)
 def prepare(self):self.define('/go');self.define('/out');self.define('/a',6);self.define('/b',2)
 def test_all_operators_calculate_when_the_trigger_fires(self):
  expressions=[({'add':[{'path':'/a'},{'path':'/b'}]},8),({'subtract':[{'path':'/a'},{'path':'/b'}]},4),({'multiply':[{'path':'/a'},{'path':'/b'}]},12),({'divide':[{'path':'/a'},{'path':'/b'}]},3),({'min':[{'path':'/a'},{'path':'/b'}]},2),({'max':[{'path':'/a'},{'path':'/b'}]},6),({'negate':{'path':'/a'}},-6),({'abs':-6},6),({'clamp':{'value':{'path':'/a'},'min':0,'max':4}},4)]
  self.prepare()
  for expression,expected in expressions:
   with self.subTest(expression=expression):
    self.command('set',path='/go',value=0);self.trigger(expression);self.command('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/out'],expected)
 def test_every_rule_reads_the_same_prewrite_epoch(self):
  self.prepare();self.command('trigger',id=1,source='/go',threshold=0,target='/a',value=10)
  self.command('trigger',id=2,source='/go',threshold=0,target='/out',expression={'multiply':[{'path':'/a'},2]})
  self.command('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/a'],10);self.assertEqual(self.s.info()['values']['/out'],12)
 def test_runtime_fault_rolls_back_input_and_trigger_bookkeeping(self):
  self.prepare();self.command('set',path='/b',value=0);self.trigger({'divide':[{'path':'/a'},{'path':'/b'}]});saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.command('set',path='/go',value=1)
  self.assertEqual(self.s.snapshot(),saved);self.command('set',path='/b',value=2);self.command('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/out'],3)
 def test_formula_sources_own_lifetime_until_trigger_removal(self):
  self.prepare();self.trigger({'path':'/a'});saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.command('remove-value',path='/a')
  self.assertEqual(self.s.snapshot(),saved);self.command('remove-trigger',id=1);self.command('remove-value',path='/a');self.define('/replacement',99);self.assertEqual(self.s.info()['triggers'],[])
 def test_queued_trigger_formula_protects_numeric_references(self):
  self.prepare();self.command('schedule',id=1,atUs=1000000,command={'op':'trigger','id':1,'source':'/go','target':'/out','expression':{'path':'/a'}});saved=self.s.snapshot()
  with self.assertRaises(ValueError):self.command('remove-value',path='/a')
  self.assertEqual(self.s.snapshot(),saved);self.command('cancel-schedule',id=1);self.command('remove-value',path='/a')
 def test_debounce_reads_execution_time_values_and_replays_purely(self):
  self.prepare();self.trigger({'multiply':[{'path':'/a'},2]},debounceMs=500);self.command('set',path='/go',value=1)
  self.command('set',path='/a',value=8);start=self.s.snapshot();self.s.advance_to(500000);self.assertEqual(self.s.info()['values']['/out'],16)
  finish=self.s.snapshot();self.s.render();self.assertEqual(finish,self.s.snapshot());self.s.restore(start);self.s.advance_to(500000);self.assertEqual(finish,self.s.snapshot())
 def test_exact_event_formula_uses_retained_record_and_preserves_watermark(self):
  self.prepare();self.command('set',path='/go',value=1);self.trigger({'multiply':[{'intentField':'value'},{'path':'/b'}]},event='/tasks/approved')
  self.command('status',id=7,area=0,text='Approval',durationMs=0,actions=[{'id':1,'label':'Approve','event':'/tasks/approved','value':.5}]);self.command('notification-action',id=7,actionId=1)
  self.assertEqual(self.s.info()['values']['/out'],1);intents=self.s.info()['intents'];self.assertEqual(len(intents),1)
  self.trigger({'add':[{'intentField':'value'},10]},event='/tasks/approved');self.command('set',path='/go',value=1)
  self.assertEqual(self.s.info()['values']['/out'],1);self.assertEqual(self.s.info()['intents'],intents);self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],1)
 def test_registration_grammar_rejection_is_atomic(self):
  self.prepare()
  bad=[{'expression':{'path':'/missing'}},{'expression':{'intentField':'value'}},{'expression':{'add':[1]}},{'expression':{'add':[1,2],'max':[3,4]}},{'expression':1,'value':1},{'expression':1,'valueFrom':'intentValue'}]
  for fields in bad:
   saved=self.s.snapshot()
   with self.subTest(fields=fields),self.assertRaises(ValueError):self.command('trigger',id=1,source='/go',target='/out',**fields)
   self.assertEqual(self.s.snapshot(),saved)
 def test_all_numeric_event_fields_are_read_without_acknowledgement(self):
  self.prepare();self.command('set',path='/go',value=1)
  self.command('status',id=7,area=0,text='Approval',durationMs=0,actions=[{'id':1,'label':'Approve','event':'/tasks/approved','value':.5}]);self.command('notification-action',id=7,actionId=1)
  saved_intents=self.s.info()['intents']
  for field,expected in [('value',.5),('id',1),('messageId',7),('actionId',1),('messageSequence',1),('atUs',0)]:
   with self.subTest(field=field):
    self.command('remove-trigger',id=1);self.trigger({'intentField':field},event='/tasks/approved');self.command('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/out'],expected);self.assertEqual(self.s.info()['intents'],saved_intents)
 def test_bounded_formula_nodes_and_depth(self):
  self.prepare();self.trigger({'add':[{'negate':1} for _ in range(15)]});self.command('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/out'],-15)
  deep=1
  for _ in range(8):deep={'abs':deep}
  for expression in [{'add':[{'negate':1} for _ in range(16)]},deep]:
   saved=self.s.snapshot()
   with self.assertRaises(ValueError):self.trigger(expression)
   self.assertEqual(self.s.snapshot(),saved)
 def test_previous_schema_restores_existing_constant_triggers(self):
  fixture=gzip.decompress((ROOT/'tests/fixtures/schema-20261031-before-trigger-formulas.snapshot.gz').read_bytes())
  # Immutable schema31 trigger record: value at byte 4203864 retains the old parser's bits.
  expected=struct.unpack_from('<d',fixture,4203864)[0]
  self.assertEqual(expected.hex(),'0x1.6666666666667p-1')
  self.s.restore(fixture)
  self.command('set',path='/go',value=1);self.assertEqual(self.s.info()['values']['/out'],expected)
 def test_hostile_compiled_formula_snapshots_reject_without_mutating_scene(self):
  self.prepare();self.trigger({'add':[{'path':'/a'},1]})
  saved=self.s.snapshot();base=24+5266400;node=base+8
  # Recompute CRC so these reach semantic validation rather than checksum rejection.
  mutations=[(base,'i',32),(base+4,'i',1),(node,'i',999),
   (node+8,'i',1),(node+12,'B',0),(node+13,'B',1),
   (node+40+4,'i',999),(node+32,'d',1),
   (node+3*40,'i',1),(base+5216,'i',1)]
  for offset,fmt,value in mutations:
   bad=bytearray(saved);struct.pack_into('<'+fmt,bad,offset,value)
   struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.subTest(offset=offset),self.assertRaises(ValueError):self.s.restore(bad)
   self.assertEqual(self.s.snapshot(),saved)
if __name__=='__main__':unittest.main()
