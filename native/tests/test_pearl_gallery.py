"""Real current WASM gallery: original source waveform and persistent artwork viewport."""
from pathlib import Path
import os,unittest,json,hashlib,subprocess,struct,tempfile,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
TEMP=tempfile.TemporaryDirectory(prefix='nocturne-pearl-gallery-')
B=Path(os.environ.get('NOCTURNE_PEARL_EVIDENCE',TEMP.name));B.mkdir(parents=True,exist_ok=True)
HTML=Path(os.environ.get('NOCTURNE_PEARL_GALLERY_PATH',ROOT/'Nocturne-Test-Harness.html'))
class PearlGallery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def setUp(self):
  self.page=self.browser.new_page(viewport={'width':1440,'height':900});self.errors=[];self.page.on('pageerror',lambda x:self.errors.append(str(x)));self.page.set_content(HTML.read_text());self.page.wait_for_function('window.nativeLab');self.page.evaluate('nativeLab.hold()')
 def tearDown(self):self.page.close()
 def load(self,id):self.page.evaluate("id=>{nativeLab.load(nativeLab.recipes.find(r=>r.id===id));nativeLab.hold();nativeLab.draw();}",id)
 def assertStageVisible(self):
  a=self.page.locator('.stage').bounding_box();v=self.page.viewport_size
  self.assertGreaterEqual(a['x'],0);self.assertGreaterEqual(a['y'],0);self.assertLessEqual(a['x']+a['width'],v['width']);self.assertLessEqual(a['y']+a['height'],v['height']);self.assertGreater(self.page.locator('canvas').bounding_box()['height'],120)
 def test_controls_preserve_full_stage_desktop_and_narrow(self):
  for viewport in [{'width':1440,'height':900},{'width':420,'height':800}]:
   self.page.set_viewport_size(viewport);self.load('pearl-curves');self.page.evaluate('nativeLab.advance(3000000);nativeLab.draw()');self.page.locator('#config').evaluate("e=>e.closest('details').open=true");self.page.locator('#config').focus();self.assertStageVisible();self.page.locator('#config').press('Tab');self.assertStageVisible();self.page.screenshot(path=str(B/('layout-'+str(viewport['width'])+'.png')));self.assertFalse(self.errors)
 def test_original_waveform_changes_actual_native_geometry_after_reveal(self):
  for id in ['instruments','pearl-curves']:
   self.load(id);self.page.evaluate('nativeLab.advance(3000000);nativeLab.draw()')
   a=self.page.evaluate('Array.from(nativeLab.scene.render().cells).filter((_,i)=>i%4===0)')
   self.page.evaluate('nativeLab.advance(1000000);nativeLab.draw()')
   c=self.page.evaluate('Array.from(nativeLab.scene.render().cells).filter((_,i)=>i%4===0)');self.assertTrue(a!=c,id+' must retain original live data motion after reveal')
   self.assertTrue(self.page.evaluate('()=>{const s=nativeLab.scene.snapshot();nativeLab.draw();nativeLab.draw();const t=nativeLab.scene.snapshot();return s.length===t.length&&s.every((v,i)=>v===t[i]);}'));self.assertFalse(self.errors)
 def test_exact_original_sampler_and_static_controls(self):
  source=ROOT/'tests/fixtures/pearl-observatory-original.mjs'
  self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),'c221beb6e719f47f2c4744fce7cf70fcf918a31b436b6f0f1fca4df63f283904')
  script="import {ObservatoryModel} from "+json.dumps(source.as_uri())+"; const m=new ObservatoryModel();const rows=[];for(const [at,sampledAt] of [[0,0],[50,50],[425,400],[1703,1700],[5001,5000]]){m.demoData(sampledAt);rows.push({at,sampledAt,wave:m.waveform.map(v=>Math.max(0,Math.min(1,.5+v*m.options.scopeGain*.42))),heat:m.bus.samples.get('demo.heat').value,audio:m.bus.samples.get('demo.audio').value});}console.log(JSON.stringify(rows));"
  oracle=json.loads(subprocess.check_output([shutil.which('node') or 'node','--input-type=module','-e',script],text=True));(B/'actual-original-sampler.json').write_text(json.dumps(oracle,indent=2)+'\n')
  for id,target in [('instruments',2),('pearl-curves',8)]:
   self.load(id);previous=0
   for row in oracle:
    at=row['at']*1000;self.page.evaluate('delta=>{nativeLab.advance(delta);nativeLab.draw();}',at-previous);previous=at
    data=self.page.evaluate('id=>nativeLab.scene.info().widgets.find(w=>w.id===id).data',target)
    self.assertEqual(len(data),128)
    for a,e in zip(data,row['wave']):self.assertAlmostEqual(a,e,places=6)
    cells=self.page.evaluate('Array.from(nativeLab.scene.render().cells)');raw=struct.pack('<'+'I'*len(cells),*cells);(B/(id+'-'+str(at)+'-cells.bin')).write_bytes(raw)
    (B/(id+'-'+str(at)+'-sample.json')).write_text(json.dumps({'requestedTimeUs':at,'nativeTimeUs':self.page.evaluate('nativeLab.scene.info().clock.timeUs'),'originalSampleTimeMs':row['sampledAt'],'actualData':data,'oracleData':row['wave'],'frameSha256':hashlib.sha256(raw).hexdigest(),'cells':len(cells)//4},indent=2)+'\n')
   self.page.locator('#pearl-data-source').evaluate("e=>e.closest('details').open=true");self.page.locator('#pearl-data-source').select_option('authored')
   before=self.page.evaluate('id=>nativeLab.scene.info().widgets.find(w=>w.id===id).data',target);self.page.evaluate('nativeLab.advance(1000000)');after=self.page.evaluate('id=>nativeLab.scene.info().widgets.find(w=>w.id===id).data',target);self.assertEqual(before,after)
 def test_hold_custom_reset_and_snapshot_detach_data_source(self):
  self.load('instruments');self.page.evaluate('nativeLab.advance(3000000);nativeLab.draw()')
  before=self.page.evaluate('nativeLab.scene.info().widgets.find(w=>w.id===2).data');self.page.wait_for_timeout(150);self.assertEqual(before,self.page.evaluate('nativeLab.scene.info().widgets.find(w=>w.id===2).data'))
  self.page.locator('#save').evaluate("e=>e.closest('details').open=true")
  with self.page.expect_download() as downloaded:self.page.locator('#save').click()
  self.page.locator('#snapshot-file').set_input_files(downloaded.value.path());self.page.wait_for_function("document.getElementById('pearl-data-source').disabled")
  self.page.evaluate('nativeLab.advance(1000000)');self.assertEqual(before,self.page.evaluate('nativeLab.scene.info().widgets.find(w=>w.id===2).data'))
  self.load('pearl-curves');self.page.locator('#config').evaluate("e=>e.closest('details').open=true");self.page.locator('#config').fill('[{"op":"widget","id":8,"kind":"line","x":1,"y":2,"width":50,"height":10,"data":[0,1,0]}]');self.page.locator('#apply').click();self.page.evaluate('nativeLab.hold();nativeLab.advance(4000000)');self.assertEqual(self.page.evaluate('nativeLab.scene.info().widgets[0].data'),[0,1,0]);self.assertTrue(self.page.locator('#pearl-data-source').is_disabled());self.assertFalse(self.errors)
 def test_short_viewport_all_disclosures_and_coordinate_mapping(self):
  self.page.set_viewport_size({'width':420,'height':400});self.load('pearl-curves');self.page.evaluate('nativeLab.advance(3000000);nativeLab.draw()')
  for panel in self.page.locator('details').all():
   panel.evaluate("e=>{for(let p=e;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}");panel.locator(':scope > summary').focus()
   stage=self.page.locator('.stage').bounding_box();canvas=self.page.locator('canvas').bounding_box()
   self.assertGreaterEqual(stage['y'],0);self.assertLessEqual(stage['y']+stage['height'],400);self.assertGreater(canvas['height'],60)
   self.assertGreaterEqual(canvas['y'],stage['y']);self.assertLessEqual(canvas['y']+canvas['height'],stage['y']+stage['height'])
   actual=self.page.evaluate('()=>({width:nativeLab.scene.render().width,height:nativeLab.scene.render().height})');self.assertAlmostEqual(canvas['width']/canvas['height'],actual['width']/(actual['height']*2),places=2)
   panel.evaluate('e=>e.open=false')
  self.page.screenshot(path=str(B/'layout-short.png'));self.assertFalse(self.errors)
 def test_off_center_pointer_after_resize_and_context_draft(self):
  self.load('instruments');self.page.locator('#draft').fill('Retained Pearl draft / 文 🪷');self.page.locator('#draft').dispatch_event('input')
  selected=True
  for viewport in [{'width':1440,'height':700},{'width':420,'height':800}]:
   self.page.set_viewport_size(viewport);self.page.evaluate('nativeLab.draw()');r=self.page.locator('canvas').bounding_box();f=self.page.evaluate('()=>{const f=nativeLab.scene.render();return {width:f.width,height:f.height}}')
   self.page.mouse.click(r['x']+10.5*r['width']/f['width'],r['y']+28.5*r['height']/f['height']);selected=not selected
   self.assertEqual(self.page.evaluate('nativeLab.scene.info().widgets.find(w=>w.id===8).selected'),selected)
  self.page.locator('#scenes').select_option('pearl-curves');self.page.evaluate('nativeLab.hold();nativeLab.draw()');self.assertEqual(self.page.locator('#draft').input_value(),'Retained Pearl draft / 文 🪷');self.assertFalse(self.errors)
 def test_all_authored_palette_swatches_use_existing_native_material(self):
  self.load('instruments');palettes=json.loads((ROOT/'palettes.json').read_text())
  self.assertEqual(self.page.locator('#palette-swatches button').count(),len(palettes))
  self.page.locator('#palette-swatches').evaluate("e=>e.closest('details').open=true")
  for palette in palettes:
   button=self.page.locator('#palette-swatches button[data-palette="'+palette['id']+'"]');self.assertEqual(button.locator('[data-color]').evaluate_all("rows=>rows.map(e=>e.dataset.color)"),palette['colors']);button.click()
   command={'op':'material','id':1,'space':'indexed','colors':[int(c[1:],16) for c in palette['colors']],'scope':'characters','channels':{'i':{'initial':0,'step':.71,'rate':.15,'min':0,'max':len(palette['colors']),'boundary':'loop'}}};self.assertTrue(self.page.evaluate('command=>{const before=Array.from(nativeLab.scene.render().cells);nativeLab.scene.command(command);const after=nativeLab.scene.render().cells;return before.length===after.length&&before.every((v,i)=>v===after[i]);}',command));self.assertEqual(self.page.locator('#palette').input_value(),palette['id']);self.assertStageVisible()
  self.assertFalse(self.errors)
 def test_typing_weather_is_readback_driven_and_emits_actual_selected_kind(self):
  self.load('instruments');self.assertEqual(self.page.locator('#typing-weather').count(),1);self.assertTrue(self.page.locator('#typing-weather').is_disabled())
  self.load('rc2-windows-application');self.page.locator('#typing-weather').evaluate("e=>e.closest('details').open=true")
  self.assertFalse(self.page.locator('#typing-weather').is_disabled())
  for index,kind in enumerate(['embers','sparks','nova','rain','snow','ripples']):
   self.page.locator('#typing-weather').select_option(kind);self.page.locator('#draft').fill('Weather '+str(index)+' 文');self.page.locator('#draft').dispatch_event('input');app=self.page.evaluate('nativeLab.scene.info().windowApplication');self.assertEqual(app['weatherStyle'],kind);self.assertEqual(app['events'][-1]['kind'],kind)
  self.page.evaluate("nativeLab.scene.command({op:'window-application',weatherStyle:'snow'});nativeLab.draw()");self.assertEqual(self.page.locator('#typing-weather').input_value(),'snow');self.assertFalse(self.errors)
if __name__=='__main__':unittest.main()
