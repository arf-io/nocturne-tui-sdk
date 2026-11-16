"""Differential source-color tests against the actual rc.2 embedded Wasm."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import contextlib
import ctypes
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from native.tests.historical_reference import RC2_FIXTURE, rc2_workbench_file

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
ORIGINAL_VARIABLE = 'NOCTURNE_RC2_ORIGINAL_DOCS'
ORIGINAL_SHA = '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'
ORIGINAL_WASM_SHA = 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09'
PATTERNS = ['solid', 'linear', 'diagonal', 'wave', 'rotating-linear', 'plasma', 'concentric', 'moire', 'aurora', 'interference', 'chevrons', 'diamond']


def original_reference(environment=None, fixture=RC2_FIXTURE):
    """Context manager yielding the exact rc.2 Nocturne-Workbench-Docs.html path.

    Order: NOCTURNE_RC2_ORIGINAL_DOCS; else the custody-checked portable fixture
    (historical_reference verifies the same 875089-byte SHA-256 as the original
    archive entry); else SkipTest naming the missing reference, a visible gap.
    The tracked root Nocturne-Workbench-Docs.html has different bytes and is
    never substituted. A supplied path that is not a file is an error.
    """
    environment = os.environ if environment is None else environment
    supplied = environment.get(ORIGINAL_VARIABLE)
    if supplied:
        if not Path(supplied).is_file():
            raise AssertionError(f'{ORIGINAL_VARIABLE}={supplied!r} is not a file')
        return contextlib.nullcontext(Path(supplied))
    if Path(fixture).is_file():
        return rc2_workbench_file(fixture)
    raise unittest.SkipTest(
        f'BLOCKED: exact rc.2 reference Nocturne-Workbench-Docs.html (sha256 {ORIGINAL_SHA}) unavailable: '
        f'set {ORIGINAL_VARIABLE} or restore {fixture}; the tracked root Nocturne-Workbench-Docs.html '
        'differs from the original and is not substituted')


class Config(ctypes.Structure):
    _fields_ = [
        ('pattern', ctypes.c_uint32), ('focus_mode', ctypes.c_uint32),
        ('focus_x_q8', ctypes.c_int32), ('focus_y_q8', ctypes.c_int32),
        ('period_ms', ctypes.c_uint32), ('saturation_milli', ctypes.c_int32),
        ('brightness_milli', ctypes.c_int32), ('speed_falloff_milli', ctypes.c_uint32),
        ('saturation_falloff_milli', ctypes.c_uint32), ('brightness_falloff_milli', ctypes.c_uint32),
        ('cell_aspect_milli', ctypes.c_uint32), ('scale_q8', ctypes.c_uint32),
        ('angle_milli_degrees', ctypes.c_int32), ('pivot_x_q8', ctypes.c_int32),
        ('pivot_y_q8', ctypes.c_int32), ('rotation_period_ms', ctypes.c_uint32),
        ('rotation_mode', ctypes.c_uint32), ('swing_milli_degrees', ctypes.c_int32),
        ('phase_1024', ctypes.c_int32), ('seed', ctypes.c_uint32),
        ('base_rgb', ctypes.c_uint32), ('ink_rgb', ctypes.c_uint32),
        ('palette_count', ctypes.c_uint32), ('gradient_wrap', ctypes.c_uint32),
        ('interpolation', ctypes.c_uint32), ('color_mode', ctypes.c_uint32),
        ('hue_offset_degrees', ctypes.c_int32), ('motion', ctypes.c_uint32),
        ('origin_x_cells', ctypes.c_int32), ('origin_y_cells', ctypes.c_int32),
        ('wave_amplitude_milli', ctypes.c_uint32), ('reverse', ctypes.c_uint32),
        ('palette', ctypes.c_uint32 * 32),
    ]


class SourceSampler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_path = cls.enterClassContext(original_reference())
        edition = cls.original_path.read_bytes()
        if hashlib.sha256(edition).hexdigest() != ORIGINAL_SHA:
            raise AssertionError('exact rc.2 reference HTML custody mismatch')
        cls.temp = tempfile.TemporaryDirectory(prefix='source-material-sampler-')
        cls.lib_path = Path(cls.temp.name) / 'libsource_material_sampler.so'
        command = [os.environ.get('CC', 'cc'), '-std=c11', '-O2', '-fPIC', '-shared',
                   '-I', str(ROOT / 'src'), str(ROOT / 'src/source_material_sampler.c'),
                   '-o', str(cls.lib_path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.lib = ctypes.CDLL(str(cls.lib_path))
        cls.lib.nrSourceMaterialSamplerDefaults.argtypes = [ctypes.POINTER(Config)]
        cls.lib.nrSourceMaterialSamplerValidate.argtypes = [ctypes.POINTER(Config)]
        cls.lib.nrSourceMaterialSamplerValidate.restype = ctypes.c_int
        cls.lib.nrSourceMaterialSampleColor.argtypes = [ctypes.POINTER(Config), ctypes.c_uint64,
                                                         ctypes.c_int32, ctypes.c_int32,
                                                         ctypes.POINTER(ctypes.c_uint32)]
        cls.lib.nrSourceMaterialSampleColor.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    def original(self, cases):
        result = subprocess.run(['node', str(ROOT / 'tests/original_rc2_surface_sampler_oracle.mjs'), str(self.original_path)],
                                input=json.dumps(cases), capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return json.loads(result.stdout)

    def apply_original_fields(self, config, values):
        enum_fields = {
            2: ('pattern', PATTERNS),
            3: ('focus_mode', ['none', 'row', 'column', 'radial', 'diagonal-band']),
            18: ('rotation_mode', ['fixed', 'continuous', 'pendulum']),
            26: ('gradient_wrap', ['loop', 'mirror', 'hard-stops']),
            27: ('interpolation', ['linear', 'eased']),
            28: ('color_mode', ['palette', 'hsv', 'rgb-sine']),
        }
        names = {
            4: 'focus_x_q8', 5: 'focus_y_q8', 6: 'period_ms', 7: 'saturation_milli',
            8: 'brightness_milli', 9: 'speed_falloff_milli', 10: 'saturation_falloff_milli',
            11: 'brightness_falloff_milli', 12: 'cell_aspect_milli', 13: 'scale_q8',
            14: 'angle_milli_degrees', 15: 'pivot_x_q8', 16: 'pivot_y_q8',
            17: 'rotation_period_ms', 19: 'swing_milli_degrees', 20: 'phase_1024',
            22: 'seed', 23: 'base_rgb', 24: 'ink_rgb', 29: 'hue_offset_degrees',
            47: 'motion', 49: 'origin_x_cells', 50: 'origin_y_cells',
            51: 'wave_amplitude_milli', 53: 'reverse',
        }
        for index, value in values.items():
            field = getattr(Config, '_fields_')
            if index in enum_fields:
                name, choices = enum_fields[index]
                setattr(config, name, choices.index(value) if isinstance(value, str) else value)
            elif index in names:
                setattr(config, names[index], value)
            elif index in (25,):
                continue
            else:
                raise AssertionError(f'unmapped original sampler field {index}')

    def compare_cases(self, cases):
        requests = []
        for overrides, palette, time_ms, width, height in cases:
            requests.append({'values': {str(k): v for k, v in overrides.items()}, 'palette': palette,
                             'timeMs': time_ms, 'width': width, 'height': height})
        oracle = self.original(requests)
        self.assertEqual(oracle['editionSha256'], ORIGINAL_SHA)
        self.assertEqual(oracle['wasmSha256'], ORIGINAL_WASM_SHA)
        for (overrides, palette, time_ms, width, height), reference in zip(cases, oracle['results']):
            with self.subTest(overrides=overrides, time_ms=time_ms):
                self.compare_reference(overrides, palette, time_ms, width, height, reference)

    def compare_reference(self, overrides, palette, time_ms, width, height, reference):
        config = Config()
        self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(config))
        self.apply_original_fields(config, overrides)
        config.palette_count = len(palette)
        for i, color in enumerate(palette):
            config.palette[i] = color
        self.assertEqual(self.lib.nrSourceMaterialSamplerValidate(ctypes.byref(config)), 1)
        for y in range(height):
            for x in range(width):
                output = ctypes.c_uint32(0xdeadbeef)
                result = self.lib.nrSourceMaterialSampleColor(ctypes.byref(config), time_ms * 1000,
                                                               x * 256, y * 256, ctypes.byref(output))
                self.assertEqual(result, 0)
                expected = reference['rgb'][y * width + x]
                self.assertEqual(output.value, expected, (overrides, time_ms, x, y))

    def test_all_twelve_patterns_match_exact_original_rgb_frames(self):
        palette = [0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565]
        self.compare_cases([({2: index}, palette, 2000, 19, 11)
                            for index, _name in enumerate(PATTERNS)])

    def test_coordinate_time_focus_rotation_and_palette_variants_match(self):
        palettes = [
            [0x102030],
            [0xff0000, 0x00ff00, 0x0000ff],
            [((i * 37) & 255) << 16 | ((i * 73) & 255) << 8 | ((i * 109) & 255) for i in range(32)],
        ]
        cases = []
        for pattern in range(12):
            for focus in range(5):
                for rotation in range(3):
                    overrides = {2: pattern, 3: focus, 18: rotation, 4: -1250,
                                 5: 3030, 6: 3500, 7: 1333, 8: 777, 9: 825,
                                 10: 612, 11: 931, 12: 2750, 13: 4097,
                                 14: 12345, 15: 1930, 16: -2410, 17: 7400,
                                 19: 122000, 20: -173, 29: -137,
                                 47: int((pattern + focus + rotation) % 2 == 0),
                                 49: -17, 50: 23, 51: 1555,
                                 53: int((pattern + rotation) % 2 == 1)}
                    cases.append((overrides, palettes[(pattern + focus + rotation) % len(palettes)],
                                  12789 + pattern * 19 + focus * 23 + rotation * 29, 19, 11))
        self.compare_cases(cases)

    def test_palette_interpolation_wrap_and_color_modes_match(self):
        palettes = [0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565]
        cases = []
        for color_mode in range(3):
            for wrap in range(3):
                for interpolation in range(2):
                    cases.append(({2: 5, 14: 27400, 26: wrap, 27: interpolation,
                                   28: color_mode, 29: -97}, palettes, 24317, 19, 11))
        self.compare_cases(cases)

    def test_original_defaults_and_invalid_controls_preserve_outputs(self):
        config = Config()
        self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(config))
        oracle = self.original([])
        self.assertEqual(oracle['editionSha256'], ORIGINAL_SHA)
        self.assertEqual(oracle['wasmSha256'], ORIGINAL_WASM_SHA)
        original_fields = oracle['sourceDefaults']
        mapping = {
            'pattern': 2, 'focus_mode': 3, 'focus_x_q8': 4, 'focus_y_q8': 5,
            'period_ms': 6, 'saturation_milli': 7, 'brightness_milli': 8,
            'speed_falloff_milli': 9, 'saturation_falloff_milli': 10,
            'brightness_falloff_milli': 11, 'cell_aspect_milli': 12,
            'scale_q8': 13, 'angle_milli_degrees': 14, 'pivot_x_q8': 15,
            'pivot_y_q8': 16, 'rotation_period_ms': 17, 'rotation_mode': 18,
            'swing_milli_degrees': 19, 'phase_1024': 20, 'seed': 22,
            'base_rgb': 23, 'ink_rgb': 24, 'palette_count': 25,
            'gradient_wrap': 26, 'interpolation': 27, 'color_mode': 28,
            'hue_offset_degrees': 29, 'motion': 47, 'origin_x_cells': 49,
            'origin_y_cells': 50, 'wave_amplitude_milli': 51, 'reverse': 53,
        }
        for native_name, source_index in mapping.items():
            with self.subTest(default=native_name):
                self.assertEqual(getattr(config, native_name), original_fields[source_index])
        self.assertEqual(list(config.palette), oracle['sourcePalette'])
        invalid = [
            ('pattern', 12), ('focus_mode', 5), ('period_ms', 49), ('period_ms', 3600001),
            ('saturation_milli', 2001), ('brightness_milli', -1), ('speed_falloff_milli', 9),
            ('cell_aspect_milli', 499), ('scale_q8', 63), ('rotation_mode', 3),
            ('gradient_wrap', 3), ('interpolation', 2), ('color_mode', 3),
            ('hue_offset_degrees', 3601), ('origin_x_cells', 4097),
            ('origin_y_cells', -4097), ('motion', 2), ('reverse', 2),
            ('wave_amplitude_milli', 4001), ('base_rgb', 0x1000000),
            ('palette_count', 0), ('palette_count', 33),
        ]
        for name, value in invalid:
            with self.subTest(name=name, value=value):
                candidate = Config.from_buffer_copy(config)
                setattr(candidate, name, value)
                self.assertEqual(self.lib.nrSourceMaterialSamplerValidate(ctypes.byref(candidate)), 0)
                output = ctypes.c_uint32(0x12345678)
                self.assertNotEqual(self.lib.nrSourceMaterialSampleColor(ctypes.byref(candidate), 0, 0, 0,
                                                                          ctypes.byref(output)), 0)
                self.assertEqual(output.value, 0x12345678)

    def test_microsecond_clock_floors_to_original_milliseconds_and_accepts_wide_coordinates(self):
        config = Config()
        self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(config))
        first = ctypes.c_uint32()
        second = ctypes.c_uint32()
        self.assertEqual(self.lib.nrSourceMaterialSampleColor(ctypes.byref(config), 2000000, 9 * 256,
                                                               4 * 256, ctypes.byref(first)), 0)
        self.assertEqual(self.lib.nrSourceMaterialSampleColor(ctypes.byref(config), 2000999, 9 * 256,
                                                               4 * 256, ctypes.byref(second)), 0)
        self.assertEqual(first.value, second.value)
        output = ctypes.c_uint32(0xaabbccdd)
        self.assertEqual(self.lib.nrSourceMaterialSampleColor(ctypes.byref(config), 0, 1048577, 0,
                                                               ctypes.byref(output)), 0)
        self.assertNotEqual(output.value, 0xaabbccdd)

    def test_motion_matches_original_change_and_static_lock(self):
        width, height = 19, 11
        palette = [0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565]
        for overrides, should_move in [({}, True), ({47: 0}, False)]:
            requests = [{'values': overrides, 'palette': palette, 'timeMs': time,
                         'width': width, 'height': height} for time in (0, 1250)]
            oracle = self.original(requests)
            self.assertEqual(oracle['editionSha256'], ORIGINAL_SHA)
            self.assertEqual(oracle['wasmSha256'], ORIGINAL_WASM_SHA)
            original_frames = [item['rgb'] for item in oracle['results']]
            original_changed = original_frames[0] != original_frames[1]
            self.assertEqual(original_changed, should_move)

            config = Config()
            self.lib.nrSourceMaterialSamplerDefaults(ctypes.byref(config))
            self.apply_original_fields(config, overrides)
            config.palette_count = len(palette)
            for i, color in enumerate(palette):
                config.palette[i] = color
            candidate_frames = []
            for time in (0, 1250):
                frame = []
                for y in range(height):
                    for x in range(width):
                        color = ctypes.c_uint32()
                        self.assertEqual(self.lib.nrSourceMaterialSampleColor(ctypes.byref(config), time * 1000,
                                                                               x * 256, y * 256,
                                                                               ctypes.byref(color)), 0)
                        frame.append(color.value)
                candidate_frames.append(frame)
            self.assertEqual(candidate_frames, original_frames)


if __name__ == '__main__':
    unittest.main()
