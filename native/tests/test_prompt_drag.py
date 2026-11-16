from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class PromptDrag(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.s.command(dict(op='draft',text='ABCDE',emitWeather=False))
 def position(self,char):
  frame=self.s.render()
  for i,c in enumerate(frame.words()):
   if c[0]==ord(char) and c[3]==0x40000000:return i%frame.width,i//frame.width
  self.fail('glyph not visible')
 def pointer(self,phase,char,**extra):
  x,y=self.position(char);self.s.command(dict(op='pointer',phase=phase,x=x,y=y,**extra))
 def testDragReleaseAndReplacement(self):
  before=self.s.info();self.pointer('down','B');self.pointer('move','D');self.pointer('up','D');p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret']),(1,3));self.assertEqual(p['revision'],before['prompt']['revision']);self.assertEqual(self.s.info()['camera'],before['camera'])
  self.s.command(dict(op='paste',text='X'));self.assertEqual(self.s.info()['prompt']['text'],'AXDE');self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.info()['prompt']['text'],'ABCDE')
 def testShiftClickExtendsAndClickCollapses(self):
  self.pointer('down','B');self.pointer('up','B');self.pointer('down','D',shift=True);self.pointer('up','D');self.assertEqual(self.s.info()['prompt']['anchor'],1)
  self.pointer('down','C');self.pointer('up','C');self.assertEqual(self.s.info()['prompt']['anchor'],-1)
 def testCancelEndsDrag(self):
  self.pointer('down','B');self.pointer('move','D');self.pointer('cancel','D');before=self.s.info()['prompt'];self.pointer('move','E');self.assertEqual(self.s.info()['prompt'],before)
if __name__=='__main__':unittest.main()
