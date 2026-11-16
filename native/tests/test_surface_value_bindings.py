"""Surface controls compare exact snapshots with public surface authoring."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
FIELDS={'collisionEnabled':0,'renderVisible':0,'maxIndividual':100,'maxTiles':100,'overflow':0,
 'restitution':.4,'friction':.2,'settleSpeed':3,'reentrainWindSpeed':5,
 'retentionMs':4000,'fadeMs':1000,'wetnessGain':.2,'evaporation':.2,
 'heatGain':.2,'cooling':.2,'thermalEvaporation':.2,'wetnessDarkening':.2,
 'heatColor':0xabcdef,'heatTintStrength':.2}
class SurfaceValueBindings(unittest.TestCase):
 def test_every_field_matches_public_edit_and_replay(self):
  for field,value in FIELDS.items():
   with self.subTest(field=field),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:scene.command({'op':'surface','id':1})
    public=bool(value) if field in ['collisionEnabled','renderVisible'] else ['reject-new','merge-to-field'][value] if field=='overflow' else value
    s.command({'op':'define','path':'/control','value':value,'binding':{'family':'surface','id':1,'field':field}})
    oracle.command({'op':'surface','id':1,field:public});s.command({'op':'remove-value','path':'/control'})
    self.assertEqual(s.snapshot(),oracle.snapshot())
    start=s.snapshot();s.advance_to(1000000);oracle.advance_to(1000000);self.assertEqual(s.snapshot(),oracle.snapshot())
    finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_boolean_fields_and_atomic_cross_property_errors(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1})
   s.command({'op':'define','path':'/visible','value':False,'binding':{'family':'surface','id':1,'field':'renderVisible'}})
   for field,value in [('maxTiles',0),('friction',2),('wetness',1),('fadeMs',.0005),('collisionEnabled',.5)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'surface','id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
