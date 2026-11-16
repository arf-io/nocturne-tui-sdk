from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimCounts(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='prompt',mode='vim-inline'))
 def draft(self,text,caret=0):self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));self.key('Escape')
 def key(self,k,unit='scalar'):self.s.command(dict(op='key',key=k,unit=unit))
 def testCountedWordAndHorizontalMotion(self):
  self.draft('one two three four');before=self.s.info();self.key('2');self.key('w');self.assertEqual(self.s.info()['prompt']['caret'],8);self.key('3');self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],11);self.assertEqual(self.s.info()['prompt']['revision'],before['prompt']['revision'])
 def testCountedDeletionHasOneUndo(self):
  self.draft('abcdef');self.key('3');self.key('x');self.assertEqual(self.s.info()['prompt']['text'],'def');self.key('u');self.assertEqual(self.s.info()['prompt']['text'],'abcdef')
 def testGraphemeDeletionAndLineBoundaries(self):
  self.draft('é🙂\nZ');self.key('9');self.key('x','grapheme');self.assertEqual(self.s.info()['prompt']['text'],'\nZ');self.key('u');self.assertEqual(self.s.info()['prompt']['text'],'é🙂\nZ')
 def testCountSurvivesSnapshotButEscapeAndDraftCancel(self):
  self.draft('abcdef');self.key('2');checkpoint=self.s.snapshot();self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],2);self.s.restore(checkpoint);self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],2)
  self.key('3');self.key('Escape');self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],3)
  self.key('3');self.s.command(dict(op='draft',text='abcdef',caret=0,emitWeather=False));self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],1)
 def testZeroDistinguishesLineStartAndDecimalCount(self):
  self.draft('abcdefghijklmnop',12);self.key('0');self.assertEqual(self.s.info()['prompt']['caret'],0);self.key('1');self.key('0');self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],10)
 def testCountOverflowRejectsAtomically(self):
  self.draft('abc');self.key('9');self.key('9');self.key('9');self.key('9');before=self.s.snapshot()
  with self.assertRaises(ValueError):self.key('9')
  self.assertEqual(before,self.s.snapshot())

 def testBackwardCountedEditAndVerticalCount(self):
  self.draft('abc\ndefgh',8);self.key('9');self.key('X');self.assertEqual(self.s.info()['prompt']['text'],'abc\nh')
  self.draft('abc\ndef\nghi');self.key('2');self.key('j');self.assertEqual(self.s.info()['prompt']['caret'],8)
 def testSchema12PromotesWithNoPendingCount(self):
  import struct,zlib
  self.draft('abcdef');data=bytearray(self.s.snapshot());payload=data[24:24+4848352];struct.pack_into('<I',payload,4,0x20261012);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261012,len(payload),zlib.crc32(payload));self.s.restore(data);self.key('l');self.assertEqual(self.s.info()['prompt']['caret'],1)
 def testCountedUndoRestoresMultipleEditsAndKeepsRegister(self):
  self.draft('abcdef');self.key('x');self.key('x');self.key('x');register=self.s.info()['vimRegister'];self.key('2');self.key('u');self.assertEqual(self.s.info()['prompt']['text'],'bcdef');self.assertEqual(self.s.info()['vimRegister'],register);self.key('9');self.key('u');self.assertEqual(self.s.info()['prompt']['text'],'')
