"""Validation uses the real 109-row ledger and source bytes, not simulated hosts."""
from pathlib import Path
import copy,importlib.util,json,unittest,tempfile
ROOT=Path(__file__).resolve().parents[2]
class P0ReviewTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('p0_review',ROOT/'tools/rc4/build_operator_review.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.ledger=json.loads((ROOT/'native/port-ledger.json').read_text())
    def testAllRealSourceIdentitiesArePending(self):
        rows=self.module.reviewRows(ROOT,self.ledger)
        self.assertEqual(len(rows),109)
        self.assertEqual(len({r['oldId'] for r in rows}),109)
        self.assertTrue(all(r['decision']=='' and r['accepted'] is False for r in rows))
    def testChangedSourceHashRejected(self):
        ledger=copy.deepcopy(self.ledger);ledger['entries'][0]['source']['sha256']='0'*64
        with self.assertRaises(ValueError):self.module.reviewRows(ROOT,ledger)
    def testMissingOrDuplicateIdentityRejected(self):
        ledger=copy.deepcopy(self.ledger);ledger['entries'].pop()
        with self.assertRaises(ValueError):self.module.reviewRows(ROOT,ledger)
        ledger=copy.deepcopy(self.ledger);ledger['entries'][1]=ledger['entries'][0]
        with self.assertRaises(ValueError):self.module.reviewRows(ROOT,ledger)
    def testUnsafeSourceRejected(self):
        ledger=copy.deepcopy(self.ledger);ledger['entries'][0]['source']['path']='../outside-source'
        with self.assertRaises(ValueError):self.module.reviewRows(ROOT,ledger)
    def testPlatformAndExplicitRuntimeSelection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();dist=root/'native/dist';dist.mkdir(parents=True)
            for name in ['libnocturne_native.dylib','libnocturne_native.so']:(dist/name).write_bytes(name.encode())
            self.assertEqual(self.module.reviewLibrary(root,platform='darwin'),dist/'libnocturne_native.dylib')
            self.assertEqual(self.module.reviewLibrary(root,platform='linux'),dist/'libnocturne_native.so')
            custom=root/'custom.dylib';custom.write_bytes(b'actual input')
            self.assertEqual(self.module.reviewLibrary(root,custom,platform='darwin'),custom)
    def testMissingAndSymlinkRuntimeRejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            with self.assertRaises(ValueError):self.module.reviewLibrary(root,platform='darwin')
            actual=root/'actual';actual.write_bytes(b'library');link=root/'link';link.symlink_to(actual)
            with self.assertRaises(ValueError):self.module.reviewLibrary(root,link)
if __name__=='__main__':unittest.main()
