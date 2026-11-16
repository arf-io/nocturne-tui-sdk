#!/usr/bin/env python3
"""Execute every authored gallery case; retain failures and partial observations."""
from pathlib import Path
import hashlib
import os
from concurrent.futures import ProcessPoolExecutor
from collections import deque
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples'))
from delivery_runner import atomicJson


def _execute_case(arguments):
    case, executor = arguments
    started = time.monotonic()
    try:
        rows = executor([case])
        if (len(rows) != 1 or rows[0].get('id') != case['id']
                or rows[0].get('renderPure') is not True
                or rows[0].get('partitionReplay') is not True):
            raise ValueError('Gallery execution did not establish case identity, purity and replay')
        row = {'id': case['id'], 'status': 'PASS', 'observations': rows[0]}
    except Exception as error:
        row = {'id': case['id'], 'status': 'FAIL',
               'errorType': type(error).__name__, 'error': str(error)}
    row['seconds'] = time.monotonic() - started
    row['workerPid'] = os.getpid()
    return row


def run_cases(cases, executor, output, identity, *, workers=1):
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 4:
        raise ValueError('Gallery worker count must be an integer from1 to4')
    ids = [case['id'] for case in cases]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Gallery requires a nonempty unique case inventory')
    report = {**identity, 'status': 'RUNNING', 'complete': False, 'passed': False,
              'expectedCaseIds': ids, 'cases': [], 'executionWorkers': min(workers, len(cases))}
    atomicJson(output, report)
    pool = ProcessPoolExecutor(max_workers=report['executionWorkers']) if workers > 1 else None
    try:
        arguments = [(case, executor) for case in cases]
        def bounded_rows():
            pending=deque();source=iter(arguments)
            for _ in range(min(len(arguments), 2*report['executionWorkers'])):
                pending.append(pool.submit(_execute_case,next(source)))
            while pending:
                row=pending.popleft().result()
                try:argument=next(source)
                except StopIteration:argument=None
                if argument is not None:pending.append(pool.submit(_execute_case,argument))
                yield row
        rows = bounded_rows() if pool else map(_execute_case, arguments)
        for expected, row in zip(ids, rows):
            if row.get('id') != expected:
                raise ValueError('Worker result does not match its declared case')
            report['cases'].append(row)
            atomicJson(output, report)
            print(f"{expected}: {row['status']} ({row['seconds']:.3f}s)", flush=True)
    except BaseException as error:
        report.update(status='FAIL', complete=False, passed=False,
                      executionErrorType=type(error).__name__, executionError=str(error))
        atomicJson(output, report)
        # Python3.12 has no public terminate_workers; retain the owned process
        # handles before shutting down the executor, and join every worker.
        if pool:
            for child in list((getattr(pool,'_processes',None) or {}).values()):
                if child.is_alive():child.terminate()
        raise
    finally:
        if pool: pool.shutdown(wait=True, cancel_futures=True)
    report['complete'] = len(report['cases']) == len(ids)
    report['passed'] = report['complete'] and all(row['status'] == 'PASS' for row in report['cases'])
    report['status'] = 'PASS' if report['passed'] else 'FAIL'
    report['workerPids'] = sorted({row['workerPid'] for row in report['cases']})
    atomicJson(output, report)
    return report


def main():
    from gallery_cases import build_cases, execute
    from qualify import fingerprint
    library = ROOT / 'dist' / ('libnocturne_native.dylib' if sys.platform == 'darwin' else 'libnocturne_native.so')
    before = fingerprint()['sha256']
    output = ROOT / 'evidence/gallery-studies.json'
    cases = build_cases()
    atomicJson(ROOT / 'evidence/gallery-study-cases.json', cases)
    report = run_cases(cases, execute, output, {
        'schema': 'nocturne.gallery-studies.v1',
        'scope': 'Every authored isolated/application study; option completeness and artistic approval remain separate',
        'sourceBefore': before,
        'librarySha256': hashlib.sha256(library.read_bytes()).hexdigest(),
    }, workers=int(os.environ.get('NOCTURNE_GALLERY_WORKERS', '4')))
    report['sourceAfter'] = fingerprint()['sha256']
    report['sourceUnchanged'] = report['sourceAfter'] == before
    report['libraryAfterSha256'] = hashlib.sha256(library.read_bytes()).hexdigest()
    report['libraryUnchanged'] = report['libraryAfterSha256'] == report['librarySha256']
    if not report['sourceUnchanged'] or not report['libraryUnchanged']:
        report.update(passed=False, status='FAIL')
    atomicJson(output, report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
