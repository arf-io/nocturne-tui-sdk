"""Independent source-boundary expectations for logical Unicode pointer mapping."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class GraphemeHit(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrGraphemeHit
  self.fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*5;self.fn.restype=C.c_int
 def hit(self,text,columns,x,y,policy=1):
  data=(C.c_uint32*max(1,len(text)))(*map(ord,text));return self.fn(data,len(text),policy,columns,x,y)
 def testCombiningAndEmojiOnlyReturnWholeClusterBoundaries(self):
  self.assertEqual([self.hit('é中',8,x,0) for x in range(4)],[0,2,3,3])
  self.assertEqual([self.hit('👩‍🔧A',8,x,0) for x in range(4)],[0,3,3,4])
 def testWrappedRowsAndNewlineEnds(self):
  self.assertEqual(self.hit('Aé中Z',3,0,1),3);self.assertEqual(self.hit('Aé中Z',3,3,1),5)
  self.assertEqual(self.hit('A\r\n',8,0,1),3);self.assertEqual(self.hit('A\nB',8,0,1),2)
 def testEmptyInvalidAndExtremeCoordinates(self):
  self.assertEqual(self.hit('',1,0,0),0);self.assertEqual(self.hit('A',0,0,0),-1);self.assertEqual(self.hit('A',1,0,0,0),-1)
  self.assertEqual(self.hit('\ud800',1,0,0),-1);self.assertEqual(self.hit('A'*2049,1,0,0),-1);self.assertEqual(self.hit('A',1,2**32-1,2**32-1),1)
 def testOwnedPythonBoundaryAndValidation(self):
  self.assertEqual(self.s.grapheme_hit('é中',8,1,0),2)
  for args in [('A',0,0,0),('A',True,0,0),('A',1,-1,0),('A',1,0,2**32),('\ud800',1,0,0)]:
   with self.assertRaises((ValueError,TypeError)):self.s.grapheme_hit(*args)
 def testMappingDoesNotMutateScene(self):
  before=self.s.snapshot();self.hit('é中\n👩‍🔧',2,1,1);self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
