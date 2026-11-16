import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'native/scripts'))
import manual_inventory

class ManualAbiInventory(unittest.TestCase):
    def testMultilinePointerDeclarationsAndCommentExclusion(self):
        header='''/* int nrFake(void); */
typedef struct NrContext NrContext;
const char *nrInfo(const NrContext *context);
int nrSample(const double *values,
             unsigned int count, double *out);
'''
        rows=manual_inventory.abiDeclarations(header)
        self.assertEqual([r['name'] for r in rows],['nrInfo','nrSample'])
        self.assertEqual(rows[0]['signature'],'const char *nrInfo(const NrContext *context);')
        self.assertIn('unsigned int count, double *out',rows[1]['signature'])

    def testDuplicatePublicNamesReject(self):
        with self.assertRaises(ValueError):
            manual_inventory.abiDeclarations('int nrInfo(void);\nint nrInfo(int value);')

    def testActualRepositoryAbiAndAllFourHostSourcesAreRepresented(self):
        authoring=json.loads(gzip.decompress((ROOT/'native/evidence/manual-inventory-20261012/authoring.json.gz').read_bytes()))
        inventory=manual_inventory.buildInventory(ROOT,authoring)
        names={r['name'] for r in inventory['abiMethods']}
        self.assertTrue({'nrContextSize','nrNegotiateShortcuts','nrTextTrailSample','nrTextClusterSample'}<=names)
        self.assertEqual({r['host'] for r in inventory['hosts']},{'prompt-toolkit','terminal-kit','bubbletea','ratatui'})
        for row in inventory['hosts']:
            self.assertTrue((ROOT/row['source']).is_file())
            self.assertIn(row['source'],inventory['sources'])
            self.assertTrue(row['missingEvidence'])
        manual_inventory.validateSource(inventory,ROOT)

if __name__=='__main__':unittest.main()
