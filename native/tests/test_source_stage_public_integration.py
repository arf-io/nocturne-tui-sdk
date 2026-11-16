"""Retained public Stage components compared with actual RC2 Stage Wasm."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench

HTML_SHA = '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'
WASM_SHA = 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09'
STAGE_KINDS = ['text', 'box', 'rule', 'button', 'item', 'cursor', 'progress',
               'bars', 'pie', 'donut', 'scatter', 'line', 'digits', 'edge']
NODE_WORDS = 32


def source_node(kind, *, x, y, width, height, **values):
    """Build the exact original node words and the explicit RC4 opt-in command."""
    row = [0] * NODE_WORDS
    row[12], row[13], row[14], row[15] = 0xe2d9c9, 0x11100e, 1000, 0
    row[21], row[22], row[26], row[27], row[30] = 17, 24, 620, 830, 1
    row[0] = STAGE_KINDS.index(kind)
    row[1] = values.get('legacyFlags', 0)
    for field, word in (('x', 2), ('y', 3), ('width', 4), ('height', 5),
                        ('state', 6), ('value', 7), ('fromValue', 8),
                        ('durationMs', 11), ('fg', 12), ('bg', 13),
                        ('fgOpacity', 14), ('bgOpacity', 15), ('style', 16),
                        ('hueStep', 21), ('hueSpeed', 22), ('hueBase', 23),
                        ('revealMs', 24), ('hueSaturation', 26),
                        ('hueBrightness', 27), ('colorAnimation', 28),
                        ('glyph', 29), ('zoom', 30)):
        if field in values:
            row[word] = values[field]
    row[2], row[3], row[4], row[5] = x, y, width, height
    row[9] = values.get('changedMs', 0) & 0xffffffff
    row[10] = values.get('changedMs', 0) >> 32
    text = values.get('text', '')
    data = values.get('data', [])
    row[17], row[18] = 0, len(text)
    row[19], row[20] = 0, len(data)
    return row, text, data


def stage_command(entity_id, kind, *, material_id=0, **values):
    return {'op': 'source-stage-component', 'id': entity_id, 'kind': kind,
            'materialId': material_id, **values}


def prepare_scene(scene, width, height):
    """Keep source primitive comparisons isolated from SDK presentation layers."""
    scene.command({'op': 'resize', 'width': width, 'height': height})
    scene.command({'op': 'prompt', 'active': False})
    scene.command({'op': 'environment', 'stars': 0, 'background': 0x11100e})
    scene.command({'op': 'floor', 'enabled': False, 'visible': False})


class RetainedStageIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = load_rc2_workbench().encode('utf-8')
        if hashlib.sha256(html).hexdigest() != HTML_SHA:
            raise AssertionError('portable original rc.2 fixture custody mismatch')
        cls.temp = tempfile.TemporaryDirectory(prefix='source-stage-public-')
        cls.htmlPath = Path(cls.temp.name) / 'original-rc2.html'
        cls.htmlPath.write_bytes(html)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def source_paint(self, frame, nodes, text, data, time_ms,
                     oracle_width=None, oracle_height=None):
        width = frame.width if oracle_width is None else oracle_width
        height = frame.height if oracle_height is None else oracle_height
        words = frame.words()
        cells = [word for y in range(height)
                 for cell in words[y * frame.width:y * frame.width + width]
                 for word in cell]
        request = {'width': width, 'height': height, 'timeMs': time_ms,
                   'cells': cells, 'nodes': nodes, 'text': text, 'data': data}
        result = subprocess.run(
            ['node', str(ROOT / 'tests/original_rc2_stage_paint_oracle.mjs'), str(self.htmlPath)],
            input=json.dumps([request]), capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        oracle = json.loads(result.stdout)
        self.assertEqual(oracle['editionSha256'], HTML_SHA)
        self.assertEqual(oracle['wasmSha256'], WASM_SHA)
        return oracle['cases'][0]

    def original_material_rgb(self, width, height, time_ms, palette):
        request = {'width': width, 'height': height, 'timeMs': time_ms,
                   'values': {'2': 1}, 'palette': palette}
        result = subprocess.run(
            ['node', str(ROOT / 'tests/original_rc2_surface_sampler_oracle.mjs'), str(self.htmlPath)],
            input=json.dumps([request]), capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        oracle = json.loads(result.stdout)
        self.assertEqual(oracle['editionSha256'], HTML_SHA)
        self.assertEqual(oracle['wasmSha256'], WASM_SHA)
        return oracle['results'][0]['rgb']

    @staticmethod
    def assert_visible_cells_match(test, actual, expected):
        got = actual.words()
        test.assertEqual(len(got), len(expected))
        for index, want in enumerate(expected):
            test.assertEqual(got[index][:3], tuple(want[:3]), ('cell', index))

    def test_all_fourteen_public_source_kinds_match_original_wasm_over_same_cells(self):
        # Disjoint source rectangles avoid accidental cross-kind occlusion while
        # still exercising the real retained source-order array in one render.
        placements = [
            ('text', 2, 6, 8, 4, {'text': 'A中\nB9', 'revealMs': 50}),
            ('box', 16, 6, 10, 5, {'style': 2}),
            ('rule', 29, 6, 12, 1, {'style': 8}),
            ('button', 45, 6, 10, 5, {'style': 1, 'text': 'OK!'}),
            ('item', 59, 6, 8, 2, {'state': 2, 'text': 'x'}),
            ('cursor', 2, 15, 3, 2, {'style': 4, 'glyph': 0}),
            ('progress', 8, 15, 12, 1, {'style': 1, 'value': 637}),
            ('bars', 23, 15, 12, 5, {'data': [100, 900, -30, 1200]}),
            ('pie', 38, 15, 12, 6, {'data': [300, 200, 100, 250, 150]}),
            ('donut', 53, 15, 12, 6, {'data': [300, 200, 100, 250, 150]}),
            ('scatter', 2, 26, 12, 6, {'style': 1, 'data': [0, 0, 500, 500, 1000, 1000]}),
            ('line', 18, 26, 12, 6, {'data': [0, 0, 500, 1000, 1000, 0]}),
            ('digits', 34, 26, 18, 7, {'text': '18-0', 'zoom': 1}),
            ('edge', 56, 26, 12, 6, {'data': [0, 0, 500, 1000, 1000, 0]}),
        ]
        time_ms = 1_200
        with NativeScene(2030) as scene:
            prepare_scene(scene, 72, 40)
            scene.advance_to(time_ms * 1000)
            base = scene.render()
            nodes, text_values, data_values = [], [], []
            for index, (kind, x, y, width, height, extra) in enumerate(placements):
                options = {'x': x, 'y': y, 'width': width, 'height': height,
                           'legacyFlags': 41 + index, 'fg': 0xe2d9c9, 'bg': 0x11100e,
                           'fgOpacity': 1000, 'bgOpacity': 0, **extra}
                row, text, data = source_node(kind, **options)
                row[17] = len(text_values); row[19] = len(data_values)
                text_values.extend(map(ord, text)); data_values.extend(data)
                row[18], row[20] = len(text), len(data)
                nodes.append(row)
                scene.command(stage_command(300 + index, kind, **options))
            expected = self.source_paint(base, nodes, text_values, data_values,
                                         time_ms)
            self.assert_visible_cells_match(self, scene.render(), expected)

    def test_current_wasm_all_fourteen_source_kinds_match_native_and_original(self):
        placements = [
            ('text', 2, 6, 8, 4, {'text': 'A中\nB9', 'revealMs': 50}),
            ('box', 16, 6, 10, 5, {'style': 2}),
            ('rule', 29, 6, 12, 1, {'style': 8}),
            ('button', 45, 6, 10, 5, {'style': 1, 'text': 'OK!'}),
            ('item', 59, 6, 8, 2, {'state': 2, 'text': 'x'}),
            ('cursor', 2, 15, 3, 2, {'style': 4, 'glyph': 0}),
            ('progress', 8, 15, 12, 1, {'style': 1, 'value': 637}),
            ('bars', 23, 15, 12, 5, {'data': [100, 900, -30, 1200]}),
            ('pie', 38, 15, 12, 6, {'data': [300, 200, 100, 250, 150]}),
            ('donut', 53, 15, 12, 6, {'data': [300, 200, 100, 250, 150]}),
            ('scatter', 2, 26, 12, 6, {'style': 1, 'data': [0, 0, 500, 500, 1000, 1000]}),
            ('line', 18, 26, 12, 6, {'data': [0, 0, 500, 1000, 1000, 0]}),
            ('digits', 34, 26, 18, 7, {'text': '18-0', 'zoom': 1}),
            ('edge', 56, 26, 12, 6, {'data': [0, 0, 500, 1000, 1000, 0]}),
        ]
        time_ms = 1200
        commands = [
            {'op': 'resize', 'width': 72, 'height': 40},
            {'op': 'prompt', 'active': False},
            {'op': 'environment', 'stars': 0, 'background': 0x11100e},
            {'op': 'floor', 'enabled': False, 'visible': False},
        ]
        nodes, texts, data_values = [], [], []
        with NativeScene(2030) as scene:
            for command in commands:
                scene.command(command)
            scene.advance_to(time_ms * 1000)
            base = scene.render()
            for index, (kind, x, y, width, height, extra) in enumerate(placements):
                options = {'x': x, 'y': y, 'width': width, 'height': height,
                           'legacyFlags': 141 + index, 'fg': 0xe2d9c9, 'bg': 0x11100e,
                           'fgOpacity': 1000, 'bgOpacity': 0, **extra}
                row, text, data = source_node(kind, **options)
                row[17] = len(texts); row[19] = len(data_values)
                texts.extend(map(ord, text)); data_values.extend(data)
                row[18], row[20] = len(text), len(data)
                nodes.append(row)
                commands.append(stage_command(800 + index, kind, **options))
                scene.command(commands[-1])
            expected = self.source_paint(base, nodes, texts, data_values,
                                         time_ms)
            self.assert_visible_cells_match(self, scene.render(), expected)
            native_bytes = scene.render().bytes

            with tempfile.TemporaryDirectory(prefix='source-stage-wasm-public-') as output:
                request_path = Path(output) / 'request.json'
                request_path.write_text(json.dumps({
                    'commands': commands,
                    'timeUs': time_ms * 1000,
                    'invalidCommand': {'op': 'source-stage-component', 'id': 999,
                                       'kind': 'text', 'width': 1, 'height': 1,
                                       'extraSourceField': 1},
                }))
                completed = subprocess.run(
                    ['node', str(ROOT / 'tests/source_stage_public_wasm_runner.mjs'),
                     str(request_path), output],
                    cwd=ROOT / 'bindings/typescript', text=True, capture_output=True,
                    timeout=120, check=False)
                report_path = Path(output) / 'report.json'
                diagnostic = completed.stdout + completed.stderr
                if report_path.exists():
                    diagnostic += '\nPartial WASM report:\n' + report_path.read_text()
                self.assertEqual(completed.returncode, 0, diagnostic)
                report = json.loads(report_path.read_text())
                self.assertEqual(report['snapshotSchema'], current_schema())
                self.assertEqual(report['sourceSchema'], current_schema())
                self.assertTrue(report['invalidRejected'])
                self.assertTrue(report['snapshotReplayIdentical'])
                wasm_bytes = (Path(output) / report['cellsFile']).read_bytes()
                self.assertEqual(wasm_bytes, native_bytes)
                self.assert_visible_cells_match(self, scene.render(), expected)
                self.assertEqual(report['sourceStageComponents'], 14)

    def test_source_opacity_animation_and_source_order_match_original(self):
        components = [
            ('rule', 4, 8, 12, 1, {'style': 8, 'colorAnimation': 1,
                                   'hueStep': 37, 'hueSpeed': 511, 'hueBase': 19000,
                                   'hueSaturation': 733, 'hueBrightness': 680,
                                   'state': 3, 'fgOpacity': 730}),
            ('cursor', 8, 8, 2, 1, {'style': 0, 'legacyFlags': 92}),
            ('pie', 24, 8, 12, 6, {'data': [1, 2, 3, 4], 'fgOpacity': 820}),
            ('donut', 40, 8, 12, 6, {'data': [4, 3, 2, 1], 'bgOpacity': 370,
                                     'bg': 0x31507f}),
            ('digits', 54, 8, 18, 7, {'text': '8-7', 'zoom': 1}),
        ]
        with NativeScene(2030) as scene:
            prepare_scene(scene, 76, 24)
            scene.advance_to(479_000)
            base = scene.render()
            nodes, texts, data_values = [], [], []
            for index, (kind, x, y, width, height, extra) in enumerate(components):
                options = {'x': x, 'y': y, 'width': width, 'height': height,
                           'legacyFlags': 81 + index, 'fg': 0xe2d9c9, 'bg': 0x11100e,
                           'fgOpacity': 1000, 'bgOpacity': 0, **extra}
                row, text, data = source_node(kind, **options)
                row[17], row[19] = len(texts), len(data_values)
                texts.extend(map(ord, text)); data_values.extend(data)
                row[18], row[20] = len(text), len(data)
                nodes.append(row)
                scene.command(stage_command(400 + index, kind, **options))
            expected = self.source_paint(base, nodes, texts, data_values, 479)
            self.assert_visible_cells_match(self, scene.render(), expected)

    def test_opt_in_sdk_material_pattern_uses_exact_absolute_stage_cell_colors(self):
        width, height, time_ms = 32, 18, 700
        palette = [0x18304f, 0x806090, 0x35a078]
        with NativeScene(2030) as scene:
            prepare_scene(scene, width, height)
            scene.advance_to(time_ms * 1000)
            base = scene.render()
            scene.command({'op': 'material', 'id': 2, 'alpha': 1,
                           'pattern': {'kind': 'linear', 'palette': palette}})
            scene.command(stage_command(550, 'text', x=7, y=8, width=6, height=1,
                                        text='PATTERN', materialId=3,
                                        fg=0xffffff, fgOpacity=1000, legacyFlags=55))
            self.assertEqual(scene.info()['sourceStageComponents'][0]['materialId'], 3)
            expected = self.source_paint(
                base, [source_node('text', x=7, y=8, width=6, height=1,
                                   text='PATTERN', fg=0xffffff, fgOpacity=1000,
                                   legacyFlags=55)[0]], list(map(ord, 'PATTERN')), [],
                time_ms)
            samples = self.original_material_rgb(width, height, time_ms, palette)
            actual = scene.render().words()
            for offset in range(6):
                at = 8 * width + 7 + offset
                self.assertEqual(actual[at][0], expected[at][0])
                self.assertEqual(actual[at][1], samples[at], ('pattern RGB', 7 + offset, 8))

    def test_widget_meanings_remain_byte_identical_after_stage_remove_and_snapshot_replay(self):
        with NativeScene(2030) as scene, NativeScene(2030) as baseline:
            for target in (scene, baseline):
                prepare_scene(target, 40, 20)
                target.command({'op': 'widget', 'id': 1, 'kind': 'donut', 'x': 8, 'y': 6,
                                'width': 20, 'height': 8, 'data': [2, 3, 5],
                                'innerRadius': .45, 'sampling': 'braille'})
            before = scene.render().bytes
            self.assertEqual(before, baseline.render().bytes)
            scene.command(stage_command(501, 'rule', x=5, y=16, width=20, height=1,
                                        style=8, legacyFlags=71))
            saved = scene.snapshot()
            rendered = scene.render().bytes
            scene.command({'op': 'remove-source-stage-component', 'id': 501})
            self.assertEqual(scene.render().bytes, before)
            scene.restore(saved)
            self.assertEqual(scene.render().bytes, rendered)
            self.assertEqual(scene.info()['sourceStageComponents'][0]['id'], 501)

    def test_update_keeps_component_order_when_overlapping_later_source(self):
        with NativeScene(2030) as scene:
            prepare_scene(scene, 32, 16)
            base = scene.render()
            scene.command(stage_command(511, 'rule', x=4, y=7, width=20,
                                        height=1, style=2, legacyFlags=11))
            scene.command(stage_command(512, 'cursor', x=12, y=7, width=2,
                                        height=1, glyph=0, legacyFlags=12))
            # Patching the first stable ID must not move it above the second
            # retained source operation in draw order.
            scene.command(stage_command(511, 'rule', x=4, y=7, width=20,
                                        height=1, style=8, legacyFlags=13))
            first, first_text, first_data = source_node(
                'rule', x=4, y=7, width=20, height=1, style=8,
                legacyFlags=13)
            second, second_text, second_data = source_node(
                'cursor', x=12, y=7, width=2, height=1, glyph=0,
                legacyFlags=12)
            expected = self.source_paint(
                base, [first, second], first_text + second_text,
                first_data + second_data, 0)
            self.assert_visible_cells_match(self, scene.render(), expected)

    def test_invalid_source_component_is_atomic_and_rejects_unknown_kind_or_bad_data(self):
        with NativeScene(2030) as scene:
            prepare_scene(scene, 24, 16)
            before = scene.snapshot()
            for command in (
                stage_command(601, 'unknown', x=1, y=5, width=4, height=1),
                stage_command(601, 'bars', x=1, y=5, width=4, height=1,
                              data=[100, 1_000_001]),
                stage_command(601, 'text', x=1, y=5, width=0, height=1),
                stage_command(601, 'rule', x=1, y=5, width=4,
                              height=536_870_912),
                {'op': 'source-stage-component', 'id': 601, 'kind': 'text',
                 'x': 1, 'y': 5, 'width': 4, 'height': 1, 'extraSourceField': 1},
            ):
                with self.subTest(command=command), self.assertRaises(ValueError):
                    scene.command(command)
                self.assertEqual(scene.snapshot(), before)

    def test_source_components_accept_viewports_beyond_original_ui_limits(self):
        with NativeScene(2030) as scene:
            prepare_scene(scene, 600, 257)
            base = scene.render()
            scene.command(stage_command(701, 'rule', x=0, y=128, width=600,
                                        height=1, style=8, legacyFlags=99))
            frame = scene.render()
            self.assertEqual((frame.width, frame.height), (600, 257))
            self.assertTrue(any(frame.words()[128 * 600 + x][0] != 32
                                for x in range(600)))
            # RC2 node-domain parity is exact through its 512x256 source bound.
            # The retained RC4 component extends the same rule over the extra
            # visible columns; compare the original-covered region cell-for-cell.
            # RC2's frame initializer accepts only 512x256. Build the oracle
            # input at that real limit, then compare its cells with the matching
            # upper-left region of RC4's larger frame.
            row, text, data = source_node('rule', x=0, y=128, width=512,
                                          height=1, style=8, legacyFlags=99)
            expected = self.source_paint(
                base, [row], text, data, 0,
                oracle_width=512, oracle_height=256)
            got, want = frame.words(), expected
            for x in range(512):
                actual_at, expected_at = 128 * frame.width + x, 128 * 512 + x
                self.assertEqual(got[actual_at][:3], tuple(want[expected_at][:3]),
                                 ('cell', x, 128))
            self.assertTrue(any(got[128 * 600 + x][0] != 32 for x in range(512, 600)))


if __name__ == '__main__':
    unittest.main()
