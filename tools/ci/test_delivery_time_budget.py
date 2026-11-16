"""Compare CI budgets with real completed execution, without running a rebuild."""
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'native/scripts'))
from verify_contracts_package import verificationCommands


class DeliveryTimeBudget(unittest.TestCase):
    def testWorkflowAllowsMeasuredShippingAndReconstruction(self):
        execution = json.loads((ROOT / 'native/evidence/coverage-completed-frozen-20261013/EXECUTION.json').read_text())
        self.assertTrue(execution['completePlan'])
        workflow = (ROOT / '.forgejo/workflows/nocturne.yml').read_text()
        minutes = int(re.search(r'timeout-minutes:\s*(\d+)', workflow).group(1))
        # Measured qualification, shipping qualification and extracted replay,
        # plus two hours for prerequisites, hosts and archives. This is a budget,
        # not an estimate or a claim of equivalent machine performance.
        minimum = 3 * execution['elapsedSeconds'] + 7200
        self.assertGreater(minutes * 60, minimum)
        self.assertLessEqual(minutes, 1800)
        self.assertEqual(workflow.count('--step-timeout 7200'), 2)
        verifier = (ROOT / 'tools/ci/verify_packages.py').read_text()
        self.assertIn("'--timeout','86400'", verifier)
        self.assertIn("'--step-timeout','7200'", verifier)

    def testExtractionPassesIndependentStepBudgetToRealPlan(self):
        commands = verificationCommands(sys.executable, Path('/tmp/nocturne-evidence'), 7200)
        self.assertEqual(commands[0], ('extracted-build', ['sh', 'build-native.sh']))
        self.assertEqual(commands[1][0], 'extracted-strict-qualification')
        command = commands[1][1]
        self.assertEqual(command[-2:], ['--step-timeout', '7200'])
        result = subprocess.run(command + ['--list'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertTrue(plan)
        self.assertTrue(all(case['timeoutSeconds'] == 7200 for case in plan))

    def testInvalidStepBudgetsReject(self):
        for value in [0, -1, math.inf, math.nan]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    verificationCommands(sys.executable, Path('/tmp/nocturne-evidence'), value)


if __name__ == '__main__':
    unittest.main()
