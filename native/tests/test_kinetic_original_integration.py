"""Public emitter rendering must retain the original per-heat palette and geometry."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench
EFFECTS={'embers':'weather/hearth-spray','sparks':'weather/branchlight','nova':'weather/chrysanthemum','rain':'weather/wire-rain','snow':'weather/pearl-flurry'}
# Keep this isolated emitter layer clear of native host chrome; whole original
# application layer ordering is covered by test_rc2_window_application.
BASE=[{'op':'resize','width':120,'height':72},{'op':'prompt','active':False},{'op':'environment','stars':0,'style':'solid','background':0x101923},{'op':'floor','enabled':False,'visible':False},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0}]
def configured(kind=None,patch=None):
 s=NativeScene(2030)
 for c in BASE:s.command(c)
 if kind:
  s.command({'op':'emitter','id':1,'effect':EFFECTS[kind],'position':[0,0,0],'count':0,'alpha':1,'runningTimeMs':0})
  s.command({'op':'kinetic-style','id':1,**(patch or {})})
 return s
class KineticOriginalIntegration(unittest.TestCase):
 def test_public_emitter_paints_original_every_cell(self):
  requests=[];actual=[]
  for kind in EFFECTS:
   for patch in ({},{'count':1,'branches':1,'arcSegments':3,'shockwave':.8,'seed':4294967295,'glyphs':'界','drag':0}):
    with configured(kind,patch) as s,configured() as base:
     for us in (90000,750000,2300000):
      s.advance_to(us);base.advance_to(us);before=s.snapshot();actual.append(list(memoryview(s.render().bytes).cast('I')));self.assertEqual(before,s.snapshot())
      center=s.info_complete()['emitters'][0]['kinetic']['center']
      requests.append({'name':f'{kind}-{patch}-{us}','kind':kind,'effect':EFFECTS[kind],'baseCommands':BASE,'event':{'kind':kind,'id':1,'x':center[0],'y':center[1],'atMs':0},'timeMs':us/1000,'options':patch,'weight':1,'width':120,'height':72,'cells':list(memoryview(base.render().bytes).cast('I'))})
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'original.html').write_text(load_rc2_workbench());(p/'requests.json').write_text(json.dumps(requests))
   r=subprocess.run(['node',str(ROOT/'tests/original_kinetic_weather_oracle.mjs'),str(p/'original.html'),str(p/'requests.json')],capture_output=True,text=True,check=True);expected=json.loads(r.stdout)
   r=subprocess.run(['node',str(ROOT/'tests/kinetic_original_integration_wasm.mjs'),str(p/'requests.json')],capture_output=True,text=True,check=True);wasm=json.loads(r.stdout)
  for request,want,got,wasm_frame in zip(requests,expected,actual,wasm):
   with self.subTest(case=request['name']):
    diff=[(i,a,b) for i,(a,b) in enumerate(zip(want['cells'],got)) if a!=b]
    self.assertEqual(diff,[],f'{len(diff)} mismatched words; first={diff[:8]}')
    self.assertEqual(wasm_frame,want['cells'],'actual public WASM cells differ from original')
  destination=os.environ.get('NOCTURNE_KINETIC_CAPTURE_DIR')
  if destination:
   p=Path(destination);p.mkdir(parents=True,exist_ok=True)
   rows=[{'id':r['name'],'effect':r['effect'],'width':r['width'],'height':r['height'],'request':r,'original':w['cells'],'native':n,'wasm':v} for r,w,n,v in zip(requests,expected,actual,wasm)]
   encoded=json.dumps(rows,separators=(',',':')).encode();(p/'frames.json.gz').write_bytes(gzip.compress(encoded,mtime=0))
   manifest={'sourceSha256':hashlib.sha256(load_rc2_workbench().encode()).hexdigest(),'nativeSha256':hashlib.sha256((ROOT/'dist/libnocturne_native.dylib').read_bytes()).hexdigest(),'wasmSha256':hashlib.sha256((ROOT/'dist/nocturne_native.wasm').read_bytes()).hexdigest(),'framesSha256':hashlib.sha256(encoded).hexdigest(),'cases':[{'id':r['id'],'effect':r['effect'],'originalSha256':hashlib.sha256(json.dumps(r['original'],separators=(',',':')).encode()).hexdigest(),'nativeSha256':hashlib.sha256(json.dumps(r['native'],separators=(',',':')).encode()).hexdigest(),'wasmSha256':hashlib.sha256(json.dumps(r['wasm'],separators=(',',':')).encode()).hexdigest()} for r in rows]}
   (p/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 def test_material_override_atomicity_and_snapshot(self):
  with configured('nova') as s:
   s.advance_to(90000);original=s.render().bytes;saved=s.snapshot()
   s.command({'op':'kinetic-style','id':1,'paint':'material'});self.assertNotEqual(s.render().bytes,original)
   s.restore(saved);self.assertEqual(s.render().bytes,original)
   with self.assertRaises(ValueError):s.command({'op':'kinetic-style','id':1,'paint':'unsupported'})
   self.assertEqual(s.snapshot(),saved)
   s.command({'op':'clear-instance','id':1});s.command({'op':'emitter','id':1,'effect':'weather/wire-rain','count':0});s.command({'op':'kinetic-style','id':1})
if __name__=='__main__':unittest.main()
