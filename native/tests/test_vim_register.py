from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimRegister(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='prompt',mode='vim-inline'))
 def draft(self,text,caret=0):self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));self.keys('Escape')
 def keys(self,*keys,unit='scalar'):
  for k in keys:self.s.command(dict(op='key',key=k,unit=unit))
 def testYankWordDoesNotEditAndCountedPutHasOneUndo(self):
  self.draft('one two');before=self.s.info()['prompt'];self.keys('y','w');self.assertEqual(self.s.info()['prompt'],before)
  self.keys('2','P');self.assertEqual(self.s.info()['prompt']['text'],'one one one two');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'one two')
 def testDeletedWordCanBePutBefore(self):
  self.draft('one two');self.keys('d','w','P');self.assertEqual(self.s.info()['prompt']['text'],'one two')
 def testLinewiseYankAndPutBelowUnterminatedLine(self):
  self.draft('aa\nbb');self.keys('y','y','p');self.assertEqual(self.s.info()['prompt']['text'],'aa\naa\nbb')
  self.draft('aa\nbb',3);self.keys('y','y','p');self.assertEqual(self.s.info()['prompt']['text'],'aa\nbb\nbb')
 def testGraphemeAndSnapshotReplay(self):
  self.draft('é Z');self.keys('y','l',unit='grapheme');saved=self.s.snapshot();self.keys('p',unit='grapheme');expected=self.s.snapshot();self.assertEqual(self.s.info()['prompt']['text'],'éé Z');self.s.restore(saved);self.keys('p',unit='grapheme');self.assertEqual(expected,self.s.snapshot())
 def testCapacityRejectsWithoutLosingRegister(self):
  self.s.command(dict(op='prompt',presentation='framed',maxChars=2048))
  self.draft('abc');self.keys('y','w');self.draft('Z'*2048);before=self.s.snapshot()
  with self.assertRaises(ValueError):self.keys('P')
  self.assertEqual(before,self.s.snapshot());self.draft('Z');self.keys('P');self.assertEqual(self.s.info()['prompt']['text'],'abcZ')

 def testDeletedLastLineRegisterRetainsItsSource(self):
  self.draft('aa\nbb',3);self.keys('d','d');self.assertEqual(self.s.info()['vimRegister'],{'text':'bb','linewise':True});self.keys('p');self.assertEqual(self.s.info()['prompt']['text'],'aa\nbb')
 def testSchema14PreservesPendingDeleteWithEmptyRegister(self):
  import struct,zlib
  self.draft('one two');self.keys('d');data=bytearray(self.s.snapshot());payload=data[24:24+4848384];struct.pack_into('<I',payload,4,0x20261014);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261014,len(payload),zlib.crc32(payload));self.s.restore(data);self.keys('w');self.assertEqual(self.s.info()['vimRegister']['text'],'one ')
 def testCorruptRegisterRestoreIsAtomic(self):
  import struct,zlib
  from prompt_wire_layout import prompt_wire
  self.draft('abc');self.keys('y','w');before=self.s.snapshot();q,wire,lengths=prompt_wire(before,self.s)
  self.assertEqual(struct.unpack_from('<i',before,wire+q['registers'])[0],3);self.assertEqual(lengths[101],3)
  scalar=wire+q['wireBytes']+4*sum(lengths[:101]);self.assertEqual(struct.unpack_from('<III',before,scalar),(97,98,99))
  for offset,fmt,value in [(wire+q['registers'],'<i',4),(wire+q['registers']+4,'<i',2),(scalar,'<I',0x110000)]:
   with self.subTest(offset=offset,value=value):
    bad=bytearray(before);struct.pack_into(fmt,bad,offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
    with self.assertRaises(ValueError):self.s.restore(bad)
    self.assertEqual(before,self.s.snapshot())
  self.keys('P');self.assertEqual(self.s.info()['prompt']['text'],'abcabc');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'abc')
