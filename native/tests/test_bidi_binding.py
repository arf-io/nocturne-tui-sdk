from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiBinding(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def testOwnedOrderAndSourceIndices(self):
  before=self.s.snapshot();rows=self.s.bidi_visual('א12ב');self.assertEqual(rows,[[3,1,1,ord('ב')],[1,3,2,49],[2,3,2,50],[0,1,1,ord('א')]])
  rows[0][0]=99;self.assertEqual(self.s.bidi_visual('א12ב')[0][0],3);self.assertEqual(self.s.snapshot(),before)
 def testClusterLayoutKeepsCombiningSourceTogether(self):
  self.assertEqual(self.s.bidi_layout('א́ב',8),[[2,3,0,0,1,1,ord('ב')],[0,2,1,0,1,1,ord('א')]])
  with self.assertRaises(ValueError):self.s.bidi_layout('A',0)
 def testVisualHitAndCaretAffinity(self):
  self.assertEqual(self.s.bidi_hit('א́ב',8,0,0),3)
  self.assertEqual(self.s.bidi_caret('AאבB',8,1,0),[1,0,0]);self.assertEqual(self.s.bidi_caret('AאבB',8,1,1),[3,0,1])
  with self.assertRaises(ValueError):self.s.bidi_caret('א́ב',8,1)
 def testAutoAndRemovedControls(self):
  self.assertEqual([r[0] for r in self.s.bidi_visual('אA',2)],[1,0]);self.assertEqual([r[0] for r in self.s.bidi_visual('A\u202bא\u202c')],[0,2]);self.assertEqual(self.s.bidi_visual(''),[])
 def testRejectsMalformedUnicodeAndPolicy(self):
  for text,direction in [('A',True),('A',3),('\ud800',0),('A'*2049,0)]:
   with self.assertRaises((ValueError,TypeError)):self.s.bidi_visual(text,direction)
if __name__=='__main__':unittest.main()
