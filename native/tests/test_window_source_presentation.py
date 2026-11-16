"""Real RC2 Chromium differential tests for the production C window presentation port."""
from __future__ import annotations

import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes
import os
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "window_source_presentation.c"
HEADER = ROOT / "src" / "window_source_presentation.h"

CHROME = {"mac": 0, "windows": 1, "gnome": 2, "custom": 3}
SIDE = {"left": 0, "right": 1}
ACTION = {"close": 0, "minimize": 1, "maximize": 2, "background": 3}


class Options(ctypes.Structure):
    _fields_ = [
        ("opacity", ctypes.c_double), ("depthFade", ctypes.c_double),
        ("chrome", ctypes.c_int), ("controlWidth", ctypes.c_int),
        ("controlHeight", ctypes.c_int), ("customSide", ctypes.c_int),
        ("customOrder", ctypes.c_int * 4),
        ("customGlyphs", ctypes.c_uint32 * 4),
    ]


class Control(ctypes.Structure):
    _fields_ = [
        ("action", ctypes.c_int), ("glyph", ctypes.c_uint32),
        ("color", ctypes.c_uint32), ("index", ctypes.c_int),
        ("side", ctypes.c_int), ("width", ctypes.c_int),
        ("height", ctypes.c_int), ("label", ctypes.c_char * 6),
    ]


def source_options(**patch):
    value = dict(opacity=.85, depthFade=.008, chrome="mac", controlWidth=10,
                 controlHeight=3, customSide="right",
                 customOrder=("minimize", "maximize", "background", "close"),
                 customGlyphs=("−", "□", "◇", "×"))
    value.update(patch)
    return value


def c_options(value):
    custom_order = value["customOrder"]
    glyphs = value["customGlyphs"]
    return Options(value["opacity"], value["depthFade"], CHROME.get(value["chrome"], -1),
                   value["controlWidth"], value["controlHeight"],
                   SIDE.get(value["customSide"], -1),
                   (ctypes.c_int * 4)(*(ACTION[a] for a in custom_order)),
                   (ctypes.c_uint32 * 4)(*(g if isinstance(g, int) else ord(g) for g in glyphs)))


def c_controls(lib, options):
    values = (Control * 4)()
    result = lib.nrWindowSourcePresentationControls(ctypes.byref(options), values)
    if result != 0:
        raise AssertionError("C source presentation rejected a valid options value")
    return [{"action": next(name for name, n in ACTION.items() if n == item.action),
             "glyph": item.glyph, "color": item.color, "index": item.index,
             "side": "left" if item.side == SIDE["left"] else "right",
             "width": item.width, "height": item.height,
             "label": bytes(item.label).split(bytes([0]), 1)[0].decode("ascii")}
            for item in values]


def c_opacity(lib, options, world_z):
    result = ctypes.c_double(-999)
    status = lib.nrWindowSourcePresentationOpacity(
        ctypes.byref(options), world_z, ctypes.byref(result))
    if status != 0:
        raise AssertionError("C source presentation rejected a valid opacity sample")
    return result.value


class WindowSourcePresentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.exists() or not HEADER.exists():
            raise AssertionError("production window source presentation module is missing")
        cls.temp = tempfile.TemporaryDirectory(prefix="nr-window-source-presentation-")
        suffix = ".dylib" if platform.system() == "Darwin" else ".so"
        shared = Path(cls.temp.name) / ("window_source_presentation" + suffix)
        cc = os.environ.get("CC", "cc")
        args = [cc, "-std=c11", "-O0", "-fPIC", "-I", str(ROOT / "src"),
                "-dynamiclib" if platform.system() == "Darwin" else "-shared",
                str(SOURCE), "-o", str(shared)]
        subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(shared))
        cls.lib.nrWindowSourcePresentationDefaults.argtypes = [ctypes.POINTER(Options)]
        cls.lib.nrWindowSourcePresentationDefaults.restype = None
        cls.lib.nrWindowSourcePresentationValid.argtypes = [ctypes.POINTER(Options)]
        cls.lib.nrWindowSourcePresentationValid.restype = ctypes.c_int
        cls.lib.nrWindowSourcePresentationOpacity.argtypes = [ctypes.POINTER(Options), ctypes.c_double,
                                                                ctypes.POINTER(ctypes.c_double)]
        cls.lib.nrWindowSourcePresentationOpacity.restype = ctypes.c_int
        cls.lib.nrWindowSourcePresentationControls.argtypes = [ctypes.POINTER(Options), ctypes.POINTER(Control)]
        cls.lib.nrWindowSourcePresentationControls.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_original_defaults_domains_and_invalid_options(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        anchor = "return {WINDOW_SHAPES,WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,shapeContains,validateWindowOptions,WindowManager,windowVertex};"
        self.assertEqual(html.count(anchor), 1)
        exposed = html.replace(anchor,
            "window.__windowApi={DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,validateWindowOptions};" + anchor, 1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__windowApi", timeout=30000)
            source = page.evaluate("""() => {
              const a=window.__windowApi, bad=[
                {opacity:-.001},{opacity:1.001},{depthFade:-.001},{depthFade:.0801},
                {controlWidth:4},{controlWidth:16},{controlWidth:5.5},
                {controlHeight:2},{controlHeight:7},{controlHeight:3.5},
                {chrome:'x'},{customSide:'center'},
                {customOrder:'close,minimize,maximize,maximize'},
                {customOrder:'close,minimize,maximize'},
                {customGlyphs:'a,b,c'}, {customGlyphs:'a,b,\\n,d'},
                {customGlyphs:'a,ab,c,d'}, {unknown:1}
              ];
              return {defaults:a.DEFAULT_WINDOW_OPTIONS,controls:a.WINDOW_CONTROLS,
                endpointsOk:(()=>{try{a.validateWindowOptions({opacity:0,depthFade:.08,controlWidth:15,controlHeight:6});return true}catch(_){return false}})(),
                rejected:bad.map(x=>{try{a.validateWindowOptions(x);return false}catch(_){return true}})};
            }""")
            native_defaults = Options()
            self.lib.nrWindowSourcePresentationDefaults(ctypes.byref(native_defaults))
            self.assertEqual((native_defaults.opacity, native_defaults.depthFade,
                              native_defaults.chrome, native_defaults.controlWidth,
                              native_defaults.controlHeight, native_defaults.customSide),
                             (.85, .008, CHROME["mac"], 10, 3, SIDE["right"]),
                             msg="C defaults must equal source DEFAULT_WINDOW_OPTIONS")
            self.assertEqual(list(native_defaults.customOrder),
                             [ACTION[a] for a in ("minimize", "maximize", "background", "close")])
            self.assertEqual(list(native_defaults.customGlyphs), list(map(ord, ("−", "□", "◇", "×"))))
            self.assertEqual(source["defaults"]["depthFade"], .008)
            self.assertEqual(source["controls"]["depthFade"], [0, .08, .001, "per world unit"])
            self.assertTrue(source["endpointsOk"])
            self.assertEqual(source["rejected"], [True] * 18)

            self.assertEqual(self.lib.nrWindowSourcePresentationValid(ctypes.byref(native_defaults)), 1)
            for patch in (
                {"opacity": -.001}, {"opacity": 1.001}, {"depthFade": -.001},
                {"depthFade": .0801}, {"controlWidth": 4}, {"controlWidth": 16},
                {"controlHeight": 2}, {"controlHeight": 7},
                {"chrome": "x"}, {"customSide": "center"},
                {"customOrder": ("close", "minimize", "maximize", "maximize")},
                {"customGlyphs": (ord("a"), ord("b"), 0xD800, ord("d"))},
            ):
                options = c_options(source_options(**patch))
                with self.subTest(patch=patch):
                    self.assertEqual(self.lib.nrWindowSourcePresentationValid(ctypes.byref(options)), 0)
                    sentinel = (Control * 4)(*(Control(77, 88, 99, 11, 1, 12, 13, b"keep")
                                                 for _ in range(4)))
                    before = [tuple(getattr(row, name) for name, _ in Control._fields_)
                              for row in sentinel]
                    self.assertEqual(self.lib.nrWindowSourcePresentationControls(
                        ctypes.byref(options), sentinel), -1)
                    self.assertEqual([tuple(getattr(row, name) for name, _ in Control._fields_)
                                      for row in sentinel], before)
                    opacity = ctypes.c_double(123.5)
                    self.assertEqual(self.lib.nrWindowSourcePresentationOpacity(
                        ctypes.byref(options), 10, ctypes.byref(opacity)), -1)
                    self.assertEqual(opacity.value, 123.5)
            browser.close()

    def test_original_depth_fade_matches_c_for_world_z_and_floor(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        anchor = "return {WINDOW_SHAPES,WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,shapeContains,validateWindowOptions,WindowManager,windowVertex};"
        exposed = html.replace(anchor,
            "window.__windowApi={DEFAULT_WINDOW_OPTIONS,validateWindowOptions,WindowManager};" + anchor, 1)
        cases = [source_options(), source_options(opacity=.31, depthFade=.08)]
        zs = (-1000, -2, 0, .001, 1, 10, 25, 100, 1000)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__windowApi", timeout=30000)
            for config in cases:
                opts = dict(config)
                opts["chrome"] = "mac"
                del opts["customOrder"]
                del opts["customGlyphs"]
                actual = page.evaluate("""opts => {
                  const a=window.__windowApi,m=new a.WindowManager();
                  m.options=a.validateWindowOptions(opts);
                  const out=[];
                  for(const z of [-1000,-2,0,.001,1,10,25,100,1000]){
                    const id='z'+String(z).replace('.','_');m.add({id,z,title:'W'});
                    out.push(m.pose(id,0).opacity);
                  }
                  return out;
                }""", opts)
                c = c_options(config)
                self.assertEqual(self.lib.nrWindowSourcePresentationValid(ctypes.byref(c)), 1)
                observed = [c_opacity(self.lib, c, z) for z in zs]
                for z, source_value, native_value in zip(zs, actual, observed):
                    with self.subTest(options=config, z=z):
                        self.assertAlmostEqual(native_value, source_value, places=14)
                self.assertEqual(observed[0], config["opacity"])
                self.assertEqual(observed[1], config["opacity"])
                self.assertGreaterEqual(observed[-1], config["opacity"] * .2)
                self.assertAlmostEqual(observed[-1], config["opacity"] * .2, places=14)
            browser.close()

    def test_original_chrome_profiles_and_custom_unicode_controls_match_c(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        anchor = "return {WINDOW_SHAPES,WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,shapeContains,validateWindowOptions,WindowManager,windowVertex};"
        exposed = html.replace(anchor,
            "window.__windowApi={DEFAULT_WINDOW_OPTIONS,validateWindowOptions,WindowManager};" + anchor, 1)
        configs = [source_options(chrome=name) for name in ("mac", "windows", "gnome", "custom")]
        configs.append(source_options(chrome="custom", customSide="left", controlWidth=15,
            controlHeight=6, customOrder=("background", "close", "minimize", "maximize"),
            customGlyphs=("🜁", "↘", "◇", "×")))
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__windowApi", timeout=30000)
            for config in configs:
                js_options = {k: v for k, v in config.items()}
                js_options["customOrder"] = ",".join(js_options["customOrder"])
                js_options["customGlyphs"] = ",".join(js_options["customGlyphs"])
                expected = page.evaluate("""opts => {
                  const a=window.__windowApi,m=new a.WindowManager();
                  m.options=a.validateWindowOptions(opts);m.add({id:'source-window',title:'W'});
                  return m.controls('source-window').map(c=>({action:c.action,
                    glyph:[...c.glyph].map(x=>x.codePointAt(0))[0],color:c.color,label:c.label,
                    index:c.index,side:c.side,width:c.width,height:c.height}));
                }""", js_options)
                options = c_options(config)
                self.assertEqual(self.lib.nrWindowSourcePresentationValid(ctypes.byref(options)), 1)
                actual = c_controls(self.lib, options)
                self.assertEqual(actual, expected)
                self.assertEqual(len(actual), 4)
                self.assertEqual([item["index"] for item in actual], [0, 1, 2, 3])
            browser.close()

    def test_module_compiles_without_host_math_or_runtime(self):
        with tempfile.TemporaryDirectory(prefix="nr-window-source-freestanding-") as tmp:
            cc = os.environ.get("CC", "cc")
            subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-ffreestanding", "-fno-builtin", "-nostdlib", "-c",
                            "-I", str(ROOT / "src"), str(SOURCE), "-o",
                            str(Path(tmp) / "window_source_presentation.o")],
                           cwd=ROOT, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
