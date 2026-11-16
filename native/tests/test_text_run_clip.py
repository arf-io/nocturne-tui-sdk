"""Viewport intersections preserve complete canonical source clusters."""
from pathlib import Path
import sys,unittest,ctypes as C
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class TextRunClip(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
  self.s.command(dict(op='text',id=41,text='Aé中Z'))
 def testPartialWideGlyphKeepsFullSourceAndExplicitIntersection(self):
  before=self.s.snapshot();rows=self.s.text_run_clip(1,41,8,3,0,1,1)
  self.assertEqual(rows,[[41,3,4,2,0,2,1,1,1]])
  self.assertEqual(self.s.text_run_source(1,41),'Aé中Z');self.assertEqual(self.s.snapshot(),before)
 def testWrappedRowAndCombiningCluster(self):
  self.assertEqual(self.s.text_run_clip(1,41,3,0,1,3,1),[[41,3,4,0,1,2,1,0,2],[41,4,5,2,1,1,1,0,1]])
  self.assertEqual(self.s.text_run_clip(1,41,8,1,0,1,1),[[41,1,3,1,0,1,1,0,1]])
 def testEmptyOffscreenAndExtremeRectangles(self):
  for rect in [(0,0,0,1),(0,0,1,0),(0,10,8,1),(2**32-1,2**32-1,2**32-1,2**32-1)]:self.assertEqual(self.s.text_run_clip(1,41,8,*rect),[])
  with self.assertRaises(ValueError):self.s.text_run_clip(1,999,8,0,0,1,1)
  with self.assertRaises(ValueError):self.s.text_run_clip(1,41,8,-1,0,1,1)
 def testBufferCapacityProbeAndAtomicRejection(self):
  fn=self.s._lib.nrTextRunClip;fn.argtypes=[C.c_void_p]+[C.c_uint32]*8+[C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
  self.assertEqual(fn(self.s._context,1,41,1,8,0,0,8,1,None,0),4)
  out=(C.c_uint32*9)(*([99]*9));before=self.s.snapshot()
  self.assertEqual(fn(self.s._context,1,41,1,8,0,0,8,1,out,1),-1);self.assertEqual(list(out),[99]*9);self.assertEqual(before,self.s.snapshot())
if __name__=='__main__':unittest.main()
