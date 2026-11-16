from pathlib import Path
import hashlib
import json
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]

class CompositionExportVerifier(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.output=self.root/'export'
        source=self.root/'composition.json';source.write_text(json.dumps({'schema':'nocturne.composition.v1','seed':73,'commands':[{'op':'input','text':'Independent verification'}]}))
        r=subprocess.run(['node',str(ROOT/'native/scripts/validate_composition.mjs'),str(source),'--output',str(self.output),'--time-us','400000'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
    def verify(self,*extra):
        return subprocess.run(['node',str(ROOT/'native/scripts/verify_composition_export.mjs'),str(self.output),*extra],capture_output=True,text=True,timeout=30)
    def testGenuineExportRecreatedWithoutChangingFiles(self):
        before={p.name:p.read_bytes() for p in self.output.iterdir()};r=self.verify();self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertTrue(json.loads(r.stdout)['passed']);self.assertEqual(before,{p.name:p.read_bytes() for p in self.output.iterdir()})
    def testCorruptionAndRehashedFalseMetadataReject(self):
        info=self.output/'scene-info.json';original=info.read_bytes();info.write_bytes(b'corrupt')
        self.assertNotEqual(self.verify().returncode,0)
        value=json.loads(original);value['prompt']['text']='Unsupported assertion';changed=json.dumps(value).encode();info.write_bytes(changed)
        manifest=self.output/'MANIFEST.json';m=json.loads(manifest.read_text());m['files']['scene-info.json']={'bytes':len(changed),'sha256':hashlib.sha256(changed).hexdigest()};manifest.write_text(json.dumps(m))
        r=self.verify();self.assertNotEqual(r.returncode,0);self.assertIn('metadata',json.loads(r.stdout)['error'])
    def testMissingRuntimeAndUnexpectedFileReject(self):
        self.assertNotEqual(self.verify('--wasm',str(self.root/'absent.wasm')).returncode,0)
        (self.output/'unexpected.txt').write_text('extra');self.assertNotEqual(self.verify().returncode,0)

if __name__=='__main__':unittest.main()
