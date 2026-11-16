"""Immutable qualification infrastructure exercised with real processes and files.

The child workloads count executions, hash input bytes and write their actual
results. They are deliberately small process workloads, not framework stand-ins.
No external adapter, service or dependency is mocked.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'tools/qualification'))
from delivery_runner import RunJournal, inspectRun, processIdentity
from checkpoints import CheckpointError, CheckpointStore, bindingDigest, fileDigest


WORKLOAD = '''from pathlib import Path
import hashlib, json, os, sys, time
source, state, result = map(Path, sys.argv[1:4])
with state.open('a') as stream:
    stream.write(str(os.getpid()) + '\\n'); stream.flush(); os.fsync(stream.fileno())
if len(sys.argv) > 4:
    while not Path(sys.argv[4]).exists():
        time.sleep(.01)
payload = source.read_bytes()
observed = {'bytes':len(payload), 'sha256':hashlib.sha256(payload).hexdigest(), 'pid':os.getpid()}
result.write_text(json.dumps(observed, sort_keys=True))
print(json.dumps(observed, sort_keys=True), flush=True)
'''


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / 'input.txt'
        self.source.write_text('Nocturne immutable checkpoint input\n')
        self.worker = self.root / 'workload.py'
        self.worker.write_text(WORKLOAD)
        self.store = self.root / 'checkpoints'
        self.counter = self.root / 'executions.txt'
        self.output = self.root / 'result.json'
        self.case = dict(id='hash-input', argv=[sys.executable, str(self.worker),
                         str(self.source), str(self.counter), str(self.output)],
                         cwd=str(self.root), timeoutSeconds=5.0,
                         logLimitBytes=1024 * 1024, artifacts=[str(self.output)])
        self.plan = [self.case]

    def binding(self):
        """Fingerprint the real inputs and interpreter used by the workload."""
        return dict(schema='nocturne.checkpoint-binding.v1',
                    source={'input.txt':fileDigest(self.source), 'workload.py':fileDigest(self.worker)},
                    toolchains={'python':{'path':str(Path(sys.executable).resolve()),
                                         'sha256':fileDigest(Path(sys.executable))}},
                    environmentSha256=bindingDigest(dict(os.environ)),
                    plan=self.plan, policy={'strict':True})

    def execute(self, *, resume=False, runName='run-1'):
        with CheckpointStore(self.store, self.binding(), resume=resume) as store:
            with RunJournal(self.root / runName, heartbeatSeconds=.1) as run:
                store.bindRun(run)
                rows = [store.runCase(run, case['id'], self.binding) for case in self.plan]
                store.finish(run, all(row['status'] == 'PASS' for row in rows), self.binding)
            return rows, inspectRun(self.root / runName)

    def testCompletedCheckpointReusesActualResultWithoutReexecuting(self):
        rows, report = self.execute()
        self.assertTrue(report['passed'])
        self.assertFalse(rows[0]['reused'])
        firstPid = self.counter.read_text().splitlines()
        self.assertEqual(len(firstPid), 1)
        checkpoint = rows[0]['checkpoint']
        originalBytes = (self.store / checkpoint['path']).read_bytes()
        originalLog = (self.root / 'run-1' / rows[0]['log']).read_bytes()
        reused, report = self.execute(resume=True, runName='run-2')
        self.assertTrue(report['passed'])
        self.assertTrue(reused[0]['reused'])
        self.assertEqual(self.counter.read_text().splitlines(), firstPid)
        self.assertEqual((self.store / checkpoint['path']).read_bytes(), originalBytes)
        self.assertEqual((self.root / 'run-2' / reused[0]['log']).read_bytes(), originalLog)
        self.assertEqual(reused[0]['checkpoint']['sha256'], checkpoint['sha256'])
        self.assertEqual(json.loads(self.output.read_text())['sha256'], fileDigest(self.source))

    def testCheckpointReportCannotBeModifiedAndResumed(self):
        rows, _ = self.execute()
        path = self.store / rows[0]['checkpoint']['path']
        path.chmod(0o600)
        value = json.loads(path.read_text())
        value['result']['exitCode'] = 27
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(CheckpointError, 'integrity'):
            self.execute(resume=True, runName='run-2')
        self.assertEqual(len(self.counter.read_text().splitlines()), 1)

    def testStoredLogTamperingCannotBeReused(self):
        rows, _ = self.execute()
        checkpoint = json.loads((self.store / rows[0]['checkpoint']['path']).read_text())
        log = self.store / rows[0]['checkpoint']['path']
        log = log.parent / checkpoint['log']['path']
        log.chmod(0o600)
        log.write_text('altered observed child output\n')
        with self.assertRaisesRegex(CheckpointError, 'integrity'):
            self.execute(resume=True, runName='run-2')

    def testMissingStoredArtifactCannotQualify(self):
        rows, _ = self.execute()
        path = self.store / rows[0]['checkpoint']['path']
        checkpoint = json.loads(path.read_text())
        artifact = path.parent / checkpoint['artifacts'][0]['path']
        artifact.parent.chmod(0o700)
        artifact.unlink()
        with self.assertRaisesRegex(CheckpointError, 'integrity|missing'):
            self.execute(resume=True, runName='run-2')

    def testChangedLiveOutputCannotSilentlySkipItsProducer(self):
        self.execute()
        self.output.write_text('changed generated product')
        with self.assertRaisesRegex(CheckpointError, 'output|artifact'):
            self.execute(resume=True, runName='run-2')
        self.assertEqual(len(self.counter.read_text().splitlines()), 1)

    def testArtifactReaderKeepsSelectedObservationAndFinalizationRejectsLiveRewrite(self):
        with CheckpointStore(self.store, self.binding()) as store:
            with RunJournal(self.root / 'run-1') as run:
                store.bindRun(run)
                store.runCase(run, self.case['id'], self.binding)
                original = self.output.read_bytes()
                self.output.write_text('unrelated later report')
                self.assertEqual(store.artifact(self.case['id'], self.output).read_bytes(), original)
                with self.assertRaisesRegex(CheckpointError, 'output|artifact'):
                    store.finish(run, True, self.binding)
        self.assertFalse(inspectRun(self.root / 'run-1')['passed'])

    def testSelectedCheckpointHashCannotBeReplacedWithRecomputedSeal(self):
        with CheckpointStore(self.store, self.binding()) as store:
            with RunJournal(self.root / 'run-1') as run:
                store.bindRun(run)
                row = store.runCase(run, self.case['id'], self.binding)
                path = self.store / row['checkpoint']['path']
                checkpoint = json.loads(path.read_text()); checkpoint['finishedAt'] += 1
                path.chmod(0o600); path.write_text(json.dumps(checkpoint))
                marker = path.parent / 'COMPLETE.json'; marker.chmod(0o600)
                marker.write_text(json.dumps({'path':path.name,'bytes':path.stat().st_size,'sha256':fileDigest(path)}))
                with self.assertRaisesRegex(CheckpointError, 'selected checkpoint integrity'):
                    store.artifact(self.case['id'], self.output)

    def testReopenedCheckpointResealCannotBypassOriginalExecutionAnchor(self):
        rows, _ = self.execute()
        path = self.store / rows[0]['checkpoint']['path']
        checkpoint = json.loads(path.read_text()); checkpoint['finishedAt'] += 1
        path.chmod(0o600); path.write_text(json.dumps(checkpoint))
        marker = path.parent / 'COMPLETE.json'; marker.chmod(0o600)
        marker.write_text(json.dumps({'path':path.name,'bytes':path.stat().st_size,'sha256':fileDigest(path)}))
        with self.assertRaisesRegex(CheckpointError, 'anchor|integrity'):
            self.execute(resume=True, runName='run-2')
        self.assertEqual(len(self.counter.read_text().splitlines()), 1)

    def testHistoricalSummaryTamperingCannotBeIgnoredByResume(self):
        _, report = self.execute()
        path = self.store / report['checkpointSummary']['path']
        summary = json.loads(path.read_text()); summary['finishedAt'] += 1
        path.chmod(0o600); path.write_text(json.dumps(summary))
        with self.assertRaisesRegex(CheckpointError, 'anchor|integrity'):
            self.execute(resume=True, runName='run-2')

    def testManifestTamperingCannotFinalizePassed(self):
        with CheckpointStore(self.store, self.binding()) as store:
            with RunJournal(self.root / 'run-1') as run:
                store.bindRun(run)
                store.runCase(run, self.case['id'], self.binding)
                path = self.store / 'MANIFEST.json'
                manifest = json.loads(path.read_text()); manifest['binding']['policy']['strict'] = False
                path.chmod(0o600); path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(CheckpointError, 'manifest|binding'):
                    store.finish(run, True, self.binding)

    def testChangedSourceRefusesResumeBeforeAnyChild(self):
        self.execute()
        self.source.write_text('new source revision')
        with self.assertRaisesRegex(CheckpointError, 'binding'):
            self.execute(resume=True, runName='run-2')
        self.assertEqual(len(self.counter.read_text().splitlines()), 1)

    def testChangedCommandTimeoutPlanOrderAndPolicyRefuseResume(self):
        self.execute()
        original = self.binding()
        candidates = []
        for key, replacement in [('argv', self.case['argv'] + ['different-argument']),
                                 ('timeoutSeconds', 6.0), ('artifacts', [])]:
            changed = json.loads(json.dumps(original))
            changed['plan'][0][key] = replacement
            candidates.append(changed)
        changed = json.loads(json.dumps(original)); changed['policy']['strict'] = False
        candidates.append(changed)
        changed = json.loads(json.dumps(original)); changed['plan'].append({**self.case, 'id':'additional-required-case'})
        candidates.append(changed)
        for changed in candidates:
            with self.subTest(binding=changed), self.assertRaisesRegex(CheckpointError, 'binding'):
                with CheckpointStore(self.store, changed, resume=True):
                    self.fail('changed qualification identity must not open')

    def testToolchainIdentityMismatchRefusesResume(self):
        self.execute()
        changed = self.binding()
        # A second real executable has different bytes. This tests the binding,
        # without impersonating a compiler or inventing a version response.
        executable = Path('/bin/sh').resolve()
        self.assertNotEqual(fileDigest(executable), changed['toolchains']['python']['sha256'])
        changed['toolchains']['python'] = {'path':str(executable), 'sha256':fileDigest(executable)}
        with self.assertRaisesRegex(CheckpointError, 'binding'):
            with CheckpointStore(self.store, changed, resume=True):
                self.fail('a different toolchain cannot inherit results')

    def testSourceChangeDuringActualCommandCannotCreatePassedCheckpoint(self):
        self.case['argv'] = [sys.executable, '-c',
                            'from pathlib import Path; p=Path(__import__("sys").argv[1]); p.write_text(p.read_text()+"changed")',
                            str(self.source)]
        self.case['artifacts'] = []
        with self.assertRaisesRegex(CheckpointError, 'binding'):
            self.execute()
        report = inspectRun(self.root / 'run-1')
        self.assertFalse(report['passed'])
        checkpoints = list(self.store.glob('cases/*/*/CHECKPOINT.json'))
        self.assertEqual(len(checkpoints), 1)
        self.assertEqual(json.loads(checkpoints[0].read_text())['result']['status'], 'FAIL')

    def testEmptyOrPartialPlanCannotBeMarkedPassed(self):
        empty = self.binding(); empty['plan'] = []
        with self.assertRaisesRegex(ValueError, 'empty|nonempty'):
            with CheckpointStore(self.store, empty):
                pass
        self.plan.append({**self.case, 'id':'second-required-case'})
        with CheckpointStore(self.store, self.binding()) as store:
            with RunJournal(self.root / 'run-1') as run:
                store.bindRun(run)
                store.runCase(run, self.case['id'], self.binding)
                with self.assertRaisesRegex(CheckpointError, 'complete|missing|partial'):
                    store.finish(run, True, self.binding)
        self.assertFalse(inspectRun(self.root / 'run-1')['passed'])

    def testTimeoutAndMissingExecutableRemainNonpassingCheckpoints(self):
        for name, argv, timeout in [('deadline', [sys.executable,'-c','import time; time.sleep(20)'], .1),
                                    ('absent', ['/nocturne-qualification-missing-executable'], 5.0)]:
            with self.subTest(case=name):
                self.store = self.root / ('checkpoints-' + name)
                self.plan = [{**self.case, 'id':name, 'argv':argv, 'timeoutSeconds':timeout, 'artifacts':[]}]
                rows, report = self.execute(runName='run-' + name)
                self.assertEqual(rows[0]['status'], 'TIMEOUT' if name == 'deadline' else 'BLOCKED')
                self.assertFalse(report['passed'])
                self.assertFalse(rows[0]['reused'])
                retries, report = self.execute(resume=True, runName='retry-' + name)
                self.assertFalse(report['passed'])
                self.assertFalse(retries[0]['reused'])
                self.assertEqual(len(list(self.store.glob('cases/*/*/CHECKPOINT.json'))), 2)

    def testStoredSymlinkIsRejected(self):
        rows, _ = self.execute()
        path = self.store / rows[0]['checkpoint']['path']
        checkpoint = json.loads(path.read_text())
        log = path.parent / checkpoint['log']['path']
        log.parent.chmod(0o700)
        log.unlink(); log.symlink_to(self.output)
        with self.assertRaisesRegex(CheckpointError, 'symlink|integrity'):
            self.execute(resume=True, runName='run-2')

    def testStoreRequiresExplicitResumeAndKeepsOldExecutionReceipt(self):
        self.execute()
        receipt = (self.root / 'run-1/EXECUTION.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.execute(runName='run-2')
        self.assertEqual((self.root / 'run-1/EXECUTION.json').read_bytes(), receipt)

    def driver(self):
        driver = self.root / 'driver.py'
        driver.write_text('''import json, os, signal, sys
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from delivery_runner import RunJournal
from checkpoints import CheckpointStore, bindingDigest, fileDigest
root = Path(sys.argv[3]); plan = json.loads((root/'plan.json').read_text())
def binding():
    return dict(schema='nocturne.checkpoint-binding.v1',
                source={'input.txt':fileDigest(root/'input.txt'), 'workload.py':fileDigest(root/'workload.py')},
                toolchains={'python':{'path':str(Path(sys.executable).resolve()), 'sha256':fileDigest(Path(sys.executable))}},
                environmentSha256=bindingDigest(dict(os.environ)), plan=plan, policy={'strict':True})
def interrupted(signum, frame):
    raise KeyboardInterrupt('signal '+str(signum))
signal.signal(signal.SIGTERM, interrupted)
with CheckpointStore(root/'checkpoints', binding(), resume=sys.argv[5]=='resume') as store:
    with RunJournal(root/sys.argv[4], heartbeatSeconds=.1) as run:
        store.bindRun(run)
        rows = [store.runCase(run, case['id'], binding) for case in plan]
        store.finish(run, all(row['status']=='PASS' for row in rows), binding)
''')
        (self.root / 'plan.json').write_text(json.dumps(self.plan))
        return [sys.executable, str(driver), str(ROOT / 'scripts'),
                str(ROOT.parent / 'tools/qualification'), str(self.root)]

    def waitForCounter(self, process):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.counter.exists() and self.counter.stat().st_size:
                return
            if process.poll() is not None:
                self.fail('driver exited before its real child was observed')
            time.sleep(.01)
        self.fail('actual child did not start before deadline')

    @unittest.skipUnless(os.name == 'posix', 'actual POSIX process signals and flock')
    def testInterruptedChildRetriesInFreshAttemptAndConcurrentOwnerIsRefused(self):
        release = self.root / 'release'
        self.case['argv'].append(str(release))
        command = self.driver()
        with (self.root / 'driver.log').open('wb') as log:
            process = subprocess.Popen(command + ['run-1', 'new'], stdout=log, stderr=log)
            try:
                self.waitForCounter(process)
                competing = subprocess.run(command + ['competing', 'resume'], capture_output=True,
                                           text=True, timeout=10)
                self.assertNotEqual(competing.returncode, 0)
                self.assertIn('already owned', competing.stderr)
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.kill(); process.wait(timeout=10)
        receipt = inspectRun(self.root / 'run-1')
        self.assertFalse(receipt['passed'])
        self.assertEqual(receipt['commands'][0]['status'], 'INTERRUPTED')
        old = (self.root / 'run-1/EXECUTION.json').read_bytes()
        release.write_text('allow the observed workload to finish')
        resumed = subprocess.run(command + ['run-2', 'resume'], capture_output=True, text=True, timeout=15)
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        self.assertTrue(inspectRun(self.root / 'run-2')['passed'])
        self.assertEqual(len(self.counter.read_text().splitlines()), 2)
        self.assertEqual(len(list(self.store.glob('cases/*/*/CHECKPOINT.json'))), 2)
        self.assertEqual((self.root / 'run-1/EXECUTION.json').read_bytes(), old)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux PID-start identity and real SIGKILL')
    def testHardKilledOwnerCannotResumeOverStillRunningChild(self):
        release = self.root / 'release'
        self.case['argv'].append(str(release))
        command = self.driver()
        childPid = None
        with (self.root / 'hard-kill.log').open('wb') as log:
            process = subprocess.Popen(command + ['run-1', 'new'], stdout=log, stderr=log)
            try:
                self.waitForCounter(process)
                childPid = int(self.counter.read_text().splitlines()[0])
                process.kill(); process.wait(timeout=10)
                self.assertEqual(inspectRun(self.root / 'run-1')['status'], 'ABANDONED')
                self.assertIsNotNone(processIdentity(childPid), 'the child must still be alive for this test')
                try:
                    refused = subprocess.run(command + ['unsafe-resume', 'resume'], capture_output=True,
                                             text=True, timeout=3)
                except subprocess.TimeoutExpired:
                    self.fail('resume launched another child instead of refusing the still-running child')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('unfinished checkpoint child is still running', refused.stderr)
            finally:
                if process.poll() is None:
                    process.kill(); process.wait(timeout=10)
                childPids = [int(value) for value in self.counter.read_text().splitlines()] if self.counter.exists() else []
                for observedPid in childPids:
                    if processIdentity(observedPid) is not None:
                        os.killpg(observedPid, signal.SIGTERM)
                        deadline = time.monotonic() + 5
                        while processIdentity(observedPid) is not None and time.monotonic() < deadline:
                            time.sleep(.01)
        release.write_text('complete the resumed workload')
        resumed = subprocess.run(command + ['run-2', 'resume'], capture_output=True, text=True, timeout=15)
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        self.assertEqual(len(self.counter.read_text().splitlines()), 2)
        self.assertEqual(len(list(self.store.glob('cases/*/*/START.json'))), 2)
        self.assertEqual(len(list(self.store.glob('cases/*/*/CHECKPOINT.json'))), 1)
        self.assertTrue(inspectRun(self.root / 'run-2')['passed'])

    def assertMissingLaunchProvenanceBlocksResume(self, *, removeStart):
        release = self.root / 'release'
        self.case['argv'].append(str(release))
        command = self.driver()
        with (self.root / 'missing-launch-provenance.log').open('wb') as log:
            process = subprocess.Popen(command + ['run-1', 'new'], stdout=log, stderr=log)
            try:
                self.waitForCounter(process)
                childPid = int(self.counter.read_text().splitlines()[0])
                process.kill(); process.wait(timeout=10)
                self.assertIsNotNone(processIdentity(childPid), 'an actual orphan must be running for this test')
                if removeStart:
                    start = next(self.store.glob('cases/*/*/START.json'))
                    start.unlink()
                else:
                    receipt = self.root / 'run-1/EXECUTION.json'
                    record = json.loads(receipt.read_text())
                    record['commands'][0].pop('childPid', None)
                    record['commands'][0].pop('childProcessIdentity', None)
                    receipt.write_text(json.dumps(record))
                try:
                    refused = subprocess.run(command + ['unknown-owner-resume', 'resume'],
                                             capture_output=True, text=True, timeout=2)
                except subprocess.TimeoutExpired:
                    self.fail('resume launched another child despite missing durable launch provenance')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('provenance', refused.stderr)
                self.assertEqual(len(self.counter.read_text().splitlines()), 1,
                                 'unknown ownership must not launch another command')
                self.assertIsNotNone(processIdentity(childPid), 'resume must never kill an uncertain owner')
            finally:
                # The test owns this release input. Let every actually spawned
                # finite workload finish itself; never signal an uncertain PID.
                release.write_text('release the actual hash workload')
                if process.poll() is None:
                    process.kill(); process.wait(timeout=10)
                deadline = time.monotonic() + 5
                observed = [int(value) for value in self.counter.read_text().splitlines()] if self.counter.exists() else []
                while any(processIdentity(pid) is not None for pid in observed) and time.monotonic() < deadline:
                    time.sleep(.01)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux actual orphan and SIGKILL observation')
    def testUnfinishedLaunchWithoutChildPidProvenanceIsBlocked(self):
        self.assertMissingLaunchProvenanceBlocksResume(removeStart=False)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux actual orphan and SIGKILL observation')
    def testUnfinishedLaunchWithoutStartProvenanceIsBlocked(self):
        self.assertMissingLaunchProvenanceBlocksResume(removeStart=True)

    def testDeclaredEnvironmentOverridesAreBoundAppliedAndValidated(self):
        """Declared overrides apply after the inherited-environment check and are plan identity."""
        reader = self.root / 'reader.py'
        reader.write_text('import os\nprint(os.environ.get("NOCTURNE_DECLARED_PROBE"))\n')
        declared = {'NOCTURNE_DECLARED_PROBE': 'declared'}
        self.case.update(argv=[sys.executable, str(reader)], artifacts=[], environmentOverrides=declared)
        with patch.dict(os.environ, {'NOCTURNE_DECLARED_PROBE': 'inherited'}):
            rows, report = self.execute()
            self.assertTrue(report['passed'])
            self.assertEqual((self.root / 'run-1' / rows[0]['log']).read_text().split(), ['declared'])
            self.assertEqual(rows[0]['environmentOverrides'], declared)
            retained = json.loads((self.store / rows[0]['checkpoint']['path']).read_text())
            self.assertEqual((retained['case']['environmentOverrides'], retained['result']['environmentOverrides']), (declared, declared))
            changed = self.binding()
            changed['plan'] = [{**self.case, 'environmentOverrides': {'NOCTURNE_DECLARED_PROBE': 'other'}}]
            with self.assertRaisesRegex(CheckpointError, 'binding'):
                with CheckpointStore(self.store, changed, resume=True):
                    self.fail('a changed declared environment cannot inherit results')
        for overrides in [{'A=B': 'x'}, {'': 'x'}, {'1A': 'x'}, {'A': 'x\x00y'}, {'A': 1}, ['A']]:
            invalid = self.binding()
            invalid['plan'] = [{**self.case, 'environmentOverrides': overrides}]
            with self.subTest(overrides=overrides), self.assertRaisesRegex(ValueError, 'environment'):
                CheckpointStore(self.root / 'invalid-store', invalid)
        self.assertFalse((self.root / 'invalid-store').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
