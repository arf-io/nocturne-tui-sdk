import sys,unittest,json,tempfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'));sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
SETS=((0x2500,)*4,(0x2501,)*4,(0x2550,)*4,(0xb7,0x22c5,0x2219,0xb7),(0x2801,0x2808,0x2810,0x2802),(0x2581,0x2582,0x2583,0x2582),(0x203a,0x203a,0x203a,32),(0x2580,0x2584,0x2580,0x2584),(0x2574,32,0x2576,32),(0x2571,0x2572,0x2571,0x2572),(32,0x2219,0x2022,0x2219),(0x25cb,0xb7,0x25cb,0xb7))
class OriginalWaitingGallery(unittest.TestCase):
 def case(self):
  from original_waiting_studies import build_original_waiting_studies
  return build_original_waiting_studies()[0]
 def test_original_multichar_rule_sets_and_animated_boxes_are_visible(self):
  q=self.case();self.assertTrue(q['demo'])
  with NativeScene(2030)as s:
   for c in q['commands']:s.command(c)
   frames=[]
   for ms in [0,150,300,450,600]:
    s.advance_to(ms*1000);before=s.snapshot();f=s.render();self.assertEqual(s.snapshot(),before);words=f.words();frames.append(words)
    for style,chars in enumerate(SETS):
     actual=[words[(3+style)*120+4+i][0]for i in range(28)]
     self.assertEqual(actual,[chars[(i-ms//150)%4]for i in range(28)],(style,ms))
   self.assertNotEqual(frames[0][19*120+3][1],frames[-1][19*120+3][1],'original animated box perimeter')
   self.assertNotEqual(frames[0][21*120+5][0],frames[-1][21*120+5][0],'original progressive text reveal')
 def test_complete_original_rule_demo_matches_real_wasm_and_snapshot_replay(self):
  case=self.case()
  with NativeScene(2030)as s,tempfile.TemporaryDirectory()as directory:
   temp=Path(directory)
   for c in case['commands']:s.command(c)
   for ms in [0,150,300,450,600]:
    s.advance_to(ms*1000);request=temp/'request.json';request.write_text(json.dumps({'commands':case['commands'],'timeUs':ms*1000,'invalidCommand':{'op':'source-stage-component','id':1,'kind':'missing'}}));out=temp/str(ms)
    run=subprocess.run(['node',str(ROOT/'tests/source_stage_public_wasm_runner.mjs'),str(request),str(out)],capture_output=True,text=True)
    self.assertEqual(run.returncode,0,run.stdout+run.stderr)
    self.assertEqual(s.render().bytes,(out/'source-stage-cells.bin').read_bytes())
if __name__=='__main__':unittest.main()
