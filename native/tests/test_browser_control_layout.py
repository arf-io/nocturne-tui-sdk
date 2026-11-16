"""Actual current gallery controls stay right/below visible artwork."""
import importlib.util,os,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=Path(os.environ.get('NOCTURNE_LAYOUT_HTML',ROOT/'Nocturne-Test-Harness.html'))
CHECKER=Path(os.environ.get('NOCTURNE_LAYOUT_CHECKER',ROOT/'scripts/check_browser.py'))
spec=importlib.util.spec_from_file_location('browser_layout_checker',CHECKER)
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
class BrowserControlLayout(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def setUp(self):
  self.page=self.browser.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.page.set_content(HTML.read_text());self.page.wait_for_function('window.nativeLab');self.page.evaluate("nativeLab.load(nativeLab.recipes.find(r=>r.id==='windows'));nativeLab.hold();nativeLab.draw()")
 def tearDown(self):self.page.close();self.assertFalse(self.errors)
 def test_desktop_narrow_and_short_layout_keep_artwork_visible(self):
  for size in [{'width':1440,'height':1100},{'width':420,'height':800},{'width':420,'height':400}]:
   with self.subTest(viewport=size):
    self.page.set_viewport_size(size);self.page.evaluate("document.querySelector('#motion-panel').open=false")
    self.assertTrue(checker.motionControlsClearOfCanvas(self.page))
    self.page.locator('#motion-panel summary').click();self.page.locator('#fps').focus()
    self.assertTrue(checker.motionControlsClearOfCanvas(self.page))
    self.assertTrue(self.page.locator('#fps').evaluate('(e)=>{const r=e.getBoundingClientRect();return document.activeElement===e&&r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight;}'))
 def test_overlapping_motion_controls_are_rejected(self):
  for size in [{'width':1440,'height':1100},{'width':420,'height':800}]:
   with self.subTest(viewport=size):
    self.page.set_viewport_size(size)
    self.page.evaluate("()=>{const c=document.querySelector('#canvas').getBoundingClientRect(),p=document.querySelector('#motion-panel');p.style.cssText='position:fixed;z-index:9999;left:'+(c.left+10)+'px;top:'+(c.top+10)+'px;width:180px;height:80px;';}")
    self.assertFalse(checker.motionControlsClearOfCanvas(self.page))
    self.page.locator('#motion-panel').evaluate('(e)=>e.removeAttribute("style")')
 def test_offscreen_canvas_is_rejected(self):
  self.page.locator('#canvas').evaluate('(e)=>e.style.transform="translateX(-20000px)"')
  self.assertFalse(checker.motionControlsClearOfCanvas(self.page))
if __name__=='__main__':unittest.main()
