"""String-bound wait sequences match public edits on the continuous scene clock."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class IndicatorStringBinding(unittest.TestCase):
 def test_sequence_public_edit_oracle_and_replay(self):
  with NativeScene(42) as s,NativeScene(42) as oracle:
   for scene in [s,oracle]:scene.command({'op':'indicator','id':1,'x':12,'y':8,'sequence':'|/-','stepMs':120});scene.advance_to(250000)
   s.command({'op':'define','path':'/wait','value':'◐◓◑◒','binding':{'family':'indicator','id':1,'field':'sequence'}})
   oracle.command({'op':'indicator','id':1,'sequence':'◐◓◑◒'});s.command({'op':'remove-value','path':'/wait'})
   self.assertEqual(s.snapshot(),oracle.snapshot())
   start=s.snapshot()
   for time in [500000,1000000,2000000]:
    s.advance_to(time);oracle.advance_to(time);self.assertEqual(s.snapshot(),oracle.snapshot());self.assertEqual(s.render().bytes,oracle.render().bytes)
   finish=s.snapshot();s.restore(start);s.advance_to(2000000);self.assertEqual(finish,s.snapshot())
 def test_empty_capacity_and_missing_owner_reject_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'indicator','id':1})
   s.command({'op':'define','path':'/wait','value':'x'*128,'binding':{'family':'indicator','id':1,'field':'sequence'}})
   for value in ['', 'x'*129, True, '\u0001']:
    before=s.snapshot()
    with self.subTest(value=value),self.assertRaises(ValueError):s.command({'op':'set','path':'/wait','value':value})
    self.assertEqual(before,s.snapshot())
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'bind','path':'/wait','binding':{'family':'indicator','id':99,'field':'sequence'}})
   self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
