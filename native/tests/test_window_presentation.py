"""Test-first options/geometry tests for the retained RC2 theatre toolbar seam."""
from __future__ import annotations

import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes
import json
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "window_presentation.c"

CHROME = {"mac": 0, "windows": 1, "gnome": 2, "custom": 3}
ACTION = {"close": 0, "minimize": 1, "maximize": 2, "background": 3}
SIDE = {"left": 0, "right": 1}


class Options(ctypes.Structure):
    _fields_ = [
        ("opacity", ctypes.c_double), ("depthFade", ctypes.c_double),
        ("chrome", ctypes.c_int), ("controlWidth", ctypes.c_int),
        ("controlHeight", ctypes.c_int), ("customSide", ctypes.c_int),
        ("customOrder", ctypes.c_int * 4), ("customGlyphs", ctypes.c_uint32 * 4),
    ]


class PresentationState(ctypes.Structure):
    _fields_ = [("enabled", ctypes.c_uint32), ("reserved", ctypes.c_uint32),
                ("options", Options)]


class Rect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int),
                ("width", ctypes.c_int), ("height", ctypes.c_int),
                ("action", ctypes.c_int), ("index", ctypes.c_int)]



class Token(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("start", ctypes.c_int),
                ("end", ctypes.c_int), ("next", ctypes.c_int),
                ("count", ctypes.c_int), ("number", ctypes.c_double)]


class Json(ctypes.Structure):
    _fields_ = [("text", ctypes.c_char_p), ("length", ctypes.c_int),
                ("count", ctypes.c_int), ("pos", ctypes.c_int),
                ("depth", ctypes.c_int), ("tokens", Token * 16384),
                ("error", ctypes.c_char * 128)]


def defaults():
    return Options(.85, .008, CHROME["mac"], 10, 3, SIDE["right"],
                   (ctypes.c_int * 4)(ACTION["minimize"], ACTION["maximize"],
                                      ACTION["background"], ACTION["close"]),
                   (ctypes.c_uint32 * 4)(ord("−"), ord("□"), ord("◇"), ord("×")))


def make_state(enabled=0, options=None):
    return PresentationState(enabled, 0, options if options is not None else Options())


def call_patch(lib, source, prior=None, alpha=.8):
    raw = json.dumps(source, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    storage = ctypes.create_string_buffer(raw)
    parsed = Json()
    if lib.nrParse(ctypes.byref(parsed), ctypes.cast(storage, ctypes.c_char_p), len(raw)) != 1:
        raise AssertionError(f"test JSON failed to parse: {source}")
    current = prior or make_state()
    output = make_state(0xdeadbeef, defaults())
    out_alpha = ctypes.c_double(123.5)
    status = lib.nrWindowPresentationPatch(ctypes.byref(parsed), ctypes.byref(current),
                                           alpha, ctypes.byref(output), ctypes.byref(out_alpha))
    return status, current, output, out_alpha.value, parsed, storage


def option_tuple(options):
    return (options.opacity, options.depthFade, options.chrome, options.controlWidth,
            options.controlHeight, options.customSide, tuple(options.customOrder),
            tuple(options.customGlyphs))


class WindowPresentationIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.exists():
            raise AssertionError("window presentation option/helper module is missing")
        cls.temp = tempfile.TemporaryDirectory(prefix="nr-window-presentation-")
        output = Path(cls.temp.name) / ("window_presentation.dylib" if platform.system() == "Darwin"
                                        else "window_presentation.so")
        cc = os.environ.get("CC", "cc")
        link_flags = (["-dynamiclib", "-Wl,-dead_strip"] if platform.system() == "Darwin"
                      else ["-shared", "-Wl,--gc-sections"])
        command = [cc, "-std=c11", "-O0", "-fPIC", "-ffunction-sections", "-fdata-sections",
                   "-I", str(ROOT / "src"), "-I", str(ROOT / "include"), *link_flags,
                   str(SOURCE), str(ROOT / "src" / "window_source_presentation.c"),
                   str(ROOT / "src" / "json.c"), str(ROOT / "src" / "json_numbers.c"),
                   "-o", str(output)]
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(output))
        cls.lib.nrParse.argtypes = [ctypes.POINTER(Json), ctypes.c_char_p, ctypes.c_int]
        cls.lib.nrParse.restype = ctypes.c_int
        cls.lib.nrWindowPresentationPatch.argtypes = [ctypes.POINTER(Json),
            ctypes.POINTER(PresentationState), ctypes.c_double,
            ctypes.POINTER(PresentationState), ctypes.POINTER(ctypes.c_double)]
        cls.lib.nrWindowPresentationPatch.restype = ctypes.c_int
        cls.lib.nrWindowPresentationControlRects.argtypes = [ctypes.c_int,
            ctypes.POINTER(Options), ctypes.POINTER(Rect)]
        cls.lib.nrWindowPresentationControlRects.restype = ctypes.c_int
        cls.lib.nrWindowPresentationControlHit.argtypes = [ctypes.c_int,
            ctypes.POINTER(Options), ctypes.c_int, ctypes.c_int]
        cls.lib.nrWindowPresentationControlHit.restype = ctypes.c_int
        cls.lib.nrWindowSourcePresentationDefaults.argtypes = [ctypes.POINTER(Options)]
        cls.lib.nrWindowSourcePresentationDefaults.restype = None

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_source_opt_in_defaults_partial_updates_alpha_and_clear(self):
        status, _, enabled, alpha, *_ = call_patch(self.lib, {"op": "window", "id": 5,
                                                              "sourcePresentation": True})
        self.assertEqual(status, 1)
        self.assertEqual(enabled.enabled, 1)
        self.assertEqual(enabled.reserved, 0)
        self.assertEqual(alpha, .85, "first source opt-in without alpha uses RC2 opacity default")
        self.assertEqual(option_tuple(enabled.options), option_tuple(defaults()))

        status, _, implicit, alpha, *_ = call_patch(self.lib, {"op": "window", "id": 5,
                                                              "depthFade": .04})
        self.assertEqual(status, 1, "a source-only option opts in and seeds remaining source defaults")
        self.assertEqual(implicit.enabled, 1)
        self.assertEqual(implicit.options.depthFade, .04)
        self.assertEqual(implicit.options.chrome, CHROME["mac"])
        self.assertEqual(alpha, .85)

        prior_options = defaults()
        prior_options.depthFade = .03
        prior_options.controlWidth = 14
        current = make_state(1, prior_options)
        status, _, partial, alpha, *_ = call_patch(self.lib, {"op": "window", "id": 5,
                                                             "chrome": "gnome"}, current, .85)
        self.assertEqual(status, 1)
        self.assertEqual(partial.enabled, 1)
        self.assertEqual(partial.options.chrome, CHROME["gnome"])
        self.assertEqual(partial.options.depthFade, .03)
        self.assertEqual(partial.options.controlWidth, 14)
        self.assertEqual(partial.options.opacity, .85)
        self.assertEqual(alpha, .85)

        status, _, changed_alpha, alpha, *_ = call_patch(self.lib, {"op": "window", "id": 5,
                                                                   "alpha": .42}, current, .42)
        self.assertEqual(status, 1, "alpha remains the sole opacity authority while enabled")
        self.assertEqual(changed_alpha.options.opacity, .42)
        self.assertEqual(alpha, .42)

        status, _, cleared, alpha, *_ = call_patch(self.lib, {"op": "window", "id": 5,
                                                             "sourcePresentation": False}, current, .42)
        self.assertEqual(status, 1)
        self.assertEqual(bytes(cleared), bytes(PresentationState()))
        self.assertEqual(alpha, .42)

        status, _, untouched, alpha, *_ = call_patch(self.lib, {"op": "window", "id": 5,
                                                                "alpha": .42}, make_state(), .42)
        self.assertEqual(status, 0, "alpha alone must preserve no-opt-in legacy presentation")
        self.assertEqual(untouched.enabled, 0xdeadbeef, "no-op leaves outputs untouched")
        self.assertEqual(alpha, 123.5)

    def test_source_option_rejections_are_atomic(self):
        current_options = defaults()
        current_options.depthFade = .021
        current = make_state(1, current_options)
        for patch in (
            {"sourcePresentation": False, "chrome": "gnome"},
            {"sourcePresentation": "true"}, {"depthFade": -0.001},
            {"depthFade": .0801}, {"chrome": "other"},
            {"controlWidth": 4}, {"controlWidth": 5.5},
            {"controlHeight": 7}, {"controlHeight": 3.5},
            {"customSide": "center"},
            {"customOrder": "close,minimize,maximize,maximize"},
            {"customGlyphs": "a,b,\n,d"}, {"customGlyphs": "a,ab,c,d"},
        ):
            with self.subTest(patch=patch):
                status, prior, output, alpha, *_ = call_patch(
                    self.lib, {"op": "window", "id": 5, **patch}, current, .64)
                self.assertEqual(status, -1)
                self.assertEqual(output.enabled, 0xdeadbeef)
                self.assertEqual(alpha, 123.5)
                self.assertEqual(option_tuple(prior.options), option_tuple(current.options))

    def test_custom_fields_accept_original_csv_profile_and_unicode(self):
        status, _, configured, alpha, *_ = call_patch(self.lib, {
            "op": "window", "id": 5, "customSide": "left",
            "customOrder": "close,minimize,maximize,background",
            "customGlyphs": "×,−,□,◇"})
        self.assertEqual(status, 1)
        self.assertEqual(configured.enabled, 1)
        self.assertEqual(configured.options.customSide, SIDE["left"])
        self.assertEqual(list(configured.options.customOrder),
                         [ACTION[name] for name in ("close", "minimize", "maximize", "background")])
        self.assertEqual(list(configured.options.customGlyphs), list(map(ord, "×−□◇")))
        self.assertEqual(alpha, .85)

    def test_theatre_toolbar_rectangles_and_hits_match_original_javascript(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        anchor = "return {WINDOW_SHAPES,WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,shapeContains,validateWindowOptions,WindowManager,windowVertex};"
        self.assertEqual(html.count(anchor), 1)
        exposed = html.replace(anchor,
            "window.__windowApi={DEFAULT_WINDOW_OPTIONS,validateWindowOptions,WindowManager};" + anchor, 1)
        profiles = ("mac", "windows", "gnome", "custom")
        frames = (24, 45, 100, 144)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True,
                executable_path=os.environ.get("CHROMIUM") or shutil.which("chromium") or
                shutil.which("google-chrome") or shutil.which("chrome"),
                args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__windowApi", timeout=30000)
            for chrome in profiles:
                value = {"chrome": chrome, "controlWidth": 10, "controlHeight": 3}
                source = page.evaluate("""input => {
                  const a=window.__windowApi,m=new a.WindowManager();
                  m.options=a.validateWindowOptions(input);m.add({id:'window-one',title:'Window'});
                  const controls=m.controls('window-one'), total=controls.reduce((n,c)=>n+c.width+1,0);
                  return [24,45,100,144].map(frameWidth=>{
                    const start=controls[0].side==='left'?3:Math.max(3,frameWidth-total-3);
                    const rects=controls.map((c,i)=>({x:start+i*(c.width+1),y:6,
                      width:c.width,height:c.height,action:c.action,index:i}));
                    return {frameWidth,rects};
                  });
                }""", value)
                options = defaults()
                options.chrome = CHROME[chrome]
                rects = (Rect * 4)()
                for row, frame_width in zip(source, frames):
                    self.assertEqual(self.lib.nrWindowPresentationControlRects(
                        frame_width, ctypes.byref(options), rects), 0)
                    actual = [{"x": r.x, "y": r.y, "width": r.width, "height": r.height,
                               "action": next(name for name, n in ACTION.items() if n == r.action),
                               "index": r.index} for r in rects]
                    self.assertEqual(actual, row["rects"])
                    for y in range(4, 6 + options.controlHeight + 1):
                        for x in range(0, frame_width + 10):
                            expected = next((ACTION[r["action"]] for r in row["rects"]
                                if r["x"] <= x < r["x"]+r["width"] and
                                   r["y"] <= y < r["y"]+r["height"]), -1)
                            got = self.lib.nrWindowPresentationControlHit(frame_width,
                                ctypes.byref(options), x, y)
                            self.assertEqual(got, expected, (chrome, frame_width, x, y))
            browser.close()



if __name__ == "__main__":
    unittest.main()
