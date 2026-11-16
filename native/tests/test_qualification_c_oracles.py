from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,os,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import qualify
NAMES=('observatory_overlay_safety','original_world_frame_oracle','scenic_art_geometry_diff','scenic_source_raster_diff')
class QualificationCOracles(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  old=sys.argv;sys.argv=['qualify.py','--strict','--capture','--list'];out=io.StringIO()
  try:
   with contextlib.redirect_stdout(out):assert qualify.main()==0
  finally:sys.argv=old
  cls.plan=json.loads(out.getvalue());cls.byid={r['id']:r for r in cls.plan}
 def pair(self,name):
  relative='tests/'+name+'.c';return [self.byid[qualify.discoveredCaseId(kind,relative)]for kind in ('c-build','c-run')]
 def test_partial_source_fingerprint_still_ignores_unrelated_mutable_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'native';root.mkdir();before=qualify.fingerprint(root)
   evidence=root/'evidence/current.json';evidence.parent.mkdir();evidence.write_text('{"changing":1}')
   self.assertEqual(qualify.fingerprint(root),before)
   source=root.parent/'src/original.inc';source.parent.mkdir();source.write_text('original source')
   self.assertNotEqual(qualify.fingerprint(root),before)
 def test_real_original_oracle_builders_and_scenario_arguments(self):
  evidence=str(ROOT/'evidence/original-scenic-restoration-20261013')
  for name in NAMES[1:]:
   with self.subTest(helper=name):
    build,run=self.pair(name);self.assertIn('scripts/original_c_oracles.py',build['argv']);self.assertIn(name,build['argv']);self.assertEqual(run['argv'],[str(ROOT/'dist'/('discovered-'+name)),evidence]);self.assertEqual(self.plan.index(run),self.plan.index(build)+1)
 def test_observatory_safety_uses_real_88_render_fixture_and_sanitizers(self):
  build,run=self.pair(NAMES[0]);fixture=ROOT/'evidence/original-observatory-overlay-20261015/sanitizer-commands.txt'
  self.assertIn('-fsanitize=address,undefined',build['argv']);self.assertIn('-fno-sanitize-recover=all',build['argv']);self.assertEqual(run['argv'],[str(ROOT/'dist/discovered-observatory_overlay_safety'),str(fixture)]);self.assertEqual(fixture.read_text().splitlines().count('@render'),88);self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(),'2992bf542b430515675871df5e15a7e28d87dfae8577179dcfa5e1b4efeae0fc')
 def test_all_four_actual_build_outputs_are_checkpoint_artifacts(self):
  for name in NAMES:
   with self.subTest(helper=name):self.assertIn(str(ROOT/'dist'/('discovered-'+name)),self.pair(name)[0]['artifacts'])
 def test_oracle_input_files_are_part_of_actual_source_fingerprint(self):
  files=qualify.fingerprint(ROOT)['files'];directory=ROOT/'evidence/original-scenic-restoration-20261013';manifest=json.loads((directory/'ORIGINAL-WORLD-FRAMES.json').read_text());paths=[directory/'ORIGINAL-WORLD-FRAMES.json',directory/'ORIGINAL-WORLD-FRAMES.tsv',ROOT/'evidence/original-observatory-overlay-20261015/sanitizer-commands.txt']+[directory/row['cellsFile']for row in manifest['frames']]
  self.assertEqual(len(manifest['frames']),16)
  for path in paths:
   with self.subTest(path=path.name):self.assertEqual(files.get(path.relative_to(ROOT).as_posix()),hashlib.sha256(path.read_bytes()).hexdigest())
if __name__=='__main__':unittest.main(verbosity=2)
