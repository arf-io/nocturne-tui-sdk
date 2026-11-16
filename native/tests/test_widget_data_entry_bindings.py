"""Individual numeric data slots are addressable without replacing a plot series."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class WidgetDataEntryBindings(unittest.TestCase):
 def test_first_middle_and_last_full_capacity_entries_match_public_data_edit(self):
  for index in [0,63,127]:
   with self.subTest(index=index),NativeScene(42) as s,NativeScene(42) as oracle:
    initial=list(range(128));expected=initial[:];expected[index]=-17
    for scene in [s,oracle]:scene.command({'op':'widget','id':1,'kind':'line','data':initial,'revealMs':2000});scene.advance_to(250000)
    s.command({'op':'define','path':'/entry','value':-17,'binding':{'family':'widget','id':1,'field':f'data.{index}'}})
    oracle.command({'op':'widget','id':1,'data':expected});s.command({'op':'remove-value','path':'/entry'});self.assertEqual(s.snapshot(),oracle.snapshot())
    start=s.snapshot();s.advance_to(1000000);oracle.advance_to(1000000);self.assertEqual(s.snapshot(),oracle.snapshot());self.assertEqual(s.render().bytes,oracle.render().bytes)
    finish=s.snapshot();s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_index_shape_and_removed_slot_are_atomic(self):
  with NativeScene(42) as s:
   s.command({'op':'widget','id':1,'kind':'bars','data':[1,2]})
   for field in ['data.2','data.128','data.00','data.-1','data.1.extra','data.']:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':3,'binding':{'family':'widget','id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
   s.command({'op':'define','path':'/entry','value':3,'binding':{'family':'widget','id':1,'field':'data.1'}})
   s.command({'op':'widget','id':1,'data':[1]});saved=s.snapshot();s.restore(saved)
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/entry','value':4})
   self.assertEqual(saved,s.snapshot());s.command({'op':'bind','path':'/entry','binding':{'family':'widget','id':1,'field':'data.0'}})
if __name__=='__main__':unittest.main()
