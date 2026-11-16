"""Original runtime custody using real compressed files, without home paths."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import base64
import gzip
import hashlib
import io
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from native.tests.historical_reference import (
    RC2_ARCHIVE_FIXTURE, RC2_ARCHIVE_SHA256, RC2_FIXTURE, RC2_HTML_SHA256, RC2_WASM_SHA256,
    load_rc2_archive, load_rc2_workbench, rc2_workbench_file,
)


class HistoricalReference(unittest.TestCase):
    def test_exact_original_source_embedded_runtime_and_manifest(self):
        text = load_rc2_workbench()
        self.assertEqual(len(text.encode('utf-8')), 875089)
        self.assertEqual(hashlib.sha256(text.encode('utf-8')).hexdigest(), RC2_HTML_SHA256)
        payloads = re.findall(r'[A-Za-z0-9+/]{1000,}={0,2}', text)
        wasm = [base64.b64decode(payload) for payload in payloads
                if base64.b64decode(payload).startswith(b'\x00asm')]
        self.assertTrue(any(hashlib.sha256(data).hexdigest() == RC2_WASM_SHA256 for data in wasm))
        manifest = json.loads(RC2_FIXTURE.with_suffix('.json').read_text())
        self.assertEqual(manifest['htmlSha256'], RC2_HTML_SHA256)
        self.assertEqual(manifest['wasmSha256'], RC2_WASM_SHA256)
        self.assertEqual(manifest['fixtureSha256'], hashlib.sha256(RC2_FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(manifest['archiveFixture'], RC2_ARCHIVE_FIXTURE.name)
        self.assertEqual(manifest['archiveFixtureBytes'], len(load_rc2_archive()))
        self.assertEqual(manifest['archiveFixtureSha256'], hashlib.sha256(load_rc2_archive()).hexdigest())
        self.assertEqual(manifest['archiveEntry'], 'Nocturne-Workbench-Docs.html')

    def test_standalone_original_file_lifetime_and_owned_text(self):
        with rc2_workbench_file() as path:
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), load_rc2_workbench().encode('utf-8'))
            self.assertEqual(path.name, 'Nocturne-Workbench-Docs.html')
        self.assertFalse(path.exists())
        self.assertEqual(hashlib.sha256(load_rc2_workbench().encode()).hexdigest(), RC2_HTML_SHA256)

    def test_exact_original_archive_and_every_edition_match_portable_manifest(self):
        archive = load_rc2_archive()
        self.assertEqual(len(archive), 2835114)
        self.assertEqual(hashlib.sha256(archive).hexdigest(), RC2_ARCHIVE_SHA256)
        editions_path = Path(__file__).resolve().parents[1] / 'evidence/gallery-presentation-20261013/original-reference/EDITIONS.json'
        editions = json.loads(editions_path.read_text())
        self.assertEqual(editions['archiveSha256'], RC2_ARCHIVE_SHA256)
        self.assertEqual(len(editions['editions']), 32)
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            self.assertEqual(set(bundle.namelist()),
                             {row['entry'] for row in editions['editions']} | {'README.txt'})
            for row in editions['editions']:
                content = bundle.read(row['entry'])
                with self.subTest(edition=row['entry']):
                    self.assertEqual(len(content), row['bytes'])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), row['sha256'])
            self.assertEqual(bundle.read('Nocturne-Workbench-Docs.html'),
                             load_rc2_workbench().encode('utf-8'))

    def test_missing_corrupt_and_modified_original_archive_reject(self):
        from native.tests.historical_reference import RC2_ARCHIVE_FIXTURE

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.zip'
            with self.assertRaises(ValueError):
                load_rc2_archive(path)
            for data in (b'not a zip', RC2_ARCHIVE_FIXTURE.read_bytes()[:-20],
                         RC2_ARCHIVE_FIXTURE.read_bytes() + b'changed'):
                path.write_bytes(data)
                with self.subTest(length=len(data)), self.assertRaises(ValueError):
                    load_rc2_archive(path)
            path.write_bytes(RC2_ARCHIVE_FIXTURE.read_bytes())
            self.assertEqual(load_rc2_archive(path), load_rc2_archive())

    def test_missing_corrupt_and_recompressed_altered_original_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.html.gz'
            with self.assertRaises(ValueError):
                load_rc2_workbench(path)
            for data in (b'not gzip', RC2_FIXTURE.read_bytes()[:-20],
                         gzip.compress(b'altered original reference', mtime=0)):
                path.write_bytes(data)
                with self.subTest(length=len(data)), self.assertRaises(ValueError):
                    load_rc2_workbench(path)
            path.write_bytes(RC2_FIXTURE.read_bytes())
            self.assertEqual(load_rc2_workbench(path), load_rc2_workbench())


if __name__ == '__main__':
    unittest.main()
