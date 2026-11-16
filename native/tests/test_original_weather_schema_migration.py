"""Genuine standalone artwork fixtures through the combined public ABI."""
import gzip,hashlib,json,os,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
EVIDENCE=ROOT/'evidence/recovery-20261014/schema-migration'
CASES=json.loads((EVIDENCE/'readback-receipts.json').read_text())['cases']
LIBRARY=os.environ.get('NOCTURNE_MIGRATION_LIBRARY')
WASM=Path(os.environ.get('NOCTURNE_MIGRATION_WASM',ROOT/'dist/nocturne_native.wasm'))
TEXT='界e\u0301🙂אב\n'*10001

def fixture(case):
 base=ROOT/case['fixture'];return gzip.decompress(base.with_suffix('.snapshot.gz').read_bytes()),gzip.decompress(base.with_suffix('.frame.gz').read_bytes())
def subset(test,want,got,path=''):
 if isinstance(want,dict):
  for key,value in want.items():
   test.assertIn(key,got,path);subset(test,value,got[key],path+'/'+key)
 elif isinstance(want,list):
  test.assertEqual(len(got),len(want),path)
  for i,value in enumerate(want):subset(test,value,got[i],path+'/'+str(i))
 else:test.assertEqual(got,want,path)
def compare_readback(test,scene,case):
 subset(test,case['readback'],scene.info_complete());test.assertEqual(scene.text_run_source(0,0),case['source']);test.assertEqual(scene.selected_text(),case['selection'])
def grow(scene):
 scene.command({'op':'prompt','presentation':'framed','mode':'grow','active':True,'maxChars':0});scene.command({'op':'draft','text':TEXT,'emitWeather':False});scene.command({'op':'select','anchor':len(TEXT)-12,'caret':len(TEXT)})

class OriginalWeatherSchemaMigration(unittest.TestCase):
 def test_genuine_receipt_hashes_and_wire_shapes(self):
  for case in CASES:
   with self.subTest(schema=case['schema']):
    snapshot,frame=fixture(case);receipt=json.loads((ROOT/case['fixture']).with_suffix('.json').read_text())
    self.assertEqual(hashlib.sha256(snapshot).hexdigest(),case['snapshot_sha256']);self.assertEqual(hashlib.sha256(frame).hexdigest(),case['frame_sha256'])
    self.assertEqual(struct.unpack_from('<I',snapshot,12)[0],int(case['schema'],16));self.assertEqual(struct.unpack_from('<I',snapshot,28)[0],int(case['schema'],16))
    self.assertEqual(struct.unpack_from('<I',snapshot,16)[0],len(snapshot)-24);self.assertEqual(struct.unpack_from('<I',snapshot,20)[0],zlib.crc32(snapshot[24:]));self.assertEqual(len(snapshot),24+receipt['fixed_prefix_bytes']+receipt['prompt_wire_bytes'])
 def test_native_public_load_exact_artwork_readback_and_replay(self):
  for case in CASES:
   with self.subTest(schema=case['schema']),NativeScene(library=LIBRARY) as scene:
    grow(scene);old,frame=fixture(case);scene.restore(old);saved=scene.snapshot();compare_readback(self,scene,case)
    self.assertEqual(scene.render().bytes,frame);self.assertEqual(scene.snapshot(),saved);scene.restore(saved);self.assertEqual(scene.snapshot(),saved);self.assertEqual(scene.render().bytes,frame)
    self.assertGreaterEqual(struct.unpack_from('<I',saved,12)[0],0x20261085)
 def test_public_wasm_migration_and_cross_backend_prompt_growth(self):
  with tempfile.TemporaryDirectory() as directory:
   out=Path(directory);requests=[]
   for case in CASES:
    name=case['schema'];old,frame=fixture(case);(out/(name+'.old')).write_bytes(old);(out/(name+'.frame')).write_bytes(frame)
    with NativeScene(library=LIBRARY) as scene:
     grow(scene);scene.restore(old);compare_readback(self,scene,case);self.assertEqual(scene.render().bytes,frame)
     (out/(name+'.native')).write_bytes(scene.snapshot());grow(scene);self.assertEqual(scene.text_run_source(0,0),TEXT);self.assertEqual(scene.selected_text(),TEXT[-12:]);saved=scene.snapshot();grown=scene.render().bytes;self.assertEqual(scene.snapshot(),saved)
     (out/(name+'.grown-native')).write_bytes(saved);(out/(name+'.grown-frame')).write_bytes(grown)
     requests.append({**case,'text':TEXT,'selectionText':TEXT[-12:]})
   (out/'requests.json').write_text(json.dumps(requests));run=subprocess.run(['node',str(ROOT/'tests/original_weather_schema_migration_wasm.mjs'),str(out),str(WASM)],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr);report=json.loads(run.stdout);self.assertEqual(len(report['cases']),5)
   for case in CASES:
    name=case['schema']
    with self.subTest(schema=name),NativeScene(library=LIBRARY) as scene:
     wasm=(out/(name+'.grown-wasm')).read_bytes();scene.restore(wasm);self.assertEqual(scene.snapshot(),wasm);self.assertEqual(scene.text_run_source(0,0),TEXT);self.assertEqual(scene.selected_text(),TEXT[-12:]);self.assertEqual(scene.render().bytes,(out/(name+'.grown-frame')).read_bytes())
   if os.environ.get('NOCTURNE_MIGRATION_EVIDENCE'):
    destination=Path(os.environ['NOCTURNE_MIGRATION_EVIDENCE']);destination.mkdir(parents=True,exist_ok=True);report['nativeLibrary']=str(LIBRARY or ROOT/'dist/libnocturne_native.dylib');report['wasmPath']=str(WASM);report['wasmSha256']=hashlib.sha256(WASM.read_bytes()).hexdigest();(destination/'combined-migration-results.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':unittest.main()
