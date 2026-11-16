"""The fingerprint-stability replay is an explicit qualification step, never a discovered test.

native/tests/qualification_fingerprint_stability_check.py replays qualification cases in a
scratch replica of the checkout. The review of the generated-outputs repair measured 744 s for
it; one later run through the journal took 345 s. Collected by unittest discovery it ran inside
the exhaustive python-contracts step, whose deadline is 900 s, and on a host lacking a replayed
case's tool it failed that step. Operator decision of 2026-10-31: an explicit case with its own
deadline in the exhaustive and rc2 profiles, outside discovery, and never journalled as PASS
when the replay did not run. The review of that step found its selection variable could still
make the journal record PASS for a replay of nothing or of a fraction of the default cases, so
the plan declares the variable empty (the default replay) in the step's environmentOverrides
and the module refuses a selection that names no case.

Every check lists the real plans (qualify.py --list), runs the real selection, the real
discovery, the real journal or qualify.main(); none runs the full replay. Nothing here runs the
listed argv with the plan's declared overrides applied: that is the full replay, which would
take about twelve minutes inside python-contracts.
"""
import ast
import copy
import fnmatch
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

NATIVE = Path(__file__).resolve().parents[1]
CASE = 'fingerprint-stability'
MODULE = 'qualification_fingerprint_stability_check'
MODULE_FILE = NATIVE / 'tests' / (MODULE + '.py')
RETIRED = 'test_qualification_fingerprint_stability'
SELECTION = 'NOCTURNE_FINGERPRINT_STABILITY_STEPS'
DEADLINE = 1800
PROFILES = {'rc2': ['--profile', 'rc2', '--strict', '--capture'],
            'exhaustive': ['--profile', 'exhaustive', '--strict', '--capture']}
CHEAP_TEST = 'QualificationFingerprintStability.testIdenticalRewriteIsAWriteThatTheHashCannotSee'
SKIP_NAMES = {'skip', 'skipIf', 'skipUnless', 'skipTest', 'SkipTest', 'expectedFailure'}


def listed(options, *extra):
    """The plan exactly as qualify.py declares it for these options."""
    result = subprocess.run([sys.executable, str(NATIVE / 'scripts/qualify.py'), *options, *extra, '--list'],
                            cwd=NATIVE, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise AssertionError('qualify.py --list failed: ' + result.stderr[-2000:])
    return json.loads(result.stdout)


_LISTED = {}


def listed_plan(profile):
    """The profile's plan, listed once per process: every qualify.py --list costs seconds."""
    if profile not in _LISTED:
        _LISTED[profile] = listed(PROFILES[profile])
    return _LISTED[profile]


def scripts_on_path():
    if str(NATIVE / 'scripts') not in sys.path:
        sys.path.insert(0, str(NATIVE / 'scripts'))


def without_selection():
    """The caller's environment minus the replay selection, so an exported value cannot steer a check."""
    return {key: value for key, value in os.environ.items() if key != SELECTION}


def stability_module():
    """The replay module loaded by file path inside the test, so each check fails on its own."""
    if not MODULE_FILE.is_file():
        raise AssertionError(f'{MODULE_FILE.relative_to(NATIVE)} is missing')
    scripts_on_path()
    spec = importlib.util.spec_from_file_location(MODULE, MODULE_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExplicitPlanStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans = {name: listed_plan(name) for name in PROFILES}

    def test_each_profile_lists_the_step_once_with_an_explicit_command(self):
        for profile, plan in self.plans.items():
            with self.subTest(profile=profile):
                rows = [case for case in plan if case['id'] == CASE]
                self.assertEqual(len(rows), 1, f'{profile} must list exactly one {CASE}')
                self.assertEqual(rows[0]['argv'], [sys.executable, '-m', 'unittest', '-v', MODULE])
                self.assertEqual(Path(rows[0]['cwd']), NATIVE / 'tests')
                self.assertEqual([case['id'] for case in plan if MODULE in case['argv']], [CASE])
                self.assertEqual(rows[0]['artifacts'], [], 'the replay writes only inside its scratch replica')
                ids = [case['id'] for case in plan]
                self.assertLess(ids.index('build'), ids.index(CASE), 'the replay needs the built native/dist')
                self.assertGreaterEqual(rows[0]['timeoutSeconds'], DEADLINE)

    def test_each_profile_pins_the_replay_selection_to_the_default(self):
        # Declared like the sanitizer cases' leak options: it replaces whatever the caller exported, so
        # only an explicit run of the module can narrow the replay and the gate always replays DEFAULT_CASES.
        for profile, plan in self.plans.items():
            with self.subTest(profile=profile):
                self.assertEqual(next(case for case in plan if case['id'] == CASE).get('environmentOverrides'), {SELECTION: ''})
                self.assertEqual([case['id'] for case in plan if SELECTION in case.get('environmentOverrides', {})], [CASE])

    def test_deadline_is_a_floor_that_the_step_timeout_flag_only_raises(self):
        # tools/ci/test_delivery_time_budget.py requires every case at the CI budget (7200).
        for profile, options in PROFILES.items():
            for requested, expected in ((60, DEADLINE), (900, DEADLINE), (7200, 7200)):
                with self.subTest(profile=profile, stepTimeout=requested):
                    deadlines = {case['id']: case['timeoutSeconds'] for case in listed(options, '--step-timeout', str(requested))}
                    self.assertEqual(deadlines.get(CASE), expected)
                    self.assertEqual({value for name, value in deadlines.items() if name != CASE}, {requested})

    def test_checkpoint_plan_applies_the_floor_to_this_case_only(self):
        scripts_on_path()
        import qualify
        rows = [(CASE, [sys.executable, '-c', 'pass'], 'tests'), ('other', [sys.executable, '-c', 'pass'])]
        for requested, expected in ((1, (DEADLINE, 1)), (900, (DEADLINE, 900)), (DEADLINE, (DEADLINE, DEADLINE)), (7200, (7200, 7200))):
            with self.subTest(stepTimeout=requested):
                self.assertEqual(tuple(case['timeoutSeconds'] for case in qualify.checkpointPlan(rows, requested)), expected)


MAIN_WRAPPER = r'''
# Runs the real qualify.main() over the real listed fingerprint-stability case, with only its
# argv replaced by a child that exits 0 only when it sees the pinned (empty) replay selection.
# The listed argv itself is never run here: it would start the twelve-minute replay. main() also writes the tracked
# evidence/BUILD-VERIFICATION.json; that write is redirected so a live qualification's own
# record is never replaced.
import sys
from pathlib import Path
native, scratch = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(native/'scripts'))
import qualify
listed = qualify.checkpointPlan
PROBE = ('import os,sys;seen=os.environ.get("NOCTURNE_FINGERPRINT_STABILITY_STEPS");'
         'print("observed",repr(seen));sys.exit(0 if seen=="" else 3)')
def only(plan, timeoutSeconds):
    # Declare from the whole plan, then keep main()'s own row list in step: it records len(plan) as expectedSteps.
    case = next(case for case in listed(plan, timeoutSeconds) if case['id'] == 'fingerprint-stability')
    plan[:] = [row for row in plan if row[0] == 'fingerprint-stability']
    return [{**case, 'argv': [sys.executable, '-c', PROBE]}]
summary, write = qualify.ROOT/'evidence'/'BUILD-VERIFICATION.json', qualify.atomicJson
def scratchOnly(path, value):
    path = Path(path)
    if path == summary: path = scratch/'BUILD-VERIFICATION.redirected.json'
    elif not path.resolve().is_relative_to(scratch): raise AssertionError('qualify.main() wrote outside the test directory: '+str(path))
    write(path, value)
qualify.checkpointPlan, qualify.atomicJson = only, scratchOnly
sys.argv = ['qualify.py', '--profile', sys.argv[3], *sys.argv[4:]]
raise SystemExit(qualify.main())
'''


class JournalDeadline(unittest.TestCase):
    def test_main_runs_the_step_under_its_own_deadline_and_pinned_selection_on_the_journal_and_checkpoint_paths(self):
        """qualify.main(), not only --list, hands the case's own deadline to the runner.

        The default journal path (CI and verify_contracts_package.py use it) passed the
        --step-timeout value to every step, so a listed 1800 would still have killed the
        replay at 900.

        The caller exports a narrowing selection (nothing, a strict subset, an unknown id); the
        child must still see the plan's pin, which the row records, on both runner paths.
        """
        summary = NATIVE / 'evidence/BUILD-VERIFICATION.json'
        before = summary.read_bytes() if summary.exists() else None
        with tempfile.TemporaryDirectory(prefix='nocturne-stability-deadline-') as temporary:
            root = Path(temporary).resolve()
            for profile, storage, exported in (('rc2', 'journal', ','), ('exhaustive', 'journal', 'typescript-types'),
                                               ('rc2', 'checkpointed', 'not-an-rc2-case')):
                with self.subTest(profile=profile, storage=storage, exported=exported):
                    scratch = root / f'{profile}-{storage}'
                    scratch.mkdir()
                    extra = ['--checkpoint-dir', str(scratch / 'store')] if storage == 'checkpointed' else []
                    run = subprocess.run([sys.executable, '-c', MAIN_WRAPPER, str(NATIVE), str(scratch), profile,
                                          '--evidence-dir', str(scratch / 'run'), *extra],
                                         cwd=NATIVE, env={**os.environ, SELECTION: exported}, capture_output=True, text=True, timeout=600)
                    execution = scratch / 'run/EXECUTION.json'
                    self.assertTrue(execution.is_file(), run.stdout + run.stderr)
                    record = json.loads(execution.read_text())
                    self.assertEqual([row['id'] for row in record['commands']], [CASE], run.stdout + run.stderr)
                    self.assertEqual(record['commands'][0]['timeoutSeconds'], DEADLINE)
                    row = record['commands'][0]
                    self.assertEqual(row.get('environmentOverrides'), {SELECTION: ''})
                    log = (scratch / 'run' / row['log']).read_text()
                    self.assertIn("observed ''", log)
                    self.assertEqual(row['status'], 'PASS', log)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(summary.read_bytes() if summary.exists() else None, before, 'main() must not rewrite the tracked summary here')


DISCOVER = r'''
import json, sys, unittest
def leaves(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite): yield from leaves(item)
        else: yield item.id()
print(json.dumps(sorted(leaves(unittest.TestLoader().discover('tests', pattern=sys.argv[1])))))
'''


class OutsideDiscovery(unittest.TestCase):
    def test_discovery_does_not_collect_the_replay_module(self):
        # python-contracts runs "unittest discover -s tests -v", whose default pattern is test*.py.
        for pattern in ('test*.py', 'test_*.py'):
            with self.subTest(pattern=pattern):
                run = subprocess.run([sys.executable, '-c', DISCOVER, pattern], cwd=NATIVE, capture_output=True, text=True, timeout=600)
                self.assertEqual(run.returncode, 0, run.stderr[-2000:])
                identities = json.loads(run.stdout)
                # Positive controls: a discovery that found nothing could not prove an exclusion.
                self.assertTrue(any(name.startswith('test_rc2_release_plan.') for name in identities))
                self.assertTrue(any(name.startswith('test_fingerprint_stability_plan.') for name in identities))
                self.assertEqual([name for name in identities if 'qualification_fingerprint_stability' in name], [])

    def test_module_name_matches_no_test_collection_pattern(self):
        for pattern in ('test*.py', 'test_*.py', '*_test.py'):
            self.assertFalse(fnmatch.fnmatch(MODULE + '.py', pattern), pattern)
        self.assertTrue(MODULE_FILE.is_file())
        self.assertFalse((NATIVE / 'tests' / (RETIRED + '.py')).exists(), 'the retired discovered name must not remain')


class ExplicitRun(unittest.TestCase):
    def in_tests(self, *argv):
        return subprocess.run([sys.executable, *argv], cwd=NATIVE / 'tests', env=without_selection(),
                              capture_output=True, text=True, timeout=600)

    def test_module_imports_by_name_from_the_plan_working_directory(self):
        code = ("import json, unittest, " + MODULE + " as module;"
                "names = sorted(n for n in dir(module.QualificationFingerprintStability) if n.startswith('test'));"
                "loaded = unittest.defaultTestLoader.loadTestsFromName('" + MODULE + "').countTestCases();"
                "print(json.dumps({'names': names, 'loaded': loaded, 'defaults': list(module.DEFAULT_CASES)}))")
        run = self.in_tests('-c', code)
        self.assertEqual(run.returncode, 0, run.stderr[-3000:])
        found = json.loads(run.stdout)
        self.assertEqual(found['names'], ['testIdenticalRewriteIsAWriteThatTheHashCannotSee', 'testRc2CasesLeaveTheFingerprintUnchanged'])
        self.assertEqual(found['loaded'], 2)
        planned = {case['id'] for case in listed_plan('rc2')}
        self.assertLessEqual(set(found['defaults']), planned)
        self.assertNotIn(CASE, found['defaults'])

    def test_internal_test_runs_by_explicit_name(self):
        # Never the full replay: this check is itself collected by discovery.
        run = self.in_tests('-m', 'unittest', '-v', MODULE + '.' + CHEAP_TEST)
        self.assertEqual(run.returncode, 0, run.stderr[-3000:])
        self.assertIn('Ran 1 test', run.stderr)
        self.assertRegex(run.stderr, r'(?m)^OK$')


class RcSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('rc2_release_plan', NATIVE / 'scripts/rc2_release_plan.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.full = [(case['id'], case['argv'], str(Path(case['cwd']).relative_to(NATIVE))) for case in listed_plan('exhaustive')]

    def select(self, rows=None, root=NATIVE):
        return self.module.select_rc2_plan(self.full if rows is None else rows, python=sys.executable, native_root=root)

    def test_selection_keeps_the_step_exactly_as_the_full_plan_declares_it(self):
        self.assertIn(CASE, self.module.REQUIRED_CASE_IDS)
        selected = self.select()
        self.assertEqual([row for row in selected if row[0] == CASE], [row for row in self.full if row[0] == CASE])
        self.assertEqual(len([row for row in selected if row[0] == CASE]), 1)
        scope = self.module.rc2_scope(self.full, selected)
        self.assertIn(CASE, scope['includedCaseIds'])
        self.assertNotIn(CASE, scope['omittedCaseIds'])

    def test_selection_refuses_to_drop_the_step(self):
        with self.assertRaisesRegex(ValueError, CASE):
            self.select([row for row in self.full if row[0] != CASE])

    def test_selection_refuses_a_checkout_without_the_module(self):
        real = Path.is_file
        with mock.patch.object(Path, 'is_file', lambda path: False if path == MODULE_FILE else real(path)):
            with self.assertRaises(FileNotFoundError) as caught:
                self.select()
        self.assertIn(MODULE, str(caught.exception))

    def test_rc2_native_runs_this_guard(self):
        actual = {row[0]: row for row in self.select()}
        self.assertIn('test_fingerprint_stability_plan', actual['rc2-native'][1])


class ReceiptRequiresTheStep(unittest.TestCase):
    """rc2_package.validateRC2Receipt, which packaging uses, needs the step to have run and exited 0."""

    def test_receipt_without_the_step_or_with_it_unpassed_is_refused(self):
        scripts_on_path()
        from rc2_package import validateRC2Receipt
        from rc2_release_plan import REQUIRED_CASE_IDS, NATIVE_STEPS
        ids = list(REQUIRED_CASE_IDS) + [step for step, _ in NATIVE_STEPS] + ['rc2-project-codegen', 'rc2-browser', 'rc2-reference-docs',
                                         'rc2-reference-validate', 'rc2-plan-regressions']
        self.assertIn(CASE, ids)
        digest = 'a' * 64
        record = {'complete': True, 'sourceUnchanged': True, 'localBuildVerified': True, 'fourRuntimeVerified': True,
                  'sourceBefore': digest, 'sourceAfter': digest, 'qualificationProfile': 'rc2', 'runtimePlanQualified': True,
                  'expectedCaseIds': ids, 'qualificationScope': {'profile': 'rc2', 'exhaustive': False, 'includedCaseIds': ids},
                  'commands': [{'id': name, 'status': 'PASS', 'exitCode': 0} for name in ids],
                  'coverage': {'sourceFingerprint': digest, 'passed': True, 'nativeLinePercent': 80, 'requiredPercent': 70},
                  'shippingModeVerification': {'sourceFingerprint': digest, 'passed': True, 'fourRuntimePassed': True,
                                               'measuredReplayEqual': True}}
        validateRC2Receipt(record, digest)
        absent = copy.deepcopy(record)
        remaining = [name for name in ids if name != CASE]
        absent['expectedCaseIds'] = remaining
        absent['qualificationScope']['includedCaseIds'] = remaining
        absent['commands'] = [row for row in absent['commands'] if row['id'] != CASE]
        with self.assertRaises(ValueError):
            validateRC2Receipt(absent, digest)
        for status, code in (('FAIL', 1), ('BLOCKED', None), ('TIMEOUT', None), ('PASS', 1)):
            with self.subTest(status=status, exitCode=code):
                unpassed = copy.deepcopy(record)
                next(row for row in unpassed['commands'] if row['id'] == CASE).update(status=status, exitCode=code)
                with self.assertRaises(ValueError):
                    validateRC2Receipt(unpassed, digest)


class NeverPassedWhenNotRun(unittest.TestCase):
    """The step is never journalled PASS unless the replay ran to completion."""

    def test_module_has_no_skip_path(self):
        self.assertTrue(MODULE_FILE.is_file(), f'{MODULE_FILE.relative_to(NATIVE)} is missing')
        tree = ast.parse(MODULE_FILE.read_text())
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        used |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        used |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) for alias in node.names}
        # unittest exits 0 for a skipped or expected-failure test, which the journal records as PASS.
        self.assertEqual(sorted(SKIP_NAMES & used), [])

    def test_the_step_never_replays_itself(self):
        module = stability_module()
        rc2 = listed_plan('rc2')
        plan = [{'id': 'build'}, {'id': CASE}, {'id': 'gallery'}]
        with mock.patch.dict(os.environ, {SELECTION: 'all'}):
            self.assertEqual([case['id'] for case in module.selected(plan)], ['build', 'gallery'])
            self.assertEqual([case['id'] for case in module.selected(rc2)], [case['id'] for case in rc2 if case['id'] != CASE])
        with mock.patch.dict(os.environ, {SELECTION: 'gallery,' + CASE}):
            with self.assertRaisesRegex(AssertionError, CASE):
                module.selected(plan)
        with mock.patch.dict(os.environ, {SELECTION: 'gallery'}):
            self.assertEqual([case['id'] for case in module.selected(plan)], ['gallery'])
        with mock.patch.dict(os.environ, without_selection(), clear=True):
            self.assertEqual({case['id'] for case in module.selected(rc2)}, set(module.DEFAULT_CASES))

    def test_a_selection_naming_no_case_is_refused(self):
        module = stability_module()
        rc2 = listed_plan('rc2')
        for value in (',', ' , ', ',,', ' ,  , '):
            with self.subTest(value=value), mock.patch.dict(os.environ, {**without_selection(), SELECTION: value}, clear=True):
                with self.assertRaisesRegex(AssertionError, SELECTION):
                    module.selected(rc2)

    def test_unset_or_blank_selection_is_the_default_and_a_named_case_still_narrows_a_run_by_hand(self):
        # The plan's pin relies on the empty value meaning the default replay.
        module = stability_module()
        rc2 = listed_plan('rc2')
        defaults = [case['id'] for case in rc2 if case['id'] in module.DEFAULT_CASES]
        self.assertEqual(sorted(defaults), sorted(module.DEFAULT_CASES))
        for value in (None, '', '   '):
            exported = without_selection() if value is None else {**without_selection(), SELECTION: value}
            with self.subTest(value=value), mock.patch.dict(os.environ, exported, clear=True):
                self.assertEqual([case['id'] for case in module.selected(rc2)], defaults)
        with mock.patch.dict(os.environ, {**without_selection(), SELECTION: 'typescript-types'}, clear=True):
            self.assertEqual([case['id'] for case in module.selected(rc2)], ['typescript-types'])

    def test_the_value_the_plan_pins_selects_exactly_the_default_replay(self):
        module = stability_module()
        rc2 = listed_plan('rc2')
        for profile in PROFILES:
            pinned = next(case for case in listed_plan(profile) if case['id'] == CASE).get('environmentOverrides', {})
            with self.subTest(profile=profile):
                self.assertIn(SELECTION, pinned)
                with mock.patch.dict(os.environ, {**without_selection(), **pinned}, clear=True):
                    self.assertEqual({case['id'] for case in module.selected(rc2)}, set(module.DEFAULT_CASES))

    def test_an_empty_selection_is_a_failed_run_not_a_pass(self):
        # The listed argv with no declared overrides stands in for the module run by hand with the variable
        # exported: applying the plan's pin to this argv would start the full twelve-minute replay.
        scripts_on_path()
        from delivery_runner import RunJournal
        case = next(case for case in listed_plan('rc2') if case['id'] == CASE)
        with tempfile.TemporaryDirectory(prefix='nocturne-stability-empty-') as temporary:
            root = Path(temporary).resolve()
            with RunJournal(root / 'journal') as journal:
                row = journal.runStep('empty-selection', case['argv'], Path(case['cwd']), timeoutSeconds=case['timeoutSeconds'],
                                      env={**without_selection(), SELECTION: ' , '})
            log = (root / 'journal' / row['log']).read_text()
        self.assertEqual((row['status'], row['exitCode']), ('FAIL', 1), log[-3000:])
        self.assertRegex(log, SELECTION + r'.*selects no')
        self.assertNotRegex(log, r'(?m)^OK$')

    def test_a_replay_must_cover_every_selected_case(self):
        module = stability_module()
        cases = [{'id': 'gallery'}, {'id': 'typescript-types'}]
        module.requireReplayed(cases, ['typescript-types', 'gallery'])
        for selection, replayed in ((cases, []), (cases, ['gallery']), ([], []), ([], ['gallery'])):
            with self.subTest(selected=[case['id'] for case in selection], replayed=replayed):
                with self.assertRaises(AssertionError):
                    module.requireReplayed(selection, replayed)

    def test_missing_runtime_is_blocked_not_passed(self):
        module = stability_module()
        with tempfile.TemporaryDirectory(prefix='nocturne-stability-blocked-') as temporary:
            log = Path(temporary) / 'case.log'
            status, code, _ = module.execute({'argv': [str(Path(temporary) / 'no-such-runtime')], 'cwd': temporary, 'timeoutSeconds': 30},
                                             without_selection(), log)
            self.assertEqual((status, code), ('BLOCKED', None))
            self.assertIn('BLOCKED', log.read_text())

    def test_a_replay_that_cannot_run_is_journalled_as_failure(self):
        scripts_on_path()
        from delivery_runner import RunJournal
        case = next((case for case in listed_plan('rc2') if case['id'] == CASE), None)
        self.assertIsNotNone(case, f'{CASE} is not in the rc2 plan')
        # No environmentOverrides: the plan's pin would replace this value and start the full replay.
        environment = {**without_selection(), SELECTION: 'not-an-rc2-case'}
        with tempfile.TemporaryDirectory(prefix='nocturne-stability-journal-') as temporary:
            root = Path(temporary).resolve()
            with RunJournal(root / 'journal') as journal:
                row = journal.runStep('unrunnable-replay', case['argv'], Path(case['cwd']), timeoutSeconds=case['timeoutSeconds'], env=environment)
            log = (root / 'journal' / row['log']).read_text()
        # One of the module's two tests passes; the step as a whole must still fail.
        self.assertEqual((row['status'], row['exitCode']), ('FAIL', 1), log[-3000:])
        self.assertRegex(log, r'Not rc2 case ids: not-an-rc2-case|native/dist/\S+ is missing')
        self.assertNotRegex(log, r'(?m)^OK$')


if __name__ == '__main__':
    unittest.main()
