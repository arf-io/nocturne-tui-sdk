"""The qualifier and CI supply the repository root to every Python step explicitly.

On the 2026-10-31 fresh Linux strict rc2 run (native/evidence/linux-host-20261031/
qualify-rc2-02) the root reached child interpreters only by luck of the caller's
environment. qualify.py now prepends it to PYTHONPATH before binding the step
environment; the workflows set it at job level for every job that runs tests.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
PROBE = 'import native.bindings.python.nocturne_native as m;print(m.__file__)'


def qualify_module():
    if str(NATIVE / 'scripts') not in sys.path:
        sys.path.insert(0, str(NATIVE / 'scripts'))
    import qualify
    return qualify


class QualifierEnvironment(unittest.TestCase):
    def test_root_first_caller_entries_kept_and_idempotent(self):
        environment = qualify_module().qualificationEnvironment
        root = str(REPOSITORY)
        self.assertEqual(environment({})['PYTHONPATH'], root)
        self.assertEqual(environment({'PYTHONPATH': ''})['PYTHONPATH'], root)
        caller = os.pathsep.join(['/caller/one', '', '/caller/two'])
        once = environment({'PYTHONPATH': caller, 'OTHER': 'kept'})
        self.assertEqual(once, {'PYTHONPATH': root + os.pathsep + caller, 'OTHER': 'kept'})
        self.assertEqual(environment(once), once)
        source = {'PYTHONPATH': caller}
        environment(source)
        self.assertEqual(source, {'PYTHONPATH': caller})

    def test_listed_python_steps_import_this_checkout_under_the_qualifier_environment(self):
        qualify = qualify_module()
        from cargo_example import cargoEnvironment
        listed = subprocess.run([sys.executable, str(NATIVE / 'scripts/qualify.py'), '--profile', 'rc2', '--strict', '--list'],
                                cwd=NATIVE, capture_output=True, text=True, timeout=300, check=True)
        steps = [case for case in json.loads(listed.stdout) if case['argv'][0] == sys.executable]
        self.assertTrue({'rc2-native', 'rc2-native-acceptance', 'rc2-native-runtimes', 'rc2-browser', 'rc2-reference-docs', 'rc2-plan-regressions', 'parity'}
                        <= {case['id'] for case in steps})
        with tempfile.TemporaryDirectory(prefix='nocturne-decoy-checkout-') as decoy:
            (Path(decoy) / 'native/bindings/python').mkdir(parents=True)
            (Path(decoy) / 'native/bindings/python/nocturne_native.py').write_text("raise RuntimeError('decoy checkout')\n")
            for caller in ({}, {'PYTHONPATH': decoy}):
                base = {key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}
                child = cargoEnvironment(REPOSITORY, qualify.qualificationEnvironment({**base, **caller}))
                for case in steps:
                    with self.subTest(step=case['id'], caller=caller):
                        run = subprocess.run([sys.executable, '-c', PROBE], cwd=case['cwd'], env=child,
                                             capture_output=True, text=True, timeout=300)
                        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
                        self.assertEqual(Path(run.stdout.strip()).resolve(),
                                         NATIVE / 'bindings/python/nocturne_native.py')

    def test_no_planned_step_replaces_pythonpath_without_the_root(self):
        # `env PYTHONPATH=...` in a step's argv overrides the qualifier's value for that step.
        listed = subprocess.run([sys.executable, str(NATIVE / 'scripts/qualify.py'), '--strict', '--capture', '--list'],
                                cwd=NATIVE, capture_output=True, text=True, timeout=600, check=True)
        overriding = 0
        for case in json.loads(listed.stdout):
            if case['argv'][0] != 'env':
                continue
            for argument in case['argv'][1:]:
                if argument.startswith('PYTHONPATH='):
                    overriding += 1
                    entries = {(Path(case['cwd']) / entry).resolve() for entry in argument[len('PYTHONPATH='):].split(os.pathsep) if entry}
                    with self.subTest(step=case['id']):
                        self.assertIn(REPOSITORY, entries)
        if not overriding and (REPOSITORY / 'PUBLIC-TREE-REPORT.json').is_file():
            self.skipTest('the steps that override PYTHONPATH are the resource-ownership shards, which the public tree leaves out')
        self.assertGreater(overriding, 0)

    def test_main_applies_the_environment_before_any_binding_or_step(self):
        source = (NATIVE / 'scripts/qualify.py').read_text()
        main = source[source.index('def main():'):]
        applied = main.index("os.environ['PYTHONPATH']=qualificationEnvironment(os.environ)['PYTHONPATH']")
        for later in ('tool=discover()', 'cargoEnvironment(ROOT.parent,os.environ)', 'binding=currentBinding()', 'run.runStep(', 'checkpoints.runCase('):
            with self.subTest(later=later):
                self.assertLess(applied, main.index(later))


class WorkflowEnvironment(unittest.TestCase):
    TEST_COMMANDS = ('qualify-native.sh', 'unittest', 'native/tests/', 'run_historical_tests.py')

    def test_every_job_running_tests_sets_the_workspace_root(self):
        if not any((REPOSITORY / folder).is_dir() for folder in ('.github/workflows', '.forgejo/workflows')):
            # The compact RC2 SDK payload ships native/tests but no workflow definitions.
            self.skipTest('no workflow definitions in this payload; checked in the source repository')
        import yaml
        requiring = set()
        for path in ['.forgejo/workflows/nocturne.yml', '.github/workflows/nocturne.yml', '.github/workflows/rc4-native.yml']:
            workflow = yaml.load((REPOSITORY / path).read_text(), Loader=yaml.BaseLoader)
            for name, job in workflow['jobs'].items():
                commands = '\n'.join(step.get('run', '') for step in job.get('steps', []))
                if any(command in commands for command in self.TEST_COMMANDS):
                    requiring.add((path, name))
                    with self.subTest(workflow=path, job=name):
                        self.assertEqual(job.get('env', {}).get('PYTHONPATH'), '${{ github.workspace }}')
        self.assertEqual(requiring, {('.forgejo/workflows/nocturne.yml', 'native'), ('.github/workflows/nocturne.yml', 'native'),
                                     ('.github/workflows/nocturne.yml', 'supplemental'), ('.github/workflows/rc4-native.yml', 'native')})


if __name__ == '__main__':
    unittest.main()
