"""Exercise Cargo artifact selection with a real compiled Cargo JSON stream."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
from cargo_artifact import executable
class CargoArtifactTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='nocturne-cargo-artifact-');cls.root=Path(cls.temp.name).resolve()
  (cls.root/'examples').mkdir();(cls.root/'Cargo.toml').write_text('[package]\nname="nocturne-ci-artifact-check"\nversion="0.0.0"\nedition="2021"\n')
  (cls.root/'examples/qualification.rs').write_text('fn main(){println!("actual-cargo-artifact");}\n')
  cls.log=cls.root/'build.jsonl';env=dict(os.environ,CARGO_TARGET_DIR=str(cls.root/'target'),CARGO_BUILD_JOBS='2')
  with cls.log.open('wb') as f:subprocess.run(['cargo','build','--offline','--manifest-path',str(cls.root/'Cargo.toml'),'--example','qualification','--message-format=json'],env=env,stdout=f,check=True)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_actual_executable_runs(self):
  path=executable(self.log,'qualification');self.assertEqual(subprocess.check_output([str(path)],text=True).strip(),'actual-cargo-artifact')
 def test_missing_target_rejects(self):
  with self.assertRaises(ValueError):executable(self.log,'nonexistent')
 def test_distinct_artifacts_reject(self):
  rows=[json.loads(line) for line in self.log.read_text().splitlines() if line.startswith('{')]
  row=next(row for row in rows if row.get('executable'))
  other=self.root/'other';other.write_bytes(Path(row['executable']).read_bytes());other.chmod(0o755)
  changed=dict(row,executable=str(other));log=self.root/'ambiguous.jsonl';log.write_text(self.log.read_text()+json.dumps(changed)+'\n')
  with self.assertRaises(ValueError):executable(log,'qualification')
 def test_missing_executable_rejects(self):
  log=self.root/'missing.jsonl';rows=[json.loads(line) for line in self.log.read_text().splitlines() if line.startswith('{')]
  for row in rows:
   if row.get('executable'):row['executable']=str(self.root/'absent')
  log.write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
  with self.assertRaises(ValueError):executable(log,'qualification')
if __name__=='__main__':unittest.main()
