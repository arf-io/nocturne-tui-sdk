"""Modules importing ``native.`` must import from any working directory, without PYTHONPATH.

The 2026-10-31 fresh Linux qualification (native/evidence/linux-host-20261031/
qualify-rc2-02) failed five rc2-native modules with "No module named 'native'":
the repository root reached sys.path only through the caller's environment.
These tests run real interpreters in the receipt's condition (cwd native/tests,
PYTHONPATH absent) and in the other supported invocation modes.
"""
import concurrent.futures
import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
SPEC = importlib.util.spec_from_file_location('repository_root_bootstrap', NATIVE / 'scripts/repository_root_bootstrap.py')
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)
RECEIPT_MODULES = ('test_camera_controls', 'test_scene_art_clock', 'test_camera_anchor_default',
                   'test_braille_floor_regressions', 'test_rc2_native_display_copy')


def environment_without_pythonpath():
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    return environment


def python(code, cwd, environment=None):
    return subprocess.run([sys.executable, '-c', code], cwd=cwd, capture_output=True, text=True, timeout=600,
                          env=environment_without_pythonpath() if environment is None else environment)


def run_generator(*arguments):
    """The generator as a shell, CI or the documentation runs it: a command line in its own interpreter."""
    # Plain argparse text on every Python: 3.14 can colorize its messages.
    environment = dict(environment_without_pythonpath(), NO_COLOR='1', PYTHON_COLORS='0')
    environment.pop('FORCE_COLOR', None)
    return subprocess.run([sys.executable, GENERATOR.__file__, *arguments], capture_output=True, text=True,
                          timeout=600, env=environment)


class RepositoryRootBootstrap(unittest.TestCase):
    def test_every_module_importing_native_carries_the_uniform_bootstrap(self):
        names = {path.stem for path in GENERATOR.candidates()}
        self.assertTrue(set(RECEIPT_MODULES) <= names, sorted(set(RECEIPT_MODULES) - names))
        self.assertEqual([path.name for path in GENERATOR.problems()], [])
        for path in GENERATOR.candidates():
            with self.subTest(module=path.name):
                self.assertEqual(path.read_text(encoding='utf-8').count(GENERATOR.BOOTSTRAP), 1)

    def test_receipt_modules_import_from_tests_directory_without_pythonpath(self):
        for name in RECEIPT_MODULES:
            with self.subTest(module=name):
                run = python(f'import {name}', NATIVE / 'tests')
                self.assertEqual(run.returncode, 0, run.stderr[-3000:])

    def test_every_test_module_importing_native_imports_alone_without_pythonpath(self):
        # Each module in its own interpreter: no earlier module may have extended sys.path.
        names = [path.stem for path in GENERATOR.candidates() if path.stem.startswith('test_')]
        with concurrent.futures.ThreadPoolExecutor(min(8, os.cpu_count() or 1)) as pool:
            runs = dict(zip(names, pool.map(lambda name: python(f'import {name}', NATIVE / 'tests'), names)))
        failed = {name: run.stderr.strip().splitlines()[-1:] for name, run in runs.items() if run.returncode}
        self.assertEqual(failed, {})

    def test_one_module_imports_in_three_invocation_modes(self):
        module = NATIVE / 'tests/test_camera_controls.py'
        probe = "import sys;m=sys.modules['native.tests.test_camera_anchor_default'];print(m.__file__)"
        with tempfile.TemporaryDirectory(prefix='nocturne-bootstrap-cwd-') as elsewhere:
            modes = [('tests directory', 'import test_camera_controls;' + probe, NATIVE / 'tests'),
                     ('repository root', 'import native.tests.test_camera_controls;' + probe, REPOSITORY),
                     ('unrelated directory', f"import runpy;runpy.run_path({str(module)!r},run_name='probe');" + probe,
                      Path(elsewhere))]
            for label, code, cwd in modes:
                with self.subTest(mode=label):
                    run = python(code, cwd)
                    self.assertEqual(run.returncode, 0, run.stderr[-3000:])
                    self.assertEqual(Path(run.stdout.strip()), NATIVE / 'tests/test_camera_anchor_default.py')

    def test_a_different_checkout_on_pythonpath_does_not_supply_this_checkouts_modules(self):
        with tempfile.TemporaryDirectory(prefix='nocturne-decoy-checkout-') as decoy:
            tests = Path(decoy) / 'native/tests'
            tests.mkdir(parents=True)
            (tests / 'test_camera_anchor_default.py').write_text("raise RuntimeError('decoy checkout imported')\n")
            environment = environment_without_pythonpath()
            environment['PYTHONPATH'] = decoy
            run = python("import test_camera_controls,sys;print(sys.modules['native.tests.test_camera_anchor_default'].__file__)",
                         NATIVE / 'tests', environment)
            self.assertEqual(run.returncode, 0, run.stderr[-3000:])
            self.assertEqual(Path(run.stdout.strip()), NATIVE / 'tests/test_camera_anchor_default.py')


class BootstrapGenerator(unittest.TestCase):
    def apply(self, source):
        return GENERATOR.bootstrapped(textwrap.dedent(source), Path('probe.py'))

    def test_position_follows_docstring_and_future_imports(self):
        result = self.apply('''\
            """Doc string with a line separator."""
            from __future__ import annotations
            # comment
            import os
            def run():
                from native.tests.x import y
            ''').split('\n')
        self.assertEqual(result[2], '# comment')
        self.assertEqual(result[3], GENERATOR.BOOTSTRAP)
        self.assertEqual(result[4], 'import os')

    def test_modules_without_docstring_and_with_decorators(self):
        result = self.apply('''\
            #!/usr/bin/env python3
            @decorator
            def f():
                import native.bindings
            ''').split('\n')
        self.assertEqual(result[:3], ['#!/usr/bin/env python3', GENERATOR.BOOTSTRAP, '@decorator'])

    def test_idempotent_and_moves_misplaced_copy(self):
        once = self.apply('"""Doc."""\nimport native.x\n')
        self.assertEqual(GENERATOR.bootstrapped(once, Path('probe.py')), once)
        misplaced = '"""Doc."""\nimport native.x\n' + GENERATOR.BOOTSTRAP + '\n'
        self.assertEqual(GENERATOR.bootstrapped(misplaced, Path('probe.py')), once)
        self.assertEqual(self.apply('"""Doc."""\r\nimport native.x\r\n'), once.replace('\n', '\r\n'))

    def test_shared_line_is_refused_not_guessed(self):
        with self.assertRaises(ValueError):
            self.apply('"""Doc.""";import native.x\n')

    def test_write_is_atomic_mode_preserving_and_only_touches_importers(self):
        with tempfile.TemporaryDirectory(prefix='nocturne-bootstrap-write-') as directory:
            folder = Path(directory)
            importer, other = folder / 'test_importer.py', folder / 'test_other.py'
            importer.write_text('"""Doc."""\nimport json\ndef f():\n    from native.tests import x\n')
            other.write_text('"""Doc."""\nimport json\n')
            importer.chmod(0o755)
            self.assertEqual(GENERATOR.main(['--tests', directory]), 1)
            self.assertEqual(GENERATOR.main(['--tests', directory, '--write']), 0)
            self.assertEqual(GENERATOR.main(['--tests', directory]), 0)
            self.assertEqual(importer.read_text().split('\n')[1], GENERATOR.BOOTSTRAP)
            self.assertEqual(other.read_text(), '"""Doc."""\nimport json\n')
            self.assertEqual(stat.S_IMODE(importer.stat().st_mode), 0o755)
            self.assertEqual(sorted(p.name for p in folder.iterdir()), ['test_importer.py', 'test_other.py'])


class BootstrapCheckMode(unittest.TestCase):
    """``--check`` is the documented, explicit name of the default read-only mode; ``--write`` excludes it."""
    IMPORTER = '"""Doc."""\nimport json\ndef f():\n    from native.tests import x\n'
    DRIFT_REPORT = ['missing or misplaced bootstrap: test_missing.py',
                    '1 of 2 modules importing native. need the bootstrap']
    CLEAN_REPORT = ['0 of 2 modules importing native. need the bootstrap']

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='nocturne-bootstrap-check-')
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        (self.folder / 'test_missing.py').write_text(self.IMPORTER)
        (self.folder / 'test_carrying.py').write_text(GENERATOR.bootstrapped(self.IMPORTER, Path('probe.py')))
        (self.folder / 'test_other.py').write_text('"""Doc."""\nimport json\n')
        (self.folder / 'test_missing.py').chmod(0o755)

    def snapshot(self):
        """Every entry with bytes, mode and mtime: a rewrite or a leftover staging file shows."""
        return {path.name: (path.read_bytes(), stat.S_IMODE(path.stat().st_mode), path.stat().st_mtime_ns)
                for path in sorted(self.folder.iterdir())}

    def run_in_folder(self, *flags):
        return run_generator(*flags, '--tests', str(self.folder))

    def test_check_names_the_module_lacking_the_bootstrap_and_writes_nothing(self):
        before = self.snapshot()
        run = self.run_in_folder('--check')
        # Exactly 1 is the drift status; 2 would be argparse refusing the flag.
        self.assertEqual((run.returncode, run.stderr), (1, ''))
        self.assertEqual(run.stdout.splitlines(), self.DRIFT_REPORT)
        self.assertEqual(self.snapshot(), before)

    def test_check_on_a_clean_tree_exits_zero_and_changes_nothing(self):
        self.assertEqual(self.run_in_folder('--write').returncode, 0)
        before = self.snapshot()
        run = self.run_in_folder('--check')
        self.assertEqual((run.returncode, run.stderr), (0, ''))
        self.assertEqual(run.stdout.splitlines(), self.CLEAN_REPORT)
        self.assertEqual(self.snapshot(), before)

    def test_check_passes_on_the_committed_tests_directory(self):
        run = run_generator('--check')
        modules = len(GENERATOR.candidates())
        self.assertEqual((run.returncode, run.stderr), (0, ''))
        self.assertEqual(run.stdout.splitlines(), [f'0 of {modules} modules importing native. need the bootstrap'])

    def test_check_and_write_together_are_rejected_in_either_order_and_write_nothing(self):
        before = self.snapshot()
        for flags in (('--check', '--write'), ('--write', '--check')):
            with self.subTest(flags=flags):
                run = self.run_in_folder(*flags)
                self.assertEqual((run.returncode, run.stdout), (2, ''))
                # argparse names the conflict; an unrecognized --check would also exit 2.
                self.assertIn('not allowed with argument', run.stderr)
                self.assertNotIn('unrecognized', run.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_default_mode_is_unchanged(self):
        # Characterization: passes before and after --check exists. Existing callers see the
        # same report and status, and the default never writes.
        before = self.snapshot()
        drifted = self.run_in_folder()
        self.assertEqual((drifted.returncode, drifted.stderr), (1, ''))
        self.assertEqual(drifted.stdout.splitlines(), self.DRIFT_REPORT)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.run_in_folder('--write').returncode, 0)
        before = self.snapshot()
        clean = self.run_in_folder()
        self.assertEqual((clean.returncode, clean.stderr), (0, ''))
        self.assertEqual(clean.stdout.splitlines(), self.CLEAN_REPORT)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
