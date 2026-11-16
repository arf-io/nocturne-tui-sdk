"""Native cluster layout: independent expected positions, never scalar wrapping."""
import ctypes as C
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TextLayout(unittest.TestCase):
    def setUp(self):
        self.s=NativeScene();self.addCleanup(self.s.close)
        self.fn=self.s._lib.nrGraphemeLayout
        self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32]
        self.fn.restype=C.c_int
    def layout(self,text,columns,ambiguous=1):
        values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*5))()
        n=self.fn(values,len(text),ambiguous,columns,out,len(text));self.assertGreaterEqual(n,0)
        return [list(out[i*5:i*5+5]) for i in range(n)]
    def testWideClustersWrapBeforeTheWholeCluster(self):
        self.assertEqual(self.layout('Aé中Z',3),[[0,1,0,0,1],[1,3,1,0,1],[3,4,0,1,2],[4,5,2,1,1]])
    def testEmojiNeverSplitsAndOneColumnLayoutReportsOverflow(self):
        self.assertEqual(self.layout('👩‍🔧A',1),[[0,3,0,0,2],[3,4,0,1,1]])
    def testLineBreaksAndTabsHaveExplicitLayoutSemantics(self):
        self.assertEqual(self.layout('A\tB\r\nC',8),[[0,1,0,0,1],[1,2,1,0,3],[2,3,4,0,1],[3,5,5,0,0],[5,6,0,1,1]])
        self.assertEqual(self.layout('abc\tZ',3)[-2:],[[3,4,0,1,3],[4,5,0,2,1]])
    def testZeroWidthAndAmbiguousPolicyAreRetained(self):
        self.assertEqual(self.layout('́ΩZ',2,2),[[0,1,0,0,0],[1,2,0,0,2],[2,3,0,1,1]])
    def testProbeEmptyCapacityAndAtomicErrors(self):
        self.assertEqual(self.fn(None,0,1,1,None,0),0)
        values=(C.c_uint32*2)(65,66);out=(C.c_uint32*10)(*([0xdeadbeef]*10))
        self.assertEqual(self.fn(values,2,1,1,None,0),2)
        for policy,columns,capacity in [(0,1,2),(1,0,2),(1,1,1)]:
            self.assertEqual(self.fn(values,2,policy,columns,out,capacity),-1)
            self.assertEqual(list(out),[0xdeadbeef]*10)
        values[0]=0xd800
        self.assertEqual(self.fn(values,2,1,1,out,2),-1)
        self.assertEqual(list(out),[0xdeadbeef]*10)
    def testLayoutIsPureAndSupportsAliasedInputOutput(self):
        before=self.s.snapshot();self.layout('Aé中',2);self.assertEqual(before,self.s.snapshot())
        values=(C.c_uint32*10)(65,66)
        self.assertEqual(self.fn(values,2,1,1,values,2),2)
        self.assertEqual(list(values),[0,1,0,0,1,1,2,0,1,1])
    def testOwnedBindingMaximumAndRejection(self):
        rows=self.s.grapheme_layout('A'*2048,1)
        self.assertEqual(rows[-1],[2047,2048,0,2047,1])
        rows[0][2]=99;self.assertEqual(self.s.grapheme_layout('A',1),[[0,1,0,0,1]])
        for text,columns,policy in [('A',0,1),('A',True,1),('A',1.5,1),('A',2**32,1),('A',1,0),('\ud800',1,1),('A'*2049,1,1)]:
            with self.assertRaises((ValueError,TypeError)):self.s.grapheme_layout(text,columns,policy)
if __name__=='__main__':unittest.main()
