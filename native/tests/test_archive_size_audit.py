"""Independent archive accounting never equates size/inventory with feature parity."""
from pathlib import Path
import importlib.util,sys,tempfile,unittest,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/release'))
try:from archive_size_audit import inventoryArchive,compareArchives
except ImportError:inventoryArchive=compareArchives=None
class ArchiveAccountingTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def archive(self,name,files):
        path=self.root/name
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for key,value in files:z.writestr(key,value)
        return path
    def testNativeRemovalIsReported(self):
        self.assertIsNotNone(compareArchives)
        a=self.archive('old.zip',[('sdk/native/src/a.c','int a;')]);b=self.archive('new.zip',[('sdk/README.md','hello')])
        r=compareArchives(a,b)
        self.assertEqual(r['implementationRemoved'],['native/src/a.c'])
        self.assertFalse(r['noImplementationFilesRemoved'])
    def testNormalizedSingleRootAndExactEquality(self):
        self.assertIsNotNone(compareArchives)
        a=self.archive('old.zip',[('sdk/native/src/a.c','int a;')]);b=self.archive('new.zip',[('other/native/src/a.c','int a;')])
        r=compareArchives(a,b)
        self.assertEqual(r['unchanged'],['native/src/a.c'])
        self.assertTrue(r['noImplementationFilesRemoved'])
        self.assertFalse(r['featurePortingQualified'])
    def testChangedContentIsNotUnchanged(self):
        self.assertIsNotNone(compareArchives)
        a=self.archive('old.zip',[('sdk/native/src/a.c','int a;')]);b=self.archive('new.zip',[('sdk/native/src/a.c','int b;')])
        self.assertEqual(compareArchives(a,b)['changed'],['native/src/a.c'])
    def testRemovedCaptureIsNotClassedAsRuntimeSource(self):
        self.assertIsNotNone(compareArchives)
        a=self.archive('old.zip',[('sdk/native/evidence/capture/1.png',b'png'),('sdk/native/src/a.c','int a;')])
        b=self.archive('new.zip',[('sdk/native/src/a.c','int a;')])
        r=compareArchives(a,b);self.assertTrue(r['noImplementationFilesRemoved']);self.assertEqual(len(r['removed']),1)
    def testArchiveStructureReconcilesExactly(self):
        self.assertIsNotNone(compareArchives)
        a=self.archive('old.zip',[('sdk/git/history.bundle',b'x'*100),('sdk/native/evidence/capture/a.bin',b'z'*9000)])
        b=self.archive('new.zip',[('sdk/git/history.bundle',b'x'*50)])
        r=compareArchives(a,b)
        self.assertEqual(r['sizeReductionBytes'],sum(g['savedCompressedBytes'] for g in r['categoryChanges'])+r['structureReductionBytes'])
    def testDuplicateNamesRefused(self):
        self.assertIsNotNone(inventoryArchive)
        a=self.archive('dup.zip',[('sdk/a','x'),('sdk/a','y')])
        with self.assertRaises(ValueError):inventoryArchive(a)
    def testEscapingMemberRefused(self):
        self.assertIsNotNone(inventoryArchive)
        a=self.archive('bad.zip',[('sdk/../x','x')])
        with self.assertRaises(ValueError):inventoryArchive(a)
    def testDifferentNamesSameBytesReportedNotAssumedPreserved(self):
        self.assertIsNotNone(compareArchives)
        a=self.archive('old.zip',[('sdk/native/src/a.c','int a;')]);b=self.archive('new.zip',[('sdk/native/src/b.c','int a;')])
        r=compareArchives(a,b)
        self.assertEqual(r['sameContentElsewhere']['native/src/a.c'],['native/src/b.c'])
        self.assertFalse(r['noImplementationFilesRemoved'])
if __name__=='__main__':unittest.main()
