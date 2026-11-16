"""Source-only candidate packaging is deterministic and never smuggles private state."""
from pathlib import Path
import json, os, sys, tempfile, unittest, zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
try:from package_source_candidate import packageSource
except ImportError:packageSource=None
from release_archive import extractVerified, verifyArchive

class SourceCandidateTests(unittest.TestCase):
    def tree(self,root):
        root.mkdir();(root/'native').mkdir();(root/'native/core.c').write_text('int core(void){return 1;}\n')
        (root/'run.sh').write_text('#!/bin/sh\nexit 0\n');(root/'run.sh').chmod(0o755)
    def testDeterministicAllFilePreservationAndVerifiedExtraction(self):
        self.assertIsNotNone(packageSource)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);source=base/'source';self.tree(source)
            a,b=base/'one.zip',base/'two.zip'
            one=packageSource(source,a)
            for p in source.rglob('*'):os.utime(p,(100,100))
            two=packageSource(source,b)
            self.assertEqual(a.read_bytes(),b.read_bytes());self.assertEqual(one,two)
            self.assertFalse(one['fullRC4Qualified']);self.assertFalse(one['stableRelease'])
            extracted=extractVerified(a,base/'unpacked')
            for path in source.rglob('*'):
                if path.is_file():self.assertEqual(path.read_bytes(),(extracted/path.relative_to(source)).read_bytes())
            self.assertTrue(os.access(extracted/'run.sh',os.X_OK))
            self.assertEqual(set(verifyArchive(a)['files']),{'native/core.c','run.sh'})
    def testRejectPrivateHistoryCacheCompilerAndFontInputs(self):
        self.assertIsNotNone(packageSource)
        for bad in ['.git/config','vendor/a/file.rs','target/debug/app','node_modules/a/index.js',
                    'compiler/bin/rustc','git/history.bundle','keys/private.pem','font.woff2']:
            with self.subTest(path=bad),tempfile.TemporaryDirectory() as d:
                base=Path(d);source=base/'source';self.tree(source)
                path=source/bad;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('not-distributable')
                with self.assertRaises(ValueError):packageSource(source,base/'out.zip')
                self.assertFalse((base/'out.zip').exists())
    def testRejectSymlinkAndDestinationInSourceOrExisting(self):
        self.assertIsNotNone(packageSource)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);source=base/'source';self.tree(source)
            with self.assertRaises(ValueError):packageSource(source,source/'inside.zip')
            output=base/'exists.zip';output.write_text('preserve')
            with self.assertRaises(FileExistsError):packageSource(source,output)
            self.assertEqual(output.read_text(),'preserve')
            (source/'linked').symlink_to(source/'run.sh')
            with self.assertRaises(ValueError):packageSource(source,base/'out.zip')
    def testNoSilentSourceMutationOrReservedManifest(self):
        self.assertIsNotNone(packageSource)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);source=base/'source';self.tree(source)
            (source/'MANIFEST.json').write_text('{}\n')
            with self.assertRaises(ValueError):packageSource(source,base/'out.zip')
            self.assertEqual((source/'MANIFEST.json').read_text(),'{}\n')

if __name__=='__main__':unittest.main()
