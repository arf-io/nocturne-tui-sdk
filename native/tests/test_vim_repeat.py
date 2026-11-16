from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimRepeat(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='prompt',mode='vim-inline'))
 def keys(self,*keys,unit='scalar'):
  for k in keys:self.s.command(dict(op='key',key=k,unit=unit))
 def draft(self,text):self.s.command(dict(op='draft',text=text,caret=0,emitWeather=False));self.keys('Escape')
 def testCountedDeletionRepeatAndUndo(self):
  self.draft('abcdefgh');self.keys('2','x','.');self.assertEqual(self.s.info()['prompt']['text'],'efgh');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'cdefgh');self.keys('3','.');self.assertEqual(self.s.info()['prompt']['text'],'fgh')
 def testExplicitOneOverridesRememberedCount(self):
  self.draft("abcdef");self.keys("2","x","1",".");self.assertEqual(self.s.info()["prompt"]["text"],"def")
 def testOperatorRepeatIgnoresYankAndMotion(self):
  self.draft('one two three four');self.keys('d','w','y','w','.');self.assertEqual(self.s.info()['prompt']['text'],'three four')
 def testGraphemeModeAndSnapshotReplay(self):
  self.draft('é🙂Z');self.keys('x',unit='grapheme');saved=self.s.snapshot();self.keys('.');expected=self.s.snapshot();self.assertEqual(self.s.info()['prompt']['text'],'Z');self.s.restore(saved);self.keys('.');self.assertEqual(expected,self.s.snapshot())
 def testNewUnsupportedEditDoesNotRepeatOlderDeletion(self):
  self.draft('abc');self.keys('x','i','Z','Escape');before=self.s.snapshot()
  with self.assertRaises(ValueError):self.keys('.')
  self.assertEqual(before,self.s.snapshot())
 def testRepeatedNamedAppendFailureIsAtomic(self):
  from prompt_wire_layout import layout
  capacity=layout()['inlineCapacity']
  self.draft('A'*(capacity-2));self.keys('"','a','y','w');self.draft('ZZZ');self.keys('"','A','x','.');before=self.s.snapshot()
  self.assertEqual(self.s.info()['namedRegisters']['a']['text'],'A'*(capacity-2)+'ZZ')
  command=b'{"op":"key","key":"."}';lib=self.s._lib;context=self.s._context
  self.assertLess(lib.nrCommand(context,command,len(command)),0)
  self.assertEqual(lib.nrError(context),b'Prompt storage required')
  self.assertGreater(lib.nrPromptMemorySize(context),lib.nrPromptMemoryCapacity(context))
  self.assertEqual(before,self.s.snapshot())
  self.keys('.');self.assertEqual(self.s.info()['namedRegisters']['a']['text'],'A'*(capacity-2)+'ZZZ')
  self.assertEqual(self.s.info()['prompt']['text'],'');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'Z')
  self.assertEqual(self.s.info()['namedRegisters']['a']['text'],'A'*(capacity-2)+'ZZZ')
 def testRepeatedNamedAppendGrowsBeyondFormerLimit(self):
  self.draft('A'*2046);self.keys('"','a','y','w');self.draft('ZZZ');self.keys('"','A','x','.','.')
  self.assertEqual(self.s.info()['namedRegisters']['a']['text'],'A'*2046+'ZZZ')
  self.assertEqual(self.s.info()['prompt']['text'],'');self.keys('u');self.assertEqual(self.s.info()['prompt']['text'],'Z')
