#!/usr/bin/env python3
"""Run the transaction differential (native/docs/TRANSACTIONS.md, "Verification") over every generated stream.

  run_transaction_differential.py --reference REF.dylib --candidate CAND.dylib [--jobs N] [--frames N]
                                  [--snapshots N] [--streams DIR] [--only name,...]

Regenerates the streams (gen_transaction_streams.py), compiles transaction_differential.c, copies both libraries to
distinct temporary paths (so dlopen loads two images even when they are the same file), runs one driver per stream
in parallel and prints each driver's summary line, then a total. Exit status 0 only when every stream ran with
zero divergences."""
import argparse, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 4)
    parser.add_argument('--frames', default='1')
    parser.add_argument('--snapshots', default='1')
    parser.add_argument('--streams', default=str(HERE / 'fixtures' / 'transactions' / 'streams'))
    parser.add_argument('--only', default='')
    parser.add_argument('--no-generate', action='store_true')
    args = parser.parse_args()
    streams = Path(args.streams)
    if not args.no_generate:
        subprocess.run([sys.executable, str(HERE / 'gen_transaction_streams.py'), '--out', str(streams)], check=True)
    files = sorted(streams.glob('*.jsonl'))
    if args.only:
        wanted = set(args.only.split(','))
        files = [f for f in files if f.stem in wanted or f.name in wanted]
    work = Path(tempfile.mkdtemp(prefix='transaction-differential.'))
    try:
        cc = os.environ.get('CC', 'cc')
        driver = work / 'transaction-differential'
        subprocess.run([cc, '-std=c11', '-O2', '-Wall', '-Wextra', str(HERE / 'transaction_differential.c'), '-o', str(driver)], check=True)
        reference, candidate = work / 'reference.lib', work / 'candidate.lib'
        shutil.copyfile(args.reference, reference)
        shutil.copyfile(args.candidate, candidate)

        def run(stream):
            # longrun streams compare only at their {"frame":...} checkpoints (2 s and 30 s).
            frames, snapshots = ('0', '0') if stream.name.startswith('longrun') else (args.frames, args.snapshots)
            p = subprocess.run([str(driver), str(reference), str(candidate), '--frames', frames, '--snapshots', snapshots,
                                '--quiet', str(stream)], capture_output=True, text=True)
            return stream.name, p.returncode, p.stdout, p.stderr

        totals = [0, 0, 0, 0, 0, 0]
        failed = False
        with ThreadPoolExecutor(args.jobs) as pool:
            for name, code, out, err in pool.map(run, files):
                summary = out.strip().splitlines()[-1] if out.strip() else '(no summary)'
                print('%-18s %s' % (name, summary))
                if err.strip():
                    print('\n'.join('    ' + line for line in err.strip().splitlines()[:60]))
                m = re.search(r'(\d+) entries, (\d+) commands \((\d+) rejected\), (\d+) snapshots and (\d+) frames compared \(\d+ checkpoints\), (\d+) divergences', summary)
                if not m or code not in (0, 1):
                    failed = True
                    continue
                for i in range(6):
                    totals[i] += int(m.group(i + 1))
                failed |= code != 0
        print('TOTAL: %d entries, %d commands (%d rejected), %d snapshots and %d frames compared, %d divergences' % tuple(totals))
        return 1 if failed or totals[5] else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
