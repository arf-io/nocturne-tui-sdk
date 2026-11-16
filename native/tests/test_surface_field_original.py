"""All four original ripple artworks through actual public native and WASM."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.constructed_dynamic_legacy_snapshot import construct_dynamic_legacy_snapshot
from native.tests.historical_reference import load_rc2_workbench
EFFECTS={'studio':('surface-field/silk-tide',3600),'observatory':('surface-field/satin-rings',3200),'kinetic':('surface-field/opal-fronts',5000),'atelier':('surface-field/interference-tide',4200)}
def base_commands(w,h):return [{'op':'resize','width':w,'height':h},{'op':'prompt','active':False},{'op':'environment','stars':0,'presentation':'canvas','style':'solid','background':0x101923},{'op':'floor','enabled':False,'visible':False}]
def oracle(requests):
 with tempfile.TemporaryDirectory(prefix='surface-original-') as td:
  d=Path(td);(d/'original.html').write_text(load_rc2_workbench());(d/'requests.json').write_text(json.dumps(requests));r=subprocess.run(['node',str(ROOT/'tests/original_surface_field_oracle.mjs'),str(d/'original.html'),str(d/'requests.json')],capture_output=True,text=True,check=True);return json.loads(r.stdout)
class SurfaceFieldOriginal(unittest.TestCase):
 def test_genuine_source86_snapshot_native_and_wasm(self):
  folder=ROOT/'evidence/surface-original-20261014';receipt=json.loads((folder/'source86.json').read_text());old=gzip.decompress((folder/'source86.snapshot.gz').read_bytes());frame=gzip.decompress((folder/'source86.frame.gz').read_bytes())
  self.assertEqual(hashlib.sha256(old).hexdigest(),receipt['snapshotSha256']);self.assertEqual(hashlib.sha256(frame).hexdigest(),receipt['frameSha256']);self.assertEqual(struct.unpack_from('<I',old,12)[0],0x20261086)
  with NativeScene(2030) as scene:
   scene.restore(old);saved=scene.snapshot();self.assertEqual(scene.render().bytes,frame);self.assertEqual(scene.snapshot(),saved);self.assertEqual([v['paint'] for v in scene.info()['fields']],['source']*4)
  with tempfile.TemporaryDirectory() as td:
   native=Path(td)/'native.snapshot';native.write_bytes(saved)
   run=subprocess.run(['node',str(ROOT/'tests/source_field_snapshot_migration.mjs'),str(folder),str(native),str(ROOT/'dist/nocturne_native.wasm')],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout)['status'],'PASS')
 def test_actual_previous_source_optics_is_not_original_painter(self):
  requests=[];actual=[]
  for backend,(effect,life) in EFFECTS.items():
   with NativeScene(2030) as scene,NativeScene(2030) as base:
    for c in base_commands(120,72):scene.command(c);base.command(c)
    scene.command({'op':'field','effect':effect,'optics':'source','x':60,'y':36});scene.advance_to(750000);base.advance_to(750000)
    requests.append(dict(name=backend,backend=backend,lifeMs=life,eventId=1,seed=2030,timeMs=750,width=120,height=72,x=60,y=36,cells=list(memoryview(base.render().bytes).cast('I'))));actual.append(list(memoryview(scene.render().bytes).cast('I')))
  expected=oracle(requests)
  for q,w,a in zip(requests,expected,actual):self.assertNotEqual(w['cells'],a,q['name']+' prior optics already original')
 def test_original_studio_default_ring_metadata(self):
  with NativeScene(2030) as scene:
   scene.command({'op':'field','effect':'surface-field/silk-tide','paint':'source'});self.assertEqual(scene.info()['fields'][0]['rings'],3)
 def test_source_controls_reject_values_outside_actual_original_domains(self):
  for effect,patch in [('silk-tide',{'width':.05}),('silk-tide',{'speed':.001}),('silk-tide',{'lifeMs':99}),('silk-tide',{'lifeMs':30001}),('satin-rings',{'width':2}),('interference-tide',{'width':2})]:
   with self.subTest(effect=effect,patch=patch),NativeScene(2030) as scene:
    before=scene.snapshot()
    with self.assertRaises(ValueError):scene.command({'op':'field','effect':'surface-field/'+effect,'paint':'source',**patch})
    self.assertEqual(before,scene.snapshot())
 def test_lifecycle_atomic_inputs_snapshot_and_old_epoch(self):
  import zlib
  for backend,(effect,life) in EFFECTS.items():
   with self.subTest(backend=backend),NativeScene(2030) as scene:
    for c in base_commands(96,54):scene.command(c)
    # Positive control: the constructed prior physical layout must load without source paint.
    ordinary=scene.snapshot();compatible=construct_dynamic_legacy_snapshot(ordinary,0x20261078);scene.restore(compatible);self.assertEqual(scene.snapshot(),ordinary)
    baseline=scene.render().bytes;scene.command({'op':'field','effect':effect,'paint':'source','x':40,'y':22});scene.advance_to(750000)
    self.assertEqual(scene.info()['fields'][0]['paint'],'source');snapshot=scene.snapshot();frame=scene.render().bytes;self.assertEqual(snapshot,scene.snapshot());self.assertNotEqual(frame,baseline)
    for patch in [{'paint':'bad'},{'paint':True},{'optics':'legacy'},{'material':2},{'continuous':True},{'frequency':2},{'phase':30},{'interference':.2},{'falloff':3}]:
     with self.assertRaises(ValueError):scene.command({'op':'field','effect':effect,'paint':'source',**patch})
     self.assertEqual(snapshot,scene.snapshot())
    old=construct_dynamic_legacy_snapshot(snapshot,0x20261078)
    with self.assertRaises(ValueError):scene.restore(old)
    self.assertEqual(snapshot,scene.snapshot());scene.command({'op':'remove-field','id':1});self.assertFalse(scene.info()['fields']);scene.restore(snapshot);self.assertEqual(scene.render().bytes,frame)
    scene.advance_to(life*1000);self.assertEqual(scene.render().bytes,baseline)
 def test_source_bit_does_not_change_sampler_and_native_velocity_clip(self):
  for backend,(effect,life) in EFFECTS.items():
   with self.subTest(backend=backend),NativeScene(2030) as moving,NativeScene(2030) as fixed,NativeScene(2030) as clipped,NativeScene(2030) as baseline,NativeScene(2030) as sampled:
    for scene in [moving,fixed,clipped,baseline,sampled]:
     for c in base_commands(100,60):scene.command(c)
    command={'op':'field','effect':effect,'paint':'source','x':40,'y':22,'seed':13}
    moving.command({**command,'velocity':[8,4]});fixed.command({**command,'x':46,'y':25});clipped.command({**command,'x':36,'y':15,'surface':{'x':10,'y':10,'width':40,'height':25}})
    # Compare the public equation sampler with the same exact accepted controls.
    entry=fixed.info()['fields'][0];sampled.command({'op':'field','effect':effect,'optics':'source','paint':'field','x':46,'y':25,'lifeMs':life,'speed':{'studio':9,'observatory':12,'kinetic':48,'atelier':20}[backend],'width':{'studio':1.5,'observatory':1.7,'kinetic':.25,'atelier':1.2}[backend],'strength':{'studio':1,'observatory':.6,'kinetic':.85,'atelier':.8}[backend],'seed':13,**({'rings':3} if backend=='studio' else {})})
    self.assertEqual(entry['rings'],sampled.info()['fields'][0]['rings'])
    for scene in [moving,fixed,clipped,baseline,sampled]:scene.advance_to(750000)
    a=moving.render().bytes;b=fixed.render().bytes;self.assertEqual(a,b)
    for x,y in [(46,25),(50,25),(53,28)]:self.assertEqual(fixed.field_sample(1,x,y),sampled.field_sample(1,x,y))
    cut=clipped.render().bytes;under=baseline.render().bytes
    for y in range(60):
     for x in range(100):
      index=(y*100+x)*16;self.assertEqual(cut[index:index+16],(b if 10<=x<50 and 10<=y<35 else under)[index:index+16])
 def test_normal_catalogue_routes_select_original_paint(self):
  sys.path.insert(0,str(ROOT/'examples'));from gallery_cases import build_cases
  cases=build_cases();routes=[c for c in cases if c.get('catalogueEffect') in {e[0] for e in EFFECTS.values()}];self.assertEqual(len(routes),8)
  for case in routes:
   field=next(c for c in case['commands'] if c['op']=='field' and c['effect']==case['catalogueEffect']);self.assertEqual(field.get('paint'),'source')
   self.assertTrue(any(c['id']==case['id']+'-legacy' for c in cases))
 def test_four_original_painters_complete_native_wasm_frames(self):
  requests=[];actual=[]
  variations={'studio':{'lifeMs':4000,'speed':13,'width':2,'rings':4,'strength':.6,'seed':377},'observatory':{'lifeMs':5000,'speed':18,'strength':.35,'seed':377},'kinetic':{'lifeMs':6000,'speed':24,'strength':.6,'seed':4294967295},'atelier':{'lifeMs':5400,'speed':13,'strength':.5,'seed':4294967295}}
  for backend,(effect,default_life) in EFFECTS.items():
   for width,height,x,y in [(120,72,60,36),(96,54,31.25,25.75),(48,30,2.5,3.5)]:
    for version,patch in enumerate([{},variations[backend]]):
     life=patch.get('lifeMs',default_life)
     with NativeScene(2030) as scene,NativeScene(2030) as base:
      commands=base_commands(width,height)+[{'op':'field','effect':effect,'optics':'source','paint':'source','x':x,'y':y,**patch}]
      for c in commands:scene.command(c)
      for c in commands[:-1]:base.command(c)
      for ms in [0,90,425,750,1600,life-1,life]:
       scene.advance_to(ms*1000);base.advance_to(ms*1000);before=scene.snapshot();actual.append(list(memoryview(scene.render().bytes).cast('I')));self.assertEqual(before,scene.snapshot())
       requests.append(dict(name=f'{backend}-{width}x{height}-{version}-{ms}',backend=backend,effect=effect,lifeMs=life,eventId=patch.get('seed',1) if backend in ['studio','observatory'] else 1,seed=patch.get('seed',2030),timeMs=ms,width=width,height=height,x=x,y=y,controls=patch,commands=commands,cells=list(memoryview(base.render().bytes).cast('I'))))
  expected=oracle(requests)
  with tempfile.TemporaryDirectory(prefix='surface-wasm-') as td:
   p=Path(td)/'request.json';p.write_text(json.dumps(requests));r=subprocess.run(['node',str(ROOT/'tests/source_field_original_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(p)],capture_output=True,text=True,check=True);wasm=json.loads(r.stdout)
  mismatches=[]
  for q,w,n,b in zip(requests,expected,actual,wasm):
   for backend,got in [('native',n),('wasm',b)]:
    self.assertEqual(len(got),len(w['cells']));diff=[(i,a,c) for i,(a,c) in enumerate(zip(w['cells'],got)) if a!=c]
    if diff:mismatches.append((q['name'],backend,len(diff),diff[:4]))
  if os.environ.get('NOCTURNE_SURFACE_EVIDENCE'):
   d=Path(os.environ['NOCTURNE_SURFACE_EVIDENCE']);d.mkdir(parents=True,exist_ok=True)
   for name,value in [('requests',requests),('original',expected),('native',actual),('wasm',wasm)]: (d/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(value,separators=(',',':')).encode(),mtime=0))
   (d/'comparison.json').write_text(json.dumps({'cases':len(requests),'mismatches':mismatches},indent=2)+'\n')
  self.assertEqual(mismatches,[])
if __name__=='__main__':unittest.main()
