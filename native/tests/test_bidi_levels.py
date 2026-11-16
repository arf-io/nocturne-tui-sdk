"""Bracket/neutral and implicit resolution retains canonical source indexing."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiLevels(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrBidiLevels;self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def rows(self,text,base=0):
  values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*7))();self.assertEqual(self.fn(values,len(text),base,out,len(text)),len(text));return [list(out[i*7:i*7+7]) for i in range(len(text))]
 def levels(self,text,expected,base=0):self.assertEqual([r[2] for r in self.rows(text,base)],expected,repr(text))
 def testBracketContextAndEmbeddingDirection(self):
  self.levels('A(א)B',[0,0,1,0,0]);self.levels('א(א)A',[1,1,1,1,0]);self.levels('(א)',[0,1,0]);self.levels('(א)',[1,1,1],1);self.levels('א(A)',[1,1,2,1],1)
 def testNeutralRunsAndNumbers(self):
  self.levels('א ! א',[1,1,1,1,1]);self.levels('A ! א',[0,0,0,0,1]);self.levels('א 12 א',[1,1,2,2,1,1]);self.levels('ا١,٢',[1,2,2,2])
 def testNsmAfterResolvedBracketFollowsItsDirection(self):
  rows=self.rows('א(א)́A');self.assertEqual([r[2] for r in rows],[1,1,1,1,1,0]);self.assertEqual(rows[4][1],1)
 def testCanonicalBracketPairsAndNestedPairs(self):
  self.levels('א〈א〉A',[1,1,1,1,0]);self.levels('א([א])A',[1,1,1,1,1,1,0])
 def testIsolateContentsRemainIndependentAndRemovedRowsRetained(self):
  rows=self.rows('A\u2067א(א)\u2069B');self.assertEqual([r[2] for r in rows],[0,0,1,1,1,1,0,0]);self.assertEqual(rows[2][4],2)
  rows=self.rows('A\u202eB\u202cC');self.assertEqual(rows[1][3],1);self.assertEqual(rows[2][2],1)
 def testInvalidAndShortBuffersLeaveOutputUntouched(self):
  data=(C.c_uint32*2)(65,0xd800);out=(C.c_uint32*14)(*([99]*14));self.assertEqual(self.fn(data,2,0,out,2),-1);self.assertEqual(list(out),[99]*14)
  data[1]=66;self.assertEqual(self.fn(data,2,0,out,1),-1);self.assertEqual(list(out),[99]*14)
if __name__=='__main__':unittest.main()
