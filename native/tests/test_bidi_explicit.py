"""UAX9 explicit-stage scope, overrides and depth overflow before implicit resolution."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiExplicit(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrBidiExplicit
  self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def rows(self,text,base=0):
  values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*4))();n=self.fn(values,len(text),base,out,len(text));self.assertEqual(n,len(text));return [list(out[i*4:i*4+4]) for i in range(n)]
 def testEmbeddingsAndOverridesRestoreOuterLevel(self):
  self.assertEqual(self.rows('A\u202bB\u202cC'),[[0,0,0,0],[16,16,0,1],[0,0,1,0],[18,18,1,1],[0,0,0,0]])
  rows=self.rows('\u202eA1\u202cB');self.assertEqual(rows[1:3],[[0,1,1,0],[3,1,1,0]]);self.assertEqual(rows[-1],[0,0,0,0])
  rows=self.rows('\u202dא\u202c',1);self.assertEqual(rows[1],[1,0,2,0])
 def testIsolatesDiscardNestedEmbeddingsAtPdi(self):
  rows=self.rows('A\u2067\u202aB\u2069C');self.assertEqual([r[2] for r in rows],[0,0,1,2,0,0]);self.assertEqual(rows[4][3],0)
  rows=self.rows('\u2067A\u202cB\u2069C');self.assertEqual(rows[1][2],1);self.assertEqual(rows[3][2],1);self.assertEqual(rows[-1][2],0)
 def testFirstStrongIsolateStopsAtOwnPdi(self):
  for text,level in [('\u2068א\u2069A',1),('\u2068A\u2069א',2),('\u2068\u2069א',0),('\u2068\u2067א\u2069A\u2069',2)]:
   rows=self.rows(text);self.assertEqual(rows[1][2],level)
 def testOverflowRecoveryAndParagraphReset(self):
  rows=self.rows('\u202b'*130+'A'+'\u202c'*130+'B');self.assertEqual(rows[130][2],125);self.assertEqual(rows[-1][2],0)
  rows=self.rows('\u2067'*130+'A'+'\u2069'*130+'B');self.assertEqual(rows[130][2],125);self.assertEqual(rows[-1][2],0)
  rows=self.rows('\u202eA\nB');self.assertEqual(rows[2],[10,10,0,0]);self.assertEqual(rows[3],[0,0,0,0])
  self.assertEqual(self.rows('א\nA',2)[-1][2],0)
 def testProbeAndAtomicInvalidOutput(self):
  values=(C.c_uint32*3)(65,0xd800,66);out=(C.c_uint32*12)(*([99]*12))
  self.assertEqual(self.fn(values,3,0,out,3),-1);self.assertEqual(list(out),[99]*12)
  values[1]=66;self.assertEqual(self.fn(values,3,0,None,0),3);self.assertEqual(self.fn(values,3,0,out,2),-1);self.assertEqual(list(out),[99]*12)
if __name__=='__main__':unittest.main()
