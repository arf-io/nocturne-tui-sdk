"""Context-owned source/run identity independent of clipping and presentation."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class TextRunLayout(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
 def layout(self,kind,id,columns=8,capacity=2048):
  fn=self.s._lib.nrTextRunLayout;fn.argtypes=[C.c_void_p]+[C.c_uint32]*4+[C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
  out=(C.c_uint32*(max(1,capacity)*7))(*([0xdeadbeef]*(max(1,capacity)*7)))
  n=fn(self.s._context,kind,id,1,columns,out,capacity)
  return n,[list(out[i*7:i*7+7]) for i in range(max(0,n))],out
 def testPromptClustersHaveSourceOffsetsAndStableRunIdentity(self):
  self.s.command(dict(op='draft',text='Aé中',emitWeather=False));before=self.s.snapshot()
  n,rows,_=self.layout(0,0,3);self.assertEqual(rows,[[0,0,1,0,0,1,0],[0,1,3,1,0,1,0],[0,3,4,0,1,2,0]])
  self.assertEqual(self.s.snapshot(),before);self.assertEqual(n,3)
 def testAuthoredTextIdentitySurvivesReflowAndRetarget(self):
  self.s.command(dict(op='text',id=41,text='é中Z'))
  a=self.layout(1,41,8)[1];b=self.layout(1,41,2)[1]
  self.assertEqual([r[:3] for r in a],[r[:3] for r in b]);self.assertTrue(all(r[0]==41 and r[6]==1 for r in b))
  self.s.command(dict(op='text',id=41,text='日本'));self.assertEqual(self.layout(1,41)[1][0][:3],[41,0,1])
 def testWindowBodyAndTitleHaveSeparateKinds(self):
  self.s.command(dict(op='window',id=7,title='日本',text='A\nB'))
  self.assertEqual(self.layout(2,7)[1][-1],[7,2,3,0,1,1,2]);self.assertEqual(self.layout(3,7)[0],2)
 def testInvalidRunAndShortOutputRejectUntouched(self):
  self.s.command(dict(op='draft',text='ABC',emitWeather=False))
  for kind,id,col,cap in [(9,0,8,3),(1,999,8,3),(0,1,8,3),(0,0,0,3),(0,0,8,2)]:
   n,_,out=self.layout(kind,id,col,cap);self.assertEqual(n,-1);self.assertTrue(all(v==0xdeadbeef for v in out))
 def testProbeOverlapAndEmptyExistingRun(self):
  self.s.command(dict(op='draft',text='ABC',emitWeather=False));self.layout(0,0)
  fn=self.s._lib.nrTextRunLayout;self.assertEqual(fn(self.s._context,0,0,1,8,None,0),3)
  before=self.s.snapshot();overlap=C.cast(self.s._context,C.POINTER(C.c_uint32))
  self.assertEqual(fn(self.s._context,0,0,1,8,overlap,2048),-1);self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='text',id=12,text=''));self.assertEqual(self.s.text_run_source(1,12),'');self.assertEqual(self.s.text_run_layout(1,12,1),[])
 def testSnapshotRestoresRunSourceAndAllScalarCapacity(self):
  self.s.command(dict(op='text',id=41,text='中'*2048));saved=self.s.snapshot();rows=self.s.text_run_layout(1,41,1)
  self.assertEqual((len(rows),rows[-1]),(2048,[41,2047,2048,0,2047,2,1]))
  self.s.command(dict(op='text',id=41,text='changed'));self.s.restore(saved)
  self.assertEqual(self.s.text_run_source(1,41),'中'*2048);self.assertEqual(self.s.text_run_layout(1,41,1),rows)
 def testContextHitMappingUsesSameSourceAcrossReflow(self):
  self.s.command(dict(op='text',id=41,text='Aé中Z'));before=self.s.snapshot()
  self.assertEqual(self.s.text_run_hit(1,41,3,0,1),3)
  self.assertEqual(self.s.text_run_hit(1,41,3,1,1),4)
  self.assertEqual(self.s.text_run_hit(1,41,8,2,0),3)
  self.assertEqual(self.s.snapshot(),before)
  with self.assertRaises(ValueError):self.s.text_run_hit(1,999,8,0,0)
  with self.assertRaises(ValueError):self.s.text_run_hit(1,41,0,0,0)
 def testOwnedBindingSourceAndLayoutRemainAvailableBehindModal(self):
  self.s.command(dict(op='draft',text='é日本',emitWeather=False));self.s.command(dict(op='key',key='F1'));before=self.s.snapshot()
  self.assertEqual(self.s.text_run_source(0,0),'é日本');self.assertEqual(self.s.text_run_layout(0,0,2)[0],[0,0,2,0,0,1,0]);self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
