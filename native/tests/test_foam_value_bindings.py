"""Foam settings preserve accumulated source/decay/saturation history."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class FoamValueBindings(unittest.TestCase):
 def test_all_controls_match_public_edit_with_live_ledger(self):
  for field,value in {'enabled':0,'sourceRate':3,'curvatureThreshold':.2,'decay':2,'impactGain':.2,'color':0xabcdef}.items():
   with self.subTest(field=field),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:
     for command in [{'op':'surface','id':1},{'op':'mesh','triangles':[{'a':[-10,0,-10],'b':[10,0,-10],'c':[0,0,10],'surfaceId':1}]},
      {'op':'surface-waves','surfaceId':1,'waves':[[1,1,0,0,0]]},{'op':'surface-foam','surfaceId':1,'sourceRate':2,'curvatureThreshold':0}]:scene.command(command)
     scene.advance_to(250000)
    ledger=s.surface_foam(1)
    s.command({'op':'define','path':'/foam','value':value,'binding':{'family':'surface-foam','id':1,'field':field}})
    self.assertEqual(s.surface_foam(1),ledger)
    oracle.command({'op':'surface-foam','surfaceId':1,field:bool(value) if field=='enabled' else value})
    s.command({'op':'remove-value','path':'/foam'});self.assertEqual(s.snapshot(),oracle.snapshot())
    start=s.snapshot();s.advance_to(1000000);oracle.advance_to(1000000);self.assertEqual(s.snapshot(),oracle.snapshot())
    finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_missing_settings_derived_fields_and_invalid_bounds_are_atomic(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1})
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'define','path':'/foam','value':1,'binding':{'family':'surface-foam','id':1,'field':'sourceRate'}})
   self.assertEqual(before,s.snapshot());s.command({'op':'surface-foam','surfaceId':1})
   s.command({'op':'define','path':'/enabled','value':False,'binding':{'family':'surface-foam','id':1,'field':'enabled'}})
   for field,value in [('density',.5),('enabled',.5),('sourceRate',1001),('decay',-1),('color',.5)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'surface-foam','id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
