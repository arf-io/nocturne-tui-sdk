from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'examples')]
from world_shell_studies import build_world_shell_studies
import check_world_shell_browser as checker

class WorldShellCaseSelection(unittest.TestCase):
    def setUp(self):self.cases=build_world_shell_studies()
    def testAdditivePrefixDoesNotReplaceOriginalCanonicalCases(self):
        expected=[row['id'] for row in self.cases]
        recipes=self.cases+[{'id':'world-shell-source-extra','mode':'isolated'}]
        self.assertEqual(checker.worldShellCaseIds(recipes),expected)
    def testMissingOriginalCaseRejects(self):
        with self.assertRaises(ValueError):checker.worldShellCaseIds(self.cases[:-1])
    def testDuplicateOriginalCaseRejects(self):
        with self.assertRaises(ValueError):checker.worldShellCaseIds(self.cases+[self.cases[0]])

if __name__=='__main__':unittest.main()
