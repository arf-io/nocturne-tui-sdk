"""Original maximum document through real public SDK, with original JS oracle."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench
class OriginalPromptCapacity(unittest.TestCase):
 def test_original_source_accepts_65536_and_rejects_next_scalar(self):
  html=load_rc2_workbench(); start=html.index('const {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument}=(()=>{');end=html.index('})();',start)+5
  script=html[start:end]+"\nconst d=new PromptDocument('😀'.repeat(65536)); let rejected=false;try{d.insert('x')}catch(e){rejected=e instanceof RangeError};console.log(JSON.stringify({count:[...d.text].length,rejected,caret:d.caret}));"
  p=subprocess.run(['node','-e',script],capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(p.stdout),{'count':65536,'rejected':True,'caret':65536})
 def test_original_maximum_round_trips_with_real_edits_render_and_snapshot(self):
  for count in (2049,65536):
   with self.subTest(count=count),NativeScene(2030) as s:
    s.command({'op':'resize','width':100,'height':40})
    s.command({'op':'prompt','presentation':'framed','maxChars':65536})
    text='A'*(count-1)+'🌧'
    s.command({'op':'draft','text':text,'emitWeather':False})
    self.assertEqual(s.info_complete()['prompt']['text'],text)
    self.assertEqual(s.text_run_source(0,0),text)
    self.assertEqual(len(s.text_run_clusters(0,0)),count)
    self.assertEqual(len(s.text_run_layout(0,0,80)),count)
    self.assertTrue(s.text_run_clip(0,0,80,0,0,80,1))
    s.command({'op':'select','anchor':0,'caret':count})
    self.assertEqual(s.selected_text(),text)
    s.command({'op':'select','anchor':count,'caret':count})
    frame=s.render();self.assertGreater(frame.width,0)
    self.assertTrue(any(row[0]==ord('🌧') for row in frame.words()))
    snapshot=s.snapshot()
    with NativeScene(2031) as restored:
     restored.restore(snapshot);self.assertEqual(restored.info_complete()['prompt']['text'],text)
     restored.command({'op':'select','anchor':count-1,'caret':count})
     restored.command({'op':'input','text':'Z'})
     self.assertEqual(restored.info_complete()['prompt']['text'],text[:-1]+'Z')
     restored.command({'op':'key','key':'z','ctrl':True})
     self.assertEqual(restored.info_complete()['prompt']['text'],text)
    if count==65536:
     before=s.snapshot()
     with self.assertRaises((ValueError,RuntimeError)):s.command({'op':'input','text':'x'})
     self.assertEqual(s.snapshot(),before)
 def test_schema68_draft_migration(self):
  with NativeScene(1) as s:
   s.restore((ROOT/'evidence/prompt-capacity-20261014/schema68-prompt.snapshot').read_bytes())
   self.assertEqual(s.info()['prompt']['text'],'Original 🌧 draft\nSecond line')
   s.command({'op':'input','text':' kept'});self.assertTrue(s.info()['prompt']['text'].endswith(' kept'))
if __name__=='__main__':unittest.main()
