"""Actual original Atelier application particle frames through public native/WASM."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from native.tests.presentation_copy_reference import assert_snapshot_presentation
from native.tests.host_environment import failure_record
from native.tests import test_original_atelier_windows as windows
from playwright.sync_api import sync_playwright
NativeScene=windows.NativeScene;ROOT=windows.ROOT
class AtelierApplicationParticles(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True);cls.page=cls.browser.new_page();cls.page.set_content(windows.current_presentation(gzip.decompress((ROOT/'tests/fixtures/original-atelier-spatial-v0.5.html.gz').read_bytes()).decode(),'atelier'));cls.page.wait_for_function('window.atelierApp');cls.page.evaluate('atelierApp.stop()')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def original(self,events,time,options,cadence):
  return self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');m.particleConfig=MODULES.particles.particleOptions(r.options);m.configure({novaRegularity:r.cadence});m.events=r.events;m.setTime(r.time/1000);return Array.from(atelierApp.renderer.render(m).frame.cells)}""",dict(events=events,time=time,options=options,cadence=cadence))
 def test_invalid_controls_atomic_and_snapshot(self):
  with NativeScene(2030) as scene:
   for c in windows.commands():scene.command(c)
   invalid=[dict(count=-1),dict(count=257),dict(count=.5),dict(branches=0),dict(branches=21),dict(seed=-1),dict(seed=4294967296),dict(seed=.5),dict(reducedMotion=1),dict(unknown=1),dict(lifeMs=199),dict(lifeMs=10001),dict(speed=-1),dict(speed=71),dict(gravity=36),dict(rise=41),dict(drag=3.1),dict(turbulence=8.1),dict(glitterHz=0),dict(glitterHz=31),dict(trailMs=401),dict(jaggedness=8.1),dict(coreMs=601),dict(coreRadius=6.1),dict(ejecta=2.1),dict(shockwave=1.1),dict(intensity=1.1)]
   for options in invalid:
    before=scene.snapshot()
    with self.assertRaises(ValueError):scene.command(dict(op='window-application',atelierParticles=options))
    self.assertEqual(scene.snapshot(),before)
   scene.command(dict(op='window-application-event',kind='nova',id=17,x=24.5,y=6.25));scene.advance_to(175000);snapshot=scene.snapshot();frame=scene.render().bytes
   self.assertEqual(scene.info()['windowApplication']['atelierParticles']['seed'],4711)
   self.assertEqual(scene.info()['windowApplication']['weatherStyle'],'sparks')
   for style in ('embers','sparks','nova','rain','snow','ripples'):
    scene.command(dict(op='window-application',weatherStyle=style));self.assertEqual(scene.info()['windowApplication']['weatherStyle'],style)
   before=scene.snapshot()
   with self.assertRaises(ValueError):scene.command(dict(op='window-application',weatherStyle='invalid'))
   self.assertEqual(scene.snapshot(),before)
   with NativeScene(1) as restored:restored.restore(snapshot);self.assertEqual(restored.render().bytes,frame)
   scene.command(dict(op='remove-window-application'));self.assertIsNone(scene.info()['windowApplication'])
 def test_original_viewport_endpoints_auto_nova(self):
  captures=[]
  for width,height in [(36,18),(120,60),(240,100)]:
   commands=windows.commands()
   for c in commands:
    if c['op']=='resize':c.update(width=width,height=height)
    if c['op']=='camera':c['position'][2]*=width/136
    if c['op']=='window' and 'position' in c:c['position'][0]+=(136-width)/2;c['position'][1]+=height-44
   commands.append(dict(op='window-application',novaRegularity=60,atelierParticles=dict(shockwave=1)))
   original=self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(r.width,r.height);m.setScene('windows');m.configure({novaRegularity:60});m.particleConfig=MODULES.particles.particleOptions({shockwave:1});m.setTime(1250);return Array.from(atelierApp.renderer.render(m).frame.cells)}""",dict(width=width,height=height));expected=windows.map_hits(original)
   with NativeScene(2030) as scene:
    for c in commands:scene.command(c)
    scene.advance_to(1250000);actual=list(memoryview(scene.render().bytes).cast('I'));diff=[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b];self.assertEqual(len(actual),len(expected));self.assertEqual(diff,[],str((width,height,diff[:12])))
   captures.append(dict(name='viewport-'+str(width)+'x'+str(height),commands=commands,actions=[],timeUs=1250000,expected=expected))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cases.json';p.write_text(json.dumps(captures));run=subprocess.run(['node',str(ROOT/'tests/atelier_windows_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(p)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);actual=json.loads(run.stdout)
  for case,frame in zip(captures,actual):self.assertEqual(frame,case['expected'],case['name'])
 def test_genuine_schema82_snapshot_frame_and_metadata(self):
  f=ROOT/'tests/fixtures';name='original-schema82-atelier-particles';m=json.loads((f/(name+'.json')).read_text());snapshot=gzip.decompress((f/(name+'.snapshot.gz')).read_bytes());frame=gzip.decompress((f/(name+'.cells.gz')).read_bytes())
  self.assertEqual(hashlib.sha256(snapshot).hexdigest(),m['snapshotSha256']);self.assertEqual(hashlib.sha256(frame).hexdigest(),m['frameSha256'])
  with NativeScene(5) as scene:
   scene.restore(snapshot);assert_snapshot_presentation(self,scene,frame);self.assertEqual(scene.info()['windowApplication']['weatherStyle'],'rain');self.assertEqual(scene.info()['windowApplication']['atelierParticles']['seed'],4294967295)
 def test_input_helpers_match_original_model(self):
  helper=r'''#include "internal.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){State*s=calloc(1,sizeof(*s));s->schema=NR_STATE_SCHEMA;s->width=136;s->height=44;s->timeUs=1000000;s->windowApplication.enabled=1;s->windowApplication.scene=2;s->windowApplication.eventSerial=6;s->windowApplication.reserved=(uint32_t)strtoul(argv[2],0,10);
int handled=argv[1][0]=='i'?nrWindowApplicationInput(s,strtoull(argv[3],0,10),strtoull(argv[4],0,10)):nrWindowApplicationDraft(s,strtoull(argv[3],0,10),strtoull(argv[4],0,10),strtoull(argv[5],0,10),strtoll(argv[6],0,10));
printf("{\"handled\":%d,\"events\":[",handled);for(unsigned i=0;i<s->windowApplication.eventCount;i++){NrSourceWeatherEvent*e=&s->windowApplication.events[i];printf("%s[%.0f,%.0f,%.0f,%.0f,%u]",i?",":"",e->id,e->x,e->y,e->atMs,e->kind);}puts("]}");free(s);return 0;}'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'input.c';p.write_text(helper);binary=Path(d)/'input';build=subprocess.run(['cc','-I'+str(ROOT/'src'),'-I'+str(ROOT/'include'),str(p),str(ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')),'-Wl,-rpath,'+str(ROOT/'dist'),'-o',str(binary)],capture_output=True,text=True);self.assertEqual(build.returncode,0,build.stderr)
   cases=[('input','', 'hello'),('input','😀ab','🌑𐀀x'),('input','a'*123,'b'*70),('input','abc',''),('draft','abc','abc'),('draft','',''),('draft','abc','a'),('draft','😀','ab'),('draft','ab','😀'),('draft','abcd','abX'),('draft','😀ab','😀'),('draft','','hello')]
   for style in ('embers','sparks','nova','rain','snow','ripples'):
    for op,old,new in cases:
     expected=self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');m.configure({weatherStyle:r.style});m.draft=r.old;m.setTime(1000);m[r.op==='input'?'input':'replaceDraft'](r.next);return m.events.map(e=>[e.id,e.x,e.y,e.atMs,['embers','sparks','nova','rain','snow','ripples'].indexOf(e.kind)])}""",dict(op=op,old=old,next=new,style=style))
     difference=next((i for i,ch in enumerate(old) if i>=len(new) or ch!=new[i]),-1)
     counts=[len(old),len(new)] if op=='input' else [len(old.encode('utf-16-le'))//2,len(new.encode('utf-16-le'))//2,len(new),difference]
     args=[str(binary),op,str(('embers','sparks','nova','rain','snow','ripples').index(style)+1),*[str(n) for n in counts]]
     run=subprocess.run(args,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);actual=json.loads(run.stdout);self.assertEqual(actual,dict(handled=1,events=expected),(style,op,old,new))
 def test_original_all_families_fullframes_and_event_order(self):
  variants=[({},(22,7)),({'shockwave':1,'coreRadius':6,'coreMs':600,'count':128,'ejecta':1.5,'trailMs':250},(69.5,4.25)),({'speed':0,'gravity':0,'rise':0,'drag':0,'turbulence':0,'glitterHz':1,'intensity':.35,'branches':1,'jaggedness':0},(128,30)),({'reducedMotion':True},(54,37))]
  cases=[]
  for kind in ('embers','sparks','nova','rain','snow','ripples'):
   for variant,(options,xy) in enumerate(variants):
    events=[dict(id=19.5,x=xy[0],y=xy[1],atMs=0,kind=kind,glyph='x')]
    for time in (0,100000,700000,2100000,4199000,4200000):cases.append(dict(name=kind+'-'+str(variant)+'-'+str(time),events=events,timeUs=time,options=options,cadence=0))
  events=[dict(id=i+1,x=3+i*4.1,y=5+i%4,atMs=i*10,kind=('embers','sparks','nova','rain','snow')[i%5],glyph='x') for i in range(25)]
  for time in (0,250000,1000000,4200000,9000000):cases.append(dict(name='queue-'+str(time),events=events,timeUs=time,options={},cadence=0))
  for cadence in (3,30,60):
   for time in (1000000,2500000,20000000,21500000):cases.append(dict(name='cadence-'+str(cadence)+'-'+str(time),events=[],timeUs=time,options={'shockwave':.7},cadence=cadence))
  bounds={'lifeMs':(200,10000),'count':(0,256),'speed':(0,70),'gravity':(0,35),'rise':(0,40),'drag':(0,3),'turbulence':(0,8),'glitterHz':(1,30),'trailMs':(0,400),'branches':(1,20),'jaggedness':(0,8),'coreMs':(0,600),'coreRadius':(0,6),'ejecta':(0,2),'shockwave':(0,1),'intensity':(0,1),'seed':(0,4294967295)}
  for name,values in bounds.items():
   kind='nova' if name in ('count','ejecta','coreMs','coreRadius','shockwave','lifeMs') else 'sparks' if name in ('branches','jaggedness','glitterHz') else 'embers'
   for value in values:cases.append(dict(name='bound-'+name+'-'+str(value),events=[dict(id=123,x=24.5,y=6.25,atMs=0,kind=kind)],timeUs=100000 if name.startswith('core') else 175000,options={name:value},cadence=0))
  for name,event,time in [('signed-id',dict(id=-987654321.5,x=24.5,y=6.25,atMs=0,kind='nova'),700000),('negative-birth',dict(id=17,x=24.5,y=6.25,atMs=-300,kind='embers'),100000),('far-positive',dict(id=1,x=1e12,y=1e12,atMs=0,kind='nova'),100000),('far-negative',dict(id=1,x=-1e12,y=-1e12,atMs=0,kind='nova'),100000),('future-birth',dict(id=1,x=24,y=6,atMs=5000,kind='nova'),100000),('ripples-source-fallback',dict(id=1,x=24,y=6,atMs=0,kind='ripples'),700000)]:cases.append(dict(name=name,events=[event],timeUs=time,options={},cadence=0))
  if os.environ.get('NOCTURNE_ATELIER_PARTICLE_CASE'):cases=[c for c in cases if c['name'].startswith(os.environ['NOCTURNE_ATELIER_PARTICLE_CASE'])]
  captures=[]
  for case in cases:
   commands=windows.commands();commands.append(dict(op='window-application',atelierParticles=case['options'],novaRegularity=case['cadence']))
   commands.extend(dict(op='window-application-event',**{k:v for k,v in e.items() if k!='glyph'}) for e in case['events'])
   with NativeScene(2030) as scene:
    for c in commands:scene.command(c)
    scene.advance_to(case['timeUs']);before=scene.snapshot();actual=list(memoryview(scene.render().bytes).cast('I'));self.assertEqual(scene.snapshot(),before)
    original=self.original(case['events'],case['timeUs'],case['options'],case['cadence']);expected=windows.map_hits(original);diff=[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    if diff:failure_record('atelier-particles-failure.json',dict(case=case,actual=actual,original=original,expected=expected))
    self.assertEqual(diff,[],case['name']+' '+str(diff[:12]));captures.append(dict(case=dict(name=case['name'],commands=commands,actions=[],timeUs=case['timeUs']),original=original,expected=expected,native=actual))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cases.json';p.write_text(json.dumps([c['case'] for c in captures]));run=subprocess.run(['node',str(ROOT/'tests/atelier_windows_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(p)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);actual=json.loads(run.stdout)
  self.assertEqual(len(actual),len(captures))
  for c,w in zip(captures,actual):self.assertEqual(w,c['expected'],c['case']['name']);c['wasm']=w
  destination=os.environ.get('NOCTURNE_ATELIER_PARTICLES_CAPTURE')
  if destination:
   p=Path(destination);p.mkdir(parents=True,exist_ok=True);(p/'frames.json.gz').write_bytes(gzip.compress(json.dumps(captures,separators=(',',':')).encode(),mtime=0))
if __name__=='__main__':unittest.main()
