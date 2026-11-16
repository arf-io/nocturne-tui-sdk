from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class NativeCompositionExportVerifier(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'export'
        run = subprocess.run([sys.executable, str(ROOT / 'native/examples/composition_application.py'),
                              str(ROOT / 'native/examples/consumer-start.composition.json'),
                              '--time-us', '125000', '--output', str(self.output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)

    def verify(self, *extra):
        return subprocess.run([sys.executable, str(ROOT / 'native/scripts/verify_native_composition_export.py'),
                               str(self.output), *extra], capture_output=True, text=True)

    def testGenuineExportRecreatedWithoutChangingFiles(self):
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def testRehashedFalseMetadataAndCorruptFrameReject(self):
        info = self.output / 'scene-info.json'
        data = json.loads(info.read_text())
        data['prompt']['text'] = 'Unsupported claim'
        info.write_text(json.dumps(data))
        manifest = self.output / 'MANIFEST.json'
        record = json.loads(manifest.read_text())
        record['files']['scene-info.json'] = {'bytes': info.stat().st_size, 'sha256': hashlib.sha256(info.read_bytes()).hexdigest()}
        manifest.write_text(json.dumps(record))
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('metadata', json.loads(result.stdout)['error'])
        (self.output / 'scene.cells').write_bytes(b'corrupt')
        self.assertNotEqual(self.verify().returncode, 0)

    def testUnexpectedFileAndMissingRuntimeReject(self):
        self.assertNotEqual(self.verify('--library', str(self.root / 'missing.so')).returncode, 0)
        (self.output / 'extra.txt').write_text('extra')
        self.assertNotEqual(self.verify().returncode, 0)
