import gzip,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'));sys.path.insert(0,str(ROOT/'bindings/python'))
from source_modal_studies import build_source_modal_studies
from nocturne_native import NativeScene
class OriginalModalCases(unittest.TestCase):
 def test_all_current_cases_and_original_full_frames(self):
  cases=build_source_modal_studies();self.assertEqual(len(cases),30);self.assertEqual(cases,json.loads((ROOT/'tests/fixtures/source-modal/CASES.json').read_text()));oracle=json.loads(gzip.decompress((ROOT/'tests/fixtures/source-modal/COMPOSED.json.gz').read_bytes()))
  lookup={(r['kind'],r['time']*1000):r['currentIdentityFrame'] for r in oracle['rows']}
  for case in cases:
   with self.subTest(case=case['id']),NativeScene() as scene:
    for cmd in case['commands']:scene.command(cmd)
    start=scene.snapshot();actions=case.get('actions',[]);i=0
    for time in case['sampleTimesUs']:
     while i<len(actions) and actions[i]['timeUs']<=time:scene.advance_to(actions[i]['timeUs']);scene.command(actions[i]['command']);i+=1
     scene.advance_to(time);saved=scene.snapshot();frame=scene.render();self.assertEqual(saved,scene.snapshot())
     if case.get('originalKind'):self.assertEqual(list(frame.cells) if hasattr(frame,'cells') else [n for row in frame.words() for n in row],lookup[case['originalKind'],time])
    expected=case.get('expectedSourceModal',{});info=scene.info_complete()['sourceModal']
    for key,value in expected.items():self.assertEqual(info[key],value)
    final=scene.snapshot();scene.restore(start)
    for action in actions:scene.advance_to(action['timeUs']);scene.command(action['command'])
    scene.advance_to(case['sampleTimesUs'][-1]);self.assertEqual(final,scene.snapshot())
