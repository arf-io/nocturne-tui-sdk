"""T13: the command-path build switches (native/docs/TDD-STATE-COPY-ELIMINATION-20261102.md section 5.6).

build.py keeps two environment switches beside NOCTURNE_COVERAGE: NOCTURNE_COMMAND_FASTPATH (0..3) and
NOCTURNE_SHADOW_CHECK (1, reject, inject). Any other value must stop build.py before it compiles anything, and
internal.h must hold the one default of the command-path limit, which is the rollback lever.

Every child process has both switches removed from its environment unless the case sets one, so a developer's
shell never decides a verdict here.
"""
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import json
import itertools
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
SWITCHES = ('NOCTURNE_COMMAND_FASTPATH', 'NOCTURNE_SHADOW_CHECK')
# What build.py needs to start: its scripts, the sources, the headers and the freestanding WASM headers.
BUILD_INPUTS = ('scripts', 'src', 'include', 'freestanding')


def child_environment(**overrides):
    environment = {k: v for k, v in os.environ.items() if k not in SWITCHES and k != 'NOCTURNE_COVERAGE'}
    environment.update(overrides)
    return environment


def copy_build_inputs(target):
    for name in BUILD_INPUTS:
        shutil.copytree(NATIVE / name, target / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


def run_until_first_compile(native, environment, deadline=120):
    """Run build.py --native-only; stop it at its first compile line ('+ <argv>'), which build.py prints before
    every compiler run. Returns (exit code, stdout lines, stderr, whether a compile had begun)."""
    child = subprocess.Popen([sys.executable, 'scripts/build.py', '--native-only'], cwd=native, env=environment,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    lines, compiled = [], False
    try:
        for line in child.stdout:
            lines.append(line.rstrip('\n'))
            if line.startswith('+ '):
                compiled = True
                os.killpg(child.pid, signal.SIGKILL)  # the compiler too, not only build.py
                break
        _, stderr = child.communicate(timeout=deadline)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        _, stderr = child.communicate()
        raise AssertionError('build.py neither compiled nor exited within %d s' % deadline)
    return child.returncode, lines, stderr, compiled


class RejectsUnknownSwitchValues(unittest.TestCase):
    """T13 part (1): a bad value exits nonzero before any compile, and the message names the variable."""

    BAD = (('NOCTURNE_COMMAND_FASTPATH', '4'), ('NOCTURNE_COMMAND_FASTPATH', 'x'), ('NOCTURNE_SHADOW_CHECK', '2'))

    def test_bad_values_stop_build_py_before_compiling(self):
        for name, value in self.BAD:
            with self.subTest(variable=name, value=value), tempfile.TemporaryDirectory(prefix='t13-') as temporary:
                native = Path(temporary) / 'native'
                copy_build_inputs(native)
                code, lines, stderr, compiled = run_until_first_compile(native, child_environment(**{name: value}))
                if compiled:
                    self.fail('build.py began compiling with %s=%r: %s' % (name, value, lines[-1][:200]))
                self.assertNotEqual(code, 0, '%s=%r was accepted' % (name, value))
                self.assertIn(name, stderr + '\n'.join(lines), 'the refusal does not name the variable')
                self.assertFalse((native / 'dist' / 'libnocturne_native.so').exists())
                self.assertFalse((native / 'dist' / 'build-switches.json').exists(), 'a failed build left a record')


class InternalHeaderDefault(unittest.TestCase):
    """T13 part (3): internal.h holds exactly one NR_COMMAND_FASTPATH default, and its value is 0, 1 or 3."""

    def test_single_default_block(self):
        text = (NATIVE / 'src' / 'internal.h').read_text()
        blocks = re.findall(r'^#ifndef NR_COMMAND_FASTPATH\n#define NR_COMMAND_FASTPATH (\S+)\n#endif$', text, re.M)
        self.assertEqual(len(blocks), 1, 'expected exactly one #ifndef/#define/#endif default block')
        self.assertEqual(len(re.findall(r'^\s*#\s*define\s+NR_COMMAND_FASTPATH\b', text, re.M)), 1,
                         'NR_COMMAND_FASTPATH is defined outside its default block')
        self.assertIn(blocks[0], {'0', '1', '3'})
        for source in sorted((NATIVE / 'src').glob('*.[ch]')):
            if source.name != 'internal.h':
                self.assertNotRegex(source.read_text(errors='replace'), r'(?m)^\s*#\s*define\s+NR_COMMAND_FASTPATH\b',
                                    '%s defines NR_COMMAND_FASTPATH' % source.name)


def build_switches_module():
    if str(NATIVE / 'scripts') not in sys.path:
        sys.path.insert(0, str(NATIVE / 'scripts'))
    import build_switches
    return build_switches


class BuildSwitchRecord(unittest.TestCase):
    """T13 part (2): the record of the applied switches (dist/build-switches.json), null for an unset switch."""

    KEYS = {'schema', 'NOCTURNE_COMMAND_FASTPATH', 'NOCTURNE_SHADOW_CHECK', 'NOCTURNE_COVERAGE', 'defines', 'native', 'wasm'}
    SHADOW = {None: [], '1': ['-DNR_SHADOW_CHECK=1'], 'reject': ['-DNR_SHADOW_CHECK=1', '-DNR_SHADOW_REJECT_AT_COMMIT=1'],
              'inject': ['-DNR_SHADOW_CHECK=1', '-DNR_SHADOW_INJECT_K=8']}

    def test_every_accepted_combination(self):
        module = build_switches_module()
        for fastpath, shadow, coverage, wasm in itertools.product((None, '0', '1', '2', '3'), self.SHADOW, (None, '1'), (True, False)):
            environ = {k: v for k, v in (('NOCTURNE_COMMAND_FASTPATH', fastpath), ('NOCTURNE_SHADOW_CHECK', shadow),
                                          ('NOCTURNE_COVERAGE', coverage)) if v is not None}
            with self.subTest(**{k: v for k, v in environ.items()}, wasm=wasm):
                record = module.record(environ, wasm=wasm)
                self.assertEqual(set(record), self.KEYS)
                self.assertEqual(record['schema'], 'nocturne.native.build-switches.v1')
                self.assertEqual(record['NOCTURNE_COMMAND_FASTPATH'], fastpath)
                self.assertEqual(record['NOCTURNE_SHADOW_CHECK'], shadow)
                self.assertEqual(record['NOCTURNE_COVERAGE'], coverage)
                self.assertEqual(record['defines'], ([] if fastpath is None else ['-DNR_COMMAND_FASTPATH=' + fastpath]) + self.SHADOW[shadow])
                self.assertIs(record['native'], True)
                self.assertIs(record['wasm'], wasm)
                self.assertEqual(json.loads(json.dumps(record)), record)

    def test_unset_switches_record_null(self):
        record = build_switches_module().record({'UNRELATED': 'x'}, wasm=True)
        self.assertIsNone(record['NOCTURNE_COMMAND_FASTPATH'])
        self.assertIsNone(record['NOCTURNE_SHADOW_CHECK'])
        self.assertIsNone(record['NOCTURNE_COVERAGE'])
        self.assertEqual(record['defines'], [])

    def test_atomic_write_replaces_whole_file(self):
        module = build_switches_module()
        with tempfile.TemporaryDirectory(prefix='t13-') as temporary:
            target = Path(temporary) / 'build-switches.json'
            target.write_text('stale')
            module.write_record(target, module.record({}, wasm=False))
            self.assertEqual(json.loads(target.read_text())['wasm'], False)
            self.assertEqual(sorted(p.name for p in Path(temporary).iterdir()), ['build-switches.json'], 'a temporary file remained')

    def test_old_record_is_removed_before_compiling_and_a_refused_build_leaves_none(self):
        for name, value in ((None, None), ('NOCTURNE_COMMAND_FASTPATH', 'x')):
            with self.subTest(variable=name, value=value), tempfile.TemporaryDirectory(prefix='t13-') as temporary:
                native = Path(temporary) / 'native'
                copy_build_inputs(native)
                (native / 'dist').mkdir()
                (native / 'dist' / 'build-switches.json').write_text('{"stale":true}')
                code, lines, stderr, compiled = run_until_first_compile(native, child_environment(**({name: value} if name else {})))
                self.assertEqual(compiled, name is None)
                self.assertFalse((native / 'dist' / 'build-switches.json').exists(),
                                 'the old record survived until the first compile' if compiled else 'a refused build left a record')


def scripts_module(name):
    if str(NATIVE / 'scripts') not in sys.path:
        sys.path.insert(0, str(NATIVE / 'scripts'))
    return __import__(name)


class StrictQualificationRefusesShadowBuilds(unittest.TestCase):
    """T13 part (4): qualify.py --strict exits nonzero before planning, under --list too, while
    NOCTURNE_SHADOW_CHECK is set; without it, --strict --list exits 0. Plus the receipt rule of step 1.3d: under
    --strict a missing build-switch record, or one with a shadow switch, fails the run."""

    def list_plan(self, **overrides):
        return subprocess.run([sys.executable, 'scripts/qualify.py', '--strict', '--list'], cwd=NATIVE,
                              env=child_environment(**overrides), capture_output=True, text=True, timeout=300)

    def test_shadow_switch_refused(self):
        for value in ('1', 'reject', 'inject', ''):
            with self.subTest(value=value):
                result = self.list_plan(NOCTURNE_SHADOW_CHECK=value)
                self.assertNotEqual(result.returncode, 0, 'strict qualification planned with NOCTURNE_SHADOW_CHECK=%r' % value)
                self.assertIn('NOCTURNE_SHADOW_CHECK', result.stderr)
                self.assertEqual(result.stdout, '', 'a plan was printed before the refusal')

    def test_without_the_switch_strict_list_succeeds(self):
        result = self.list_plan()
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertEqual(json.loads(result.stdout)[0]['id'], 'build')

    def test_build_outputs_retain_the_record(self):
        qualify = scripts_module('qualify')
        plan = qualify.checkpointPlan([('build', [sys.executable, 'scripts/build.py'])], 900)
        self.assertIn(str(NATIVE / 'dist' / 'build-switches.json'), plan[0]['artifacts'])

    def test_strict_receipt_rule(self):
        problem = scripts_module('qualify').buildSwitchesProblem
        ordinary = scripts_module('build_switches').record({}, wasm=True)
        shadow = scripts_module('build_switches').record({'NOCTURNE_SHADOW_CHECK': 'inject'}, wasm=True)
        self.assertIsNone(problem(ordinary, strict=True))
        self.assertIsNone(problem(scripts_module('build_switches').record({'NOCTURNE_COMMAND_FASTPATH': '1'}, wasm=True), strict=True))
        self.assertIn('missing', problem(None, strict=True))
        self.assertIn('NOCTURNE_SHADOW_CHECK', problem(shadow, strict=True))
        self.assertIn('schema', problem({'NOCTURNE_SHADOW_CHECK': None}, strict=True))
        self.assertIsNone(problem(None, strict=False))
        self.assertIsNone(problem(shadow, strict=False))


class ShadowExportsFlagged(unittest.TestCase):
    """T13 part (5): dependencies.shadowExports flags every nrShadow* name. A pure function: nothing here reads dist/."""

    def test_flags_shadow_names_only(self):
        shadow_exports = scripts_module('dependencies').shadowExports
        clean = ['nrInit', 'nrCommand', 'nrRender', 'nrContextSize', 'memory', '__heap_base', 'nrShado', 'xnrShadowAnyFailure']
        self.assertEqual(shadow_exports(clean), [])
        self.assertEqual(shadow_exports(clean + ['nrShadowAnyFailure']), ['nrShadowAnyFailure'])
        self.assertEqual(shadow_exports(['nrShadowFailure', 'nrInit', 'nrShadowAnyFailure']), ['nrShadowAnyFailure', 'nrShadowFailure'])


if __name__ == '__main__':
    unittest.main()
