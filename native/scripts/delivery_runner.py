#!/usr/bin/env python3
"""Observed child-process execution with atomic, non-reusable terminal receipts.

A RUNNING file is a diagnostic, never a synchronization primitive. runStep waits
on the actual child process. inspectRun reports an orphaned process as ABANDONED.
The owner uses finish only after all required checks and artifact verification.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import math
import os
import re
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid


ENVIRONMENT_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')


def declaredEnvironment(overrides: dict | None) -> dict[str, str]:
    """Validate one step's declared environment overrides and return a copy.

    Names must be portable variable names and values strings without NUL. A
    malformed declaration is a ValueError, raised before any process starts.
    """
    if overrides is None: return {}
    if not isinstance(overrides, dict) or any(
            not isinstance(key, str) or not ENVIRONMENT_NAME.fullmatch(key) or
            not isinstance(value, str) or '\x00' in value for key, value in overrides.items()):
        raise ValueError('declared environment overrides must map portable names to strings without NUL')
    return dict(overrides)


def atomicJson(path: Path, value: dict) -> None:
    """Replace a JSON record atomically; never expose a partially written receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name+'.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def processIdentity(pid: int) -> str | None:
    """Linux boot ID plus process start ticks guard against PID reuse.

    Other platforms still check liveness, but report identityStrength accordingly.
    """
    if pid <= 0: return None
    # A mounted /proc view can outlive or describe another PID namespace. The
    # kernel liveness probe must agree before process-start metadata is trusted.
    try: os.kill(pid, 0)
    except ProcessLookupError: return None
    except PermissionError: pass
    except OSError: return None
    if hasattr(os, 'pidfd_open'):
        try:
            descriptor = os.pidfd_open(pid)
            try:
                if select.select([descriptor], [], [], 0)[0]: return None
            finally: os.close(descriptor)
        except ProcessLookupError: return None
        except OSError: pass
    try:
        if int(Path('/proc/self/stat').read_text().split(' ',1)[0]) != os.getpid():
            return f'pid:{pid}'
        stat = Path(f'/proc/{pid}/stat').read_text()
        fields = stat[stat.rfind(')')+2:].split()
        if fields[0] == 'Z': return None
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip()+':'+fields[19]
    except (OSError, IndexError):
        try: os.kill(pid, 0); return f'pid:{pid}'
        except OSError: return None


def inspectRun(directory: Path) -> dict:
    """Read a completed record or report a live/abandoned run without busy waiting.

    Returns a copy. Never rewrites evidence or interprets a timeout as success.
    """
    record = json.loads((directory/'EXECUTION.json').read_text())
    if record.get('status') == 'RUNNING':
        identity = processIdentity(int(record.get('pid', -1))) if record.get('pid', 0)>0 else None
        if identity is None or (record.get('processIdentity') and identity != record['processIdentity']):
            record.update(status='ABANDONED', complete=False, passed=False)
    return record


class RunJournal:
    """Own one qualification run and its real child processes.

    Inputs: a fresh directory and heartbeat interval in seconds. Existing receipts
    are refused. On exception or interruption the context writes a terminal FAIL
    or INTERRUPTED record. SIGKILL cannot run cleanup: inspectRun then detects the
    dead owner. Does not install software or elevate privileges.
    """
    def __init__(self, directory: Path, heartbeatSeconds: float = 5.0, descendantGraceSeconds: float = 2.0):
        if not math.isfinite(heartbeatSeconds) or heartbeatSeconds <= 0:
            raise ValueError('finite positive heartbeat required')
        if not math.isfinite(descendantGraceSeconds) or descendantGraceSeconds < 0:
            raise ValueError('finite non-negative descendant grace required')
        self.directory = Path(directory).resolve()
        self.heartbeatSeconds = heartbeatSeconds
        self.descendantGraceSeconds = descendantGraceSeconds
        self.receipt = self.directory/'EXECUTION.json'
        self.child: subprocess.Popen | None = None
        self.started = time.monotonic()
        self.finished = False
        self.record: dict = {}

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        # O_EXCL prevents two runners from reusing the same run directory.
        if self.receipt.exists(): raise FileExistsError(str(self.receipt))
        fd = os.open(self.directory/'.owner.lock', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        os.close(fd)
        pid = os.getpid()
        self.record = dict(schema='nocturne.execution.v2', runId=str(uuid.uuid4()),
                           pid=pid, host=socket.gethostname(), processIdentity=processIdentity(pid),
                           startedAt=time.time(), status='RUNNING', complete=False,
                           passed=False, commands=[], artifacts=[])
        identity = self.record['processIdentity']
        self.record['identityStrength'] = 'process-start' if identity and not identity.startswith('pid:') else 'pid-liveness-only'
        try: self.record['pidNamespace'] = os.readlink('/proc/self/ns/pid')
        except OSError: self.record['pidNamespace'] = None
        self.write()
        return self

    def write(self):
        self.record['elapsedSeconds'] = round(time.monotonic()-self.started, 3)
        self.record['updatedAt'] = time.time()
        atomicJson(self.receipt, self.record)

    def childGroupExists(self) -> bool:
        """Check the owned POSIX session's group, even after its leader exits.

        This is process supervision, not containment of a program that deliberately
        escapes the session. Non-POSIX platforms expose direct-child liveness only.
        """
        if self.child is None: return False
        if os.name != 'posix': return self.child.poll() is None
        try:
            os.killpg(self.child.pid, 0)
            return True
        except ProcessLookupError: return False
        except PermissionError:
            if sys.platform != 'darwin': raise
            # Darwin can report EPERM for a group with only exiting/zombie
            # members. Confirm absence of live members; never suppress an
            # actual inability to supervise a running process.
            result = subprocess.run(['/bin/ps', '-axo', 'pgid=,stat='],
                                    capture_output=True, text=True, check=True, timeout=5)
            for line in result.stdout.splitlines():
                group, state = line.split()
                if int(group) == self.child.pid and not state.startswith('Z'):
                    raise
            return False

    def signalChildGroup(self, sig):
        try: os.killpg(self.child.pid, sig)
        except ProcessLookupError: pass
        except PermissionError:
            if self.childGroupExists(): raise

    def terminateChild(self):
        """Terminate the whole owned group; reap the direct child before return.

        A leader can exit on TERM while a descendant ignores it. Always escalate
        the remaining group, not only a still-running leader. Never target an
        arbitrary PID read from an older receipt.
        """
        if self.child is None: return
        if os.name == 'posix':
            self.signalChildGroup(signal.SIGTERM)
            deadline = time.monotonic()+.25
            while self.childGroupExists() and time.monotonic() < deadline:
                self.child.poll()
                time.sleep(.01)
            self.signalChildGroup(signal.SIGKILL)
        elif self.child.poll() is None:
            self.child.terminate()
            try: self.child.wait(timeout=2)
            except subprocess.TimeoutExpired: self.child.kill()
        self.child.wait(timeout=5)

    def runStep(self, name: str, argv: list[str], cwd: Path,
                timeoutSeconds: float = 900, env: dict | None = None,
                logLimitBytes: int = 64*1024*1024,
                environmentOverrides: dict | None = None) -> dict:
        """Execute one command and wait for its process, with a per-step deadline.

        After the leader exits, descendants still in its process group get at most
        ``descendantGraceSeconds`` to finish exiting; ``descendantExitSeconds`` records
        the wait. A group that persists is terminated and fails the step.

        Returns the actual result and writes the log and its SHA-256. Failed or
        missing tools are records, not exceptions that leave status RUNNING.
        ``environmentOverrides`` are the step's declared variables: they replace
        the same names in ``env`` (or the inherited environment) for this child
        only, and the step record retains them.
        """
        if self.finished: raise RuntimeError('run already finalized')
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):
            raise ValueError('step name must be a safe filename')
        if any(r['id']==name for r in self.record['commands']): raise ValueError('duplicate step name')
        if not argv or not math.isfinite(timeoutSeconds) or timeoutSeconds <= 0:
            raise ValueError('command and finite positive timeout required')
        if type(logLimitBytes) is not int or logLimitBytes <= 0:
            raise ValueError('positive integer log capacity required')
        overrides = declaredEnvironment(environmentOverrides)
        childEnv = {**(os.environ if env is None else env), **overrides} if overrides else env
        logs = self.directory/'logs'; logs.mkdir(exist_ok=True)
        log = logs/(name+'.log'); begin=time.monotonic()
        step = dict(id=name, argv=argv, cwd=str(Path(cwd).resolve()),
                    log=str(log.relative_to(self.directory)), status='RUNNING', exitCode=None,
                    timeoutSeconds=timeoutSeconds, logLimitBytes=logLimitBytes, startedAt=time.time())
        if overrides: step['environmentOverrides'] = overrides
        self.record['commands'].append(step); self.record['currentStep']=name; self.write()
        deadline = begin+timeoutSeconds; nextBeat = begin+self.heartbeatSeconds
        try:
            with log.open('wb') as stream:
                try:
                    self.child=subprocess.Popen(argv,cwd=cwd,env=childEnv,stdout=stream,
                                                stderr=subprocess.STDOUT,start_new_session=os.name=='posix')
                except OSError as error:
                    stream.write((str(error)+'\n').encode())
                    step.update(status='BLOCKED', reason=str(error))
                else:
                    step['childPid']=self.child.pid
                    step['childProcessIdentity']=processIdentity(self.child.pid)
                    self.write()
                    while self.child.poll() is None:
                        now=time.monotonic()
                        if now >= deadline:
                            self.terminateChild(); step['status']='TIMEOUT'; break
                        if log.stat().st_size > logLimitBytes:
                            self.terminateChild(); step.update(status='FAIL',reason='log capacity exceeded'); break
                        if now >= nextBeat:
                            step['seconds']=round(now-begin,3); self.write()
                            print(f'{name}: RUNNING ({step["seconds"]:.1f}s; pid {self.child.pid})',flush=True)
                            nextBeat=now+self.heartbeatSeconds
                        time.sleep(min(.1, max(.001, deadline-now)))
                    step['exitCode']=self.child.wait()
                    if self.childGroupExists():
                        # The leader is reaped, but a grandchild may still be exiting (for
                        # example flushing coverage profiles). Wait a bounded grace window
                        # and record it; a group that persists past the window is a
                        # leftover: it is terminated and the step fails.
                        waited=time.monotonic(); graceEnd=waited+self.descendantGraceSeconds
                        while self.childGroupExists() and time.monotonic() < graceEnd: time.sleep(.01)
                        step['descendantExitSeconds']=round(time.monotonic()-waited,3)
                        if self.childGroupExists():
                            self.terminateChild()
                            if step['status']=='RUNNING':
                                step.update(status='FAIL', reason='Descendant remained after command leader exited')
                    if step['status']=='RUNNING': step['status']='PASS' if step['exitCode']==0 else 'FAIL'
                    if log.stat().st_size > logLimitBytes: step.update(status='FAIL', reason='log capacity exceeded')
        except BaseException:
            self.terminateChild(); step['exitCode']=self.child.returncode if self.child else None
            step['status']='INTERRUPTED'; raise
        finally:
            step['seconds']=round(time.monotonic()-begin,3)
            if log.exists(): step['logSha256']=hashlib.sha256(log.read_bytes()).hexdigest()
            self.child=None; self.record['currentStep']=None; self.write()
        print(f'{name}: {step["status"]} ({step["seconds"]:.3f}s)',flush=True)
        return step

    def finish(self, passed: bool, **metadata):
        """Finalize only after verification. Failed steps cannot be blessed as PASS."""
        if passed and not self.record['commands']:
            raise ValueError('empty execution: no command was run')
        if passed and any(r['status']!='PASS' for r in self.record['commands']):
            raise ValueError('cannot mark failed or blocked checks passed')
        expected = self.record.get('expectedSteps')
        expectedIds = self.record.get('expectedCaseIds')
        if passed and (expected is not None and (type(expected) is not int or expected <= 0 or
                len(self.record['commands']) != expected) or expectedIds is not None and
                [row['id'] for row in self.record['commands']] != expectedIds):
            raise ValueError('partial or empty declared qualification plan cannot pass')
        self.record.update(metadata)
        self.record.update(status='PASS' if passed else 'FAIL',complete=True,passed=passed)
        self.record['finishedAt']=time.time(); self.finished=True; self.write()

    def __exit__(self, kind, error, traceback):
        self.terminateChild()
        if kind is not None:
            self.record.update(status='INTERRUPTED' if issubclass(kind,KeyboardInterrupt) else 'FAIL',
                               complete=True,passed=False,exception=f'{kind.__name__}: {error}')
            self.record['finishedAt']=time.time(); self.finished=True; self.write()
        elif not self.finished:
            self.finish(False,reason='Owner left without completing qualification')
        return False


def main():
    """Inspect a run; never wait on, advance, or change another run's receipt."""
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    try: record=inspectRun(args.directory)
    except (OSError,ValueError) as error:
        record={'status':'INVALID_OR_MISSING','complete':False,'passed':False,'error':str(error)}
    print(json.dumps(record,indent=2))
    return 0 if record.get('status')=='PASS' and record.get('passed') else (3 if record.get('status')=='RUNNING' else 2)
if __name__=='__main__':raise SystemExit(main())
