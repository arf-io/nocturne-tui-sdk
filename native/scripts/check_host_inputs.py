#!/usr/bin/env python3
"""Cross-framework input acceptance using actual dependency hosts and real PTYs.

Terminal reads measure write-to-observed-cell latency, not physical display scanout.
Every case owns the terminal and records exact child restoration before cleanup.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

from dependency_pty import PtyProbe, digest, timestamp, writeJson
from qualify_dependency_hosts import sourceFingerprint, sourceSummary

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ('modal', 'wheel', 'focus', 'prompt-marquee', 'prompt-grow',
             'prompt-vim-inline', 'prompt-vim-full', 'graph', 'unicode', 'latency', 'backpressure')


def observedState(probe: PtyProbe) -> dict:
    """Return the first fixture registration's actual native input state."""
    states = probe.info().get('registeredStates', [])
    return states[0]['states'] if states else {}


def typed(probe: PtyProbe, raw: bytes, expected: str, caret: int | None = None) -> None:
    """Submit real PTY bytes and wait for the exact accepted native document."""
    probe.send(raw)
    probe.wait(lambda: probe.info().get('prompt', {}).get('text') == expected and
               (caret is None or probe.info()['prompt']['caret'] == caret),
               'exact accepted native document ' + repr(expected))


def modal(probe: PtyProbe) -> None:
    typed(probe, b'kept', 'kept', 4)
    camera = probe.info()['camera']
    probe.send(b'\x1bOP')
    probe.wait(lambda: probe.visible('CURRENT NATIVE CONTRACTS') and probe.info().get('modal') == 1,
               'actual help modal visible with native modal ownership')
    # Closing F1 is an in-order processing barrier for preceding real input.
    probe.send(b'X\r\t\x1b[<64;50;10M\x1b[<0;50;17M\x1b[<32;55;17M\x1b[<0;55;17m\x1bOP')
    probe.wait(lambda: not probe.visible('CURRENT NATIVE CONTRACTS') and probe.info().get('modal') == 0,
               'modal closes after queued keyboard/pointer input')
    assert probe.info()['prompt']['text'] == 'kept', 'modal keyboard leaked into accepted document'
    assert probe.info()['camera'] == camera, 'modal pointer/wheel leaked into camera'
    typed(probe, b'Y', 'keptY', 5)


def wheel(probe: PtyProbe) -> None:
    original = probe.info()['camera']
    probe.send(b'\x1b[<64;50;10M')
    probe.wait(lambda: probe.info().get('camera') != original, 'positive SGR wheel reaches camera')
    forward = probe.info()['camera']
    probe.send(b'\x1b[<65;50;10M')
    probe.wait(lambda: probe.info().get('camera') == original, 'negative SGR wheel reverses the same camera axis')
    assert forward != original
    probe.send(b'\x1b[<64;50;24M')
    typed(probe, b'barrier', 'barrier')
    assert probe.info()['camera'] == original, 'wheel over prompt moved camera'


def focus(probe: PtyProbe) -> None:
    probe.send(b'\x1b[<35;10;11M\x1b[<0;10;11M')
    probe.wait(lambda: observedState(probe).get('pressed') is True, 'actual pointer press reaches registered widget')
    probe.send(b'\x1b[O')
    probe.wait(lambda: observedState(probe).get('pressed') is False and
               observedState(probe).get('hover') is False, 'terminal focus loss cancels native press and hover')
    camera = probe.info()['camera']
    probe.send(b'\x1b[<32;55;17M\x1b[<0;55;17m')
    typed(probe, b'barrier', 'barrier')
    assert probe.info()['camera'] == camera, 'drag after focus loss retained camera capture'


def promptMode(probe: PtyProbe, mode: str) -> None:
    assert probe.info()['prompt']['mode'] == {'marquee': 0, 'grow': 1, 'vim-inline': 2, 'vim-full': 3}[mode], 'fixture prompt mode not retained'
    if mode.startswith('vim-'):
        # A freshly reset native fixture starts in normal mode. Do not enqueue
        # an unnecessary Escape: CSI parsers would validly treat immediately
        # following text as an Alt chord before the isolated-Escape deadline.
        probe.wait(lambda: probe.visible('VIM STYLE / NORMAL'), 'actual native Vim normal mode visible')
        typed(probe, b'iabc', 'abc', 3)
        probe.wait(lambda: probe.visible('VIM STYLE / INSERT'), 'actual insert presentation before Escape')
        probe.send(b'\x1b')
        probe.wait(lambda: probe.visible('VIM STYLE / NORMAL'), 'Escape returns to native normal mode')
        typed(probe, b'hiX', 'abXc', 3)
        probe.wait(lambda: probe.visible('VIM STYLE / INSERT'), 'actual insert presentation after edited character')
        probe.send(b'\x1b')
        probe.wait(lambda: probe.visible('VIM STYLE / NORMAL'), 'normal mode after inserted edit')
        typed(probe, b'u', 'abc')
    else:
        typed(probe, b'abc', 'abc', 3)
        typed(probe, b'\x1b[D' + 'é'.encode(), 'abéc', 3)
        typed(probe, b'\x1b[200~ "\\Z\x1b[201~', 'abé "\\Zc', 7)
        typed(probe, b'\x7f', 'abé "\\c', 6)
        if probe.name.startswith('prompt-toolkit-'):
            before = probe.info()['prompt']['text']
            caret = probe.info()['prompt']['caret']
            typed(probe, b'\t', before[:caret] + '    ' + before[caret:], caret + 4)
    assert probe.info()['clock']['timeUs'] == 0, 'held prompt input advanced simulation'


def graph(probe: PtyProbe) -> None:
    def hits():
        for row in reversed(probe.records()):
            if row.get('nodeHits'):
                return row['nodeHits']
        return {}
    probe.wait(lambda: len(hits()) >= 2, 'actual native render exposes two selectable graph nodes')
    for node in ('11', '12'):
        # Opening the inspector can reflow native projection after selection.
        # Resolve the next target from its actual current frame owner.
        x, y = hits()[node]
        probe.send(f'\x1b[<0;{x + 1};{y + 1}M\x1b[<0;{x + 1};{y + 1}m'.encode())
        probe.wait(lambda: probe.info().get('selection') == int(node), 'graph inspector selects node ' + node)
    assert probe.info()['selection'] == 12, 'inspector failed to retarget through existing selection'


def latency(probe: PtyProbe) -> None:
    samples = []
    text = 'latency:'
    typed(probe, text.encode(), text)
    probe.wait(lambda: probe.visible(text), 'unique latency marker is visibly presented before measurement')
    for char in 'ABCDEFGHIJKLMNOPQRSTUVWX':
        text += char
        start = time.perf_counter_ns()
        probe.send(char.encode())
        probe.wait(lambda: probe.visible(text), 'PTY output visibly presents accepted prefix ' + text)
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    probe.wait(lambda: probe.info()['prompt']['text'] == text, 'all measured inputs retained in the native document')
    ordered = sorted(samples)
    percentile = lambda fraction: ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]
    probe.result['latency'] = {'metric': 'PTY write to observed rendered cell', 'unit': 'ms',
                               'samples': samples, 'count': len(samples),
                               'p50': statistics.median(samples), 'p95': percentile(.95),
                               'p99': percentile(.99), 'max': max(samples),
                               'physicalDisplayMeasured': False}


def unicodeProfile(probe: PtyProbe) -> None:
    """Compare known unsupported scalars against visible one-cell replacements."""
    source = 'Aé界e\u0301🙂\u200d\u202eZ'
    expected = 'Aé�e����Z'
    probe.wait(lambda: expected in probe.screen.lines()[6], 'wide, combining, emoji, ZWJ and RLO use one-cell display fallbacks')
    probe.wait(lambda: 'A�B' in probe.screen.lines()[7], 'C1 controls cannot reach terminal control dispatch')
    retained = {entry['id']: entry.get('text') for entry in probe.info().get('widgets', [])}
    assert retained.get(30) == source and retained.get(31) == 'A\u0085B', 'display fallback changed canonical source text'
    probe.result['unicode'] = {'source': source, 'expectedDisplay': expected,
                               'canonicalSourceRetained': True, 'physicalShapingQualified': False}


def backpressure(probe: PtyProbe) -> None:
    # Delay reads from the actual PTY while production animation continues. This
    # creates bounded terminal-output pressure; later exact state/output checks
    # establish acceptance. The delay itself is never counted as a passing check.
    text = 'BURST:' + '0123456789' * 48
    started = time.monotonic()
    probe.send(b'\x1b[200~' + text.encode() + b'\x1b[201~')
    time.sleep(.20)
    probe.wait(lambda: probe.info().get('prompt', {}).get('text') == text,
               'all burst text retained after bounded PTY output congestion')
    typed(probe, b'Z', text + 'Z')
    probe.result['backpressure'] = {'bytesSubmitted': len(text.encode()) + 1,
                                    'withheldReadSeconds': .20,
                                    'secondsToObservedRetention': time.monotonic() - started,
                                    'nativeDocumentExact': True,
                                    'hostQueueOverflowQualified': False}


def fixtureCommands(scenario: str) -> list[dict]:
    commands = [json.loads(line) for line in (ROOT / 'native/tests/fixtures/dependency-hosts.ndjson').read_text().splitlines() if line]
    mode = scenario[len('prompt-'):] if scenario.startswith('prompt-') else 'grow'
    commands.append({'op': 'prompt', 'mode': mode, 'minRows': 2, 'maxRows': 4})
    if scenario == 'graph':
        # Real framework footers reduce the scene to23rows. Author a neutral
        # fixture camera so node11 is not clipped by the inherited artistic tilt.
        commands.extend([{'op': 'camera', 'orthographic': True, 'position': [0, 0, 120], 'span': 160,
                          'yaw': 0, 'pitch': 0, 'roll': 0},
                         {'op': 'node', 'id': 11, 'label': 'Node eleven', 'position': [-50, 20, 0], 'detail': 'first'},
                         {'op': 'node', 'id': 12, 'label': 'Node twelve', 'position': [-50, -20, 0], 'detail': 'second'}])
    if scenario == 'backpressure':
        commands.append({'op': 'emitter', 'id': 1, 'effect': 'weather/autumn-drift', 'count': 512, 'runningTimeMs': 20000})
    if scenario == 'unicode':
        commands.extend([{'op': 'widget', 'id': 30, 'kind': 'text', 'text': 'Aé界e\u0301🙂\u200d\u202eZ', 'x': 4, 'y': 6, 'width': 40, 'height': 1, 'alpha': 0},
                         {'op': 'widget', 'id': 31, 'kind': 'text', 'text': 'A\u0085B', 'x': 4, 'y': 7, 'width': 40, 'height': 1, 'alpha': 0}])
    return commands


def runCase(host: str, scenario: str, binary: Path | None, out: Path, timeout: float) -> dict:
    name = host + '-' + scenario
    fixture = out / (name + '.fixture.ndjson')
    fixture.write_text(''.join(json.dumps(command) + '\n' for command in fixtureCommands(scenario)))
    if host == 'terminal-kit':
        argv = ['node', str(ROOT / 'native/hosts/terminal-kit/qualification.mjs')]
    elif host == 'prompt-toolkit':
        argv = [sys.executable, str(ROOT / 'native/hosts/python/qualification.py')]
    elif host == 'bubbletea':
        argv = [str(binary)]
    else:
        argv = [str(binary), '--trace', str(out / (name + '.trace.jsonl'))]
        if scenario != 'backpressure':
            argv.append('--hold')
    env = dict(os.environ, NOCTURNE_TEST_SCENARIO=scenario, NOCTURNE_TEST_FIXTURE=str(fixture))
    probe = PtyProbe(argv, ROOT, env, out, name, timeout)
    try:
        # The full-screen prompt intentionally covers the fixture title widget.
        # The native top bar remains visible in all four prompt presentations.
        probe.waitReady('NOCTURNE')
        probe.wait(lambda: bool(probe.info()), 'actual native state trace')
        if scenario.startswith('prompt-'):
            promptMode(probe, scenario[len('prompt-'):])
        else:
            {'modal': modal, 'wheel': wheel, 'focus': focus, 'graph': graph, 'unicode': unicodeProfile,
             'latency': latency, 'backpressure': backpressure}[scenario](probe)
        probe.send(b'\x11')
        probe.finish(0)
    except BaseException as error:
        probe.result.update(status='TIMEOUT' if isinstance(error, TimeoutError) else 'FAIL',
                            accepted=False, reason=repr(error))
        if isinstance(error, KeyboardInterrupt):
            probe.result['status'] = 'INTERRUPTED'
            raise
    finally:
        probe.close()
    print(name, probe.result['status'], probe.result.get('reason', ''), flush=True)
    return probe.result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=['terminal-kit', 'bubbletea', 'prompt-toolkit', 'ratatui'])
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--scenarios', nargs='+', choices=SCENARIOS, default=list(SCENARIOS))
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=20)
    args = parser.parse_args()
    out = args.evidence_dir.resolve()
    if out.exists() or out.is_relative_to(ROOT):
        parser.error('new external evidence directory required')
    if args.host in ('bubbletea', 'ratatui') and (not args.binary or not args.binary.is_file()):
        parser.error('actual built host fixture binary is required')
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('finite positive timeout required')
    out.mkdir(parents=True)
    before = sourceSummary(sourceFingerprint())
    writeJson(out / 'SOURCE-BEFORE.json', before)
    identity = {}
    for name, argv in [('python', [sys.executable, '--version']),
                       *([('node', ['node', '--version'])] if args.host == 'terminal-kit' else []),
                       *([('go', ['go', 'version'])] if args.host == 'bubbletea' else []),
                       *([('rustc', [os.environ.get('RUSTC', 'rustc'), '-Vv'])] if args.host == 'ratatui' else [])]:
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
            identity[name] = {'argv': argv, 'exitCode': result.returncode,
                              'stdout': result.stdout, 'stderr': result.stderr}
        except OSError as error:
            identity[name] = {'argv': argv, 'status': 'unavailable', 'reason': repr(error)}
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    report = {'schema': 'nocturne.host-input.qualification.v1', 'startedAt': timestamp(),
              'host': args.host, 'status': 'RUNNING', 'fullRC4Qualified': False,
              'platform': platform.platform(), 'runtimeIdentity': identity,
              'sourceHead': git.stdout.strip() if git.returncode == 0 else None,
              'sourceBefore': before['sha256'], 'sourceManifest': 'SOURCE-BEFORE.json',
              'sourceManifestSha256': digest(out / 'SOURCE-BEFORE.json'),
              'binarySha256': digest(args.binary) if args.binary else None,
              'scenarios': args.scenarios, 'cases': []}
    path = out / 'QUALIFICATION.json'
    writeJson(path, report)
    try:
        for scenario in args.scenarios:
            report['cases'].append(runCase(args.host, scenario, args.binary, out, args.timeout))
            writeJson(path, report)
        report['status'] = 'PASS' if all(case['status'] == 'PASS' and case['accepted'] for case in report['cases']) else 'FAIL'
    except BaseException as error:
        report.update(status='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'FAIL', reason=repr(error))
    finally:
        after = sourceSummary(sourceFingerprint())
        report.update(finishedAt=timestamp(), sourceAfter=after['sha256'], sourceUnchanged=before['sha256'] == after['sha256'])
        if not report['sourceUnchanged']:
            report['status'] = 'FAIL'
        writeJson(path, report)
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
