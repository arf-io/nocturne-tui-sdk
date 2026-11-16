"""Archived real receipts exercise policy; these are not new runtime passes."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'native/scripts'))
from runtime_qualification import runtimePlanQualified

class RuntimeQualificationStatus(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((ROOT/'native/tests/fixtures/release-build-receipt-c7deb564.json').read_text())
        self.rows=self.receipt['commands'];self.ids=[r['id'] for r in self.rows]
    def evaluate(self,**changes):
        args=dict(complete=True,sourceUnchanged=True,strict=True,capture=True,
                  expectedCaseIds=self.ids,commands=self.rows,fourRuntimePassed=True)
        args.update(changes);return runtimePlanQualified(**args)
    def testExactExecutedPlanQualifiesRuntimeScope(self):self.assertTrue(self.evaluate())
    def testEveryRequiredPolicyIsStrictBoolean(self):
        for key in ['complete','sourceUnchanged','strict','capture','fourRuntimePassed']:
            for value in [False,None,1,'true']:
                with self.subTest(key=key,value=value):self.assertFalse(self.evaluate(**{key:value}))
    def testIncompleteDuplicateAndReorderedCasesReject(self):
        for rows in [self.rows[:-1],self.rows+[self.rows[-1]],list(reversed(self.rows)),[]]:
            self.assertFalse(self.evaluate(commands=rows))
        self.assertFalse(self.evaluate(expectedCaseIds=self.ids+[self.ids[-1]],commands=self.rows+[self.rows[-1]]))
        self.assertFalse(self.evaluate(expectedCaseIds=[],commands=[]))
    def testFailureBlockedAndWrongExitReject(self):
        for status,code in [('FAIL',1),('BLOCKED',None),('PASS',1),('PASS',None),('PASS',False)]:
            rows=copy.deepcopy(self.rows);rows[0].update(status=status,exitCode=code)
            self.assertFalse(self.evaluate(commands=rows))

if __name__=='__main__':unittest.main()
