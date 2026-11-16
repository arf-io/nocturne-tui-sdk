"""The actual canonical plan must include every authored type test."""
import json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class QualificationTypeInventory(unittest.TestCase):
 def test_new_type_tests_cannot_be_silently_omitted(self):
  run=subprocess.run([sys.executable,str(ROOT/'scripts/qualify.py'),'--strict','--list'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(run.returncode,0,run.stderr)
  plan=json.loads(run.stdout);case=next(row for row in plan if row['id']=='typescript-types');command=case['argv'] if 'argv'in case else case['command']
  expected={p.relative_to(ROOT).as_posix()for p in (ROOT/'tests/types').iterdir() if p.is_file() and p.suffix in {'.ts','.mts','.cts'} and not p.name.endswith(('.d.ts','.d.mts','.d.cts'))};expected.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'bindings/typescript').iterdir() if p.is_file() and p.name.endswith(('-types.ts','-types.mts','-types.cts')));self.assertIn('bindings/typescript/observatory-overlay-types.mts',expected);self.assertIn('bindings/typescript/source-stage-types.mts',expected);self.assertFalse(expected-set(command),sorted(expected-set(command)));self.assertTrue(all(command.count(path)==1 for path in expected));declarations={p.relative_to(ROOT).as_posix()for folder in ['tests/types','bindings/typescript']for p in (ROOT/folder).iterdir()if p.is_file()and p.name.endswith(('.d.ts','.d.mts','.d.cts'))};self.assertFalse(declarations.intersection(command))
 def test_model_sanitizer_executes_and_retains_its_actual_binary(self):
  run=subprocess.run([sys.executable,str(ROOT/'scripts/qualify.py'),'--strict','--list'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(run.returncode,0,run.stderr)
  plan=json.loads(run.stdout);rows={row['id']:row for row in plan}
  self.assertIn('source-model-sanitizer-build',rows);self.assertIn('source-model-sanitizer-run',rows)
  build=rows['source-model-sanitizer-build'];execute=rows['source-model-sanitizer-run']
  command=build.get('argv',build.get('command'));self.assertIn('tests/source_model_contract.c',command);self.assertIn('-fsanitize=address,undefined',command)
  self.assertIn(str(ROOT/'dist/source-model-safety'),build['artifacts'])
  self.assertEqual(execute.get('argv',execute.get('command')),[str(ROOT/'dist/source-model-safety')])
  self.assertLess(plan.index(build),plan.index(execute))
if __name__=='__main__':unittest.main()
