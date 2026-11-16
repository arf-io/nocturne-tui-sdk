from pathlib import Path
import copy
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'native/scripts'));sys.path.insert(0,str(ROOT/'native/examples'))
from parameter_reference import buildReference
from gallery_cases import build_cases

class ParameterReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata=json.loads((ROOT/'native/web/workshop_fields.json').read_text());cls.cases=build_cases()
    @unittest.skipIf((ROOT/'PUBLIC-TREE-REPORT.json').is_file(),'the fixture studies that exercise every field are left out of the public tree')
    def testAllCurrentFieldsHaveStableReferenceAndActualCasePresence(self):
        result=buildReference(ROOT,self.metadata,self.cases)
        self.assertEqual(len(result['operations']),len(self.metadata['operations']))
        self.assertEqual(len(result['parameters']),len(self.metadata['fields']))
        alpha=next(p for p in result['parameters'] if p['id']=='parameter:widget.alpha')
        self.assertTrue(alpha['caseIds']);self.assertEqual(alpha['types'],next(p['types'] for p in self.metadata['fields'] if p['op']=='widget' and p['field']=='alpha'))
        actual={c['id'] for c in self.cases};self.assertTrue(all(set(p['caseIds'])<=actual for p in result['parameters']))
        self.assertFalse(result['manualComplete']);self.assertFalse(result['semanticCoverageProven'])
    def testStaleDuplicateAndOrphanMetadataReject(self):
        for kind in ['stale','duplicate','orphan']:
            data=copy.deepcopy(self.metadata)
            if kind=='stale':data['sourceSha256']='0'*64
            elif kind=='duplicate':data['fields'].append(data['fields'][0])
            else:data['fields'][0]['op']='not-a-public-operation'
            with self.subTest(kind=kind),self.assertRaises(ValueError):buildReference(ROOT,data,self.cases)

if __name__=='__main__':unittest.main()
