import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'hosts/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import failure_record
from atelier_application import TEXT_TRANSITIONS,atelier_text_command
SHA='01500ccd3106f40a7f0b3e21fe4a580f1e0666980e998930feaf94bff730aced'
class OriginalAtelierText(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  source=gzip.decompress((ROOT/'tests/fixtures/original-atelier-spatial-v0.5.html.gz').read_bytes());assert hashlib.sha256(source).hexdigest()==SHA
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True);cls.page=cls.browser.new_page();cls.page.set_content(source.decode(),wait_until='domcontentloaded');cls.page.wait_for_function('window.atelierApp');cls.page.evaluate('atelierApp.stop()')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def test_original_18_painters_native_and_wasm(self):
  cases=[];actual=[];original=[]
  for effect in [k.split('/')[1] for k in TEXT_TRANSITIONS if k.startswith('atelier/')]:
   if os.environ.get('NOCTURNE_ATELIER_EFFECT') and effect!=os.environ['NOCTURNE_ATELIER_EFFECT']:continue
   for phase in ('show','hide'):
    for variant in (0,1):
     style=dict(textLightness=.83 if not variant else .71,textChroma=.1 if not variant else .18,hueOffset=0 if not variant else 103,hueStep=13 if not variant else -27,textHueSpeed=12 if not variant else -7)
     options=dict(effect=effect,durationMs=1200,delayMs=70 if variant else 0,staggerMs=28,batchSize=1 if not variant else 3,seed=6137 if not variant else 4294967295,travelRows=13,spreadColumns=8,drift=2,speedJitter=.55 if not variant else .95,alphabet=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!?+-*/',cycleHz=18,easing='smooth' if not variant else 'back',reverseOrder=bool(variant),randomOrder=bool(variant),trailLength=2 if not variant else 8,overshoot=1.2,turns=1.5,hueSpread=110,local=False)
     text='NØ✦aB' if not variant else 'A\nN✦\tZ'+''.join(chr(65+i%26) for i in range(90))
     common=[{'op':'resize','width':96,'height':48},{'op':'prompt','active':False},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'floor','visible':False}]
     material={'op':'material','id':15,'space':'oklch','scope':'characters','channels':{'l':style['textLightness'],'c':style['textChroma'],'h':{'initial':style['hueOffset'],'rate':style['textHueSpeed'],'min':0,'max':360,'boundary':'loop'}},'hueStep':style['hueStep'],'alpha':1}
     command={'op':'text','id':1,'text':text,'effect':TEXT_TRANSITIONS['atelier/'+effect],'phase':phase,'phaseModel':'source-paint','x':9,'y':22,'width':86,'material':15,**{k:v for k,v in options.items() if k in ('seed','durationMs','delayMs','staggerMs','batchSize','alphabet','easing','reverseOrder','randomOrder','trailLength','overshoot','hueSpread')},'distance':13,'scatter':8,'wind':2,'variation':options['speedJitter'],'scrambleHz':18,'cycles':1.5}
     with NativeScene(2030) as scene,NativeScene(2030) as base:
      for target in (scene,base):
       for c in common:target.command(c)
      scene.command(material);scene.command(command)
      for ms in (0,425,1100,6000):
       scene.advance_to(ms*1000);base.advance_to(ms*1000);before=scene.snapshot();words=list(memoryview(scene.render().bytes).cast('I'));self.assertEqual(scene.snapshot(),before)
       request=dict(name=f'{effect}-{phase}-{variant}-{ms}',commands=[*common,material,command],text=text,phase=phase,timeMs=ms,options=options,style=style,width=96,height=48,cells=list(memoryview(base.render().bytes).cast('I')))
       wanted=self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();Object.assign(m.options,r.style);m.motionMs=r.timeMs;atelierApp.renderer.base.prepare(m.palette,m.options);let f={width:r.width,height:r.height,cells:Uint32Array.from(r.cells)};const poses=MODULES.text_fx.sampleText(r.text,r.phase,r.timeMs,r.options);atelierApp.renderer.paintText(f,r.text,poses,9,22,m);return Array.from(f.cells)}""",request)
       different=[(i,a,b) for i,(a,b) in enumerate(zip(words,wanted)) if a!=b]
       if different:failure_record('atelier-text-failure.json',dict(request=request,actual=words,original=wanted))
       self.assertEqual(len(different),0,request['name']+': '+str(different[:12]));cases.append(request);actual.append(words);original.append(wanted)
  with tempfile.TemporaryDirectory() as d:
   request=Path(d)/'cases.json';request.write_text(json.dumps(cases));run=subprocess.run(['node',str(ROOT/'tests/source_text_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(request)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);wasm=json.loads(run.stdout)
  self.assertEqual(len(wasm),len(cases))
  for c,a,b in zip(cases,wasm,original):
   different=[i for i,(x,y) in enumerate(zip(a['cells'],b)) if x!=y];self.assertEqual(len(a['cells']),len(b));self.assertEqual(len(different),0,c['name']+' WASM: '+str(different[:12]))
  if os.environ.get('NOCTURNE_ATELIER_TEXT_CAPTURE'):
   p=Path(os.environ['NOCTURNE_ATELIER_TEXT_CAPTURE']);p.mkdir(parents=True,exist_ok=True);p.joinpath('frames.json.gz').write_bytes(gzip.compress(json.dumps([dict(request=c,native=a,original=b,wasm=w['cells']) for c,a,b,w in zip(cases,actual,original,wasm)],separators=(',',':')).encode(),mtime=0))
 def test_original_routes(self):
  for effect in [k for k in TEXT_TRANSITIONS if k.startswith('atelier/')]:self.assertEqual(atelier_text_command('Original',effect)['phaseModel'],'source-paint')
  sys.path.insert(0,str(ROOT/'examples'));from gallery_cases import build_cases
  routes=[c for c in build_cases() if (c.get('sourceIdentity')or'').startswith('text/atelier/')]
  self.assertEqual(len(routes),36)
  for case in routes:
   q=next(c for c in case['commands'] if c['op']=='text' and c['id']==1)
   self.assertEqual(q['phaseModel'],'source-paint');self.assertEqual(q['seed'],6137);self.assertEqual(q['material'],15);self.assertEqual(q['durationMs'],1200)
class OriginalAtelierTextBrowser(unittest.TestCase):
 def test_normal_picker_selects_all_original_atelier_painters(self):
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True)
   try:
    page=browser.new_page(reduced_motion='reduce');page.goto(Path(os.environ.get('NOCTURNE_ORIGINAL_GALLERY',ROOT/'Nocturne-RC4-Source-Build.html')).resolve().as_uri());page.wait_for_function('window.nativeLab');page.get_by_text('Native effect catalogue • all port identities',exact=True).click()
    for effect in [k for k in TEXT_TRANSITIONS if k.startswith('atelier/')]:
     page.select_option('#effect',TEXT_TRANSITIONS[effect]);page.click('#effect-peak');info=page.evaluate('nativeLab.scene.infoComplete()');self.assertEqual(info['clock']['timeUs'],900000)
     q=next(t for t in info['textRuns'] if t['id']==1);self.assertEqual(q['phaseModel'],'source-paint');self.assertEqual(q['seed'],6137)
   finally:browser.close()
if __name__=='__main__':unittest.main()
