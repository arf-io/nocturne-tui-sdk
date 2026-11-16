"""JSON data keys retain decoded identity without native identifier truncation."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class JsonObjectKeys(unittest.TestCase):
 def test_structured_equality_uses_long_decoded_keys_independent_of_order(self):
  with NativeScene(42) as s:
   value={'日'*500:3,'nul\0key':4,'tail':[1,2]}
   s.command({'op':'define','path':'/object','type':'json','value':value})
   s.command({'op':'define','path':'/equal','value':False})
   s.command({'op':'set','path':'/equal','expression':{'equal':[{'path':'/object'},{'literal':dict(reversed(list(value.items())))}]}})
   self.assertIs(s.info()['values']['/equal'],True);saved=s.snapshot();s.render();self.assertEqual(saved,s.snapshot())
 def test_short_subtree_remains_addressable_after_long_and_nul_keys(self):
  value={'k'*1000:1,'nul\0key':2,'wanted':7}
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/object','type':'json','value':value});s.command({'op':'define','path':'/out','value':0})
   s.command({'op':'set','path':'/out','expression':{'path':'/object','pointer':'/wanted'}})
   self.assertEqual(s.info()['values']['/out'],7)
   s.command({'op':'emit-intent','event':'/host/object','payload':value})
   s.command({'op':'set','path':'/out','intentId':1,'expression':{'intentPath':'/wanted'}})
   self.assertEqual(s.info()['values']['/out'],7);saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
 def test_long_unicode_and_nul_data_keys_round_trip_and_copy(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/object','type':'json','value':None})
   for identity,key in enumerate(['k'*2000,'日'*500,'nul\0key','😀'*200],1):
    value={key:identity};s.command({'op':'set','path':'/object','value':value})
    self.assertEqual(s.info()['values']['/object'],value);saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
    s.command({'op':'emit-intent','event':'/host/object','payload':value})
    s.command({'op':'set','path':'/object','intentId':identity,'expression':{'intentPath':''}})
    s.command({'op':'ack-intent','id':identity});self.assertEqual(s.info()['values']['/object'],value)
 def test_decoded_duplicate_long_escaped_and_nul_keys_reject_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/object','type':'json','value':None});before=s.snapshot()
   for left,right in [('x'*2000,'x'*2000),('日'*200,'\\u65e5'*200),('a\\u0000b','a\\u0000b'),('abc','a\\u0062c')]:
    source='{"op":"set","path":"/object","value":{"'+left+'":1,"'+right+'":2}}'
    with self.subTest(left=left[:20]),self.assertRaises(ValueError):s.command_raw(source.encode())
    self.assertEqual(before,s.snapshot())
 def test_full_128_byte_state_patch_name_is_authorable(self):
  with NativeScene(42) as s:
   name='s'*128;rule={'id':'state','states':{name:{'enabled':False}}}
   s.command({'op':'character-rule','rule':rule});self.assertEqual(s.info()['characterRules'],[rule])
