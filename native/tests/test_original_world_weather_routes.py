"""Actual normal catalog route commands must select original weather painting."""
import copy,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'));sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from gallery_cases import build_cases
class OriginalWorldWeatherRoutes(unittest.TestCase):
 def test_normal_routes_run_actual_source_styles_and_preserve_generic(self):
  from original_world_weather_routes import apply_original_world_weather_routes
  catalogue=json.loads((ROOT/'catalogue.json').read_text());cases=build_cases();before={c['id']:copy.deepcopy(c) for c in cases};result=apply_original_world_weather_routes(cases,catalogue);by={c['id']:c for c in result};count=0
  for entry in catalogue:
   identity=entry.get('sourceIdentity') or ''
   if not identity.startswith(('weather/world.','weather/thermal.','weather/studio.nova','weather/observatory.rain','weather/observatory.snow','weather/observatory.embers','weather/observatory.sparks','weather/observatory.nova')):continue
   for mode in ('isolated','application'):
    key='study-'+entry['id'].replace('/','-')+'-'+mode;case=by[key];clone=by[key+'-generic'];self.assertEqual(clone['commands'],before.get(key+'-generic',before[key])['commands']);self.assertEqual(case['catalogueEffect'],entry['id']);self.assertFalse(clone['demo'])
    with NativeScene(2030) as scene:
     for command in case['commands']:scene.command(command)
     scene.advance_to(750000);row=next(e for e in scene.info_complete()['emitters'] if e['id']==1);family='worldSource' if identity.startswith('weather/world.') else 'thermalSource' if identity.startswith('weather/thermal.') else 'corona' if identity=='weather/observatory.nova' else 'observatory' if identity.startswith('weather/observatory.') else 'studioNova';self.assertEqual(row[family]['paint'],'source');self.assertEqual(next(c for c in case['commands'] if c['op']=='emitter' and c['id']==1)['alpha'],1)
     before_render=scene.snapshot();frame=scene.render().bytes;self.assertTrue(frame);self.assertEqual(before_render,scene.snapshot())
     if family=='worldSource':
      self.assertEqual(row[family]['seed'],(2654435761^2030)&0xffffffff);self.assertEqual(row[family]['controls']['count'],160);self.assertEqual(row[family]['controls']['gravity'],8)
      if identity=='weather/world.ripples':self.assertEqual(row[family]['pointsCount'],0);self.assertEqual(row[family]['ripplePlane']['rings'],4);self.assertNotEqual(row['birthOrientation'],[0,0,0])
     count+=1
  self.assertEqual(count,32)
if __name__=='__main__':unittest.main()
