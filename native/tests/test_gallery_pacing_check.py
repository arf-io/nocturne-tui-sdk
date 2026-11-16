"""The live gallery pacing check: fixed thresholds, its verdicts and its release-plan registration.

scripts/check_gallery_pacing.py drives Chromium against the built gallery and its evaluate() is
pure, so each bound is exercised directly with clock samples shaped like the ones the 2026-11-01
RC3 gallery produced (catch-up growing about 650 ms per second at 3 fps). No gallery is built or
run here. Two tests run a real runtime on small inputs: the template's own pacing code in Node on
the real WASM core (TemplateLivePacing), and the #error observer the check installs in Chromium on
a page holding only <div id="error"> (PacingErrorChannelObserver); each reports BLOCKED when its
runtime is missing. main() runs with a stand-in for the Playwright surface and a shaped run.
"""
import contextlib, copy, importlib.util, io, json, sys, tempfile, types, unittest
from pathlib import Path
from unittest import mock
NATIVE = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded)
    return loaded


check = module('check_gallery_pacing', NATIVE / 'scripts/check_gallery_pacing.py')
plan = module('rc2_release_plan', NATIVE / 'scripts/rc2_release_plan.py')


def scene(identity, fps=55.0, catch_up_us=0, growth_us_per_s=0, seconds=5, host=None, attract=True, error=''):
    """Five 1 s samples of a live scene: painted frames, native clock and optional host backlog."""
    samples = []
    for second in range(1, seconds + 1):
        target = second * 1_000_000
        lag = catch_up_us + growth_us_per_s * second
        samples.append({'t': second * 1000.0, 'at': 10_000.0 + second * 1000, 'paints': round(fps * second),
                        'timeUs': target - lag, 'targetUs': target, 'step': (target - lag) * 120 // 1_000_000,
                        'paused': False, 'host': host})
    return {'id': identity, 'attract': attract, 'seconds': seconds, 'samples': samples, 'error': error}


def at_rate(identity, steps_per_second, fps=31.0, seconds=5):
    """A live scene whose native clock moves at a steady rate and never lags its target."""
    out = scene(identity, fps=fps, seconds=seconds)
    for second, row in enumerate(out['samples'], 1):
        step = int(steps_per_second * second)
        row.update(step=step, timeUs=step * 1_000_000 // 120, targetUs=step * 1_000_000 // 120)
    return out


def resume(backlog_us=0, advanced_us=20_000, delay_ms=16.0, frames=12, host=None, stall=False, frame_us=16_667, error='', budget_us=None):
    """A resume: the clock before, the first painted frames after, and the next sample."""
    before = {'t': 1000.0, 'timeUs': 3_000_000, 'targetUs': 3_000_000, 'step': 360, 'host': None}
    if budget_us is not None:
        before['frameBudgetUs'] = budget_us
    end = before['t'] + 5000
    if stall:
        before['end'] = end
    trace = []
    for i in range(frames):
        time_us = before['timeUs'] + advanced_us + frame_us * i
        trace.append({'t': end + delay_ms + 16 * i, 'timeUs': time_us, 'targetUs': time_us + backlog_us,
                      'step': time_us * 120 // 1_000_000, 'host': host})
    out = {'before': before, 'trace': trace, 'after': [dict(trace[-1], t=900.0, at=end + 800)] if trace else [], 'error': error}
    if not stall:
        out['shown'] = end
    return out


def live_run(**overrides):
    run = {'scenes': [scene(name) for name in check.DEFAULT_SCENES], 'visibility': resume(),
           'stall': resume(stall=True), 'errors': [], 'errorChannel': [],
           'cpuCount': 16, 'load': {'before': 1.0, 'after': 1.5}, 'retries': []}
    run.update(overrides)
    return run


def attempt(fps=55.0, load=1.0, rate=120):
    """One more pass over the default scenes, at a host load average sampled before and after it."""
    return {'scenes': [at_rate(name, rate, fps=fps) for name in check.DEFAULT_SCENES], 'load': {'before': load, 'after': load}}


def verdicts(run):
    return {row['name']: row['status'] for row in check.evaluate(run)}


def failing(run):
    return {name for name, status in verdicts(run).items() if status != 'PASS'}


REAL_TIME = 'simulation keeps real time: per-scene median at least 108 steps/s'
REAL_TIME_CEILING = 'simulation keeps real time: per-scene median at most 132 steps/s'
ERROR_CHANNEL = 'gallery error channel (#error) empty at the end of every phase and never written'
def progressed(phase):
    return f'{phase}: the simulation advances at least 12 steps over the frames and sample after resume'


class PacingSimulationProgress(unittest.TestCase):
    """A gallery that paints but does not simulate is the failure the gate exists to catch."""

    def test_a_frozen_simulation_fails_at_any_frame_rate(self):
        # Review mutant m1 (liveAdvance throws): steps/s 0 in every window while painting 38 fps.
        frozen = [at_rate(name, 0, fps=55.0) for name in check.DEFAULT_SCENES]
        self.assertIn(REAL_TIME, failing(live_run(scenes=frozen)))

    def test_slow_motion_fails_and_real_time_passes(self):
        # Review mutant m2 (one step per frame) ran at 11-45 steps/s; the threshold is 90 percent of 120.
        for rate in (0, 1, 10, 30, 107):
            with self.subTest(rate=rate):
                self.assertIn(REAL_TIME, failing(live_run(scenes=[at_rate(name, rate) for name in check.DEFAULT_SCENES])))
        for rate in (108, 120):
            with self.subTest(rate=rate):
                self.assertEqual(verdicts(live_run(scenes=[at_rate(name, rate) for name in check.DEFAULT_SCENES])).get(REAL_TIME), 'PASS')

    def test_one_slow_scene_is_enough_to_fail(self):
        scenes = [at_rate(name, 120) for name in check.DEFAULT_SCENES]
        scenes[2] = at_rate(check.DEFAULT_SCENES[2], 60)
        self.assertIn(REAL_TIME, failing(live_run(scenes=scenes)))

    def test_a_simulation_running_faster_than_real_time_fails(self):
        # Double accrual in the gallery (wanted = elapsedMs * 2000) ran at per-scene medians of 232-241
        # steps/s and passed every other assertion in Chromium: the floor alone let it through.
        fast = live_run(scenes=[at_rate(name, 240) for name in check.DEFAULT_SCENES])
        self.assertEqual(check.verdict(check.evaluate(fast)), 'FAIL')
        self.assertEqual(verdicts(fast).get(REAL_TIME), 'PASS')   # the floor is a separate bound
        self.assertEqual(failing(fast), {REAL_TIME_CEILING})      # and nothing else notices

    def test_the_ceiling_is_110_percent_of_the_fixed_step(self):
        self.assertEqual((check.MIN_STEPS_PER_SECOND, check.MAX_STEPS_PER_SECOND), (108, 132))
        self.assertEqual(check.MAX_STEPS_PER_SECOND, round(1.1 * check.STEP_HZ))
        for rate in (108, 120, 132):
            with self.subTest(rate=rate):
                self.assertEqual(verdicts(live_run(scenes=[at_rate(name, rate) for name in check.DEFAULT_SCENES])).get(REAL_TIME_CEILING), 'PASS')
        for rate in (133, 144, 240, 480):
            with self.subTest(rate=rate):
                self.assertIn(REAL_TIME_CEILING, failing(live_run(scenes=[at_rate(name, rate) for name in check.DEFAULT_SCENES])))

    def test_one_fast_scene_is_enough_to_fail_the_ceiling(self):
        scenes = [at_rate(name, 120) for name in check.DEFAULT_SCENES]
        scenes[1] = at_rate(check.DEFAULT_SCENES[1], 240)
        self.assertEqual(failing(live_run(scenes=scenes)), {REAL_TIME_CEILING})

    def test_every_pass_is_held_to_the_ceiling(self):
        run = live_run(retries=[attempt(fps=20.0, load=1.0), attempt(fps=40.0, load=1.0, rate=240)])
        self.assertEqual(verdicts(run).get(REAL_TIME_CEILING), 'FAIL')
        self.assertEqual(verdicts(live_run(retries=[attempt(fps=40.0, load=1.0)])).get(REAL_TIME_CEILING), 'PASS')

    def test_the_median_tolerates_one_window_that_drained_a_full_backlog(self):
        # A frame budget is 24 steps: draining it in one window moves that window by 24 steps/s (the
        # next one by -24) and the median of the four windows not at all.
        scenes = [at_rate(name, 120) for name in check.DEFAULT_SCENES]
        scenes[0]['samples'][2]['step'] += 24
        self.assertEqual(set(verdicts(live_run(scenes=scenes)).values()), {'PASS'})

    def test_a_page_with_no_windows_fails_the_ceiling_too(self):
        stopped = [at_rate(name, 120) for name in check.DEFAULT_SCENES]
        for row in stopped[0]['samples']:
            row['paintAt'] = 10_500.0
        self.assertTrue({REAL_TIME, REAL_TIME_CEILING} <= failing(live_run(scenes=stopped)))

    def test_the_median_tolerates_one_jittered_window(self):
        # Sampling between frames moves one window by up to a frame of steps (HEAD at load 6: 107-138).
        scenes = [at_rate(name, 120) for name in check.DEFAULT_SCENES]
        rows = scenes[0]['samples']
        rows[2]['step'] -= 14
        self.assertEqual(verdicts(live_run(scenes=scenes)).get(REAL_TIME), 'PASS')

    def test_steps_per_second_are_timed_between_painted_frames(self):
        # The clock moves only on painted frames, so a 1 s sample reads the step of the last paint.
        # With 250 ms frames the sample-to-paint lag alone moves a window by 30 steps/s; timing each
        # window between the paints behind its samples measures the simulation, not the sampler.
        def lagging(rate):
            out = scene('rain', fps=4.0)
            for row, lag_ms in zip(out['samples'], (0, 250, 0, 125, 250)):
                paint = row['at'] - lag_ms
                step = int(rate * (paint - 10_000.0) / 1000)
                row.update(paintAt=paint, step=step, timeUs=step * 1_000_000 // 120, targetUs=step * 1_000_000 // 120)
            return out
        real_time = [lagging(120) for _ in check.DEFAULT_SCENES]
        self.assertLess(check.statistics.median([(b['step'] - a['step']) / ((b['t'] - a['t']) / 1000)
                                                 for a, b in zip(real_time[0]['samples'], real_time[0]['samples'][1:])]), 108)
        self.assertEqual(verdicts(live_run(scenes=real_time)).get(REAL_TIME), 'PASS')
        self.assertIn(REAL_TIME, failing(live_run(scenes=[lagging(100) for _ in check.DEFAULT_SCENES])))
        self.assertIn(REAL_TIME, failing(live_run(scenes=[lagging(0) for _ in check.DEFAULT_SCENES])))

    def test_a_page_that_stops_painting_has_no_windows(self):
        stopped = [at_rate(name, 120) for name in check.DEFAULT_SCENES]
        for row in stopped[0]['samples']:
            row['paintAt'] = 10_500.0
        self.assertIn(REAL_TIME, failing(live_run(scenes=stopped)))

    def test_a_simulation_frozen_after_resume_fails(self):
        # Review mutant m3 (visibilitychange sets running=false): the clock never moves after resume.
        for phase, stall in (('visibility', False), ('stall', True)):
            with self.subTest(phase=phase):
                name = progressed(phase)
                self.assertIn(name, failing(live_run(**{phase: resume(frame_us=0, stall=stall)})))
                self.assertIn(name, failing(live_run(**{phase: resume(frames=0, stall=stall)})))
                # 12 steps across the frames after resume pass; 11 do not (one step per 8333 us frame).
                self.assertEqual(verdicts(live_run(**{phase: resume(frame_us=1_000_000 // 120 + 70, frames=13, stall=stall)})).get(name), 'PASS')
                self.assertIn(name, failing(live_run(**{phase: resume(frame_us=1_000_000 // 120, frames=12, stall=stall)})))

    def test_the_first_sample_after_resume_counts_toward_progress(self):
        run = live_run(visibility=resume(frame_us=0))
        run['visibility']['after'] = [dict(run['visibility']['trace'][-1], step=run['visibility']['trace'][0]['step'] + 30, t=900.0, at=7000.0)]
        self.assertEqual(verdicts(run).get(progressed('visibility')), 'PASS')

    def test_text_in_the_gallery_error_channel_fails(self):
        # tick() reports a live-loop exception to #error and stops; no pageerror is raised.
        scenes = [scene(name) for name in check.DEFAULT_SCENES]
        scenes[1]['error'] = 'mutant: live loop crash'
        self.assertIn(ERROR_CHANNEL, failing(live_run(scenes=scenes)))
        self.assertIn(ERROR_CHANNEL, failing(live_run(stall=resume(stall=True, error='TypeError: boom'))))
        self.assertIn(ERROR_CHANNEL, failing(live_run(visibility=resume(error='RangeError'))))
        # A message that a later act() cleared is still a failure.
        self.assertIn(ERROR_CHANNEL, failing(live_run(errorChannel=[{'t': 1234.0, 'text': 'mutant: live loop crash'}])))
        self.assertEqual(verdicts(live_run()).get(ERROR_CHANNEL), 'PASS')

    def test_an_unread_error_channel_fails(self):
        run = live_run(); del run['scenes'][0]['error']
        self.assertIn(ERROR_CHANNEL, failing(run))
        run = live_run(); run['stall']['error'] = None
        self.assertIn(ERROR_CHANNEL, failing(run))
        run = live_run(); del run['errorChannel']
        self.assertIn(ERROR_CHANNEL, failing(run))

    def test_the_live_loop_crash_mutant_fails_for_progress_and_error(self):
        # The shape check_gallery_pacing.py recorded for review mutant m1, which then passed 8 of 8.
        run = live_run(scenes=[at_rate(name, 0, fps=38.0) for name in check.DEFAULT_SCENES],
                       visibility=resume(frame_us=0), stall=resume(frame_us=0, stall=True),
                       errorChannel=[{'t': 900.0, 'text': 'mutant: live loop crash'}])
        for scene_row in run['scenes']:
            scene_row['error'] = 'mutant: live loop crash'
        self.assertTrue({REAL_TIME, ERROR_CHANNEL, progressed('visibility'), progressed('stall')} <= failing(run))


FPS = 'median frame rate above 30 fps in at least one of 3 passes'


class PacingFrameRateUnderContention(unittest.TestCase):
    """Frame rate is best of three passes; only it may be BLOCKED by measured host contention."""

    def test_constants(self):
        self.assertEqual((check.FPS_ATTEMPTS, check.CONTENDED_LOAD_PER_CPU), (3, 0.25))

    def test_a_later_pass_above_thirty_fps_passes(self):
        first = attempt(fps=25.0, load=6.0)
        run = live_run(scenes=first['scenes'], load=first['load'], retries=[attempt(fps=33.0, load=6.0)])
        self.assertEqual(verdicts(run).get(FPS), 'PASS')
        self.assertEqual(check.verdict(check.evaluate(run)), 'PASS')

    def test_low_frame_rate_on_a_quiet_host_fails(self):
        # The pre-fix gallery: 16.7-17.8 fps at load 1.9-3.3 is a per-command cost regression.
        low = attempt(fps=17.0, load=2.0)
        run = live_run(scenes=low['scenes'], load=low['load'], retries=[attempt(fps=17.0, load=2.0), attempt(fps=17.0, load=2.0)])
        self.assertEqual(verdicts(run).get(FPS), 'FAIL')
        self.assertEqual(check.verdict(check.evaluate(run)), 'FAIL')

    def test_low_frame_rate_in_every_contended_pass_is_blocked(self):
        # HEAD 9c497bb: 19.5-25.3 fps at load 5.2-6.9 with every simulation assertion passing.
        low = attempt(fps=20.0, load=5.2)
        run = live_run(scenes=low['scenes'], load=low['load'], retries=[attempt(fps=21.0, load=6.0), attempt(fps=19.0, load=4.0)])
        self.assertEqual(verdicts(run).get(FPS), 'BLOCKED')
        self.assertEqual(check.verdict(check.evaluate(run)), 'BLOCKED')
        self.assertEqual(check.EXIT_CODES['BLOCKED'], 3)

    def test_one_quiet_pass_with_a_low_frame_rate_fails(self):
        low = attempt(fps=20.0, load=6.0)
        run = live_run(scenes=low['scenes'], load=low['load'], retries=[attempt(fps=20.0, load=2.0), attempt(fps=20.0, load=6.0)])
        self.assertEqual(verdicts(run).get(FPS), 'FAIL')

    def test_contention_never_excuses_a_simulation_failure(self):
        # A frozen simulation on a loaded host is FAIL, not BLOCKED.
        frozen = attempt(fps=20.0, load=8.0, rate=0)
        run = live_run(scenes=frozen['scenes'], load=frozen['load'], retries=[attempt(fps=20.0, load=8.0, rate=0), attempt(fps=20.0, load=8.0, rate=0)])
        self.assertEqual(verdicts(run).get(REAL_TIME), 'FAIL')
        self.assertEqual(check.verdict(check.evaluate(run)), 'FAIL')
        self.assertEqual(check.EXIT_CODES['FAIL'], 2)

    def test_every_pass_must_keep_real_time_and_bounded_catch_up(self):
        run = live_run(retries=[attempt(fps=20.0, load=1.0), attempt(fps=40.0, load=1.0, rate=60)])
        self.assertEqual(verdicts(run).get(REAL_TIME), 'FAIL')
        lagging = attempt(fps=40.0)
        for row in lagging['scenes'][1]['samples']:
            row['targetUs'] = row['timeUs'] + 400_000
        self.assertEqual(verdicts(live_run(retries=[lagging])).get('catch-up below 250 ms at every 1 s sample after the first 2 s'), 'FAIL')

    def test_an_unmeasured_load_is_not_contention(self):
        low = attempt(fps=20.0, load=6.0)
        run = live_run(scenes=low['scenes'], load=None, retries=[])
        self.assertEqual(verdicts(run).get(FPS), 'FAIL')

    def test_verdict_precedence(self):
        rows = lambda *statuses: [{'name': str(i), 'status': s, 'detail': ''} for i, s in enumerate(statuses)]
        self.assertEqual(check.verdict(rows('PASS', 'PASS')), 'PASS')
        self.assertEqual(check.verdict(rows('PASS', 'BLOCKED')), 'BLOCKED')
        self.assertEqual(check.verdict(rows('FAIL', 'BLOCKED')), 'FAIL')
        self.assertEqual(check.verdict([]), 'FAIL')
        self.assertEqual(check.EXIT_CODES, {'PASS': 0, 'FAIL': 2, 'BLOCKED': 3})


class PacingThresholds(unittest.TestCase):
    def test_declared_scope_matches_the_work_order(self):
        self.assertEqual(check.VIEWPORT, {'width': 1600, 'height': 900})
        self.assertGreaterEqual(len(check.DEFAULT_SCENES), 4)
        self.assertGreaterEqual(len(check.DEFAULT_SCENES) * check.SECONDS_PER_SCENE, 20)
        self.assertEqual((check.CATCH_UP_LIMIT_US, check.MIN_MEDIAN_FPS, check.WARMUP_SAMPLES), (250_000, 30.0, 2))
        # One frame budget: the gallery default of 12 native steps at the fixed 120 Hz step.
        self.assertEqual(check.FRAME_BUDGET_US, 100_000)
        self.assertEqual(check.HIDDEN_SECONDS, 5)
        self.assertEqual((check.MIN_STEPS_PER_SECOND, check.RESUME_MIN_STEPS), (108, 12))
        # A page's own frame budget (nativeLab.pacing().frameBudgetUs) is believed up to 24 steps.
        self.assertEqual(check.MAX_FRAME_BUDGET_US, 200_000)

    def test_default_scenes_are_classic_attract_recipes(self):
        # Documented attract rule: every recipe without `demonstrates` is in the rotation.
        classic = {recipe['id']: recipe for recipe in json.loads((NATIVE / 'recipes.json').read_text())}
        for name in check.DEFAULT_SCENES:
            self.assertIn(name, classic)
            self.assertNotIn('demonstrates', classic[name])

    def test_live_page_passes_every_assertion(self):
        self.assertEqual(set(verdicts(live_run()).values()), {'PASS'})

    def test_measured_rc3_backlog_growth_fails(self):
        run = live_run(scenes=[scene(name, fps=3.2, catch_up_us=300_000, growth_us_per_s=650_000) for name in check.DEFAULT_SCENES])
        result = verdicts(run)
        self.assertEqual(result['catch-up below 250 ms at every 1 s sample after the first 2 s'], 'FAIL')
        self.assertEqual(result[FPS], 'FAIL')

    def test_only_the_first_two_samples_of_the_run_are_warm_up(self):
        run = live_run()
        for index in range(2):
            run['scenes'][0]['samples'][index]['timeUs'] -= 900_000
        self.assertEqual(verdicts(run)['catch-up below 250 ms at every 1 s sample after the first 2 s'], 'PASS')
        run['scenes'][0]['samples'][2]['timeUs'] -= 250_000
        self.assertEqual(verdicts(run)['catch-up below 250 ms at every 1 s sample after the first 2 s'], 'FAIL')
        later = live_run()
        later['scenes'][3]['samples'][0]['timeUs'] -= 260_000
        self.assertEqual(verdicts(later)['catch-up below 250 ms at every 1 s sample after the first 2 s'], 'FAIL')

    def test_frame_rate_must_exceed_thirty(self):
        for fps, expected in ((30.0, 'FAIL'), (29.0, 'FAIL'), (31.0, 'PASS')):
            run = live_run(scenes=[scene(name, fps=fps) for name in check.DEFAULT_SCENES])
            self.assertEqual(verdicts(run)[FPS], expected, fps)

    def test_host_reported_backlog_is_held_to_the_same_bound(self):
        run = live_run(scenes=[scene(name, host=400_000) for name in check.DEFAULT_SCENES])
        self.assertEqual(verdicts(run)['catch-up below 250 ms at every 1 s sample after the first 2 s'], 'FAIL')
        run = live_run(visibility=resume(host=150_000))
        self.assertEqual(verdicts(run)['visibility: backlog at most one frame budget after resume'], 'FAIL')

    def test_resumed_backlog_must_stay_within_one_frame_budget(self):
        for phase, stall in (('visibility', False), ('stall', True)):
            with self.subTest(phase=phase):
                name = f'{phase}: backlog at most one frame budget after resume'
                self.assertEqual(verdicts(live_run(**{phase: resume(backlog_us=100_000, stall=stall)}))[name], 'PASS')
                self.assertEqual(verdicts(live_run(**{phase: resume(backlog_us=100_001, stall=stall)}))[name], 'FAIL')
                self.assertEqual(verdicts(live_run(**{phase: resume(backlog_us=5_000_000, stall=stall)}))[name], 'FAIL')
                self.assertEqual(verdicts(live_run(**{phase: resume(frames=0, stall=stall)}))[name], 'FAIL')

    def test_the_resume_limit_is_the_frame_budget_the_page_reports(self):
        # The gallery's live budget is 24 steps (200 ms): a session scene's host backlog may sit at it.
        for phase, stall in (('visibility', False), ('stall', True)):
            with self.subTest(phase=phase):
                name = f'{phase}: backlog at most one frame budget after resume'
                self.assertEqual(verdicts(live_run(**{phase: resume(host=150_000, budget_us=200_000, stall=stall)}))[name], 'PASS')
                self.assertEqual(verdicts(live_run(**{phase: resume(host=200_000, budget_us=200_000, stall=stall)}))[name], 'PASS')
                self.assertEqual(verdicts(live_run(**{phase: resume(host=200_001, budget_us=200_000, stall=stall)}))[name], 'FAIL')
                # A smaller authored budget is the smaller limit.
                self.assertEqual(verdicts(live_run(**{phase: resume(host=9_000, budget_us=8_333, stall=stall)}))[name], 'FAIL')
                self.assertEqual(verdicts(live_run(**{phase: resume(host=150_000, budget_us=200_000, stall=stall)})).get(f'{phase}: frame budget the page reports at most 200 ms'), 'PASS')
        reached = 'visibility: the 5 s interval does not reach the simulation'
        self.assertEqual(verdicts(live_run(visibility=resume(advanced_us=200_000, budget_us=200_000)))[reached], 'PASS')
        self.assertEqual(verdicts(live_run(visibility=resume(advanced_us=250_000, budget_us=200_000)))[reached], 'FAIL')

    def test_a_page_cannot_loosen_its_own_limit(self):
        # A reported budget above the check's fixed 24-step maximum fails, and the maximum still bounds the backlog.
        for phase, stall in (('visibility', False), ('stall', True)):
            with self.subTest(phase=phase):
                result = verdicts(live_run(**{phase: resume(host=300_000, budget_us=5_000_000, stall=stall)}))
                self.assertEqual(result.get(f'{phase}: frame budget the page reports at most 200 ms'), 'FAIL')
                self.assertEqual(result[f'{phase}: backlog at most one frame budget after resume'], 'FAIL')
                for bad in ('200000', -1, float('nan')):
                    self.assertEqual(verdicts(live_run(**{phase: resume(budget_us=bad, stall=stall)})).get(f'{phase}: frame budget the page reports at most 200 ms'), 'FAIL', bad)

    def test_a_page_that_reports_no_budget_keeps_the_12_step_default(self):
        name = 'visibility: backlog at most one frame budget after resume'
        self.assertEqual(verdicts(live_run(visibility=resume(host=100_000)))[name], 'PASS')
        self.assertEqual(verdicts(live_run(visibility=resume(host=150_000)))[name], 'FAIL')
        self.assertEqual(verdicts(live_run(visibility=resume(host=100_000))).get('visibility: frame budget the page reports at most 200 ms'), 'PASS')

    def test_a_dropped_backlog_that_replayed_the_hidden_interval_still_fails(self):
        # No backlog remains, but the first frame already holds the hidden seconds.
        name = 'visibility: the 5 s interval does not reach the simulation'
        self.assertEqual(verdicts(live_run(visibility=resume(advanced_us=5_000_000)))[name], 'FAIL')
        self.assertEqual(verdicts(live_run(visibility=resume(advanced_us=250_000)))[name], 'FAIL')
        self.assertEqual(verdicts(live_run(visibility=resume(advanced_us=100_000)))[name], 'PASS')
        stalled = 'stall: the 5 s interval does not reach the simulation'
        self.assertEqual(verdicts(live_run(stall=resume(advanced_us=5_000_000, stall=True)))[stalled], 'FAIL')
        self.assertEqual(verdicts(live_run(stall=resume(advanced_us=200_000, stall=True)))[stalled], 'PASS')

    def test_scene_count_attract_membership_and_duration_are_required(self):
        name = 'at least four attract scenes for at least 20 s'
        self.assertEqual(verdicts(live_run(scenes=[scene(n) for n in check.DEFAULT_SCENES[:3]]))[name], 'FAIL')
        self.assertEqual(verdicts(live_run(scenes=[scene(n, attract=n != 'rain') for n in check.DEFAULT_SCENES]))[name], 'FAIL')
        self.assertEqual(verdicts(live_run(scenes=[scene(n, seconds=4) for n in check.DEFAULT_SCENES]))[name], 'FAIL')

    def test_missing_phase_and_page_errors_fail(self):
        run = live_run(); del run['stall']
        self.assertEqual(verdicts(run)['stall resume measured'], 'FAIL')
        self.assertEqual(verdicts(live_run(errors=['TypeError: boom']))['no browser exceptions'], 'FAIL')

    def test_command_line_refuses_a_smaller_run(self):
        with self.assertRaises(SystemExit):check.main(['--scenes', 'autumn,rain,windows'])
        with self.assertRaises(SystemExit):check.main(['--seconds-per-scene', '4'])


def stand_in_playwright(launch_error=None):
    """sys.modules entries for a playwright.sync_api that holds no browser.

    main() needs only a page that accepts the gallery and answers the build query; everything it
    measures comes from measure(), which the tests replace, so the verdict and the exit status are real."""
    class Page:
        def on(self, event, handler): pass
        def set_content(self, html): pass
        def wait_for_function(self, expression, **options): pass
        def evaluate(self, expression, argument=None): return 'stand-in build'
    class Browser:
        version = 'stand-in browser'
        def new_page(self, **options): return Page()
        def close(self): pass
    class Chromium:
        def launch(self, **options):
            if launch_error:
                raise launch_error
            return Browser()
    class Session:
        chromium = Chromium()
        def __enter__(self): return self
        def __exit__(self, *exception): return False
    api = types.ModuleType('playwright.sync_api'); api.sync_playwright = Session
    package = types.ModuleType('playwright'); package.sync_api = api
    return {'playwright': package, 'playwright.sync_api': api}


def run_main(run, modules=None):
    """check.main() from the command line down with measure() returning `run`: (exit status, printed text, written report)."""
    with tempfile.TemporaryDirectory() as directory:
        gallery, report = Path(directory) / 'gallery.html', Path(directory) / 'report.json'
        gallery.write_text('<!doctype html><title>stand-in gallery</title>')
        printed = io.StringIO()
        with mock.patch.dict(sys.modules, stand_in_playwright() if modules is None else modules), \
                mock.patch.object(check, 'measure', return_value=run), contextlib.redirect_stdout(printed):
            status = check.main(['--gallery', str(gallery), '--output', str(report)])
        return status, printed.getvalue(), json.loads(report.read_text()) if report.exists() else None


class PacingExitStatus(unittest.TestCase):
    """main() maps the verdict to the process exit status: PASS 0, FAIL 2, BLOCKED 3.

    Run through main() itself, not the EXIT_CODES table, so a main() that returned 0 for
    anything not failing or 2 for anything not passing would be caught."""

    def test_a_passing_run_exits_zero(self):
        status, printed, report = run_main(live_run())
        self.assertEqual((status, report['status'], report['passed']), (0, 'PASS', True))
        self.assertNotIn('BLOCKED', printed)

    def test_a_failing_run_exits_two(self):
        # A simulation that runs at 240 steps/s, a frozen one, and a frame rate that failed on a quiet host.
        low = attempt(fps=17.0, load=2.0)
        for name, run in (('fast', live_run(scenes=[at_rate(n, 240) for n in check.DEFAULT_SCENES])),
                          ('frozen', live_run(scenes=[at_rate(n, 0) for n in check.DEFAULT_SCENES])),
                          ('slow on a quiet host', live_run(scenes=low['scenes'], load=low['load'],
                                                            retries=[attempt(fps=17.0, load=2.0), attempt(fps=17.0, load=2.0)]))):
            with self.subTest(run=name):
                status, _, report = run_main(run)
                self.assertEqual((status, report['status'], report['passed']), (2, 'FAIL', False))

    def test_a_blocked_run_exits_three_not_zero_or_two(self):
        # The frame rate alone failed, in every pass, at a measured load of 0.25 per CPU or more.
        low = attempt(fps=20.0, load=5.2)
        run = live_run(scenes=low['scenes'], load=low['load'], retries=[attempt(fps=21.0, load=6.0), attempt(fps=19.0, load=4.0)])
        status, printed, report = run_main(run)
        self.assertEqual((status, report['status'], report['passed']), (3, 'BLOCKED', False))
        self.assertEqual({row['name']: row['status'] for row in report['checks'] if row['status'] != 'PASS'}, {FPS: 'BLOCKED'})
        self.assertIn('BLOCKED host contention', printed)
        self.assertIn('This is not a pass.', printed)

    def test_contention_does_not_turn_a_failure_into_a_blocked_exit(self):
        frozen = attempt(fps=20.0, load=8.0, rate=0)
        status, printed, report = run_main(live_run(scenes=frozen['scenes'], load=frozen['load'],
                                                    retries=[attempt(fps=20.0, load=8.0, rate=0), attempt(fps=20.0, load=8.0, rate=0)]))
        self.assertEqual((status, report['status']), (2, 'FAIL'))
        self.assertNotIn('BLOCKED host contention', printed)

    def test_no_playwright_exits_three_before_any_measurement(self):
        status, printed, report = run_main(live_run(), modules={'playwright': None, 'playwright.sync_api': None})
        self.assertEqual((status, report), (3, None))
        self.assertIn('BLOCKED Playwright unavailable', printed)

    def test_a_chromium_that_cannot_start_exits_three(self):
        status, printed, report = run_main(live_run(), modules=stand_in_playwright(launch_error=RuntimeError('no browser on this host')))
        self.assertEqual((status, report), (3, None))
        self.assertIn('BLOCKED Chromium could not start: no browser on this host', printed)

    def test_the_written_report_carries_the_verdict_and_the_thresholds_it_used(self):
        _, _, report = run_main(live_run())
        self.assertEqual((report['status'], report['passed'], len(report['checks'])), ('PASS', True, 15))
        self.assertEqual({row['status'] for row in report['checks']}, {'PASS'})
        thresholds = report['thresholds']
        self.assertEqual((thresholds['minStepsPerSecond'], thresholds['maxStepsPerSecond']), (check.MIN_STEPS_PER_SECOND, check.MAX_STEPS_PER_SECOND))


class PacingErrorChannelObserver(unittest.TestCase):
    """The #error observer the check installs, in Chromium on a page that holds only <div id="error">.

    A MutationObserver delivers its records when the task that made the mutations ends, so reading the
    box then misses text that was written and cleared inside one task. The check reads the records."""

    @classmethod
    def setUpClass(cls):
        import os
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise AssertionError(f'BLOCKED: Playwright is required to run the error-channel observer in Chromium: {error}') from error
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM') or None, args=['--no-sandbox'])
        except Exception as error:
            cls.playwright.stop()
            raise AssertionError(f'BLOCKED: Chromium could not start for the error-channel observer: {str(error).splitlines()[0]}') from error

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop()

    def page(self, markup='<div id="error"></div>'):
        page = self.browser.new_page(); self.addCleanup(page.close)
        page.set_content('<!doctype html><title>error channel</title>' + markup)
        self.assertTrue(page.evaluate(check.INSTRUMENT))
        return page

    def task(self, page, script):
        """Run `script` as one task, then let the observer's records be delivered."""
        page.evaluate('()=>{const box=document.getElementById("error");' + script + '}')
        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')

    def recorded(self, page):
        return page.evaluate('()=>__pacingCheck.errors.map(entry=>entry.text)')

    def test_text_written_and_cleared_in_one_task_is_recorded(self):
        page = self.page()
        self.task(page, 'box.textContent="mutant: live loop crash";box.textContent="";')
        self.assertEqual(page.evaluate('()=>__pacingCheck.errorText()'), '')   # the end-of-phase read sees an empty box
        self.assertEqual(self.recorded(page), ['mutant: live loop crash'])

    def test_text_that_stays_is_recorded_once(self):
        page = self.page()
        self.task(page, 'box.textContent="mutant: live loop crash";')
        self.assertEqual(page.evaluate('()=>__pacingCheck.errorText()'), 'mutant: live loop crash')
        self.assertEqual(self.recorded(page), ['mutant: live loop crash'])

    def test_nothing_is_recorded_while_nothing_is_written(self):
        page = self.page()
        self.task(page, 'box.textContent="";')   # clearing an empty box writes nothing
        self.assertEqual(self.recorded(page), [])

    def test_writes_in_separate_tasks_are_each_recorded_in_order(self):
        page = self.page()
        self.task(page, 'box.textContent="first";')
        self.task(page, 'box.textContent="";')
        self.task(page, 'box.textContent="second";')
        self.assertEqual(self.recorded(page), ['first', 'second'])
        times = page.evaluate('()=>__pacingCheck.errors.map(entry=>entry.t)')
        self.assertTrue(all(isinstance(t, (int, float)) for t in times) and times == sorted(times))

    def test_markup_written_and_cleared_in_one_task_is_recorded(self):
        page = self.page()
        self.task(page, 'box.innerHTML="<b>mutant: <i>nested</i></b>";box.textContent="";')
        self.assertEqual(self.recorded(page), ['mutant: nested'])

    def test_a_text_node_edited_and_cleared_in_one_task_is_recorded(self):
        page = self.page()
        self.task(page, 'box.textContent="settled";')
        self.task(page, 'const text=box.firstChild;text.data="mutant: transient";text.data="";')
        self.assertIn('mutant: transient', self.recorded(page))
        self.assertEqual(page.evaluate('()=>__pacingCheck.errorText()'), '')

    def test_a_text_node_edit_that_stays_is_recorded(self):
        page = self.page()
        self.task(page, 'box.textContent="settled";')
        self.task(page, 'box.firstChild.data="mutant: edited";')
        self.assertIn('mutant: edited', self.recorded(page))

    def test_a_long_message_is_cut_to_400_characters(self):
        page = self.page()
        self.task(page, 'box.textContent="x".repeat(1000);')
        self.assertEqual([len(text) for text in self.recorded(page)], [400])

    def test_text_already_in_the_box_when_the_check_starts_is_recorded(self):
        page = self.page('<div id="error">already failed</div>')
        self.assertEqual(self.recorded(page), ['already failed'])

    def test_a_page_without_the_box_records_nothing(self):
        page = self.page('')
        self.assertIsNone(page.evaluate('()=>__pacingCheck.errorText()'))
        self.assertEqual(self.recorded(page), [])

    def test_what_the_observer_records_fails_the_error_channel_assertion(self):
        # From the page to the verdict: the box is empty at the end of every phase, the message was still written.
        page = self.page()
        self.task(page, 'box.textContent="mutant: live loop crash";box.textContent="";')
        entries = page.evaluate('()=>__pacingCheck.errors')
        run = live_run(errorChannel=entries)
        self.assertIn(ERROR_CHANNEL, failing(run))
        detail = next(row['detail'] for row in check.evaluate(run) if row['name'] == ERROR_CHANNEL)
        self.assertIn('mutant: live loop crash', detail)
        quiet = self.page().evaluate('()=>__pacingCheck.errors')
        self.assertEqual(verdicts(live_run(errorChannel=quiet)).get(ERROR_CHANNEL), 'PASS')


# The template's own live pacing code, run in Node against the real WASM core. Taken verbatim from
# native/web/template.html: the live pacing block (from "// Live pacing" through its visibilitychange
# handler), the pacing state, budgetedTime(), advancePearlTo(), applyAutoActions() and tick(). Only
# presentation is replaced (draw, sync and the DOM); performance.now() is a clock the scenario moves,
# so frame times are exact, and a scenario may charge each native time command a cost on that clock.
LIVE_HARNESS = r"""
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const template=readFileSync(process.env.PACING_TEMPLATE,'utf8'),native=process.env.PACING_NATIVE,lines=template.split('\n');
const {NativeScene}=await import(pathToFileURL(native+'/bindings/typescript/native_scene.mjs').href);
const wasm=readFileSync(native+'/dist/nocturne_native.wasm'),recipes=JSON.parse(readFileSync(native+'/recipes.json','utf8'));
const balance=s=>[...s].reduce((d,c)=>d+(c==='{')-(c==='}'),0);
function definition(prefix){const i=lines.findIndex(l=>l.startsWith(prefix));if(i<0)throw Error('template lacks '+prefix);
 if(balance(lines[i])===0)return lines[i];const end=lines.findIndex((l,j)=>j>i&&l==='}');if(end<0)throw Error('unterminated '+prefix);return lines.slice(i,end+1).join('\n');}
function block(){const i=lines.findIndex(l=>l.startsWith('// Live pacing')),j=lines.findIndex((l,k)=>k>i&&l.startsWith("document.addEventListener('visibilitychange'"));
 if(i<0||j<0)throw Error('template lacks the live pacing block');return lines.slice(i,j+1).join('\n');}
function tick(){const line=lines.find(l=>l.includes('function tick(now){'));if(!line)throw Error('template lacks tick()');const s=line.indexOf('function tick(now){');let d=0;
 for(let i=line.indexOf('{',s);i<line.length;i++){if(line[i]==='{')d++;else if(line[i]==='}'&&--d===0)return line.slice(s,i+1);}throw Error('unbalanced tick()');}
const source=[definition('const pacing='),definition('function budgetedTime('),definition('function advancePearlTo('),definition('function applyAutoActions('),block(),tick()].join('\n');
const body=`let active=recipe,logicalUs=0,running=true,lastWall=performance.now(),pearlSession=null,projectEditor=null,scenicSession=null,pearlSource=null,autoActions=[],nextAutoAction=0;
let attractEnabled=false,attractDeadline=Infinity,attractRotation=null,fps=60,lastPaint=0,lastSync=0,lastFrame=null;const window={},errors=[];
function draw(){}function sync(){}function report(e){errors.push(String(e?.message??e));}function requestAnimationFrame(){}function act(fn){fn();}function load(){}
function showMetadataRefusal(info){refusals.push(info.error);running=false;}function applyScriptAction(){throw Error('no autoActions here');}function syncPearlControls(){}function updatePearlSource(){}
${source}
return {pacing,tick,liveAccrue,liveAdvance,liveBudget,budgetedTime,livePacing,liveMetrics,liveClockUs,errors,
 get logicalUs(){return logicalUs;},set logicalUs(v){logicalUs=v;},get running(){return running;},set running(v){running=v;},get lastWall(){return lastWall;},set lastWall(v){lastWall=v;}};`;
async function page(recipe,cost=null){
 const scene=await NativeScene.create(wasm,2030),drain=c=>{let r=scene.command(c);while(r===1)r=scene.command(c);};
 for(const c of recipe.commands)drain(c);drain({op:'pause',paused:false});
 const time={now:1000},performance={now:()=>time.now},listeners=[],document={hidden:false,addEventListener:(type,fn)=>{if(type==='visibilitychange')listeners.push(fn);}},refusals=[];
 const clock=()=>{const info=scene.info();return info.error?null:info.clock;},step=()=>clock()?.step??null;
 if(cost){const command=scene.command.bind(scene);scene.command=c=>{const before=c.op==='time'?step():0,r=command(c);if(c.op==='time')time.now+=cost(step()-before);return r;};}
 const api=new Function('recipe','scene','performance','document','refusals',body)(recipe,scene,performance,document,refusals);
 const frame=(ms=1000/60)=>{const before=step();time.now+=ms;api.tick(time.now);const after=step();return {budget:api.liveBudget(),steps:before===null||after===null?null:after-before};};
 const visibility=hidden=>{document.hidden=hidden;for(const fn of listeners)fn();};
 return {api,scene,time,frame,step,clock,visibility,refusals};}
const frames=(p,n,ms)=>Array.from({length:n},(_,i)=>p.frame(typeof ms==='function'?ms(i):ms));
// Frame intervals of 10-59 ms, so frames ask for 1-7 steps and a step-cost estimate has spread to learn from.
const varied=i=>10+(i*7)%50;
const rain=recipes.find(r=>r.id==='rain'),out={};
{const p=await page(rain,k=>6+.1*k);const f=frames(p,90,varied);out.healthy={first:f[0].budget,budgets:[...new Set(f.map(r=>r.budget))]};}
{const p=await page(rain,k=>20+4*k);const f=frames(p,90,varied);out.overrun={first:f[0].budget,budgets:[...new Set(f.map(r=>r.budget))]};}
{const p=await page(rain);const f=frames(p,30);out.stall={budget:p.api.liveBudget(),perFrame:[...new Set(f.map(r=>r.steps))],gap:p.frame(1000).steps,next:p.frame().steps};}
out.authored={};
for(const budget of [1,12,60]){const p=await page({...rain,frameBudget:budget});const f=frames(p,30);out.authored[budget]={budgets:[...new Set(f.map(r=>r.budget))],perFrame:[...new Set(f.map(r=>r.steps))],gap:p.frame(1000).steps};}
// nativeLab.budgetedTime() from a fresh scene: the one bounded call each painted frame makes.
out.helper={};
for(const budget of [undefined,1,12,60]){const p=await page(budget===undefined?rain:{...rain,frameBudget:budget});const code=p.api.budgetedTime(500000),clock=p.scene.info().clock;
 out.helper[budget??'default']={code,step:clock.step,timeUs:clock.timeUs,targetUs:clock.targetUs,budget:p.api.liveBudget()};}
// Accounting: every visible, running millisecond is either simulated (logicalUs) or counted behind.
{const p=await page(rain),wall=[],start=p.api.logicalUs;const go=ms=>{wall.push(ms);return p.frame(ms);};
 for(let i=0;i<30;i++)go(1000/60);const before=p.api.pacing.behindUs;const gap=go(1000);for(let i=0;i<5;i++)go(300);for(let i=0;i<10;i++)go(1000/60);
 out.behind={droppedUs:p.api.pacing.droppedUs??null,behindBefore:before,behindAfterGap:null,behindUs:p.api.pacing.behindUs,gapSteps:gap.steps,
  logicalUs:p.api.logicalUs-start,wallUs:wall.reduce((a,b)=>a+b,0)*1000,backlogUs:p.api.logicalUs-p.clock().timeUs,metrics:p.api.liveMetrics(p.scene.info()),pacing:p.api.livePacing()};}
// Hidden: visibilitychange to hidden, 5 s with requestAnimationFrame withheld, visible again.
{const p=await page(rain);for(let i=0;i<20;i++)p.frame();const behind=p.api.pacing.behindUs,stepHidden=p.step();
 p.visibility(true);p.time.now+=5000;p.visibility(false);const first=p.frame(),rest=[p.frame(),p.frame()];
 // A browser that still ticks a hidden page (rAF at 1 Hz): those intervals are hidden time too, not simulated.
 p.visibility(true);const hiddenTicks=[p.frame(1000),p.frame(1000)];p.visibility(false);p.frame();
 out.hidden={hiddenUs:p.api.pacing.hiddenUs??null,behindChange:p.api.pacing.behindUs-behind,firstSteps:first.steps,restSteps:rest.map(r=>r.steps),hiddenTickSteps:hiddenTicks.map(r=>r.steps),
  stepWhileHidden:stepHidden,pacing:p.api.livePacing()};}
// An external clock change (load(), reset(), seek) is not counted as behind and restarts the accounting.
{const p=await page(rain);for(let i=0;i<30;i++)p.frame();const behind=p.api.pacing.behindUs;
 p.scene.command({op:'reset',seed:2030});for(const c of rain.commands){let r=p.scene.command(c);while(r===1)r=p.scene.command(c);}p.scene.command({op:'pause',paused:false});p.api.logicalUs=0;
 const after=Array.from({length:6},()=>p.frame());out.reset={behindChange:p.api.pacing.behindUs-behind,steps:after.map(r=>r.steps),timeUs:p.clock().timeUs,logicalUs:p.api.logicalUs};}
// A target more than one budget ahead (a partial native call): the clock is read and the excess counted behind.
{const p=await page(rain);for(let i=0;i<10;i++)p.frame();const behind=p.api.pacing.behindUs;p.api.logicalUs+=1000000;const f=p.frame(),limit=p.api.liveBudget()*1000000/120;
 out.partial={steps:f.steps,behindChange:p.api.pacing.behindUs-behind,backlogUs:p.api.logicalUs-p.clock().timeUs,limit,errors:p.api.errors.slice()};}
// The same partial frame while the bounded metadata view is refused: no TypeError replaces the refusal.
{const p=await page(rain);for(let i=0;i<10;i++)p.frame();
 for(let i=1;i<=24;i++)p.scene.command({op:'text',id:i,text:'\u{1F642}'.repeat(2048)});p.scene.command({op:'draft',text:'\u754C'.repeat(300000),emitWeather:false});
 const refused=p.scene.info().error??null,pacing=p.api.livePacing(),beforeRefusals=p.refusals.length;p.api.logicalUs+=1000000;p.frame();
 out.metadata={refused,pacingBacklog:pacing.backlogUs,refusalsFromPacing:beforeRefusals,refusals:p.refusals.slice(),errors:p.api.errors.slice(),running:p.api.running};}
console.log(JSON.stringify(out));
"""


class TemplateLivePacing(unittest.TestCase):
    """The template's live loop (tick, liveAccrue, liveAdvance, budgetedTime) on the real WASM core in Node."""

    @classmethod
    def setUpClass(cls):
        import os, shutil, subprocess
        template = Path(os.environ.get('NOCTURNE_PACING_TEMPLATE', NATIVE / 'web/template.html'))
        node = os.environ.get('NODE') or shutil.which('node')
        if not node:
            raise AssertionError('BLOCKED: Node is required to execute the template pacing code')
        if not (NATIVE / 'dist/nocturne_native.wasm').is_file():
            raise AssertionError('BLOCKED: build native/dist/nocturne_native.wasm first (sh build-native.sh)')
        result = subprocess.run([node, '--input-type=module', '-e', LIVE_HARNESS], capture_output=True, text=True, timeout=300,
                                env={**os.environ, 'PACING_TEMPLATE': str(template), 'PACING_NATIVE': str(NATIVE)})
        if result.returncode:
            raise AssertionError(result.stderr[-2000:])
        cls.out = json.loads(result.stdout)

    def test_the_default_budget_is_24_steps_from_the_first_frame(self):
        # Fixed policy: no estimator, so a healthy host never shrinks the budget (review: 10-22 at load 5).
        healthy = self.out['healthy']
        self.assertEqual((healthy['first'], healthy['budgets']), (24, [24]))

    def test_slow_native_calls_never_change_the_budget(self):
        # 20 ms per call plus 4 ms per step: the removed estimator shrank the budget toward 4.
        self.assertEqual((self.out['overrun']['first'], self.out['overrun']['budgets']), (24, [24]))

    def test_a_long_frame_advances_exactly_one_budget(self):
        stall = self.out['stall']
        self.assertEqual(stall['perFrame'], [2])   # 60 Hz frames at the fixed 120 Hz step
        self.assertEqual((stall['budget'], stall['gap']), (24, 24))
        self.assertEqual(stall['next'], 2)   # the excess is not replayed on the next frame

    def test_budgeted_time_is_the_live_call_and_uses_the_live_budget(self):
        # One helper: the browser clock guards call nativeLab.budgetedTime(), so it must be the call
        # every painted frame makes, with the same budget (previously a retained 12-step helper).
        for name, row in self.out['helper'].items():
            with self.subTest(frameBudget=name):
                steps = min(row['budget'], 60)
                self.assertEqual(row['budget'], 24 if name == 'default' else int(name))
                self.assertEqual((row['step'], row['targetUs']), (steps, 500_000))
                self.assertEqual(row['timeUs'], 500_000 if steps == 60 else steps * 1_000_000 // 120)
                self.assertEqual(row['code'], 0 if steps == 60 else 1)
        import os
        template = Path(os.environ.get('NOCTURNE_PACING_TEMPLATE', NATIVE / 'web/template.html')).read_text().split('\n')
        advance = [line for line in template if line.startswith('function liveAdvance(')]
        self.assertEqual(len(advance), 1)
        self.assertIn('budgetedTime(target)', advance[0])
        self.assertNotIn('advancePearlTo(', advance[0])

    def test_every_visible_running_millisecond_is_simulated_or_counted_behind(self):
        behind = self.out['behind']
        self.assertIsNone(behind['droppedUs'])   # reported as behind: the simulation is behind, nothing is dropped
        self.assertEqual(behind['gapSteps'], 24)
        # 1000 ms frame: 200 ms simulated, 800 ms behind; five 300 ms frames: 100 ms behind each.
        self.assertAlmostEqual(behind['behindUs'] - behind['behindBefore'], 800_000 + 5 * 100_000, delta=2)
        self.assertAlmostEqual(behind['logicalUs'] + behind['behindUs'], behind['wallUs'], delta=2)
        self.assertLessEqual(behind['backlogUs'], 24 * 1_000_000 / 120)
        self.assertEqual(behind['pacing']['behindUs'], behind['behindUs'])
        self.assertIn('behindMsPerSecond', behind['pacing']); self.assertNotIn('droppedUs', behind['pacing'])
        self.assertIn('behind', behind['metrics']); self.assertNotIn('dropped', behind['metrics'])

    def test_hidden_time_is_counted_separately_and_never_simulated(self):
        hidden = self.out['hidden']
        self.assertAlmostEqual(hidden['hiddenUs'], 5_000_000 + 2 * 1_000_000, delta=2)
        self.assertEqual(hidden['behindChange'], 0)
        self.assertLessEqual(hidden['firstSteps'], 2)   # the 5 s hidden interval is not replayed
        self.assertEqual(hidden['restSteps'], [2, 2])
        self.assertEqual(hidden['hiddenTickSteps'], [0, 0])
        self.assertEqual(hidden['pacing']['hiddenUs'], hidden['hiddenUs'])

    def test_an_external_clock_change_restarts_the_accounting(self):
        reset = self.out['reset']
        self.assertEqual(reset['behindChange'], 0)
        self.assertEqual(reset['steps'][1:], [2] * 5)
        self.assertLessEqual(reset['logicalUs'] - reset['timeUs'], 1)

    def test_a_partial_native_call_counts_the_excess_behind(self):
        partial = self.out['partial']
        self.assertEqual((partial['steps'], partial['errors']), (24, []))
        self.assertLessEqual(partial['backlogUs'], partial['limit'] + 1)
        self.assertGreater(partial['behindChange'], 500_000)

    def test_a_metadata_refusal_during_a_partial_frame_is_not_replaced_by_a_type_error(self):
        metadata = self.out['metadata']
        self.assertEqual(metadata['refused'], 'metadata capacity exceeded')
        self.assertIsNone(metadata['pacingBacklog']); self.assertEqual(metadata['refusalsFromPacing'], 0)
        self.assertEqual(metadata['errors'], [])
        self.assertEqual(metadata['refusals'], ['metadata capacity exceeded'])
        self.assertFalse(metadata['running'])

    def test_the_metrics_line_leads_with_the_simulation_rate_and_lag(self):
        # At 760 px and below .stage .metrics shows one line; the live figures must be on it.
        import os
        template = Path(os.environ.get('NOCTURNE_PACING_TEMPLATE', NATIVE / 'web/template.html')).read_text()
        self.assertIn("setText('metrics',`${liveMetrics(info)}  |  C/WASM ${renderMs.toFixed(2)} ms + ${paintMode} paint", template)
        self.assertTrue(self.out['behind']['metrics'].startswith(tuple(f'{n} of 120 steps/s, behind' for n in range(0, 200))), self.out['behind']['metrics'])

    def test_authored_frame_budgets_are_used_exactly(self):
        for budget, row in self.out['authored'].items():
            with self.subTest(frameBudget=budget):
                self.assertEqual(row['budgets'], [int(budget)])
                self.assertEqual(row['gap'], int(budget))
                self.assertLessEqual(max(row['perFrame']), int(budget))


class PacingRegistration(unittest.TestCase):
    def test_rc2_plan_runs_the_check_as_a_browser_step_beside_rc2_browser(self):
        full = [(name, ['true']) for name in plan.REQUIRED_CASE_IDS]
        selected = plan.select_rc2_plan(full, python=sys.executable, native_root=NATIVE)
        names = [row[0] for row in selected]
        self.assertIn('rc2-gallery-pacing', names)
        self.assertEqual(names.index('rc2-gallery-pacing'), names.index('rc2-browser') + 1)
        self.assertEqual(selected[names.index('rc2-gallery-pacing')], ('rc2-gallery-pacing', [sys.executable, 'scripts/check_gallery_pacing.py']))
        self.assertIn('test_gallery_pacing_check', selected[names.index('rc2-native')][1])

    def test_rc2_plan_refuses_a_missing_pacing_check(self):
        # Discover the plan's required sources by its own refusals, then remove only the check.
        import tempfile
        full = [(name, ['true']) for name in plan.REQUIRED_CASE_IDS]
        with tempfile.TemporaryDirectory() as directory:
            root, created = Path(directory), []
            for _ in range(200):
                try:
                    plan.select_rc2_plan(full, native_root=root); break
                except FileNotFoundError as missing:
                    path = Path(missing.args[0]); path.parent.mkdir(parents=True, exist_ok=True); path.touch()
                    created.append(path.relative_to(root).as_posix())
            self.assertIn('scripts/check_gallery_pacing.py', created)
            (root / 'scripts/check_gallery_pacing.py').unlink()
            with self.assertRaises(FileNotFoundError):
                plan.select_rc2_plan(full, native_root=root)


if __name__ == '__main__':
    unittest.main()
