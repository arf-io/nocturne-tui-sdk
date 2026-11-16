"""Native normal-mode edits preserve lines, undo and accepted-input ownership."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimEdits(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
  self.s.command(dict(op='prompt',mode='vim-inline'))
 def draft(self,text,caret):
  self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False))
  self.s.command(dict(op='key',key='Escape'))
 def key(self,key,unit='scalar'):self.s.command(dict(op='key',key=key,unit=unit))
 def testEditsAndUndo(self):
  for key,expected in [('x','ab\nef'),('X','ab\nef'),('D','ab\n'),('C','ab\n'),('s','ab\nef')]:
   self.draft('ab\ndef',3 if key!='X' else 4)
   before=self.s.info();self.key(key);after=self.s.info()
   self.assertEqual(after['prompt']['text'],expected)
   self.assertEqual(after['prompt']['revision'],before['prompt']['revision']+1)
   self.assertEqual(after['clock'],before['clock']);self.assertEqual(after['fieldCount'],before['fieldCount'])
   self.key('Escape');self.key('u');self.assertEqual(self.s.info()['prompt']['text'],'ab\ndef')
 def testLineBoundariesAreNotJoined(self):
  for key,caret in [('x',2),('X',3),('D',2),('X',0)]:
   self.draft('ab\ncd',caret);before=self.s.info()['prompt'];self.key(key,'grapheme')
   self.assertEqual(self.s.info()['prompt'],before)
 def testGraphemeInteriorDeletesWholeCluster(self):
  for key,caret in [('x',1),('s',1),('X',2)]:
   self.draft('éZ',caret);self.key(key,'grapheme')
   self.assertEqual(self.s.info()['prompt']['text'],'Z')
 def testChangeCommandsEnterInsertEvenOnEmptyLine(self):
  for key in ['C','s']:
   self.draft('\n',0);self.key(key);self.key('Q')
   self.assertEqual(self.s.info()['prompt']['text'],'Q\n')
if __name__=='__main__':unittest.main()
