from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimOperators(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='prompt',mode='vim-inline'))
 def draft(self,text,caret=0):self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));self.keys('Escape')
 def keys(self,*keys,unit='scalar'):
  for key in keys:self.s.command(dict(op='key',key=key,unit=unit))
 def testDeleteWordAndMultipliedCountsWithSingleUndo(self):
  self.draft('one two three four five six seven');self.keys('2','d','3','w');self.assertEqual(self.s.info()['prompt']['text'],'seven');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'one two three four five six seven')
 def testChangeWordPreservesFollowingSpaceAndEntersInsert(self):
  self.draft('one two');self.keys('c','w');self.assertEqual(self.s.info()['prompt']['text'],' two');self.assertEqual(self.s.info()['prompt']['vimMode'],'insert');self.keys('Z');self.assertEqual(self.s.info()['prompt']['text'],'Z two')
 def testDoubledLineOperators(self):
  self.draft('aa\nbb\ncc');self.keys('2','d','d');self.assertEqual(self.s.info()['prompt']['text'],'cc');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'aa\nbb\ncc')
  self.draft('aa\nbb',3);self.keys('c','c');self.assertEqual(self.s.info()['prompt']['text'],'aa\n');self.assertEqual(self.s.info()['prompt']['vimMode'],'insert')
 def testGraphemeInclusiveEndAndBackwardMotion(self):
  self.draft('éx Z');self.keys('d','e',unit='grapheme');self.assertEqual(self.s.info()['prompt']['text'],' Z')
  self.draft('one two',4);self.keys('d','b');self.assertEqual(self.s.info()['prompt']['text'],'two')
 def testPendingOperatorSnapshotsAndEscape(self):
  self.draft('one two');self.keys('d');saved=self.s.snapshot();self.keys('w');expected=self.s.snapshot();self.s.restore(saved);self.keys('w');self.assertEqual(expected,self.s.snapshot());self.s.restore(saved);self.keys('Escape','w');self.assertEqual(self.s.info()['prompt']['text'],'one two')

 def testOneCharacterChangeAndEndOfDocumentDelete(self):
  self.draft('a b');self.keys('c','w');self.assertEqual(self.s.info()['prompt']['text'],' b')
  self.draft('abc');self.keys('d','w');self.assertEqual(self.s.info()['prompt']['text'],'')
 def testLastLineDeleteAndChange(self):
  self.draft('aa\nbb',3);self.keys('d','d');self.assertEqual(self.s.info()['prompt']['text'],'aa')
  self.draft('aa\nbb');self.keys('c','c');self.assertEqual(self.s.info()['prompt']['text'],'\nbb')
 def testInvalidMotionRetainsPendingTransaction(self):
  self.draft('one two');self.keys('d');before=self.s.snapshot()
  with self.assertRaises(ValueError):self.keys('z')
  self.assertEqual(before,self.s.snapshot());self.keys('w');self.assertEqual(self.s.info()['prompt']['text'],'two')

 def testSchema13RetainsOlderPendingCount(self):
  import struct,zlib
  self.draft('abcdef');self.keys('2');data=bytearray(self.s.snapshot());payload=data[24:24+4848368];struct.pack_into('<I',payload,4,0x20261013);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261013,len(payload),zlib.crc32(payload));self.s.restore(data);self.keys('l');self.assertEqual(self.s.info()['prompt']['caret'],2)
 def testVerticalDeleteIncludesOriginLineAndUsesOneUndo(self):
  self.draft('aa\nbb\ncc\ndd');self.keys('d','j');self.assertEqual(self.s.info()['prompt']['text'],'cc\ndd');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'aa\nbb\ncc\ndd')
  self.draft('aa\nbb\ncc',7);self.keys('d','k');self.assertEqual(self.s.info()['prompt']['text'],'aa')
 def testCountedVerticalYankAndChange(self):
  self.draft('aa\nbb\ncc\ndd');before=self.s.info()['prompt'];self.keys('y','2','j');self.assertEqual(self.s.info()['prompt'],before);self.assertEqual(self.s.info()['vimRegister'],{'text':'aa\nbb\ncc\n','linewise':True})
  self.keys('c','j');self.assertEqual(self.s.info()['prompt']['text'],'\ncc\ndd');self.assertEqual(self.s.info()['prompt']['vimMode'],'insert')
 def testVerticalOperatorsUseSourceLinesAcrossWrapping(self):
  text='x'*120+'\nbb\ncc'
  self.s.command(dict(op='resize',width=20,height=10));self.draft(text);self.keys('d','j');self.assertEqual(self.s.info()['prompt']['text'],'cc')

 def testVerticalBoundaryMotionDoesNotDeleteOrOverwriteRegister(self):
  self.draft('one two');self.keys('y','w');register=self.s.info()['vimRegister']
  for caret,motion in [(0,'k'),(3,'j')]:
   self.draft('aa\nbb',caret);before=self.s.info()['prompt'];self.keys('d',motion);self.assertEqual(self.s.info()['prompt'],before);self.assertEqual(self.s.info()['vimRegister'],register)
