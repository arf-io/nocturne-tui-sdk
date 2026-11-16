from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class NamedRegisters(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='prompt',mode='vim-inline'))
 def keys(self,*keys):
  for k in keys:self.s.command(dict(op='key',key=k))
 def draft(self,text):self.s.command(dict(op='draft',text=text,caret=0,emitWeather=False));self.keys('Escape')
 def testIndependentNamedCopiesAndOneShotSelection(self):
  self.draft('alpha');self.keys('"','a','y','w');self.draft('beta');self.keys('"','b','y','w');self.draft('Z');self.keys('"','a','P');self.assertEqual(self.s.info()['prompt']['text'],'alphaZ');self.draft('Z');self.keys('P');self.assertEqual(self.s.info()['prompt']['text'],'betaZ')
 def testUppercaseAppendsWithoutReplacing(self):
  self.draft('one ');self.keys('"','a','y','w');self.draft('two');self.keys('"','A','y','w');self.draft('Z');self.keys('"','a','P');self.assertEqual(self.s.info()['prompt']['text'],'one twoZ')
 def testBlackHoleDeleteKeepsRegisters(self):
  self.draft('keep');self.keys('y','w');self.draft('remove');self.keys('"','_','d','w');self.assertEqual(self.s.info()['prompt']['text'],'');self.keys('P');self.assertEqual(self.s.info()['prompt']['text'],'keep')
 def testPendingSelectorAndNamedContentsReplay(self):
  self.draft('abc');self.keys('"','a','y','w');self.draft('Z');self.keys('"');saved=self.s.snapshot();self.keys('a','P');expected=self.s.snapshot();self.s.restore(saved);self.keys('a','P');self.assertEqual(expected,self.s.snapshot())
 def testAppendGrowsAndInvalidSelectorIsAtomic(self):
  self.draft('A'*2048);self.keys('"','a','y','w');self.draft('Z');self.keys('"','A','y');before=self.s.snapshot()
  self.keys('w');self.assertEqual(self.s.info()['namedRegisters']['a']['text'],'A'*2048+'Z')
  self.keys('Escape','"');before=self.s.snapshot()
  with self.assertRaises(ValueError):self.keys('!')
  self.assertEqual(before,self.s.snapshot())

 def testLinewiseAppendAndEscapeCancellation(self):
  self.draft('one');self.keys('"','a','y','y');self.draft('two');self.keys('"','A','y','y');self.assertEqual(self.s.info()['namedRegisters']['a'],{'text':'one\ntwo','linewise':True})
  self.draft('Z');self.keys('"','a','Escape','P');self.assertEqual(self.s.info()['prompt']['text'],'one\ntwo\nZ')
 def testPreviousSchemaRetainsUnnamedAndPendingYank(self):
  import struct,zlib
  self.draft('abc');self.keys('y','w');self.draft('Z');self.keys('y');data=bytearray(self.s.snapshot());payload=data[24:24+4856584];struct.pack_into('<I',payload,4,0x20261015);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261015,len(payload),zlib.crc32(payload));self.s.restore(data);self.keys('Escape','P');self.assertEqual(self.s.info()['prompt']['text'],'abcZ')
