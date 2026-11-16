"""Weak resolution must use isolating sequences, not adjacent source text."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiWeak(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrBidiWeak;self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def rows(self,text,base=0):
  data=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*7))();self.assertEqual(self.fn(data,len(text),base,out,len(text)),len(text));return [list(out[i*7:i*7+7]) for i in range(len(text))]
 def types(self,text,expected,base=0):self.assertEqual([r[1] for r in self.rows(text,base)],expected)
 def testMarksAndArabicEuropeanNumbers(self):
  self.types('ا́1',[1,1,4]);self.types('א́1',[1,1,3]);self.types('Á1',[0,0,0]);self.types('́',[1],1)
 def testSeparatorsTerminatorsAndStrongContext(self):
  self.types('א1+2',[1,3,3,3]);self.types('ا١,٢',[1,4,4,4]);self.types('א$12$$',[1,3,3,3,3,3]);self.types('ا1$',[1,4,13]);self.types('A+1',[0,13,0])
 def testIsolateContentsCannotSupplyOuterNumberContext(self):
  rows=self.rows('ا\u2066A\u20691');self.assertEqual(rows[-1][1],4);self.assertEqual([r[4] for r in rows],[0,0,2,0,0]);self.assertEqual(rows[2][5:],[0,0])
  rows=self.rows('A\u2067ا\u20691');self.assertEqual(rows[-1][1],0);self.assertEqual(rows[2][1],1)
 def testNsmAfterIsolateFormattingBecomesNeutral(self):
  self.types('\u2066A\u2069́',[19,0,22,13]);self.types('\u2069́',[22,13])
 def testRemovedControlsDoNotBreakWeakAdjacency(self):
  rows=self.rows('ا\u00ad1');self.assertEqual(rows[-1][1],4);self.assertEqual(rows[1][3:5],[1,0xffffffff])
 def testParagraphAndEmbeddingBoundariesSetSequenceContext(self):
  self.types('ا1\nA1',[1,4,10,0,0]);rows=self.rows('A\u202b1\u202cB');self.assertEqual(rows[2][1],3);self.assertEqual(rows[2][5:],[1,1])
 def testInvalidInputAndShortOutputAreAtomic(self):
  data=(C.c_uint32*2)(65,0xd800);out=(C.c_uint32*14)(*([99]*14));self.assertEqual(self.fn(data,2,0,out,2),-1);self.assertEqual(list(out),[99]*14)
  data[1]=66;self.assertEqual(self.fn(data,2,0,out,1),-1);self.assertEqual(list(out),[99]*14);self.assertEqual(self.fn(data,2,0,None,0),2)
if __name__=='__main__':unittest.main()
