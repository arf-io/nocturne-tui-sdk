"""Tests and qualification scripts must not depend on one workstation's paths.

The 2026-10-31 fresh Linux qualification (native/evidence/linux-host-20261031/
qualify-rc2-02) spawned /opt/homebrew/bin/node; other tests hard-coded Homebrew
LLVM, wrote failure records under another user's home directory and read an off-host
reference. External tools resolve from an environment variable, then PATH, as
native/scripts/build.py does; an absent tool is BLOCKED, never a pass.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
SCANNED = (NATIVE / 'tests', NATIVE / 'scripts')
SKIPPED_PARTS = {'fixtures', '__pycache__', 'node_modules'}
WORKSTATION_PATH = re.compile(rb'/opt/homebrew|/usr/local/opt|/Users/')
# The single accepted occurrence: build.py's own compiler discovery probes keg-only
# Homebrew LLVM/LLD directories, only when they exist, before PATH. Tests reuse that
# discovery (toolchain.discover) instead of copying any of these paths.
BUILD_DISCOVERY_LINE = (b"    extras=[Path(p)for p in ['/opt/homebrew/opt/llvm/bin','/opt/homebrew/opt/lld/bin',"
                        b"'/usr/local/opt/llvm/bin','/usr/local/opt/lld/bin']]")
ALLOWED = {('scripts/toolchain.py', BUILD_DISCOVERY_LINE)}


def workstation_paths():
    """Every line under native/tests and native/scripts naming a workstation path."""
    found = []
    for base in SCANNED:
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(NATIVE)
            if path == THIS or not path.is_file() or SKIPPED_PARTS & set(relative.parts):
                continue
            for number, line in enumerate(path.read_bytes().split(b'\n'), 1):
                if WORKSTATION_PATH.search(line) and (relative.as_posix(), line.rstrip(b'\r')) not in ALLOWED:
                    found.append(f'{relative.as_posix()}:{number}: {line.strip()[:160].decode("utf-8", "replace")}')
    return found


def without(environment, *names):
    result = dict(environment)
    for name in names:
        result.pop(name, None)
    return result


def run_python(code, environment, cwd=NATIVE / 'tests'):
    return subprocess.run([sys.executable, '-c', code], cwd=cwd, env=environment, capture_output=True,
                          text=True, timeout=600)


class WorkstationPaths(unittest.TestCase):
    def test_no_checkout_relative_toolchain_layout_in_typescript_tests(self):
        # Fresh extraction fresh-sdk-07: composition-codegen.test.mjs fell back to a macOS-checkout
        # layout (../../toolchains/typescript-5.8.3/.../tsc.js) when the compiler variables were unset.
        hits = []
        for path in sorted((NATIVE / 'bindings/typescript').glob('*.mjs')):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if 'toolchains/typescript-' in line:
                    hits.append(f'{path.relative_to(NATIVE)}:{number}')
        self.assertEqual(hits, [])

    def test_no_workstation_paths_outside_fixtures(self):
        self.assertEqual(workstation_paths(), [])

    def test_allowed_build_discovery_line_is_still_exact(self):
        # Fails if the accepted line changes or disappears, so the allowance cannot drift.
        lines = (NATIVE / 'scripts/toolchain.py').read_bytes().split(b'\n')
        self.assertEqual(lines.count(BUILD_DISCOVERY_LINE), 1)


class HostTools(unittest.TestCase):
    def test_node_resolves_from_NODE_then_PATH(self):
        from native.tests.host_environment import ToolUnavailable, node_executable
        real = shutil.which('node')
        if not real:
            self.fail('BLOCKED: node not available on PATH; this resolution test needs a real node')
        self.assertEqual(node_executable({'NODE': real, 'PATH': ''}), real)
        self.assertEqual(node_executable({'PATH': str(Path(real).parent)}), str(Path(real).parent / 'node'))
        with tempfile.TemporaryDirectory(prefix='nocturne-empty-path-') as empty:
            with self.assertRaisesRegex(ToolUnavailable, r'^BLOCKED: node not available: set NODE or put node on PATH'):
                node_executable({'PATH': empty})
            missing = str(Path(empty) / 'node')
            with self.assertRaisesRegex(ToolUnavailable, r'^BLOCKED: node not available: NODE=') as caught:
                node_executable({'NODE': missing, 'PATH': str(Path(real).parent)})
            self.assertIn(missing, str(caught.exception))
        self.assertTrue(issubclass(ToolUnavailable, AssertionError))

    def test_wasm_tools_are_build_discovery_and_absence_is_blocked(self):
        from native.tests.host_environment import wasm_toolchain
        from native.scripts.toolchain import discover
        tools = discover()
        self.assertEqual(wasm_toolchain(), (tools['wasmCC'], tools['wasmLD']))
        probe = 'from native.tests.host_environment import wasm_toolchain;wasm_toolchain()'
        with tempfile.TemporaryDirectory(prefix='nocturne-empty-path-') as empty:
            # An explicit variable naming a missing file: build discovery checks it before its
            # Homebrew directories and PATH, so this is BLOCKED on every host, macOS included.
            cases = {'clang': dict(without(os.environ, 'WASM_CLANG', 'WASM_LD', 'PYTHONPATH'), WASM_CC=str(Path(empty) / 'clang')),
                     'wasm-ld': dict(without(os.environ, 'WASM_CC', 'WASM_CLANG', 'PYTHONPATH'), WASM_LD=str(Path(empty) / 'wasm-ld'))}
            for tool, environment in cases.items():
                with self.subTest(tool=tool):
                    run = run_python(probe, environment, cwd=NATIVE.parent)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertRegex(run.stderr, r'ToolUnavailable: BLOCKED: ')
                    self.assertIn(tool, run.stderr.splitlines()[-1])
                    self.assertIn('WASM_CC' if tool == 'clang' else 'WASM_LD', run.stderr.splitlines()[-1])

    def test_absent_node_and_clang_fail_the_real_tests_with_blocked_reasons(self):
        # The fresh-host failure mode: a test reaching for a missing tool must fail
        # with an explicit reason, not FileNotFoundError and never a pass or skip.
        cases = [('test_model_gallery_resources.ModelGalleryResources.test_actual_wasm_worker_checks_model_and_bad_resources',
                  'BLOCKED: node not available'),
                 ('test_dynamic_bidi.DynamicBidi.test_import_free_wasm_large_paragraphs', 'BLOCKED: clang')]
        with tempfile.TemporaryDirectory(prefix='nocturne-empty-path-') as empty:
            # Empty PATH removes node on any host (it has no fallback directories); clang needs an
            # explicit missing WASM_CC because build discovery also probes Homebrew LLVM directories.
            environment = dict(without(os.environ, 'NODE', 'WASM_CLANG', 'WASM_LD', 'PYTHONPATH'), PATH=empty,
                               WASM_CC=str(Path(empty) / 'clang'))
            for test, reason in cases:
                with self.subTest(test=test):
                    run = subprocess.run([sys.executable, '-m', 'unittest', '-v', test], cwd=NATIVE / 'tests',
                                         env=environment, capture_output=True, text=True, timeout=900)
                    output = run.stdout + run.stderr
                    self.assertNotEqual(run.returncode, 0, output[-2000:])
                    self.assertIn(reason, output)
                    self.assertIn('FAIL: ', output)
                    self.assertNotIn('FileNotFoundError', output)
                    self.assertNotIn('skipped', output)


class FailureRecords(unittest.TestCase):
    def test_default_and_explicit_failure_directories(self):
        from native.tests.host_environment import failure_directory
        self.assertEqual(failure_directory({}), NATIVE / 'evidence/test-failures')
        self.assertEqual(failure_directory({'NOCTURNE_TEST_FAILURE_DIR': '/explicit/place'}), Path('/explicit/place'))

    def test_record_is_written_whole_into_a_created_directory(self):
        from native.tests.host_environment import failure_record
        with tempfile.TemporaryDirectory(prefix='nocturne-failure-records-') as directory:
            target = Path(directory) / 'nested/records'
            message = failure_record('probe-failure.json', {'actual': [1, 2], 'expected': [1, 3]},
                                     {'NOCTURNE_TEST_FAILURE_DIR': str(target)})
            self.assertEqual(message, f'failure record written: {target / "probe-failure.json"}')
            self.assertEqual(json.loads((target / 'probe-failure.json').read_text()), {'actual': [1, 2], 'expected': [1, 3]})
            self.assertEqual(sorted(p.name for p in target.iterdir()), ['probe-failure.json'])

    def test_unwritable_directory_reports_and_never_masks_the_assertion(self):
        from native.tests.host_environment import failure_record
        with tempfile.TemporaryDirectory(prefix='nocturne-failure-records-') as directory:
            blocker = Path(directory) / 'file'
            blocker.write_text('not a directory')
            message = failure_record('probe.json', {'x': 1}, {'NOCTURNE_TEST_FAILURE_DIR': str(blocker / 'below')})
            self.assertTrue(message.startswith('failure record probe.json not written to '), message)
        with self.assertRaises(ValueError):
            failure_record('../escape.json', {}, {'NOCTURNE_TEST_FAILURE_DIR': '/unused'})


class OriginalReference(unittest.TestCase):
    def test_environment_then_custody_checked_fixture_then_visible_skip(self):
        from native.tests.test_source_material_sampler import ORIGINAL_SHA, ORIGINAL_VARIABLE, original_reference
        with original_reference({}) as fixture_copy:
            self.assertEqual(hashlib.sha256(fixture_copy.read_bytes()).hexdigest(), ORIGINAL_SHA)
            with tempfile.TemporaryDirectory(prefix='nocturne-original-docs-') as directory:
                supplied = Path(directory) / 'supplied.html'
                shutil.copyfile(fixture_copy, supplied)
                with original_reference({ORIGINAL_VARIABLE: str(supplied)}) as path:
                    self.assertEqual(path, supplied)
                with self.assertRaisesRegex(AssertionError, ORIGINAL_VARIABLE):
                    original_reference({ORIGINAL_VARIABLE: str(Path(directory) / 'missing.html')})
                with self.assertRaises(unittest.SkipTest) as skipped:
                    original_reference({}, fixture=Path(directory) / 'absent.html.gz')
        self.assertFalse(fixture_copy.exists())
        reason = str(skipped.exception)
        for required in ('BLOCKED', 'Nocturne-Workbench-Docs.html', ORIGINAL_SHA, ORIGINAL_VARIABLE, 'not substituted'):
            self.assertIn(required, reason)


if __name__ == '__main__':
    unittest.main()
