"""Original modal controls on the ordinary gallery, with actual Chromium/WASM."""
import os,unittest,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class SourceModalGallery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True);cls.page=cls.browser.new_page(viewport={'width':1440,'height':1000});cls.page.goto(Path(os.environ.get('NOCTURNE_MODAL_GALLERY',ROOT/'Nocturne-RC4-Source-Build.html')).as_uri());cls.page.wait_for_function('window.nativeLab?.scene');cls.page.evaluate('nativeLab.hold()');
  if cls.page.locator('#source-modal-panel').count():cls.page.locator('#source-modal-panel > summary').click()
 def setUp(self):
  if self.page.locator('#source-modal-clear').count():self.page.locator('#source-modal-clear').click()
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def test_all_original_kinds_normal_controls(self):
  p=self.page;self.assertEqual(p.locator('#source-modal-kind').count(),1)
  for kind in ['center','fullscreen','drawer-left','drawer-right','drawer-top','drawer-bottom','corner','toast','error','confirmation','dropdown']:
   p.locator('#source-modal-kind').select_option(kind);p.locator('#source-modal-open').click();info=p.evaluate('nativeLab.scene.infoComplete().sourceModal');self.assertEqual(info['entries'][-1]['kind'],kind);self.assertTrue(info['associated']);p.locator('#source-modal-pop').click();self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.depth'),0)
 def test_normal_picker_original_modal_frames(self):
  import gzip,json
  rows=json.loads(gzip.decompress((ROOT/'tests/fixtures/source-modal/COMPOSED.json.gz').read_bytes()))['rows'];p=self.page
  for row in rows:
   if row['time']!=400:continue
   identity='source-modal-'+row['kind'];p.locator('#scenes').select_option(identity);p.evaluate("id=>{nativeLab.load(nativeLab.recipes.find(r=>r.id===id));nativeLab.hold();nativeLab.advance(400000);nativeLab.draw()}",identity)
   self.assertTrue(p.evaluate('Array.from(nativeLab.scene.render().cells)')==row['currentIdentityFrame'],identity+' full original frame')
 def test_nested_query_restoration_help_and_blocked_pointer(self):
  p=self.page;p.locator('#source-modal-kind').select_option('center');p.locator('#source-modal-open').click();p.locator('#source-modal-query').fill('camera');p.locator('#source-modal-open').click();p.locator('#source-modal-query').fill('inner');p.locator('#source-modal-pop').click();self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.query'),'camera')
  p.locator('canvas').focus();p.keyboard.press('F1');self.assertEqual(p.evaluate('nativeLab.scene.info().modal'),1);p.keyboard.press('Escape');self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.depth'),1);p.keyboard.press('Escape');self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.depth'),0)
 def test_query_above_old_capacity_remains_visible_and_editable(self):
  p=self.page;p.locator('#source-modal-open').click();text='λ'*70001;p.locator('#source-modal-query').fill(text);self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.query'),text);p.evaluate('nativeLab.draw()');self.assertEqual(p.locator('#source-modal-query').input_value(),text);self.assertEqual(p.locator('#error').inner_text(),'');p.locator('#source-modal-open').click();self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.depth'),2);p.locator('#source-modal-pop').click();self.assertEqual(p.evaluate('nativeLab.scene.infoComplete().sourceModal.query'),text);p.locator('#source-modal-pop').click()
 def test_changing_background_and_snapshot_controller_replay(self):
  p=self.page;p.evaluate("nativeLab.scene.command({op:'source-stage-component',id:42,kind:'item',legacyFlags:42,x:0,y:4,width:10,height:1,text:'background'})");p.locator('#source-modal-open').click();a=p.evaluate("Array.from(nativeLab.scene.render().cells)");p.evaluate("nativeLab.scene.command({op:'source-stage-component',id:42,kind:'item',legacyFlags:42,x:0,y:4,width:10,height:1,text:'changed'});nativeLab.draw()");self.assertEqual(p.evaluate("nativeLab.scene.infoComplete().sourceStageComponents.find(n=>n.id===42).text"),'changed');self.assertTrue(a!=p.evaluate('Array.from(nativeLab.scene.render().cells)'), 'background authored update must change actual visible pixels')
  self.assertTrue(p.evaluate("(()=>{const a=nativeLab.scene.snapshot();nativeLab.scene.command({op:'source-modal',action:'dismiss'});nativeLab.draw();nativeLab.scene.restore(a);nativeLab.draw();return nativeLab.scene.infoComplete().sourceModal.depth===1})()"));p.locator('#source-modal-pop').click();self.assertEqual(p.evaluate('nativeLab.scene.sourceStageHit(1,4).id'),42)
if __name__=='__main__':unittest.main()
