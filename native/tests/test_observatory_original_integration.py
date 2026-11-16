"""Every public frame word against the actual original Observatory painter and WASM palette."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,os,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.constructed_dynamic_legacy_snapshot import construct_dynamic_legacy_snapshot
from native.tests.historical_reference import load_rc2_workbench
EFFECTS={'sparks':'weather/pinfire','embers':'weather/lantern-motes','rain':'weather/rain-threads','snow':'weather/snow-dust'}
BASE=[{'op':'resize','width':120,'height':72},{'op':'prompt','active':False},{'op':'environment','stars':0,'style':'solid','background':0x101923,'presentation':'canvas'},{'op':'floor','enabled':False,'visible':False},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0}]
def configured(kind=None,patch=None,base=BASE,alpha=1):
 s=NativeScene(2030)
 for c in base:s.command(c)
 if kind:
  s.command({'op':'emitter','id':1,'effect':EFFECTS[kind],'position':[0,0,0],'count':0,'alpha':alpha,'runningTimeMs':0});s.command({'op':'observatory-style','id':1,**(patch or {})})
 return s
class ObservatoryOriginalIntegration(unittest.TestCase):
 def test_public_original_every_cell_native_and_wasm(self):
  requests=[];actual=[]
  for kind in EFFECTS:
   for size in ((120,72),(32,96),(192,24)):
    for patch in ({'seed':2030,'speed':12,'intensity':.6,'durationMs':3200},{'seed':4294967295,'speed':42,'intensity':1,'durationMs':4200}):
     commands=[{**BASE[0],'width':size[0],'height':size[1]}]+BASE[1:]
     with configured(kind,patch,commands) as s,configured(base=commands) as base:
      for us in (0,90000,425000,1700000,patch['durationMs']*1000):
       s.advance_to(us);base.advance_to(us);before=s.snapshot();actual.append(list(memoryview(s.render().bytes).cast('I')));self.assertEqual(before,s.snapshot())
       center=s.info_complete()['emitters'][0]['observatory']['center']
       requests.append({'name':f'{kind}-{patch}-{us}','kind':kind,'effect':EFFECTS[kind],'baseCommands':commands,'center':center,'timeMs':us/1000,'options':patch,'width':commands[0]['width'],'height':commands[0]['height'],'cells':list(memoryview(base.render().bytes).cast('I'))})
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'original.html').write_text(load_rc2_workbench());(p/'requests.json').write_text(json.dumps(requests))
   expected=json.loads(subprocess.run(['node',str(ROOT/'tests/original_observatory_paint_oracle.mjs'),str(p/'original.html'),str(p/'requests.json')],capture_output=True,text=True,check=True).stdout)
   wasm=json.loads(subprocess.run(['node',str(ROOT/'tests/observatory_original_integration_wasm.mjs'),str(p/'requests.json')],capture_output=True,text=True,check=True).stdout)
  if os.environ.get('NOCTURNE_OBSERVATORY_EVIDENCE'):
   p=Path(os.environ['NOCTURNE_OBSERVATORY_EVIDENCE']);p.mkdir(parents=True,exist_ok=True)
   for name,data in [('requests',requests),('original',expected),('native',actual),('wasm',wasm)]:
    with gzip.open(p/(name+'.json.gz'),'wt') as f:json.dump(data,f,separators=(',',':'))
  for request,want,got,w in zip(requests,expected,actual,wasm):
   with self.subTest(case=request['name']):
    diff=[(i,a,b) for i,(a,b) in enumerate(zip(want['cells'],got)) if a!=b]
    self.assertEqual(diff,[],f'{len(diff)} mismatched words; first={diff[:8]}')
    self.assertEqual(w,want['cells'],'Public WASM cells differ from original')
 def test_material_override_atomicity_and_snapshot(self):
  with configured('sparks') as s:
   self.assertEqual(s.info_complete()['emitters'][0]['observatory']['paint'],'source')
   s.advance_to(90000);original=s.render().bytes;saved=s.snapshot();s.command({'op':'observatory-style','id':1,'paint':'material'});self.assertNotEqual(s.render().bytes,original)
   material=s.snapshot();material_frame=s.render().bytes;self.assertEqual(s.info_complete()['emitters'][0]['observatory']['paint'],'material');s.restore(material);self.assertEqual(s.render().bytes,material_frame)
   s.restore(saved);self.assertEqual(s.render().bytes,original)
   old=construct_dynamic_legacy_snapshot(saved,0x20261081)
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),saved)
   old=construct_dynamic_legacy_snapshot(material,0x20261081);s.restore(old);self.assertEqual(s.render().bytes,material_frame);s.restore(saved)
   with self.assertRaises(ValueError):s.command({'op':'observatory-style','id':1,'paint':'unsupported'})
   self.assertEqual(s.snapshot(),saved)
 def test_native_alpha_is_additive_and_zero_leaves_destination(self):
  with configured('sparks') as s,configured() as base,configured('sparks',alpha=.35) as partial,configured('sparks',alpha=0) as zero:
   for scene in (s,base,partial,zero):scene.advance_to(90000)
   self.assertNotEqual(partial.render().bytes,s.render().bytes);self.assertNotEqual(partial.render().bytes,base.render().bytes)
   self.assertEqual(zero.render().bytes,base.render().bytes)
if __name__=='__main__':unittest.main()
