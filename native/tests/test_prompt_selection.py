from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class PromptSelection(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def select(self,a,b,unit='scalar'):self.s.command(dict(op='select',anchor=a,caret=b,unit=unit))
 def testReverseSelectionReplacesOnceAndUndoes(self):
  self.s.command(dict(op='draft',text='Aé日本Z',caret=1,emitWeather=False));self.select(5,1,'grapheme');revision=self.s.info()['prompt']['revision'];self.s.command(dict(op='paste',text='👩‍🔧'))
  p=self.s.info()['prompt'];self.assertEqual((p['text'],p['caret'],p['anchor']),('A👩‍🔧Z',4,-1));self.assertEqual(p['revision'],revision+1)
  self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.info()['prompt']['text'],'Aé日本Z')
 def testDeleteAndBackspaceDeleteSelectedRange(self):
  for key in ['Delete','Backspace']:
   self.s.command(dict(op='draft',text='ab\ncd',emitWeather=False));self.select(1,4);self.s.command(dict(op='key',key=key));self.assertEqual(self.s.info()['prompt']['text'],'ad')
 def testBoundaryRejectionAndFocusOwnership(self):
  self.s.command(dict(op='draft',text='éZ',emitWeather=False));before=self.s.snapshot()
  with self.assertRaises(Exception):self.select(1,3,'grapheme')
  self.assertEqual(self.s.snapshot(),before);self.s.command(dict(op='key',key='F1'));before=self.s.snapshot();self.select(0,3);self.assertEqual(self.s.snapshot(),before)
 def testShiftMovementExtendsAndPlainArrowCollapses(self):
  self.s.command(dict(op='draft',text='abcd',caret=1,emitWeather=False));self.s.command(dict(op='key',key='ArrowRight',shift=True));p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret']),(1,2))
  self.s.command(dict(op='key',key='ArrowLeft'));p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret']),(-1,1))
 def testSelectedCellsAreHighlightedWithoutRenderMutation(self):
  self.s.command(dict(op='draft',text='ABCD',caret=4,emitWeather=False));plain=self.s.render().bytes;self.select(1,3);before=self.s.snapshot();selected=self.s.render().bytes
  self.assertNotEqual(plain,selected);self.assertEqual(self.s.snapshot(),before)
 def testVimSelectionDeleteChangeAndUndo(self):
  for key in ['x','X','s','D','C']:
   self.s.command(dict(op='prompt',mode='vim-full'));self.s.command(dict(op='key',key='Escape'));self.s.command(dict(op='draft',text='Aé日本Z',caret=1,emitWeather=False));self.select(1,5,'grapheme');self.s.command(dict(op='key',key=key,unit='grapheme'))
   p=self.s.info()['prompt'];self.assertEqual((p['text'],p['anchor']),('AZ',-1),key)
   self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.info()['prompt']['text'],'Aé日本Z')
 def testEndpointShortcutsClearSelection(self):
  for key,caret in [('a',0),('e',4)]:
   self.s.command(dict(op='draft',text='ABCD',emitWeather=False));self.select(1,3);self.s.command(dict(op='key',key=key,ctrl=True));p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret']),(-1,caret))
 def testSelectAllAndUndoableReplacement(self):
  self.s.command(dict(op='draft',text='é日本',caret=2,emitWeather=False));before=self.s.info()['prompt']['revision'];self.s.command(dict(op='key',key='SelectAll'));p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret'],p['revision']),(0,4,before));self.s.command(dict(op='paste',text='X'));self.assertEqual(self.s.info()['prompt']['text'],'X');self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.info()['prompt']['text'],'é日本')
 def testEscapeCancelsRangeBeforeLeavingInsertMode(self):
  self.s.command(dict(op='prompt',mode='vim-full'));self.s.command(dict(op='key',key='i'));self.s.command(dict(op='draft',text='ABCD',caret=2,emitWeather=False));self.select(1,3);before=self.s.info()['prompt'];self.s.command(dict(op='key',key='Escape'));p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret'],p['vimMode']),(-1,3,'insert'));self.assertEqual(p['text'],before['text']);self.assertEqual(p['revision'],before['revision']);self.s.command(dict(op='key',key='Escape'));self.assertEqual(self.s.info()['prompt']['vimMode'],'normal')
 def testModalEscapePreservesUnderlyingSelection(self):
  self.s.command(dict(op='draft',text='ABCD',emitWeather=False));self.select(1,3);self.s.command(dict(op='key',key='F1'));self.s.command(dict(op='key',key='Escape'));self.assertEqual(self.s.info()['prompt']['anchor'],1);self.s.command(dict(op='key',key='Escape'));self.assertEqual(self.s.info()['prompt']['anchor'],-1)
 def testSelectionReplacementUsesFreedCapacity(self):
  self.s.command(dict(op='draft',text='A'*2048,emitWeather=False));self.select(0,2048);self.s.command(dict(op='paste',text='日本'));self.assertEqual(self.s.info()['prompt']['text'],'日本')
if __name__=='__main__':unittest.main()
