"""Full registry replacement, teardown, source bounds and complete metadata."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class CharacterRegistryCapacity(unittest.TestCase):
 def test_full_rule_registry_rejects_growth_but_allows_replacement_and_reuse(self):
  with NativeScene(42) as s:
   for start in [0,64]:s.command({'op':'batch','commands':[{'op':'character-rule','rule':{'id':f'rule-{i}','enabled':False}} for i in range(start,start+64)]})
   full=s.snapshot();self.assertEqual(len(s.info()['characterRules']),128)
   with self.assertRaises(ValueError):s.command({'op':'character-rule','rule':{'id':'overflow'}})
   self.assertEqual(full,s.snapshot())
   s.command({'op':'character-rule','rule':{'id':'rule-127','priority':1,'enabled':False}})
   self.assertEqual(len(s.info()['characterRules']),128)
   s.command({'op':'remove-character-rule','id':'rule-0'});s.command({'op':'character-rule','rule':{'id':'replacement','enabled':False}})
   self.assertEqual(len(s.info()['characterRules']),128);saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
 def test_full_region_registry_complete_info_and_atomic_overflow(self):
  with NativeScene(42) as s:
   for start in range(0,1024,64):
    s.command({'op':'batch','commands':[{'op':'character-region','region':{'id':f'region-{i}','path':'/'+'p'*120+str(i),'role':'r'*128,'state':'s'*128,'cells':[]}} for i in range(start,start+64)]})
   full=s.snapshot();info=s.info_complete();self.assertEqual(len(info['characterRegions']),1024)
   self.assertEqual(info['characterRegions'][-1]['id'],'region-1023');self.assertEqual(full,s.snapshot())
   with self.assertRaises(ValueError):s.command({'op':'character-region','region':{'id':'overflow','path':'/overflow'}})
   self.assertEqual(full,s.snapshot())
   s.command({'op':'character-region','region':{'id':'region-1023','path':'/updated','cells':[]}})
   s.command({'op':'remove-character-region','id':'region-0'});s.command({'op':'character-region','region':{'id':'replacement','path':'/replacement','cells':[]}})
   self.assertEqual(len(s.info_complete()['characterRegions']),1024);saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
 def test_exact_source_byte_limit_for_rules_and_regions(self):
  with NativeScene(42) as s:
   for operation,field,definition in [('character-rule','rule',{'id':'byte-rule','enabled':False}),('character-region','region',{'id':'byte-region','path':'/byte','cells':[]})]:
    encoded=json.dumps(definition,separators=(',',':'));prefix=f'{{"op":"{operation}","{field}":'
    source=encoded[:-1]+' '*(4095-len(encoded))+'}'
    s.command_raw((prefix+source+'}').encode());before=s.snapshot()
    with self.assertRaises(ValueError):s.command_raw((prefix+source[:-1]+' }'+'}').encode())
    self.assertEqual(before,s.snapshot())
