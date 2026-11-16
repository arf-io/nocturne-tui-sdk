"""Float-body controls match public edits without resetting simulated motion."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
FIELDS={'mass':2000,'radius':2,'fluidDensity':800,'gravity':10,'drag':3,'visible':0,'color':0xabcdef,'surfaceId':2,
 'position.x':2,'position.y':2,'position.z':2,'velocity.x':1,'velocity.y':1,'velocity.z':1}
class FloatValueBindings(unittest.TestCase):
 def test_all_fields_match_public_edit_on_moving_body(self):
  for field,value in FIELDS.items():
   with self.subTest(field=field),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:
     for command in [{'op':'surface','id':1},{'op':'surface','id':2},{'op':'mesh','triangles':[{'a':[-10,0,-10],'b':[10,0,-10],'c':[0,0,10],'surfaceId':1}]},
      {'op':'float-body','id':1,'surfaceId':1,'position':[0,0,0],'velocity':[1,0,0]}]:scene.command(command)
     scene.advance_to(250000)
    before=oracle.float_body(1);edit={'op':'float-body','id':1}
    if '.' in field:
     name,axis=field.split('.');vector=list(before[:3] if name=='position' else before[3:6]);vector['xyz'.index(axis)]=value;edit[name]=vector
    else:edit[field]=bool(value) if field=='visible' else value
    s.command({'op':'define','path':'/control','value':value,'binding':{'family':'float-body','id':1,'field':field}})
    oracle.command(edit);s.command({'op':'remove-value','path':'/control'});self.assertEqual(s.snapshot(),oracle.snapshot())
    start=s.snapshot();s.advance_to(1000000);oracle.advance_to(1000000);self.assertEqual(s.snapshot(),oracle.snapshot())
    finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_removed_body_and_invalid_settings_reject_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1});s.command({'op':'float-body','id':1,'surfaceId':1})
   s.command({'op':'define','path':'/visible','value':False,'binding':{'family':'float-body','id':1,'field':'visible'}})
   for field,value in [('mass',0),('radius',100),('surfaceId',2),('normal.x',1),('visible',.5)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'float-body','id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
   s.command({'op':'remove-float-body','id':1});before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/visible','value':True})
   self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
