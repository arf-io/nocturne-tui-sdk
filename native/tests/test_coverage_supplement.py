"""The coverage supplement runs exactly the ten retained equation/control/replay tests as one journaled step."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import coverage_supplement as supplement
class CoverageSupplement(unittest.TestCase):
 def test_plan_names_exactly_the_ten_retained_tests_in_one_step(self):
  self.assertEqual(len(supplement.TESTS),10)
  self.assertEqual(len(set(supplement.TESTS)),10)
  for name in supplement.TESTS:
   module=name.split('.')[0]
   self.assertTrue((Path(__file__).resolve().parent/(module+'.py')).is_file(),module)
  argv=supplement.plan_argv('/py')
  self.assertEqual(argv[:5],['/py','-B','-m','unittest','-v']);self.assertEqual(argv[5:],list(supplement.TESTS))
 def test_refuses_reused_output_or_profile_directories(self):
  with tempfile.TemporaryDirectory() as d:
   used=Path(d)/'used';used.mkdir();(used/'EXECUTION.json').write_text('{}')
   with self.assertRaises(FileExistsError):supplement.check_directories(used,Path(d)/'profiles')
   profiles=Path(d)/'profiles';profiles.mkdir();(profiles/'x.profraw').write_bytes(b'')
   with self.assertRaises(FileExistsError):supplement.check_directories(Path(d)/'fresh',profiles)
   with self.assertRaises(ValueError):supplement.check_directories(Path(d)/'fresh',Path(d)/'missing-profiles')
if __name__=='__main__':unittest.main()
