from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimLines(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def draft(self,text,caret,mode):
  self.s.command(dict(op='prompt',mode=mode));self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));self.s.command(dict(op='key',key='Escape'))
 def testSourceLineMotions(self):
  for mode in ['vim-inline','vim-full']:
   for unit in ['scalar','grapheme']:
    for key,expected in [('0',3),('^',5),('$',8)]:
     self.draft('ab\n  éXY\nlast',7,mode);before=self.s.info();self.s.command(dict(op='key',key=key,unit=unit));after=self.s.info()
     self.assertEqual(after['prompt']['caret'],expected)
     self.assertEqual(after['prompt']['text'],before['prompt']['text']);self.assertEqual(after['prompt']['revision'],before['prompt']['revision']);self.assertEqual(after['clock'],before['clock'])
 def testLastClusterAndEmptyLines(self):
  for key,expected in [('$',0),('0',0),('^',0)]:
   self.draft('é\n',1,'vim-inline');self.s.command(dict(op='key',key=key,unit='grapheme'));self.assertEqual(self.s.info()['prompt']['caret'],expected)
  for key in ['0','^','$']:
   self.draft('ab\n\ncd',3,'vim-full');self.s.command(dict(op='key',key=key));self.assertEqual(self.s.info()['prompt']['caret'],3)
 def testLineInsertAndAppend(self):
  for key,expected in [('I','ab\n  QéXY\nlast'),('A','ab\n  éXYQ\nlast')]:
   self.draft('ab\n  éXY\nlast',7,'vim-inline');self.s.command(dict(op='key',key=key,unit='grapheme'));self.s.command(dict(op='key',key='Q'));self.assertEqual(self.s.info()['prompt']['text'],expected)
 def testTabIndentAndBlankLineAppend(self):
  for key,expected in [('I','x\n\t QZ'),('A','x\n\t ZQ')]:
   self.draft('x\n\t Z',4,'vim-full');self.s.command(dict(op='key',key=key));self.s.command(dict(op='key',key='Q'));self.assertEqual(self.s.info()['prompt']['text'],expected)
if __name__=='__main__':unittest.main()
