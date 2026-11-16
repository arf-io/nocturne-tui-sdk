"""Scheduled batches execute atomically in order and retain actual expression owners."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ScheduledBatches(unittest.TestCase):
 def test_event_copy_ack_batch_executes_and_replays(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/task','type':'json','value':None})
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[
    {'op':'emit-intent','event':'/host/task','payload':{'id':'noc-1'}},
    {'op':'set','path':'/task','intentId':1,'expression':{'intentPath':''}},
    {'op':'ack-intent','id':1}]}})
   start=s.snapshot();s.advance_to(500000)
   self.assertEqual(s.info()['values']['/task'],{'id':'noc-1'});self.assertEqual(s.info()['intents'],[])
   finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(500000);self.assertEqual(finish,s.snapshot())
 def test_queued_batch_retains_actual_sources_but_not_literal_paths(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/source','value':3});s.command({'op':'define','path':'/unused','value':7})
   s.command({'op':'define','path':'/out','value':0});s.command({'op':'define','path':'/data','type':'json','value':None})
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[
    {'op':'set','path':'/out','expression':{'path':'/source'}},
    {'op':'set','path':'/data','expression':{'literal':{'path':'/unused'}}}]}})
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'remove-value','path':'/source'})
   self.assertEqual(before,s.snapshot());s.command({'op':'remove-value','path':'/unused'})
   s.advance_to(500000);self.assertEqual(s.info()['values']['/out'],3)
 def test_invalid_child_rolls_back_schedule_registration(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/out','value':0})
   for child in [{'op':'time','timeUs':500000},{'op':'batch','commands':[]},{'op':'set','path':'/missing','value':1}]:
    before=s.snapshot()
    with self.subTest(child=child),self.assertRaises(ValueError):s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'set','path':'/out','value':2},child]}})
    self.assertEqual(before,s.snapshot())
 def test_execution_failure_rolls_back_prior_batch_children_and_clock(self):
  with NativeScene(42) as s:
   s.command({'op':'widget','id':1,'kind':'progress','min':0,'max':10})
   s.command({'op':'define','path':'/out','value':0})
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[
    {'op':'set','path':'/out','value':2},{'op':'widget','id':1,'min':5}]}})
   s.command({'op':'widget','id':1,'max':4});before=s.snapshot()
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(before,s.snapshot());s.command({'op':'cancel-schedule','id':1})
if __name__=='__main__':unittest.main()
