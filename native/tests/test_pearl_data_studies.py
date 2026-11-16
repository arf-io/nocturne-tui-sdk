"""Normal original Pearl recipes participate in the real native/WASM gallery paths."""
from pathlib import Path
import json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'))
from pearl_data_studies import build_pearl_data_studies
from gallery_cases import execute
class PearlDataStudies(unittest.TestCase):
 def test_generated_source_configuration_reproduces_from_current_native_queries(self):
  with tempfile.TemporaryDirectory() as directory:
   target=Path(directory)/'cases.json';run=subprocess.run(['node','scripts/emit_pearl_studies.mjs',str(target)],cwd=ROOT,capture_output=True,text=True,timeout=90);self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertEqual(json.loads(target.read_text()),build_pearl_data_studies())
 def test_actual_normal_native_and_wasm_gallery_replay(self):
  cases=build_pearl_data_studies();self.assertEqual([row['id']for row in cases],['pearl-studio-original','pearl-fleet-original']);self.assertTrue(all(row['demo']and row['actions']for row in cases));rows=execute(cases);self.assertEqual(len(rows),2)
  with tempfile.TemporaryDirectory() as directory:
   report=Path(directory)/'wasm.json';run=subprocess.run(['node','scripts/check_gallery_cases.mjs',str(ROOT/'examples/pearl_data_studies.json'),str(report)],cwd=ROOT,env=dict(os.environ,NOCTURNE_GALLERY_WORKERS='1'),capture_output=True,text=True,timeout=120);self.assertEqual(run.returncode,0,run.stdout+run.stderr);result=json.loads(report.read_text());self.assertTrue(result['passed']);self.assertEqual(result['expectedCaseIds'],[row['id']for row in cases]);self.assertTrue(all(row['renderPure']and row['partitionReplay']for row in result['cases']))
