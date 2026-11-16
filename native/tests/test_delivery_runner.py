"""Regression tests for the abandoned RUNNING receipt / 20-second delivery failure."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from delivery_runner import RunJournal, atomicJson, inspectRun, processIdentity

class DeliveryRunnerTests(unittest.TestCase):
    def testDarwinEmptyGroupPermissionErrorIsNotLiveChild(self):
        with tempfile.TemporaryDirectory() as directory:
            run = RunJournal(Path(directory))
            run.child = Mock(pid=123)
            with patch('sys.platform', 'darwin'), \
                 patch('delivery_runner.os.killpg', side_effect=PermissionError(1, 'Operation not permitted')), \
                 patch('delivery_runner.subprocess.run', return_value=Mock(stdout='123 Z\n456 S\n')):
                self.assertFalse(run.childGroupExists())

    def testDarwinLiveGroupPermissionErrorRemainsFailure(self):
        with tempfile.TemporaryDirectory() as directory:
            run = RunJournal(Path(directory))
            run.child = Mock(pid=123)
            with patch('sys.platform', 'darwin'), \
                 patch('delivery_runner.os.killpg', side_effect=PermissionError(1, 'Operation not permitted')), \
                 patch('delivery_runner.subprocess.run', return_value=Mock(stdout='123 S\n')):
                with self.assertRaises(PermissionError):
                    run.childGroupExists()

    def testProcessExitIsAuthorityNotArbitraryPollingCount(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory), heartbeatSeconds=.02) as run:
                record = run.runStep('delayed', [sys.executable, '-c', 'import time; time.sleep(.45); print("done")'], ROOT, timeoutSeconds=5)
                self.assertEqual(record['status'], 'PASS')
                self.assertGreater(record['seconds'], .4)
                run.finish(True)
            receipt = json.loads((Path(directory) / 'EXECUTION.json').read_text())
            self.assertEqual(receipt['status'], 'PASS')
            self.assertTrue(receipt['complete'])
            self.assertEqual(receipt['commands'][0]['exitCode'], 0)
    def testFailureIsTerminalAndRetainsLog(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                record = run.runStep('red', [sys.executable, '-c', 'print("failure detail"); raise SystemExit(7)'], ROOT)
                self.assertEqual(record['exitCode'], 7)
            receipt = json.loads((Path(directory) / 'EXECUTION.json').read_text())
            self.assertEqual(receipt['status'], 'FAIL')
            self.assertIn('failure detail', (Path(directory) / record['log']).read_text())
    def testTimeoutKillsAndWaitsForActualChild(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                record = run.runStep('hung', [sys.executable, '-c', 'import time; time.sleep(30)'], ROOT, timeoutSeconds=.15)
                self.assertEqual(record['status'], 'TIMEOUT')
                self.assertIsNotNone(record['exitCode'])
            self.assertEqual(inspectRun(Path(directory))['status'], 'FAIL')
    def testMissingToolIsBlockedNotPass(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                record = run.runStep('absent', ['/nocturne-test/tool-does-not-exist'], ROOT)
                self.assertEqual(record['status'], 'BLOCKED')
                self.assertIsNone(record['exitCode'])
            self.assertFalse(inspectRun(Path(directory))['passed'])
    def testExceptionWritesTerminalReceipt(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'synthetic'):
                with RunJournal(Path(directory)):
                    raise ValueError('synthetic')
            receipt = inspectRun(Path(directory))
            self.assertEqual(receipt['status'], 'FAIL')
            self.assertIn('synthetic', receipt['exception'])
    def testCannotOverwritePriorReceipt(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                run.finish(False)  # This fixture checks custody, not an empty PASS.
            with self.assertRaises(FileExistsError):
                with RunJournal(Path(directory)): pass
    def testAtomicWriteNoPartialJson(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'state.json'
            for n in range(5):
                atomicJson(path, {'n': n, 'items': list(range(200))})
                self.assertEqual(json.loads(path.read_text())['n'], n)
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])
    def testStaleRunningIsReportedNotWaitedForever(self):
        with tempfile.TemporaryDirectory() as directory:
            atomicJson(Path(directory)/'EXECUTION.json', {'status':'RUNNING', 'pid':2**30, 'complete':False})
            receipt = inspectRun(Path(directory))
            self.assertEqual(receipt['status'], 'ABANDONED')
            self.assertFalse(receipt['passed'])
    def testNoSuccessWhenChecksFail(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                run.runStep('red', [sys.executable,'-c','raise SystemExit(3)'], ROOT)
                with self.assertRaises(ValueError): run.finish(True)
            self.assertEqual(inspectRun(Path(directory))['status'], 'FAIL')

    def testFastOversizedLogIsNotPassed(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                item=run.runStep('too-large',[sys.executable,'-c','print("x"*2048)'],ROOT,logLimitBytes=1024)
                self.assertEqual(item['status'],'FAIL')
            self.assertFalse(inspectRun(Path(directory))['passed'])
    def testDeclaredPlanCannotBePartiallyFinalizedAsPass(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                run.record['expectedSteps']=2
                run.record['expectedCaseIds']=['first','second']
                run.runStep('first',[sys.executable,'-c','assert sum(range(100)) == 4950'],ROOT)
                with self.assertRaisesRegex(ValueError,'partial|complete|missing'):
                    run.finish(True)
            self.assertFalse(inspectRun(Path(directory))['passed'])
    def testReapedProcessHasNoLiveIdentity(self):
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])
        try:
            child.kill();child.wait(timeout=5)
            self.assertIsNone(processIdentity(child.pid),'a reaped child is dead even if a proc view is stale')
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=5)
    def testInspectCliReportsDeadOwner(self):
        with tempfile.TemporaryDirectory() as directory:
            atomicJson(Path(directory)/'EXECUTION.json',{'status':'RUNNING','pid':2**30})
            result=subprocess.run([sys.executable,str(ROOT/'scripts/delivery_runner.py'),directory],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertEqual(json.loads(result.stdout)['status'],'ABANDONED')

    def testDeclaredEnvironmentOverridesInheritedValuesAndIsRecorded(self):
        """A declared case variable replaces the inherited value for that child only."""
        reader = [sys.executable, '-c', 'import os; print(os.environ.get("NOCTURNE_DECLARED_PROBE")); print(os.environ.get("NOCTURNE_INHERITED_PROBE"))']
        declared = {'NOCTURNE_DECLARED_PROBE': 'declared'}
        inherited = {**os.environ, 'NOCTURNE_DECLARED_PROBE': 'inherited', 'NOCTURNE_INHERITED_PROBE': 'kept'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with RunJournal(root) as run:
                plain = run.runStep('inherited', reader, ROOT, timeoutSeconds=10, env=inherited)
                explicit = run.runStep('declared', reader, ROOT, timeoutSeconds=10, env=inherited, environmentOverrides=declared)
                with patch.dict(os.environ, {'NOCTURNE_DECLARED_PROBE': 'process', 'NOCTURNE_INHERITED_PROBE': 'process-kept'}):
                    process = run.runStep('declared-process', reader, ROOT, timeoutSeconds=10, environmentOverrides=declared)
            self.assertEqual((root/plain['log']).read_text().split(), ['inherited', 'kept'])
            self.assertEqual((root/explicit['log']).read_text().split(), ['declared', 'kept'])
            self.assertEqual((root/process['log']).read_text().split(), ['declared', 'process-kept'])
            self.assertNotIn('environmentOverrides', plain)
            self.assertEqual(inherited['NOCTURNE_DECLARED_PROBE'], 'inherited')
            record = json.loads((root/'EXECUTION.json').read_text())
            self.assertEqual([row.get('environmentOverrides') for row in record['commands']], [None, declared, declared])

    def testMalformedEnvironmentOverridesAreRejectedBeforeLaunch(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory)/'launched'
            command = [sys.executable, '-c', 'import pathlib, sys; pathlib.Path(sys.argv[1]).write_text("x")', str(marker)]
            with RunJournal(Path(directory)/'run') as run:
                for index, overrides in enumerate([{'A=B': 'x'}, {'': 'x'}, {'1A': 'x'}, {'A': 'x\x00y'}, {'A': 1}, {1: 'x'}, ['A']]):
                    with self.subTest(overrides=overrides), self.assertRaisesRegex(ValueError, 'environment'):
                        run.runStep(f'invalid-{index}', command, ROOT, timeoutSeconds=10, environmentOverrides=overrides)
                self.assertEqual(run.record['commands'], [])
            self.assertFalse(marker.exists())

if __name__ == '__main__': unittest.main()


class DescendantGrace(unittest.TestCase):
    """A grandchild that is still exiting when the leader is reaped is not a leftover.

    runStep checks the owned process group the instant the leader exits. Linux run 04
    (native/evidence/linux-host-20261031/qualify-rc2-04) failed rc2-native with
    'Descendant remained after command leader exited' although its 225 tests had
    passed and no process survived the leader by more than milliseconds. The runner
    waits a bounded grace window; a descendant that persists past it still fails the
    step and is terminated with its group.
    """
    SPAWN = 'import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep({sleep})"]); raise SystemExit(0)'

    def test_descendant_exiting_shortly_after_the_leader_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory), descendantGraceSeconds=2) as run:
                record = run.runStep('late-child', [sys.executable, '-c', self.SPAWN.format(sleep=.3)], ROOT, timeoutSeconds=10)
            self.assertEqual((record['status'], record['exitCode']), ('PASS', 0), record)
            self.assertNotIn('reason', record)
            self.assertGreater(record['descendantExitSeconds'], 0)
            self.assertLess(record['descendantExitSeconds'], 2)

    def test_descendant_persisting_past_the_grace_window_fails_and_is_terminated(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory), descendantGraceSeconds=.3) as run:
                record = run.runStep('leftover', [sys.executable, '-c', self.SPAWN.format(sleep=30)], ROOT, timeoutSeconds=10)
            self.assertEqual((record['status'], record['exitCode']), ('FAIL', 0), record)
            self.assertEqual(record['reason'], 'Descendant remained after command leader exited')
            self.assertGreaterEqual(record['descendantExitSeconds'], .3)
            with self.assertRaises(ProcessLookupError):
                os.killpg(record['childPid'], 0)

    def test_grace_window_must_be_finite_and_not_negative(self):
        for bad in (-1, float('inf'), float('nan')):
            with self.subTest(grace=bad), tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                RunJournal(Path(directory), descendantGraceSeconds=bad)
