#!/usr/bin/env python3
"""Build and execute both dependency-backed Linux hosts using provisioned caches.

No downloads, installation scripts, manifest edits or lock regeneration. The
current C library/WASM must already exist in the build copy. Targets and evidence
are NEW external directories. RunJournal owns each command; each PTY case owns
its real terminal child. Missing one framework does not suppress the other host.

Example, from an SDK build copy with external node_modules on normal resolution:
 python3 native/scripts/qualify_dependency_hosts.py --target-dir /tmp/hosts-target \
   --evidence-dir /tmp/hosts-evidence
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shlex
import signal
import sys
from pathlib import Path
from delivery_runner import RunJournal, atomicJson
from dependency_pty import ENV_KEYS, digest, timestamp

ROOT = Path(__file__).resolve().parents[2]


def offlineEnvironment(base: dict[str, str], target: Path) -> dict[str, str]:
    """Return a copied environment with readonly, offline Go resolution.

    Keep the caller's verified module cache and Rust environment. Reject Go flags
    that could alter module selection, rather than silently replacing them. An
    absent GOCACHE receives an external target-local path. Raises ValueError for
    a conflicting module flag; never mutates the supplied mapping.
    """
    env = dict(base)
    flags = shlex.split(env.get('GOFLAGS', ''))
    for flag in flags:
        if (flag.startswith('-modfile') or flag == '-mod' or
                flag.startswith('-mod=') and flag != '-mod=readonly'):
            raise ValueError('GOFLAGS must retain the original readonly module graph')
    if '-mod=readonly' not in flags:
        flags.append('-mod=readonly')
    env.update(GOFLAGS=' '.join(flags), GOPROXY='off', GOSUMDB='off',
               GOTOOLCHAIN='local', PYTHONDONTWRITEBYTECODE='1')
    env.setdefault('GOCACHE', str(target / 'go-cache'))
    return env


def sourceFingerprint(root: Path = ROOT) -> dict[str, str]:
    """Hash the complete source tree while excluding external/generated products."""
    ignored = {'.git', 'node_modules', '__pycache__', 'target'}
    # build_gallery.py writes these exact ignored outputs into a fresh tree.
    # Authored HTML, including identically named files elsewhere, remains source.
    galleryProducts = {Path('Nocturne-RC4.html'), Path('native/Nocturne-RC4-Source-Build.html')}
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if relative.parts[:2] == ('native', 'dist') or relative in galleryProducts:
            continue
        if any(part in ignored for part in relative.parts) or path.is_symlink() or not path.is_file():
            continue
        hashes[str(relative)] = digest(path)
    return hashes


def sourceSummary(files: dict[str, str]) -> dict[str, object]:
    """Return the canonical aggregate and file map for one source snapshot."""
    aggregate = hashlib.sha256()
    for name, fileDigest in sorted(files.items()):
        aggregate.update(name.encode('utf-8'))
        aggregate.update(b'\0')
        aggregate.update(fileDigest.encode('ascii'))
        aggregate.update(b'\n')
    return {'sha256': aggregate.hexdigest(), 'files': dict(files)}


def outcome(rows: list[dict]) -> str:
    """Combine terminal results; an empty or unfinished plan can never pass."""
    states = {row['status'] for row in rows}
    for status in ('INTERRUPTED', 'TIMEOUT', 'BLOCKED', 'FAIL'):
        if status in states:
            return status
    return 'PASS' if rows and states == {'PASS'} else 'FAIL'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-dir', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=180,
                        help='finite seconds per build/test command')
    parser.add_argument('--pty-timeout', type=float, default=20,
                        help='finite seconds per individual PTY case')
    args = parser.parse_args()
    target, out = args.target_dir.resolve(), args.evidence_dir.resolve()
    for path in (target, out):
        if path.exists() or path.is_relative_to(ROOT):
            parser.error('target and evidence must be new external paths')
    if target == out or target.is_relative_to(out) or out.is_relative_to(target):
        parser.error('target and evidence must be disjoint')
    if any(not math.isfinite(n) or n <= 0 for n in (args.timeout, args.pty_timeout)):
        parser.error('timeouts must be positive and finite')
    if not sys.platform.startswith('linux'):
        parser.error('this gate qualifies Linux PTYs only')
    try:
        env = offlineEnvironment(os.environ, target)
    except ValueError as error:
        parser.error(str(error))
    target.mkdir(parents=True)
    before = sourceSummary(sourceFingerprint())
    summary = dict(schema='nocturne.dependency-hosts.qualification.v2', status='RUNNING',
                   startedAt=timestamp(), platform=platform.platform(),
                   sourceBefore=before['sha256'], sourceFiles=len(before['files']), commands=[], hosts={},
                   fullRC4Qualified=False, stableRelease=False,
                   environment={key: env[key] for key in ENV_KEYS if key in env})

    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'signal {signum}')
    old = signal.signal(signal.SIGTERM, interrupted)
    try:
        with RunJournal(out) as journal:
            summary['commands'] = journal.record['commands']
            atomicJson(out / 'QUALIFICATION.json', summary)

            def step(name, argv, cwd=ROOT, timeout=None, acquisition=False):
                started = timestamp()
                row = journal.runStep(name, argv, cwd, timeoutSeconds=timeout or args.timeout, env=env)
                row.update(startedAt=started, finishedAt=timestamp(),
                           timeoutSeconds=timeout or args.timeout,
                           environment=summary['environment'])
                if acquisition and row['status'] == 'FAIL':
                    log = (out / row['log']).read_text(errors='replace')
                    if any(s in log for s in ('MODULE_NOT_FOUND', 'module lookup disabled by GOPROXY=off',
                                              'missing go.sum entry')):
                        row['status'] = 'BLOCKED'
                        row['reason'] = 'Exact dependency unavailable; see original exit and log'
                journal.write()
                atomicJson(out / 'QUALIFICATION.json', summary)
                return row

            step('pty-harness', [sys.executable, 'native/tests/test_dependency_pty.py'])
            step('gate-policy', [sys.executable, 'native/tests/test_dependency_host_gate.py'])
            nodeHome = ROOT / 'native/hosts/terminal-kit'
            nodeStart = len(summary['commands'])
            step('node-version', ['node', '--version'])
            # package.json loading uses Node's ordinary package resolution. The
            # supplied installation is not copied into source or a fake framework.
            packageCheck = """const fs=require('fs');const p=require('./package.json');
const versions={};for(const [n,v] of Object.entries(p.dependencies)){
 const f=require.resolve(n+'/package.json');const j=JSON.parse(fs.readFileSync(f));
 if(j.version!==v)throw Error(n+': expected '+v+', got '+j.version);
 versions[n]={version:j.version,packageJson:f};}console.log(JSON.stringify(versions,null,2));"""
            dependency = step('node-dependencies', ['node', '-e', packageCheck], nodeHome, acquisition=True)
            if dependency['status'] == 'PASS':
                step('terminal-kit-tests', ['node', '--test', 'host.test.mjs'], nodeHome)
                row = step('terminal-kit-pty', [sys.executable, 'native/scripts/check_dependency_hosts.py',
                           '--host', 'terminal-kit', '--evidence-dir', str(out / 'terminal-kit-pty'),
                           '--timeout', str(args.pty_timeout)], timeout=args.pty_timeout * 11 + 20)
                if row['exitCode'] in (3, 4):
                    row['status'] = {3: 'BLOCKED', 4: 'TIMEOUT'}[row['exitCode']]
            summary['hosts']['terminal-kit'] = {'status': outcome(summary['commands'][nodeStart:])}

            goHome = ROOT / 'native/hosts/bubbletea'
            goStart = len(summary['commands'])
            step('go-version', ['go', 'version'])
            host = target / 'bubbletea-host'
            fixture = target / 'bubbletea-fixture'
            built = step('bubbletea-build', ['go', 'build', '-o', str(host), '.'], goHome, acquisition=True)
            tests = step('bubbletea-tests', ['go', 'test', '-count=1', '-v', '.'], goHome, acquisition=True)
            compiled = step('bubbletea-fixture-build', ['go', 'test', '-c', '-o', str(fixture)], goHome, acquisition=True)
            if built['status'] == 'PASS':
                step('bubbletea-linked-dependencies', ['go', 'version', '-m', str(host)])
            if built['status'] == compiled['status'] == 'PASS':
                row = step('bubbletea-pty', [sys.executable, 'native/scripts/check_dependency_hosts.py',
                           '--host', 'bubbletea', '--bubbletea-bin', str(host),
                           '--bubbletea-fixture', str(fixture), '--evidence-dir', str(out / 'bubbletea-pty'),
                           '--timeout', str(args.pty_timeout)], timeout=args.pty_timeout * 10 + 20)
                if row['exitCode'] in (3, 4):
                    row['status'] = {3: 'BLOCKED', 4: 'TIMEOUT'}[row['exitCode']]
            summary['hosts']['bubbletea'] = {'status': outcome(summary['commands'][goStart:])}
            for hostName, expected in [('terminal-kit', 11), ('bubbletea', 10)]:
                receipt = out / (hostName + '-pty/QUALIFICATION.json')
                hostResult = summary['hosts'][hostName]
                if receipt.exists():
                    detail = json.loads(receipt.read_text())
                    cases = detail.get('cases', [])
                    hostResult.update(ptyReceipt=str(receipt.relative_to(out)),
                                      ptyReceiptSha256=digest(receipt),
                                      executedPtyCases=len(cases), expectedPtyCases=expected)
                    accepted = detail.get('status') == 'PASS' and len(cases) == expected and all(
                        c.get('accepted') and c.get('status') == 'PASS' and
                        c.get('rawModeObserved') and c.get('terminalAttributesRestoredByChild') and
                        not c.get('parentForcedCleanup') for c in cases)
                    hostResult['qualified'] = hostResult['status'] == 'PASS' and accepted
                else:
                    hostResult.update(qualified=False, executedPtyCases=0, expectedPtyCases=expected)
            after = sourceSummary(sourceFingerprint())
            sourceChanges = sorted(p for p in before['files'].keys() | after['files'].keys()
                                   if before['files'].get(p) != after['files'].get(p))
            summary.update(sourceAfter=after['sha256'], sourceUnchanged=before['sha256'] == after['sha256'],
                           sourceAfterFiles=len(after['files']), sourceChanges=sourceChanges,
                           status=outcome(summary['commands']))
            if not summary['sourceUnchanged'] or not all(h['qualified'] for h in summary['hosts'].values()):
                if summary['status'] == 'PASS':
                    summary['status'] = 'FAIL'
            journal.finish(summary['status'] == 'PASS', sourceUnchanged=summary['sourceUnchanged'],
                           hosts=summary['hosts'], fullRC4Qualified=False)
    except BaseException as error:
        summary.update(status='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'FAIL', reason=repr(error))
    finally:
        signal.signal(signal.SIGTERM, old)
        summary['finishedAt'] = timestamp()
        out.mkdir(parents=True, exist_ok=True)
        atomicJson(out / 'QUALIFICATION.json', summary)
    print(json.dumps({k: summary[k] for k in ['status', 'hosts', 'fullRC4Qualified']}, indent=2))
    return {'PASS': 0, 'FAIL': 2, 'BLOCKED': 3, 'TIMEOUT': 4, 'INTERRUPTED': 130}[summary['status']]


if __name__ == '__main__':
    raise SystemExit(main())
