from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_contracts import copyHandoffDocuments

class PackageHandoff(unittest.TestCase):
    def testCurrentGuidanceAndLegacyAreBothPreservedExactly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            output = Path(temporary) / 'delivery'
            root.mkdir(); output.mkdir()
            (root / 'HANDOFF.md').write_bytes(b'Current source and unfinished release gates\n')
            (root / 'LLM-HANDOFF.md').write_bytes(b'Historical guidance\n')
            copied = copyHandoffDocuments(root, output, 'Nocturne-1.0.0-rc.1')
            self.assertEqual((output / 'Nocturne-1.0.0-rc.1-Handoff.md').read_bytes(), (root / 'HANDOFF.md').read_bytes())
            self.assertEqual((output / 'Nocturne-1.0.0-rc.1-LLM-Handoff.md').read_bytes(), (root / 'LLM-HANDOFF.md').read_bytes())
            self.assertEqual(len(copied), 2)

    def testLegacyOnlySourceRetainsItsExistingHandoffExport(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'; root.mkdir()
            output = Path(temporary) / 'delivery'; output.mkdir()
            (root / 'LLM-HANDOFF.md').write_bytes(b'Legacy source guidance\n')
            copyHandoffDocuments(root, output, 'candidate')
            self.assertEqual((output / 'candidate-Handoff.md').read_bytes(), b'Legacy source guidance\n')
            self.assertEqual((root / 'LLM-HANDOFF.md').read_bytes(), b'Legacy source guidance\n')

    def testMissingOptionalGuidanceDoesNotInventHandoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'; root.mkdir()
            output = Path(temporary) / 'delivery'; output.mkdir()
            self.assertEqual(copyHandoffDocuments(root, output, 'candidate'), [])
            self.assertEqual(list(output.iterdir()), [])
