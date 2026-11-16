import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'))
from gallery_cases import build_cases
class OriginalWeatherRoutes(unittest.TestCase):
 def test_all_ten_original_weather_styles_are_primary(self):
  cases=build_cases();catalog=json.loads((ROOT/'catalogue.json').read_text());count=0
  for entry in catalog:
   source=entry.get('sourceIdentity') or ''
   if not entry['id'].startswith('weather/') or not source.startswith(('weather/kinetic.','weather/atelier.')):continue
   count+=1;family='kinetic' if source.startswith('weather/kinetic.') else 'atelier';seed=2030 if family=='kinetic' else 4711
   routes=[c for c in cases if c.get('catalogueEffect')==entry['id']];self.assertEqual(len(routes),2)
   for case in routes:
    emitter=next(c for c in case['commands'] if c['op']=='emitter' and c['id']==1);self.assertEqual(emitter['alpha'],1)
    style=next(c for c in case['commands'] if c['op']==family+'-style');self.assertEqual(style,{'op':family+'-style','id':1,'paint':'source','seed':seed,'eventId':1 if family=='kinetic' else seed})
    self.assertTrue(any(c['id']==case['id']+'-generic' for c in cases))
  self.assertEqual(count,10)
 def test_classic_kinetic_recipes_use_source_and_retain_generic_versions(self):
  recipes=json.loads((ROOT/'recipes.json').read_text())
  for identity in ('chrysanthemum','arcs'):
   case=next(c for c in recipes if c['id']==identity)
   emitter=next(c for c in case['commands'] if c['op']=='emitter');self.assertEqual(emitter.get('alpha'),1)
   self.assertIn({'op':'kinetic-style','id':1,'paint':'source','seed':2030,'eventId':1},case['commands'])
   prior=next(c for c in recipes if c['id']==identity+'-generic')
   self.assertFalse(any(c['op']=='kinetic-style' for c in prior['commands']))
class OriginalWeatherRouteBrowser(unittest.TestCase):
 def test_all_ten_normal_picker_readbacks_use_source_paint(self):
  from playwright.sync_api import sync_playwright
  catalog=json.loads((ROOT/'catalogue.json').read_text())
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True)
   try:
    page=browser.new_page(reduced_motion='reduce');page.goto(Path(os.environ.get('NOCTURNE_ORIGINAL_GALLERY',ROOT/'Nocturne-RC4-Source-Build.html')).resolve().as_uri());page.wait_for_function('window.nativeLab');page.get_by_text('Native effect catalogue • all port identities',exact=True).click()
    for entry in catalog:
     source=entry.get('sourceIdentity') or ''
     if not entry['id'].startswith('weather/') or not source.startswith(('weather/kinetic.','weather/atelier.')):continue
     page.select_option('#effect',entry['id']);page.click('#effect-peak');info=page.evaluate('nativeLab.scene.infoComplete()')
     self.assertEqual(info['clock']['timeUs'],900000)
     row=next(e for e in info['emitters'] if e['id']==1);style=row['kinetic'] if source.startswith('weather/kinetic.') else row['atelier']
     self.assertEqual(style['paint'],'source');self.assertEqual(row['alpha'],1)
   finally:browser.close()
if __name__=='__main__':unittest.main()
