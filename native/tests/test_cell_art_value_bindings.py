"""Cell-art controls retain glyph/color payloads and support full layout coordinates."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
BASE={'op':'cell-art','id':1,'width':2,'height':1,'x':4,'y':8,'alpha':.7,'layer':'overlay','cells':[[65,0xabcdef,0x123456],[66,0x654321,0x102030]]}
class CellArtValueBindings(unittest.TestCase):
 def test_controls_match_public_edit_without_replacing_cells(self):
  for field,value in [('x',12),('y',14),('alpha',.3),('layer',0),('x',2147483647),('y',-2147483648)]:
   with self.subTest(field=field,value=value),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:scene.command(BASE)
    s.command({'op':'define','path':'/art','value':value,'binding':{'family':'cell-art','id':1,'field':field}})
    oracle.command({'op':'cell-art','id':1,field:['background','overlay'][value] if field=='layer' else value})
    s.command({'op':'remove-value','path':'/art'});self.assertEqual(s.snapshot(),oracle.snapshot());self.assertEqual(s.render().bytes,oracle.render().bytes)
    start=s.snapshot();s.advance_to(1000000);finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_invalid_control_and_removed_resource_are_atomic(self):
  with NativeScene(42) as s:
   s.command(BASE)
   for field,value in [('width',3),('x',.5),('alpha',2),('layer',2)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'cell-art','id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
   s.command({'op':'define','path':'/art','value':.5,'binding':{'family':'cell-art','id':1,'field':'alpha'}})
   s.command({'op':'remove-cell-art','id':1});before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/art','value':.2})
   self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
