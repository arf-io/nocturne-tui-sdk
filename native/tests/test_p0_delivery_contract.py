"""Real repository documentary custody regressions for the P0 continuation."""
from pathlib import Path
import hashlib,json,unittest
ROOT=Path(__file__).resolve().parents[2]
class GoverningContractTests(unittest.TestCase):
    def testOperatorSourcesAreByteBound(self):
        authority=json.loads((ROOT/'native/docs/contract/AUTHORITY.json').read_text())
        self.assertTrue(authority['governingContractResolved'])
        self.assertEqual(authority['baseline'],'b125a317f7c39c2bd27801e6ebf3c3fde8e6f6ca')
        for item in authority['sources']:
            self.assertEqual(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest(),item['sha256'])
        self.assertIn('Now build out the RC4 Native Architecture with the contracts defined.',authority['operatorAuthorization'])
    def testArchitectureAdoptedWithoutRewritingHistoricalCheckpoint(self):
        text=(ROOT/'native/docs/ARCHITECTURE.md').read_text()
        self.assertIn('**Status:** adopted governing RC4 architecture',text)
        self.assertIn('## 16. What this checkpoint does and does not deliver',text)
    def testTraceabilityLinksContractBacklogSourceTestsReceipts(self):
        trace=json.loads((ROOT/'native/docs/contract/TRACEABILITY.json').read_text())
        self.assertTrue(trace['governingContractResolved'])
        self.assertFalse(trace['fullRC4Qualified'])
        ids={item['id'] for item in json.loads((ROOT/'RC4-BACKLOG.json').read_text())['items']}
        self.assertGreaterEqual(len(trace['requirements']),72)
        for row in trace['requirements']:
            for key in ['contract','backlogIds','sourceFiles','tests','receipts','status']:
                self.assertIn(key,row,row['id'])
            self.assertTrue(set(row['backlogIds'])<=ids,row['id'])
            self.assertTrue((ROOT/row['contract'].split('#')[0]).is_file(),row['id'])
        self.assertGreaterEqual(len(trace['conflicts']),5)
    def testOnlyAuthorityIsClosedByDocumentaryAdoption(self):
        backlog=json.loads((ROOT/'RC4-BACKLOG.json').read_text())['items']
        items={item['id']:item for item in backlog}
        self.assertEqual(items['RC4-012']['status'],'DONE')
        for key in ['RC4-001','RC4-002','RC4-006','RC4-023']:
            self.assertEqual(items[key]['status'],'OPEN')
        self.assertFalse(json.loads((ROOT/'RELEASE.json').read_text())['fullRC4Qualified'])
if __name__=='__main__':unittest.main()
