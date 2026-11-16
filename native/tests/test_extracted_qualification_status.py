"""Receipt validation inputs do not represent new runtime qualification evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'native/scripts'))
import verify_contracts_package as verifier

class ExtractedQualificationStatus(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((ROOT / 'native/tests/fixtures/release-build-receipt-c7deb564.json').read_text())

    def testCandidateRemainsFalse(self):
        self.receipt['fullRC4Qualified'] = False
        self.assertIs(verifier.extractedQualificationStatus(self.receipt, self.receipt['sourceAfter'], False), False)

    def testQualifiedFinalDeclarationPropagatesTrue(self):
        self.receipt['fullRC4Qualified'] = True
        self.assertIs(verifier.extractedQualificationStatus(self.receipt, self.receipt['sourceAfter'], True), True)

    def testFinalDeclarationRejectsMissingQualification(self):
        for invalid in (False, None, 'true', 1):
            with self.subTest(invalid=invalid):
                self.receipt['fullRC4Qualified'] = invalid
                with self.assertRaises(ValueError):
                    verifier.extractedQualificationStatus(self.receipt, self.receipt['sourceAfter'], True)

    def testFinalDeclarationRejectsIncompleteAndChangedSource(self):
        self.receipt['fullRC4Qualified'] = True
        for key in ('complete', 'sourceUnchanged', 'localBuildVerified', 'fourRuntimeVerified'):
            receipt = copy.deepcopy(self.receipt)
            receipt[key] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                verifier.extractedQualificationStatus(receipt, receipt['sourceAfter'], True)
        with self.assertRaises(ValueError):
            verifier.extractedQualificationStatus(self.receipt, '0' * 64, True)

if __name__ == '__main__':
    unittest.main()
