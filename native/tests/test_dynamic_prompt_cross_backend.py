"""Large pointer-free snapshots must round-trip between actual native and WASM."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import node_executable
class DynamicPromptCrossBackend(unittest.TestCase):
 def test_independent_schema73_snapshot_preserves_original_frame(self):
  import gzip,hashlib
  folder=ROOT/'evidence/dynamic-prompt-20261014'
  snapshot=gzip.decompress((folder/'schema73-original-branch.snapshot.gz').read_bytes())
  expected=gzip.decompress((folder/'schema73-original-branch.frame.gz').read_bytes())
  with NativeScene(1) as scene:
   scene.restore(snapshot)
   self.assertEqual(len(scene.text_run_source(0,0)),70003)
   self.assertEqual(scene.render().bytes,expected)
   before=scene.snapshot();scene.restore(before);self.assertEqual(scene.snapshot(),before)
 def test_independent_schema75_snapshot_preserves_source_frame_and_undo(self):
  import gzip,hashlib
  folder=ROOT/'evidence/dynamic-prompt-20261014';metadata=json.loads((folder/'schema75-original-branch.json').read_text())
  with NativeScene(1) as scene:
   scene.restore(gzip.decompress((folder/'schema75-original-branch.snapshot.gz').read_bytes()))
   self.assertEqual(hashlib.sha256(scene.text_run_source(0,0).encode()).hexdigest(),metadata['source_sha256'])
   self.assertEqual(scene.render().bytes,gzip.decompress((folder/'schema75-original-branch.frame.gz').read_bytes()))
   source=scene.text_run_source(0,0);scene.command({'op':'key','key':'z','ctrl':True});self.assertNotEqual(scene.text_run_source(0,0),source)
   scene.command({'op':'key','key':'r','ctrl':True});self.assertEqual(scene.text_run_source(0,0),source)
 def test_large_native_wasm_native_snapshot_and_frame(self):
  with tempfile.TemporaryDirectory(prefix='nocturne-dynamic-snapshot-') as temp,NativeScene(2030) as scene:
   folder=Path(temp);text='A界e\u0301אב🙂\n'*10001
   for i in range(100):scene.command({'op':'input','text':'界'+str(i)})
   scene.command({'op':'prompt','layout':'bidi','direction':'auto','mode':'grow'})
   scene.command({'op':'draft','text':text,'emitWeather':False});scene.command({'op':'select','anchor':len(text)-15,'caret':len(text)})
   snapshot=scene.snapshot();(folder/'native.snap').write_bytes(snapshot);(folder/'native.frame').write_bytes(scene.render().bytes)
   result=subprocess.run([node_executable(),str(ROOT/'tests/dynamic_prompt_cross_backend.mjs'),str(folder)],capture_output=True,text=True,check=True)
   self.assertEqual(json.loads(result.stdout)['scalars'],len(text));self.assertEqual((folder/'wasm.snap').read_bytes(),snapshot)
   scene.restore((folder/'wasm-edited.snap').read_bytes());self.assertEqual(scene.text_run_source(0,0),text[:-15]+'WASM界');self.assertEqual(scene.render().bytes,(folder/'wasm-edited.frame').read_bytes())
   scene.command({'op':'key','key':'z','ctrl':True});self.assertEqual(scene.text_run_source(0,0),text)
   scene.command({'op':'key','key':'z','ctrl':True});self.assertEqual(scene.text_run_source(0,0),''.join('界'+str(i) for i in range(100)))
if __name__=='__main__':unittest.main()
