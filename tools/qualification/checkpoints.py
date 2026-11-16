"""Immutable, source-bound checkpoints for observed qualification commands.

This module stores observations from the real RunJournal process runner. It does
not substitute an adapter, execute a saved log, or turn a partial plan into PASS.
Each retry has a new directory; COMPLETE.json is published last. A fresh execution
receipt remains mandatory even when completed cases are reused.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import socket
import stat
import tempfile
import time

try:
    import fcntl
except ImportError:
    fcntl = None


STORE_SCHEMA = 'nocturne.qualification-store.v1'
CHECKPOINT_SCHEMA = 'nocturne.qualification-checkpoint.v1'
TERMINAL_STATES = {'PASS', 'FAIL', 'BLOCKED', 'TIMEOUT', 'INTERRUPTED'}
SAFE_CASE = re.compile(r'[A-Za-z0-9_-]+\Z')
SAFE_ATTEMPT = re.compile(r'[0-9]{6}\Z')
SAFE_ENVIRONMENT_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')


class CheckpointError(ValueError):
    """A checkpoint, binding, output, lock, or complete-plan check was rejected."""


def canonicalBytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON; nonfinite numbers are errors."""
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')


def bindingDigest(value: object) -> str:
    """Return the SHA-256 of canonical JSON, including order within arrays."""
    return hashlib.sha256(canonicalBytes(value)).hexdigest()


def fileDigest(path: Path) -> str:
    """Hash an actual file incrementally, without loading captures into memory."""
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _syncDirectory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _noSymlinks(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            raise CheckpointError('symlink rejected in checkpoint path: ' + str(part))


def _regular(path: Path) -> None:
    _noSymlinks(path)
    try:
        mode = path.stat().st_mode
    except OSError as error:
        raise CheckpointError('missing checkpoint integrity input: ' + str(path)) from error
    if not stat.S_ISREG(mode):
        raise CheckpointError('nonregular checkpoint integrity input: ' + str(path))


def _readJson(path: Path) -> dict:
    _regular(path)
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise CheckpointError('checkpoint JSON integrity error: ' + str(path)) from error
    if not isinstance(value, dict):
        raise CheckpointError('checkpoint JSON integrity object required: ' + str(path))
    return value


def _immutableBytes(path: Path, payload: bytes) -> None:
    """Publish a fully fsynced file exclusively, never replace an existing name."""
    _noSymlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o444)
        # Linking is atomic and fails if the destination already exists. A crash
        # before this point leaves an ignored temporary file, never a PASS record.
        os.link(temporary, path, follow_symlinks=False)
        _syncDirectory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _immutableJson(path: Path, value: dict) -> None:
    _immutableBytes(path, canonicalBytes(value))


def _copyImmutable(source: Path, target: Path) -> dict:
    """Copy and hash stable regular-file bytes, refusing concurrent changes."""
    _regular(source)
    before = source.stat()
    _noSymlinks(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=target.parent)
    digest = hashlib.sha256()
    size = 0
    try:
        with source.open('rb') as incoming, os.fdopen(descriptor, 'wb') as outgoing:
            for chunk in iter(lambda: incoming.read(1024 * 1024), b''):
                outgoing.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            outgoing.flush()
            os.fsync(outgoing.fileno())
            os.fchmod(outgoing.fileno(), 0o444)
        after = source.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise CheckpointError('artifact changed while checkpointing: ' + str(source))
        os.link(temporary, target, follow_symlinks=False)
        _syncDirectory(target.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'bytes':size, 'sha256':digest.hexdigest()}


def _storedPath(directory: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative or
            '\x00' in relative or any(part in ('', '.', '..') for part in relative.split('/')) or
            PurePosixPath(relative).is_absolute()):
        raise CheckpointError('unsafe checkpoint integrity path')
    path = directory.joinpath(*PurePosixPath(relative).parts)
    _noSymlinks(path)
    return path


def _verifyFile(directory: Path, record: dict) -> Path:
    try:
        path = _storedPath(directory, record['path'])
        _regular(path)
        if path.stat().st_size != record['bytes'] or fileDigest(path) != record['sha256']:
            raise CheckpointError('checkpoint file integrity mismatch: ' + str(path))
        return path
    except (KeyError, TypeError, OSError) as error:
        raise CheckpointError('invalid checkpoint file integrity record') from error


def _artifactInventory(case: dict) -> tuple[list[dict], list[tuple[Path, int, str]]]:
    roots, files = [], []
    for index, name in enumerate(case.get('artifacts', [])):
        path = Path(name)
        _noSymlinks(path)
        if path.is_file():
            _regular(path)
            roots.append({'path':str(path), 'kind':'file', 'members':['.']})
            files.append((path, index, '.'))
        elif path.is_dir():
            members = []
            for member in sorted(path.rglob('*')):
                _noSymlinks(member)
                if member.is_dir():
                    continue
                _regular(member)
                relative = member.relative_to(path).as_posix()
                members.append(relative)
                files.append((member, index, relative))
            roots.append({'path':str(path), 'kind':'directory', 'members':members})
        else:
            raise CheckpointError('required output artifact is missing: ' + str(path))
    return roots, files


class CheckpointStore:
    """Own an immutable qualification store under one process lock.

    Inputs: a new directory, a JSON binding with a nonempty ordered ``plan`` and
    source/toolchain/environment identities, and explicit ``resume=True`` to open
    existing evidence. Each case declares id, argv, cwd, timeoutSeconds and optional
    logLimitBytes/artifacts/reusable/environmentOverrides. Artifacts are absolute
    regular-file/directory paths, retained incrementally and checked before reuse.
    environmentOverrides maps variable names to strings; they are part of the bound
    plan and replace those names in the checked inherited environment for that case.

    Errors: invalid plans raise ValueError; integrity, binding and lock violations
    raise CheckpointError; implicit overwrites raise FileExistsError. POSIX flock
    is required. Windows execution is explicitly unsupported by this store.

    Example: with CheckpointStore(path, binding, resume=True) as store, call
    store.bindRun(run), store.runCase(run, id, actualBindingProbe) for every planned
    case, then store.finish(run, passed, actualBindingProbe). ``run`` is the SDK's
    observed RunJournal, and the probe hashes actual current inputs and tools.
    """

    def __init__(self, directory: Path, binding: dict, *, resume: bool = False):
        self.directory = Path(directory).absolute()
        _noSymlinks(self.directory)
        self.binding = json.loads(canonicalBytes(binding))
        self.bindingSha256 = bindingDigest(self.binding)
        self.resume = resume
        self._lock = None
        self._run = None
        self._visited = []
        self._selected = {}
        self._validatePlan()

    def _validatePlan(self) -> None:
        plan = self.binding.get('plan')
        if not isinstance(plan, list) or not plan:
            raise ValueError('a nonempty qualification plan is required')
        ids = []
        for case in plan:
            if not isinstance(case, dict) or not isinstance(case.get('id'), str) or not SAFE_CASE.fullmatch(case['id']):
                raise ValueError('case id must be a safe filename')
            ids.append(case['id'])
            argv = case.get('argv')
            if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or '\x00' in arg for arg in argv):
                raise ValueError('case argv must be a nonempty string array')
            if not isinstance(case.get('cwd'), str) or not Path(case['cwd']).is_absolute():
                raise ValueError('case cwd must be absolute')
            timeout = case.get('timeoutSeconds')
            if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
                raise ValueError('case timeout must be finite and positive')
            limit = case.get('logLimitBytes', 64 * 1024 * 1024)
            if type(limit) is not int or limit <= 0:
                raise ValueError('case log limit must be a positive integer')
            artifacts = case.get('artifacts', [])
            if not isinstance(artifacts, list) or any(not isinstance(name, str) or not Path(name).is_absolute() for name in artifacts):
                raise ValueError('case artifact paths must be absolute')
            if len(set(artifacts)) != len(artifacts):
                raise ValueError('duplicate case artifact path')
            if type(case.get('reusable', True)) is not bool:
                raise ValueError('reusable must be boolean')
            overrides = case.get('environmentOverrides', {})
            if not isinstance(overrides, dict) or any(
                    not isinstance(key, str) or not SAFE_ENVIRONMENT_NAME.fullmatch(key) or
                    not isinstance(value, str) or '\x00' in value for key, value in overrides.items()):
                raise ValueError('case environment overrides must map portable names to strings without NUL')
        if len(set(ids)) != len(ids):
            raise ValueError('duplicate case id')
        self.plan = plan
        self.cases = {case['id']:case for case in plan}

    def __enter__(self):
        if fcntl is None:
            raise CheckpointError('POSIX process locking unavailable; resumable qualification is BLOCKED')
        if not self.resume and self.directory.exists() and any(self.directory.iterdir()):
            raise FileExistsError('checkpoint store exists; explicit resume is required: ' + str(self.directory))
        if self.resume and not self.directory.is_dir():
            raise CheckpointError('missing checkpoint store for resume')
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.directory / '.owner.lock', os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise CheckpointError('checkpoint store is already owned by another process') from error
            self._lock = descriptor
            manifest = self.directory / 'MANIFEST.json'
            expected = {'schema':STORE_SCHEMA, 'bindingSha256':self.bindingSha256, 'binding':self.binding}
            if self.resume:
                if _readJson(manifest) != expected:
                    raise CheckpointError('checkpoint binding mismatch: source, plan, commands, environment or toolchain changed')
            else:
                _immutableJson(manifest, expected)
            self._scan()
            return self
        except BaseException:
            self._lock = None
            os.close(descriptor)
            raise

    def __exit__(self, kind, error, traceback):
        if self._lock is not None:
            os.close(self._lock)
            self._lock = None
        return False

    def _scan(self) -> dict[str, list[Path]]:
        expected = {'schema':STORE_SCHEMA, 'bindingSha256':self.bindingSha256, 'binding':self.binding}
        if _readJson(self.directory / 'MANIFEST.json') != expected:
            raise CheckpointError('checkpoint manifest binding integrity changed')
        self._verifyRunSummaries()
        root = self.directory / 'cases'
        attempts = {name:[] for name in self.cases}
        if not root.exists():
            return attempts
        _noSymlinks(root)
        for folder in sorted(root.iterdir()):
            _noSymlinks(folder)
            if not folder.is_dir() or folder.name not in self.cases:
                raise CheckpointError('unknown case in checkpoint integrity inventory')
            for attempt in sorted(folder.iterdir()):
                _noSymlinks(attempt)
                if not attempt.is_dir() or not SAFE_ATTEMPT.fullmatch(attempt.name):
                    raise CheckpointError('invalid checkpoint attempt inventory')
                attempts[folder.name].append(attempt)
                self._verifyAttempt(folder.name, attempt)
            expected = [f'{index:06d}' for index in range(1, len(attempts[folder.name]) + 1)]
            if [path.name for path in attempts[folder.name]] != expected:
                raise CheckpointError('missing checkpoint attempt in integrity inventory')
        return attempts

    def _verifyRunSummaries(self) -> None:
        """Check retained invocation indices against their execution anchors."""
        root = self.directory / 'runs'
        if not root.exists():
            return
        _noSymlinks(root)
        for path in sorted(root.iterdir()):
            if path.name.startswith('.pending-'):
                continue
            summary = _readJson(path)
            if (path.suffix != '.json' or summary.get('schema') != 'nocturne.qualification-checkpoint-summary.v1' or
                    summary.get('executionRunId') != path.stem or summary.get('bindingSha256') != self.bindingSha256 or
                    summary.get('expectedCaseIds') != list(self.cases)):
                raise CheckpointError('historical summary integrity mismatch')
            directory = summary.get('executionDirectory')
            if not isinstance(directory, str) or not Path(directory).is_absolute():
                raise CheckpointError('historical summary execution anchor is missing')
            record = _readJson(Path(directory) / 'EXECUTION.json')
            anchor = {'path':path.relative_to(self.directory).as_posix(), 'sha256':fileDigest(path)}
            if record.get('runId') != path.stem or record.get('checkpointSummary') != anchor:
                raise CheckpointError('historical summary execution anchor integrity mismatch')
            visited = summary.get('visitedCaseIds')
            selected = summary.get('checkpoints')
            if (not isinstance(visited, list) or visited != list(self.cases)[:len(visited)] or
                    not isinstance(selected, dict) or set(selected) != set(visited) or
                    summary.get('completePlan') is not (visited == list(self.cases)) or
                    type(summary.get('passed')) is not bool or summary['passed'] and not summary['completePlan']):
                raise CheckpointError('historical summary complete-plan integrity mismatch')
            for name, checkpoint in selected.items():
                if not isinstance(checkpoint, dict):
                    raise CheckpointError('historical checkpoint anchor integrity mismatch')
                retained = _storedPath(self.directory, checkpoint.get('path'))
                parts = retained.relative_to(self.directory).parts
                if (len(parts) != 4 or parts[0] != 'cases' or parts[1] != name or
                        not SAFE_ATTEMPT.fullmatch(parts[2]) or parts[3] != 'CHECKPOINT.json'):
                    raise CheckpointError('historical checkpoint anchor path integrity mismatch')
                _regular(retained)
                if fileDigest(retained) != checkpoint.get('sha256'):
                    raise CheckpointError('historical checkpoint anchor integrity mismatch')

    def _verifyAttempt(self, name: str, attempt: Path, *, liveOutputs: bool = False) -> dict | None:
        marker = attempt / 'COMPLETE.json'
        if not marker.exists():
            # An interrupted copy or a killed owner never produces a reusable
            # record. Any unfinished attempt is kept for inspection and retried.
            return None
        seal = _readJson(marker)
        checkpointPath = _verifyFile(attempt, seal)
        if checkpointPath.name != 'CHECKPOINT.json':
            raise CheckpointError('invalid checkpoint integrity seal')
        checkpoint = _readJson(checkpointPath)
        start = _readJson(attempt / 'START.json')
        if (checkpoint.get('schema') != CHECKPOINT_SCHEMA or
                checkpoint.get('bindingSha256') != self.bindingSha256 or
                checkpoint.get('case') != self.cases[name] or
                start.get('bindingSha256') != self.bindingSha256 or
                start.get('case') != self.cases[name] or
                checkpoint.get('startSha256') != fileDigest(attempt / 'START.json')):
            raise CheckpointError('checkpoint binding/start integrity mismatch')
        directory = start.get('executionDirectory')
        if not isinstance(directory, str) or not Path(directory).is_absolute():
            raise CheckpointError('checkpoint original execution anchor is missing')
        original = _readJson(Path(directory) / 'EXECUTION.json')
        originalRows = [row for row in original.get('commands', []) if isinstance(row, dict) and row.get('id') == name]
        anchor = {'path':checkpointPath.relative_to(self.directory).as_posix(), 'sha256':seal['sha256']}
        if (original.get('runId') != start.get('executionRunId') or len(originalRows) != 1 or
                originalRows[0].get('checkpoint') != anchor):
            raise CheckpointError('checkpoint original execution anchor integrity mismatch')
        row = checkpoint.get('result', {})
        if (row.get('id') != name or row.get('argv') != self.cases[name]['argv'] or
                row.get('cwd') != self.cases[name]['cwd'] or row.get('status') not in TERMINAL_STATES or
                checkpoint.get('complete') is not True):
            raise CheckpointError('checkpoint result integrity mismatch')
        if row['status'] == 'PASS' and (type(row.get('exitCode')) is not int or row['exitCode'] != 0 or
                type(row.get('childPid')) is not int or row['childPid'] <= 0 or
                checkpoint.get('bindingAfterSha256') != self.bindingSha256):
            raise CheckpointError('uncompleted child cannot supply a passing checkpoint')
        log = checkpoint.get('log', {})
        _verifyFile(attempt, log)
        if log.get('sha256') != row.get('logSha256'):
            raise CheckpointError('observed log/checkpoint integrity mismatch')
        for artifact in checkpoint.get('artifacts', []):
            _verifyFile(attempt, artifact)
        if row['status'] == 'PASS' and liveOutputs:
            roots, files = _artifactInventory(self.cases[name])
            if roots != checkpoint.get('artifactRoots') or len(files) != len(checkpoint.get('artifacts', [])):
                raise CheckpointError('live output artifact membership changed; use a fresh qualification store')
            for (source, rootIndex, relative), artifact in zip(files, checkpoint['artifacts']):
                if (artifact.get('root') != rootIndex or artifact.get('relative') != relative or
                        source.stat().st_size != artifact['bytes'] or fileDigest(source) != artifact['sha256']):
                    raise CheckpointError('live output artifact integrity changed: ' + str(source))
        return checkpoint

    def _assertBinding(self, probe) -> str:
        actual = bindingDigest(probe())
        if actual != self.bindingSha256:
            raise CheckpointError('qualification binding changed during execution or before resume')
        return actual

    def _checkUnfinishedChild(self, name: str, attempt: Path) -> None:
        """Refuse an orphan or an uncertain namespace; never signal its process."""
        if (attempt / 'COMPLETE.json').exists():
            return
        if not (attempt / 'START.json').exists():
            raise CheckpointError('unfinished checkpoint start provenance is missing; inspect its original execution or use a fresh store')
        from delivery_runner import processIdentity
        start = _readJson(attempt / 'START.json')
        if start.get('bindingSha256') != self.bindingSha256 or start.get('case') != self.cases[name]:
            raise CheckpointError('unfinished checkpoint binding integrity mismatch')
        if start.get('host') != socket.gethostname() or start.get('pidNamespace') != self._run.record.get('pidNamespace'):
            raise CheckpointError('unfinished checkpoint owner namespace is unknown; inspect its original host or use a fresh store')
        directory = start.get('executionDirectory')
        if not isinstance(directory, str) or not Path(directory).is_absolute():
            raise CheckpointError('unfinished checkpoint execution provenance is missing')
        record = _readJson(Path(directory) / 'EXECUTION.json')
        if record.get('runId') != start.get('executionRunId'):
            raise CheckpointError('unfinished checkpoint execution provenance integrity mismatch')
        rows = [row for row in record.get('commands', []) if isinstance(row, dict) and row.get('id') == name]
        # A crash may occur after the kernel spawned a child but before its PID
        # was durably written. Missing launch metadata is uncertain ownership,
        # never proof that no child was started. The same rule rejects deleted
        # provenance without inventing a safe recovery or signaling unknown PIDs.
        if len(rows) != 1 or type(rows[0].get('childPid')) is not int or rows[0]['childPid'] <= 0:
            raise CheckpointError('unfinished checkpoint child provenance is incomplete; inspect its original execution or use a fresh store')
        row = rows[0]
        identity = processIdentity(row['childPid'])
        expected = row.get('childProcessIdentity')
        # Weak PID-only identity cannot establish safe PID reuse. Block a
        # live/uncertain process, without killing or adopting it. The Linux
        # pidfd liveness check also identifies exited, unreaped children.
        if identity is not None and (not isinstance(expected, str) or identity.startswith('pid:') or
                                     expected.startswith('pid:') or identity == expected):
            raise CheckpointError('unfinished checkpoint child is still running; wait for its actual exit before resume')

    def bindRun(self, run) -> None:
        """Attach a fresh observed RunJournal; refuse existing commands or reuse."""
        if self._lock is None or self._run is not None or run.record.get('commands') or run.finished:
            raise CheckpointError('checkpoint store requires one fresh execution journal')
        self._run = run
        run.record.update(expectedSteps=len(self.plan), expectedCaseIds=list(self.cases),
                          checkpointDirectory=str(self.directory), checkpointBindingSha256=self.bindingSha256)
        run.write()

    def _retain(self, attempt: Path, case: dict, row: dict, bindingAfter: str) -> dict:
        observed = json.loads(canonicalBytes(row))
        log = Path(self._run.directory) / observed['log']
        logRecord = {'path':'stdout.log', **_copyImmutable(log, attempt / 'stdout.log')}
        if logRecord['sha256'] != observed.get('logSha256'):
            raise CheckpointError('observed process log integrity changed before checkpoint')
        roots, records = [], []
        if observed['status'] == 'PASS':
            try:
                roots, files = _artifactInventory(case)
                for index, (source, rootIndex, relative) in enumerate(files):
                    path = f'artifacts/{index:06d}'
                    records.append({'path':path, 'root':rootIndex, 'relative':relative,
                                    **_copyImmutable(source, attempt / path)})
            except (OSError, CheckpointError) as error:
                observed.update(status='FAIL', reason='output artifact checkpoint failed: ' + str(error))
                row.update(status=observed['status'], reason=observed['reason'])
                self._run.write()
        checkpoint = {'schema':CHECKPOINT_SCHEMA, 'bindingSha256':self.bindingSha256,
                      'bindingAfterSha256':bindingAfter, 'case':case,
                      'startSha256':fileDigest(attempt / 'START.json'),
                      'complete':True, 'finishedAt':time.time(), 'result':observed,
                      'log':logRecord, 'artifactRoots':roots, 'artifacts':records}
        path = attempt / 'CHECKPOINT.json'
        _immutableJson(path, checkpoint)
        seal = {'path':path.name, 'sha256':fileDigest(path), 'bytes':path.stat().st_size}
        _immutableJson(attempt / 'COMPLETE.json', seal)
        return {'path':path.relative_to(self.directory).as_posix(), 'sha256':seal['sha256']}

    def runCase(self, run, name: str, bindingProbe, *, env: dict | None = None) -> dict:
        """Observe one planned real command or reuse its fully verified checkpoint.

        Input order, command, deadline, source, toolchain and environment stay bound.
        Declared case environment overrides apply only after the inherited
        environment matches its binding, so the plan, not the host, sets them.
        Failed, timed-out, blocked or unsealed attempts are never reused. A live
        artifact mismatch fails closed instead of silently blessing missing products.
        Raises CheckpointError on integrity/source changes; child failures retain
        their actual terminal status and are returned for the caller's gate decision.
        """
        if run is not self._run or run.finished or len(self._visited) >= len(self.plan) or self.plan[len(self._visited)]['id'] != name:
            raise CheckpointError('cases must execute exactly once in complete-plan order')
        self._assertBinding(bindingProbe)
        environment = dict(os.environ if env is None else env)
        if self.binding.get('environmentSha256') != bindingDigest(environment):
            raise CheckpointError('command environment binding does not match its execution environment')
        case = self.cases[name]
        attempts = self._scan()[name]
        for attempt in attempts:
            self._checkUnfinishedChild(name, attempt)
        previous = self._verifyAttempt(name, attempts[-1], liveOutputs=True) if attempts else None
        if previous is not None and previous['result']['status'] == 'PASS' and case.get('reusable', True):
            row = json.loads(canonicalBytes(previous['result']))
            log = run.directory / 'logs' / (name + '.log')
            _copyImmutable(attempts[-1] / previous['log']['path'], log)
            checkpoint = attempts[-1] / 'CHECKPOINT.json'
            row.update(log=log.relative_to(run.directory).as_posix(), reused=True,
                       reusedFromRun=_readJson(attempts[-1] / 'START.json')['executionRunId'],
                       checkpoint={'path':checkpoint.relative_to(self.directory).as_posix(),
                                   'sha256':fileDigest(checkpoint)})
            run.record['commands'].append(row)
            run.write()
            print(name + ': REUSED verified immutable checkpoint', flush=True)
        else:
            attempt = self.directory / 'cases' / name / f'{len(attempts) + 1:06d}'
            attempt.mkdir(parents=True, exist_ok=False)
            _syncDirectory(attempt.parent)
            start = {'bindingSha256':self.bindingSha256, 'case':case, 'startedAt':time.time(),
                     'executionRunId':run.record['runId'], 'executionDirectory':str(run.directory),
                     'host':run.record['host'], 'pidNamespace':run.record.get('pidNamespace')}
            _immutableJson(attempt / 'START.json', start)
            try:
                row = run.runStep(name, case['argv'], Path(case['cwd']),
                                  timeoutSeconds=case['timeoutSeconds'], env=environment,
                                  logLimitBytes=case.get('logLimitBytes', 64 * 1024 * 1024),
                                  environmentOverrides=case.get('environmentOverrides'))
            except BaseException:
                if run.record['commands'] and run.record['commands'][-1]['id'] == name:
                    row = run.record['commands'][-1]
                    row['reused'] = False
                    row['checkpoint'] = self._retain(attempt, case, row, bindingDigest(bindingProbe()))
                    run.write()
                raise
            row['reused'] = False
            after = bindingDigest(bindingProbe())
            if after != self.bindingSha256:
                row.update(status='FAIL', reason='qualification binding changed during the observed command')
            row['checkpoint'] = self._retain(attempt, case, row, after)
            run.write()
            if after != self.bindingSha256:
                raise CheckpointError('qualification binding changed during the observed command')
        self._visited.append(name)
        self._selected[name] = dict(row['checkpoint'])
        return row

    def artifact(self, name: str, originalPath: Path) -> Path:
        """Return a selected immutable artifact after integrity verification.

        Use this for parity/review decisions so a stale global report cannot stand
        in for the exact report retained by the selected case. Raises CheckpointError
        when the case did not retain that path or its checkpoint is incomplete.
        """
        selected = self._selected.get(name)
        if selected is None:
            raise CheckpointError('case has no selected checkpoint artifact')
        path = self.directory / selected['path']
        if fileDigest(path) != selected['sha256']:
            raise CheckpointError('selected checkpoint integrity changed')
        attempt = path.parent
        checkpoint = self._verifyAttempt(name, attempt)
        if checkpoint is None:
            raise CheckpointError('case checkpoint is incomplete')
        for artifact in checkpoint['artifacts']:
            root = checkpoint['artifactRoots'][artifact['root']]
            source = Path(root['path']) if artifact['relative'] == '.' else Path(root['path']) / artifact['relative']
            if source == originalPath:
                return attempt / artifact['path']
        raise CheckpointError('artifact not retained by case: ' + str(originalPath))

    def finish(self, run, passed: bool, bindingProbe, **metadata) -> None:
        """Seal a complete-plan summary, then finalize the fresh execution receipt.

        A requested PASS requires every declared case, the current binding, each
        immutable retained log/artifact, and unchanged live output products. Missing
        or nonpassing cases raise CheckpointError; callers cannot override that gate.
        """
        if run is not self._run or run.finished:
            raise CheckpointError('checkpoint execution journal is not active')
        complete = self._visited == list(self.cases) and [row['id'] for row in run.record['commands']] == list(self.cases)
        if passed:
            if not complete:
                raise CheckpointError('partial qualification cannot pass; missing required cases')
            self._assertBinding(bindingProbe)
            self._scan()
            for name, selected in self._selected.items():
                path = self.directory / selected['path']
                if fileDigest(path) != selected['sha256']:
                    raise CheckpointError('selected checkpoint integrity changed')
                checkpoint = self._verifyAttempt(name, path.parent, liveOutputs=True)
                if checkpoint is None or checkpoint['result']['status'] != 'PASS':
                    raise CheckpointError('nonpassing checkpoint cannot qualify')
        summary = {'schema':'nocturne.qualification-checkpoint-summary.v1',
                   'bindingSha256':self.bindingSha256, 'executionRunId':run.record['runId'],
                   'executionDirectory':str(run.directory),
                   'expectedCaseIds':list(self.cases), 'visitedCaseIds':self._visited,
                   'checkpoints':self._selected, 'completePlan':complete,
                   'passed':bool(passed and complete), 'finishedAt':time.time()}
        path = self.directory / 'runs' / (run.record['runId'] + '.json')
        _immutableJson(path, summary)
        run.finish(passed, **metadata, completePlan=complete,
                   checkpointSummary={'path':path.relative_to(self.directory).as_posix(), 'sha256':fileDigest(path)},
                   reusedCases=sum(bool(row.get('reused')) for row in run.record['commands']))
