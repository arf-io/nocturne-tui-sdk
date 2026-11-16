from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VimWords(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def motion(self,text,caret,key,expected,unit='scalar'):
  for mode in ['vim-inline','vim-full']:
   self.s.command(dict(op='prompt',mode=mode));self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));self.s.command(dict(op='key',key='Escape'))
   before=self.s.info();self.s.command(dict(op='key',key=key,unit=unit));after=self.s.info()
   self.assertEqual(after['prompt']['caret'],expected,(text,caret,key,unit));self.assertEqual(after['prompt']['text'],text)
   self.assertEqual(after['prompt']['revision'],before['prompt']['revision']);self.assertEqual(after['clock'],before['clock'])
 def testPunctuationBelongsToSameWord(self):
  for caret,key,result in [(0,'W',6),(2,'B',0),(4,'E',8),(6,'E',8),(8,'B',6)]:self.motion('ab.cd 日本語',caret,key,result)
 def testSmallWordsSeparatePunctuationAndIdentifiers(self):
  for caret,key,result in [(0,'w',2),(2,'w',3),(3,'w',6),(4,'b',3),(3,'b',2),(2,'b',0),(0,'e',1),(1,'e',2),(2,'e',4)]:self.motion('ab.cd 日本語',caret,key,result)
  self.motion('a_b ++ c',0,'w',4);self.motion('a_b ++ c',4,'e',5)
 def testSmallWordWhitespaceAndGraphemeBoundaries(self):
  self.motion('ab\n\ncd',0,'w',3);self.motion('ab\n\ncd',3,'w',4);self.motion('ab\n\ncd',3,'b',0)
  self.motion('é.x',0,'w',2,'grapheme');self.motion('é.x',2,'b',0,'grapheme');self.motion('é.x',0,'e',2,'grapheme')
 def testEmptyLinesAreWordsExceptForEndMotion(self):
  for caret,key,result in [(0,'W',3),(3,'W',4),(4,'B',3),(3,'B',0),(0,'E',1),(1,'E',5)]:self.motion('ab\n\ncd',caret,key,result)
 def testGraphemeEndsAndInteriorCarets(self):
  self.motion('é x',0,'E',3,'grapheme');self.motion('éx y',0,'E',2,'grapheme');self.motion('éx y',1,'B',0,'grapheme');self.motion('x é',0,'E',2,'grapheme')
 def testDocumentEdgesAndWhitespace(self):
  for text,caret,key,result in [('',0,'W',0),('',0,'B',0),('',0,'E',0),('abc',2,'W',2),('abc',3,'B',0),(' \t\n',0,'E',3),('a\n',0,'W',2)]:self.motion(text,caret,key,result)
if __name__=='__main__':unittest.main()
