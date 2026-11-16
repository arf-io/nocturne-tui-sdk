"""A released working tree must agree with its Git index after history restoration."""
from pathlib import Path
import importlib.util,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import package_contracts
class PackageMetadataTests(unittest.TestCase):
    def testStableTrackedMetadataIsNotReplacedByExport(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'RELEASE.json').write_text('{"build":"candidate"}\n')
            (root/'BUILD-IDENTITY.json').write_text('{"abi":1}\n')
            files={}
            package_contracts.includeTrackedReleaseMetadata(root,files)
            self.assertEqual(files['RELEASE.json'],root/'RELEASE.json')
            self.assertEqual(files['BUILD-IDENTITY.json'],root/'BUILD-IDENTITY.json')
    def testMissingMetadataFailsRatherThanGeneratingInventedPass(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):package_contracts.includeTrackedReleaseMetadata(Path(d),{})
if __name__=='__main__':unittest.main()
