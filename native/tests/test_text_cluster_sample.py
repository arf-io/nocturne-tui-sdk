"""Persistent whole-grapheme identity and native pose/source ownership."""
import ctypes as C
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class TextClusters(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
 def text(self,value):self.s.command(dict(op='text',id=1,text=value,effect='text/glyph-rain',durationMs=1000))
 def test_source_spans_reflow_pose_and_replay(self):
  self.text('Ae\u0301👩\u200d🔧Z');before=self.s.snapshot()
  rows=[self.s.text_cluster_sample(1,i) for i in range(4)]
  self.assertEqual([r[1:3] for r in rows],[(0,1),(1,3),(3,6),(6,7)])
  self.assertEqual(len({r[0] for r in rows}),4)
  self.assertEqual(rows[1][3:],self.s.text_sample(1,1)[3:])
  self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='text',id=1,width=2));self.assertEqual([self.s.text_cluster_sample(1,i)[0] for i in range(4)],[r[0] for r in rows])
  self.s.restore(before);self.assertEqual([self.s.text_cluster_sample(1,i) for i in range(4)],rows)
 def test_changed_combining_cluster_gets_new_identity(self):
  self.text('Ae\u0301Z');old=[self.s.text_cluster_sample(1,i)[0] for i in range(3)]
  self.text('Ae\u0300Z');new=[self.s.text_cluster_sample(1,i)[0] for i in range(3)]
  self.assertEqual(old[0],new[0]);self.assertEqual(old[2],new[2]);self.assertNotEqual(old[1],new[1])
 def test_merged_clusters_do_not_reuse_partial_identity(self):
  self.text('eZ');old=self.s.text_cluster_sample(1,0)[0]
  self.text('e\u0301Z');self.assertNotEqual(old,self.s.text_cluster_sample(1,0)[0])
  self.text('👩🔧Z');old=self.s.text_cluster_sample(1,0)[0]
  self.text('👩\u200d🔧Z');self.assertNotEqual(old,self.s.text_cluster_sample(1,0)[0])
 def test_invalid_empty_and_owned_output(self):
  self.text('A');row=self.s.text_cluster_sample(1,0);self.text('B');self.assertEqual(row[1:3],(0,1))
  for id,index in [(1,1),(2,0),(0,0),(1,-1),(True,0)]:
   with self.assertRaises(ValueError):self.s.text_cluster_sample(id,index)
  self.text('')
  with self.assertRaises(ValueError):self.s.text_cluster_sample(1,0)
 def test_native_rejection_is_atomic(self):
  self.text('é');fn=self.s._lib.nrTextClusterSample
  out=(C.c_int32*8)(*([12345]*8));saved=self.s.snapshot()
  for id,index,cap in [(1,1,8),(2,0,8),(1,0,7)]:
   self.assertEqual(fn(self.s._context,id,index,out,cap),-1);self.assertEqual(list(out),[12345]*8)
  self.assertEqual(fn(self.s._context,1,0,C.cast(self.s._context,C.POINTER(C.c_int32)),8),-1)
  self.assertEqual(self.s.snapshot(),saved)
if __name__=='__main__':unittest.main()
