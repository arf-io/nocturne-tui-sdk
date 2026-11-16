"""Original132 controller frames from the real current WASM adapter and native renderer."""
from pathlib import Path
import array,gzip,json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PearlObservatoryNative(unittest.TestCase):
 def test_original132_current_native_and_wasm_complete_frames(self):
  oracle=json.loads(gzip.decompress((ROOT/'tests/fixtures/pearl-data-original/OBSERVATORY-ACTIONS-ORACLE.json.gz').read_bytes()));expected={row['id']:row['frame']['cells']for row in oracle['rows']}
  with tempfile.TemporaryDirectory(prefix='observatory-native-')as output:
   trace=Path(output)/'actual.json';run=subprocess.run(['node','--test','--test-name-pattern=all original Observatory controller','bindings/typescript/pearl_observatory_stage.test.mjs'],cwd=ROOT,env=dict(os.environ,NOCTURNE_OBSERVATORY_TRACE=str(trace)),capture_output=True,text=True,timeout=180);self.assertEqual(run.returncode,0,run.stdout+run.stderr);rows=json.loads(trace.read_text());self.assertEqual([r['id']for r in rows],list(expected))
   with NativeScene(library=ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'))as scene:
    for row in rows:
     for command in row['commands']:scene.command(command)
     before=scene.snapshot();frame=scene.render();actual=array.array('I');actual.frombytes(frame.bytes);wanted=expected[row['id']];self.assertEqual(len(actual),len(wanted))
     for at in range(0,len(actual),4):self.assertEqual(actual[at:at+3].tolist(),wanted[at:at+3],(row['id'],at//4))
     self.assertEqual(scene.snapshot(),before)
