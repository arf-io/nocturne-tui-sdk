"""Visual cluster units retain logical source and line-specific bidi resolution."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiClusters(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrBidiClusterLayout;self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def rows(self,text,columns=8,direction=2):
  values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*7))();n=self.fn(values,len(text),1,columns,direction,out,len(text));self.assertGreaterEqual(n,0);return [list(out[i*7:i*7+7]) for i in range(n)]
 def testCombiningClusterNeverReversesInternalSource(self):
  self.assertEqual(self.rows('א́ב'),[[2,3,0,0,1,1,ord('ב')],[0,2,1,0,1,1,ord('א')]])
 def testEmojiClustersAndMixedNumericRun(self):
  rows=self.rows('א👩‍🔧ב');self.assertEqual([(r[0],r[1]) for r in rows],[(4,5),(1,4),(0,1)]);self.assertEqual(rows[1][4],2)
  self.assertEqual([r[0] for r in self.rows('א12ב')],[3,1,2,0])
 def testReorderRunsPerWrappedLine(self):
  self.assertEqual([(r[0],r[2],r[3]) for r in self.rows('אבגד',2)],[(1,0,0),(0,1,0),(3,0,1),(2,1,1)])
 def testMirroringAndRemovedControlsKeepOffsets(self):
  rows=self.rows('(א)',8,1);self.assertEqual([r[6] for r in rows],[ord('('),ord('א'),ord(')')])
  rows=self.rows('A\u202bא\u202c',8,0);self.assertEqual([r[0] for r in rows],[0,2])
 def testProbeAndShortOrInvalidOutputRemainUntouched(self):
  values=(C.c_uint32*3)(0x5d0,0x301,0x5d1);out=(C.c_uint32*21)(*([99]*21));self.assertEqual(self.fn(values,3,1,8,2,None,0),2)
  self.assertEqual(self.fn(values,3,1,8,2,out,1),-1);self.assertEqual(list(out),[99]*21)
  self.assertEqual(self.fn(values,3,1,0,2,out,3),-1);self.assertEqual(list(out),[99]*21)
if __name__=='__main__':unittest.main()
