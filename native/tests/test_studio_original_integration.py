"""Actual original Studio WASM raster and JavaScript tile composition."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,json,os,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.constructed_dynamic_legacy_snapshot import construct_dynamic_legacy_snapshot
from native.tests.historical_reference import load_rc2_workbench
BASE=[{'op':'resize','width':120,'height':72},{'op':'prompt','active':False},{'op':'environment','stars':0,'style':'solid','background':0x101923},{'op':'floor','enabled':False,'visible':False},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0}]
EFFECT='weather/pearl-bloom'
def configured(patch=None,base=BASE,alpha=1):
 s=NativeScene(2030)
 for c in base:s.command(c)
 if patch is not None:
  s.command({'op':'emitter','id':1,'effect':EFFECT,'position':[0,0,0],'count':0,'alpha':alpha,'runningTimeMs':0});s.command({'op':'studio-style','id':1,**patch})
 return s
class StudioOriginalIntegration(unittest.TestCase):
 def test_public_original_every_cell_native_and_wasm(self):
  requests=[];actual=[]
  variants=({}, {'rippleSpeed':2304,'rippleOpacity':700,'rippleRings':3,'strength':1000}, {'rippleSpeed':6000,'rippleWidth':900,'rippleOpacity':1000,'rippleRings':6,'cellAspect':500,'strength':1000,'palette':[0x00ddee,0xee2200,0x6622ff],'starPalette':[0xeeeecc,0xccffdd],'glyphs':'·*✦','waveScale':2048,'seed':71}, {'rippleOpacity':0,'glyphs':'界😀✧','palette':[0x224466],'starPalette':[0xaabbcc],'strength':0,'seed':2147483647}, {'rippleSpeed':262144,'rippleWidth':8192,'rippleRings':6,'cellAspect':4000,'waveScale':64,'strength':1000,'rippleOpacity':1000})
  for index,patch in enumerate(variants):
   commands=([{**BASE[0],'width':40}]+BASE[1:]) if index==2 else BASE
   with configured(patch,commands) as s,configured(base=commands) as base:
    for us in (0,1000,90000,432000,864000,1800000,3599000,3600000):
     s.advance_to(us);base.advance_to(us);before=s.snapshot();actual.append(list(memoryview(s.render().bytes).cast('I')));self.assertEqual(before,s.snapshot())
     center=s.info_complete()['emitters'][0]['studioNova']['center']
     requests.append({'name':f'{index}-{us}','effect':EFFECT,'baseCommands':commands,'center':center,'timeMs':us/1000,'options':patch,'width':commands[0]['width'],'height':commands[0]['height'],'cells':list(memoryview(base.render().bytes).cast('I'))})
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'original.html').write_text(load_rc2_workbench());(p/'requests.json').write_text(json.dumps(requests))
   ref=subprocess.run(['node',str(ROOT/'tests/original_studio_paint_oracle.mjs'),str(p/'original.html'),str(p/'requests.json')],capture_output=True,text=True);self.assertEqual(ref.returncode,0,ref.stderr);expected=json.loads(ref.stdout)
   run=subprocess.run(['node',str(ROOT/'tests/studio_original_integration_wasm.mjs'),str(p/'requests.json')],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);wasm=json.loads(run.stdout)
  if os.environ.get('NOCTURNE_STUDIO_EVIDENCE'):
   p=Path(os.environ['NOCTURNE_STUDIO_EVIDENCE']);p.mkdir(parents=True,exist_ok=True)
   for name,data in [('requests',requests),('original',expected),('native',actual),('wasm',wasm)]:
    with gzip.open(p/(name+'.json.gz'),'wt') as f:json.dump(data,f,separators=(',',':'))
  for request,want,got,w in zip(requests,expected,actual,wasm):
   with self.subTest(case=request['name']):
    diff=[(i,a,b) for i,(a,b) in enumerate(zip(want['cells'],got)) if a!=b]
    self.assertEqual(diff,[],f'{len(diff)} mismatched words; first={diff[:8]}');self.assertEqual(w,want['cells'],'Public WASM cells differ from original')
 def test_mode_replay_and_semantic_epoch_rejects_atomically(self):
  with configured({}) as s:
   self.assertEqual(s.info_complete()['emitters'][0]['studioNova']['paint'],'source');s.advance_to(864000);source=s.render().bytes;saved=s.snapshot()
   old=construct_dynamic_legacy_snapshot(saved,0x20261077)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),saved)
   s.command({'op':'studio-style','id':1,'paint':'material'});self.assertNotEqual(s.render().bytes,source);old=construct_dynamic_legacy_snapshot(s.snapshot(),0x20261077);frame=s.render().bytes
   s.restore(old);self.assertEqual(s.render().bytes,frame)
   self.assertEqual(s.info_complete()['emitters'][0]['studioNova']['paint'],'material');s.restore(saved);self.assertEqual(s.render().bytes,source)
   with self.assertRaises(ValueError):s.command({'op':'studio-style','id':1,'paint':'unsupported'})
   self.assertEqual(s.snapshot(),saved)
 def test_alpha_remains_additive(self):
  with configured({}) as full,configured({},alpha=.4) as partial,configured({},alpha=0) as zero,configured() as base:
   for s in (full,partial,zero,base):s.advance_to(864000)
   self.assertNotEqual(full.render().bytes,partial.render().bytes);self.assertNotEqual(partial.render().bytes,base.render().bytes);self.assertEqual(zero.render().bytes,base.render().bytes)
if __name__=='__main__':unittest.main()
