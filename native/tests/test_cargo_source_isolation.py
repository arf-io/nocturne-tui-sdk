"""Real Cargo projects and outputs; source-root cache regression, no mocks."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cargo_example import cargoEnvironment,buildExample
class CargoSourceIsolation(unittest.TestCase):
 def test_source_mapping_is_stable_idempotent_and_distinct(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();base={'CARGO_TARGET_DIR':str(root/'cache')}
   a=cargoEnvironment(root/'a',base);b=cargoEnvironment(root/'b',base)
   self.assertNotEqual(a['CARGO_TARGET_DIR'],b['CARGO_TARGET_DIR'])
   self.assertEqual(cargoEnvironment(root/'a',a),a)
   self.assertTrue(Path(a['CARGO_TARGET_DIR']).is_relative_to(root/'cache'))
 def test_actual_same_package_projects_keep_distinct_executables(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();env={**os.environ,'CARGO_TARGET_DIR':str(root/'cache')};seen=[];timestamp=1700000000000000000
   for name,value in [('one','SOURCE-ONE'),('two','SOURCE-TWO')]:
    project=root/name;(project/'examples').mkdir(parents=True)
    (project/'Cargo.toml').write_text('[package]\nname="source-isolation-probe"\nversion="0.0.0"\nedition="2021"\n')
    (project/'Cargo.lock').write_text('version = 4\n\n[[package]]\nname="source-isolation-probe"\nversion="0.0.0"\n')
    source=project/'examples/probe.rs';source.write_text('fn main(){println!("'+value+'");}');os.utime(source,ns=(timestamp,timestamp))
    executable=buildExample(project/'Cargo.toml','probe',project/'build.log',env=env)
    self.assertEqual(subprocess.check_output([str(executable)],text=True).strip(),value);seen.append(executable)
   self.assertNotEqual(seen[0],seen[1])
