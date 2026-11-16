from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class EditorRedo(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='prompt',mode='vim-inline'));self.s.command(dict(op='draft',text='abcdef',caret=0,emitWeather=False));self.key('Escape')
 def key(self,k,**modifiers):self.s.command(dict(op='key',key=k,**modifiers))
 def testUndoRedoAndRegisterRetention(self):
  self.key('x');self.key('x');register=self.s.info()['vimRegister'];self.key('2');self.key('u');self.assertEqual(self.s.info()['prompt']['text'],'abcdef');self.key('r',ctrl=True);self.assertEqual(self.s.info()['prompt']['text'],'bcdef');self.key('r',ctrl=True);self.assertEqual(self.s.info()['prompt']['text'],'cdef');self.assertEqual(self.s.info()['vimRegister'],register)
 def testNewEditInvalidatesRedoBranch(self):
  self.key('x');self.key('u');self.key('l');self.key('x');before=self.s.snapshot();self.key('r',ctrl=True);self.assertEqual(before,self.s.snapshot())
 def testRedoSnapshotAndRenderPurity(self):
  self.key('x');self.key('u');saved=self.s.snapshot();self.s.render();self.assertEqual(saved,self.s.snapshot());self.key('r',ctrl=True);expected=self.s.snapshot();self.s.restore(saved);self.key('r',ctrl=True);self.assertEqual(expected,self.s.snapshot())
 def testConventionalRedoShortcutAndRepeatedHistoryTravel(self):
  self.key('x');self.key('z',ctrl=True);self.key('z',ctrl=True,shift=True);self.assertEqual(self.s.info()['prompt']['text'],'bcdef')
  for _ in range(20):self.key('u');self.key('r',ctrl=True)
  self.assertEqual(self.s.info()['prompt']['text'],'bcdef')

 def testCountedRedoAndRingCapacity(self):
  self.s.command(dict(op='reset'));self.s.command(dict(op='prompt',mode='vim-inline'));self.s.command(dict(op='draft',text='a'*120,caret=0,emitWeather=False));self.key('Escape')
  for _ in range(110):self.key('x')
  self.key('9');self.key('9');self.key('u');self.assertEqual(len(self.s.info()['prompt']['text']),109);self.assertEqual(self.s.info()['prompt']['redoAvailable'],99)
  self.key('u');self.assertEqual(len(self.s.info()['prompt']['text']),110);self.assertEqual(self.s.info()['prompt']['redoAvailable'],100)
  self.key('u');self.assertEqual(len(self.s.info()['prompt']['text']),110);self.assertEqual(self.s.info()['prompt']['redoAvailable'],100)
  self.key('9');self.key('9');self.key('r',ctrl=True);self.assertEqual(len(self.s.info()['prompt']['text']),11)
  self.key('r',ctrl=True);self.assertEqual(len(self.s.info()['prompt']['text']),10);self.assertEqual(self.s.info()['prompt'].get('redoAvailable',0),0)
 def testSchema16PromotesWithoutRedoAndStillSupportsUndo(self):
  import struct,zlib
  self.key('x');data=bytearray(self.s.snapshot());payload=data[24:24+5069808];struct.pack_into('<I',payload,4,0x20261016);data=data[:24]+payload;struct.pack_into('<III',data,12,0x20261016,len(payload),zlib.crc32(payload));self.s.restore(data);before=self.s.snapshot();self.key('r',ctrl=True);self.assertEqual(before,self.s.snapshot());self.key('u');self.key('r',ctrl=True);self.assertEqual(self.s.info()['prompt']['text'],'bcdef')
 def testCorruptRedoCountRejectsAtomically(self):
  import struct,zlib
  self.key('x');self.key('u');before=self.s.snapshot();bad=bytearray(before);struct.pack_into('<i',bad,24+5069808,17);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
  with self.assertRaises(ValueError):self.s.restore(bad)
  self.assertEqual(before,self.s.snapshot())
