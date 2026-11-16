"""Numeric payload leaves use exact retained records and JSON Pointer addressing."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PayloadExpressions(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene(42);self.addCleanup(self.s.close)
  self.cmd('define',path='/out',value=0)
 def cmd(self,op,**kw):self.s.command({'op':op,**kw})
 def evaluate(self,path,intent=1):
  self.cmd('set',path='/out',intentId=intent,expression={'intentPath':path})
  return self.s.info()['values']['/out']
 def test_objects_arrays_escaped_keys_unicode_and_root(self):
  payload={'task':{'done':7,'total':10},'items':[3,8],'a/b':4,'~key':5,'日本':6,'':9}
  self.cmd('emit-intent',event='/host/task',payload=payload)
  for path,value in [('/task/done',7),('/items/0',3),('/items/1',8),('/a~1b',4),('/~0key',5),('/日本',6),('/',9)]:
   with self.subTest(path=path):self.assertEqual(self.evaluate(path),value)
  self.cmd('set',path='/out',intentId=1,expression={'divide':[{'intentPath':'/task/done'},{'intentPath':'/task/total'}]})
  self.assertEqual(self.s.info()['values']['/out'],.7)
  self.cmd('emit-intent',event='/host/task',payload=12);self.assertEqual(self.evaluate('',2),12)
  self.assertEqual(len(self.s.info()['intents']),2)
 def test_invalid_pointer_missing_value_and_wrong_types_are_atomic(self):
  self.cmd('emit-intent',event='/host/task',payload={'items':[1],'flag':True,'text':'7','nil':None})
  for path in ['relative','/bad~2key','/missing','/items/01','/items/-','/items/1','/flag','/text','/nil','']:
   before=self.s.snapshot()
   with self.subTest(path=path),self.assertRaises(ValueError):self.evaluate(path)
   self.assertEqual(before,self.s.snapshot())
  self.cmd('ack-intent',id=1);before=self.s.snapshot()
  with self.assertRaises(ValueError):self.evaluate('/items/0')
  self.assertEqual(before,self.s.snapshot())
 def test_trigger_uses_matched_record_and_replays_payload_reference(self):
  self.cmd('define',path='/go',value=1)
  self.cmd('trigger',id=1,source='/go',target='/out',event='/host/task',debounceMs=500,expression={'intentPath':'/task/done'})
  self.cmd('emit-intent',event='/host/other',payload={'task':{'done':99}})
  self.cmd('emit-intent',event='/host/task',payload={'task':{'done':7}})
  start=self.s.snapshot();self.s.advance_to(500000);finish=self.s.snapshot()
  self.assertEqual(self.s.info()['values']['/out'],7);self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],2)
  self.s.render();self.assertEqual(finish,self.s.snapshot());self.s.restore(start);self.s.advance_to(500000);self.assertEqual(finish,self.s.snapshot())
 def test_firing_missing_payload_path_rolls_back_new_event(self):
  self.cmd('define',path='/go',value=1)
  self.cmd('trigger',id=1,source='/go',target='/out',event='/host/task',expression={'intentPath':'/task/done'})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('emit-intent',event='/host/task',payload={'task':{'other':7}})
  self.assertEqual(before,self.s.snapshot())
if __name__=='__main__':unittest.main()
