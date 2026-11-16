"""Real browser/current native Pearl data/controller workflow; no historical renderer."""
from pathlib import Path
import os,unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=Path(os.environ.get('NOCTURNE_PEARL_GALLERY_PATH',ROOT/'Nocturne-Test-Harness.html'))
class PearlDataGallery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=True)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def setUp(self):
  self.page=self.browser.new_page(viewport={'width':1440,'height':900});self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.set_content(HTML.read_text());self.page.wait_for_function('window.nativeLab');self.page.evaluate('nativeLab.hold()')
 def tearDown(self):self.page.close()
 def load(self,identity):
  self.assertEqual(self.page.locator('#scenes option[value="'+identity+'"]').count(),1,'actual normal original recipe');self.page.locator('#scenes').select_option(identity);self.page.evaluate('nativeLab.hold();nativeLab.draw()')
 def state(self):return self.page.evaluate('nativeLab.pearlSession().snapshot()')
 def test_normal_studio_47ms_every_commit_hold_and_detach(self):
  self.load('pearl-studio-original');self.assertEqual(self.state()['data']['value'],670)
  self.page.evaluate('nativeLab.advance(46000)');self.assertEqual(self.state()['data']['dataCount'],0)
  self.page.evaluate('nativeLab.advance(1000)');self.assertEqual(self.state()['data']['value'],431)
  before=self.state();self.page.wait_for_timeout(180);self.assertEqual(self.state(),before)
  self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');self.page.locator('#pearl-studio-value').fill('123');self.assertEqual(self.state()['data']['value'],123)
  self.page.evaluate('nativeLab.advance(47000)');self.assertEqual(self.state()['data']['value'],505)
  self.assertTrue(self.page.evaluate('()=>{const a=nativeLab.scene.snapshot();nativeLab.draw();nativeLab.draw();const b=nativeLab.scene.snapshot();return a.every((v,i)=>v===b[i]);}'))
  self.page.locator('#save').evaluate("e=>e.closest('details').open=true")
  with self.page.expect_download() as download:self.page.locator('#save').click()
  self.page.locator('#snapshot-file').set_input_files(download.value.path());self.page.wait_for_function('nativeLab.pearlSession()===null');self.assertFalse(self.errors)
 def test_normal_fleet_actual_native_click_drafts_send_history_and_settings(self):
  self.load('pearl-fleet-original');self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');self.assertEqual(self.state()['demoTick'],96)
  self.page.evaluate('nativeLab.advance(80000)');self.assertEqual(self.state()['demoTick'],97)
  self.page.locator('#pearl-fleet-open').click();self.page.evaluate('nativeLab.advance(560000)');self.assertTrue(self.state()['source']['semantics']['agentId'])
  self.page.locator('#pearl-fleet-draft').fill('Original source draft 👩‍💻');self.page.locator('#pearl-fleet-draft').dispatch_event('input');self.page.locator('#pearl-fleet-send').click();self.assertEqual(len(self.state()['commands']),1)
  self.page.evaluate('nativeLab.advance(80000)');self.assertEqual(len(self.state()['commands']),0);self.assertTrue(self.state()['replies'])
  self.page.locator('#pearl-fleet-dense').check();self.assertTrue(self.state()['options']['dense']);self.page.locator('#pearl-fleet-read').check();self.assertEqual(self.state()['source']['timeMs'],0)
  self.page.locator('#pearl-fleet-close').click();self.page.locator('#pearl-fleet-read').uncheck();self.page.locator('#pearl-fleet-dense').uncheck();self.page.evaluate('nativeLab.advance(560000);nativeLab.draw()')
  target=self.page.evaluate("()=>{const n=nativeLab.pearlSession().compose().nodes.find(n=>n.id>=1000&&n.id<1032);return {x:n.x+1,y:n.y+1};}");r=self.page.locator('canvas').bounding_box();frame=self.page.evaluate('()=>{const f=nativeLab.scene.render();return {width:f.width,height:f.height}}');self.page.mouse.click(r['x']+target['x']*r['width']/frame['width'],r['y']+target['y']*r['height']/frame['height']);self.assertTrue(self.page.evaluate('nativeLab.pearlSession().fleet.opened'));self.assertFalse(self.errors)
 def test_existing_instruments_source_buses_and_lower_reference_are_actual_native_data(self):
  self.load('instruments');self.page.evaluate('nativeLab.advance(1703000);nativeLab.draw()')
  value=self.page.evaluate('nativeLab.pearlSignals()');self.assertEqual(value['sample']['dataMs'],1700);self.assertEqual(len(value['sample']['reference']),128);self.assertEqual(len(value['sample']['bus']),3);self.assertEqual(value['studio']['dataCount'],36)
  self.assertEqual(self.page.evaluate('nativeLab.scene.info().widgets.find(w=>w.id===65000).data.length'),128)
  self.page.locator('#pearl-data-source').evaluate("e=>e.closest('details').open=true");self.page.locator('#pearl-data-source').select_option('authored');self.assertEqual(self.page.evaluate('nativeLab.scene.info().widgets.find(w=>w.id===65000).alpha'),0);self.assertFalse(self.errors)

 def test_fleet_unbounded_actual_input_and_owned_checkpoint_restore(self):
  self.load('pearl-fleet-original');self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');text='文👩‍💻é'.join(['long']*10002);self.assertGreater(len(text),65536)
  self.page.locator('#pearl-fleet-draft').fill(text);self.assertEqual(self.state()['draft'],text)
  with self.page.expect_download() as download:self.page.locator('#pearl-fleet-save').click()
  path=download.value.path();self.page.locator('#pearl-fleet-draft').fill('changed');self.page.locator('#pearl-fleet-file').set_input_files(path);self.page.wait_for_function("(text)=>nativeLab.pearlSession().fleet.draft===text || document.getElementById('error').textContent",arg=text);self.assertEqual(self.page.locator('#error').text_content(),'')
  self.assertEqual(self.state()['draft'],text);before=self.state();self.page.locator('#pearl-fleet-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"schema":"bad"}'});self.page.wait_for_timeout(80);self.assertEqual(self.state(),before)
  self.page.locator('#pearl-fleet-send').click();self.assertEqual(self.state()['commands'][-1]['text'],text);self.assertIn(text,self.state()['source']['semantics']['transcript']);self.assertFalse(self.errors)

 def test_observatory_all16_normal_original_scenes_and_live_clock(self):
  identities=['chat','scope','warp','dag','spatial-menu','bbs','bbs-config','windows','lynx','nano','pico','tmux','controls','sensors','logs','text']
  for identity in identities:
   self.load('pearl-observatory-'+identity);self.assertEqual(self.state()['model']['scene'],identity);self.assertEqual(self.page.evaluate('nativeLab.scene.info().windowApplication.scene'),'observatory');self.assertTrue(self.page.evaluate('()=>{const a=nativeLab.scene.snapshot();nativeLab.draw();const b=nativeLab.scene.snapshot();return a.every((v,i)=>v===b[i]);}'))
  self.load('pearl-observatory-scope');self.page.evaluate('nativeLab.advance(125000)');self.assertEqual(self.state()['model']['dataMs'],100);self.assertEqual(self.state()['model']['sensorSeq'],2);self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');self.page.locator('#pearl-observer-motion').uncheck();self.page.evaluate('nativeLab.advance(100000)');self.assertEqual(self.state()['model']['motionMs'],125);self.assertEqual(self.state()['model']['dataMs'],200);self.assertFalse(self.errors)
 def test_observatory_real_input_checkpoint_scratch_native_hit_and_bus_routes(self):
  self.load('pearl-observatory-chat');self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');text='文👩‍💻é'.join(['note']*10002);self.assertGreater(len(text),65536);self.page.locator('#pearl-observer-draft').fill(text);self.assertEqual(self.state()['model']['draft'],text)
  with self.page.expect_download() as download:self.page.locator('#pearl-observer-save').click()
  self.page.locator('#pearl-observer-draft').fill('changed');self.page.locator('#pearl-observer-file').set_input_files(download.value.path());self.page.wait_for_function('(text)=>nativeLab.pearlSession().model.draft===text',arg=text);self.assertEqual(self.state()['model']['draft'],text);self.page.locator('#pearl-observer-send').click();self.assertEqual(self.state()['model']['messages'][-1]['text'],'YOU: '+text)
  self.page.locator('#pearl-observer-scenes').select_option('nano');self.page.locator('#pearl-observer-editor').fill(text);self.assertEqual(self.state()['model']['editor'],text)
  self.page.locator('#pearl-observer-scenes').select_option('sensors');self.page.locator('#pearl-observer-bind-demo').evaluate("e=>e.closest('details').open=true");self.page.locator('#pearl-observer-bind-demo').click();self.page.evaluate('nativeLab.advance(100000)');self.assertEqual(self.state()['model']['bus']['bindings'][0]['source'],'demo.audio');self.assertNotEqual(self.page.evaluate('nativeLab.pearlSession().model.effective().brightness'),.28)
  self.page.locator('#pearl-observer-scenes').select_option('windows');node=self.page.evaluate('nativeLab.pearlSession().compose().nodes.find(n=>n.id===2200)');r=self.page.locator('canvas').bounding_box();frame=self.page.evaluate('()=>{const f=nativeLab.scene.render();return {width:f.width,height:f.height}}');self.page.mouse.click(r['x']+(node['x']+.5)*r['width']/frame['width'],r['y']+(node['y']+.5)*r['height']/frame['height']);self.assertEqual(self.state()['model']['windows'][0]['mode'],'collapsed');self.assertFalse(self.errors)

 def test_observatory_actual_web_audio_synthetic_stream_and_cleanup(self):
  self.load('pearl-observatory-sensors');self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');self.assertEqual(self.page.locator('#pearl-observer-microphone').count(),1);self.assertEqual(self.page.locator('#pearl-observer-display-audio').count(),1)
  self.page.locator('#play').evaluate("e=>{const details=e.closest('details');if(details)details.open=true}");self.page.locator('#play').click()
  result=self.page.evaluate("""async()=>{const context=new AudioContext(),osc=context.createOscillator(),gain=context.createGain(),destination=context.createMediaStreamDestination();gain.gain.value=.2;osc.frequency.value=440;osc.connect(gain).connect(destination);await context.resume();osc.start();await nativeLab.observerAudio().attach(destination.stream,{prefix:'audio.synthetic-test',quality:'synthetic',label:'SYNTHETIC / actual browser oscillator'});window.__actualAudio={context,osc,destination};return destination.stream.getAudioTracks().length;}""");self.assertEqual(result,1)
  self.page.wait_for_function("()=>{const m=nativeLab.pearlSession().model;return m.bus.samples.has('audio.synthetic-test.rms')&&m.bus.samples.get('audio.synthetic-test.rms').value>0.01}")
  values=self.page.evaluate("()=>{const m=nativeLab.pearlSession().model;return {samples:[...m.bus.samples.values()].filter(s=>s.source.startsWith('audio.synthetic-test.')),wave:m.waveform,label:m.sourceLabel}}")
  self.assertEqual(len(values['samples']),5);self.assertTrue(all(s['quality']=='synthetic' for s in values['samples']));self.assertTrue(any(abs(v)>.01 for v in values['wave']));self.assertIn('SYNTHETIC',values['label'])
  self.page.evaluate('nativeLab.hold()');before=self.page.evaluate("nativeLab.pearlSession().model.bus.samples.get('audio.synthetic-test.rms').seq");self.page.wait_for_timeout(90);self.assertEqual(self.page.evaluate("nativeLab.pearlSession().model.bus.samples.get('audio.synthetic-test.rms').seq"),before)
  self.page.locator('#pearl-observer-stop-audio').evaluate("e=>e.closest('details').open=true");self.page.locator('#pearl-observer-stop-audio').click();self.page.wait_for_function('nativeLab.observerAudio().active===null');self.assertEqual(self.page.evaluate('__actualAudio.destination.stream.getTracks()[0].readyState'),'ended');self.page.evaluate('__actualAudio.osc.stop();__actualAudio.context.close()');self.assertFalse(self.errors)

 def test_observatory_all_options_and_held_motion_step(self):
  self.load('pearl-observatory-scope');missing=self.page.evaluate("Object.keys(nativeLab.pearlSession().model.options).filter(k=>!document.getElementById('pearl-observer-'+k))");self.assertEqual(missing,[])
  self.page.locator('#pearl-live-panel').evaluate('e=>e.open=true');self.page.evaluate('nativeLab.advance(125000)');self.page.locator('#pearl-observer-motion').uncheck();self.page.evaluate('nativeLab.advance(100000)');before=self.state()['elapsedMs'];self.page.locator('#step').evaluate("e=>{const details=e.closest('details');if(details)details.open=true}");self.page.locator('#step').click();self.assertGreater(self.state()['elapsedMs'],before);self.assertEqual(self.page.locator('#error').text_content(),'');self.assertFalse(self.errors)
 def test_observatory_invalid_audio_source_closes_actual_supplied_stream(self):
  self.load('pearl-observatory-sensors');result=self.page.evaluate("""async()=>{const context=new AudioContext(),destination=context.createMediaStreamDestination();let rejected=false;try{await nativeLab.observerAudio().attach(destination.stream,{prefix:'invalid source'});}catch{rejected=true;}const value={rejected,states:destination.stream.getTracks().map(t=>t.readyState),active:nativeLab.observerAudio().active};await context.close();return value;}""");self.assertTrue(result['rejected']);self.assertEqual(result['states'],['ended']);self.assertIsNone(result['active']);self.assertFalse(self.errors)
