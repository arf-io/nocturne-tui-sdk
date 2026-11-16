"""Actual ordinary catalogue Play/Peak controls versus retained full Atelier app."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,json,os,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
from native.tests import test_original_atelier_windows as oracle
class AtelierWindowGallery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True);cls.original=cls.browser.new_page();cls.original.set_content(gzip.decompress((oracle.ROOT/'tests/fixtures/original-atelier-spatial-v0.5.html.gz').read_bytes()).decode());cls.original.wait_for_function('window.atelierApp');cls.original.evaluate('atelierApp.stop()')
  cls.page=cls.browser.new_page(reduced_motion='reduce');cls.page.goto(Path(os.environ.get('NOCTURNE_ORIGINAL_GALLERY',oracle.ROOT/'Nocturne-RC4-Source-Build.html')).resolve().as_uri());cls.page.wait_for_function('window.nativeLab')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def compare(self,effect,time):
  expected=self.original.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');m.workspace.configure({effect:r.effect});if(r.time>=1000000){m.setTime(1000);m.workspace.hide(1,1000)}m.setTime(r.time/1000);return Array.from(atelierApp.renderer.render(m).frame.cells)}""",dict(effect=effect,time=time));expected=oracle.map_hits(expected)
  actual=self.page.evaluate("(()=>{const f=nativeLab.scene.render();return Array.from(new Uint32Array(f.bytes.buffer,f.bytes.byteOffset,f.bytes.byteLength/4))})()")
  self.assertEqual(len(actual),len(expected));diff=[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b];self.assertEqual(diff,[],effect+' @ '+str(time)+' '+str(diff[:10]))
 def test_all_22_normal_picker_peak_and_play_fullframes(self):
  self.page.locator('#effect').evaluate("e=>e.closest('details').open=true")
  count=0
  for entry in json.loads((oracle.ROOT/'catalogue.json').read_text()):
   if not (entry.get('sourceIdentity') or '').startswith('window/atelier/'):continue
   effect=entry['sourceIdentity'].rsplit('/',1)[1];count+=1
   self.page.evaluate("nativeLab.scene.command({op:'draft',text:'',emitWeather:false})");self.page.select_option('#effect',entry['id']);self.page.click('#effect-peak');self.page.evaluate('nativeLab.hold();nativeLab.draw()')
   self.assertEqual(self.page.evaluate('nativeLab.scene.infoComplete().windowApplication.scene'),'atelier-windows');self.compare(effect,900000)
   self.page.uncheck('#reduced-motion');self.page.evaluate("document.getElementById('effect-play').click();nativeLab.hold();nativeLab.advance(1425000);nativeLab.draw()");self.compare(effect,1425000)
  self.assertEqual(count,22)
if __name__=='__main__':unittest.main()
