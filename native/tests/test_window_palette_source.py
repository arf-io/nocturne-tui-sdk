"""Exact RC2 palette preparation across Chromium, current C, and standalone Wasm."""
from __future__ import annotations

import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "window_palette_source.c"
HEADER = ROOT / "src" / "window_palette_source.h"
PROBE = ROOT / "tests" / "window_palette_source_probe.c"
WASM_RUNNER = ROOT / "tests" / "window_palette_source_wasm_runner.mjs"
HTML_SHA = "375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385"
WASM_SHA = "aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09"
DEFAULT_COLORS = (0x647795, 0xAF88BB, 0x69A9A5, 0xB89477, 0x73709F)
DEFAULT_BACKGROUND = 0x101319
DEFAULT_INK = 0xDFD8CC
RAMP_SIZE = 2048
WHEEL_SIZE = 360


def run_with_diagnostics(command, **kwargs):
    """Run a probe/build command and surface captured compiler diagnostics."""
    kwargs.pop("check", None)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    result = subprocess.run(command, check=False, **kwargs)
    if result.returncode:
        rendered = " ".join(str(part) for part in command)
        raise AssertionError(
            f"command exited {result.returncode}: {rendered}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


class Config(ctypes.Structure):
    _fields_ = [
        ("colorCount", ctypes.c_uint32), ("weightCount", ctypes.c_uint32),
        ("colors", ctypes.c_uint32 * 32),
        ("backgroundRgb", ctypes.c_uint32), ("inkRgb", ctypes.c_uint32),
        ("lockLightness", ctypes.c_uint32), ("reserved", ctypes.c_uint32),
        ("weights", ctypes.c_double * 32),
        ("lightness", ctypes.c_double), ("chroma", ctypes.c_double),
        ("brightness", ctypes.c_double), ("hueOffsetDegrees", ctypes.c_double),
        ("feather", ctypes.c_double), ("textLightness", ctypes.c_double),
        ("textChroma", ctypes.c_double),
    ]


class Prepared(ctypes.Structure):
    _fields_ = [("ramp", ctypes.c_uint32 * RAMP_SIZE),
                ("wheel", ctypes.c_uint32 * WHEEL_SIZE),
                ("stopTotal", ctypes.c_double)]


def make_config(colors=DEFAULT_COLORS, background=DEFAULT_BACKGROUND, ink=DEFAULT_INK,
                weights=(), **options):
    values = dict(lightness=.62, chroma=.14, brightness=.28, hueOffsetDegrees=0,
                  lockLightness=1, feather=1, textLightness=.83, textChroma=.10)
    values.update(options)
    config = Config()
    config.colorCount = len(colors)
    config.weightCount = len(weights)
    for index, color in enumerate(colors):
        config.colors[index] = color
    config.backgroundRgb = background
    config.inkRgb = ink
    config.lockLightness = values.pop("lockLightness")
    for index, weight in enumerate(weights):
        config.weights[index] = weight
    for key, value in values.items():
        setattr(config, key, value)
    return config


def clone_config(config):
    result = Config()
    ctypes.memmove(ctypes.byref(result), ctypes.byref(config), ctypes.sizeof(Config))
    return result


def config_bytes(config):
    return list(ctypes.string_at(ctypes.byref(config), ctypes.sizeof(Config)))


def hex_rgb(value):
    return f"#{value:06x}"


class WindowPaletteSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from native.tests.historical_reference import RC2_WASM_SHA256, load_rc2_workbench

        if not SOURCE.is_file() or not HEADER.is_file():
            raise AssertionError("production window palette source module is missing")
        html = load_rc2_workbench()
        if hashlib.sha256(html.encode("utf-8")).hexdigest() != HTML_SHA:
            raise AssertionError("pinned RC2 HTML custody mismatch")
        if RC2_WASM_SHA256 != WASM_SHA:
            raise AssertionError("pinned RC2 embedded Wasm custody mismatch")
        cls.temp = tempfile.TemporaryDirectory(prefix="nr-window-palette-source-")
        out = Path(cls.temp.name)
        cc = os.environ.get("CC", "cc")
        library = out / ("window_palette_source" + (".dylib" if platform.system() == "Darwin" else ".so"))
        link_flag = "-dynamiclib" if platform.system() == "Darwin" else "-shared"
        run_with_diagnostics([cc, "-std=c11", "-O2", "-ffp-contract=off", "-fno-fast-math",
            "-fno-strict-aliasing", "-fPIC", "-Wall", "-Wextra",
            "-Wno-misleading-indentation", "-Werror", "-I", str(ROOT / "src"),
            "-I", str(ROOT / "include"), link_flag,
            str(SOURCE), str(ROOT / "src" / "math.c"),
            str(PROBE), "-o", str(library)], cwd=ROOT)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.nrWindowPaletteSourceDefaults.argtypes = [ctypes.POINTER(Config)]
        cls.lib.nrWindowPaletteSourceValidate.argtypes = [ctypes.POINTER(Config)]
        cls.lib.nrWindowPaletteSourceValidate.restype = ctypes.c_int
        cls.lib.nrWindowPaletteSourcePrepare.argtypes = [ctypes.POINTER(Config), ctypes.POINTER(Prepared)]
        cls.lib.nrWindowPaletteSourcePrepare.restype = ctypes.c_int
        cls.lib.nrWindowPaletteSourceColorAt.argtypes = [ctypes.POINTER(Prepared), ctypes.c_double,
                                                          ctypes.POINTER(ctypes.c_uint32)]
        cls.lib.nrWindowPaletteSourceColorAt.restype = ctypes.c_int
        cls.lib.nrWindowPaletteSourceInk.argtypes = [ctypes.POINTER(Prepared), ctypes.c_double,
                                                      ctypes.POINTER(ctypes.c_uint32)]
        cls.lib.nrWindowPaletteSourceInk.restype = ctypes.c_int
        cls.lib.nrWindowPaletteSourceProbeLayout.argtypes = [ctypes.POINTER(ctypes.c_uint32)]

        cls.wasm_file = out / "window_palette_source.wasm"
        clang, wasm_ld, node = shutil.which("clang"), shutil.which("wasm-ld"), shutil.which("node")
        if not clang or not wasm_ld or not node:
            raise AssertionError("clang, wasm-ld, and Node are required for the Wasm oracle")
        cls.node = node
        object_paths = []
        for name, source in (("palette", SOURCE), ("math", ROOT / "src" / "math.c"),
                             ("probe", PROBE), ("wasm_mem", ROOT / "src" / "wasm_mem.c")):
            obj = out / f"{name}.o"
            run_with_diagnostics([clang, "--target=wasm32", "-std=c11", "-O2", "-ffp-contract=off",
                "-fno-fast-math", "-fno-strict-aliasing", "-ffunction-sections", "-fdata-sections",
                "-Wall", "-Wextra", "-Wno-misleading-indentation", "-Werror",
                "-Iinclude", "-Isrc", "-Ifreestanding",
                "-nostdlib", "-ffreestanding", "-fno-builtin", "-c", str(source), "-o", str(obj)],
                cwd=ROOT)
            object_paths.append(str(obj))
        run_with_diagnostics([wasm_ld, "--no-entry", "--export-memory", "--gc-sections",
            "--export=nrWindowPaletteSourceProbeLayout",
            "--export=nrWindowPaletteSourceValidate", "--export=nrWindowPaletteSourcePrepare",
            "--export=nrWindowPaletteSourceColorAt", "--export=nrWindowPaletteSourceInk",
            "--stack-first", "-z", "stack-size=1048576", "--initial-memory=16777216",
            *object_paths, "-o", str(cls.wasm_file)], cwd=ROOT)

        from playwright.sync_api import sync_playwright

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        cls.page = cls.browser.new_page()
        cls.page.set_content(html, wait_until="domcontentloaded", timeout=30000)
        cls.page.wait_for_function("window.fieldGuide && window.fieldGuide.engine", timeout=30000)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "browser"):
            cls.browser.close()
            cls.playwright.stop()
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def original(self, config, phases=(), hues=()):
        payload = {
            "colors": [hex_rgb(config.colors[i]) for i in range(config.colorCount)],
            "background": hex_rgb(config.backgroundRgb), "ink": hex_rgb(config.inkRgb),
            "options": {
                "lightness": config.lightness, "chroma": config.chroma,
                "brightness": config.brightness, "hueOffset": config.hueOffsetDegrees,
                "lockLightness": bool(config.lockLightness), "feather": config.feather,
                "textLightness": config.textLightness, "textChroma": config.textChroma,
                "stopWidths": [config.weights[i] for i in range(config.weightCount)],
            },
            "phases": list(phases), "hues": list(hues),
        }
        return self.page.evaluate("""input => {
          const renderer = new ObservatoryRenderer(fieldGuide.engine);
          const palette = {colors:input.colors, background:input.background, ink:input.ink};
          const options = validateOptions(input.options);
          renderer.prepare(palette, options);
          return {ramp:Array.from(renderer.ramp), wheel:Array.from(renderer.wheel),
            stopTotal:renderer.stopTotal,
            colorsAt:input.phases.map(phase=>({status:0,rgb:renderer.colorAt(phase)})),
            inks:input.hues.map(hue=>({status:0,rgb:renderer.ink(hue)}))};
        }""", payload)

    def native(self, config, phases, hues):
        prepared = Prepared()
        if self.lib.nrWindowPaletteSourcePrepare(ctypes.byref(config), ctypes.byref(prepared)) != 0:
            raise AssertionError("native module rejected a valid palette")
        colors_at, inks = [], []
        for phase in phases:
            color = ctypes.c_uint32(0xDEADBEEF)
            status = self.lib.nrWindowPaletteSourceColorAt(ctypes.byref(prepared), phase,
                                                            ctypes.byref(color))
            colors_at.append({"status": status, "rgb": color.value})
        for hue in hues:
            color = ctypes.c_uint32(0xDEADBEEF)
            status = self.lib.nrWindowPaletteSourceInk(ctypes.byref(prepared), hue,
                                                        ctypes.byref(color))
            inks.append({"status": status, "rgb": color.value})
        return {"ramp": list(prepared.ramp), "wheel": list(prepared.wheel),
                "stopTotal": prepared.stopTotal, "colorsAt": colors_at, "inks": inks}

    def wasm(self, configs, phases, hues):
        cases = [{"configBytes": config_bytes(config), "phases": list(phases), "hues": list(hues)}
                 for config in configs]
        case_path = Path(self.temp.name) / "window-palette-cases.json"
        case_path.write_text(json.dumps(cases, allow_nan=False))
        result = run_with_diagnostics([self.node, str(WASM_RUNNER), str(self.wasm_file), str(case_path)],
            cwd=ROOT, timeout=120)
        return json.loads(result.stdout)

    def assert_matches_original(self, config, phases, hues, wasm_result):
        expected = self.original(config, phases, hues)
        actual = self.native(config, phases, hues)
        self.assert_palette_equal(actual, expected, "native")
        self.assertEqual(wasm_result["valid"], 1)
        self.assertEqual(wasm_result["status"], 0)
        self.assert_palette_equal({key: wasm_result[key] for key in expected}, expected, "Wasm")

    def assert_palette_equal(self, actual, expected, engine):
        for key in ("ramp", "wheel"):
            self.assert_word_array_equal(actual[key], expected[key], f"{engine} {key}")
        for key in ("stopTotal", "colorsAt", "inks"):
            self.assertEqual(actual[key], expected[key], f"{engine} {key}")

    def assert_word_array_equal(self, actual, expected, label):
        if actual == expected:
            return
        if len(actual) != len(expected):
            self.fail(f"{label} length {len(actual)} != expected {len(expected)}")
        count = 0
        first = []
        for index, (got, want) in enumerate(zip(actual, expected)):
            if got != want:
                count += 1
                if len(first) < 8:
                    first.append((index, got, want))
        self.fail(f"{label} differs at {count} indices; first (index, actual, expected): {first}")

    def test_defaults_match_original_chromium_full_arrays(self):
        config = Config()
        self.lib.nrWindowPaletteSourceDefaults(ctypes.byref(config))
        layout = (ctypes.c_uint32 * 19)()
        self.lib.nrWindowPaletteSourceProbeLayout(layout)
        expected_layout = [ctypes.sizeof(Config)] + [
            getattr(Config, field).offset for field in (
                "colorCount", "weightCount", "colors", "backgroundRgb", "inkRgb",
                "lockLightness", "reserved", "weights", "lightness", "chroma",
                "brightness", "hueOffsetDegrees", "feather", "textLightness", "textChroma")]
        expected_layout += [ctypes.sizeof(Prepared), Prepared.wheel.offset, Prepared.stopTotal.offset]
        self.assertEqual(list(layout), expected_layout)
        self.assertEqual(tuple(config.colors[:config.colorCount]), DEFAULT_COLORS)
        self.assertEqual((config.backgroundRgb, config.inkRgb), (DEFAULT_BACKGROUND, DEFAULT_INK))
        self.assertEqual((config.lightness, config.chroma, config.brightness,
                          config.hueOffsetDegrees, config.lockLightness, config.feather,
                          config.textLightness, config.textChroma),
                         (.62, .14, .28, 0, 1, 1, .83, .10))
        phases = (0, .25, 1.75, -0.125, 4.999, 5, 10.25)
        hues = (0, 1, 359, 360, -1, 180.5, -360.5)
        wasm = self.wasm([config], phases, hues)
        self.assertEqual(wasm["layout"], expected_layout)
        self.assert_matches_original(config, phases, hues, wasm["results"][0])
        self.assertEqual(wasm["imports"], [])

    def test_weighted_palette_endpoints_and_achromatic_stops_match(self):
        configs = [
            make_config(colors=(0x000000, 0x777777, 0xFFFFFF),
                background=0x123456, ink=0xFEDCBA, weights=(.05, 16, .5, 4),
                lightness=.05, chroma=.4, brightness=1, hueOffsetDegrees=-360,
                lockLightness=0, feather=0, textLightness=.35, textChroma=0),
            make_config(colors=(0xFF0000, 0x00FF00, 0x0000FF, 0x808080),
                background=0x010203, weights=(2.5,), brightness=0,
                hueOffsetDegrees=360, feather=.37, textLightness=.95, textChroma=.3),
            make_config(colors=(0xABCDEF,), background=0x112233, ink=0xFFEEDD,
                weights=(16,), lightness=.95, chroma=0, brightness=.73,
                hueOffsetDegrees=127.5, lockLightness=0, feather=1),
            make_config(colors=tuple(i * 0x010101 for i in range(32)),
                background=0, ink=0xFFFFFF, weights=tuple(.05 if i % 2 == 0 else 16 for i in range(32)),
                brightness=0, hueOffsetDegrees=360, feather=1),
        ]
        phases = (0, .0001, .125, 1.5, 3.999, 7.75, -2.25, 101.125)
        hues = (-721.5, -360, -1.5, 0, 12.5, 179.5, 359, 360.5, 721)
        wasm = self.wasm(configs, phases, hues)
        for config, result in zip(configs, wasm["results"]):
            with self.subTest(colors=tuple(config.colors[:config.colorCount]),
                              weights=tuple(config.weights[:config.weightCount])):
                self.assert_matches_original(config, phases, hues, result)

    def test_invalid_config_and_lookup_failures_are_atomic(self):
        valid = make_config()
        invalid = []
        for field, values in (
            ("colorCount", (0, 33)), ("weightCount", (33,)),
            ("backgroundRgb", (0x1000000,)), ("inkRgb", (0x1000000,)),
            ("lockLightness", (2,)), ("reserved", (1,)),
            ("lightness", (.049, .951)), ("chroma", (-.001, .401)),
            ("brightness", (-.001, 1.001)),
            ("hueOffsetDegrees", (-360.001, 360.001)), ("feather", (-.001, 1.001)),
            ("textLightness", (.349, .951)), ("textChroma", (-.001, .301)),
        ):
            for value in values:
                candidate = clone_config(valid)
                setattr(candidate, field, value)
                invalid.append(candidate)
        for value in (.049, 16.001, float("nan"), float("inf")):
            candidate = clone_config(valid)
            candidate.weightCount = 1
            candidate.weights[0] = value
            invalid.append(candidate)
        candidate = clone_config(valid)
        candidate.colors[0] = 0x1000000
        invalid.append(candidate)

        wasm = self.wasm(invalid, (), ())
        self.assertEqual(wasm["imports"], [])
        for index, candidate in enumerate(invalid):
            with self.subTest(index=index):
                self.assertEqual(self.lib.nrWindowPaletteSourceValidate(ctypes.byref(candidate)), 0)
                before = bytes([0xA5]) * ctypes.sizeof(Prepared)
                output = Prepared.from_buffer_copy(before)
                self.assertEqual(self.lib.nrWindowPaletteSourcePrepare(ctypes.byref(candidate),
                                                                       ctypes.byref(output)), -1)
                self.assertEqual(ctypes.string_at(ctypes.byref(output), ctypes.sizeof(output)), before)
                self.assertEqual(wasm["results"][index]["valid"], 0)
                self.assertEqual(wasm["results"][index]["status"], -1)
                self.assertEqual(wasm["results"][index]["preparedBytes"], list(before))

        prepared = Prepared()
        self.assertEqual(self.lib.nrWindowPaletteSourcePrepare(ctypes.byref(valid),
                                                                ctypes.byref(prepared)), 0)
        for bad in (float("nan"), float("inf"), -float("inf"), 1e300):
            out = ctypes.c_uint32(0xDEADBEEF)
            self.assertEqual(self.lib.nrWindowPaletteSourceColorAt(ctypes.byref(prepared), bad,
                                                                     ctypes.byref(out)), -1)
            self.assertEqual(out.value, 0xDEADBEEF)
            self.assertEqual(self.lib.nrWindowPaletteSourceInk(ctypes.byref(prepared), bad,
                                                                ctypes.byref(out)), -1)
            self.assertEqual(out.value, 0xDEADBEEF)

        lookup = self.wasm([valid], ("__nan__", "__inf__", "__-inf__", 1e300),
                            ("__nan__", "__inf__", "__-inf__", 1e300))["results"][0]
        self.assertEqual(lookup["status"], 0)
        self.assertTrue(all(value == {"status": -1, "rgb": 0xDEADBEEF}
                            for value in lookup["colorsAt"]))
        self.assertTrue(all(value == {"status": -1, "rgb": 0xDEADBEEF}
                            for value in lookup["inks"]))


if __name__ == "__main__":
    unittest.main()
