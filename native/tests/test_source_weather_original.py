"""Actual original Kinetic JS/WASM versus current C weather sampler and painter."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C
import hashlib,json,os,platform,subprocess,tempfile,unittest,shutil,gzip,struct
from pathlib import Path
from native.tests.historical_reference import load_rc2_workbench
ROOT=Path(__file__).resolve().parents[1]
FIELDS='count lifeMs launchSpeed gravity drag wind flickerHz trailMs branches arcSegments arcJitter coreMs shockwave explosionForce seed brightness emberSpread arcReach'.split()
DEFAULTS=[52,5000,12,8,.65,1.2,18,90,5,10,1.2,260,0,48,2030,.85,5,17]
KINDS=['embers','sparks','nova','rain','snow','ripples']
def cases():
 out=[]
 for kind in KINDS:
  variants=[{}, {'count':160,'seed':4294967295,'glyphs':'🜁·+⣿','drag':0,'trailMs':400,'shockwave':.8},
    {'count':1,'branches':12,'arcSegments':24,'coreMs':0,'brightness':.4,'wind':-20,'gravity':40,'arcJitter':6,'emberSpread':20,'arcReach':45,'explosionForce':70}]
  for vi,options in enumerate(variants):
   for ms in ([0,50,149,150,259,260,519,520,1200,4999,5000] if vi==0 else [10,750,2300]):
    w,h=64,24;cells=[]
    for i in range(w*h):cells += [[0x2580,0x2584,0x28ff,32,ord('A')][i%5],0x284f7a+(i%32),0x101923+(i%16),i%19]
    out.append(dict(name=f'{kind}-{vi}-{ms}',event=dict(kind=kind,id=6137,x=32.25 if vi!=2 else -4.2,y=12.75,atMs=100),timeMs=ms+100,options=options,weight=.73,width=w,height=h,cells=cells))
 # Every original public control at both domain endpoints, in a family it affects.
 bounds={'count':(1,160,'nova'),'lifeMs':(100,12000,'nova'),'launchSpeed':(0,40,'embers'),'gravity':(0,40,'embers'),'drag':(0,5,'nova'),'wind':(-20,20,'snow'),'flickerHz':(0,60,'sparks'),'trailMs':(0,400,'nova'),'branches':(1,12,'sparks'),'arcSegments':(3,24,'sparks'),'arcJitter':(0,6,'sparks'),'coreMs':(0,1500,'nova'),'shockwave':(0,1,'nova'),'explosionForce':(1,70,'nova'),'seed':(0,4294967295,'nova'),'brightness':(0,1,'nova'),'emberSpread':(0,20,'embers'),'arcReach':(1,45,'sparks')}
 for field,(lo,hi,kind) in bounds.items():
  for value in (lo,hi):
   c=dict(out[0]);c['name']=f'endpoint-{field}-{value}';c['options']={field:value};c['event']={**c['event'],'kind':kind,'x':32,'y':12};c['timeMs']=100+(value/2 if field=='lifeMs' else 750);out.append(c)
 for kind in KINDS:
  for eid in [0,.25,4294967295,9007199254740991]:
   c=dict(out[0]);c['name']=f'event-id-{kind}-{eid}';c['options']={};c['event']={**c['event'],'kind':kind,'id':eid,'x':32,'y':12};c['timeMs']=875;out.append(c)
 for kind in KINDS:
  c=dict(out[0]);c['name']=f'not-yet-born-{kind}';c['options']={};c['event']={**c['event'],'kind':kind};c['timeMs']=99;out.append(c)
 return out
def layer_cases():
 out=[];base=cases()[0]
 for ms in [0,19999,20000,20500,24999,25000,40000,40500]:
  for many in [False,True]:
   c={k:v for k,v in base.items() if k not in ('event','weight')};c['name']=f'layer-{ms}-{many}';c['timeMs']=ms
   c['events']=[dict(kind=KINDS[i%6],id=i,x=8+i,y=7+i%10,atMs=ms-1200 if ms>=1200 else 0) for i in range(32)] if many else []
   c['layer']=dict(weatherIntensity=.38,novaStrength=.28,novaRegularity=3);out.append(c)
 return out
class OriginalWeather(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='nr-original-weather-');cls.tmp=Path(cls.temp.name)
  original=cls.tmp/'original.html';original.write_text(load_rc2_workbench())
  cls.cases=cases();cls.layers=layer_cases();request=cls.tmp/'requests.json';request.write_text(json.dumps(cls.cases+cls.layers))
  r=subprocess.run(['node',str(ROOT/'tests/original_kinetic_weather_oracle.mjs'),str(original),str(request)],capture_output=True,text=True)
  if r.returncode:raise AssertionError(r.stderr)
  originals=json.loads(r.stdout);cls.reference=originals[:len(cls.cases)];cls.layer_reference=originals[len(cls.cases):]
  suffix='.dylib' if platform.system()=='Darwin' else '.so';lib=cls.tmp/('weather'+suffix)
  src=['source_weather.c','math.c'];cmd=['cc','-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-fPIC','-dynamiclib' if suffix=='.dylib' else '-shared','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src')]
  r=subprocess.run(cmd+[str(ROOT/'src'/s) for s in src]+[str(ROOT/'tests/source_weather_probe.c'),'-o',str(lib)],capture_output=True,text=True)
  if r.returncode:raise AssertionError(r.stdout+r.stderr)
  cls.lib=C.CDLL(str(lib));cls.probe=cls.lib.nrSourceWeatherProbe
  cls.probe.argtypes=[C.c_uint32,C.POINTER(C.c_double),C.POINTER(C.c_double),C.POINTER(C.c_uint32),C.c_uint32,C.c_double,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.POINTER(C.c_double)]
  cls.layer_probe=cls.lib.nrSourceWeatherLayerProbe
  cls.layer_probe.argtypes=[C.POINTER(C.c_uint32),C.POINTER(C.c_double),C.c_uint32,C.c_double,C.POINTER(C.c_double),C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_double),C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32)]
  cls.wasm=cls.tmp/'weather.wasm';clang=os.environ.get('WASM_CC') or shutil.which('clang');ld=os.environ.get('WASM_LD') or shutil.which('wasm-ld')
  if not clang or not ld:raise AssertionError('WASM clang and wasm-ld required')
  objects=[]
  for source in [ROOT/'src'/name for name in ('source_weather.c','math.c','wasm_mem.c')]+[ROOT/'tests/source_weather_probe.c']:
   obj=cls.tmp/(source.stem+'.o');cmd=[clang,'--target=wasm32','-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-nostdlib','-ffreestanding','-fno-builtin','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'freestanding'),'-c',str(source),'-o',str(obj)];r=subprocess.run(cmd,capture_output=True,text=True)
   if r.returncode:raise AssertionError(r.stdout+r.stderr)
   objects.append(str(obj))
  r=subprocess.run([ld,'--no-entry','--export-memory','--export=nrSourceWeatherProbe','--export=nrSourceWeatherLayerProbe','--export=nrAlloc','--stack-first','-z','stack-size=1048576','--initial-memory=16777216',*objects,'-o',str(cls.wasm)],capture_output=True,text=True)
  if r.returncode:raise AssertionError(r.stdout+r.stderr)
  wasm_request=cls.tmp/'wasm-request.json';wasm_request.write_text(json.dumps([{**c,'wheel':w['wheel']} for c,w in zip(cls.cases+cls.layers,cls.reference+cls.layer_reference)]))
  r=subprocess.run(['node',str(ROOT/'tests/source_weather_wasm.mjs'),str(cls.wasm),str(wasm_request)],capture_output=True,text=True)
  if r.returncode:raise AssertionError(r.stderr)
  cls.wasm_results=json.loads(r.stdout)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def native(self,c,wheel):
  o=dict(zip(FIELDS,DEFAULTS));o.update(c['options']);glyphs=list(map(ord,o.get('glyphs','·∙⋅*+⠁⠂⠄')))
  vals=(C.c_double*18)(*[o[k] for k in FIELDS]);e=c['event'];event=(C.c_double*5)(e['id'],e['x'],e['y'],e['atMs'],c['timeMs'])
  cells=(C.c_uint32*len(c['cells']))(*c['cells']);sample=(C.c_double*4096)()
  rc=self.probe(KINDS.index(e['kind']),event,vals,(C.c_uint32*len(glyphs))(*glyphs),len(glyphs),c['weight'],(C.c_uint32*360)(*wheel),c['width'],c['height'],cells,sample)
  self.assertEqual(rc,0);n=int(sample[0]);m=int(sample[1]);return list(cells),list(sample)[:5+6*n+7*m]
 def test_original_sample_and_every_painted_cell(self):
  captured=[]
  for c,want in zip(self.cases,self.reference):
   with self.subTest(case=c['name']):
    cells,sample=self.native(c,want['wheel']);s=want['sample'];flat=[len(s['points']),len(s['segments']),s['core'],s['radius'],s['shockwave']]
    for p in s['points']:flat += [p['x'],p['y'],p['opacity'],p['heat'],p['size'],ord(p['glyph'])]
    for p in s['segments']:flat += [p['x1'],p['y1'],p['x2'],p['y2'],p['opacity'],p['heat'],p['branch']]
    self.assertEqual(len(sample),len(flat))
    for at,(a,b) in enumerate(zip(sample,flat)):self.assertAlmostEqual(a,b,delta=2e-10*max(1,abs(b)),msg=f'{c["name"]} sample field {at}')
    different=[i for i,(a,b) in enumerate(zip(cells,want['cells'])) if a!=b]
    self.assertEqual(different,[],f'{c["name"]}: {len(different)} differing words; first {[(i,cells[i],want["cells"][i]) for i in different[:12]]}')
    captured.append(dict(name=c['name'],request=c,original=want,native=dict(cells=cells,sample=sample)))
  if os.environ.get('NOCTURNE_WEATHER_EVIDENCE'):
   directory=Path(os.environ['NOCTURNE_WEATHER_EVIDENCE']);directory.mkdir(parents=True,exist_ok=True)
   for c,w in zip(captured,self.wasm_results):c['wasm']=w
   raw=json.dumps(captured,separators=(',',':')).encode();(directory/'frames.json.gz').write_bytes(gzip.compress(raw,mtime=0))
   selected=[c for c in captured if c['name'] in {f'{k}-0-{ms}' for k in KINDS for ms in (50,1200)}]
   manifest=[]
   for c in selected:
    for source in ('original','native','wasm'):
     data=struct.pack('<'+'I'*len(c[source]['cells']),*c[source]['cells']);name=c['name']+'-'+source+'.cells';(directory/name).write_bytes(data);manifest.append(dict(name=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
   (directory/'frames-manifest.json').write_text(json.dumps(dict(singleEventFrames=len(captured),sourceOriginalHtmlSha256='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385',rawArchiveSha256=hashlib.sha256((directory/'frames.json.gz').read_bytes()).hexdigest(),files=manifest),indent=2)+'\n')

 def test_original_layer_event_order_and_automatic_nova(self):
  for c,want in zip(self.layers,self.layer_reference):
   with self.subTest(case=c['name']):
    es=c['events'];events=(C.c_double*max(1,len(es)*4))(*[v for e in es for v in (e['id'],e['x'],e['y'],e['atMs'])]);kinds=(C.c_uint32*max(1,len(es)))(*[KINDS.index(e['kind']) for e in es]);glyphs=list(map(ord,'·∙⋅*+⠁⠂⠄'));cells=(C.c_uint32*len(c['cells']))(*c['cells']);o=c['layer']
    rc=self.layer_probe(kinds,events,len(es),c['timeMs'],(C.c_double*18)(*DEFAULTS),(C.c_uint32*8)(*glyphs),8,(C.c_double*3)(o['weatherIntensity'],o['novaStrength'],o['novaRegularity']),(C.c_uint32*360)(*want['wheel']),c['width'],c['height'],cells)
    self.assertEqual(rc,want['count']);different=[i for i,(a,b) in enumerate(zip(cells,want['cells'])) if a!=b];self.assertEqual(different,[],f'{c["name"]} differing words {different[:12]}')
 def test_import_free_wasm_matches_original_every_painted_cell(self):
  for c,want,actual in zip(self.cases+self.layers,self.reference+self.layer_reference,self.wasm_results):
   with self.subTest(case=c['name']):
    self.assertEqual(actual['rc'],want['count'] if 'events' in c else 0)
    different=[i for i,(a,b) in enumerate(zip(actual['cells'],want['cells'])) if a!=b]
    self.assertEqual(different,[],f'{c["name"]} WASM differing words {different[:12]}')
    if 'event' in c:
     _,native=self.native(c,want['wheel']);self.assertEqual(actual['sample'],native,'native/WASM arithmetic differs')
 def test_invalid_input_preserves_frame(self):
  bounds={'count':(1,160),'lifeMs':(100,12000),'launchSpeed':(0,40),'gravity':(0,40),'drag':(0,5),'wind':(-20,20),'flickerHz':(0,60),'trailMs':(0,400),'branches':(1,12),'arcSegments':(3,24),'arcJitter':(0,6),'coreMs':(0,1500),'shockwave':(0,1),'explosionForce':(1,70),'seed':(0,4294967295),'brightness':(0,1),'emberSpread':(0,20),'arcReach':(1,45)}
  invalid=[{field:v} for field,(lo,hi) in bounds.items() for v in (lo-1,hi+1,float('nan'),float('inf'))]+[{field:1.5} for field in ('count','branches','arcSegments','seed')]
  for patch in invalid:
   with self.subTest(patch=patch):
    c=self.cases[0];o=dict(zip(FIELDS,DEFAULTS));o.update(patch);cells=(C.c_uint32*len(c['cells']))(*c['cells']);sample=(C.c_double*4096)(*([123]*4096));e=c['event'];event=(C.c_double*5)(e['id'],e['x'],e['y'],e['atMs'],c['timeMs'])
    rc=self.probe(0,event,(C.c_double*18)(*[o[k] for k in FIELDS]),(C.c_uint32*1)(65),1,.5,(C.c_uint32*360)(*self.reference[0]['wheel']),c['width'],c['height'],cells,sample)
    self.assertEqual(rc,-1);self.assertEqual(list(cells),c['cells']);self.assertEqual(list(sample),[123]*4096)
if __name__=='__main__':unittest.main()
