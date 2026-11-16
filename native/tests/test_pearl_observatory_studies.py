"""All16 source host routes coexist with the existing8weather studies."""
from pathlib import Path
import json,os,sys,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'))
from pearl_observatory_studies import build_pearl_observatory_studies
from observatory_studies import build_observatory_studies
from gallery_cases import build_cases,execute
class PearlObservatoryStudies(unittest.TestCase):
 def test_distinct_original_weather_and_all16_host_routes(self):
  host=build_pearl_observatory_studies();weather=build_observatory_studies();self.assertEqual(len(host),16);self.assertEqual(len(weather),8);ids=[r['id']for r in build_cases()];self.assertEqual(len(ids),len(set(ids)));self.assertTrue(all(ids.count(r['id'])==1 for r in host+weather));self.assertTrue(all(r['demo']and r['sampleTimesUs']==[0,50000,500000,1700000]and r['pearlSource']['family']=='observatory'for r in host))
 def test_actual_native_and_wasm_gallery_full_recipe_replay(self):
  rows=build_pearl_observatory_studies();result=execute(rows);self.assertEqual(len(result),16)
  with tempfile.TemporaryDirectory()as directory:
   report=Path(directory)/'wasm.json';run=subprocess.run(['node','scripts/check_gallery_cases.mjs',str(ROOT/'examples/pearl_observatory_studies.json'),str(report)],cwd=ROOT,env=dict(os.environ,NOCTURNE_GALLERY_WORKERS='1'),capture_output=True,text=True,timeout=240);self.assertEqual(run.returncode,0,run.stdout+run.stderr);value=json.loads(report.read_text());self.assertTrue(value['passed']);self.assertEqual(value['expectedCaseIds'],[r['id']for r in rows]);self.assertTrue(all(r['renderPure']and r['partitionReplay']for r in value['cases']))
 def test_original_model_command_generation_reproduces(self):
  with tempfile.TemporaryDirectory()as directory:
   target=Path(directory)/'cases.json';run=subprocess.run(['node','scripts/emit_observatory_studies.mjs',str(target)],cwd=ROOT,capture_output=True,text=True,timeout=180);self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertEqual(json.loads(target.read_text()),build_pearl_observatory_studies())
