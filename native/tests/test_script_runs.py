"""Whole-grapheme native script itemization references; deferred qualification."""
import ctypes as C
import unittest
from test_hull_immersion import NativeScene
class ScriptRuns(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.fn=self.scene._lib.nrScriptRuns
  self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def runs(self,text):
  source=(C.c_uint32*len(text))(*(ord(x) for x in text));n=self.fn(source,len(text),None,0);self.assertGreaterEqual(n,0);out=(C.c_uint32*(n*3))();self.assertEqual(self.fn(source,len(text),out,n),n);return [(out[i*3],out[i*3+1],int(out[i*3+2]).to_bytes(4,'big').decode('ascii')) for i in range(n)]
 def test_combining_clusters_common_context_and_mixed_scripts(self):
  before=self.scene.snapshot();self.assertEqual(self.runs('a\u0301 b'),[(0,4,'Latn')]);self.assertEqual(self.runs('  العربية'),[(0,9,'Arab')]);self.assertEqual(self.runs('abc العربية'),[(0,4,'Latn'),(4,11,'Arab')]);self.assertEqual(self.runs('👩\u200d🔧'),[(0,3,'Zyyy')]);self.assertEqual(self.runs(''),[]);self.assertEqual(self.scene.snapshot(),before)
 def test_script_extensions_choose_nearby_compatible_japanese_script(self):
  self.assertEqual(self.runs('あー'),[(0,2,'Hira')]);self.assertEqual(self.runs('アー'),[(0,2,'Kana')]);self.assertEqual(self.runs('ーあ'),[(0,2,'Hira')])
 def test_owned_binding_rows_survive_subsequent_queries(self):
  before=self.scene.snapshot();rows=self.scene.script_runs('a\u0301 العربية')
  self.assertEqual(rows,[(0,3,'Latn'),(3,10,'Arab')])
  self.assertEqual(self.scene.script_runs('アー'),[(0,2,'Kana')])
  self.assertEqual(rows,[(0,3,'Latn'),(3,10,'Arab')])
  rows[0]=(99,99,'Zyyy')
  self.assertEqual(self.scene.script_runs('a\u0301 العربية'),[(0,3,'Latn'),(3,10,'Arab')])
  self.assertEqual(self.scene.script_runs(''),[]);self.assertEqual(self.scene.snapshot(),before)
 def test_discovery_states_script_row_contract_without_mutation(self):
  before=self.scene.snapshot();info=self.scene.info();contract=info['contract']
  self.assertIn('script-itemization',contract['features'])
  query=contract['queryContracts']['nrScriptRuns']
  self.assertEqual(query['fields'],['start','end','iso15924TagBigEndian'])
  self.assertEqual((query['capacityUnit'],query['rowWords'],query['alignmentBytes']),('row',3,4))
  self.assertEqual(query['profile'],'nr-script-grapheme-v1');self.assertTrue(query['pure']);self.assertTrue(query['ownedBindings']);self.assertEqual(self.scene.snapshot(),before)
 def test_atomic_short_invalid_and_aliasing(self):
  source=(C.c_uint32*2)(ord('a'),ord('א'));out=(C.c_uint32*6)(*([777]*6));self.assertEqual(self.fn(source,2,out,1),-1);self.assertEqual(list(out),[777]*6)
  source[1]=0xd800;self.assertEqual(self.fn(source,2,out,2),-1);self.assertEqual(list(out),[777]*6)
  alias=(C.c_uint32*6)(ord('a'),ord('א'),0,0,0,0);self.assertEqual(self.fn(alias,2,alias,2),2);self.assertEqual(list(alias),[0,1,int.from_bytes(b'Latn','big'),1,2,int.from_bytes(b'Hebr','big')])
