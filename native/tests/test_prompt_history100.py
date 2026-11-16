import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json,sys,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench
class PromptHistory100(unittest.TestCase):
 def test_original_source_and_current100undos_redos_eviction(self):
  html=load_rc2_workbench();start=html.index('const {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument}=(()=>{');end=html.index('})();',start)+5
  script=html[start:end]+"\nconst d=new PromptDocument('');for(let i=0;i<105;i++)d.insert(String.fromCodePoint(0x410+i));const current=d.text;for(let i=0;i<100;i++)d.undo();const oldest=d.text;d.undo();const extra=d.text;for(let i=0;i<100;i++)d.redo();console.log(JSON.stringify({current,oldest,extra,restored:d.text}));"
  original=json.loads(subprocess.run(['node','-e',script],capture_output=True,text=True,check=True).stdout)
  with NativeScene() as scene:
   for i in range(105):scene.command({'op':'input','text':chr(0x410+i)})
   self.assertEqual(scene.text_run_source(0,0),original['current']);saved=scene.snapshot()
   for i in range(100):scene.command({'op':'key','key':'z','ctrl':True})
   self.assertEqual(scene.text_run_source(0,0),original['oldest']);scene.command({'op':'key','key':'z','ctrl':True});self.assertEqual(scene.text_run_source(0,0),original['extra'])
   mid=scene.snapshot()
   with NativeScene() as restored:
    restored.restore(mid)
    for i in range(100):restored.command({'op':'key','key':'r','ctrl':True})
    self.assertEqual(restored.text_run_source(0,0),original['restored'])
   scene.restore(saved);self.assertEqual(scene.text_run_source(0,0),original['current'])
 def test_variable_length_unicode_history_and_redo_invalidation(self):
  with NativeScene() as scene:
   values=['界🙂e\u0301'*(i%17)+str(i) for i in range(101)]
   for value in values:scene.command({'op':'draft','text':value,'emitWeather':False})
   for value in reversed(values[:-1]):
    scene.command({'op':'key','key':'z','ctrl':True});self.assertEqual(scene.text_run_source(0,0),value)
   scene.command({'op':'input','text':'changed'});before=scene.text_run_source(0,0);scene.command({'op':'key','key':'r','ctrl':True});self.assertEqual(scene.text_run_source(0,0),before)
 def test_packed_history_grows_for_used_words_and_replays100large_edits(self):
  with NativeScene() as scene:
   values=['界'*(5000+i)+str(i) for i in range(101)]
   for value in values:scene.command({'op':'draft','text':value,'emitWeather':False})
   self.assertLess(scene._lib.nrPromptMemoryCapacity(scene._context),25*1024*1024)
   saved=scene.snapshot()
   with NativeScene() as restored:
    restored.restore(saved)
    for value in reversed(values[:-1]):
     restored.command({'op':'key','key':'z','ctrl':True});self.assertEqual(restored.text_run_source(0,0),value)
 def test_genuine_schema73_migration_preserves_source_frame_and_history(self):
  import gzip,hashlib
  folder=ROOT/'evidence/dynamic-prompt-20261014';metadata=json.loads((folder/'schema73-original-branch.json').read_text());commands=json.loads(gzip.decompress((folder/'schema73-original-branch.commands.json.gz').read_bytes()))
  with NativeScene() as scene:
   scene.restore(gzip.decompress((folder/'schema73-original-branch.snapshot.gz').read_bytes()))
   self.assertEqual(hashlib.sha256(scene.text_run_source(0,0).encode()).hexdigest(),metadata['source_sha256']);self.assertEqual(scene.render().bytes,gzip.decompress((folder/'schema73-original-branch.frame.gz').read_bytes()))
   scene.command({'op':'key','key':'z','ctrl':True});self.assertEqual(scene.text_run_source(0,0),commands[1]['text'])
   scene.command({'op':'key','key':'r','ctrl':True});self.assertEqual(hashlib.sha256(scene.text_run_source(0,0).encode()).hexdigest(),metadata['source_sha256'])
 def test_missing_history_storage_and_invalid_history_scalar_are_atomic(self):
  import ctypes as C,struct,zlib
  with NativeScene() as scene:
   scene.command({'op':'draft','text':'A'*5000,'emitWeather':False});rejected=False
   for i in range(30):
    saved=scene.snapshot();command={'op':'draft','text':'B'*5000,'emitWeather':False};raw=json.dumps(command).encode()
    code=scene._lib.nrCommand(scene._context,raw,len(raw))
    if code<0:
     self.assertEqual(scene._lib.nrError(scene._context),b'Prompt storage required');self.assertEqual(scene.snapshot(),saved);scene.command(command);rejected=True;break
   self.assertTrue(rejected)
   before=scene.snapshot();changed=bytearray(before);wire=scene._lib.nrPromptWireSize();fixed=scene._lib.nrSnapshotSize()-24-wire
   # Skip current document to the first nonempty historical record.
   scalar=24+fixed+wire+5000*4;struct.pack_into('<I',changed,scalar,0xd800);struct.pack_into('<I',changed,20,zlib.crc32(changed[24:]))
   with self.assertRaises(ValueError):scene.restore(changed)
   self.assertEqual(scene.snapshot(),before)
if __name__=='__main__':unittest.main()
