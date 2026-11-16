"""Exact source appearance probes for selected historical Stage components.

Positive: exact rc.2 Wasm render output and source-derived variant checks.
Negative: original renderer rejects invalid node records before any output is
accepted. Current-frame integration is owned by the parent compositor concern.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import hashlib
import json
import ctypes
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native.tests.historical_reference import load_rc2_workbench

ROOT = Path(__file__).resolve().parents[1]
HTML_SHA = '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'
WASM_SHA = 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09'
FIELDS = dict(kind=0, id=1, x=2, y=3, width=4, height=5, state=6, value=7,
              from_value=8, changed_lo=9, changed_hi=10, duration=11, fg=12,
              bg=13, fg_opacity=14, bg_opacity=15, style=16, text_offset=17,
              text_length=18, data_offset=19, data_length=20, hue_step=21,
              hue_speed=22, hue_base=23, reveal=24, saturation=26,
              brightness=27, animation=28, glyph=29, zoom=30)


class Material(ctypes.Structure):
    _fields_ = [('pattern', ctypes.c_uint32), ('focusMode', ctypes.c_uint32),
                ('focusXQ8', ctypes.c_int32), ('focusYQ8', ctypes.c_int32),
                ('periodMs', ctypes.c_uint32), ('saturationMilli', ctypes.c_int32),
                ('brightnessMilli', ctypes.c_int32), ('speedFalloffMilli', ctypes.c_uint32),
                ('saturationFalloffMilli', ctypes.c_uint32), ('brightnessFalloffMilli', ctypes.c_uint32),
                ('cellAspectMilli', ctypes.c_uint32), ('scaleQ8', ctypes.c_uint32),
                ('angleMilliDegrees', ctypes.c_int32), ('pivotXQ8', ctypes.c_int32),
                ('pivotYQ8', ctypes.c_int32), ('rotationPeriodMs', ctypes.c_uint32),
                ('rotationMode', ctypes.c_uint32), ('swingMilliDegrees', ctypes.c_int32),
                ('phase1024', ctypes.c_int32), ('seed', ctypes.c_uint32),
                ('baseRgb', ctypes.c_uint32), ('inkRgb', ctypes.c_uint32),
                ('paletteCount', ctypes.c_uint32), ('gradientWrap', ctypes.c_uint32),
                ('interpolation', ctypes.c_uint32), ('colorMode', ctypes.c_uint32),
                ('hueOffsetDegrees', ctypes.c_int32), ('motion', ctypes.c_uint32),
                ('originXCells', ctypes.c_int32), ('originYCells', ctypes.c_int32),
                ('waveAmplitudeMilli', ctypes.c_uint32), ('reverse', ctypes.c_uint32),
                ('palette', ctypes.c_uint32 * 32)]


class StageCell(ctypes.Structure):
    _fields_ = [('glyph', ctypes.c_uint32), ('foregroundRgb', ctypes.c_uint32),
                ('backgroundRgb', ctypes.c_uint32), ('legacyFlags', ctypes.c_uint32),
                ('semanticOwner', ctypes.c_uint32)]


class Component(ctypes.Structure):
    _fields_ = [('node', ctypes.c_int32 * 32), ('text', ctypes.POINTER(ctypes.c_uint32)),
                ('textCount', ctypes.c_uint32), ('data', ctypes.POINTER(ctypes.c_int32)),
                ('dataCount', ctypes.c_uint32), ('timeMs', ctypes.c_uint64),
                ('material', ctypes.POINTER(Material)), ('baseColor', ctypes.c_uint32),
                ('semanticOwner', ctypes.c_uint32)]


READ = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32,
                        ctypes.POINTER(StageCell))
CELL = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32,
                        ctypes.c_uint32,
                        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                        ctypes.c_uint32, ctypes.c_uint32)
SUBCELL = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32,
                           ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                           ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32)


class Sink(ctypes.Structure):
    _fields_ = [('context', ctypes.c_void_p), ('frameWidth', ctypes.c_int32),
                ('frameHeight', ctypes.c_int32), ('readCell', READ), ('cell', CELL),
                ('subcell', SUBCELL)]


def node(kind, **values):
    row = [0] * 32
    row[FIELDS['kind']] = kind
    row[FIELDS['width']] = 12
    row[FIELDS['height']] = 4
    row[FIELDS['fg']] = 0xe2d9c9
    row[FIELDS['bg']] = 0x11100e
    row[FIELDS['fg_opacity']] = 1000
    row[FIELDS['bg_opacity']] = 0
    row[FIELDS['zoom']] = 1
    for name, value in values.items():
        row[FIELDS[name]] = value
    return row


class OriginalStageComponentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = load_rc2_workbench().encode('utf-8')
        if hashlib.sha256(html).hexdigest() != HTML_SHA:
            raise AssertionError('original HTML custody mismatch')
        cls.temp = tempfile.TemporaryDirectory(prefix='historical-stage-components-')
        cls.originalPath = Path(cls.temp.name) / 'original-rc2.html'
        cls.originalPath.write_bytes(html)
        cls.libraryPath = Path(cls.temp.name) / 'libsource_stage_components.so'
        command = [os.environ.get('CC', 'cc'), '-std=c11', '-O2', '-fPIC', '-shared',
                   '-I', str(ROOT / 'src'), str(ROOT / 'src/source_material_sampler.c'),
                   str(ROOT / 'src/source_stage_components.c'), '-o', str(cls.libraryPath)]
        built = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        cls.lib = ctypes.CDLL(str(cls.libraryPath))
        cls.lib.nrSourceMaterialSamplerDefaults.argtypes = [ctypes.POINTER(Material)]
        cls.lib.nrSourceMaterialSampleColor.argtypes = [ctypes.POINTER(Material), ctypes.c_uint64,
                                                       ctypes.c_int32, ctypes.c_int32,
                                                       ctypes.POINTER(ctypes.c_uint32)]
        cls.lib.nrSourceMaterialSampleColor.restype = ctypes.c_int
        cls.lib.nrSourceStageComponentApply.argtypes = [ctypes.POINTER(Component), ctypes.POINTER(Sink)]
        cls.lib.nrSourceStageComponentApply.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    def render(self, request):
        completed = subprocess.run(
            ['node', str(ROOT / 'tests/original_rc2_surface_sampler_oracle.mjs'), str(self.originalPath)],
            input=json.dumps([{'width': 24, 'height': 12, 'timeMs': 0, **request}]),
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result['editionSha256'], HTML_SHA)
        self.assertEqual(result['wasmSha256'], WASM_SHA)
        return result['results'][0]['cells']

    @staticmethod
    def mix(a, b, p):
        p = max(0, min(1000, p))
        return sum((((a >> shift) & 255) + ((((b >> shift) & 255) - ((a >> shift) & 255)) * p // 1000)) << shift
                   for shift in (16, 8, 0))

    def compare_module(self, request, nodeRow, text=None, data=None, time_ms=0,
                       palette=None, wrap=0, interpolation=1, color_mode=0):
        width, height = 24, 12
        rows = [nodeRow] if not nodeRow or isinstance(nodeRow[0], int) else nodeRow
        source_values = {'2': 0, **(request or {})}
        base = self.render({'values': source_values, 'timeMs': time_ms,
                            'palette': palette} if palette else {'values': source_values, 'timeMs': time_ms})
        raster = [list(cell) for cell in base]
        owners = [0] * (width * height)
        explicit_events = []
        def read(_ctx, x, y, out):
            if x < 0 or y < 0 or x >= width or y >= height:
                return -1
            c = raster[y * width + x]
            out.contents.glyph = c[0]
            out.contents.foregroundRgb = c[1]
            out.contents.backgroundRgb = c[2]
            out.contents.legacyFlags = c[3]
            out.contents.semanticOwner = owners[y * width + x]
            return 0
        def apply_cell(_ctx, x, y, operation, glyph, fg, fg_alpha, bg, bg_alpha, bg_explicit, flags, owner):
            if x < 0 or y < 0 or x >= width or y >= height:
                return
            i = y * width + x
            old = raster[i]
            if operation == 1:  # NR_SOURCE_CELL_FILL
                explicit_events.append((x, y, glyph, fg, fg_alpha, bg, bg_alpha, old[:]))
                flat = self.mix(old[2], old[1], 500) if old[0] in (0x2580, 0x258c) else old[2]
                new_bg = self.mix(flat, bg, bg_alpha) if bg_alpha else old[2]
                fgbase = new_bg if bg_alpha else flat
                new_fg = self.mix(old[1], fgbase, fg_alpha) if fg_alpha else old[1]
                raster[i] = [glyph, new_fg, new_bg, flags or old[3]]
            elif operation == 2:  # NR_SOURCE_CELL_FLATTEN
                raster[i] = [glyph, old[1], bg, flags or old[3]]
            elif operation == 3:  # NR_SOURCE_CELL_BACKGROUND_TINT
                raster[i] = [glyph, old[1], bg, old[3]]
            else:
                flat = self.mix(old[2], old[1], 500) if old[0] in (0x2580, 0x258c) else old[2]
                raster[i] = [glyph, self.mix(flat, fg, fg_alpha), flat, flags or old[3]]
            if operation not in (2, 3) and owner:
                owners[i] = owner
        def apply_subcell(_ctx, x, y, sx, sy, rgb, alpha, coverage, flags, _owner):
            if not coverage or x < 0 or y < 0 or x >= width or y >= height:
                return
            i = y * width + x
            bits = (1, 8, 2, 16, 4, 32, 64, 128)
            if raster[i][0] < 0x2800 or raster[i][0] > 0x28ff:
                raster[i][0] = 0x2800
            raster[i][0] |= bits[sy * 2 + sx]
            raster[i][1] = self.mix(raster[i][2], rgb, alpha)
            raster[i][3] = flags
        read_cb, cell_cb, sub_cb = READ(read), CELL(apply_cell), SUBCELL(apply_subcell)
        sink = Sink(None, width, height, read_cb, cell_cb, sub_cb)
        tvals = (ctypes.c_uint32 * len(text))(*text) if text else None
        dvals = (ctypes.c_int32 * len(data))(*data) if data else None
        mat = Material()
        self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(mat))
        if palette:
            mat.paletteCount = len(palette)
            for i, color in enumerate(palette):
                mat.palette[i] = color
        mat.gradientWrap = wrap
        mat.interpolation = interpolation
        mat.colorMode = color_mode
        # Match the exact five-stop Stage default palette while keeping the
        # pattern irrelevant to this primitive-only test.
        for row in rows:
            component = Component((ctypes.c_int32 * 32)(*row), tvals, len(text or []),
                                  dvals, len(data or []), time_ms, ctypes.pointer(mat),
                                  0x11100e, 0xabc)
            result = self.lib.nrSourceStageComponentApply(ctypes.byref(component), ctypes.byref(sink))
            self.assertEqual(result, 0)
        actual = [tuple(c) for c in raster]
        expected = self.render({'values': source_values, 'nodes': rows, 'text': text or [],
                                'data': data or [], 'timeMs': time_ms,
                                **({'palette': palette} if palette else {})})
        self.assertEqual(actual, [tuple(c) for c in expected], explicit_events[:4])
        return owners

    def test_oracle_returns_full_cells_and_proves_all_five_known_variants(self):
        rule = [self.render({'nodes': [node(2, width=12, height=1, style=s)]}) for s in range(12)]
        self.assertEqual(len({tuple(c[0] for c in frame) for frame in rule}), 12)
        progress = [self.render({'nodes': [node(6, width=12, height=1, style=s, value=625)]})
                    for s in range(3)]
        self.assertEqual(len({tuple(c[0] for c in frame) for frame in progress}), 3)
        pie_data = [250, 300, 450]
        palettes = [[0xff0000, 0x00ff00, 0x0000ff], [0x101010, 0xeeeeee, 0xff00ff]]
        pie_frames = [self.render({'nodes': [node(8, width=12, height=6, data_offset=0,
                                                  data_length=3)], 'data': pie_data,
                                   'palette': p}) for p in palettes]
        self.assertNotEqual(pie_frames[0], pie_frames[1])
        digit_a = self.render({'nodes': [node(12, width=12, height=6, text_offset=0,
                                               text_length=2)], 'text': [ord('1'), ord('2')]})
        digit_b = self.render({'nodes': [node(12, width=12, height=6, text_offset=0,
                                               text_length=2)], 'text': [ord('8'), ord('-')]})
        self.assertNotEqual(digit_a, digit_b)
        self.assertEqual(len(digit_a), 24 * 12)

    def test_native_primitives_reconstruct_exact_original_component_frames(self):
        for style in range(12):
            self.compare_module({}, node(2, x=2, y=3, width=12, height=1,
                                         style=style, id=41), time_ms=300)
        for style in range(3):
            self.compare_module({}, node(6, x=2, y=3, width=12, height=1,
                                         style=style, value=637, id=42))
        for kind in (8, 9):
            self.compare_module({}, node(kind, x=5, y=2, width=12, height=6,
                                         data_length=5, id=43), data=[300, 200, 100, 250, 150])
            self.compare_module({25: 3, 26: 1, 27: 0}, node(kind, x=5, y=2, width=12, height=6,
                                                             data_length=5, id=43),
                                data=[300, 200, 100, 250, 150],
                                palette=[0xff0000, 0x00ff00, 0x0000ff], wrap=1, interpolation=0)
        self.compare_module({}, node(12, x=2, y=2, width=18, height=7,
                                     text_length=4, zoom=1, id=44),
                            text=[ord(c) for c in '18-0'])

    def test_node_color_modes_and_partial_fill_match_original_integer_rounding(self):
        for animation in range(4):
            with self.subTest(animation=animation):
                self.compare_module({}, node(2, x=2, y=3, width=12, height=1, style=3,
                                             id=45, animation=animation, hue_step=37,
                                             hue_speed=511, hue_base=19000,
                                             saturation=733, brightness=680, state=3))
        self.compare_module({}, node(6, x=2, y=3, width=12, height=1, value=410,
                                     bg_opacity=430, bg=0x31507f, id=46))

    def test_native_primitives_reconstruct_exact_frames_for_remaining_nine_kinds(self):
        authored = list(map(ord, 'A中\nB9'))
        text_node = node(0, x=2, y=1, width=6, height=4,
                         text_length=len(authored), reveal=50, id=51)
        self.compare_module({}, text_node, text=authored, time_ms=100)
        for kind in (1, 3):
            for style in range(4):
                row = node(kind, x=2, y=2, width=10, height=5, style=style,
                           text_length=3, id=52)
                self.compare_module({}, row, text=list(map(ord, 'OK!')))
        for state in range(4):
            self.compare_module({}, node(4, x=2, y=2, width=8, height=2,
                                         state=state, text_length=1, id=53), text=[ord('x')])
        for style in range(5):
            self.compare_module({}, node(5, x=5, y=4, width=3, height=2,
                                         style=style, id=54), time_ms=479)
        self.compare_module({}, node(7, x=2, y=2, width=12, height=5, value=810,
                                    duration=700, data_length=4, id=55),
                            data=[100, 900, -30, 1200], time_ms=221)
        for style in range(2):
            self.compare_module({}, node(10, x=2, y=2, width=12, height=6,
                                         style=style, data_length=6, id=56),
                                data=[0, 0, 500, 500, 1000, 1000])
        for kind, data in ((11, [0, 1000, 500, 500, 1000, 0]),
                           (13, [0, 0, 500, 1000, 1000, 0])):
            row = node(kind, x=2, y=2, width=12, height=6,
                       data_length=len(data), duration=0, id=57)
            self.compare_module({}, row, data=data, time_ms=1199)

    def test_cursor_background_tint_and_layer_flags_preserve_prior_composed_cell(self):
        text = [ord('A')]
        layers = [node(0, x=5, y=4, width=1, height=1, text_length=1, id=61),
                  node(5, x=5, y=4, width=1, height=1, style=0, id=62)]
        owners = self.compare_module({}, layers, text=text, time_ms=0)
        self.assertEqual(owners[4 * 24 + 5], 0xabc)
        owners = self.compare_module({}, layers, text=text, time_ms=400)
        self.assertEqual(owners[4 * 24 + 5], 0xabc)

    def test_rule_animation_and_pie_donut_have_actual_source_glyph_motion(self):
        req = {'nodes': [node(2, width=12, height=1, style=8)]}
        self.assertNotEqual(self.render({**req, 'timeMs': 0}),
                            self.render({**req, 'timeMs': 150}))
        data = [1, 2, 3, 4]
        pie = self.render({'nodes': [node(8, width=12, height=6, data_length=4)], 'data': data})
        donut = self.render({'nodes': [node(9, width=12, height=6, data_length=4)], 'data': data})
        self.assertNotEqual(tuple(c[0] for c in pie), tuple(c[0] for c in donut))

    def test_original_oracle_exposes_distinct_frames_for_the_other_nine_kinds(self):
        text_data = [ord(c) for c in 'A中\nB9']
        text_node = node(0, x=2, y=1, width=6, height=4, text_length=len(text_data))
        whole = self.render({'values': {'2': 0}, 'nodes': [text_node], 'text': text_data})
        revealed = self.render({'values': {'2': 0}, 'timeMs': 100,
                                'nodes': [node(0, x=2, y=1, width=6, height=4,
                                               text_length=len(text_data), reveal=50)],
                                'text': text_data})
        self.assertNotEqual(whole, revealed)
        box = [self.render({'values': {'2': 0}, 'nodes': [node(1, x=2, y=2, width=10,
                                                                height=5, style=s)]}) for s in range(4)]
        self.assertEqual(len({tuple(c[0] for c in f) for f in box}), 4)
        button = self.render({'values': {'2': 0}, 'nodes': [node(3, x=2, y=2, width=10,
                                                                  height=5, style=2,
                                                                  text_length=3)],
                              'text': list(map(ord, 'OK!'))})
        self.assertNotEqual(button, box[2])
        items = [self.render({'values': {'2': 0}, 'nodes': [node(4, x=2, y=2, width=8,
                                                                  height=2, state=s,
                                                                  text_length=1)],
                              'text': [ord('x')]}) for s in range(4)]
        self.assertEqual(len({tuple(c[0] for c in f) for f in items}), 4)
        cursors = [self.render({'values': {'2': 0}, 'nodes': [node(5, x=5, y=4, width=3,
                                                                    height=2, style=s)]})
                   for s in range(5)]
        self.assertGreaterEqual(len({tuple(c[0] for c in f) for f in cursors}), 4)
        bars = [self.render({'values': {'2': 0}, 'nodes': [node(7, x=2, y=2, width=12,
                                                                 height=5, data_length=len(d))],
                             'data': d}) for d in ([100, 900], [900, 100], [-20, 500, 1200])]
        self.assertEqual(len(set(tuple(c[0] for c in f) for f in bars)), 3)
        scatter = [self.render({'values': {'2': 0}, 'nodes': [node(10, x=2, y=2, width=12,
                                                                      height=6, style=s,
                                                                      data_length=6)],
                                'data': [0, 0, 500, 500, 1000, 1000]}) for s in range(2)]
        self.assertNotEqual(scatter[0], scatter[1])
        line_frames = [self.render({'values': {'2': 0}, 'nodes': [node(11, x=2, y=2,
                                                                         width=12, height=6,
                                                                         data_length=len(d))],
                                    'data': d}) for d in ([0, 1000], [1000, 0], [0, 500, 1000])]
        self.assertEqual(len(set(tuple(c[0] for c in f) for f in line_frames)), 3)
        edge = [self.render({'values': {'2': 0}, 'timeMs': t,
                             'nodes': [node(13, x=2, y=2, width=12, height=6,
                                            data_length=6)] ,
                             'data': [0, 0, 500, 1000, 1000, 0]}) for t in (0, 1200)]
        self.assertNotEqual(edge[0], edge[1])

    def test_negative_original_oracle_rejects_out_of_domain_data(self):
        invalid = node(7, x=2, y=2, width=12, height=5, data_length=2)
        completed = subprocess.run(
            ['node', str(ROOT / 'tests/original_rc2_surface_sampler_oracle.mjs'), str(self.originalPath)],
            input=json.dumps([{'width': 24, 'height': 12, 'timeMs': 0,
                               'values': {'2': 0}, 'nodes': [invalid], 'data': [100, 1000001]}]),
            capture_output=True, text=True, timeout=60)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('original render failed: -4', completed.stderr)

    def test_wide_local_sample_coordinates_match_original_world_origin_frames(self):
        # RC2 renders at most 512 local columns, but its authored world origin
        # moves the exact source coordinate past the old sampler's 4096-cell
        # guard. Translate that origin into the direct sample coordinate.
        for pattern in (1, 2, 3, 7, 8, 9, 10):
            with self.subTest(pattern=pattern):
                output = self.render({'width': 512, 'height': 1,
                                      'values': {'2': pattern, '49': 4096}})
                expected = output[511][2]
                material = Material()
                self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(material))
                material.pattern = pattern
                result = ctypes.c_uint32(0xdeadbeef)
                rc = self.lib.nrSourceMaterialSampleColor(ctypes.byref(material), 0,
                                                          4607 * 256, 0,
                                                          ctypes.byref(result))
                self.assertEqual(rc, 0)
                self.assertEqual(result.value, expected)

    def test_sample_coordinates_near_int32_limits_are_overflow_safe(self):
        for pattern in range(12):
            material = Material()
            self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(material))
            material.pattern = pattern
            out = ctypes.c_uint32(0xdeadbeef)
            result = self.lib.nrSourceMaterialSampleColor(ctypes.byref(material), 1234567,
                                                          2_000_000_000, -2_000_000_000,
                                                          ctypes.byref(out))
            self.assertEqual(result, 0)
            self.assertLessEqual(out.value, 0xffffff)

    def test_large_offscreen_components_clip_without_callbacks_and_reject_extent_overflow(self):
        callbacks = []
        def read(_ctx, _x, _y, _out):
            callbacks.append('read')
            return 0
        def cell(*_args): callbacks.append('cell')
        def subcell(*_args): callbacks.append('subcell')
        read_cb, cell_cb, sub_cb = READ(read), CELL(cell), SUBCELL(subcell)
        sink = Sink(None, 24, 12, read_cb, cell_cb, sub_cb)
        material = Material()
        self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(material))

        # Huge but representable source geometry remains unbounded by the old
        # renderer viewport. Offscreen work is clipped before sink callbacks.
        for kind in range(14):
            row = node(kind, x=4096, y=4096, width=1_000_000_000,
                       height=500_000_000)
            component = Component((ctypes.c_int32 * 32)(*row), None, 0,
                                  None, 0, 0, ctypes.pointer(material),
                                  0x11100e, 0)
            self.assertEqual(self.lib.nrSourceStageComponentApply(
                ctypes.byref(component), ctypes.byref(sink)), 0, ('kind', kind))
        self.assertEqual(callbacks, [])

        # Width beyond signed 2x subcell extent is rejected before any output.
        row = node(2, x=0, y=0, width=(2**31 - 1) // 2 + 1, height=1)
        invalid = Component((ctypes.c_int32 * 32)(*row), None, 0,
                            None, 0, 0, ctypes.pointer(material), 0x11100e, 0)
        self.assertEqual(self.lib.nrSourceStageComponentApply(
            ctypes.byref(invalid), ctypes.byref(sink)), -1)
        self.assertEqual(callbacks, [])

    def test_negative_original_node_validation_rejects_invalid_dimensions(self):
        # nsStageRender reports -4 when node validation rejects the record. The
        # harness surfaces that failed render as a nonzero process result.
        bad = node(6, width=513, height=1)
        completed = subprocess.run(
            ['node', str(ROOT / 'tests/original_rc2_surface_sampler_oracle.mjs'), str(self.originalPath)],
            input=json.dumps([{'width': 24, 'height': 12, 'timeMs': 0, 'nodes': [bad]}]),
            capture_output=True, text=True, timeout=60)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('original render failed: -4', completed.stderr)

    def test_negative_native_validation_and_invalid_kind_emit_no_primitives(self):
        calls = []
        def read(_ctx, _x, _y, _out):
            calls.append('read')
            return 0
        def cell(*_args): calls.append('cell')
        def subcell(*_args): calls.append('subcell')
        read_cb, cell_cb, sub_cb = READ(read), CELL(cell), SUBCELL(subcell)
        sink = Sink(None, 24, 12, read_cb, cell_cb, sub_cb)
        mat = Material()
        self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(mat))
        bad = node(6, width=0, height=1)
        invalid = Component((ctypes.c_int32 * 32)(*bad), None, 0, None, 0, 0,
                            ctypes.pointer(mat), 0x11100e, 0)
        self.assertEqual(self.lib.nrSourceStageComponentApply(ctypes.byref(invalid), ctypes.byref(sink)), -1)
        self.assertEqual(calls, [])
        unsupported_row = node(14, width=3, height=1)
        unsupported = Component((ctypes.c_int32 * 32)(*unsupported_row), None, 0, None, 0, 0,
                                ctypes.pointer(mat), 0x11100e, 0)
        self.assertEqual(self.lib.nrSourceStageComponentApply(ctypes.byref(unsupported), ctypes.byref(sink)), -1)
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
