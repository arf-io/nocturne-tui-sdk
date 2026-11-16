"""Synthetic executors check orchestration only, never claim native gallery acceptance."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_gallery_studies import run_cases


class GalleryExecutionReceipts(unittest.TestCase):
    def run_fixture(self, cases, executor):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            with contextlib.redirect_stdout(io.StringIO()):
                result = run_cases(cases, executor, output, {'scope': 'synthetic orchestration fixture'})
            self.assertEqual(json.loads(output.read_text()), result)
            return result

    def test_failure_is_retained_and_later_cases_execute(self):
        observed = []
        def executor(cases):
            case = cases[0];observed.append(case['id'])
            if case['id'] == 'broken':
                raise ValueError('independent oracle mismatch')
            return [{'id': case['id'], 'renderPure': True, 'partitionReplay': True}]
        result = self.run_fixture([{'id': 'broken'}, {'id': 'later'}], executor)
        self.assertEqual(observed, ['broken', 'later'])
        self.assertTrue(result['complete'])
        self.assertFalse(result['passed'])
        self.assertEqual([row['status'] for row in result['cases']], ['FAIL', 'PASS'])
        self.assertEqual(result['cases'][0]['error'], 'independent oracle mismatch')

    def test_wrong_case_or_missing_runtime_properties_cannot_pass(self):
        for row in [{'id': 'foreign', 'renderPure': True, 'partitionReplay': True},
                    {'id': 'requested', 'renderPure': True},
                    {'id': 'requested', 'renderPure': False, 'partitionReplay': True}]:
            with self.subTest(row=row):
                result = self.run_fixture([{'id': 'requested'}], lambda cases: [row])
                self.assertFalse(result['passed'])

    def test_empty_or_duplicate_inventory_is_rejected(self):
        for cases in [[], [{'id': 'same'}, {'id': 'same'}]]:
            with self.assertRaises(ValueError):
                self.run_fixture(cases, lambda cases: [])

    def test_success_requires_every_declared_case(self):
        result = self.run_fixture([{'id': 'first'}, {'id': 'second'}],
            lambda cases: [{'id': cases[0]['id'], 'renderPure': True, 'partitionReplay': True}])
        self.assertTrue(result['complete'])
        self.assertTrue(result['passed'])
        self.assertEqual(result['expectedCaseIds'], [row['id'] for row in result['cases']])


if __name__ == '__main__':
    unittest.main()
