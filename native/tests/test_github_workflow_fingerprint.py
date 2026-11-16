"""The actual automated workflow bytes belong to the qualification fingerprint."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from qualify import fingerprint
class GithubWorkflowFingerprintTests(unittest.TestCase):
 def test_automated_workflow_changes_fingerprint(self):
  with tempfile.TemporaryDirectory(prefix='nocturne-workflow-fingerprint-') as d:
   repo=Path(d);native=repo/'native';native.mkdir();workflow=repo/'.github/workflows/nocturne.yml';workflow.parent.mkdir(parents=True)
   workflow.write_text('name: first\n');a=fingerprint(native)
   workflow.write_text('name: changed\n');b=fingerprint(native)
   self.assertIn('../.github/workflows/nocturne.yml',a['files'])
   self.assertNotEqual(a['sha256'],b['sha256'])
 def test_dependency_policy_changes_fingerprint(self):
  with tempfile.TemporaryDirectory(prefix='nocturne-dependency-fingerprint-') as d:
   repo=Path(d);native=repo/'native';native.mkdir();policy=repo/'tools/requirements-qualification.txt';policy.parent.mkdir(parents=True)
   policy.write_text('PyYAML==6.0.2\n');a=fingerprint(native)
   policy.write_text('PyYAML==6.0.3\n');b=fingerprint(native)
   self.assertIn('../tools/requirements-qualification.txt',a['files'])
   self.assertNotEqual(a['sha256'],b['sha256'])
if __name__=='__main__':unittest.main()
