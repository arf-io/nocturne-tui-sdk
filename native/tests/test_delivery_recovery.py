"""Real-process regressions for lost delivery, vacuous PASS, and orphan writers."""
from pathlib import Path
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'native/scripts'))
from delivery_runner import RunJournal

STAGE = ROOT / 'native/scripts/execute_stage.py'

class DeliveryRecoveryTests(unittest.TestCase):
    def testEmptyJournalCannotPass(self):
        with tempfile.TemporaryDirectory() as directory:
            with RunJournal(Path(directory)) as run:
                with self.assertRaisesRegex(ValueError, 'empty|no command'):
                    run.finish(True)

    def testNonfiniteHeartbeatRejected(self):
        for value in (math.nan, math.inf):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    RunJournal(Path(directory), heartbeatSeconds=value)

    def testNonfiniteDeadlineRejectedBeforeSpawn(self):
        for value in (math.nan, math.inf):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                with RunJournal(Path(directory)) as run:
                    with self.assertRaises(ValueError):
                        run.runStep('invalid', [sys.executable, '-c', 'pass'], ROOT, timeoutSeconds=value)

    def orphanCase(self, timeout):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            marker = home / 'late-write'
            # A pipe ensures the grandchild has installed its TERM handler before
            # the leader exits or sleeps. No mock process or fake clock is used.
            program = '''import os,signal,sys,time
from pathlib import Path
r,w=os.pipe()
child=os.fork()
if child==0:
    os.close(r)
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    os.write(w,b"ready");os.close(w)
    time.sleep(.8)
    Path(sys.argv[1]).write_text("orphan wrote after receipt")
    time.sleep(20)
    os._exit(0)
os.close(w);os.read(r,5);os.close(r)
if sys.argv[2]=="timeout": time.sleep(20)
'''
            item = None
            try:
                with RunJournal(home / 'run') as run:
                    item = run.runStep('fork', [sys.executable, '-c', program, str(marker),
                                               'timeout' if timeout else 'exit'], ROOT,
                                       timeoutSeconds=.25 if timeout else 4)
                time.sleep(.9)
                self.assertFalse(marker.exists(), 'descendant was still able to write after finalization')
                self.assertEqual(item['status'], 'TIMEOUT' if timeout else 'FAIL')
                log = home / 'run' / item['log']
                self.assertEqual(item['logSha256'], hashlib.sha256(log.read_bytes()).hexdigest())
            finally:
                # Emergency cleanup on the baseline RED is never counted as a fix.
                if item:
                    try: os.killpg(item['childPid'], signal.SIGKILL)
                    except ProcessLookupError: pass

    @unittest.skipUnless(hasattr(os, 'fork'), 'POSIX process group regression')
    def testTimeoutKillsTermIgnoringDescendant(self):
        self.orphanCase(True)

    @unittest.skipUnless(hasattr(os, 'fork'), 'POSIX process group regression')
    def testSuccessfulLeaderCannotLeaveWritingDescendant(self):
        self.orphanCase(False)

    def stage(self, home, command, artifacts=(), repo=ROOT):
        args = [sys.executable, str(STAGE), '--repo', str(repo), '--run-dir', str(home/'run'),
                '--name', 'probe', '--timeout', '10']
        for path in artifacts:
            args.extend(['--require-artifact', str(path)])
        return subprocess.run(args + ['--'] + command, capture_output=True, text=True, timeout=20)

    def testStageCreatesReceiptBeforeMissingRepositoryError(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            result=self.stage(home,[sys.executable,'-c','pass'],repo=home/'absent')
            self.assertEqual(result.returncode,2)
            receipt=home/'run/EXECUTION.json'
            self.assertTrue(receipt.is_file(), result.stderr)
            data=json.loads(receipt.read_text())
            self.assertEqual(data['status'],'FAIL')
            self.assertIn('repository',data['exception'].lower())

    def testMissingManifestOrArtifactNeverBecomesEmptySuccess(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            result=self.stage(home,[sys.executable,'-c','print("built nothing")'],[home/'missing-sdk.tar.gz'])
            self.assertEqual(result.returncode,2)
            data=json.loads((home/'run/EXECUTION.json').read_text())
            self.assertEqual(data['status'],'FAIL')
            self.assertFalse(data['passed'])
            self.assertIn('artifact',data['exception'].lower())

    def testStageRetainsActualExitAndErrorLog(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            result=self.stage(home,[sys.executable,'-c','print("actual failure");raise SystemExit(7)'])
            self.assertEqual(result.returncode,2)
            data=json.loads((home/'run/EXECUTION.json').read_text())
            self.assertEqual(data['commands'][0]['exitCode'],7)
            self.assertIn('actual failure',(home/'run/logs/probe.log').read_text())

    def testStageProducesHashBoundArtifactAndReusableCommand(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);artifact=home/'payload.bin'
            command=[sys.executable,'-c','from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(b"verified payload")',str(artifact)]
            result=self.stage(home,command,[artifact])
            self.assertEqual(result.returncode,0,result.stderr + result.stdout)
            data=json.loads((home/'run/EXECUTION.json').read_text())
            self.assertEqual(data['status'],'PASS')
            self.assertTrue(data['sourceUnchanged'])
            self.assertEqual(data['commands'][0]['argv'],command)
            self.assertEqual(data['artifacts'][0]['sha256'],hashlib.sha256(artifact.read_bytes()).hexdigest())
            before=(home/'run/EXECUTION.json').read_bytes()
            second=self.stage(home,command,[artifact])
            self.assertNotEqual(second.returncode,0)
            self.assertEqual((home/'run/EXECUTION.json').read_bytes(),before)

if __name__=='__main__': unittest.main()
