"""Host-origin structured events share retained intent ownership and replay."""
from pathlib import Path
import sys,unittest,struct,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class HostEvents(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close)
 def cmd(self,op,**kw):return self.s.command({'op':op,**kw})
 def test_all_json_payload_types_are_retained_until_explicit_ack(self):
  payloads=[None,True,False,42,.5,'Unicode é / 日本',[1,False,'a'],{'task':{'id':'noc-1','ready':True},'items':[1,2]}]
  for payload in payloads:self.cmd('emit-intent',event='/host/task',payload=payload)
  intents=self.s.info()['intents'];self.assertEqual([i['payload'] for i in intents],payloads)
  self.assertTrue(all(i['origin']=='host' and i['messageId']==0 and i['actionId']==0 for i in intents))
  before=self.s.snapshot();self.s.render();self.assertEqual(before,self.s.snapshot())
  self.s.restore(before);self.assertEqual(self.s.info()['intents'],intents)
  self.cmd('ack-intent',id=1);self.assertEqual(len(self.s.info()['intents']),len(payloads)-1)
 def test_numeric_trigger_uses_exact_host_event_without_consuming_payload(self):
  self.cmd('define',path='/go',value=1);self.cmd('define',path='/out',value=0)
  self.cmd('trigger',id=1,source='/go',target='/out',event='/host/approved',expression={'multiply':[{'intentField':'value'},2]})
  self.cmd('emit-intent',event='/host/other',value=99,payload={'ignored':True})
  self.cmd('emit-intent',event='/host/approved',value=7,payload={'task':'noc-1'})
  self.assertEqual(self.s.info()['values']['/out'],14)
  self.assertEqual(len(self.s.info()['intents']),2);self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],2)
 def test_capacity_and_invalid_payloads_reject_atomically(self):
  bad=[{'event':'relative'},{'event':'/bad//path'},{'event':'/host/task','payload':'x'*4096},{'event':'/host/task','value':1000001}]
  deep=0
  for _ in range(9):deep=[deep]
  bad.append({'event':'/host/task','payload':deep})
  for command in bad:
   before=self.s.snapshot()
   with self.subTest(command=command),self.assertRaises(ValueError):self.cmd('emit-intent',**command)
   self.assertEqual(before,self.s.snapshot())
  for _ in range(64):self.cmd('emit-intent',event='/host/task',payload={'ready':True})
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('emit-intent',event='/host/task')
  self.assertEqual(before,self.s.snapshot());self.cmd('ack-intent',id=1);self.cmd('emit-intent',event='/host/task',payload={'replacement':True})
  self.assertEqual(self.s.info()['intents'][-1]['id'],65)
 def test_scheduled_events_replay_with_execution_timestamp(self):
  self.cmd('schedule',id=1,atUs=500000,command={'op':'emit-intent','event':'/host/task','payload':{'ready':True},'value':3})
  start=self.s.snapshot();self.s.advance_to(1000000);finish=self.s.snapshot()
  self.assertEqual(self.s.info()['intents'][0]['atUs'],500000)
  self.s.restore(start);self.s.advance_to(1000000);self.assertEqual(finish,self.s.snapshot())
 def test_trigger_fault_rolls_back_event_identity_and_payload(self):
  self.cmd('define',path='/go',value=1)
  self.cmd('define',path='/fov',value=60,binding={'family':'camera','field':'fov'})
  self.cmd('trigger',id=1,source='/go',target='/fov',event='/host/task',expression=200)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('emit-intent',event='/host/task',payload={'ready':True})
  self.assertEqual(before,self.s.snapshot());self.cmd('remove-trigger',id=1)
  self.cmd('emit-intent',event='/host/task',payload={'ready':True});self.assertEqual(self.s.info()['intents'][0]['id'],1)
 def test_node_depth_unicode_and_import_validation(self):
  self.cmd('emit-intent',event='/host/task',payload=list(range(127)))
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.cmd('emit-intent',event='/host/task',payload=list(range(128)))
  self.assertEqual(before,self.s.snapshot())
  with self.assertRaises(ValueError):self.s.command_raw(b'{"op":"emit-intent","event":"/host/task","payload":"\\ud800"}')
  self.assertEqual(before,self.s.snapshot())
  self.cmd('ack-intent',id=1);self.cmd('emit-intent',event='/host/task',payload={'ready':True})
  before=self.s.snapshot();base=24+5433312
  for offset,fmt,value in [(base,'I',4096),(base+8,'B',93),(base+4103,'B',1),(base+8200,'I',1),(base+4,'I',0),(base+4104,'i',4),(base+4104+8,'i',1),(base+4104+24,'d',7)]:
   bad=bytearray(before);struct.pack_into('<'+fmt,bad,offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.subTest(offset=offset),self.assertRaises(ValueError):self.s.restore(bad)
   self.assertEqual(before,self.s.snapshot())
 def test_complete_metadata_retains_large_payloads(self):
  for _ in range(64):self.cmd('emit-intent',event='/host/task',payload='x'*4093)
  before=self.s.snapshot();info=self.s.info_complete()
  self.assertEqual(len(info['intents']),64);self.assertTrue(all(i['payload']=='x'*4093 for i in info['intents']))
  self.assertEqual(before,self.s.snapshot())
if __name__=='__main__':unittest.main()
