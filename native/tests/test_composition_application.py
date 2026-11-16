"""Exercise the consumer starter against actual native and WASM runtimes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / 'native/examples/composition_application.py'


class CompositionApplication(unittest.TestCase):
    def run_app(self, source, output):
        return subprocess.run([
            sys.executable, str(STARTER), str(source), '--output', str(output),
            '--time-us', '125000',
        ], cwd=ROOT, capture_output=True, text=True, timeout=30)

    def testNativeApplicationReproducesActualWasmComposition(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'composition.json'
            document = {'schema': 'nocturne.composition.v1', 'seed': 73, 'commands': [
                {'op': 'resize', 'width': 64, 'height': 24},
                {'op': 'input', 'text': 'Reusable consumer screen'},
            ]}
            source.write_text(json.dumps(document))
            output = root / 'native-screen'
            native = self.run_app(source, output)
            self.assertEqual(native.returncode, 0, native.stderr + native.stdout)
            wasm = subprocess.run([
                'node', str(ROOT / 'native/scripts/validate_composition.mjs'),
                str(source), '--output', str(root / 'wasm-screen'),
                '--time-us', '125000',
            ], cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(wasm.returncode, 0, wasm.stderr + wasm.stdout)
            for name in ['composition.json', 'scene.cells', 'scene.snapshot']:
                self.assertEqual((output / name).read_bytes(), (root / 'wasm-screen' / name).read_bytes(), name)
            manifest = json.loads((output / 'MANIFEST.json').read_text())
            for name, record in manifest['files'].items():
                data = (output / name).read_bytes()
                self.assertEqual(len(data), record['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'])
            self.assertTrue(json.loads(native.stdout)['renderPure'])
            self.assertEqual(json.loads((output / 'scene-info.json').read_text())['prompt']['text'], 'Reusable consumer screen')

    def testInvalidDocumentsAndNativeCommandsNeverCreateOutput(self):
        documents = [
            {'schema': 'unknown', 'seed': 1, 'commands': []},
            {'schema': 'nocturne.composition.v1', 'seed': True, 'commands': []},
            {'schema': 'nocturne.composition.v1', 'seed': 1, 'commands': [None]},
            {'schema': 'nocturne.composition.v1', 'seed': 1, 'commands': [{'op': 'unknown-command'}]},
            {'schema': 'nocturne.composition.v1', 'seed': 1, 'commands': [], 'unowned': 1},
        ]
        for document in documents:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / 'composition.json'
                source.write_text(json.dumps(document))
                result = self.run_app(source, root / 'output')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / 'output').exists())
                self.assertFalse(json.loads(result.stdout)['passed'])

    def testExistingOutputIsPreserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'composition.json'
            source.write_text(json.dumps({'schema': 'nocturne.composition.v1', 'seed': 1, 'commands': []}))
            output = root / 'output'
            output.mkdir()
            (output / 'keep.txt').write_bytes(b'preserved')
            result = self.run_app(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(output.iterdir()), [output / 'keep.txt'])
            self.assertEqual((output / 'keep.txt').read_bytes(), b'preserved')
