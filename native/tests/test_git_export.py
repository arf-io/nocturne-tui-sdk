"""Exact-source and union-history export tests using real disposable Git repositories."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
EXPORTER = ROOT / 'tools/release/export_git.py'


def git(root, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=root, text=True).strip()


class GitExportTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(EXPORTER.is_file(), 'Missing exact-tree Git exporter')
        spec = importlib.util.spec_from_file_location('nocturne_export_git', EXPORTER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.name', 'Nocturne export tests')
        git(self.root, 'config', 'user.email', 'nocturne-tests@example.invalid')
        (self.root / 'README.md').write_text('Exact committed source.\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'Initial source')
        self.baseline = git(self.root, 'rev-parse', 'HEAD')
        self.declaration = {
            'build': '0.9.0-rc.4+export-test', 'sourceBaseline': self.baseline,
            'verification': 'native/evidence/BUILD-VERIFICATION.json',
            'fullRC4Qualified': False, 'state': 'RELEASE_CANDIDATE',
            'scope': 'Source integrity test; runtime qualification is unexecuted.',
        }
        (self.root / 'RELEASE.json').write_text(json.dumps(self.declaration) + '\n')
        (self.root / '.gitattributes').write_text('hidden.txt export-ignore\nsubstituted.txt export-subst\n')
        (self.root / 'hidden.txt').write_text('Tracked content must survive export-ignore.\n')
        (self.root / 'substituted.txt').write_text('$Format:%H$\n')
        (self.root / 'run.sh').write_text('#!/bin/sh\nexit 0\n')
        (self.root / 'run.sh').chmod(0o755)
        (self.root / 'Unicode space λ.txt').write_text('λ, τ, and spaces.\n')
        (self.root / 'binary.dat').write_bytes(bytes(range(256)))
        self.commit()
        git(self.root, 'branch', 'historical', self.baseline)
        git(self.root, 'tag', '-a', 'historical-tag', '-m', 'Retain annotated tag', self.baseline)
        git(self.root, 'update-ref', 'refs/archive/earlier/source', self.baseline)
        git(self.root, 'update-ref', 'refs/handoff/original', self.commitId)

    def commit(self):
        git(self.root, 'add', '-A')
        git(self.root, 'commit', '-qm', 'Committed export inputs')
        self.commitId = git(self.root, 'rev-parse', 'HEAD')

    def export(self, name='export'):
        output = self.base / name
        result = self.module.exportGit(self.root, self.commitId, output)
        return output, result

    def testTarIsDeterministicAndContainsEveryExactTrackedByte(self):
        out1, first = self.export('one')
        out2, second = self.export('two')
        archive = out1 / first['artifacts']['sourceTar']['name']
        self.assertEqual(first['artifacts']['sourceTar']['sha256'], second['artifacts']['sourceTar']['sha256'])
        self.assertEqual(archive.read_bytes(), (out2 / second['artifacts']['sourceTar']['name']).read_bytes())
        # ls-tree quotePath handling is irrelevant to the binary-safe exporter;
        # use the manifest for exact non-ASCII path names here.
        expected = {path: subprocess.check_output(['git', 'show', self.commitId + ':' + path], cwd=self.root)
                    for path in first['files']}
        with tarfile.open(archive, 'r:gz') as tar:
            members = {member.name: member for member in tar if not member.isdir()}
            self.assertEqual(set(members), {'nocturne/' + path for path in expected})
            for path, content in expected.items():
                member = members['nocturne/' + path]
                self.assertEqual(tar.extractfile(member).read(), content)
                self.assertEqual((member.uid, member.gid, member.uname, member.gname), (0, 0, '', ''))
            self.assertEqual(members['nocturne/run.sh'].mode, 0o755)
        self.assertIn('hidden.txt', first['files'])
        self.assertTrue(first['integrity']['freshBundleRestoreVerified'])
        self.assertTrue(first['integrity']['freshTarExtractionVerified'])

    def testBundleRestoresAllNamedRefsIncludingAnnotatedTagsAndCustomNamespaces(self):
        output, result = self.export()
        restored = self.base / 'independent.git'
        git(self.base, 'init', '--bare', '-q', str(restored))
        bundle = output / result['artifacts']['historyBundle']['name']
        subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=restored, check=True, capture_output=True)
        subprocess.run(['git', 'fetch', '--no-tags', str(bundle), 'refs/*:refs/*'], cwd=restored, check=True, capture_output=True)
        expected = git(self.root, 'for-each-ref', '--format=%(objectname) %(refname)').splitlines()
        actual = git(restored, 'for-each-ref', '--format=%(objectname) %(refname)').splitlines()
        self.assertEqual(actual, expected)
        self.assertIn('refs/archive/earlier/source', result['namedRefs'])
        self.assertIn('refs/handoff/original', result['namedRefs'])
        self.assertEqual(git(restored, 'rev-parse', 'historical-tag'), git(self.root, 'rev-parse', 'historical-tag'))

    def testDirtyAndUntrackedFilesDoNotChangeExactCommittedPayload(self):
        (self.root / 'README.md').write_text('Uncommitted change must not leak into exact source.\n')
        (self.root / 'private-untracked.txt').write_text('Not a Git object.\n')
        output, result = self.export()
        with tarfile.open(output / result['artifacts']['sourceTar']['name']) as tar:
            self.assertEqual(tar.extractfile('nocturne/README.md').read(), b'Exact committed source.\n')
            self.assertNotIn('nocturne/private-untracked.txt', tar.getnames())

    def testUnqualifiedSourceExportsWithoutClaimingRuntimeSuccess(self):
        output, result = self.export()
        self.assertEqual(result['status'], 'SOURCE_HISTORY_VERIFIED')
        self.assertEqual(result['runtimeQualification']['status'], 'NOT_ASSESSED_BY_EXPORTER')
        self.assertIs(result['runtimeQualification']['declaredFullRC4Qualified'], False)
        self.assertEqual(result['sourceCommit'], self.commitId)
        document = (output / result['artifacts']['sourceContents']['name']).read_text()
        self.assertIn('Tracked content must survive export-ignore.', document)
        self.assertIn('$Format:%H$', document)
        self.assertIn(hashlib.sha256(bytes(range(256))).hexdigest(), document)

    def testDisallowedTrackedFilesFailInsteadOfSilentlyOmittingThem(self):
        initial = self.commitId
        for index, name in enumerate(('font.woff2', 'node_modules/dependency/index.js', '.env', 'bin/rustc')):
            with self.subTest(name=name):
                git(self.root, 'reset', '--hard', initial)
                self.commitId = initial
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Disallowed export input.\n')
                self.commit()
                with self.assertRaisesRegex(ValueError, 'disallowed'):
                    self.export('invalid' + str(index))

    def testDeletedDisallowedFileStillBlocksReachableHistoryBundle(self):
        path = self.root / 'historical.otf'
        path.write_text('Historical font bytes.\n')
        self.commit()
        path.unlink()
        self.commit()
        with self.assertRaisesRegex(ValueError, 'disallowed.*historical.otf'):
            self.export()

    def testPrivateKeyContentFailsEvenWithAnInnocentFileName(self):
        (self.root / 'notes.txt').write_text('-----BEGIN ' + 'PRIVATE KEY-----\nnot-a-real-key\n')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'private key'):
            self.export()

    def testSymlinkIsRefusedBeforeExport(self):
        os.symlink('../../outside', self.root / 'escaping-link')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.export()

    def testExactFullCommitAndExternalNewOutputAreRequired(self):
        with self.assertRaisesRegex(ValueError, 'exact full commit'):
            self.module.exportGit(self.root, 'HEAD', self.base / 'symbolic')
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.module.exportGit(self.root, self.commitId, self.root / 'out')
        existing = self.base / 'existing'
        existing.mkdir()
        with self.assertRaisesRegex(ValueError, 'new output'):
            self.module.exportGit(self.root, self.commitId, existing)


if __name__ == '__main__':
    unittest.main()
