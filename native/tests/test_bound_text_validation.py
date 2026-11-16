"""Bound component text follows public text validation without weakening data strings."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
CASES=[('widget','text',{'op':'widget','id':1,'kind':'button'}),
 ('window','title',{'op':'window','id':1}),('window','text',{'op':'window','id':1}),
 ('text','text',{'op':'text','id':1,'text':'old'}),
 ('node','label',{'op':'node','id':1,'label':'old'}),('node','detail',{'op':'node','id':1,'label':'old'}),
 ('indicator','sequence',{'op':'indicator','id':1})]
class BoundTextValidation(unittest.TestCase):
 def test_forbidden_controls_reject_both_authoring_routes(self):
  for family,field,base in CASES:
   with self.subTest(family=family,field=field),NativeScene(42) as s:
    s.command(base);s.command({'op':'define','path':'/text','value':'old','binding':{'family':family,'id':1,'field':field}})
    for control in ['\x00','\x01','\x1b','\x1f']:
     for command in [{'op':family,'id':1,field:'before'+control+'after'},
      {'op':'set','path':'/text','value':'before'+control+'after'}]:
      before=s.snapshot()
      with self.subTest(command=command),self.assertRaises(ValueError):s.command(command)
      self.assertEqual(before,s.snapshot())
 def test_tabs_newlines_and_unicode_remain_valid(self):
  for family,field,base in CASES:
   with self.subTest(family=family,field=field),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:scene.command(base)
    value='日本\té\n👩‍🔧'
    s.command({'op':'define','path':'/text','value':value,'binding':{'family':family,'id':1,'field':field}})
    s.command({'op':'remove-value','path':'/text'});oracle.command({'op':family,'id':1,field:value})
    self.assertEqual(s.snapshot(),oracle.snapshot())
 def test_unbound_data_strings_retain_control_characters(self):
  with NativeScene(42) as s:
   value='\x00\x01\x1b';s.command({'op':'define','path':'/data','value':value})
   self.assertEqual(s.info()['values']['/data'],value);saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
if __name__=='__main__':unittest.main()
