"""Bounded prompt source: the original v0.1 prompt kernel as a layer over part of the scene.

`{op:"prompt-source", ..., layer:{region, z, order, alpha, frame}}` places the kernel in a rectangle:
`region` is a cell rectangle `{x,y,width,height}`, `"prompt"` (the active prompt's frame, resolved every
frame, so it follows a growing prompt) or `{widget:id}` (that widget's rectangle). The kernel runs with the
rectangle as its viewport and is composited at its origin. Outside the rectangle the ordinary scene is drawn
unchanged; inside it the source paints as it does over the full viewport. Without a layer nothing changes.

Oracles, all recorded from real runs:
  * fixtures/bounded-prompt-source/frames.json: every recipe frame at 2 s and 30 s, and the composite scene
    with and without each full-viewport preset, from the base build 9aa27afd (capture_base.py);
  * the archived v0.1 kernel source (fixtures/first-prompt-v01), compiled here, rendered at the layer size;
  * a genuine schema-0x20261097 snapshot written by the base build (fixtures/bounded-prompt-source/schema97).
Everything below executes the real native library; nothing is mocked.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C
import gzip
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
sys.path.insert(0, str(NATIVE / 'bindings/python'))
from nocturne_native import NativeScene  # noqa: E402
from native.tests.current_writer_contract import current_schema  # noqa: E402
from native.tests.constructed_dynamic_legacy_snapshot import layout  # noqa: E402
from native.tests.test_first_prompt_source import Cell, Config, INDICES, NR_ID_PROMPT, compile_original  # noqa: E402

FIXTURE = NATIVE / 'tests/fixtures/bounded-prompt-source'
FRAMES = json.loads((FIXTURE / 'frames.json').read_text())
SCENE = json.loads((FIXTURE / 'scene.json').read_text())
OPERATOR = json.loads((FIXTURE / 'operator-example.json').read_text())
RECIPES = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
PRESETS = [p for p in json.loads((NATIVE / 'examples/first-prompt-original-presets.json').read_text())
           if p['values']['layout'] == 1]
TIMES = (2_000_000, 30_000_000)
W, H = 160, 48
BORDER = {0x256d, 0x256e, 0x2570, 0x256f, 0x2500, 0x2502}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_all(scene, commands):
    for command in commands:
        while scene.command(command) == 1:
            pass


def preset_command(preset, **extra):
    command = {'op': 'prompt-source', 'values': preset['values'], **extra}
    for key in ('palette', 'starPalette', 'glyphs'):
        if key in preset:
            command[key] = [int(x.lstrip('#'), 16) if isinstance(x, str) else x for x in preset[key]]
    return command


TIDEPOOL = next(p for p in PRESETS if p['id'] == 'tidepool')


def composite(extra=(), time_us=TIMES[0], after_typing=()):
    """scene.json, as capture_base.py runs it: extra before the text is typed, after_typing once it is."""
    scene = NativeScene(seed=SCENE['seed'])
    run_all(scene, SCENE['commands'])
    run_all(scene, extra)
    scene.advance_to(time_us - SCENE['typeBeforeUs'])
    run_all(scene, [{'op': 'input', 'text': SCENE['typed']}])
    run_all(scene, after_typing)
    scene.advance_to(time_us)
    return scene


def cells(data):
    return [data[i:i + 16] for i in range(0, len(data), 16)]


def bounds(scene):
    return scene.info()['prompt']['firstPromptSource']['layer']['bounds']


def inside(rect, index, width=W):
    x, y = index % width, index // width
    return rect is not None and rect['x'] <= x < rect['x'] + rect['width'] and rect['y'] <= y < rect['y'] + rect['height']


def without_source(scene):
    """The same state with the prompt source disabled: weather events, document and clock are retained."""
    other = NativeScene(seed=1)
    other.restore(scene.snapshot())
    other.command({'op': 'prompt-source', 'enabled': False})
    return other


class LayerTestCase(unittest.TestCase):
    def assertOutsideEqual(self, frame, reference, rect, exclude=None, width=W):
        a, b = cells(frame), cells(reference)
        self.assertEqual(len(a), len(b))
        differ = [i for i in range(len(a)) if not inside(rect, i, width) and not inside(exclude, i, width) and a[i] != b[i]]
        self.assertEqual(differ[:8], [], f'{len(differ)} cells outside the layer differ')
        return a, b


class DefaultsUnchanged(LayerTestCase):
    def test_every_recipe_frame_equals_the_base_build(self):
        frames = FRAMES['recipes']
        self.assertEqual(len(frames), 60)
        for key, expected in sorted(frames.items()):
            recipe_id, time_us = key.split('@')
            with self.subTest(frame=key), NativeScene(seed=2030) as scene:
                scene.command({'op': 'resize', 'width': W, 'height': H})
                run_all(scene, RECIPES[recipe_id]['commands'])
                scene.advance_to(int(time_us))
                self.assertEqual(digest(scene.render().bytes), expected)

    def test_full_viewport_sources_equal_the_base_build(self):
        frames = FRAMES['composite']
        self.assertEqual(len(frames), 16)
        for key, expected in sorted(frames.items()):
            preset_id, time_us = key.split('@')
            extra = [] if preset_id == 'none' else [preset_command(next(p for p in PRESETS if p['id'] == preset_id))]
            with self.subTest(frame=key), composite(extra, int(time_us)) as scene:
                self.assertEqual(digest(scene.render().bytes), expected)
                if extra:
                    layer = scene.info()['prompt']['firstPromptSource']['layer']
                    self.assertEqual(layer, {'region': None, 'bounds': {'x': 0, 'y': 0, 'width': W, 'height': H},
                                             'z': 'above', 'order': 0, 'alpha': {'fg': 1, 'bg': 1}, 'frame': 'invisible'})

    def test_explicit_defaults_and_a_whole_grid_region_are_the_same_frames(self):
        # A layer over the whole grid takes the bounded path (clipped weather, region-only ids, banner spans)
        # and must reproduce the full-viewport frame byte for byte, weather in flight included.
        for layer in ({'z': 'above', 'order': 0, 'alpha': 1, 'frame': 'invisible'},
                      {'region': {'x': 0, 'y': 0, 'width': W, 'height': H}},
                      {'region': {'x': 0, 'y': 0, 'width': W, 'height': H}, 'alpha': 1.0},
                      {'region': {'x': 0, 'y': 0, 'width': W, 'height': H}, 'alpha': {'fg': 1, 'bg': 1.0}}):
            for time_us in TIMES:
                with self.subTest(layer=layer, time=time_us), composite([preset_command(TIDEPOOL, layer=layer)], time_us) as scene:
                    self.assertEqual(digest(scene.render().bytes), FRAMES['composite'][f'tidepool@{time_us}'])


class BoundedToThePrompt(LayerTestCase):
    def test_outside_the_prompt_frame_is_the_scene_and_inside_is_the_source(self):
        for time_us in TIMES:
            with self.subTest(time=time_us), composite([preset_command(TIDEPOOL, layer={'region': 'prompt'})], time_us) as scene:
                rect = bounds(scene)
                self.assertEqual(rect, {'x': 0, 'y': H - 3, 'width': W, 'height': 1})
                frame = scene.render().bytes
                with without_source(scene) as plain:
                    reference = plain.render().bytes
                    self.assertGreater(scene.info()['prompt']['appearance']['weather']['eventCount'], 0)
                a, b = self.assertOutsideEqual(frame, reference, rect)
                changed = sum(1 for i in range(len(a)) if inside(rect, i) and a[i] != b[i])
                self.assertGreater(changed, W // 2, 'the source paints inside the prompt frame')
                # The kernel's '>' and the typed tail sit on the prompt row at the kernel's own columns.
                row = [struct.unpack('<4I', a[rect['y'] * W + x]) for x in range(W)]
                self.assertEqual(chr(row[5][0]), '>')
                self.assertEqual(''.join(chr(row[7 + k][0]) for k in range(len(SCENE['typed']))), SCENE['typed'])
                self.assertTrue(all(row[7 + k][3] == NR_ID_PROMPT for k in range(len(SCENE['typed']) + 1)))

    def test_outside_equals_a_scene_that_never_had_a_source(self):
        # Fresh construction: text typed before the source is enabled, so both scenes hold the same weather
        # events. The reference is the base build's own frame (frames.json "none"), not this build's.
        for time_us in TIMES:
            with self.subTest(time=time_us):
                with composite([], time_us, after_typing=[preset_command(TIDEPOOL, layer={'region': 'prompt'})]) as scene:
                    frame, rect = scene.render().bytes, bounds(scene)
                with composite([], time_us) as plain:
                    reference = plain.render().bytes
                self.assertEqual(digest(reference), FRAMES['composite'][f'none@{time_us}'])
                self.assertOutsideEqual(frame, reference, rect)

    def test_the_layer_follows_bounded_growth(self):
        heights = []
        with composite([preset_command(TIDEPOOL, layer={'region': 'prompt'})]) as scene:
            for lines in range(1, 7):
                text = ' '.join(['agent'] * 26 * lines)[:156 * lines - 3]
                scene.command({'op': 'draft', 'text': text, 'emitWeather': False})
                rect = bounds(scene)
                heights.append(rect['height'])
                self.assertEqual((rect['x'], rect['y'], rect['width']), (0, H - 2 - rect['height'], W))
                source = scene.info()['prompt']['firstPromptSource']
                self.assertEqual(source['values'][:2], [W, rect['height']], 'the kernel viewport is the layer')
                self.assertEqual(source['row'], rect['y'] + rect['height'] // 2)
                frame = scene.render().bytes
                with without_source(scene) as plain:
                    self.assertOutsideEqual(frame, plain.render().bytes, rect)
        self.assertEqual(heights, [1, 2, 3, 4, 4, 4])

    def test_the_layer_follows_a_framed_growing_prompt(self):
        with composite([{'op': 'prompt', 'presentation': 'framed', 'mode': 'grow', 'minRows': 1, 'maxRows': 4},
                        preset_command(TIDEPOOL, layer={'region': 'prompt'})]) as scene:
            seen = []
            for lines in (1, 3, 6):
                scene.command({'op': 'draft', 'text': '\n'.join(['agent output'] * lines), 'emitWeather': False})
                rect = bounds(scene)
                seen.append(rect['height'])
                frame = scene.render().bytes
                with without_source(scene) as plain:
                    # The framed prompt paints only inside this rectangle, so outside it the scenes agree.
                    self.assertOutsideEqual(frame, plain.render().bytes, rect)
            self.assertEqual(seen, sorted(seen))
            self.assertLess(seen[0], seen[-1])

    def test_without_a_prompt_frame_nothing_is_placed(self):
        with composite([preset_command(TIDEPOOL, layer={'region': 'prompt'})]) as scene:
            scene.command({'op': 'prompt', 'active': False})
            self.assertIsNone(bounds(scene))
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['row'], -1)
            frame = scene.render().bytes
            with without_source(scene) as plain:
                self.assertEqual(frame, plain.render().bytes)


class KernelInsideTheLayer(LayerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='nocturne-bounded-prompt-')
        cls.oracle = compile_original(Path(cls.temp.name), 'original', False)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def kernel(self, w, h, text, values, arrays, time_us):
        q = Config()
        self.oracle.nsDefaultConfig(C.byref(q))
        q.values[0], q.values[1], q.values[3] = w, h, 1
        for name, value in values.items():
            q.values[INDICES[name]] = value
        for name, items in arrays.items():
            field = getattr(q, name)
            q.values[{'palette': 39, 'starPalette': 40, 'glyphs': 41}[name]] = len(items)
            for i, item in enumerate(items):
                field[i] = item
        data = (C.c_uint32 * len(text))(*map(ord, text))
        out = (Cell * (w * h))()
        self.assertEqual(self.oracle.nsRender(C.byref(q), time_us // 1000, data, len(text), out, len(out)), len(out))
        return cells(bytes(out)), (h // 2 if q.values[16] < 0 else min(q.values[16], h - 1))

    def test_every_preset_inside_a_cell_region_is_the_archived_kernel_at_that_size(self):
        rect = {'x': 20, 'y': 10, 'width': 60, 'height': 9}
        text = 'bounded source'
        for preset in PRESETS:
            command = preset_command(preset, layer={'region': rect})
            arrays = {k: command[k] for k in ('palette', 'starPalette', 'glyphs') if k in command}
            with self.subTest(preset=preset['id']), NativeScene(seed=2030) as scene:
                run_all(scene, [{'op': 'resize', 'width': W, 'height': H}, {'op': 'environment', 'stars': 120},
                                command, {'op': 'draft', 'text': text, 'emitWeather': False}])
                for time_us in (0, 100_000, 1_200_000, 2_400_000):
                    scene.advance_to(time_us)
                    expected, row = self.kernel(60, 9, text, preset['values'], arrays, time_us)
                    actual = cells(scene.render().bytes)
                    for k in range(len(text) + 1):  # the documented fourth-word adaptation: input cells own the prompt
                        expected[row * 60 + 7 + k] = expected[row * 60 + 7 + k][:12] + struct.pack('<I', NR_ID_PROMPT)
                    got = [actual[(rect['y'] + r) * W + rect['x'] + i] for r in range(9) for i in range(60)]
                    self.assertEqual(got, expected, f'{preset["id"]} at {time_us}')

    def test_a_clipped_kernel_runs_at_the_clipped_size(self):
        with NativeScene(seed=2030) as scene:
            run_all(scene, [{'op': 'resize', 'width': W, 'height': H},
                            preset_command(TIDEPOOL, layer={'region': {'x': 100, 'y': 30, 'width': 60, 'height': 18}}),
                            {'op': 'draft', 'text': 'clip', 'emitWeather': False}])
            scene.command({'op': 'resize', 'width': 130, 'height': 40})  # a terminal shrink is accepted
            self.assertEqual(bounds(scene), {'x': 100, 'y': 30, 'width': 30, 'height': 10})
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['region'],
                             {'x': 100, 'y': 30, 'width': 60, 'height': 18}, 'the authored region is retained')
            expected, row = self.kernel(30, 10, 'clip', TIDEPOOL['values'], {'palette': preset_command(TIDEPOOL)['palette']}, 0)
            actual = cells(scene.render().bytes)
            got = [actual[(30 + r) * 130 + 100 + i][:12] for r in range(10) for i in range(30)]
            self.assertEqual(got, [cell[:12] for cell in expected])
            scene.command({'op': 'resize', 'width': 90, 'height': 40})
            self.assertIsNone(bounds(scene))
            scene.command({'op': 'resize', 'width': W, 'height': H})
            self.assertEqual(bounds(scene), {'x': 100, 'y': 30, 'width': 60, 'height': 18})


class LayerControls(LayerTestCase):
    REGION = {'x': 30, 'y': 6, 'width': 50, 'height': 12}

    def scene_with(self, layer, time_us=TIMES[0]):
        return composite([preset_command(TIDEPOOL, layer=layer)], time_us)

    def prompt_rect(self, scene):
        with without_source(scene) as plain:
            plain.command({'op': 'prompt-source', 'values': {'layout': 1}, 'layer': {'region': 'prompt'}})
            return bounds(plain)

    def test_a_cell_region_leaves_the_scene_outside_it(self):
        with self.scene_with({'region': self.REGION}) as scene:
            self.assertEqual(bounds(scene), self.REGION)
            frame = scene.render().bytes
            prompt = self.prompt_rect(scene)
            with without_source(scene) as plain:
                # The source presents the prompt document, so the ordinary prompt frame is not painted either.
                self.assertOutsideEqual(frame, plain.render().bytes, self.REGION, exclude=prompt)

    def test_alpha_blends_over_the_scene_and_keeps_its_glyphs_under_blank_cells(self):
        with self.scene_with({'region': self.REGION}) as opaque, self.scene_with({'region': self.REGION, 'alpha': 0.4}) as blended:
            a, b = cells(opaque.render().bytes), cells(blended.render().bytes)
            with without_source(blended) as plain:
                reference = cells(plain.render().bytes)
            self.assertOutsideEqual(b''.join(b), b''.join(reference), self.REGION, exclude=self.prompt_rect(blended))
            region = [i for i in range(len(a)) if inside(self.REGION, i)]
            self.assertTrue(all(a[i] != b[i] or a[i] == reference[i] for i in region))
            kept = [i for i in region if struct.unpack('<I', a[i][:4])[0] == 32 and struct.unpack('<I', reference[i][:4])[0] != 32]
            self.assertGreater(len(kept), 0, 'scene glyphs exist under blank source cells')
            self.assertTrue(all(b[i][:4] == reference[i][:4] for i in kept), 'they show through at alpha < 1')
            self.assertEqual(blended.info()['prompt']['firstPromptSource']['layer']['alpha'], {'fg': 0.4, 'bg': 0.4})

    def test_alpha_zero_leaves_scene_cells_and_still_owns_the_input_row(self):
        with NativeScene(seed=2030) as scene:
            run_all(scene, [{'op': 'resize', 'width': W, 'height': H}, {'op': 'environment', 'stars': 150},
                            preset_command(TIDEPOOL, layer={'region': self.REGION, 'alpha': 0}),
                            {'op': 'draft', 'text': 'ghost', 'emitWeather': False}])
            frame = cells(scene.render().bytes)
            with without_source(scene) as plain:
                reference = cells(plain.render().bytes)
            region = [i for i in range(len(frame)) if inside(self.REGION, i)]
            self.assertTrue(all(frame[i][:12] == reference[i][:12] for i in region))
            row = scene.info()['prompt']['firstPromptSource']['row']
            self.assertEqual(struct.unpack('<I', frame[row * W + 30 + 7][12:])[0], NR_ID_PROMPT)

    def test_foreground_and_background_alphas_are_independent(self):
        def frames(alpha):
            with NativeScene(seed=2030) as scene:
                run_all(scene, [{'op': 'resize', 'width': W, 'height': H}, {'op': 'environment', 'stars': 150},
                                {'op': 'widget', 'id': 2, 'kind': 'text', 'x': 30, 'y': 8, 'width': 50, 'height': 6, 'text': 'scene text under the band'},
                                preset_command(TIDEPOOL, layer={'region': self.REGION, 'alpha': alpha}),
                                {'op': 'draft', 'text': 'ink', 'emitWeather': False}])
                scene.advance_to(500_000)
                frame = cells(scene.render().bytes)
                with without_source(scene) as plain:
                    reference = cells(plain.render().bytes)
                with NativeScene(seed=1) as opaque:
                    opaque.restore(scene.snapshot())
                    opaque.command({'op': 'prompt-source', 'layer': {'alpha': 1}})
                    source = cells(opaque.render().bytes)
                return frame, reference, source, scene.info()['prompt']['firstPromptSource']['layer']['alpha']
        word = lambda cell, k: struct.unpack('<4I', cell)[k]
        region = [i for i in range(W * H) if inside(self.REGION, i)]
        # Paper only: the source's backgrounds, the scene's glyphs (their ink covered by the paper), no source glyphs.
        frame, reference, source, alpha = frames({'fg': 0, 'bg': 1})
        self.assertEqual(alpha, {'fg': 0, 'bg': 1})
        self.assertTrue(all(word(frame[i], 2) == word(source[i], 2) for i in region))
        self.assertTrue(all(word(frame[i], 0) == word(reference[i], 0) for i in region))
        ink = [i for i in region if word(reference[i], 0) != 32]
        self.assertGreater(len(ink), 10)
        self.assertTrue(all(word(frame[i], 1) == word(source[i], 2) for i in ink), 'opaque paper covers the scene ink')
        # Ink only: the scene's backgrounds, and the source's glyphs at full strength where it draws one.
        frame, reference, source, alpha = frames({'fg': 1, 'bg': 0})
        self.assertTrue(all(word(frame[i], 2) == word(reference[i], 2) for i in region if word(source[i], 0) == 32))
        drawn = [i for i in region if word(source[i], 0) != 32]
        self.assertGreater(len(drawn), 3)
        self.assertTrue(all(word(frame[i], 0) == word(source[i], 0) and word(frame[i], 1) == word(source[i], 1) for i in drawn))
        # A partial patch keeps the other channel.
        with NativeScene() as scene:
            scene.command({'op': 'prompt-source', 'layer': {'region': self.REGION, 'alpha': {'bg': 0.25}}})
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['alpha'], {'fg': 1, 'bg': 0.25})
            scene.command({'op': 'prompt-source', 'layer': {'alpha': {'fg': 0.5}}})
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['alpha'], {'fg': 0.5, 'bg': 0.25})

    def test_a_visible_frame_is_drawn_on_the_region_edges_only(self):
        with self.scene_with({'region': self.REGION}) as plain, self.scene_with({'region': self.REGION, 'frame': 'visible'}) as framed:
            a, b = cells(plain.render().bytes), cells(framed.render().bytes)
            r = self.REGION
            edge = lambda i: inside(r, i) and (i % W in (r['x'], r['x'] + r['width'] - 1) or i // W in (r['y'], r['y'] + r['height'] - 1))
            self.assertTrue(all(a[i] == b[i] for i in range(len(a)) if not edge(i)))
            self.assertTrue(all(struct.unpack('<I', b[i][:4])[0] in BORDER for i in range(len(b)) if edge(i)))
            self.assertEqual(framed.info()['prompt']['firstPromptSource']['layer']['frame'], 'visible')

    def test_a_widget_region_follows_the_widget(self):
        with self.scene_with({'region': {'widget': 1}}) as scene:
            self.assertEqual(bounds(scene), {'x': 104, 'y': 4, 'width': 50, 'height': 10})
            scene.command({'op': 'widget', 'id': 1, 'kind': 'line', 'x': 60, 'y': 20, 'width': 40, 'height': 8})
            rect = bounds(scene)
            self.assertEqual(rect, {'x': 60, 'y': 20, 'width': 40, 'height': 8})
            frame = scene.render().bytes
            with without_source(scene) as plain:
                self.assertOutsideEqual(frame, plain.render().bytes, rect, exclude=self.prompt_rect(scene))
            scene.command({'op': 'widget', 'id': 1, 'kind': 'line', 'x': 150, 'y': 44, 'width': 40, 'height': 8})
            self.assertEqual(bounds(scene), {'x': 150, 'y': 44, 'width': 10, 'height': 4}, 'clipped to the grid')

    def test_a_widget_off_the_grid_places_nothing(self):
        with self.scene_with({'region': {'widget': 1}}) as scene:
            scene.command({'op': 'widget', 'id': 1, 'kind': 'line', 'x': 400, 'y': 4, 'width': 50, 'height': 10})
            self.assertIsNone(bounds(scene))
            frame = scene.render().bytes
            with without_source(scene) as plain:
                self.assertOutsideEqual(frame, plain.render().bytes, None, exclude=self.prompt_rect(scene))

    def test_pointer_hits_reach_the_prompt_inside_and_widgets_outside(self):
        with NativeScene(seed=2030) as scene:
            run_all(scene, [{'op': 'resize', 'width': W, 'height': H},
                            {'op': 'widget', 'id': 7, 'kind': 'text', 'x': 100, 'y': 30, 'width': 30, 'height': 3, 'text': 'tap'},
                            preset_command(TIDEPOOL, layer={'region': self.REGION}),
                            {'op': 'draft', 'text': 'abcdef', 'emitWeather': False}])
            scene.render()
            row = scene.info()['prompt']['firstPromptSource']['row']
            scene.command({'op': 'pointer', 'phase': 'down', 'x': 30 + 7 + 2, 'y': row, 'button': 0})
            scene.command({'op': 'pointer', 'phase': 'up', 'x': 30 + 7 + 2, 'y': row, 'button': 0})
            self.assertEqual(scene.info()['prompt']['caret'], 2)
            frame = cells(scene.render().bytes)
            self.assertEqual(struct.unpack('<I', frame[31 * W + 110][12:])[0] >> 24, 0x30, 'the widget keeps its hit id')


class LayerValidation(LayerTestCase):
    INVALID = [
        ({'region': {'x': 150, 'y': 0, 'width': 20, 'height': 2}}, 'Prompt source region must lie inside the grid'),
        ({'region': {'x': -1, 'y': 0, 'width': 2, 'height': 2}}, 'Prompt source region must lie inside the grid'),
        ({'region': {'x': 0, 'y': 47, 'width': 2, 'height': 2}}, 'Prompt source region must lie inside the grid'),
        ({'region': {'x': 0, 'y': 0, 'width': 0, 'height': 2}}, "Prompt source region is below the kernel's 1x1 minimum"),
        ({'region': {'x': 0, 'y': 0, 'width': 3, 'height': -1}}, "Prompt source region is below the kernel's 1x1 minimum"),
        ({'region': {'x': 0, 'y': 0, 'width': 2.5, 'height': 2}}, 'Prompt source region needs integer x, y, width and height'),
        ({'region': {'x': 0, 'y': 0, 'width': 2}}, 'Prompt source region needs integer x, y, width and height'),
        ({'region': {'x': 0, 'y': 0, 'width': 2, 'height': 2, 'depth': 1}}, 'Prompt source region needs integer x, y, width and height'),
        ({'region': 'window'}, 'Prompt source region must be {x,y,width,height}, "prompt", {widget} or null'),
        ({'region': 3}, 'Prompt source region must be {x,y,width,height}, "prompt", {widget} or null'),
        ({'region': {'widget': 9}}, 'Prompt source region widget does not exist'),
        ({'region': {'widget': 0}}, 'Prompt source region widget must be a widget id'),
        ({'region': {'widget': 1, 'x': 0}}, 'Prompt source region widget must be a widget id'),
        ({'z': 'below'}, 'Prompt source layer z "below" requires the surface-layers design'),
        ({'z': 'top'}, 'Prompt source layer z must be "above"'),
        ({'order': 1}, 'Prompt source layer order other than 0 requires the surface-layers design'),
        ({'order': 0.5}, 'Prompt source layer order must be an integer'),
        ({'alpha': 1.5}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': -0.1}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': '0.5'}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': True}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': {}}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': {'fg': 2}}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': {'fg': 0.5, 'bg': '1'}}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': {'fg': 0.5, 'ink': 1}}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'alpha': [0.5, 0.5]}, 'Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}'),
        ({'frame': 'maybe'}, 'Prompt source layer frame must be "visible" or "invisible"'),
        ({'blend': 'add'}, 'Unknown prompt source layer field'),
    ]

    def test_invalid_layers_are_rejected_with_a_clear_error_and_change_nothing(self):
        with composite([preset_command(TIDEPOOL, layer={'region': 'prompt', 'alpha': 0.7})]) as scene:
            before = scene.snapshot()
            for layer, message in self.INVALID:
                with self.subTest(layer=layer):
                    with self.assertRaises(ValueError) as caught:
                        scene.command({'op': 'prompt-source', 'values': {'seed': 9}, 'layer': layer})
                    self.assertEqual(str(caught.exception), message)
                    self.assertEqual(scene.snapshot(), before)
            for command, message in [({'op': 'prompt-source', 'layer': 'prompt'}, 'Unknown prompt source layer field'),
                                     ({'op': 'prompt-source', 'enabled': False, 'layer': None}, 'Disable prompt without a config patch')]:
                with self.subTest(command=command):
                    with self.assertRaises(ValueError) as caught:
                        scene.command(command)
                    self.assertEqual(str(caught.exception), message)
                    self.assertEqual(scene.snapshot(), before)

    def test_prompt_placement_needs_a_visible_prompt(self):
        with NativeScene() as scene:
            scene.command({'op': 'prompt', 'active': False})
            before = scene.snapshot()
            with self.assertRaises(ValueError) as caught:
                scene.command({'op': 'prompt-source', 'layer': {'region': 'prompt'}})
            self.assertEqual(str(caught.exception), 'Prompt source region "prompt" needs a visible prompt')
            self.assertEqual(scene.snapshot(), before)

    def test_boundaries_are_accepted(self):
        with NativeScene() as scene:
            for region in ({'x': 0, 'y': 0, 'width': 1, 'height': 1}, {'x': W - 1, 'y': H - 1, 'width': 1, 'height': 1},
                           {'x': 0, 'y': 0, 'width': W, 'height': H}):
                scene.command({'op': 'resize', 'width': W, 'height': H})
                scene.command({'op': 'prompt-source', 'layer': {'region': region}})
                self.assertEqual(bounds(scene), region)
                scene.render()
            for alpha in (0, 0.0, 1, 0.25):
                scene.command({'op': 'prompt-source', 'layer': {'alpha': alpha}})
                self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['alpha'], {'fg': alpha, 'bg': alpha})
            scene.command({'op': 'prompt-source', 'layer': {'alpha': {'fg': 0, 'bg': 1}}})
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['alpha'], {'fg': 0, 'bg': 1})

    def test_patch_semantics(self):
        with composite() as scene:
            scene.command({'op': 'prompt-source', 'layer': {'region': {'x': 1, 'y': 2, 'width': 30, 'height': 5}, 'alpha': 0.5, 'frame': 'visible'}})
            scene.command({'op': 'prompt-source', 'values': {'seed': 4}})
            layer = scene.info()['prompt']['firstPromptSource']['layer']
            self.assertEqual((layer['region'], layer['alpha'], layer['frame']), ({'x': 1, 'y': 2, 'width': 30, 'height': 5}, {'fg': 0.5, 'bg': 0.5}, 'visible'))
            scene.command({'op': 'prompt-source', 'layer': {'alpha': 0.25}})
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['region']['width'], 30, 'omitted region kept')
            scene.command({'op': 'prompt-source', 'layer': {'region': None}})
            layer = scene.info()['prompt']['firstPromptSource']['layer']
            self.assertEqual((layer['region'], layer['alpha'], layer['frame']), (None, {'fg': 0.25, 'bg': 0.25}, 'visible'))
            scene.command({'op': 'prompt-source', 'layer': None})
            self.assertEqual(scene.info()['prompt']['firstPromptSource']['layer']['alpha'], {'fg': 1, 'bg': 1})
            scene.command({'op': 'prompt-source', 'layer': {'region': 'prompt'}})
            scene.command({'op': 'prompt-source', 'enabled': False})
            scene.command({'op': 'prompt-source'})
            self.assertIsNone(scene.info()['prompt']['firstPromptSource']['layer']['region'], 'disabling clears the layer')


def layer_offset():
    field = next(x for x in layout()['appendFields'] if x['name'] == 'promptSourceLayer')
    if field['bytes'] != 56:
        raise AssertionError('prompt source layer wire size changed')
    return 24 + field['offset']


def resealed(snapshot, offset, payload):
    data = bytearray(snapshot)
    data[offset:offset + len(payload)] = payload
    struct.pack_into('<I', data, 20, zlib.crc32(data[24:]))
    return bytes(data)


def as_schema97(saved):
    """A current snapshot re-expressed in the schema-97 layout: drop the 56 layer bytes, retag, reseal."""
    offset = layer_offset()
    if saved[offset:offset + 56] != bytes(56):
        raise AssertionError('cannot discard an active prompt source layer')
    old = bytearray(saved[:offset] + saved[offset + 56:])
    for at, value in ((12, 0x20261097), (28, 0x20261097), (16, len(old) - 24)):
        struct.pack_into('<I', old, at, value)
    struct.pack_into('<I', old, 20, zlib.crc32(old[24:]))
    return bytes(old)


def layer_bytes(placement=0, widget=0, x=0, y=0, w=0, h=0, frame=0, z=0, order=0, configured=0, fg=0.0, bg=None):
    return struct.pack('<IIiiiiIIiIdd', placement, widget, x, y, w, h, frame, z, order, configured, fg, fg if bg is None else bg)


class LayerSnapshots(LayerTestCase):
    def test_round_trip_keeps_the_layer_and_the_frame(self):
        with composite([preset_command(TIDEPOOL, layer={'region': 'prompt', 'alpha': {'fg': 0.8, 'bg': 0.6}, 'frame': 'visible'})]) as scene:
            frame, saved, info = scene.render().bytes, scene.snapshot(), scene.info()['prompt']['firstPromptSource']
            self.assertEqual(struct.unpack_from('<I', saved, 12)[0], current_schema())
            self.assertEqual(saved[layer_offset():layer_offset() + 56], layer_bytes(placement=2, frame=1, configured=1, fg=0.8, bg=0.6))
        with NativeScene(seed=1) as fresh:
            fresh.restore(saved)
            self.assertEqual(fresh.snapshot(), saved)
            self.assertEqual(fresh.render().bytes, frame)
            self.assertEqual(fresh.info()['prompt']['firstPromptSource'], info)

    def test_genuine_schema97_snapshot_restores_with_the_full_viewport(self):
        manifest = json.loads((FIXTURE / 'schema97/manifest.json').read_text())
        raw = gzip.decompress((FIXTURE / 'schema97/snapshot.gz').read_bytes())
        frame = gzip.decompress((FIXTURE / 'schema97/frame.gz').read_bytes())
        self.assertEqual(digest(raw), manifest['snapshotSha256'])
        self.assertEqual(digest(frame), manifest['frameSha256'])
        self.assertEqual(manifest['frameSha256'], FRAMES['composite']['tidepool@2000000'])
        self.assertEqual(struct.unpack_from('<I', raw, 12)[0], 0x20261097)
        with NativeScene() as scene:
            scene.restore(raw)
            self.assertEqual(scene.render().bytes, frame)
            self.assertIsNone(scene.info()['prompt']['firstPromptSource']['layer']['region'])
            promoted = scene.snapshot()
            self.assertEqual(struct.unpack_from('<I', promoted, 12)[0], current_schema())
            self.assertEqual(promoted[layer_offset():layer_offset() + 56], bytes(56))
            with NativeScene() as again:
                again.restore(promoted)
                self.assertEqual(again.render().bytes, frame)
            # Promoted, the scene accepts a layer, and that layer acts as on a live scene.
            scene.command({'op': 'prompt-source', 'layer': {'region': 'prompt'}})
            with composite([preset_command(TIDEPOOL)], after_typing=[{'op': 'prompt-source', 'layer': {'region': 'prompt'}}]) as live:
                self.assertEqual(scene.render().bytes, live.render().bytes)

    def test_schema97_cannot_carry_pending_layer_commands(self):
        cases = {
            'prompt-source layer': {'op': 'prompt-source', 'layer': {'region': 'prompt'}},
            'prompt-source alpha': {'op': 'prompt-source', 'layer': {'alpha': 0.5}},
            'batch': {'op': 'batch', 'commands': [{'op': 'environment', 'stars': 9}, {'op': 'prompt-source', 'layer': None}]},
        }
        for name, command in cases.items():
            with self.subTest(case=name), NativeScene() as scene:
                scene.schedule(7, 500_000, command)
                old = as_schema97(scene.snapshot())
                with NativeScene() as other:
                    before = other.snapshot()
                    with self.assertRaises(ValueError):
                        other.restore(old)
                    self.assertEqual(other.snapshot(), before)

    def test_schema97_with_an_older_pending_command_restores_and_runs(self):
        # Positive companion: the same constructed layout restores, so the rejection above is the layer field.
        # (The pending probe used to normalise every older schema below the prompt-source epoch, rejecting an
        # older snapshot whose queue held a prompt-source command; fixed, see test_pending_probe_schema.py.)
        with NativeScene() as scene:
            scene.schedule(7, 500_000, {'op': 'environment', 'stars': 9})
            old = as_schema97(scene.snapshot())
        with NativeScene() as other:
            other.restore(old)
            self.assertEqual(struct.unpack_from('<I', other.snapshot(), 12)[0], current_schema())
            other.advance_to(500_000)
            self.assertEqual(other.info()['environment']['stars'], 9)
            other.command(preset_command(TIDEPOOL))
            self.assertIsNone(other.info()['prompt']['firstPromptSource']['layer']['region'])
            other.command({'op': 'prompt-source', 'layer': {'region': {'x': 0, 'y': 0, 'width': 10, 'height': 3}}})
            self.assertEqual(bounds(other), {'x': 0, 'y': 0, 'width': 10, 'height': 3})

    def test_non_canonical_layer_bytes_are_rejected_on_restore(self):
        offset = layer_offset()
        with NativeScene() as scene:
            scene.command({'op': 'prompt-source', 'layer': {'region': {'x': 2, 'y': 3, 'width': 20, 'height': 4}, 'alpha': 0.5}})
            good = scene.snapshot()
            self.assertEqual(good[offset:offset + 56], layer_bytes(1, 0, 2, 3, 20, 4, configured=1, fg=0.5))
            for name, payload in [
                ('z reserved', layer_bytes(1, 0, 2, 3, 20, 4, z=1, configured=1, fg=0.5)),
                ('order reserved', layer_bytes(1, 0, 2, 3, 20, 4, order=1, configured=1, fg=0.5)),
                ('foreground alpha above one', layer_bytes(1, 0, 2, 3, 20, 4, configured=1, fg=1.5, bg=0.5)),
                ('background alpha below zero', layer_bytes(1, 0, 2, 3, 20, 4, configured=1, fg=0.5, bg=-0.5)),
                ('alpha not a number', layer_bytes(1, 0, 2, 3, 20, 4, configured=1, fg=0.5, bg=float('nan'))),
                ('unconfigured alpha with a value', layer_bytes(1, 0, 2, 3, 20, 4, fg=0.0, bg=0.5)),
                ('unknown alpha flag', layer_bytes(1, 0, 2, 3, 20, 4, configured=2, fg=0.5)),
                ('unknown placement', layer_bytes(4)),
                ('empty cell region', layer_bytes(1, 0, 2, 3, 0, 4)),
                ('negative origin', layer_bytes(1, 0, -1, 3, 20, 4)),
                ('viewport with a rectangle', layer_bytes(0, 0, 2, 3, 20, 4)),
                ('prompt with a rectangle', layer_bytes(2, 0, 2, 3, 20, 4)),
                ('widget id zero', layer_bytes(3, 0)),
                ('widget beyond ids', layer_bytes(3, 65536)),
                ('unknown frame', layer_bytes(1, 0, 2, 3, 20, 4, frame=2)),
            ]:
                with self.subTest(case=name):
                    with self.assertRaises(ValueError):
                        scene.restore(resealed(good, offset, payload))
                    self.assertEqual(scene.snapshot(), good)
            scene.restore(resealed(good, offset, layer_bytes(2, frame=1)))
            layer = scene.info()['prompt']['firstPromptSource']['layer']
            self.assertEqual((layer['region'], layer['frame'], layer['alpha']), ('prompt', 'visible', {'fg': 1, 'bg': 1}))
            scene.command({'op': 'prompt-source', 'enabled': False})
            disabled = scene.snapshot()
            with self.assertRaises(ValueError):
                scene.restore(resealed(disabled, offset, layer_bytes(2)))


class WeatherOptions(C.Structure):
    _fields_ = [(name, C.c_double) for name in (
        'count lifeMs launchSpeed gravity drag wind flickerHz trailMs branches arcSegments arcJitter coreMs '
        'shockwave explosionForce seed brightness emberSpread arcReach').split()] + [('glyphCount', C.c_uint32), ('glyphs', C.c_uint32 * 64)]


class WeatherEvent(C.Structure):
    _fields_ = [('kind', C.c_uint32), ('id', C.c_double), ('x', C.c_double), ('y', C.c_double), ('atMs', C.c_double)]


class ClippedWeather(unittest.TestCase):
    """A clipped weather paint writes, inside the clip, exactly what an unclipped paint writes, and nothing outside."""

    @classmethod
    def setUpClass(cls):
        name = 'libnocturne_native.dylib' if sys.platform == 'darwin' else 'libnocturne_native.so'
        cls.lib = C.CDLL(str(NATIVE / 'dist' / name))
        cls.lib.nrSourceWeatherPaintLayer.restype = C.c_int
        cls.lib.nrSourceWeatherPaintLayerClipped.restype = C.c_int

    def test_every_style_and_clip_matches_the_unclipped_paint_inside_and_leaves_the_rest(self):
        width, height = 96, 40
        glyphs = [32, 32, 32, ord('a'), 0x2580, 0x2584, 0x2847, 0x258c, 0x2591]
        base = (C.c_uint32 * (width * height * 4))()
        for i in range(width * height):  # a deterministic mixed scene: blanks, text, half blocks, braille, shades
            h = (i * 2654435761) & 0xffffffff
            base[4 * i:4 * i + 4] = [glyphs[h % len(glyphs)], (h >> 8) & 0xffffff, (h >> 4) & 0xffffff, 0]
        options = WeatherOptions()
        self.lib.nrSourceWeatherDefaults(C.byref(options))
        options.lifeMs, options.launchSpeed = 1800.0, 9.0
        wheel = (C.c_uint32 * 360)(*[(0x400000 + i * 0x10203) & 0xffffff for i in range(360)])
        events = (WeatherEvent * 12)(*[WeatherEvent(k % 6, k + 1.0, 4.0 + 8.5 * k, 3.0 + 3.1 * k, 100.0 * k) for k in range(12)])
        clips = [(0, 0, width, height), (10, 5, 30, 12), (0, 0, 1, 1), (95, 39, 1, 1), (40, 0, 56, 40), (0, 30, 96, 10), (20, 10, 0, 0)]
        for time_ms in (300.0, 900.0, 1500.0):
            full = (C.c_uint32 * len(base))(*base)
            expected = self.lib.nrSourceWeatherPaintLayer(events, 12, C.c_double(time_ms), C.byref(options), C.c_double(0.8),
                                                         C.c_double(1), C.c_double(0), wheel, width, height, full)
            self.assertGreater(expected, 0)
            self.assertNotEqual(list(full), list(base), 'the weather paints something')
            for x, y, w, h in clips:
                with self.subTest(time=time_ms, clip=(x, y, w, h)):
                    clipped = (C.c_uint32 * len(base))(*base)
                    got = self.lib.nrSourceWeatherPaintLayerClipped(events, 12, C.c_double(time_ms), C.byref(options), C.c_double(0.8),
                                                                   C.c_double(1), C.c_double(0), wheel, width, height, clipped, x, y, w, h)
                    self.assertEqual(got, expected)
                    changed = sum(1 for i in range(width * height) if x <= i % width < x + w and y <= i // width < y + h
                                  and list(full[4 * i:4 * i + 4]) != list(base[4 * i:4 * i + 4]))
                    if time_ms == 1500.0 and (w, h) in ((30, 12), (56, 40)):
                        self.assertGreater(changed, 0, 'the weather reaches into this clip')
                    for i in range(width * height):
                        inside_clip = x <= i % width < x + w and y <= i // width < y + h
                        want = full if inside_clip else base
                        self.assertEqual(list(clipped[4 * i:4 * i + 4]), list(want[4 * i:4 * i + 4]), (i % width, i // width))
        outside = (C.c_uint32 * len(base))(*base)
        self.assertEqual(self.lib.nrSourceWeatherPaintLayerClipped(events, 12, C.c_double(900.0), C.byref(options), C.c_double(0.8),
                                                                   C.c_double(1), C.c_double(0), wheel, width, height, outside, 90, 0, 7, 1), -1)
        self.assertEqual(list(outside), list(base), 'an invalid clip writes nothing')


EXPORT = r"""
import {writeFile,mkdir} from 'node:fs/promises';
import {dirname,join} from 'node:path';
import {readFileSync} from 'node:fs';
import {projectFromCommands} from '%(ts)s/composition_project.mjs';
import {generateProjectFiles} from '%(ts)s/composition_codegen.mjs';
const [sceneFile,out]=process.argv.slice(2);
const scene=JSON.parse(readFileSync(sceneFile,'utf8'));
const project=projectFromCommands(scene.commands,{name:'Bounded prompt source',seed:scene.seed,width:scene.width,height:scene.height,timeline:scene.timeline});
const files=generateProjectFiles(project);
for(const [name,value] of Object.entries(files)){const path=join(out,name);await mkdir(dirname(path),{recursive:true});await writeFile(path,value);}
console.log(Object.keys(files).sort().join(','));
"""


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


def operator_scene(layer=True):
    """The operator's example: tidepool bound to the bottom rows of an agent widget window whose text scrolls."""
    commands = [c for c in OPERATOR['commands'] if layer or c['op'] != 'prompt-source']
    return {'seed': OPERATOR['seed'], 'width': OPERATOR['width'], 'height': OPERATOR['height'],
            'commands': commands, 'timeline': OPERATOR['timeline']}


def operator_native(time_us, layer=True):
    scene = NativeScene(seed=OPERATOR['seed'])
    run_all(scene, [{'op': 'resize', 'width': OPERATOR['width'], 'height': OPERATOR['height']}])
    run_all(scene, operator_scene(layer)['commands'])
    for k, event in enumerate(OPERATOR['timeline']):
        scene.schedule(1000 + k, event['timeUs'], event['command'])
    scene.advance_to(time_us)
    return scene


class OperatorExample(LayerTestCase):
    def test_tidepool_is_bound_to_the_bottom_rows_of_the_agent_window_and_the_text_shows_through(self):
        region = next(c for c in OPERATOR['commands'] if c['op'] == 'prompt-source')['layer']['region']
        widget = next(c for c in OPERATOR['commands'] if c['op'] == 'widget')
        self.assertEqual(region['x'], widget['x'] + 1)
        self.assertEqual(region['width'], widget['width'] - 2)
        self.assertEqual(region['y'] + region['height'], widget['y'] + widget['height'] - 1, 'bottom rows, inside the border')
        texts = []
        for time_us in (3_000_000, OPERATOR['timeUs']):
            with operator_native(time_us) as scene:
                self.assertEqual(bounds(scene), region)
                frame = scene.render().bytes
                with without_source(scene) as plain:
                    reference = plain.render().bytes
                self.assertOutsideEqual(frame, reference, region, exclude=self.prompt_rect(scene))
                a, b = cells(frame), cells(reference)
                text = [i for i in range(len(a)) if inside(region, i) and 33 <= struct.unpack('<I', b[i][:4])[0] < 127]
                shown = [i for i in text if a[i][:4] == b[i][:4]]
                self.assertGreater(len(shown), 10, 'agent text shows through the layer')
                ascii_row = lambda y: ''.join(chr(g) if 32 <= g < 127 else ' ' for g in (struct.unpack('<I', b[y * W + x][:4])[0] for x in range(10, 76)))
                rows = [ascii_row(y).strip() for y in range(8, 20)]
                texts.append(rows)
        self.assertNotEqual(texts[0], texts[1], 'the agent text scrolls')
        self.assertTrue(texts[1][-1].startswith('agent> waiting for review'), texts[1])
        self.assertTrue(texts[0][0].startswith('agent> reading the plan'), texts[0])
        self.assertTrue(texts[1][0].startswith('agent> schema 0x20261098'), 'the first lines have scrolled away')

    def prompt_rect(self, scene):
        with without_source(scene) as plain:
            plain.command({'op': 'prompt-source', 'values': {'layout': 1}, 'layer': {'region': 'prompt'}})
            return bounds(plain)


class LayerRuntimeParity(unittest.TestCase):
    """The operator's example, exported as a Workshop project, draws the same bytes in WASM, Python, Go and Rust."""

    @classmethod
    def setUpClass(cls):
        if not (NATIVE / 'dist/nocturne_native.wasm').is_file():
            raise unittest.SkipTest('build the SDK first (sh build-native.sh): missing native/dist/nocturne_native.wasm')
        cls.root = Path(tempfile.mkdtemp(prefix='.bounded-prompt-parity-', dir=REPOSITORY))
        (cls.root / 'export.mjs').write_text(EXPORT % {'ts': (NATIVE / 'bindings/typescript').as_uri()})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def export(self, name, scene):
        out = REPOSITORY / f'.bounded-prompt-{name}-{os.getpid()}'
        shutil.rmtree(out, ignore_errors=True)
        self.addCleanup(shutil.rmtree, out, True)
        source = self.root / f'{name}.json'
        source.write_text(json.dumps(scene))
        names = run(['node', str(self.root / 'export.mjs'), str(source), str(out)], REPOSITORY).strip().split(',')
        for required in ('panel-node.mjs', 'panel.py', 'main.go', 'src/main.rs', 'panel.ts'):
            self.assertIn(required, names)
        return out

    def frame(self, out, language):
        for name in ('panel.cells', 'panel.info.json'):
            (out / name).unlink(missing_ok=True)
        when = f"--time={OPERATOR['timeUs']}"
        if language == 'wasm':
            run(['node', 'panel-node.mjs', when], out)
        elif language == 'python':
            run([os.environ.get('PYTHON', sys.executable), 'panel.py', when], out)
        elif language == 'go':
            run(['go', 'run', '.', when], out, env={'GOFLAGS': '-mod=mod', 'GOWORK': 'off'})
        elif language == 'rust':
            env = {'CARGO_TARGET_DIR': str(self.root / 'cargo-target')}
            if os.environ.get('NOCTURNE_COVERAGE') == '1':
                dist = str(NATIVE / 'dist')
                env.update(DYLD_FALLBACK_LIBRARY_PATH=dist, LD_LIBRARY_PATH=dist)
            run(['cargo', 'run', '--quiet', '--offline', '--', when], out, env=env)
        else:
            raise ValueError(language)
        data = (out / 'panel.cells').read_bytes()
        info = json.loads((out / 'panel.info.json').read_text())
        self.assertEqual(len(data) % 16, 0)
        return data, info['prompt']['firstPromptSource']

    def test_every_runtime_draws_the_same_bounded_scene(self):
        out = self.export('layer', operator_scene())
        region = next(c for c in OPERATOR['commands'] if c['op'] == 'prompt-source')['layer']['region']
        frames = {}
        for language in ('wasm', 'python', 'go', 'rust'):
            data, source = self.frame(out, language)
            self.assertEqual(source['layer']['bounds'], region, language)
            self.assertEqual(source['layer']['alpha'], OPERATOR['commands'][-1]['layer']['alpha'], language)
            self.assertNotEqual(source['layer']['alpha']['fg'], source['layer']['alpha']['bg'], 'the example sets each channel')
            frames[language] = data
        for language, data in frames.items():
            self.assertEqual(digest(data), digest(frames['wasm']), f'{language} frame differs from the WASM frame')
        plain, source = self.frame(self.export('plain', operator_scene(layer=False)), 'wasm')
        self.assertIsNone(source)
        self.assertNotEqual(plain, frames['wasm'])
        print(json.dumps({'layer': digest(frames['wasm']), 'withoutLayer': digest(plain), 'cells': len(plain) // 16}), file=sys.stderr)

    def test_typescript_contract_accepts_the_layer(self):
        compiler = typescript_compiler()
        if compiler is None:
            self.fail('TypeScript compiler not found: set NOCTURNE_TYPESCRIPT_MODULE or put tsc on PATH')
        config = json.dumps({'compilerOptions': {
            'strict': True, 'noEmit': True, 'target': 'es2022', 'module': 'es2022', 'moduleResolution': 'bundler',
            'allowJs': True, 'checkJs': False, 'skipLibCheck': True, 'lib': ['es2022', 'dom']}, 'files': ['panel.ts']})
        out = self.export('typed', operator_scene())
        (out / 'tsconfig.json').write_text(config)
        run([*compiler, '-p', 'tsconfig.json'], out)
        bad = operator_scene()
        bad['commands'] = bad['commands'][:-1] + [{**bad['commands'][-1], 'layer': {'region': 'prompt', 'z': 'sideways'}}]
        bad_out = self.export('typed-bad', bad)
        (bad_out / 'tsconfig.json').write_text(config)
        result = subprocess.run([*compiler, '-p', 'tsconfig.json'], cwd=bad_out, capture_output=True, text=True, timeout=300)
        self.assertNotEqual(result.returncode, 0, 'the TypeScript contract accepted z "sideways"')
        self.assertIn('sideways', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
