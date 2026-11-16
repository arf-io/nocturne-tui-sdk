"""Owned structured plot data edits preserve widget identity and reveal timing."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class WidgetDataBindings(unittest.TestCase):
 def test_arrays_match_public_edits_with_existing_reveal(self):
  for data in [[1,2,3],[],[-1000000,0,1000000]]:
   with self.subTest(data=data),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:scene.command({'op':'widget','id':1,'kind':'bars','data':[5,6,7,8],'revealMs':2000});scene.advance_to(250000)
    s.command({'op':'define','path':'/series','type':'json','value':data,'binding':{'family':'widget','id':1,'field':'data'}})
    oracle.command({'op':'widget','id':1,'data':data});s.command({'op':'remove-value','path':'/series'});self.assertEqual(s.snapshot(),oracle.snapshot())
    start=s.snapshot();s.advance_to(1000000);oracle.advance_to(1000000);self.assertEqual(s.snapshot(),oracle.snapshot());self.assertEqual(s.render().bytes,oracle.render().bytes)
    finish=s.snapshot();s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_payload_copy_survives_ack_and_invalid_element_rolls_back(self):
  with NativeScene(42) as s:
   s.command({'op':'widget','id':1,'kind':'bars','data':[]})
   s.command({'op':'define','path':'/series','type':'json','value':[],'binding':{'family':'widget','id':1,'field':'data'}})
   s.command({'op':'emit-intent','event':'/host/series','payload':{'series':[2,4,6]}})
   s.command({'op':'set','path':'/series','intentId':1,'expression':{'intentPath':'/series'}});s.command({'op':'ack-intent','id':1})
   self.assertEqual(s.info()['values']['/series'],[2,4,6])
   for data in [[True],[None],['3'],{},[1000001]]:
    before=s.snapshot()
    with self.subTest(data=data),self.assertRaises(ValueError):s.command({'op':'set','path':'/series','value':data})
    self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
