"""Native grapheme-cell width policy: authored examples and atomic ABI failures."""
import ctypes as C, subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TextWidth(unittest.TestCase):
    def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
    def rows(self,text,ambiguous=1):return self.s.grapheme_widths(text,ambiguous)
    def testCombiningCjkAndEmojiSequencesUseClusterWidths(self):
        self.assertEqual(self.rows('Ae\u0301中👩\u200d🔧🇺🇸Z'),[[0,1,1],[1,3,1],[3,4,2],[4,7,2],[7,9,2],[9,10,1]])
    def testExplicitAmbiguousWidthHasNoLocaleDependency(self):
        self.assertEqual(self.rows('Ω·Ａｱ',1),[[0,1,1],[1,2,1],[2,3,2],[3,4,1]])
        self.assertEqual(self.rows('Ω·Ａｱ',2),[[0,1,2],[1,2,2],[2,3,2],[3,4,1]])
    def testValidEmojiVariationOnlyAndKeycapPolicy(self):
        for text,width in [('❤',1),('❤\ufe0f',2),('❤\ufe0e',1),('A\ufe0f',1),('1\ufe0f\u20e3',2),('#\u20e3',2),('A\u20e3',1),('⌚\ufe0e',2)]:
            self.assertEqual(self.rows(text),[[0,len(text),width]],text)
    def testNonspacingAndControlsHaveNoIndependentColumns(self):
        self.assertEqual(self.rows('\u0301\u0302'),[[0,2,0]])
        self.assertEqual(self.rows('\r\n\t\u200b'),[[0,2,0],[2,3,0],[3,4,0]])
        self.assertEqual(self.rows('क\u093f'),[[0,2,1]])
        self.assertEqual(self.rows('각'),[[0,3,2]])
    def testEmptyMaximumAndOwnedPurity(self):
        before=self.s.snapshot();self.assertEqual(self.rows(''),[])
        rows=self.rows('A'*2048);self.assertEqual(rows,[[i,i+1,1] for i in range(2048)])
        rows[0][2]=99;self.assertEqual(self.rows('A'),[[0,1,1]])
        self.assertEqual(before,self.s.snapshot())
    def testBadPolicyUnicodeAndCapacityRejectWithoutSceneMutation(self):
        before=self.s.snapshot()
        for text,policy in [('A',0),('A',3),('A',True),('A',1.5),('\ud800',1),('A'*2049,1)]:
            with self.assertRaises((ValueError,TypeError)):self.rows(text,policy)
        self.assertEqual(before,self.s.snapshot())
    def testNativeProbeAndAtomicFailure(self):
        fn=self.s._lib.nrGraphemeWidths;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        text=(C.c_uint32*2)(65,66);out=(C.c_uint32*6)(*([0xdeadbeef]*6))
        self.assertEqual(fn(text,2,1,None,0),2)
        for pointer,count,policy,capacity in [(text,2,1,1),(text,2,0,2),(None,1,1,2),(text,2049,1,2)]:
            self.assertEqual(fn(pointer,count,policy,out,capacity),-1);self.assertEqual(list(out),[0xdeadbeef]*6)
        text[0]=0xd800;self.assertEqual(fn(text,2,1,out,2),-1);self.assertEqual(list(out),[0xdeadbeef]*6)
        self.assertEqual(fn(None,0,1,None,0),0)
    def testOfflineWidthTableMatchesPinnedSources(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/generate_width.py'),'--check'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
