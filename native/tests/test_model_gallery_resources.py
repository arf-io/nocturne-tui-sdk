"""Real original model resource through canonical native and WASM gallery paths."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import base64,copy,hashlib,json,os,subprocess,sys,tempfile,unittest,struct
from pathlib import Path
from original_scenic_samples import OriginalScenicSamples
from native.tests.host_environment import node_executable
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'));from gallery_cases import execute
class ModelGalleryResources(unittest.TestCase):
 def case(self):
  return json.loads(Path(os.environ.get('NOCTURNE_MODEL_CASE',ROOT/'examples/orbital-loom-model.json')).read_text())
 def expected_frame(self,case):
  fixture=ROOT/'tests/fixtures/source-model'
  frame=next(f for f in json.loads((fixture/'ORACLE.json').read_text())['frames'] if f['id']=='model-1-0-0.cells')
  with tempfile.TemporaryDirectory(prefix='original-model-gallery-') as directory:
   return bytearray(OriginalScenicSamples(directory).expected_model(frame,(fixture/frame['id']).read_bytes(),base64.b64decode(case['modelRecords'])))
 def test_recipe_assertions_match_original_samples(self):
  case=self.case();expected=self.expected_frame(case);width=case['viewport']['width']
  for row in case['expectedCells']:
   self.assertEqual(row['glyph'],struct.unpack_from('<I',expected,(row['y']*width+row['x'])*16)[0],f'cell {row["x"]},{row["y"]}')
   self.assertEqual(row['semanticId'],0)
  for row in case['expectedColors']:
   self.assertEqual(row['foreground'],struct.unpack_from('<I',expected,(row['y']*width+row['x'])*16+4)[0],f'color {row["x"]},{row["y"]}')
 def test_native_canonical_case_draws_full_original_frame(self):
  case=self.case();rows=execute([case]);expected=self.expected_frame(case)
  for at in range(12,len(expected),16):expected[at:at+4]=bytes(4)
  self.assertEqual(len(base64.b64decode(case['modelRecords'])),4608*40)
  for row in rows[0]['samples']:self.assertEqual(row['frameSha256'],hashlib.sha256(expected).hexdigest())
  self.assertTrue(rows[0]['renderPure']);self.assertTrue(rows[0]['partitionReplay'])
  if os.environ.get('NOCTURNE_MODEL_RESOURCE_EVIDENCE'):
   target=Path(os.environ['NOCTURNE_MODEL_RESOURCE_EVIDENCE']);target.mkdir(parents=True,exist_ok=True);(target/'native-original-model.json').write_text(json.dumps(rows,indent=2))
 def test_actual_wasm_worker_checks_model_and_bad_resources(self):
  cases=[self.case()];bad=copy.deepcopy(cases[0]);bad['id']='invalid-model-base64';bad['modelRecords']+='\n';cases.append(bad);reset=copy.deepcopy(cases[0]);reset['id']='invalid-model-nested-reset';reset['commands'].insert(0,{'op':'batch','commands':[{'op':'reset'}]});cases.append(reset)
  for index,value in enumerate([None,[],{},7,True]):
   wrong=copy.deepcopy(cases[0]);wrong['id']=f'invalid-model-type-{index}';wrong['modelRecords']=value;cases.append(wrong)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'cases.json').write_text(json.dumps(cases));run=subprocess.run([node_executable(),str(ROOT/'scripts/check_gallery_cases.mjs'),str(p/'cases.json'),str(p/'result.json')],capture_output=True,text=True,env={**os.environ,'NOCTURNE_GALLERY_WORKERS':'1'},timeout=120);report=json.loads((p/'result.json').read_text());rows={r['id']:r for r in report['cases']};self.assertEqual(rows[cases[0]['id']]['status'],'PASS',run.stdout+run.stderr);self.assertEqual(rows[bad['id']]['status'],'FAIL');self.assertEqual(rows[reset['id']]['status'],'FAIL');self.assertEqual(run.returncode,1)
   for case in cases[1:]:self.assertEqual(rows[case['id']]['status'],'FAIL')
   if os.environ.get('NOCTURNE_MODEL_RESOURCE_EVIDENCE'):
    target=Path(os.environ['NOCTURNE_MODEL_RESOURCE_EVIDENCE']);target.mkdir(parents=True,exist_ok=True);(target/'wasm-actual-cases.json').write_text(json.dumps(report,indent=2))
 def test_native_rejects_noncanonical_resource_and_nested_reset(self):
  for data in [self.case()['modelRecords']+'\n','YQ==','YQ===','YR==',None,[],{},7,True]:
   case=self.case();case['modelRecords']=data
   with self.assertRaises(ValueError):execute([case])
  case=self.case();case['commands'].insert(0,{'op':'batch','commands':[{'op':'batch','commands':[{'op':'reset'}]}]})
  with self.assertRaises(ValueError):execute([case])
if __name__=='__main__':unittest.main()
