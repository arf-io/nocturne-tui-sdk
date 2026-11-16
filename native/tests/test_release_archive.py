"""Archive acceptance is independent of an old status file or ZIP filename."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest,warnings,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from release_archive import verifyArchive, extractVerified

def digest(data):return hashlib.sha256(data).hexdigest()
class ReleaseArchiveTests(unittest.TestCase):
    def make(self, folder, *, payload=None, extra=None, metadata=None):
        payload=payload or {'README.md':b'Hello\n','native/src/a.c':b'int value=1;\n'}
        manifest={'sourceCommit':'0123456789','files':{name:{'bytes':len(data),'sha256':digest(data)} for name,data in payload.items()}}
        path=folder/'sdk.zip'
        with zipfile.ZipFile(path,'w') as z:
            for name,data in payload.items():z.writestr('nocturne-sdk/'+name,data)
            if extra:
                for name,data in extra:z.writestr(name,data)
            z.writestr('nocturne-sdk/MANIFEST.json',json.dumps(metadata or manifest))
        return path
    def testValidExactArchive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.make(root);r=verifyArchive(p)
            self.assertEqual(len(r['files']),2)
            out=extractVerified(p,root/'out');self.assertEqual((out/'README.md').read_bytes(),b'Hello\n')
    def testExtractionNeverOverwrites(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.make(root);(root/'out').mkdir()
            with self.assertRaises(FileExistsError):extractVerified(p,root/'out')
    def testExtraUnlistedFileRejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(Path(d),extra=[('nocturne-sdk/hidden.txt',b'x')])
            with self.assertRaises(ValueError):verifyArchive(p)
    def testDuplicateRejected(self):
        with tempfile.TemporaryDirectory() as d, warnings.catch_warnings():
            warnings.simplefilter('ignore');p=self.make(Path(d),extra=[('nocturne-sdk/README.md',b'x')])
            with self.assertRaises(ValueError):verifyArchive(p)
    def testEscapingPathsRejected(self):
        for name in ['../escape','/absolute','other/file','nocturne-sdk/../escape','nocturne-sdk/./x','nocturne-sdk\\escape','nocturne-sdk/x:stream']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                p=self.make(Path(d),extra=[(name,b'x')])
                with self.assertRaises(ValueError):verifyArchive(p)
    def testSymlinkRejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(Path(d));i=zipfile.ZipInfo('nocturne-sdk/link');i.external_attr=0o120777<<16
            with zipfile.ZipFile(p,'a') as z:z.writestr(i,b'/etc/passwd')
            with self.assertRaises(ValueError):verifyArchive(p)
    def testPayloadHashMismatchRejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(Path(d),metadata={'files':{'README.md':{'bytes':6,'sha256':'0'*64},'native/src/a.c':{'bytes':13,'sha256':'0'*64}}})
            with self.assertRaises(ValueError):verifyArchive(p)
    def testManifestCannotOmitFile(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(Path(d),metadata={'files':{}})
            with self.assertRaises(ValueError):verifyArchive(p)
    def testManifestCannotIncludeItself(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(Path(d),metadata={'files':{'MANIFEST.json':{'bytes':0,'sha256':'0'*64}}})
            with self.assertRaises(ValueError):verifyArchive(p)
    def testCapacityCheckBeforeExtraction(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(Path(d))
            with self.assertRaises(ValueError):verifyArchive(p,maxExpandedBytes=3)
    def testFilesAreReadableAfterExtraction(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.make(root);out=extractVerified(p,root/'out')
            self.assertEqual((out/'README.md').stat().st_mode&0o777,0o644)
if __name__=='__main__':unittest.main()
