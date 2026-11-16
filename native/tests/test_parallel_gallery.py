"""Actual independent contexts prove parallel gallery dispatch preserves all checks."""
import importlib.util,json,multiprocessing,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'examples'))
from check_gallery_studies import run_cases
from gallery_cases import execute
CASES=[{'id':'parallel-'+str(i),'commands':[{'op':'resize','width':48,'height':20},{'op':'prompt','active':False},{'op':'draft','text':'Nocturne🌙'+str(i),'emitWeather':False},{'op':'emitter','id':1,'effect':'weather/hearth-spray','count':4}],'sampleTimesUs':[0,250000]} for i in range(3)]
def crash_executor(cases):
 if cases[0]['id']=='parallel-1':os._exit(71)
 return execute(cases)
class ParallelGallery(unittest.TestCase):
 def test_actual_serial_parallel_observations_match(self):
  with tempfile.TemporaryDirectory() as d:
   a=run_cases(CASES,execute,Path(d)/'serial.json',{'test':'actual'},workers=1);b=run_cases(CASES,execute,Path(d)/'parallel.json',{'test':'actual'},workers=4)
   self.assertTrue(a['passed']);self.assertTrue(b['passed']);self.assertTrue(b['complete']);self.assertEqual([v['id'] for v in b['cases']],[v['id'] for v in CASES])
   for x,y in zip(a['cases'],b['cases']):self.assertEqual(x['status'],y['status']);self.assertEqual(x['observations'],y['observations'])
 def test_actual_invalid_middle_case_is_fail_and_all_rows_retained(self):
  cases=json.loads(json.dumps(CASES));cases[1]['commands'].append({'op':'not-a-native-command'})
  with tempfile.TemporaryDirectory() as d:
   r=run_cases(cases,execute,Path(d)/'fail.json',{},workers=4);self.assertFalse(r['passed']);self.assertTrue(r['complete']);self.assertEqual([v['status'] for v in r['cases']],['PASS','FAIL','PASS']);self.assertEqual(r['cases'][1]['errorType'],'ValueError')
 def test_invalid_worker_bounds_reject(self):
  for workers in [0,-1,5,True,1.5]:
   with tempfile.TemporaryDirectory() as d,self.subTest(workers=workers),self.assertRaises(ValueError):run_cases(CASES,execute,Path(d)/'no.json',{},workers=workers)

 def test_actual_worker_exit_is_incomplete_fail_and_workers_closed(self):
  before={p.pid for p in multiprocessing.active_children()}
  with tempfile.TemporaryDirectory() as d:
   output=Path(d)/'crash.json'
   with self.assertRaises(Exception):run_cases(CASES,crash_executor,output,{},workers=4)
   r=json.loads(output.read_text());self.assertEqual(r['status'],'FAIL');self.assertFalse(r['complete']);self.assertFalse(r['passed']);self.assertLess(len(r['cases']),len(CASES))
  self.assertEqual({p.pid for p in multiprocessing.active_children()},before)
