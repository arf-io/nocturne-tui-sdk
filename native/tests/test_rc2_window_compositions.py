"""Word-exact original RC2 spatial-window body compositor regressions."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / 'bindings/python'))
sys.path.insert(0, str(ROOT / 'examples'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench
from rc2_window_studies import build_rc2_window_studies

WIDTH, HEIGHT = 136, 44
WINDOW_ID_TAG = 0x20000000
SOURCE_EFFECTS = (
    'fade', 'bounce', 'genie', 'roll-up', 'roll-down', 'drawer-left',
    'drawer-right', 'drawer-top', 'drawer-bottom', 'center', 'top-left',
    'top-right', 'bottom-left', 'bottom-right', 'iris', 'explosion',
    'accordion', 'portal', 'orbital-bloom', 'venetian', 'ribbon-unfurl',
)


def original_runtime_source():
    from native.tests.presentation_copy_reference import current_presentation
    source = current_presentation(load_rc2_workbench(), "kinetic")
    anchor = 'return {KineticRenderer,hitKinetic,activateKinetic};'
    if source.count(anchor) != 1:
        raise AssertionError('Pinned RC2 Kinetic renderer export anchor changed')
    exports = ('window.__rc2WindowComposition={KineticRenderer,KineticModel,'
               'DEFAULT_OBSERVATORY_OPTIONS,WINDOW_EFFECTS};' + anchor)
    return source.replace(anchor, exports, 1)


def expected_ids():
    ids = {f'rc2-{scene}-{mode}'
           for scene in ('windows', 'shapes')
           for mode in ('isolated', 'application')}
    ids.update(f'rc2-window-{effect}-{mode}'
               for effect in SOURCE_EFFECTS
               for mode in ('isolated', 'application'))
    return ids


def validate_studies(studies):
    if not isinstance(studies, list) or len(studies) != 46:
        raise AssertionError('RC2 composition catalog must contain 46 studies')
    by_id = {}
    for case in studies:
        if not isinstance(case, dict) or type(case.get('id')) is not str:
            raise AssertionError('Malformed RC2 composition study')
        if case['id'] in by_id:
            raise AssertionError(f"Duplicate RC2 composition study {case['id']}")
        by_id[case['id']] = case
        if case.get('mode') not in ('isolated', 'application'):
            raise AssertionError(f"{case['id']}: invalid mode")
        if case.get('originalScene') not in ('windows', 'shapes'):
            raise AssertionError(f"{case['id']}: invalid source scene")
        if not isinstance(case.get('provenance'), dict) or not case['provenance']:
            raise AssertionError(f"{case['id']}: source provenance is required")
        if not isinstance(case.get('commands'), list) or not case['commands']:
            raise AssertionError(f"{case['id']}: commands are required")
        if not isinstance(case.get('actions'), list):
            raise AssertionError(f"{case['id']}: actions must be a list")
        if any(not isinstance(a, dict) or type(a.get('timeUs')) is not int
               or a['timeUs'] < 0 or not isinstance(a.get('command'), dict)
               for a in case['actions']):
            raise AssertionError(f"{case['id']}: malformed timed action")
        action_times = [a['timeUs'] for a in case['actions']]
        if action_times != sorted(action_times):
            raise AssertionError(f"{case['id']}: timed actions must be chronological")
        times = case.get('sampleTimesUs')
        if (not isinstance(times, list) or not times
                or any(type(t) is not int or t < 0 for t in times)
                or times != sorted(set(times))):
            raise AssertionError(f"{case['id']}: malformed sample times")
    if set(by_id) != expected_ids():
        missing, unexpected = expected_ids() - set(by_id), set(by_id) - expected_ids()
        raise AssertionError(f'RC2 study ID mismatch; missing={sorted(missing)}, '
                             f'unexpected={sorted(unexpected)}')
    for scene in ('windows', 'shapes'):
        for mode in ('isolated', 'application'):
            case = by_id[f'rc2-{scene}-{mode}']
            if case.get('originalEffect') is not None:
                raise AssertionError(f"{case['id']}: preset must not invent an effect")
            if case['sampleTimesUs'] != [0, 425000, 1700000]:
                raise AssertionError(f"{case['id']}: incomplete preset sample schedule")
            if case['originalScene'] != scene:
                raise AssertionError(f"{case['id']}: preset scene mismatch")
    for effect in SOURCE_EFFECTS:
        for mode in ('isolated', 'application'):
            case = by_id[f'rc2-window-{effect}-{mode}']
            if case.get('originalEffect') != effect or case['originalScene'] != 'windows':
                raise AssertionError(f"{case['id']}: source effect mapping mismatch")
            if case['sampleTimesUs'] != [1425000, 3425000]:
                raise AssertionError(f"{case['id']}: samples must cover minimize and restore")
            actions = [(a['timeUs'], a['command'].get('action'))
                       for a in case['actions']
                       if a['command'].get('op') == 'window-action']
            if actions != [(1000000, 'minimize'), (3000000, 'restore')]:
                raise AssertionError(f"{case['id']}: source Pearl action schedule mismatch")
    return by_id


def baseline_commands(case):
    """Keep the exact scene/actions while suppressing only generated body alpha."""
    commands = copy.deepcopy(case['commands'])
    changed = 0
    for command in commands:
        if command.get('op') == 'window' and command.get('sourcePresentation') is True:
            command['alpha'] = 0
            changed += 1
    if changed != 3:
        raise AssertionError(f"{case['id']}: expected three source window body commands, got {changed}")
    return commands


def apply_until(scene, actions, sample_time, applied):
    for index, action in enumerate(actions):
        if index in applied or action['timeUs'] > sample_time:
            continue
        scene.advance_to(action['timeUs'])
        scene.command(action['command'])
        applied.add(index)
    scene.advance_to(sample_time)


def packed_words(scene):
    frame = scene.render()
    words = list(memoryview(frame.bytes).cast('I'))
    if len(words) != WIDTH * HEIGHT * 4:
        raise AssertionError(f'Unexpected native frame word count: {len(words)}')
    return words


def assert_packed_equal(test, expected, actual, context):
    test.assertEqual(len(actual), len(expected), f'{context}: frame truncation')
    differences = [(i, expected[i], actual[i])
                   for i in range(len(expected)) if expected[i] != actual[i]]
    test.assertEqual(len(differences), 0,
                     f'{context}: {len(differences)} packed-word differences; '
                     f'first differences (word, expected, actual)={differences[:16]}')


def capture_comparison(case, sample_time, original, native, baseline):
    destination = os.environ.get('NOCTURNE_RC2_WINDOW_CAPTURE_DIR')
    if not destination:
        return
    directory = Path(destination)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{case['id']}-{sample_time}.json"
    path.write_text(json.dumps({
        'id': case['id'], 'timeUs': sample_time, 'width': WIDTH, 'height': HEIGHT,
        'original': original['words'], 'native': native, 'baseline': baseline,
    }, separators=(',', ':')))


def browser_original_frame(page, case, sample_time, baseline):
    return page.evaluate('''input => {
      const api=window.__rc2WindowComposition;
      if(!api || !window.fieldGuide) throw new Error('Original RC2 runtime is unavailable');
      const model=new api.KineticModel();
      model.resize(input.width,input.height);
      model.setScene(input.scene);
      model.spaceWindows.configure({effect:input.effect??model.spaceWindows.options.effect,
                                    durationMs:850});
      for(const action of input.actions){
        if(action.timeUs>input.timeUs) continue;
        const c=action.command;
        if(c.op==='window-action'){
          if(c.action!=='minimize' && c.action!=='restore') throw new Error('Unexpected source window action');
          model.spaceWindows.act('pearl',c.action,action.timeUs/1000);
        }
      }
      model.setTime(input.timeUs/1000);
      const renderer=new api.KineticRenderer(window.fieldGuide.engine);
      const options=model.effective(input.timeUs/1000);
      renderer.base.prepare(model.palette,options);
      const frame={width:input.width,height:input.height,cells:Uint32Array.from(input.baseline)};
      renderer.windows(frame,model,options);
      const ids=new Map(model.spaceWindows.list().map((w,i)=>[15000+i,0x20000000|(i+1)]));
      for(let i=3;i<frame.cells.length;i+=4) if(ids.has(frame.cells[i])) frame.cells[i]=ids.get(frame.cells[i]);
      return {words:Array.from(frame.cells),scene:model.scene,dimensions:[model.width,model.height],
        camera:model.camera.snapshot(),palette:model.palette,waveform:model.waveform,
        windowOptions:model.spaceWindows.options,selectedWindow:model.spaceWindows.selected,
        windows:model.spaceWindows.list().map(w=>({id:w.id,title:w.title,x:w.x,y:w.y,z:w.z,
          width:w.width,height:w.height,yaw:w.yaw,pitch:w.pitch,roll:w.roll,shape:w.shape??null,content:w.content}))};
    }''', {
        'scene': case['originalScene'], 'effect': case.get('originalEffect'),
        'actions': case['actions'], 'timeUs': sample_time,
        'width': WIDTH, 'height': HEIGHT, 'baseline': baseline,
    })


class RC2WindowCompositions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright

        cls.studies = validate_studies(build_rc2_window_studies())
        cls.source_presets = json.loads((ROOT / 'examples/rc2_window_presets.json').read_text())
        cls.source = original_runtime_source()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, args=['--no-sandbox'])
        cls.page = cls.browser.new_page()
        cls.page.set_content(cls.source, wait_until='domcontentloaded')
        cls.page.wait_for_function('window.fieldGuide && window.__rc2WindowComposition')
        effects = cls.page.evaluate('window.__rc2WindowComposition.WINDOW_EFFECTS')
        if effects != list(SOURCE_EFFECTS):
            raise AssertionError('Pinned original RC2 window effect list changed')

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'browser', None):
            cls.browser.close()
        if getattr(cls, 'playwright', None):
            cls.playwright.stop()

    def test_study_catalog_and_packed_frame_reject_incomplete_inputs(self):
        studies = build_rc2_window_studies()
        with self.assertRaisesRegex(AssertionError, '46 studies'):
            validate_studies(studies[:-1])
        duplicate = copy.deepcopy(studies)
        duplicate[-1] = copy.deepcopy(duplicate[0])
        with self.assertRaisesRegex(AssertionError, 'Duplicate'):
            validate_studies(duplicate)
        case = copy.deepcopy(studies[0])
        case['sampleTimesUs'] = [0, 0]
        malformed = [c for c in studies if c['id'] != case['id']] + [case]
        with self.assertRaisesRegex(AssertionError, 'sample times'):
            validate_studies(malformed)
        bad_provenance = copy.deepcopy(studies)
        bad_provenance[0]['provenance'] = []
        with self.assertRaisesRegex(AssertionError, 'provenance'):
            validate_studies(bad_provenance)
        bad_scene = copy.deepcopy(studies)
        bad_scene[0]['originalScene'] = 'windows-ish'
        with self.assertRaisesRegex(AssertionError, 'source scene'):
            validate_studies(bad_scene)
        with self.assertRaisesRegex(AssertionError, 'frame truncation'):
            assert_packed_equal(self, [1, 2], [1], 'negative frame')
        with self.assertRaisesRegex(AssertionError, 'packed-word differences'):
            assert_packed_equal(self, [1, 2], [1, 3], 'negative frame')

    def assert_original_source_defaults(self, original, scene):
        expected = self.source_presets['scenes'][scene]
        self.assertEqual(original['scene'], scene)
        self.assertEqual(original['dimensions'], [expected['width'], expected['height']])
        self.assertEqual(original['camera'], expected['camera'])
        self.assertEqual(original['selectedWindow'], expected['selected'])
        self.assertEqual([w['id'] for w in original['windows']], ['pearl', 'atlas', 'iris'])
        for actual, source in zip(original['windows'], expected['windows']):
            for field in ('id', 'title', 'content', 'x', 'y', 'z', 'width', 'height',
                          'yaw', 'pitch', 'roll'):
                self.assertEqual(actual[field], source[field],
                                 f"{scene}/{source['id']} source {field}")
            self.assertEqual(actual['shape'], source.get('shape'))
        self.assertEqual(original['palette'], expected['palette'])
        self.assertEqual(original['waveform'], expected['waveform'])

    def test_current_native_and_wasm_match_original_window_bodies_exactly(self):
        requests = []
        receipts = []
        for study_id in sorted(self.studies):
            case = self.studies[study_id]
            visible = NativeScene(2030)
            baseline = None
            try:
                baseline = NativeScene(2030)
                for command in case['commands']:
                    visible.command(command)
                baseline_commands_for_case = baseline_commands(case)
                for command in baseline_commands_for_case:
                    baseline.command(command)
                visible_actions, baseline_actions = set(), set()
                requests.append({'id': study_id, 'commands': case['commands'],
                                 'baselineCommands': baseline_commands_for_case,
                                 'actions': case['actions'], 'sampleTimesUs': case['sampleTimesUs']})
                for sample_time in case['sampleTimesUs']:
                    apply_until(visible, case['actions'], sample_time, visible_actions)
                    apply_until(baseline, case['actions'], sample_time, baseline_actions)
                    before = visible.snapshot()
                    native_words = packed_words(visible)
                    self.assertEqual(visible.snapshot(), before,
                                     f'{study_id} render changed retained state')
                    baseline_words = packed_words(baseline)
                    original = browser_original_frame(self.page, case, sample_time, baseline_words)
                    capture_comparison(case, sample_time, original, native_words, baseline_words)
                    with self.subTest(study=study_id, timeUs=sample_time):
                        self.assert_original_source_defaults(original, case['originalScene'])
                        expected_options = dict(self.source_presets['scenes'][case['originalScene']]['appearance'])
                        if case.get('originalEffect') is not None:
                            expected_options['effect'] = case['originalEffect']
                        self.assertEqual(original['windowOptions'], expected_options,
                                         f'{study_id}: original source effect defaults')
                        expected = original['words']
                        assert_packed_equal(self, expected, native_words,
                                            f'{study_id}@{sample_time} original/native')
                    receipts.append({'id': study_id, 'timeUs': sample_time,
                                     'baseline': baseline_words, 'words': native_words})
            finally:
                if baseline is not None:
                    baseline.close()
                visible.close()

        with tempfile.TemporaryDirectory(prefix='nocturne-rc2-window-') as directory:
            request = Path(directory) / 'request.json'
            response = Path(directory) / 'response.json'
            request.write_text(json.dumps(requests, separators=(',', ':')))
            process = subprocess.run(
                ['node', str(ROOT / 'tests/rc2_window_compositions_wasm_runner.mjs'),
                 str(request), str(response)], check=False, timeout=180,
                capture_output=True, text=True)
            self.assertEqual(process.returncode, 0,
                             f'Production Wasm comparison runner failed: {process.stderr[-4000:]}')
            wasm = json.loads(response.read_text())
        self.assertEqual(len(wasm), len(receipts), 'Wasm comparison frame count')
        for actual, expected in zip(wasm, receipts):
            key = f"{expected['id']}@{expected['timeUs']}"
            with self.subTest(study=expected['id'], timeUs=expected['timeUs'], target='wasm'):
                self.assertEqual(actual.get('id'), expected['id'], f'{key}: Wasm study identity')
                self.assertEqual(actual.get('timeUs'), expected['timeUs'], f'{key}: Wasm sample time')
                assert_packed_equal(self, expected['baseline'], actual['baseline'],
                                    f'{key} baseline native/Wasm')
                assert_packed_equal(self, expected['words'], actual['words'],
                                    f'{key} native/Wasm')
