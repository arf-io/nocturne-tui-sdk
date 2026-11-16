from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hosts/python'))
from nocturne_native import NativeScene
from unicode_document_view import UnicodeDocumentView
class UnicodeDocumentViewTest(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close);self.view=UnicodeDocumentView()
 def testPainterEmitsWholeClustersAtNativeVisualPositions(self):
  self.s.command(dict(op='draft',text='א́👩‍🔧ב',emitWeather=False));before=self.s.snapshot();paint=self.view.paint(self.s,20,8)
  self.assertIn('א́',paint);self.assertIn('👩‍🔧',paint);self.assertIn('ב',paint);self.assertEqual(self.s.snapshot(),before)
 def testPointerUsesNativeVisualSourceMapping(self):
  self.s.command(dict(op='draft',text='אב',caret=0,emitWeather=False));self.view.paint(self.s,8,8)
  self.view.pointer(self.s,'down',0,1,False);self.view.pointer(self.s,'up',0,1,False);self.assertEqual(self.s.info()['prompt']['caret'],2)
 def testTinyViewportAndInteriorCaretShiftNavigation(self):
  self.s.command(dict(op='draft',text='éZ',caret=1,emitWeather=False));paint=self.view.paint(self.s,1,1);self.assertNotIn('é',paint)
  self.view.paint(self.s,8,8);self.assertTrue(self.view.move(self.s,'ArrowRight',True));self.assertEqual(self.s.info()['prompt']['anchor'],0)
 def testWheelPagingPersistsAndDoesNotMutateNativeState(self):
  self.s.command(dict(op='draft',text='\n'.join(str(i) for i in range(30)),caret=0,emitWeather=False));self.view.paint(self.s,20,5);before=self.s.snapshot()
  self.assertTrue(self.view.scroll_by(self.s,3));self.view.paint(self.s,20,5);self.assertEqual(self.view.scroll,3);self.assertEqual(self.s.snapshot(),before)
  self.view.scroll_by(self.s,10000);self.assertEqual(self.view.scroll,self.view.max_scroll);self.view.scroll_by(self.s,-10000);self.assertEqual(self.view.scroll,0)
 def testVerticalNavigationRetainsPreferredColumnAcrossShortLine(self):
  self.s.command(dict(op='draft',text='ABCDE\nX\nABCDE',caret=4,emitWeather=False));self.view.paint(self.s,20,8)
  self.view.move(self.s,'ArrowDown');self.view.paint(self.s,20,8);self.assertEqual(self.s.info()['prompt']['caret'],7)
  self.view.move(self.s,'ArrowDown');self.assertEqual(self.s.info()['prompt']['caret'],12)
 def testSelectionAndModalOwnership(self):
  self.s.command(dict(op='draft',text='AאבB',emitWeather=False));self.s.command(dict(op='select',anchor=1,caret=3));paint=self.view.paint(self.s,8,8);self.assertIn('48;2;67;99;127',paint)
  self.s.command(dict(op='key',key='F1'));before=self.s.snapshot();self.assertIsNone(self.view.paint(self.s,8,8));self.assertFalse(self.view.pointer(self.s,'down',0,1,False));self.assertEqual(self.s.snapshot(),before)
 def testDragAnchorTracksRetainedClusterAcrossInsertedPrefix(self):
  self.s.command(dict(op='draft',text='ABC',emitWeather=False));self.view.paint(self.s,20,8);self.view.pointer(self.s,'down',1,1,False)
  self.s.command(dict(op='draft',text='XABC',emitWeather=False));self.view.pointer(self.s,'move',4,1,False)
  self.assertEqual(self.s.info()['prompt']['anchor'],2);self.assertEqual(self.s.selected_text(),'BC');self.view.pointer(self.s,'up',4,1,False);self.assertIsNone(self.view.drag)
 def testDragCancelsWhenAnchoringClusterIsRetired(self):
  self.s.command(dict(op='draft',text='ABC',emitWeather=False));self.view.paint(self.s,20,8);self.view.pointer(self.s,'down',1,1,False)
  self.s.command(dict(op='draft',text='AXC',emitWeather=False));before=self.s.snapshot();self.view.pointer(self.s,'move',3,1,False)
  self.assertIsNone(self.view.drag);self.assertEqual(self.s.snapshot(),before)
 def testDragReleaseOutsideDocumentCancels(self):
  self.s.command(dict(op='draft',text='ABC',emitWeather=False));self.view.paint(self.s,20,8);self.view.pointer(self.s,'down',1,1,False)
  self.view.pointer(self.s,'up',1,0,False);self.assertIsNone(self.view.drag)
  before=self.s.snapshot();self.view.pointer(self.s,'move',3,1,False);self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
