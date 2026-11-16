import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiCaret(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
  self.hit=self.s._lib.nrBidiClusterHit;self.hit.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*6;self.hit.restype=C.c_int
  self.caret=self.s._lib.nrBidiCaret;self.caret.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*6+[C.POINTER(C.c_uint32),C.c_uint32];self.caret.restype=C.c_int
 def values(self,text):return (C.c_uint32*max(1,len(text)))(*map(ord,text))
 def at(self,text,offset,affinity=1,columns=8,direction=2):
  out=(C.c_uint32*3)(99,99,99);status=self.caret(self.values(text),len(text),1,columns,direction,offset,affinity,out,3);self.assertEqual(status,0);return list(out)
 def testRtlEdgesAndCombiningSourceBoundaries(self):
  for text,expected in [('אב',[2,1,0]),('א́ב',[3,2,0])]:self.assertEqual([self.hit(self.values(text),len(text),1,8,2,x,0) for x in range(3)],expected)
 def testMixedBoundaryAffinityHasTwoVisualPositions(self):
  self.assertEqual(self.at('AאבB',1,0),[1,0,0]);self.assertEqual(self.at('AאבB',1,1),[3,0,1]);self.assertEqual(self.at('AאבB',3,0),[1,0,1]);self.assertEqual(self.at('AאבB',3,1),[3,0,0])
 def testWrapAndNewlineAffinity(self):
  self.assertEqual(self.at('אבגד',2,0,2),[0,0,1]);self.assertEqual(self.at('אבגד',2,1,2),[2,1,1]);self.assertEqual(self.at('A\n',2),[0,1,0])
 def testInvalidInteriorAndShortOutputDoNotWrite(self):
  text='א́ב';out=(C.c_uint32*3)(99,99,99)
  for offset,affinity,capacity in [(1,1,3),(4,1,3),(2,2,3),(2,1,2)]:self.assertEqual(self.caret(self.values(text),len(text),1,8,2,offset,affinity,out,capacity),-1);self.assertEqual(list(out),[99]*3)
 def testEmptyAndExtremeHitCoordinates(self):
  self.assertEqual(self.at('',0),[0,0,0]);self.assertEqual(self.hit(self.values('אב'),2,1,8,2,2**32-1,2**32-1),0)
if __name__=='__main__':unittest.main()
