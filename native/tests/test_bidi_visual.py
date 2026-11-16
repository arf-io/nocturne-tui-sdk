import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiVisual(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrBidiVisual;self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def rows(self,text,base=0):
  values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*4))();n=self.fn(values,len(text),base,out,len(text));self.assertGreaterEqual(n,0);return [list(out[i*4:i*4+4]) for i in range(n)]
 def testRtlNumbersKeepInternalDigitOrder(self):
  self.assertEqual([r[0] for r in self.rows('א12ב')],[3,1,2,0]);self.assertEqual([r[2] for r in self.rows('א12ב')],[1,2,2,1])
 def testOddBracketsMirrorWithoutChangingSource(self):
  self.assertEqual([r[3] for r in self.rows('(א)',1)],[ord('('),ord('א'),ord(')')])
 def testTrailingWhitespaceAndRemovedControls(self):
  rows=self.rows('A\u202bא \u202c');self.assertEqual([r[0] for r in rows],[0,2,3]);self.assertEqual(rows[-1][2],0)
 def testInvalidAndShortOutputAreAtomic(self):
  data=(C.c_uint32*2)(65,0xd800);out=(C.c_uint32*8)(*([99]*8));self.assertEqual(self.fn(data,2,0,out,2),-1);self.assertEqual(list(out),[99]*8)
  data[1]=66;self.assertEqual(self.fn(data,2,0,out,1),-1);self.assertEqual(list(out),[99]*8)
if __name__=='__main__':unittest.main()
