"""Actual host decisions/native query WASM and native painter replay against originals."""
from pathlib import Path
import array,gzip,json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PearlDataNative(unittest.TestCase):
 def test_all_original_host_controller_frames_native_and_wasm(self):
  with tempfile.TemporaryDirectory(prefix='pearl-original-native-') as output:
   trace=Path(output)/'actual.jsonl';env=dict(os.environ,NOCTURNE_PEARL_TRACE=str(trace))
   run=subprocess.run(['node','--test','bindings/typescript/pearl_stage.test.mjs'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
   total=0
   with NativeScene(library=ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')) as scene:
    with trace.open() as stream:
     for line in stream:
      row=json.loads(line)
      for command in row['commands']:scene.command(command)
      before=scene.snapshot();frame=scene.render();actual=array.array('I');actual.frombytes(frame.bytes);expected=row['cells'];self.assertEqual(len(actual),len(expected))
      for i in range(0,len(actual),4):self.assertEqual(actual[i:i+3].tolist(),expected[i:i+3],(row['label'],i//4))
      self.assertEqual(before,scene.snapshot());total+=1
   oracle=json.loads(gzip.decompress((ROOT/'tests/fixtures/pearl-data-original/FLEET-ACTIONS-ORACLE.json.gz').read_bytes()));expected_count=32+29+10+sum(bool(row['frame']['width'] and row['frame']['height']) for scenario in oracle['scenarios'] for row in scenario['rows']);self.assertEqual(total,expected_count)
