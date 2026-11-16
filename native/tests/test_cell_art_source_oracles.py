"""Actual C and WASM reject false authored cell-art expectations; no mocks."""
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'))
from gallery_cases import execute

class CellArtSourceOracles(unittest.TestCase):
 def case(self):
  return {'id':'retained-font-source','mode':'isolated','commands':[
   {'op':'resize','width':20,'height':10},{'op':'prompt','active':False},
   {'op':'cell-art','id':1,'width':2,'height':1,'x':3,'y':4,'alpha':1,'layer':'overlay','cells':[[65,0x123456,0x654321],[66,0xff0000,0]]}],
   'sampleTimesUs':[0], 'cellArtSampleChecks':[{'timeUs':0,'id':1,'x':3,'y':4,'alpha':1,'width':2,'height':1,'cells':[[65,0x123456,0x654321],[66,0xff0000,0]]}]}
 def wasm(self,case):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'cases.json';path.write_text(json.dumps([case]))
   return subprocess.run(['node',str(ROOT/'scripts/check_gallery_cases.mjs'),str(path)],capture_output=True,text=True,timeout=30)
 def test_actual_source_passes_native_and_wasm(self):
  self.assertEqual(execute([self.case()])[0]['renderPure'],True)
  result=self.wasm(self.case());self.assertEqual(result.returncode,0,result.stderr+result.stdout)
 def test_wrong_dimensions_fail_native_and_wasm(self):
  for field in ('width','height'):
   with self.subTest(field=field):
    case=self.case();case['cellArtSampleChecks'][0][field]+=1
    with self.assertRaises(RuntimeError):execute([case])
    result=self.wasm(case);self.assertNotEqual(result.returncode,0,result.stdout)
 def test_wrong_source_rejected_by_wasm(self):
  for field in ('width','height','cells'):
   with self.subTest(field=field):
    case=self.case();expected=case['cellArtSampleChecks'][0]
    if field=='cells':expected['cells'][0][1]=0
    else:expected[field]+=1
    result=self.wasm(case);self.assertNotEqual(result.returncode,0,result.stdout)
 def test_wrong_source_color_fails_native_and_wasm(self):
  case=self.case();case['cellArtSampleChecks'][0]['cells'][0][1]=0
  with self.assertRaises(RuntimeError):execute([case])
  result=self.wasm(case);self.assertNotEqual(result.returncode,0,result.stdout)
if __name__=='__main__':unittest.main()
