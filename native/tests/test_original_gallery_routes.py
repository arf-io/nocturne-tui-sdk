import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy,gzip,hashlib,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"examples"))
from gallery_cases import build_cases
class OriginalRoutes(unittest.TestCase):
 def test_normal_catalogue_window_routes_and_compact_variants(self):
  cases={c["id"]:c for c in build_cases()};catalog=json.loads((ROOT/"catalogue.json").read_text())
  for entry in catalog:
   if not (entry.get("sourceIdentity") or "").startswith("window/kinetic/"):continue
   for mode in ("isolated","application"):
    identity="study-"+entry["id"].replace("/","-")+"-"+mode;case=cases[identity]
    self.assertEqual(case.get("catalogueEffect"),entry["id"])
    self.assertEqual(case.get("sourceIdentity"),entry["sourceIdentity"])
    self.assertEqual([c["label"] for c in case["commands"] if c["op"]=="window-content"],["pearl","atlas","iris"])
    if mode=="application":self.assertTrue(any(c["op"]=="window-application" for c in case["commands"]))
    self.assertIn(identity+"-compact",cases)
 def test_text_picker_and_all_original_background_choices(self):
  cases=build_cases();catalog=json.loads((ROOT/"catalogue.json").read_text())
  for entry in catalog:
   if not (entry.get("sourceIdentity") or "").startswith("text/kinetic/"):continue
   routes=[c for c in cases if c.get("catalogueEffect")==entry["id"]]
   self.assertEqual(len(routes),2)
   for case in routes:self.assertEqual(next(c for c in case["commands"] if c["op"]=="text" and c["id"]==1)["phaseModel"],"source-paint")
  expected={"linear","double-axis","wave","plasma","caustics","vortex","contours","aurora","woven","moire","tunnel","diamond","bilinear","checker","warp"}
  actual={c["originalBackground"] for c in cases if "originalBackground" in c}
  self.assertEqual(actual,expected)
class OriginalRouteBrowser(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from playwright.sync_api import sync_playwright
  from native.tests.test_rc2_window_compositions import original_runtime_source
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True)
  cls.original=cls.browser.new_page();cls.original.set_content(original_runtime_source(),wait_until='domcontentloaded');cls.original.wait_for_function('window.__rc2WindowComposition && window.fieldGuide')
  cls.page=cls.browser.new_page(reduced_motion='reduce');cls.page.goto(Path(os.environ.get('NOCTURNE_ORIGINAL_GALLERY',ROOT/'Nocturne-RC4-Source-Build.html')).resolve().as_uri());cls.page.wait_for_function('window.nativeLab')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def assert_frame(self,key,effect=None,background=None,time_us=0):
  expected=self.original.evaluate("""r=>{const api=window.__rc2WindowComposition,m=new api.KineticModel();m.resize(136,44);m.setScene('windows');if(r.effect)m.spaceWindows.configure({effect:r.effect});if(r.background)m.configure({backgroundStyle:r.background});if(r.t>=1000000&&r.effect){m.setTime(1000);m.spaceWindows.act('pearl','minimize',1000);}m.draft='';m.setTime(r.t/1000);return Array.from(new api.KineticRenderer(fieldGuide.engine).render(m,r.t/1000).frame.cells)}""",{'effect':effect,'background':background,'t':time_us})
  actual=self.page.evaluate("(()=>{let f=nativeLab.scene.render();return Array.from(new Uint32Array(f.bytes.buffer,f.bytes.byteOffset,f.bytes.byteLength/4));})()")
  self.assertEqual(len(actual),len(expected));different=[i for i,(a,b) in enumerate(zip(actual,expected)) if i%4!=3 and a!=b];self.assertEqual(different,[],key+': '+str(different[:10]))
  if os.environ.get('NOCTURNE_ROUTE_CAPTURES'):
   folder=Path(os.environ['NOCTURNE_ROUTE_CAPTURES']);folder.mkdir(parents=True,exist_ok=True);(folder/(hashlib.sha256(key.encode()).hexdigest()[:16]+'.json.gz')).write_bytes(gzip.compress(json.dumps({'key':key,'original':expected,'wasm':actual}).encode(),mtime=0))
 def test_normal_picker_original_windows_and_text(self):
  self.page.get_by_text('Native effect catalogue • all port identities',exact=True).click()
  catalog=json.loads((ROOT/'catalogue.json').read_text())
  for entry in catalog:
   source=entry.get('sourceIdentity') or ''
   if not source.startswith(('window/kinetic/','text/kinetic/')):continue
   self.page.evaluate("nativeLab.scene.command({op:'draft',text:'',emitWeather:false})")
   self.page.select_option('#effect',entry['id']);self.page.click('#effect-peak');self.page.evaluate('nativeLab.hold();nativeLab.draw()')
   info=self.page.evaluate('nativeLab.scene.infoComplete()')
   self.assertEqual(info['clock']['timeUs'],900000)
   if source.startswith('window/'):
    self.assertEqual(info['windowApplication']['paletteWindowId'],1);self.assertEqual(info['camera']['profile'],'original');self.assertEqual([w['content']['label'] for w in info['windows']],['pearl','atlas','iris'])
    self.assert_frame('picker-'+entry['id'],effect=source.rsplit('/',1)[1],time_us=900000)
    self.page.uncheck('#reduced-motion');self.page.evaluate("document.getElementById('effect-play').click();nativeLab.hold();nativeLab.advance(1425000);nativeLab.draw()")
    self.assert_frame('play-'+entry['id'],effect=source.rsplit('/',1)[1],time_us=1425000)
   else:self.assertEqual(next(t for t in info['textRuns'] if t['id']==1)['phaseModel'],'source-paint')
 def test_normal_surface_picker_uses_source_optics(self):
  self.page.locator('#effect').evaluate("e=>e.closest('details').open=true")
  for effect in ('silk-tide','satin-rings','opal-fronts','interference-tide'):
   self.page.select_option('#effect','surface-field/'+effect);self.page.click('#effect-peak')
   info=self.page.evaluate('nativeLab.scene.infoComplete()');self.assertEqual(info['clock']['timeUs'],900000)
   self.assertEqual(info['fields'][0]['optics'],'source')
 def test_normal_original_background_entries(self):
  from original_gallery_routes import ORIGINAL_BACKGROUNDS
  for background in ORIGINAL_BACKGROUNDS:
   self.page.evaluate("nativeLab.scene.command({op:'draft',text:'',emitWeather:false})")
   self.page.select_option('#scenes','original-background-'+background);self.page.evaluate('nativeLab.hold();nativeLab.advance(1700000);nativeLab.draw()')
   self.assert_frame('background-'+background,background=background,time_us=1700000)
if __name__=="__main__":unittest.main()
