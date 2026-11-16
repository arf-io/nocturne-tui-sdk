"""Authored for the collected text/scenic gate; no host key delivery inferred."""
import ctypes as C,itertools,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class ShortcutNegotiation(unittest.TestCase):
 def test_augmenting_assignment_reserved_chords_and_owned_output(self):
  with NativeScene() as s:
   before=s.snapshot();rows=s.negotiate_shortcuts([10,20,30],[[10,ord('q'),2],[10,ord('s'),2],[20,ord('q'),2],[30,ord('x'),8]],[[ord('q'),2,0],[ord('s'),2,0],[ord('x'),8,1]])
   self.assertEqual(rows,[[10,ord('s'),2,1],[20,ord('q'),2,1],[30,0,0,0]])
   rows[0][0]=0;self.assertEqual(s.snapshot(),before)
 def test_all_three_action_graphs_match_independent_exhaustive_cardinality(self):
  with NativeScene() as s:
   for mask in range(512):
    candidates=[[a+1,k+65,0] for a in range(3) for k in range(3) if mask&(1<<(a*3+k))]
    result=s.negotiate_shortcuts([1,2,3],candidates,[[65+k,0,0] for k in range(3)])
    best=0
    for choice in itertools.product(range(-1,3),repeat=3):
     used=[k for k in choice if k>=0]
     if len(set(used))!=len(used):continue
     if all(k<0 or mask&(1<<(a*3+k)) for a,k in enumerate(choice)):best=max(best,len(used))
    self.assertEqual(sum(r[3] for r in result),best);self.assertEqual(len({tuple(r[1:3]) for r in result if r[3]}),best)
 def test_candidate_preference_and_host_order_independence(self):
  with NativeScene() as s:
   c=[[1,66,0],[1,65,0],[1,66,0]]
   self.assertEqual(s.negotiate_shortcuts([1],c,[[65,0,0],[66,0,0]]),[[1,66,0,1]])
   self.assertEqual(s.negotiate_shortcuts([1],c,[[66,0,0],[65,0,0]]),[[1,66,0,1]])
 def test_empty_large_and_invalid_tables(self):
  with NativeScene() as s:
   self.assertEqual(s.negotiate_shortcuts([],[],[]),[])
   actions=list(range(1,65));rows=s.negotiate_shortcuts(actions,[[a,64+a,0] for a in actions],[[64+a,0,0] for a in actions]);self.assertTrue(all(r[3]==1 for r in rows))
   for actions,candidates,host in [([1,1],[],[]),([0],[],[]),([1],[[2,65,0]],[]),([1],[[1,0,0]],[]),([1],[],[[65,16,0]]),([1],[],[[65,0,2]]),([1],[],[[65,0,0],[65,0,1]])]:
    with self.assertRaises(ValueError):s.negotiate_shortcuts(actions,candidates,host)
 def test_raw_atomic_output_short_and_misaligned(self):
  with NativeScene() as s:
   s.negotiate_shortcuts([],[],[]);fn=s._lib.nrNegotiateShortcuts;a=(C.c_uint32*1)(1);c=(C.c_uint32*3)(1,65,0);h=(C.c_uint32*3)(65,0,0);out=(C.c_uint32*4)(99,99,99,99)
   self.assertEqual(fn(a,1,c,1,h,1,out,0),-1);self.assertEqual(list(out),[99]*4)
   self.assertEqual(fn(a,1,c,1,h,1,None,0),1)
   raw=(C.c_ubyte*20)(*([123]*20));ptr=C.cast(C.byref(raw,1),C.POINTER(C.c_uint32));self.assertEqual(fn(a,1,c,1,h,1,ptr,1),-1);self.assertEqual(bytes(raw),bytes([123]*20))

 def test_raw_input_output_aliasing_is_staged(self):
  with NativeScene() as s:
   s.negotiate_shortcuts([],[],[]);fn=s._lib.nrNegotiateShortcuts
   a=(C.c_uint32*4)(1,99,99,99);c=(C.c_uint32*3)(1,65,2);h=(C.c_uint32*3)(65,2,0)
   self.assertEqual(fn(a,1,c,1,h,1,a,1),1);self.assertEqual(list(a),[1,65,2,1])
 def test_application_uses_negotiated_help_and_dispatch(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
  from shortcut_application import ShortcutApplication
  with NativeScene() as s:
   s.command(dict(op='draft',text='Source e\u0301',emitWeather=False))
   app=ShortcutApplication(s,[[ord('s'),2,1],[ord('s'),8,0],[ord('r'),2,0],[ord('q'),2,1]])
   self.assertIn('Save: Meta+s',s.text_run_source(2,1));self.assertIn('Close: unassigned',s.text_run_source(2,1))
   self.assertFalse(app.dispatch(ord('s'),2));self.assertTrue(app.dispatch(ord('s'),8));self.assertEqual(app.saved,'Source e\u0301');self.assertTrue(app.dispatch(ord('r'),2));self.assertEqual(app.refreshes,1);self.assertFalse(app.dispatch(ord('q'),2));self.assertFalse(app.closed)
