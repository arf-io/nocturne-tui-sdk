"""Package actual built browser artifacts without dropping data."""
import base64,gzip,importlib.util,json,os,re,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artifact_package',ROOT/'scripts/package_gallery_artifact.py')

class GalleryArtifactPackaging(unittest.TestCase):
 def report_path(self):
  if os.environ.get('NOCTURNE_COMPARISON_REPORT'):return Path(os.environ['NOCTURNE_COMPARISON_REPORT'])
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);root=Path(temporary.name)
  with tarfile.open(ROOT/'evidence/rc2-window-gallery-20261014/captures-05.tar.gz') as archive:archive.extractall(root,filter='data')
  source=importlib.util.spec_from_file_location('comparison_report',ROOT/'scripts/report_rc2_window_compositions.py')
  module=importlib.util.module_from_spec(source);source.loader.exec_module(module)
  path=root/'report.html';path.write_text(module.build_report(module.load_captures(root/'captures-05'),'gallery.html'));return path
 def test_actual_gallery_and_report_payload_bytes_are_preserved(self):
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  for source,kind in [(ROOT/'Nocturne-RC4-Source-Build.html','gallery'),(self.report_path(),'report')]:
   with self.subTest(kind=kind):
    original=source.read_text();packed,raw=module.package_html(original)
    pattern=r'decodeArtifactData\("([A-Za-z0-9+/=]+)"\)' if kind=='gallery' else r'id="capture-index">([A-Za-z0-9+/=]+)</script>'
    payload=re.search(pattern,packed).group(1)
    self.assertEqual(gzip.decompress(base64.b64decode(payload)).decode(),raw)
    self.assertGreater(len(json.loads(raw)),0);self.assertLess(len(packed.encode()),16*1024*1024)
    if kind=='gallery':self.assertIn('const recipes=await decodeArtifactData(',packed)
    else:self.assertEqual(len(json.loads(raw)),96)
    with self.assertRaises(ValueError):module.package_html(packed)
 def test_unknown_and_broken_documents_reject(self):
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  for data in ['', '<html></html>','const recipes=[broken;','const recipes=[];']:
   with self.subTest(data=data),self.assertRaises(ValueError):module.package_html(data)

 def test_existing_output_is_preserved_by_real_packager(self):
  with tempfile.TemporaryDirectory() as temporary:
   output=Path(temporary)/'gallery.html';output.write_bytes(b'existing artifact')
   result=subprocess.run([sys.executable,str(ROOT/'scripts/package_gallery_artifact.py'),str(ROOT/'Nocturne-RC4-Source-Build.html'),str(output)],capture_output=True,text=True,timeout=30)
   self.assertNotEqual(result.returncode,0);self.assertIn('FileExistsError',result.stderr)
   self.assertEqual(output.read_bytes(),b'existing artifact')
