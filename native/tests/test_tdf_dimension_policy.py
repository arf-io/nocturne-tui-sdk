from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'integrations'))
sys.path.insert(0,str(ROOT/'native/scripts'))
from tdfiglet_bridge import parseAnsi
from qualify import fingerprint

class TdfDimensionPolicy(unittest.TestCase):
    def testWideTallAnsiHasNoImplicitAxisCeiling(self):
        art=parseAnsi('\x1b[31m'+'\n'.join(['A'*101]*25))
        self.assertEqual((art['width'],art['height']),(101,25))
        self.assertEqual(len(art['cells']),101*25*4)
        self.assertEqual(art['cells'][:3],[ord('A'),0xaa0000,0])

    def testExplicitCallerAxisBoundsRemainEnforced(self):
        with self.assertRaises(ValueError):parseAnsi('A'*101,maxWidth=100)
        with self.assertRaises(ValueError):parseAnsi('\n'.join(['A']*25),maxHeight=24)

    def testSparseRectangleBudgetRejectsBeforeLargeAllocation(self):
        with self.assertRaisesRegex(ValueError,'budget'):
            parseAnsi('A'*101+'\nB',maxCells=150)

    def testShippedIntegrationCodeIsSourceFingerprintBound(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'native';root.mkdir();folder=root.parent/'integrations';folder.mkdir()
            p=folder/'tdfiglet_bridge.py';p.write_text('first source\n')
            before=fingerprint(root)['sha256'];p.write_text('changed source\n')
            self.assertNotEqual(before,fingerprint(root)['sha256'])

if __name__=='__main__':unittest.main()
