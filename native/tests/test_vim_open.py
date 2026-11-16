from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimOpen(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def draft(self,text,caret):
  self.s.command(dict(op='prompt',mode='vim-inline'));self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));self.s.command(dict(op='key',key='Escape'))
 def testOpenAndUndoRestoreOriginalCaret(self):
  for key,text,caret,expected,pos in [('o','ab\ncd',1,'ab\n\ncd',3),('O','ab\ncd',4,'ab\n\ncd',3),('o','ab',0,'ab\n',3),('O','ab',1,'\nab',0),('o','',0,'\n',1),('O','',0,'\n',0)]:
   self.draft(text,caret);before=self.s.info();self.s.command(dict(op='key',key=key));after=self.s.info()
   self.assertEqual(after['prompt']['text'],expected);self.assertEqual(after['prompt']['caret'],pos)
   self.assertEqual(after['prompt']['revision'],before['prompt']['revision']+1)
   self.assertEqual(after['fieldCount'],before['fieldCount']);self.assertEqual(after['clock'],before['clock'])
   self.s.command(dict(op='key',key='Escape'));self.s.command(dict(op='key',key='u'))
   self.assertEqual(self.s.info()['prompt']['text'],text);self.assertEqual(self.s.info()['prompt']['caret'],caret)
 def testOpenEntersInsert(self):
  for key,expected in [('o','ab\nQ\ncd'),('O','Q\nab\ncd')]:
   self.draft('ab\ncd',1);self.s.command(dict(op='key',key=key));self.s.command(dict(op='key',key='Q'));self.assertEqual(self.s.info()['prompt']['text'],expected)
 def testCapacityFailureIsAtomic(self):
  self.s.command(dict(op='prompt',presentation='framed',maxChars=2048))
  for key in ['o','O']:
   self.draft('a'*2048,100);before=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command(dict(op='key',key=key))
   self.assertEqual(self.s.snapshot(),before)
   self.s.command(dict(op='prompt',presentation='framed',maxChars=0));self.s.command(dict(op='key',key=key))
   self.assertEqual(len(self.s.info()['prompt']['text']),2049)
   self.s.command(dict(op='key',key='Escape'));self.s.command(dict(op='key',key='u'))
   self.assertEqual(self.s.info()['prompt']['text'],'a'*2048)
   self.s.command(dict(op='prompt',presentation='framed',maxChars=2048))
if __name__=='__main__':unittest.main()
