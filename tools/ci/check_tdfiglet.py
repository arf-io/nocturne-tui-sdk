"""Run real external TDF scenes in both modes and runtimes; preserve every attempt."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FONT_SHA256 = 'a947aadf36337988a5961846dd0cfe51454d478ed7e2862e12e44f5c80c251af'


def run(binary, font, output, python=sys.executable, node='node', executor=subprocess.run):
    binary, font, output = map(lambda value: Path(value).resolve(), (binary, font, output))
    digest = hashlib.sha256(font.read_bytes()).hexdigest()
    if digest != FONT_SHA256:
        raise ValueError('TDF fixture font digest mismatch')
    output.mkdir(parents=True, exist_ok=False)
    report = {'scope': 'Actual external TDF outline/block/color; isolated/application; native/WASM',
              'fontSha256': digest, 'binarySha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'complete': False, 'passed': False, 'attempts': []}
    receipt = output / 'RESULTS.json'

    def save():
        pending = receipt.with_suffix('.tmp')
        pending.write_text(json.dumps(report, indent=2) + '\n')
        pending.replace(receipt)

    save()
    for subfont in (0, 2, 7):
        destination = output / f'subfont-{subfont}'
        native = [python, str(ROOT / 'native/examples/tdfiglet_scene.py'), '--binary', str(binary),
                  '--font', str(font), '--subfont', str(subfont), '--mode', 'both',
                  '--output', str(destination), 'NOC']
        wasm = [node, str(ROOT / 'native/scripts/check_gallery_cases.mjs'), str(destination / 'cases.json'), str(output / f'wasm-{subfont}.json')]
        native_passed = False
        for runtime, command in [('native', native), ('wasm', wasm)]:
            row = {'subfont': subfont, 'runtime': runtime, 'command': command, 'passed': False}
            if runtime == 'wasm' and not native_passed:
                row['status'] = 'NOT_EXECUTED'
                row['reason'] = 'Native scene did not complete; its exported cases are not accepted inputs'
            else:
                try:
                    with (output / f'{runtime}-{subfont}.log').open('wb') as log:
                        result = executor(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=180)
                    row.update(exitCode=result.returncode, passed=result.returncode == 0,
                               status='PASS' if result.returncode == 0 else 'FAIL')
                except (OSError, subprocess.TimeoutExpired) as error:
                    row.update(status='FAIL', error=str(error), errorType=type(error).__name__)
                if runtime == 'native':
                    native_passed = row['passed']
            report['attempts'].append(row)
            save()
    report['complete'] = len(report['attempts']) == 6
    report['passed'] = report['complete'] and all(row['passed'] for row in report['attempts'])
    save()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--font', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = run(args.binary, args.font, args.output)
    raise SystemExit(0 if result['passed'] else 1)
