"""Bound flow rates preserve the same cumulative history as public flow edits."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class FlowValueBindings(unittest.TestCase):
 def test_rates_match_public_edits_with_history_and_replay(self):
  with NativeScene(42) as s,NativeScene(42) as oracle:
   base={'op':'flow','id':1,'flux':2,'stages':[{'name':'fall','delayUs':100000,'tailUs':500000}]}
   for scene in [s,oracle]:scene.command(base);scene.advance_to(250000)
   s.command({'op':'define','path':'/flux','value':4,'binding':{'family':'flow','id':1,'field':'flux'}})
   oracle.command({'op':'flow-rate','id':1,'flux':4})
   for time,value in [(500000,0),(750000,3),(750000,5),(1000000,5)]:
    s.advance_to(time);oracle.advance_to(time)
    s.command({'op':'set','path':'/flux','value':value});oracle.command({'op':'flow-rate','id':1,'flux':value})
    self.assertEqual(s.info()['flows'],oracle.info()['flows'])
   start=s.snapshot();s.advance_to(2000000);finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot())
   s.restore(start);s.advance_to(2000000);self.assertEqual(finish,s.snapshot())
   oracle.advance_to(2000000);s.command({'op':'remove-value','path':'/flux'});self.assertEqual(s.snapshot(),oracle.snapshot())
 def test_invalid_binding_and_rates_are_atomic(self):
  with NativeScene(42) as s:
   s.command({'op':'flow','id':1,'flux':2,'stages':[{'name':'fall'}]})
   for binding,value in [({'family':'flow','id':99,'field':'flux'},2),({'family':'flow','id':1,'field':'stage'},2),({'family':'flow','id':1,'field':'flux'},-1),({'family':'flow','id':1,'field':'flux'},1000001)]:
    before=s.snapshot()
    with self.subTest(binding=binding,value=value),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':binding})
    self.assertEqual(before,s.snapshot())
 def test_full_history_rejects_new_epoch_but_allows_same_tick_replacement(self):
  with NativeScene(42) as s:
   s.command({'op':'flow','id':1,'flux':2,'stages':[{'name':'fall'}]})
   s.command({'op':'define','path':'/flux','value':2,'binding':{'family':'flow','id':1,'field':'flux'}})
   for epoch in range(1,128):
    s.advance_to(epoch*1000);s.command({'op':'set','path':'/flux','value':epoch+2})
   s.command({'op':'set','path':'/flux','value':999})
   s.advance_to(128000);before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/flux','value':1000})
   self.assertEqual(before,s.snapshot());self.assertEqual(s.info()['values']['/flux'],999)
   s.command({'op':'set','path':'/flux','value':999});self.assertEqual(before,s.snapshot())
 def test_retained_expression_controls_flow_without_consuming_event(self):
  with NativeScene(42) as s:
   for command in [
    {'op':'flow','id':1,'flux':2,'stages':[{'name':'fall'}]},
    {'op':'define','path':'/flux','value':2,'binding':{'family':'flow','id':1,'field':'flux'}},
    {'op':'trigger','id':1,'target':'/flux','event':'/host/flow','whenExpression':True,'expression':{'intentPath':'/flux'}},
    {'op':'emit-intent','event':'/host/flow','payload':{'flux':5}},
   ]:s.command(command)
   self.assertEqual(s.info()['values']['/flux'],5);self.assertEqual(len(s.info()['intents']),1)
   self.assertEqual(s.info()['valueDescriptors']['/flux']['binding'],{'family':'flow','id':1,'field':'flux'})
if __name__=='__main__':unittest.main()
