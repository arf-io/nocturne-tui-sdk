"""Retained material pattern appearance against original RC2 Stage Wasm."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench

HTML_SHA = '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'
WASM_SHA = 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09'
KINDS = ['solid', 'linear', 'diagonal', 'wave', 'rotating-linear', 'plasma',
         'concentric', 'moire', 'aurora', 'interference', 'chevrons', 'diamond']
PALETTE = [0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565]


class RetainedMaterialPatterns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = load_rc2_workbench().encode('utf-8')
        if hashlib.sha256(html).hexdigest() != HTML_SHA:
            raise AssertionError('original rc.2 HTML custody mismatch')
        cls.temp = tempfile.TemporaryDirectory(prefix='material-pattern-integration-')
        cls.html_path = Path(cls.temp.name) / 'original-rc2.html'
        cls.html_path.write_bytes(html)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def original(self, cases):
        result = subprocess.run(
            ['node', str(ROOT / 'tests/original_rc2_surface_sampler_oracle.mjs'), str(self.html_path)],
            input=json.dumps(cases), capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        oracle = json.loads(result.stdout)
        self.assertEqual(oracle['editionSha256'], HTML_SHA)
        self.assertEqual(oracle['wasmSha256'], WASM_SHA)
        return oracle['results']

    def wasm_frames(self, requests):
        result = subprocess.run(
            ['node', str(ROOT / 'tests/render_material_pattern_wasm.mjs')],
            input=json.dumps(requests), capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def pattern_command(self, kind, *, controls=None, palette=None):
        pattern = {'kind': kind, **(controls or {})}
        if palette is not None:
            pattern['palette'] = palette
        return {'op': 'material', 'id': 2, 'pattern': pattern}

    @staticmethod
    def setup_panel(scene, width=20, height=12, x=3, y=2):
        scene.command({'op': 'resize', 'width': width, 'height': height})
        scene.command({'op': 'material', 'id': 2, 'alpha': 1})
        scene.command({'op': 'widget', 'id': 1, 'kind': 'box', 'x': x, 'y': y,
                       'width': 11, 'height': 7, 'padding': 0, 'border': 'none',
                       'alpha': 1, 'backgroundMaterial': 2})

    def assert_panel_matches(self, scene, rgb, width, x=3, y=2, panel_width=11, panel_height=7):
        frame = scene.render()
        words = frame.words()
        self.assertEqual((frame.width, frame.height), (width, len(rgb) // width))
        for py in range(panel_height):
            for px in range(panel_width):
                at = (y + py) * width + x + px
                self.assertEqual(words[at][2], rgb[at], ('cell', x + px, y + py))

    def test_all_twelve_kinds_match_actual_original_wasm_at_absolute_2d_cells(self):
        width, height = 20, 12
        times = (0, 2_137)
        requests = [
            {'width': width, 'height': height, 'timeMs': time_ms,
             'values': {'2': KINDS.index(kind)}, 'palette': PALETTE}
            for time_ms in times for kind in KINDS
        ]
        expected = self.original(requests)
        wasm_requests = [
            {'width': width, 'height': height, 'timeMs': time_ms,
             'x': 3, 'y': 2, 'panelWidth': 11, 'panelHeight': 7,
             'pattern': {'kind': kind, 'palette': PALETTE}}
            for time_ms in times for kind in KINDS
        ]
        wasm = self.wasm_frames(wasm_requests)
        self.assertEqual(len(expected), len(times) * len(KINDS))
        self.assertEqual(len(wasm), len(wasm_requests))
        index = 0
        with NativeScene(2030) as scene:
            self.setup_panel(scene, width, height)
            for time_ms in times:
                if time_ms:
                    scene.advance_to(time_ms * 1000)
                for kind in KINDS:
                    with self.subTest(kind=kind, time_ms=time_ms):
                        scene.command(self.pattern_command(kind, palette=PALETTE))
                        frame = scene.render()
                        self.assert_panel_matches(scene, expected[index]['rgb'], width)
                        self.assertEqual(frame.words(), tuple(tuple(cell) for cell in wasm[index]))
                    index += 1

    def test_custom_focus_rotation_palette_controls_match_source_samples(self):
        width, height = 20, 12
        controls = {
            'focusMode': 'radial', 'focusXQ8': 1152, 'focusYQ8': 768,
            'periodMs': 3700, 'saturationMilli': 923, 'brightnessMilli': 612,
            'speedFalloffMilli': 375, 'saturationFalloffMilli': 681,
            'brightnessFalloffMilli': 825, 'cellAspectMilli': 2750,
            'scaleQ8': 8120, 'angleMilliDegrees': 19000,
            'pivotXQ8': 1728, 'pivotYQ8': 896, 'rotationPeriodMs': 7100,
            'rotationMode': 'pendulum', 'swingMilliDegrees': 81000,
            'phase1024': 73, 'seed': 12345, 'baseRgb': 0x243142,
            'inkRgb': 0xd4c5a1, 'gradientWrap': 'mirror',
            'interpolation': 'linear', 'colorMode': 'hsv',
            'hueOffsetDegrees': -73, 'motion': True,
            'originXCells': 2, 'originYCells': -1,
            'waveAmplitudeMilli': 915, 'reverse': True,
        }
        palette = [0x09243a, 0x9d3568, 0xe8bd64]
        fields = {
            'kind': (2, 'rotating-linear'), 'focusMode': (3, 'radial'),
            'focusXQ8': (4, 1152), 'focusYQ8': (5, 768), 'periodMs': (6, 3700),
            'saturationMilli': (7, 923), 'brightnessMilli': (8, 612),
            'speedFalloffMilli': (9, 375), 'saturationFalloffMilli': (10, 681),
            'brightnessFalloffMilli': (11, 825), 'cellAspectMilli': (12, 2750),
            'scaleQ8': (13, 8120), 'angleMilliDegrees': (14, 19000),
            'pivotXQ8': (15, 1728), 'pivotYQ8': (16, 896),
            'rotationPeriodMs': (17, 7100), 'rotationMode': (18, 'pendulum'),
            'swingMilliDegrees': (19, 81000), 'phase1024': (20, 73),
            'seed': (22, 12345), 'baseRgb': (23, 0x243142), 'inkRgb': (24, 0xd4c5a1),
            'gradientWrap': (26, 'mirror'), 'interpolation': (27, 'linear'),
            'colorMode': (28, 'hsv'), 'hueOffsetDegrees': (29, -73),
            'motion': (47, True), 'originXCells': (49, 2), 'originYCells': (50, -1),
            'waveAmplitudeMilli': (51, 915), 'reverse': (53, True),
        }
        enum_values = {
            2: KINDS, 3: ['none', 'row', 'column', 'radial', 'diagonal-band'],
            18: ['fixed', 'continuous', 'pendulum'],
            26: ['loop', 'mirror', 'hard-stops'], 27: ['linear', 'eased'],
            28: ['palette', 'hsv', 'rgb-sine'],
        }
        original_values = {}
        for _, (field_id, value) in fields.items():
            original_values[field_id] = enum_values[field_id].index(value) if field_id in enum_values else int(value)
        self.assertEqual(len(fields), len(controls) + 1)
        cases = [{'width': width, 'height': height, 'timeMs': time_ms,
                  'values': original_values, 'palette': palette}
                 for time_ms in (0, 1100, 4100)]
        results = self.original(cases)
        with NativeScene(2030) as scene:
            self.setup_panel(scene, width, height)
            scene.command(self.pattern_command('rotating-linear', controls=controls, palette=palette))
            for time_ms, result in zip((0, 1100, 4100), results):
                if time_ms:
                    scene.advance_to(time_ms * 1000)
                with self.subTest(time_ms=time_ms):
                    self.assert_panel_matches(scene, result['rgb'], width)

    def test_widget_foreground_glyphs_sample_pattern_at_their_absolute_cells(self):
        width, height = 20, 12
        kinds = ('linear', 'wave', 'rotating-linear', 'plasma', 'aurora', 'diamond')
        cases = [{'width': width, 'height': height, 'timeMs': 731,
                  'values': {'2': KINDS.index(kind)}, 'palette': PALETTE}
                 for kind in kinds]
        expected = self.original(cases)
        wasm = self.wasm_frames([{
            'width': width, 'height': height, 'timeMs': 731,
            'widget': {'op': 'widget', 'id': 4, 'kind': 'text', 'x': 3, 'y': 2,
                       'width': 11, 'height': 2, 'padding': 0, 'border': 'none',
                       'alpha': 1, 'material': 2, 'text': 'Nocturne'},
            'pattern': {'kind': kind, 'palette': PALETTE}}
            for kind in kinds])
        with NativeScene(2030) as scene:
            scene.command({'op': 'resize', 'width': width, 'height': height})
            scene.command({'op': 'material', 'id': 2, 'alpha': 1})
            scene.command({'op': 'widget', 'id': 4, 'kind': 'text', 'x': 3, 'y': 2,
                           'width': 11, 'height': 2, 'padding': 0, 'border': 'none',
                           'alpha': 1, 'material': 2, 'text': 'Nocturne'})
            scene.advance_to(731_000)
            for kind, result, wasm_frame in zip(kinds, expected, wasm):
                scene.command(self.pattern_command(kind, palette=PALETTE))
                frame = scene.render()
                self.assertEqual(frame.words(), tuple(tuple(cell) for cell in wasm_frame))
                words = frame.words()
                for offset, glyph in enumerate('Nocturne'):
                    at = 2 * width + 3 + offset
                    with self.subTest(kind=kind, glyph=glyph, x=3 + offset):
                        self.assertEqual(words[at][0], ord(glyph))
                        self.assertEqual(words[at][1], result['rgb'][at])

    def test_plot_pattern_samples_covered_subcells_and_keeps_widget_ownership(self):
        width, height = 32, 16
        widget = {'op': 'widget', 'id': 4, 'kind': 'bars', 'x': 4, 'y': 2,
                  'width': 18, 'height': 10, 'padding': 0, 'border': 'none',
                  'alpha': 1, 'material': 2, 'data': [1, .55, .8, .35]}
        pattern = {'kind': 'wave', 'motion': False, 'palette': PALETTE}
        wasm = self.wasm_frames([{'width': width, 'height': height, 'timeMs': 0,
                                  'widget': widget, 'pattern': pattern}])[0]
        with NativeScene(2030) as scene:
            scene.command({'op': 'resize', 'width': width, 'height': height})
            scene.command({'op': 'material', 'id': 2, 'alpha': 1})
            scene.command(widget)
            baseline = scene.render().words()
            scene.command({'op': 'material', 'id': 2, 'pattern': pattern})
            frame = scene.render()
            words = frame.words()
            owned = [index for index, cell in enumerate(words)
                     if cell[3] == 0x30000004 and cell[0] != 32]
            baseline_owned = [index for index, cell in enumerate(baseline)
                              if cell[3] == 0x30000004 and cell[0] != 32]
            self.assertGreater(len(owned), 4)
            self.assertEqual(owned, baseline_owned)
            self.assertTrue(any(words[index][1] != baseline[index][1] for index in owned))
            self.assertGreater(len({words[index][1] for index in owned}), 1)
            self.assertEqual(words, tuple(tuple(cell) for cell in wasm))

    def test_non_widget_indicator_uses_its_actual_surface_cell(self):
        width, height = 20, 12
        pattern = {'kind': 'linear', 'motion': False, 'palette': PALETTE}
        expected = self.original([{
            'width': width, 'height': height, 'timeMs': 0,
            'values': {'2': KINDS.index('linear')}, 'palette': PALETTE,
        }])[0]['rgb']
        with NativeScene(2030) as scene:
            scene.command({'op': 'resize', 'width': width, 'height': height})
            scene.command({'op': 'material', 'id': 2, 'alpha': 1})
            scene.command({'op': 'indicator', 'id': 7, 'x': 5, 'y': 4,
                           'sequence': 'A', 'stepMs': 100, 'material': 2})
            scene.command(self.pattern_command('linear', controls={'motion': False},
                                               palette=PALETTE))
            cell = scene.render().words()[4 * width + 5]
            self.assertEqual(cell[0], ord('A'))
            self.assertEqual(cell[1], expected[4 * width + 5])
            self.assertNotEqual(cell[1], expected[4 * width + 6],
                                'different surface coordinates must sample differently')

    def test_non_widget_indicator_pattern_clear_restores_legacy_frame(self):
        with NativeScene(2030) as scene:
            scene.command({'op': 'resize', 'width': 20, 'height': 12})
            scene.command({'op': 'material', 'id': 2, 'space': 'rgb',
                           'channels': {'r': .2, 'g': .4, 'b': .6}, 'alpha': 1})
            scene.command({'op': 'indicator', 'id': 7, 'x': 5, 'y': 4,
                           'sequence': 'AB', 'stepMs': 100, 'material': 2})
            legacy = scene.render()
            scene.command(self.pattern_command('linear', controls={'motion': False},
                                               palette=PALETTE))
            patterned = scene.render()
            self.assertNotEqual(patterned.words()[4 * 20 + 5][1],
                                legacy.words()[4 * 20 + 5][1])
            scene.command({'op': 'material', 'id': 2, 'pattern': None})
            self.assertEqual(scene.render().bytes, legacy.bytes)

    def test_text_transition_samples_the_rounded_visible_glyph_cell(self):
        width, height = 20, 12
        expected = self.original([{
            'width': width, 'height': height, 'timeMs': 0,
            'values': {'2': KINDS.index('wave')}, 'palette': PALETTE,
        }])[0]['rgb']
        with NativeScene(2030) as scene:
            scene.command({'op': 'resize', 'width': width, 'height': height})
            scene.command({'op': 'material', 'id': 2, 'alpha': 1})
            scene.command({'op': 'text', 'id': 9, 'text': 'A', 'x': 5, 'y': 4,
                           'width': 4, 'material': 2, 'effect': 'text/glyph-fall',
                           'phase': 'show', 'durationMs': 0, 'jitterMs': 0,
                           'phaseModel': 'source'})
            scene.command(self.pattern_command('wave', controls={'motion': False},
                                               palette=PALETTE))
            cell = scene.render().words()[4 * width + 5]
            self.assertEqual(cell[0], ord('A'))
            self.assertEqual(cell[1], expected[4 * width + 5])

    def test_source_field_query_samples_its_actual_xy(self):
        width, height = 20, 12
        expected = self.original([{
            'width': width, 'height': height, 'timeMs': 0,
            'values': {'2': KINDS.index('linear')}, 'palette': PALETTE,
        }])[0]['rgb']
        with NativeScene(2030) as scene:
            scene.command({'op': 'resize', 'width': width, 'height': height})
            scene.command({'op': 'material', 'id': 2, 'alpha': 1})
            scene.command({'op': 'field', 'effect': 'surface-field/satin-rings',
                           'optics': 'source', 'x': 5, 'y': 4, 'width': 1,
                           'speed': 0, 'strength': .7, 'lifeMs': 4000, 'seed': 0,
                           'continuous': True, 'material': 2})
            scene.command(self.pattern_command('linear', controls={'motion': False},
                                               palette=PALETTE))
            sample = scene.field_sample(1, 5, 4)
            self.assertEqual(sample[1], expected[4 * width + 5])
            self.assertNotEqual(sample[1], expected[4 * width + 6])

    def test_projected_electrical_arc_samples_material_per_covered_cell(self):
        from native.tests.test_electrical_graphs import arc as electrical_arc
        with NativeScene(2030) as baseline_scene, NativeScene(2030) as scene:
            for current in (baseline_scene, scene):
                current.command({'op': 'resize', 'width': 80, 'height': 30})
                current.command({'op': 'environment', 'stars': 0, 'style': 'solid'})
                current.command({'op': 'camera', 'position': [0, 0, 40], 'yaw': 0,
                                 'pitch': 0, 'roll': 0, 'near': .1, 'far': 200,
                                 'fov': 70, 'span': 40, 'orthographic': False})
                current.command({'op': 'material', 'id': 2, 'alpha': 1})
            scene.command(electrical_arc(points=[
                {'position': [-8, 0, 0], 'parent': -1},
                {'position': [8, 0, 0], 'parent': 0}],
                speed=100, holdMs=200, fadeMs=300, jitter=0, flicker=0, alpha=1))
            baseline_scene.advance_to(200_000)
            scene.advance_to(200_000)
            blank = baseline_scene.render().words()
            legacy = scene.render().words()
            scene.command(self.pattern_command('linear', controls={'motion': False},
                                               palette=PALETTE))
            patterned = scene.render().words()
            covered = [i for i in range(len(blank))
                       if legacy[i][:3] != blank[i][:3]]
            self.assertGreater(len(covered), 4)
            self.assertTrue(all(patterned[i][0] == legacy[i][0] for i in covered))
            self.assertTrue(any(patterned[i][1:3] != legacy[i][1:3] for i in covered))
            self.assertGreater(len({patterned[i][1] for i in covered}), 1)

    def test_legacy_material_behavior_null_clearing_and_snapshot_replay(self):
        width, height = 20, 12
        with NativeScene(42) as scene:
            scene.command({'op': 'resize', 'width': width, 'height': height})
            scene.command({'op': 'material', 'id': 2, 'space': 'rgb',
                           'channels': {'r': .2, 'g': .4, 'b': .6}, 'alpha': 1})
            scene.command({'op': 'widget', 'id': 1, 'kind': 'box', 'x': 3, 'y': 2,
                           'width': 11, 'height': 7, 'border': 'none', 'alpha': 1,
                           'backgroundMaterial': 2})
            legacy = scene.render()
            self.assertTrue(all(legacy.words()[y * width + x][2] == 0x336699
                                for y in range(2, 9) for x in range(3, 14)))
            scene.command(self.pattern_command('wave'))
            patterned = scene.render()
            self.assertNotEqual(patterned.bytes, legacy.bytes)
            saved = scene.snapshot()
            self.assertEqual(scene.render().bytes, patterned.bytes)
            self.assertEqual(scene.snapshot(), saved)
            scene.command({'op': 'material', 'id': 2, 'pattern': None})
            self.assertEqual(scene.render().bytes, legacy.bytes)
            scene.restore(saved)
            self.assertEqual(scene.render().bytes, patterned.bytes)

    def test_noncanonical_sampler_palette_tail_rejected_on_snapshot_restore(self):
        with NativeScene(42) as scene:
            scene.command({'op': 'material', 'id': 2, 'pattern': {
                'palette': [0x123456, 0x789abc]}})
            saved = scene.snapshot()
            prefix = struct.pack('<IIIII', 1, 0, 5, 0, 12800)
            self.assertEqual(saved.count(prefix), 1)
            record = saved.index(prefix)
            tail = record + 8 + 128 + 31 * 4
            changed = bytearray(saved)
            struct.pack_into('<I', changed, tail, 0x010203)
            struct.pack_into('<I', changed, 20, zlib.crc32(changed[24:]))
            with self.assertRaises(ValueError):
                scene.restore(changed)
            self.assertEqual(scene.snapshot(), saved)

    def test_schema66_restore_promotes_before_new_pattern_commands(self):
        with NativeScene(42) as scene:
            current = scene.snapshot()
            old = bytearray(current[:24 + 13_578_976])
            struct.pack_into('<I', old, 12, 0x20261066)
            struct.pack_into('<I', old, 28, 0x20261066)
            struct.pack_into('<I', old, 16, len(old) - 24)
            struct.pack_into('<I', old, 20, zlib.crc32(old[24:]))
            scene.restore(old)
            scene.command({'op': 'material', 'id': 2, 'pattern': {'kind': 'wave'}})
            self.assertEqual(scene.info_complete()['materialPatterns'][0]['kind'], 'wave')
            scene.command({'op': 'material', 'id': 2, 'pattern': None})
            self.assertEqual(scene.info_complete()['materialPatterns'], [])

    def test_snapshot_rejects_pattern_attached_to_unused_material_slot(self):
        with NativeScene(42) as scene:
            scene.command({'op': 'material', 'id': 2, 'pattern': {'kind': 'wave'}})
            saved = scene.snapshot()
            prefix = struct.pack('<IIIII', 1, 0, 3, 0, 12800)
            self.assertEqual(saved.count(prefix), 1)
            source = saved.index(prefix) - 2 * 264
            unused_slot = source + 4 * 264
            changed = bytearray(saved)
            changed[unused_slot:unused_slot + 264] = saved[source + 2 * 264:source + 3 * 264]
            struct.pack_into('<I', changed, 20, zlib.crc32(changed[24:]))
            with self.assertRaises(ValueError):
                scene.restore(changed)
            self.assertEqual(scene.snapshot(), saved)

    def test_schema66_snapshot_with_pending_pattern_null_is_rejected(self):
        with NativeScene(42) as scene:
            scene.command({'op': 'schedule', 'id': 9, 'atUs': 500000,
                           'command': {'op': 'material', 'id': 2, 'pattern': None}})
            current = scene.snapshot()
            old = bytearray(current[:24 + 13_578_976])
            struct.pack_into('<I', old, 12, 0x20261066)
            struct.pack_into('<I', old, 28, 0x20261066)
            struct.pack_into('<I', old, 16, len(old) - 24)
            struct.pack_into('<I', old, 20, zlib.crc32(old[24:]))
            before = scene.snapshot()
            with self.assertRaises(ValueError):
                scene.restore(old)
            self.assertEqual(scene.snapshot(), before)

if __name__ == '__main__':
    unittest.main()
