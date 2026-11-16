"""Retained BlackHoleRenderer.sky, actual model/engine and every output cell."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
from native.tests.test_rc2_window_compositions import original_runtime_source
from native.bindings.python.nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1]
START={'x':0,'y':0,'z':0,'yaw':-18,'pitch':8,'roll':12,'fov':70,'near':.1,'far':1000}
def base_commands():return [{'op':'resize','width':96,'height':36},{'op':'environment','stars':0,'background':0x070b14,'style':'solid','presentation':'canvas'},{'op':'prompt','active':False},{'op':'floor','visible':False},{'op':'camera','profile':'original','navigation':'fly','position':[0,0,0],**{k:v for k,v in START.items() if k not in ('x','y','z')}}]
def flight(speed):return {'op':'flight','profile':'original','cruise':{'speed':speed,'heading':{'yaw':28,'pitch':12}}}
def options(**patch):return dict(starProfile='source',worldSeed=2030,skyDensity=9,skyRadius=280,skyExposure=6500,trailMs=100,textLightness=.83,textChroma=.1,**patch)
class OriginalWorldSky(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True,args=['--no-sandbox']);cls.page=cls.browser.new_page()
  source=original_runtime_source().replace('return {BLACK_HOLE_CUSTOM_SCENES,segmentedGlyph,BlackHoleRenderer,activateBlackHole,runBlackHoleAction};','window.__sourceSky={BlackHoleModel,BlackHoleRenderer};return {BLACK_HOLE_CUSTOM_SCENES,segmentedGlyph,BlackHoleRenderer,activateBlackHole,runBlackHoleAction};')
  cls.page.set_content(source,wait_until='domcontentloaded');cls.page.wait_for_function('window.__sourceSky && window.fieldGuide')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def original(self,base,speed,time,opts):
  return self.page.evaluate("""r=>{const{BlackHoleModel,BlackHoleRenderer}=__sourceSky,m=new BlackHoleModel();m.resize(96,36);m.setScene('warp');m.camera.configure(r.start);m.configureBH({worldSeed:r.o.worldSeed,skyDensity:r.o.skyDensity,skyRadius:r.o.skyRadius,skyExposure:r.o.skyExposure});m.configure({trailMs:r.o.trailMs,textLightness:r.o.textLightness,textChroma:r.o.textChroma});m.flight.cruise(0,m.camera.snapshot(),r.speed,{yaw:28,pitch:12});m.motionMs=r.t/1000;m.camera.configure(m.flight.sample(m.motionMs));const render=new BlackHoleRenderer(fieldGuide.engine),o=m.effective();render.base.prepare(m.palette,o);const frame={width:96,height:36,cells:new Uint32Array(r.base)};render.sky(frame,m,o);return Array.from(frame.cells);}""",{'start':START,'base':base,'speed':speed,'t':time,'o':opts})
 def cases(self):
  result=[]
  for speed in [0,14,40]:
   for trail in [0,100,250]:
    o=options();o['trailMs']=trail
    result.append((f'speed{speed}-trail{trail}',speed,o,[0,1000000,3900000]))
  o=options();o.update(worldSeed=4294967295,skyDensity=18,skyRadius=360,skyExposure=30000,textLightness=.35,textChroma=.3)
  result.append(('max-controls',40,o,[2000000]))
  return result
 def assert_frame(self,actual,expected,key):
  capture=os.environ.get('NOCTURNE_SKY_CAPTURE_DIR')
  if capture:
   p=Path(capture);p.mkdir(parents=True,exist_ok=True);(p/(hashlib.sha256(key.encode()).hexdigest()[:20]+'.json.gz')).write_bytes(gzip.compress(json.dumps({'key':key,'width':96,'height':36,'original':expected,'actual':actual},separators=(',',':')).encode(),mtime=0))
  self.assertEqual(len(actual),len(expected));diff=[(i,a,b)for i,(a,b)in enumerate(zip(actual,expected))if a!=b];self.assertFalse(bool(diff),f'{key}: {len(diff)} differing words, first{diff[:5]}')
 def test_native_full_original_frames(self):
  for name,speed,o,times in self.cases():
   with self.subTest(name=name),NativeScene(2030) as scene:
    for c in base_commands():scene.command(c)
    base=list(memoryview(scene.render().bytes).cast('I'));scene.command({'op':'environment',**o});scene.command(flight(speed))
    for t in times:
     scene.advance_to(t);before=scene.snapshot();actual=list(memoryview(scene.render().bytes).cast('I'));self.assertEqual(before,scene.snapshot());self.assert_frame(actual,self.original(base,speed,t,o),f'native-{name}@{t}')
 def test_wasm_full_original_frames(self):
  with NativeScene(2030) as scene:
   for c in base_commands():scene.command(c)
   base=list(memoryview(scene.render().bytes).cast('I'))
  requests=[{'id':name,'commands':base_commands()+[{'op':'environment',**o},flight(speed)],'times':times}for name,speed,o,times in self.cases()]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'in.json').write_text(json.dumps(requests));subprocess.run(['node',str(ROOT/'tests/original_camera_wasm_runner.mjs'),str(p/'in.json'),str(p/'out.json')],check=True,capture_output=True)
   cases={x[0]:x for x in self.cases()}
   for r in json.loads((p/'out.json').read_text()):
    _,speed,o,_=cases[r['id']];self.assert_frame(r['words'],self.original(base,speed,r['timeUs'],o),f'wasm-{r["id"]}@{r["timeUs"]}')
 def test_controls_snapshot_atomicity_and_fast_trails(self):
  with NativeScene(2030) as scene:
   for c in base_commands():scene.command(c)
   scene.command({'op':'environment',**options()});scene.command(flight(40));scene.advance_to(3000000);frame=scene.render().bytes;saved=scene.snapshot();info=scene.info()['sourceSky'];self.assertEqual(info['worldSeed'],2030);self.assertEqual(info['trailMs'],100)
   scene.command({'op':'environment','trailMs':0});self.assertNotEqual(frame,scene.render().bytes);scene.restore(saved);self.assertEqual(scene.render().bytes,frame)
   for bad in [{'skyDensity':0},{'skyDensity':1.5},{'worldSeed':-1},{'skyRadius':361},{'trailMs':251},{'textChroma':.31},{'starProfile':'fake'}]:
    with self.assertRaises(ValueError):scene.command({'op':'environment',**bad})
    self.assertEqual(scene.snapshot(),saved)
   scene.command({'op':'environment','starProfile':'default'});self.assertIsNone(scene.info()['sourceSky'])
