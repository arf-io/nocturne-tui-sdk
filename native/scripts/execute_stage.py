#!/usr/bin/env python3
"""Execute ONE bounded delivery stage, with a durable receipt before preflight.

Examples:
  python3 native/scripts/execute_stage.py --repo . --run-dir ../runs/build-001 \
    --name build --timeout 120 --require-artifact native/dist/nocturne_native.wasm \
    -- sh build-native.sh

This command actually launches the stage. delivery_runner.py only inspects one.
Each retry requires a fresh run directory. A receipt is a stage result, not an SDK
release certificate. The caller must independently verify final package contents.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from delivery_runner import RunJournal
from qualify import fingerprint


def fileDigest(path: Path) -> str:
    """Hash a regular explicit input/output in bounded memory; propagate I/O errors."""
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def sourceState(repo: Path) -> dict:
    """Bind Git revision/tree, non-evidence tracked diff, and qualification source.

    The native fingerprint includes sources, tests, bindings, and named tooling.
    It excludes generated native/dist and receipts as the existing gate specifies.
    Returns hashes only; it does not export environment values or credentials.
    Raises ValueError for a non-repository or absent native source.
    """
    if not repo.is_dir() or not (repo/'native/src').is_dir():
        raise ValueError(f'Repository/native source does not exist: {repo}')
    def git(*args):
        result=subprocess.run(['git','-C',str(repo),*args],capture_output=True,timeout=10)
        if result.returncode:
            raise ValueError('Repository Git preflight failed: '+result.stderr.decode(errors='replace'))
        return result.stdout
    return {'commit':git('rev-parse','HEAD').decode().strip(),
            'tree':git('rev-parse','HEAD^{tree}').decode().strip(),
            'nonEvidenceDiffSha256':hashlib.sha256(git('diff','--binary','HEAD','--','.',':(exclude)native/evidence/**')).hexdigest(),
            'qualificationFingerprint':fingerprint(repo/'native')['sha256']}


def main(argv: list[str] | None = None) -> int:
    """Run a stage and verify every declared output. Exit 0 PASS, 2 failure.

    Actual child exit/status and raw combined output remain in EXECUTION.json and
    logs/<name>.log. Missing/corrupt paths never default to an empty success object.
    Source edits during a stage fail the receipt. This is a POSIX-tested supervisor;
    Windows direct-child fallback does not claim job-object descendant containment.
    """
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--name',required=True)
    parser.add_argument('--timeout',type=float,required=True)
    parser.add_argument('--heartbeat',type=float,default=5)
    parser.add_argument('--require-artifact',type=Path,action='append',default=[])
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv)
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    journal=RunJournal(args.run_dir,args.heartbeat)
    try:
        with journal:
            repo=args.repo.resolve()
            journal.record.update(expectedSteps=1,expectedCaseIds=[args.name],
                                  repository=str(repo),platform=platform.platform(),
                                  python=sys.version,artifactRequirements=[str(p) for p in args.require_artifact])
            journal.write()  # Durable BEFORE any source/path/tool preflight.
            if journal.directory.is_relative_to(repo):
                raise ValueError('Run directory must be outside repository')
            before=sourceState(repo)
            journal.record.update(sourceBefore=before,environmentSha256=hashlib.sha256(
                json.dumps(dict(os.environ),sort_keys=True).encode()).hexdigest())
            journal.write()
            item=journal.runStep(args.name,command,repo,timeoutSeconds=args.timeout)
            after=sourceState(repo)
            unchanged=before==after
            journal.record.update(sourceAfter=after,sourceUnchanged=unchanged)
            journal.write()
            if item['status']!='PASS':
                journal.finish(False,reason='Command did not pass')
            else:
                if not unchanged: raise ValueError('Source changed during stage')
                for supplied in args.require_artifact:
                    path=supplied if supplied.is_absolute() else repo/supplied
                    if path.is_symlink() or not path.is_file() or path.stat().st_size==0:
                        raise ValueError(f'Required artifact missing, empty or symlink: {path}')
                    journal.record['artifacts'].append({'path':str(path.resolve()),
                        'bytes':path.stat().st_size,'sha256':fileDigest(path)})
                journal.finish(True)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'FAIL','error':str(error),'receipt':str(journal.receipt)}),flush=True)
        return 2
    print(json.dumps({'status':journal.record['status'],'sourceCommit':journal.record.get('sourceBefore',{}).get('commit'),
                      'receipt':str(journal.receipt),'artifacts':journal.record['artifacts']}),flush=True)
    return 0 if journal.record['passed'] else 2

if __name__=='__main__': raise SystemExit(main())
