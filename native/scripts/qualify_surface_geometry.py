#!/usr/bin/env python3
"""Run real geometry checks and preserve exact source/toolchain/command receipts."""
from pathlib import Path
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

from delivery_runner import RunJournal, atomicJson
from qualify import fingerprint

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'c7deb564c70b3f778d538fbed115d71ad49879e2'


def retainReplayArtifacts(source: Path, destination: Path, *, passed: bool):
    """Copy proof only after this run's replay command completed successfully.

    A failed/blocked command may leave output from an earlier invocation in the
    shared evidence directory. Keep that prior data intact and out of this run.
    """
    if not passed:return
    for name in ['parity.json','plan.ndjson','go-build.log','rust-build.log'] + [
            'parity-'+language+suffix for language in ['python','typescript','go','rust']
            for suffix in ['.jsonl','.stderr']]:
        artifact=source/name
        if artifact.exists():shutil.copyfile(artifact,destination/name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['red', 'green', 'bindings'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    cc = os.environ.get('CC', 'cc')
    sources = [str(p) for p in sorted((ROOT/'src').glob('*.c')) if p.name != 'wasm_mem.c']
    before = fingerprint()
    version = subprocess.run([cc, '--version'], capture_output=True, text=True, check=True).stdout
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    with RunJournal(args.out, heartbeatSeconds=10) as journal:
        journal.record.update(stage=args.stage, baselineCommit=BASELINE, testedHead=head,
                              sourceBefore=before['sha256'], platform=platform.platform(),
                              compiler=version, python=sys.version, environment={
                                  key:os.environ[key] for key in ['CC','PATH','CARGO_HOME','CARGO_TARGET_DIR','CARGO_NET_OFFLINE','WASM_CC','WASM_LD','LD_LIBRARY_PATH','ASAN_OPTIONS','UBSAN_OPTIONS'] if key in os.environ})
        journal.write()
        atomicJson(args.out/'source-files.json', before)
        build = journal.runStep('build-native', [sys.executable,'scripts/build.py'] + ([] if args.stage=='bindings' else ['--native-only']), ROOT)
        checks = journal.runStep('surface-contracts', [sys.executable,'-m','unittest','discover','-s','tests','-p','test_surface_geometry.py','-v'], ROOT)
        if args.stage == 'red':
            output = (args.out/'logs/surface-contracts.log').read_text()
            expected = build['status']=='PASS' and checks['exitCode']==1 and 'Unknown or not-yet-implemented operation' in output and 'SyntaxError' not in output and 'ImportError' not in output
            after = fingerprint()
            journal.finish(False, expectedRed=expected, sourceAfter=after['sha256'],
                           sourceUnchanged=before['sha256']==after['sha256'],
                           reason='New named-surface API is absent from the executed baseline C core.',
                           fourRuntimeVerified=False, fullRC4Qualified=False)
            return 0 if expected else 1
        if args.stage == 'bindings':
            for name, argv in [('clang',[os.environ.get('WASM_CC','clang'),'--version']),
                               ('wasm-ld',[os.environ.get('WASM_LD','wasm-ld'),'--version']),
                               ('node',['node','--version']),('go',['go','version']),
                               ('rust',['rustc','-vV']),('cargo',['cargo','--version']),
                               ('typescript',['tsc','--version'])]:
                journal.runStep('toolchain-'+name,argv,ROOT)
            journal.runStep('typescript-types',['tsc','--noEmit','--strict','--target','es2022',
                            '--module','nodenext','--moduleResolution','nodenext',
                            'examples/typed.ts','examples/selectors.ts','tests/types/selectors.ts',
                            'tests/types/surfaces.ts'],ROOT)
            journal.runStep('typescript-snapshots',['node','--test','bindings/typescript/snapshot-layout.test.mjs'],ROOT)
            journal.runStep('go-contracts',['go','test','-count=1','./...'],ROOT/'bindings/go')
            journal.runStep('rust-contracts',['cargo','test','--offline','--locked','--manifest-path',
                            'bindings/rust/Cargo.toml','--all-targets'],ROOT)
            journal.runStep('rust-doctests',['cargo','test','--offline','--locked','--manifest-path',
                            'bindings/rust/Cargo.toml','--doc'],ROOT)
            replay=journal.runStep('four-runtime-replay',[sys.executable,'scripts/parity.py','--require-rust'],ROOT)
            retainReplayArtifacts(ROOT/'evidence',args.out,passed=replay['status']=='PASS')
            parity=json.loads((args.out/'parity.json').read_text()) if replay['status']=='PASS' else {}
            after=fingerprint()
            passed=before['sha256']==after['sha256'] and all(s['status']=='PASS' for s in journal.record['commands'])
            journal.finish(passed,sourceAfter=after['sha256'],sourceUnchanged=before['sha256']==after['sha256'],
                           fourRuntimeVerified=passed and parity.get('fourRuntimePassed',False),
                           fullRC4Qualified=False,
                           scope='Executed shared C/WASM geometry slice and existing replay in Python, Go, Rust and TypeScript; physical platforms and historical art remain separate gates.')
            return 0 if passed else 1
        common = [cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno',
                  '-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                  '-Iinclude','-Isrc',*sources]
        journal.runStep('geometry-sanitizer-build',[*common,'tests/surface_geometry.c','-o','dist/surface-geometry'],ROOT)
        journal.runStep('geometry-sanitizer-run',[str(ROOT/'dist/surface-geometry')],ROOT)
        journal.runStep('legacy-safety-build',[*common,'tests/safety.c','-o','dist/native-safety'],ROOT)
        journal.runStep('legacy-safety-run',[str(ROOT/'dist/native-safety')],ROOT)
        journal.runStep('python-contracts',[sys.executable,'-m','unittest','discover','-s','tests','-v'],ROOT)
        after=fingerprint()
        passed=before['sha256']==after['sha256'] and all(s['status']=='PASS' for s in journal.record['commands'])
        journal.finish(passed, sourceAfter=after['sha256'],sourceUnchanged=before['sha256']==after['sha256'],
                       fourRuntimeVerified=False,fullRC4Qualified=False,
                       scope='Executed shared C/Python surface slice; other bindings/platforms and full architecture remain separate gates.')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
