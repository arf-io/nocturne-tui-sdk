from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class PasteOwnership(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def paste(self,text):self.s.command(dict(op='paste',text=text))
 def testPasteIsOneEditAndUndoRestoresOriginalCaret(self):
  self.s.command(dict(op='draft',text='AB',caret=1,emitWeather=False));before=self.s.info();self.paste('é\n日本');after=self.s.info()
  self.assertEqual(after['prompt']['text'],'Aé\n日本B');self.assertEqual(after['prompt']['caret'],6)
  self.assertEqual(after['prompt']['revision'],before['prompt']['revision']+1);self.assertEqual(after['fieldCount'],before['fieldCount']+4)
  self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.info()['prompt']['text'],'AB');self.assertEqual(self.s.info()['prompt']['caret'],1)
 def testEmptyAndBlockedPastesArePure(self):
  self.s.command(dict(op='draft',text='accepted',emitWeather=False))
  before=self.s.snapshot();self.paste('');self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='key',key='F1'));self.assertEqual(self.s.info()['inputOwner'],'modal');before=self.s.snapshot();self.paste('X');self.assertEqual(self.s.snapshot(),before)
 def testReaderTargetRatherThanVisibilityOwnsPaste(self):
  self.s.command(dict(op='draft',text='accepted',emitWeather=False))
  self.s.command(dict(op='window',id=1,text='reader'));self.s.command(dict(op='window-action',id=1,action='read'))
  self.assertEqual(self.s.info()['inputOwner'],'reader');before=self.s.snapshot();self.paste('X');self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='window-action',id=1,action='close',durationMs=1000))
  self.assertEqual(self.s.info()['inputOwner'],'prompt');self.assertGreater(self.s.info()['windows'][0]['visible'],0)
  self.paste('X');self.assertEqual(self.s.info()['prompt']['text'],'acceptedX')
 def testVimNormalBlocksPasteButInsertAcceptsIt(self):
  self.s.command(dict(op='prompt',mode='vim-full'));self.s.command(dict(op='key',key='Escape'));before=self.s.snapshot();self.paste('X');self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='key',key='i'));self.paste('X');self.assertEqual(self.s.info()['prompt']['text'],'X')
 def testDefaultPasteCrossesFormerLimitsAndInvalidInputIsAtomic(self):
  text='a'*65536;self.s.command(dict(op='draft',text=text,emitWeather=False));self.paste('é🚀')
  self.assertEqual(self.s.text_run_source(0,0),text+'é🚀');self.assertEqual(self.s.info()['prompt']['caret'],65539)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.command_raw(b'{"op":"paste","text":"\xff"}')
  self.assertEqual(self.s.snapshot(),before);self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.text_run_source(0,0),text)
 def testInvalidOrOverCapacityPasteCannotChangeState(self):
  self.s.command(dict(op='prompt',presentation='framed',maxChars=2048))
  self.s.command(dict(op='draft',text='a'*2048,emitWeather=False))
  for text in ['X','\r','x'*2049]:
   before=self.s.snapshot()
   with self.assertRaises(ValueError):self.paste(text)
   self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
