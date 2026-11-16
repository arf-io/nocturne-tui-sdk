"""Qualification cases must leave the source fingerprint they are bound to unchanged.

qualify.py binds every case to fingerprint(). A case that creates, deletes or
rewrites a fingerprinted file stops a checkpointed run with "qualification binding
changed during the observed command" (Linux host receipt 2026-10-31, qualify-rc2-02:
rc2-project-codegen created native/bindings/typescript/contracts.js).

Each selected rc2 case runs here with its exact --list argv and cwd and the
qualifier's case environment, inside a scratch replica of this checkout, so tracked
evidence and generated pages in the checkout are never rewritten. The replica holds
every fingerprinted file plus the build products and the unfingerprinted inputs the
cases read. Its fingerprint and rc2 plan must equal the checkout's (modulo the root
path) before any case runs.

Byte hashes alone cannot see a writer that reproduces existing bytes: a stale
generated file overwritten with identical output kept the macOS fingerprint stable
and hid this defect. Every fingerprinted path is therefore also compared by inode,
size and modification time.

This module is the qualifier's explicit fingerprint-stability case in the exhaustive and
rc2 profiles (python -m unittest -v qualification_fingerprint_stability_check, from
native/tests). Its name carries no test prefix, so unittest discovery, including the
python-contracts step, never collects the twelve-minute replay; the case has its own
deadline (STEP_TIMEOUT_FLOORS in scripts/qualify.py).

Cases default to DEFAULT_CASES. NOCTURNE_FINGERPRINT_STABILITY_STEPS selects others for a
run by hand: comma-separated rc2 case ids, or "all" for the whole rc2 plan in plan order
except this step, which cannot replay itself (later cases consume earlier build products).
A selection that names no case is refused, and a run fails unless every selected case was
replayed. The qualifier's step pins the variable to the empty default (STEP_ENVIRONMENT_PINS
in scripts/qualify.py), so a value exported by the caller narrows only a run by hand, never
the journalled step, and a PASS recorded for the step replayed every DEFAULT_CASES entry.
Build first (sh build-native.sh). A case whose runtime is missing fails as BLOCKED; nothing
is skipped.
"""
from __future__ import annotations
from pathlib import Path
import json, os, shutil, signal, subprocess, sys, tempfile, threading, time, unittest

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
sys.path.insert(0, str(NATIVE / 'scripts'))
from qualify import fingerprint
from cargo_example import cargoEnvironment
from toolchain import discover

SELECTION = 'NOCTURNE_FINGERPRINT_STABILITY_STEPS'
STEP = 'fingerprint-stability'  # the plan case that runs this module
DEFAULT_CASES = ('gallery', 'typescript-types', 'sdk-contract', 'rc2-project-codegen', 'rc2-reference-validate')
# Unfingerprinted inputs the cases read: build products, page templates, launch and
# release files. Generated evidence media is not copied; a case that needs it fails
# visibly instead of passing against a partial replica.
RUNTIME_FOLDERS = ('native/dist', 'native/web', 'native/reference-evidence', 'tools', 'docs')
UNCOPIED = ('__pycache__', 'node_modules', 'target')
# tsc's CommonJS output for the type-only native/bindings/typescript/contracts.ts.
CONTRACTS_STUB = b'"use strict";\nObject.defineProperty(exports, "__esModule", { value: true });\n'


def replicate(destination: Path) -> dict:
    """Copy the checkout's fingerprinted files and case inputs; return its fingerprint.

    destination becomes a repository root with the same relative layout. Files are
    copied with their metadata, so a later write is visible as a new modification time.
    """
    live = fingerprint(NATIVE)
    for name in live['files']:
        target = Path(os.path.normpath(destination / 'native' / name))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(NATIVE / name, target)
    for folder in RUNTIME_FOLDERS:
        if (REPOSITORY / folder).is_dir():
            shutil.copytree(REPOSITORY / folder, destination / folder, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(*UNCOPIED))
    for source, target in [(REPOSITORY, destination), (NATIVE, destination / 'native')]:
        for path in source.iterdir():
            if path.is_file(): shutil.copy2(path, target / path.name)
    (destination / 'native/evidence').mkdir(exist_ok=True)
    return live


def observe(native: Path) -> tuple[dict, dict]:
    """Return fingerprint(native) and (inode, size, mtime_ns) for each fingerprinted file."""
    current = fingerprint(native)
    status = {name: (lambda s: (s.st_ino, s.st_size, s.st_mtime_ns))((native / name).stat())
              for name in current['files']}
    return current, status


def differences(before: tuple[dict, dict], after: tuple[dict, dict]) -> dict:
    """Name every created, deleted, rewritten or content-changed fingerprinted path."""
    (oldPrint, oldStatus), (newPrint, newStatus) = before, after
    common = set(oldStatus) & set(newStatus)
    return {'fingerprintChanged': oldPrint['sha256'] != newPrint['sha256'],
            'created': sorted(set(newStatus) - set(oldStatus)),
            'deleted': sorted(set(oldStatus) - set(newStatus)),
            'rewritten': sorted(name for name in common if oldStatus[name] != newStatus[name]),
            'contentChanged': sorted(name for name in common if oldPrint['files'][name] != newPrint['files'][name])}


def rc2Plan(native: Path) -> list[dict]:
    """The strict rc2 cases exactly as qualify.py --list declares them for this root."""
    result = subprocess.run([sys.executable, str(native / 'scripts/qualify.py'), '--profile', 'rc2', '--strict', '--capture', '--list'],
                            cwd=native, capture_output=True, text=True, timeout=600)
    if result.returncode != 0: raise AssertionError('qualify.py --list failed: ' + result.stderr[-4000:])
    return json.loads(result.stdout)


def portable(plan: list[dict], repository: Path, tools: list[str]) -> list[dict]:
    """Replace the repository root (but not tool executables) with a placeholder."""
    text = json.dumps(plan)
    for index, tool in enumerate(tools): text = text.replace(json.dumps(tool)[1:-1], f'@TOOL{index}@')
    return json.loads(text.replace(json.dumps(str(repository))[1:-1], '@REPOSITORY@'))


def caseEnvironment(repository: Path) -> dict:
    """The environment qualify.py main() gives its cases, for a replica root."""
    environment = dict(os.environ)
    environment.setdefault('CARGO_NET_OFFLINE', 'true')
    environment.setdefault('CARGO_TERM_COLOR', 'never')
    module = environment.get('NOCTURNE_TYPESCRIPT_MODULE') or str(
        Path(shutil.which('tsc', path=environment.get('PATH')) or 'tsc').resolve().parent.parent / 'lib/typescript.js')
    environment.setdefault('NOCTURNE_TYPESCRIPT_MODULE', module)
    return cargoEnvironment(repository, environment)


def stop(child: subprocess.Popen) -> None:
    """Terminate the case's whole session, then reap it."""
    try:
        if os.name == 'posix': os.killpg(child.pid, signal.SIGTERM)
        else: child.terminate()
        child.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if os.name == 'posix':
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
        else: child.kill()
        child.wait()


def execute(case: dict, environment: dict, log: Path) -> tuple[str, int | None, float]:
    """Run one case to completion like RunJournal.runStep; return status, exit code, seconds."""
    begin = time.monotonic()
    with log.open('wb') as stream:
        try:
            child = subprocess.Popen(case['argv'], cwd=case['cwd'], env=environment, stdin=subprocess.DEVNULL,
                                     stdout=stream, stderr=subprocess.STDOUT, start_new_session=os.name == 'posix')
        except OSError as error:
            stream.write(f'BLOCKED: {error}\n'.encode())
            return 'BLOCKED', None, time.monotonic() - begin
        try:
            code = child.wait(timeout=case['timeoutSeconds'])
        except subprocess.TimeoutExpired:
            stop(child)
            return 'TIMEOUT', None, time.monotonic() - begin
        except BaseException:
            stop(child)
            raise
    return ('PASS' if code == 0 else 'FAIL'), code, time.monotonic() - begin


def selected(plan: list[dict]) -> list[dict]:
    """The rc2 cases to replay: DEFAULT_CASES when the selection is unset or blank, never none."""
    value = os.environ.get(SELECTION, '').strip()
    names = [case['id'] for case in plan if case['id'] != STEP] if value == 'all' else [name.strip() for name in value.split(',') if name.strip()] if value else list(DEFAULT_CASES)
    if not names: raise AssertionError(f'{SELECTION} selects no rc2 case ({value!r}); a replay of nothing cannot show stability')
    if STEP in names: raise AssertionError(f'{STEP} runs this module and cannot replay itself')
    unknown = sorted(set(names) - {case['id'] for case in plan})
    if unknown: raise AssertionError('Not rc2 case ids: ' + ', '.join(unknown))
    return [case for case in plan if case['id'] in set(names)]


def requireReplayed(cases: list[dict], replayed: list[str]) -> None:
    """Fail unless at least one case was selected and every selected case was replayed."""
    if not cases: raise AssertionError('no case was selected, so nothing was replayed')
    missing = [case['id'] for case in cases if case['id'] not in replayed]
    if missing: raise AssertionError('selected but not replayed: ' + ', '.join(missing))


class QualificationFingerprintStability(unittest.TestCase):
    def testIdenticalRewriteIsAWriteThatTheHashCannotSee(self):
        with tempfile.TemporaryDirectory(prefix='nocturne-fingerprint-rewrite-') as temporary:
            native = Path(temporary) / 'native'; stale = native / 'bindings/typescript/contracts.js'
            stale.parent.mkdir(parents=True); stale.write_bytes(CONTRACTS_STUB); os.utime(stale, ns=(0, 0))
            before = observe(native)
            stale.write_bytes(CONTRACTS_STUB)
            after = observe(native); change = differences(before, after)
            self.assertFalse(change['fingerprintChanged'])
            self.assertEqual(change['rewritten'], ['bindings/typescript/contracts.js'])
            (native / 'bindings/typescript/fresh.js').write_bytes(CONTRACTS_STUB)
            self.assertEqual(differences(after, observe(native))['created'], ['bindings/typescript/fresh.js'])

    def testRc2CasesLeaveTheFingerprintUnchanged(self):
        # Cases run in their own sessions, out of reach of a group kill aimed at this
        # process (the qualifier's step timeout). TERM tears them down first.
        def interrupted(signum, frame): raise KeyboardInterrupt(f'received signal {signum}')
        previous = signal.signal(signal.SIGTERM, interrupted) if threading.current_thread() is threading.main_thread() else None
        try: self.observeSelectedCases()
        finally:
            if previous is not None: signal.signal(signal.SIGTERM, previous)

    def observeSelectedCases(self):
        # The selection is judged first, so a bad one fails the same way whatever the build state.
        livePlan = rc2Plan(NATIVE); cases = selected(livePlan)
        for name in ['libnocturne_native.dylib' if sys.platform == 'darwin' else 'libnocturne_native.so', 'nocturne_native.wasm']:
            self.assertTrue((NATIVE / 'dist' / name).is_file(), f'native/dist/{name} is missing; run sh build-native.sh first')
        with tempfile.TemporaryDirectory(prefix='nocturne-fingerprint-stability-') as temporary:
            base = Path(temporary).resolve(); repository = base / 'repository'; logs = base / 'logs'; logs.mkdir()
            self.assertFalse(base.is_relative_to(REPOSITORY), 'the replica must live outside the checkout it measures')
            live = replicate(repository); native = repository / 'native'
            self.assertEqual(fingerprint(native)['sha256'], live['sha256'], 'replica must carry the exact qualification fingerprint')
            replicaPlan = rc2Plan(native)
            self.assertNotIn(str(NATIVE), json.dumps(replicaPlan), 'replica cases must never address the checkout')
            tool = discover()
            tools = sorted({sys.executable, *(value for value in tool.values() if isinstance(value, str) and os.path.isabs(value))}, key=len, reverse=True)
            self.assertEqual(portable(replicaPlan, repository, tools), portable(livePlan, REPOSITORY, tools))
            planned = {case['id']: case for case in replicaPlan}; environment = caseEnvironment(repository); replayed = []
            for case in [planned[case['id']] for case in cases]:
                log = logs / (case['id'] + '.log'); before = observe(native)
                status, code, seconds = execute(case, environment, log)
                replayed.append(case['id'])
                change = differences(before, observe(native))
                print(f"{case['id']}: {status} exit={code} {seconds:.1f}s {json.dumps(change)}", file=sys.stderr, flush=True)
                with self.subTest(case=case['id'], check='completed'):
                    tail = '\n'.join(log.read_text(errors='replace').splitlines()[-60:])
                    self.assertEqual(status, 'PASS', f"{case['id']} {status} exit={code}; an unfinished case cannot show stability\n{tail}")
                with self.subTest(case=case['id'], check='fingerprint'):
                    self.assertEqual({key: value for key, value in change.items() if value}, {},
                                     f"{case['id']} wrote inside the qualification fingerprint")
            requireReplayed(cases, replayed)


if __name__ == '__main__': unittest.main()
