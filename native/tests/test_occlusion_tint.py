"""Occlusion tint and occluded dots: scene-wide environment controls over hidden braille-family particles.

A terminal cell holds one glyph, one foreground and one background. Under braille sampling the nearest
particle owns the cell's dots; particles hidden behind it have, until now, always been blended into the
cell background, so a dense pile reads as solid cell-sized squares. Two `environment` controls let the
author choose the look:

  occlusionTint  0..1, default 1. How strongly hidden braille-family particles tint the background.
                 1 keeps every existing frame; 0 shows only the scene behind them.
  occludedDots   "hidden" (default) keeps occlusion real; "merge" lets hidden particles add their dots.

Oracles, all recorded from real runs (tests/fixtures/occlusion-tint/frames.json):
  * every recipe frame at 2 s and 30 s from the base build 0edf36f8, before these controls existed;
  * the two render prototypes on concern/braille-occlusion-merge-prototype-20261114 (59a8f067 merge,
    05c70131 tint), built and run with their environment switches, for every frame they change;
  * a genuine schema-0x20261096 snapshot written by the base build (fixtures/occlusion-tint/schema96).
Everything below executes the real native library; nothing is mocked.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(NATIVE / 'bindings/python'))
from nocturne_native import NativeScene  # noqa: E402
from native.tests.current_writer_contract import current_schema  # noqa: E402
from native.tests.constructed_dynamic_legacy_snapshot import layout  # noqa: E402

FIXTURE = NATIVE / 'tests/fixtures/occlusion-tint'
FRAMES = json.loads((FIXTURE / 'frames.json').read_text())
RECIPES = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
AUTUMN_30 = 'autumn@30000000'
# Base build 0edf36f8, autumn at 30 s, 160x48, seed 2030: the frame before these controls existed.
AUTUMN_30_BASE_SHA256 = '4b483eb25bf37341a126d12315df83f444da7d4d964c17b4f0d4bed933c193ed'


def saturation(rgb):
    channels = ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
    return max(channels) - min(channels)


def counts(frame):
    words = frame.words()
    return (sum(1 for _, _, background, _ in words if saturation(background) > 40),
            sum(1 for glyph, *_ in words if 0x2800 <= glyph <= 0x28ff))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_all(scene, commands):
    for command in commands:
        while scene.command(command) == 1:
            pass


def recipe_scene(recipe_id, extra=(), seed=2030):
    scene = NativeScene(seed=seed)
    scene.command({'op': 'resize', 'width': 160, 'height': 48})
    run_all(scene, RECIPES[recipe_id]['commands'])
    run_all(scene, extra)
    return scene


def recipe_frame(key, extra=()):
    recipe_id, time_us = key.split('@')
    with recipe_scene(recipe_id, extra) as scene:
        scene.advance_to(int(time_us))
        return scene.render()


def control_offset():
    """Snapshot byte offset of the retained occlusion controls, from the compiled State layout."""
    field = next(x for x in layout()['appendFields'] if x['name'] == 'occlusionControls')
    if field['bytes'] != 16:
        raise AssertionError('occlusion controls wire size changed')
    return 24 + field['offset']


def resealed(snapshot, offset, payload):
    data = bytearray(snapshot)
    data[offset:offset + len(payload)] = payload
    struct.pack_into('<I', data, 20, zlib.crc32(data[24:]))
    return bytes(data)


class OcclusionDefaults(unittest.TestCase):
    def test_defaults_leave_every_recipe_frame_byte_identical_to_the_base_build(self):
        frames = FRAMES['base']['frames']
        self.assertEqual(frames[AUTUMN_30]['sha256'], AUTUMN_30_BASE_SHA256)
        self.assertEqual(len(frames), 2 * len(RECIPES))
        for key, expected in frames.items():
            with self.subTest(frame=key):
                self.assertEqual(digest(recipe_frame(key).bytes), expected['sha256'])

    def test_explicit_defaults_are_the_same_frame(self):
        for extra in ([{'op': 'environment', 'occlusionTint': 1}],
                      [{'op': 'environment', 'occludedDots': 'hidden'}],
                      [{'op': 'environment', 'occlusionTint': 1, 'occludedDots': 'hidden'}]):
            with self.subTest(extra=extra):
                frame = recipe_frame(AUTUMN_30, extra)
                self.assertEqual(digest(frame.bytes), AUTUMN_30_BASE_SHA256)
                self.assertEqual(counts(frame), (85, 511))

    def test_info_reports_defaults_and_changes(self):
        with NativeScene() as scene:
            environment = scene.info()['environment']
            self.assertEqual(environment['occlusionTint'], 1)
            self.assertEqual(environment['occludedDots'], 'hidden')
            scene.command({'op': 'environment', 'occlusionTint': 0.35, 'occludedDots': 'merge'})
            environment = scene.info()['environment']
            self.assertEqual(environment['occlusionTint'], 0.35)
            self.assertEqual(environment['occludedDots'], 'merge')
            self.assertEqual(scene.info_complete()['environment'], environment)
            scene.command({'op': 'environment', 'stars': 10})
            self.assertEqual(scene.info()['environment']['occlusionTint'], 0.35, 'omitted fields keep their value')
            scene.command({'op': 'reset', 'seed': 2030})
            environment = scene.info()['environment']
            self.assertEqual((environment['occlusionTint'], environment['occludedDots']), (1, 'hidden'))


class OcclusionLooks(unittest.TestCase):
    def check_variant(self, name):
        variant = FRAMES['prototypes']['variants'][name]
        extra = [{'op': 'environment', **variant['environment']}]
        self.assertIn(AUTUMN_30, variant['frames'])
        for key, expected in variant['frames'].items():
            with self.subTest(variant=name, frame=key):
                frame = recipe_frame(key, extra)
                self.assertEqual(digest(frame.bytes), expected['sha256'])
                self.assertEqual(list(counts(frame)), [expected['tinted'], expected['braille']])
        return variant['frames'][AUTUMN_30]

    def test_occlusion_tint_reproduces_the_tint_prototype(self):
        self.assertEqual((lambda f: (f['tinted'], f['braille']))(self.check_variant('tint-0.35')), (0, 511))
        self.assertEqual((lambda f: (f['tinted'], f['braille']))(self.check_variant('tint-0.6')), (27, 511))
        self.assertEqual((lambda f: (f['tinted'], f['braille']))(self.check_variant('tint-0')), (0, 511))

    def test_occluded_dots_merge_reproduces_the_merge_prototype(self):
        self.assertEqual((lambda f: (f['tinted'], f['braille']))(self.check_variant('merge')), (2, 511))
        self.check_variant('merge-tint-0.35')

    def test_unchanged_frames_stay_unchanged_under_every_setting(self):
        # Frames the prototypes did not change (no braille-family particle hidden behind another) stay base.
        base = FRAMES['base']['frames']
        for name, variant in FRAMES['prototypes']['variants'].items():
            extra = [{'op': 'environment', **variant['environment']}]
            for key in ('pearl-curves@2000000', 'instruments@2000000', 'aurora@30000000'):
                if key not in base or key in variant['frames']:
                    continue
                with self.subTest(variant=name, frame=key):
                    self.assertEqual(digest(recipe_frame(key, extra).bytes), base[key]['sha256'])


class OcclusionValidation(unittest.TestCase):
    INVALID = [
        ({'occlusionTint': -0.01}, 'occlusionTint must be a number from 0 to 1'),
        ({'occlusionTint': 1.0001}, 'occlusionTint must be a number from 0 to 1'),
        ({'occlusionTint': '0.5'}, 'occlusionTint must be a number from 0 to 1'),
        ({'occlusionTint': True}, 'occlusionTint must be a number from 0 to 1'),
        ({'occlusionTint': None}, 'occlusionTint must be a number from 0 to 1'),
        ({'occludedDots': 'blend'}, 'occludedDots must be "hidden" or "merge"'),
        ({'occludedDots': 1}, 'occludedDots must be "hidden" or "merge"'),
        ({'occludedDots': ''}, 'occludedDots must be "hidden" or "merge"'),
    ]

    def test_invalid_values_are_rejected_with_a_clear_error_and_change_nothing(self):
        with recipe_scene('autumn') as scene:
            scene.command({'op': 'environment', 'occlusionTint': 0.6})
            before = scene.snapshot()
            for fields, message in self.INVALID:
                with self.subTest(fields=fields):
                    with self.assertRaises(ValueError) as caught:
                        scene.command({'op': 'environment', 'stars': 7, **fields})
                    self.assertEqual(str(caught.exception), message)
                    self.assertEqual(scene.snapshot(), before)
                    self.assertEqual(scene.info()['environment']['occlusionTint'], 0.6)

    def test_boundaries_are_accepted(self):
        with NativeScene() as scene:
            for value in (0, 0.0, 1, 1.0, 0.5):
                scene.command({'op': 'environment', 'occlusionTint': value})
                self.assertEqual(scene.info()['environment']['occlusionTint'], value)


class OcclusionSnapshots(unittest.TestCase):
    def test_current_snapshot_round_trips_controls_and_frame(self):
        with recipe_scene('autumn', [{'op': 'environment', 'occlusionTint': 0.35, 'occludedDots': 'merge'}]) as scene:
            scene.advance_to(30_000_000)
            frame, saved = scene.render().bytes, scene.snapshot()
            self.assertEqual(struct.unpack_from('<I', saved, 12)[0], current_schema())
            self.assertEqual(digest(frame), FRAMES['prototypes']['variants']['merge-tint-0.35']['frames'][AUTUMN_30]['sha256'])
        with NativeScene(seed=1) as fresh:
            fresh.restore(saved)
            self.assertEqual(fresh.snapshot(), saved)
            self.assertEqual(fresh.render().bytes, frame)
            environment = fresh.info()['environment']
            self.assertEqual((environment['occlusionTint'], environment['occludedDots']), (0.35, 'merge'))

    def test_genuine_schema96_snapshot_restores_with_default_controls(self):
        manifest = json.loads((FIXTURE / 'schema96/manifest.json').read_text())
        raw = gzip.decompress((FIXTURE / 'schema96/snapshot.gz').read_bytes())
        frame = gzip.decompress((FIXTURE / 'schema96/frame.gz').read_bytes())
        self.assertEqual(digest(raw), manifest['snapshotSha256'])
        self.assertEqual(digest(frame), manifest['frameSha256'])
        self.assertEqual(manifest['frameSha256'], AUTUMN_30_BASE_SHA256)
        self.assertEqual(struct.unpack_from('<I', raw, 12)[0], 0x20261096)
        with NativeScene() as scene:
            scene.restore(raw)
            environment = scene.info()['environment']
            self.assertEqual((environment['occlusionTint'], environment['occludedDots']), (1, 'hidden'))
            self.assertEqual(scene.render().bytes, frame)
            promoted = scene.snapshot()
            self.assertEqual(struct.unpack_from('<I', promoted, 12)[0], current_schema())
            self.assertEqual(promoted[control_offset():control_offset() + 16], bytes(16))
            with NativeScene() as again:
                again.restore(promoted)
                self.assertEqual(again.render().bytes, frame)
            # The restored scene is the same state the recipe reaches: the controls then act exactly as on a live scene.
            scene.command({'op': 'environment', 'occlusionTint': 0.35})
            self.assertEqual(digest(scene.render().bytes),
                             FRAMES['prototypes']['variants']['tint-0.35']['frames'][AUTUMN_30]['sha256'])

    def test_non_canonical_or_out_of_range_controls_are_rejected_on_restore(self):
        offset = control_offset()
        with NativeScene() as scene:
            scene.command({'op': 'environment', 'occlusionTint': 0.5})
            good = scene.snapshot()
            configured, dots, tint = struct.unpack_from('<IId', good, offset)
            self.assertEqual((configured, dots, tint), (1, 0, 0.5))
            for name, payload in [
                ('tint above one', struct.pack('<IId', 1, 0, 1.5)),
                ('negative tint', struct.pack('<IId', 1, 0, -0.25)),
                ('unconfigured tint with a value', struct.pack('<IId', 0, 0, 0.5)),
                ('unknown configured flag', struct.pack('<IId', 2, 0, 0.5)),
                ('unknown dots mode', struct.pack('<IId', 1, 2, 0.5)),
                ('not a number', struct.pack('<IId', 1, 0, float('nan'))),
            ]:
                with self.subTest(case=name):
                    with self.assertRaises(ValueError):
                        scene.restore(resealed(good, offset, payload))
                    self.assertEqual(scene.snapshot(), good)
            scene.restore(resealed(good, offset, struct.pack('<IId', 1, 1, 0.25)))
            environment = scene.info()['environment']
            self.assertEqual((environment['occlusionTint'], environment['occludedDots']), (0.25, 'merge'))

    @staticmethod
    def as_schema96(saved):
        """A current snapshot re-expressed in the schema-96 layout: drop every fixed field appended since schema 96
        (the 16 control bytes and any later appendix, such as schema 98's prompt source layer), retag, reseal."""
        offset = control_offset()
        q = layout()
        end = 24 + q['fixed']  # the end of the fixed prefix: every field from occlusionControls on is newer than 96
        if saved[offset:end] != bytes(end - offset):
            raise AssertionError('cannot discard active occlusion controls or a later appendix')
        old = bytearray(saved[:offset] + saved[end:])
        for at, value in ((12, 0x20261096), (28, 0x20261096), (16, len(old) - 24)):
            struct.pack_into('<I', old, at, value)
        struct.pack_into('<I', old, 20, zlib.crc32(old[24:]))
        return bytes(old)

    def test_schema96_cannot_carry_pending_occlusion_commands(self):
        # Pending commands restore under their source schema; schema 96 never accepted these fields.
        cases = {
            'environment occlusionTint': {'op': 'environment', 'occlusionTint': 0.35},
            'environment occludedDots': {'op': 'environment', 'occludedDots': 'merge'},
            'batch': {'op': 'batch', 'commands': [{'op': 'environment', 'stars': 9}, {'op': 'environment', 'occlusionTint': 0}]},
            'bound occlusionTint': {'op': 'define', 'path': '/look', 'value': 0.5,
                                    'binding': {'family': 'environment', 'field': 'occlusionTint'}},
            'bound occludedDots': {'op': 'define', 'path': '/look', 'value': 1,
                                   'binding': {'family': 'environment', 'field': 'occludedDots'}},
        }
        for name, command in cases.items():
            with self.subTest(case=name), NativeScene() as scene:
                scene.schedule(7, 500_000, command)
                old = self.as_schema96(scene.snapshot())
                with NativeScene() as other:
                    before = other.snapshot()
                    with self.assertRaises(ValueError):
                        other.restore(old)
                    self.assertEqual(other.snapshot(), before)

    def test_schema96_with_an_older_pending_environment_command_restores_and_runs(self):
        # Positive companion: the same constructed layout restores, so the rejection above is the new field.
        with NativeScene() as scene:
            scene.schedule(7, 500_000, {'op': 'environment', 'stars': 9})
            old = self.as_schema96(scene.snapshot())
        with NativeScene() as other:
            other.restore(old)
            self.assertEqual(struct.unpack_from('<I', other.snapshot(), 12)[0], current_schema())
            other.advance_to(500_000)
            environment = other.info()['environment']
            self.assertEqual((environment['stars'], environment['occlusionTint'], environment['occludedDots']), (9, 1, 'hidden'))
            # After promotion the scene is current: the controls are accepted from now on.
            other.command({'op': 'environment', 'occlusionTint': 0.6})
            self.assertEqual(other.info()['environment']['occlusionTint'], 0.6)


class OcclusionResourceValues(unittest.TestCase):
    def test_bound_value_animates_occlusion_tint_through_scheduled_sets(self):
        variants = FRAMES['prototypes']['variants']
        with recipe_scene('autumn') as scene:
            scene.command({'op': 'define', 'path': '/look/tint', 'value': 1,
                           'binding': {'family': 'environment', 'id': 0, 'field': 'occlusionTint'}})
            scene.schedule(1, 29_000_000, {'op': 'set', 'path': '/look/tint', 'value': 0.6})
            scene.schedule(2, 29_500_000, {'op': 'set', 'path': '/look/tint', 'value': 0.35})
            scene.advance_to(28_000_000)
            self.assertEqual(scene.info()['environment']['occlusionTint'], 1)
            scene.advance_to(29_200_000)
            self.assertEqual(scene.info()['environment']['occlusionTint'], 0.6)
            scene.advance_to(30_000_000)
            self.assertEqual(scene.info()['environment']['occlusionTint'], 0.35)
            frame = scene.render()
            self.assertEqual(digest(frame.bytes), variants['tint-0.35']['frames'][AUTUMN_30]['sha256'])
            self.assertEqual(counts(frame), (0, 511))
            # A bound value is retained state: it survives a snapshot round trip.
            saved = scene.snapshot()
            with NativeScene() as other:
                other.restore(saved)
                self.assertEqual(other.render().bytes, frame.bytes)

    def test_bound_value_selects_occluded_dots(self):
        with recipe_scene('autumn') as scene:
            scene.command({'op': 'define', 'path': '/look/dots', 'value': 1,
                           'binding': {'family': 'environment', 'field': 'occludedDots'}})
            self.assertEqual(scene.info()['environment']['occludedDots'], 'merge')
            scene.advance_to(30_000_000)
            self.assertEqual(digest(scene.render().bytes),
                             FRAMES['prototypes']['variants']['merge']['frames'][AUTUMN_30]['sha256'])
            scene.command({'op': 'set', 'path': '/look/dots', 'value': 0})
            self.assertEqual(digest(scene.render().bytes), AUTUMN_30_BASE_SHA256)

    def test_out_of_domain_bound_values_roll_back(self):
        for field, value in [('occlusionTint', 1.5), ('occlusionTint', -1), ('occludedDots', 2), ('occludedDots', 0.5)]:
            with self.subTest(field=field, value=value), NativeScene() as scene:
                before = scene.snapshot()
                with self.assertRaises(ValueError):
                    scene.command({'op': 'define', 'path': '/look', 'value': value,
                                   'binding': {'family': 'environment', 'field': field}})
                self.assertEqual(scene.snapshot(), before)


EXPORT = r"""
import {writeFile,mkdir} from 'node:fs/promises';
import {dirname,join} from 'node:path';
import {readFileSync} from 'node:fs';
import {projectFromCommands} from '%(ts)s/composition_project.mjs';
import {generateProjectFiles} from '%(ts)s/composition_codegen.mjs';
const [commandsFile,out]=process.argv.slice(2);
const project=projectFromCommands(JSON.parse(readFileSync(commandsFile,'utf8')),{name:'Occlusion look',seed:2030,width:160,height:48});
const files=generateProjectFiles(project);
for(const [name,value] of Object.entries(files)){const path=join(out,name);await mkdir(dirname(path),{recursive:true});await writeFile(path,value);}
console.log(Object.keys(files).sort().join(','));
"""
TIME_US = 30_000_000
LOOK = {'op': 'environment', 'occlusionTint': 0.35, 'occludedDots': 'merge'}


def run(args, cwd, env=None, timeout=900):
    result = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise AssertionError(f"{' '.join(map(str, args))} failed in {cwd}:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
    return result.stdout


def typescript_compiler():
    module = os.environ.get('NOCTURNE_TYPESCRIPT_MODULE')
    if module and (Path(module).parent / 'tsc.js').is_file():
        return [shutil.which('node') or 'node', str(Path(module).parent / 'tsc.js')]
    tsc = shutil.which('tsc') or str(REPOSITORY / 'node_modules/.bin/tsc')
    return [tsc] if Path(tsc).is_file() else None


class OcclusionRuntimeParity(unittest.TestCase):
    """One non-default look, exported as a Workshop project, draws the same bytes in WASM, Python, Go and Rust."""

    @classmethod
    def setUpClass(cls):
        if not (NATIVE / 'dist/nocturne_native.wasm').is_file():
            raise unittest.SkipTest('build the SDK first (sh build-native.sh): missing native/dist/nocturne_native.wasm')
        cls.root = Path(tempfile.mkdtemp(prefix='.occlusion-parity-', dir=REPOSITORY))
        (cls.root / 'export.mjs').write_text(EXPORT % {'ts': (NATIVE / 'bindings/typescript').as_uri()})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def export(self, name, commands):
        # Generated programs resolve the SDK as ../native, so the project directory sits beside native/.
        out = REPOSITORY / f'.occlusion-{name}-{os.getpid()}'
        shutil.rmtree(out, ignore_errors=True)
        self.addCleanup(shutil.rmtree, out, True)
        source = self.root / f'{name}.json'
        source.write_text(json.dumps(commands))
        names = run(['node', str(self.root / 'export.mjs'), str(source), str(out)], REPOSITORY).strip().split(',')
        for required in ('panel-node.mjs', 'panel.py', 'main.go', 'src/main.rs', 'panel.ts'):
            self.assertIn(required, names)
        return out

    def frame(self, out, language):
        for name in ('panel.cells', 'panel.info.json'):
            (out / name).unlink(missing_ok=True)
        when = f'--time={TIME_US}'
        if language == 'wasm':
            run(['node', 'panel-node.mjs', when], out)
        elif language == 'python':
            run([os.environ.get('PYTHON', sys.executable), 'panel.py', when], out)
        elif language == 'go':
            run(['go', 'run', '.', when], out, env={'GOFLAGS': '-mod=mod', 'GOWORK': 'off'})
        elif language == 'rust':
            env = {'CARGO_TARGET_DIR': str(self.root / 'cargo-target')}
            if os.environ.get('NOCTURNE_COVERAGE') == '1':
                # As test_project_export_languages: a coverage qualification links the measured shared core, whose
                # rpath does not reach a dependent program, so the loader is pointed at native/dist.
                dist = str(NATIVE / 'dist')
                env.update(DYLD_FALLBACK_LIBRARY_PATH=dist, LD_LIBRARY_PATH=dist)
            run(['cargo', 'run', '--quiet', '--offline', '--', when], out, env=env)
        else:
            raise ValueError(language)
        data = (out / 'panel.cells').read_bytes()
        info = json.loads((out / 'panel.info.json').read_text())
        self.assertEqual(len(data) % 16, 0)
        return data, info['environment']

    @staticmethod
    def composition():
        # A Workshop project starts from its own base (orthographic camera, floor disabled, an RGB material 1);
        # restore the recipe's perspective camera, collision floor and OKLCh gradient so the leaves pile up.
        commands = [{**c, 'space': 'oklch'} if c['op'] == 'material' and 'space' not in c else c
                    for c in RECIPES['autumn']['commands']]
        return commands + [{'op': 'camera', 'orthographic': False}, {'op': 'floor', 'enabled': True}]

    def test_every_runtime_draws_the_same_non_default_look(self):
        commands = self.composition()
        look = self.export('look', commands + [LOOK])
        frames = {}
        for language in ('wasm', 'python', 'go', 'rust'):
            data, environment = self.frame(look, language)
            self.assertEqual((environment['occlusionTint'], environment['occludedDots']), (0.35, 'merge'), language)
            frames[language] = data
        reference = frames['wasm']
        for language, data in frames.items():
            self.assertEqual(digest(data), digest(reference), f'{language} frame differs from the WASM frame')
        # The look is in effect in this composition: the same project at the defaults draws different bytes.
        plain, environment = self.frame(self.export('plain', commands), 'wasm')
        self.assertEqual((environment['occlusionTint'], environment['occludedDots']), (1, 'hidden'))
        self.assertNotEqual(plain, reference)
        tinted = lambda data: sum(1 for i in range(8, len(data), 16) if saturation(int.from_bytes(data[i:i + 4], 'little')) > 40)
        braille = lambda data: sum(1 for i in range(0, len(data), 16) if 0x2800 <= int.from_bytes(data[i:i + 4], 'little') <= 0x28ff)
        self.assertGreater(tinted(plain), 0)
        self.assertLess(tinted(reference), tinted(plain))
        self.assertEqual(braille(reference), braille(plain))
        print(json.dumps({'look': digest(reference), 'default': digest(plain), 'cells': len(reference) // 16,
                          'tinted': [tinted(plain), tinted(reference)], 'braille': braille(reference)}), file=sys.stderr)

    def test_typescript_contract_accepts_the_controls(self):
        compiler = typescript_compiler()
        if compiler is None:
            self.fail('TypeScript compiler not found: set NOCTURNE_TYPESCRIPT_MODULE or put tsc on PATH')
        out = self.export('typed', self.composition() + [LOOK])
        (out / 'tsconfig.json').write_text(json.dumps({'compilerOptions': {
            'strict': True, 'noEmit': True, 'target': 'es2022', 'module': 'es2022', 'moduleResolution': 'bundler',
            'allowJs': True, 'checkJs': False, 'skipLibCheck': True, 'lib': ['es2022', 'dom']}, 'files': ['panel.ts']}))
        run([*compiler, '-p', 'tsconfig.json'], out)
        # And the compiler refuses an invalid choice, so the check above is not vacuous.
        bad = self.export('typed-bad', self.composition() + [{'op': 'environment', 'occludedDots': 'blend'}])
        (bad / 'tsconfig.json').write_text((out / 'tsconfig.json').read_text())
        result = subprocess.run([*compiler, '-p', 'tsconfig.json'], cwd=bad, capture_output=True, text=True, timeout=300)
        self.assertNotEqual(result.returncode, 0, 'the TypeScript contract accepted occludedDots "blend"')
        self.assertIn('blend', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
