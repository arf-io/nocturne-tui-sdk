"""Actual original thermal geometry, Projector and painter against public frames."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,json,os,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.constructed_dynamic_legacy_snapshot import construct_dynamic_legacy_snapshot
from native.tests.historical_reference import load_rc2_workbench
EFFECTS={'embers':'weather/thermal-cinders','leaves':'weather/autumn-drift'}
CASES=[(120,60,[0,10,45],0,0,0,60,[0,0,0]),(32,96,[8,9,48],12,-4,17,120,[3,1,-2]),(192,24,[-2,5,38],-5,6,-8,30,[-4,2,1])]
def commands(case):
 w,h,position,yaw,pitch,roll,fov,origin=case
 return [{'op':'resize','width':w,'height':h},{'op':'prompt','active':False},{'op':'environment','stars':0,'style':'solid','background':0x101923,'presentation':'canvas'},{'op':'floor','enabled':False,'visible':False},{'op':'camera','position':position,'yaw':yaw,'pitch':pitch,'roll':roll,'fov':fov,'near':.1,'far':2000}]
def configured(kind=None,patch=None,case=CASES[0],alpha=1):
 s=NativeScene(2030)
 for c in commands(case):s.command(c)
 if kind:
  s.command({'op':'emitter','id':1,'effect':EFFECTS[kind],'position':case[-1],'count':0,'alpha':alpha,'runningTimeMs':0});s.command({'op':'thermal-style','id':1,**(patch or {})})
 return s
class ThermalOriginalIntegration(unittest.TestCase):
 def test_public_original_every_cell_native_and_wasm(self):
  requests=[];actual=[];metadata=[]
  for kind in EFFECTS:
   for case in CASES:
    for seed in (2030,4294967295):
     patch={'seed':seed}
     with configured(kind,patch,case) as s,configured(case=case) as base:
      for us in (0,90000,750000,2000000,6499000,6500000):
       s.advance_to(us);base.advance_to(us);before=s.snapshot();actual.append(list(memoryview(s.render().bytes).cast('I')));self.assertEqual(before,s.snapshot());metadata.append(s.info_complete()['emitters'][0]['thermalSource'])
       w,h,pos,yaw,pitch,roll,fov,origin=case
       requests.append({'name':f'{kind}-{w}x{h}-{seed}-{us}','kind':kind,'effect':EFFECTS[kind],'baseCommands':commands(case),'origin':origin,'camera':dict(x=pos[0],y=pos[1],z=pos[2],yaw=yaw,pitch=pitch,roll=roll,fov=fov,near=.1,far=2000),'timeMs':us/1000,'options':patch,'width':w,'height':h,'cells':list(memoryview(base.render().bytes).cast('I'))})
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'original.html').write_text(load_rc2_workbench());(p/'requests.json').write_text(json.dumps(requests))
   ref=subprocess.run(['node',str(ROOT/'tests/original_thermal_paint_oracle.mjs'),str(p/'original.html'),str(p/'requests.json')],capture_output=True,text=True);self.assertEqual(ref.returncode,0,ref.stderr);expected=json.loads(ref.stdout)
   run=subprocess.run(['node',str(ROOT/'tests/thermal_original_integration_wasm.mjs'),str(p/'requests.json')],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);wasm=json.loads(run.stdout)
  if os.environ.get('NOCTURNE_THERMAL_EVIDENCE'):
   p=Path(os.environ['NOCTURNE_THERMAL_EVIDENCE']);p.mkdir(parents=True,exist_ok=True)
   for name,data in [('requests',requests),('original',expected),('native',actual),('wasm',wasm),('metadata',metadata)]:
    with gzip.open(p/(name+'.json.gz'),'wt') as f:json.dump(data,f,separators=(',',':'))
  for request,want,got,w,meta in zip(requests,expected,actual,wasm,metadata):
   with self.subTest(case=request['name']):
    diff=[(i,a,b) for i,(a,b) in enumerate(zip(want['cells'],got)) if a!=b];self.assertEqual(diff,[],f'{len(diff)} mismatched words; first={diff[:8]}');self.assertEqual(w,want['cells'],'Public WASM cells differ from original')
    self.assertEqual(meta['projectedSegmentsCount'],len(want['projected']))
    for a,b in zip(meta['projectedSegments'],want['projected'][:16]):
     for x,y in zip(a,b):self.assertAlmostEqual(x,y,delta=5e-5)
 def test_mode_replay_and_semantic_epoch_rejects_atomically(self):
  with configured('leaves') as s:
   self.assertEqual(s.info_complete()['emitters'][0]['thermalSource']['paint'],'source');s.advance_to(750000);source=s.render().bytes;saved=s.snapshot()
   old=construct_dynamic_legacy_snapshot(saved,0x20261078)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),saved);s.command({'op':'thermal-style','id':1,'paint':'material'});self.assertNotEqual(s.render().bytes,source);old=construct_dynamic_legacy_snapshot(s.snapshot(),0x20261078);frame=s.render().bytes
   s.restore(old);self.assertEqual(s.render().bytes,frame)
   self.assertEqual(s.info_complete()['emitters'][0]['thermalSource']['paint'],'material');s.restore(saved);self.assertEqual(s.render().bytes,source)
   with self.assertRaises(ValueError):s.command({'op':'thermal-style','id':1,'paint':'unsupported'})
   self.assertEqual(s.snapshot(),saved)
 def test_alpha_remains_additive(self):
  with configured('leaves') as full,configured('leaves',alpha=.4) as partial,configured('leaves',alpha=0) as zero,configured() as base:
   for s in (full,partial,zero,base):s.advance_to(750000)
   self.assertNotEqual(full.render().bytes,partial.render().bytes);self.assertNotEqual(partial.render().bytes,base.render().bytes);self.assertEqual(zero.render().bytes,base.render().bytes)
if __name__=='__main__':unittest.main()
