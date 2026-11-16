import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'));sys.path.insert(0,str(ROOT/'bindings/python'))
from gallery_cases import build_cases
from nocturne_native import NativeScene
class OriginalSurfaceRoutes(unittest.TestCase):
 def test_source_defaults_reach_all_primary_surface_recipes(self):
  cases=build_cases();catalog=json.loads((ROOT/'catalogue.json').read_text())
  for entry in [e for e in catalog if e['contract']=='SurfaceField']:
   routes=[c for c in cases if c.get('catalogueEffect')==entry['id']];self.assertEqual(len(routes),2)
   for case in routes:
    field=next(c for c in case['commands'] if c['op']=='field' and c['effect']==entry['id'])
    self.assertEqual(field['optics'],'source');self.assertFalse({'speed','width','strength','lifeMs'}&field.keys())
    self.assertTrue(any(c['id']==case['id']+'-legacy' for c in cases))
    with NativeScene(2030) as scene:
     for c in case['commands']:scene.command(c)
     self.assertEqual(scene.info()['fields'][0]['optics'],'source');scene.advance_to(900000);self.assertTrue(scene.render().bytes)
if __name__=='__main__':unittest.main()
