"""Bind exact optional OTF fixture bytes in qualification inputs."""
import hashlib,importlib.util,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('nocturne_qualification_font_binding',ROOT/'scripts/qualify.py');qualify=importlib.util.module_from_spec(spec);spec.loader.exec_module(qualify)
class QualificationFontBinding(unittest.TestCase):
 def test_optional_otf_bytes_are_bound_and_replacement_changes_identity(self):
  with tempfile.TemporaryDirectory(prefix='nocturne-otf-binding-')as directory:
   fixture=Path(directory)/'fixture.otf';fixture.write_bytes(b'OTTO exact external fixture identity A')
   env={**os.environ,'NOCTURNE_OTF_FONT':str(fixture)}
   before=qualify.toolExecutables({},env)
   self.assertIn('NOCTURNE_OTF_FONT',before)
   self.assertEqual(before['NOCTURNE_OTF_FONT']['sha256'],hashlib.sha256(fixture.read_bytes()).hexdigest())
   fixture.write_bytes(b'OTTO exact external fixture identity B');after=qualify.toolExecutables({},env)
   self.assertNotEqual(before['NOCTURNE_OTF_FONT']['sha256'],after['NOCTURNE_OTF_FONT']['sha256'])
   env.pop('NOCTURNE_OTF_FONT');self.assertNotIn('NOCTURNE_OTF_FONT',qualify.toolExecutables({},env))
if __name__=='__main__':unittest.main()
