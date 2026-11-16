"""Original RC2 theatre buttons painted through production native Stage cells."""
from __future__ import annotations

import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json
import ctypes
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from native.tests.historical_reference import load_rc2_workbench
from native.tests.test_window_presentation import ACTION, Options, defaults

ROOT = Path(__file__).resolve().parents[1]


class Cell(ctypes.Structure):
    _fields_ = [("glyph", ctypes.c_uint32), ("foreground", ctypes.c_uint32),
                ("background", ctypes.c_uint32), ("id", ctypes.c_uint32)]


def stage_node(source, text_offset):
    fields = dict(kind=0, id=1, x=2, y=3, width=4, height=5, state=6,
                  fg=12, bg=13, fgOpacity=14, bgOpacity=15, style=16,
                  textOffset=17, textLength=18, hueStep=21, hueSpeed=22,
                  saturation=26, brightness=27, zoom=30)
    row = [0] * 32
    values = {
        "kind": 3, "id": source["id"], "x": source["x"], "y": source["y"],
        "width": source["width"], "height": source["height"],
        "state": source.get("state", 0), "fg": source["fg"], "bg": source["bg"],
        "fgOpacity": source["fgOpacity"], "bgOpacity": source["bgOpacity"],
        "style": source.get("style", 0), "textOffset": text_offset,
        "textLength": len(source["text"]), "hueStep": 17, "hueSpeed": 24,
        "saturation": 620, "brightness": 830, "zoom": 1,
    }
    for name, value in values.items():
        row[fields[name]] = value
    return row


class WindowPresentationPaint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ctypes

        cls.temp = tempfile.TemporaryDirectory(prefix="nr-window-toolbar-paint-")
        probe = Path(cls.temp.name) / "probe.c"
        probe.write_text(r'''#include "internal.h"
#include <stdlib.h>
int nrWindowToolbarPaintProbe(int width, const NrWindowSourcePresentationOptions *options,
    uint32_t targetId, const NrCell *initial, NrCell *out, uint32_t capacity) {
    const int height=12;
    if(width<1||!out||capacity<(uint32_t)width*height)return -2;
    NrContext *c=calloc(1,sizeof(NrContext));if(!c)return -3;
    size_t n=(size_t)width*height;
    c->cells=calloc(n,sizeof(NrCell));c->characterIndices=calloc(n,sizeof(uint32_t));
    c->characterOwners=calloc(n,sizeof(uint32_t));
    if(!c->cells||!c->characterIndices||!c->characterOwners){free(c->cells);free(c->characterIndices);free(c->characterOwners);free(c);return -3;}
    c->state.width=(uint32_t)width;c->state.height=height;c->clip=(ClipRect){0,0,width,height};
    if(initial)memcpy(c->cells,initial,n*sizeof(NrCell));
    int result=nrWindowPresentationDrawTheatreToolbar(c,width,options,1.0,targetId);
    memcpy(out,c->cells,n*sizeof(NrCell));
    free(c->cells);free(c->characterIndices);free(c->characterOwners);free(c);return result;
}
int nrWindowPresentationValidityProbe(uint32_t schema, int enabled) {
    State *s=calloc(1,sizeof(State));if(!s)return -3;
    s->schema=schema;s->windows[0].used=1;s->windows[0].id=5;s->windows[0].alpha=.85;
    if(enabled){s->windowPresentation[0].enabled=1;nrWindowSourcePresentationDefaults(&s->windowPresentation[0].options);}
    int result=nrValidWindowPresentation(s);free(s);return result;
}
''', encoding="utf-8")
        output = Path(cls.temp.name) / ("window_toolbar.dylib" if platform.system() == "Darwin"
                                        else "window_toolbar.so")
        link = ["-dynamiclib", "-Wl,-dead_strip"] if platform.system() == "Darwin" else ["-shared", "-Wl,--gc-sections"]
        library = ROOT / "dist" / ("libnocturne_native.dylib" if platform.system() == "Darwin"
                                   else "libnocturne_native.so")
        if not library.is_file():
            raise AssertionError(f"build the complete current native library first: {library}")
        # The toolbar calls the real Stage implementation, including its current
        # scene/modal dependencies. Link the qualified image rather than maintain
        # a second, incomplete implementation source list in this probe.
        command = [os.environ.get("CC", "cc"), "-std=c11", "-O0", "-fPIC",
                   "-ffunction-sections", "-fdata-sections", "-I", str(ROOT / "src"),
                   "-I", str(ROOT / "include"), *link, str(probe), str(library),
                   "-Wl,-rpath," + str(library.parent), "-o", str(output)]
        compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if compiled.returncode:
            raise AssertionError(compiled.stdout + compiled.stderr)
        cls.lib = ctypes.CDLL(str(output))
        cls.production = ctypes.CDLL(str(library))
        for symbol in ("nrWindowPresentationDrawTheatreToolbar", "nrValidWindowPresentation"):
            if ctypes.cast(getattr(cls.lib, symbol), ctypes.c_void_p).value != ctypes.cast(
                    getattr(cls.production, symbol), ctypes.c_void_p).value:
                raise AssertionError(f"probe did not resolve the current production symbol: {symbol}")
        cls.lib.nrWindowToolbarPaintProbe.argtypes = [ctypes.c_int, ctypes.POINTER(Options),
            ctypes.c_uint32, ctypes.POINTER(Cell), ctypes.POINTER(Cell), ctypes.c_uint32]
        cls.lib.nrWindowToolbarPaintProbe.restype = ctypes.c_int
        cls.lib.nrWindowPresentationValidityProbe.argtypes = [ctypes.c_uint32, ctypes.c_int]
        cls.lib.nrWindowPresentationValidityProbe.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_rc2_theatre_button_cells_match_original_wasm_paint(self):
        from playwright.sync_api import sync_playwright

        source = load_rc2_workbench()
        renderer_anchor = "return {KineticRenderer,hitKinetic,activateKinetic};"
        stage_anchor = "frame = this.engine.paint(frame, m.motionMs, nodes);"
        self.assertEqual(source.count(renderer_anchor), 1)
        self.assertEqual(source.count(stage_anchor), 1)
        exposed = source.replace(renderer_anchor,
            "window.__historicalTheatreApi={KineticModel,KineticRenderer};" + renderer_anchor, 1)
        exposed = exposed.replace(stage_anchor,
            "return {frame,nodes,semantics,drawnStars,activeWeather,actions};", 1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True,
                executable_path=os.environ.get("CHROMIUM") or shutil.which("chromium") or
                shutil.which("google-chrome") or shutil.which("chrome"),
                args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__historicalTheatreApi", timeout=30000)
            actual = page.evaluate("""() => {
              const api=window.__historicalTheatreApi, model=new api.KineticModel();
              model.scene='windows';model.width=100;model.height=12;
              const result=new api.KineticRenderer(window.fieldGuide.engine).render(model,0);
              return {width:result.frame.width,height:result.frame.height,
                cells:Array.from(result.frame.cells),buttons:result.nodes.filter(n=>
                  n.kind==='button'&&n.id>=12000&&n.id<12004)};
            }""")
            browser.close()
        self.assertEqual(errors, [])
        self.assertEqual((actual["width"], actual["height"]), (100, 12))
        self.assertEqual(len(actual["buttons"]), 4)
        self.assertTrue(all(node["bg"] == 0x1e2938 and node["bgOpacity"] == 880 and
                            node["fgOpacity"] == 1000 for node in actual["buttons"]))

        base = [tuple(actual["cells"][i:i + 4]) for i in range(0, len(actual["cells"]), 4)]
        text, nodes = [], []
        for button in actual["buttons"]:
            pool = [ord(char) for char in button["text"]]
            nodes.append(stage_node(button, len(text)))
            text.extend(pool)
        original_request = [{"width": 100, "height": 12, "timeMs": 0,
                             "cells": [value for cell in base for value in cell],
                             "nodes": nodes, "text": text}]
        html_path = Path(self.temp.name) / "original.html"
        html_path.write_text(source, encoding="utf-8")
        original = subprocess.run(["node", str(ROOT / "tests/original_rc2_stage_paint_oracle.mjs"),
                                   str(html_path)], input=json.dumps(original_request),
                                  capture_output=True, text=True, timeout=60, check=True)
        expected_result = json.loads(original.stdout)
        expected = expected_result["cases"][0]
        options = defaults()
        count = actual["width"] * actual["height"]
        initial_cells = (Cell * count)(*(Cell(*cell) for cell in base))
        native_cells = (Cell * count)()
        self.assertEqual(self.lib.nrWindowToolbarPaintProbe(100, ctypes.byref(options),
            1, initial_cells, native_cells, count), 0)
        for index, (native, original_cell) in enumerate(zip(native_cells, expected)):
            self.assertEqual((native.glyph, native.foreground, native.background),
                             tuple(original_cell[:3]), f"toolbar paint cell {index}")
        self.assertEqual(expected_result["editionSha256"],
                         "375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385")
        self.assertEqual(expected_result["wasmSha256"],
                         "aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09")

    def test_enabled_source_presentation_requires_schema_67(self):
        self.assertEqual(self.lib.nrWindowPresentationValidityProbe(0x20261066, 0), 1)
        self.assertEqual(self.lib.nrWindowPresentationValidityProbe(0x20261067, 0), 1)
        self.assertEqual(self.lib.nrWindowPresentationValidityProbe(0x20261066, 1), 0)
        self.assertEqual(self.lib.nrWindowPresentationValidityProbe(0x20261067, 1), 1)


if __name__ == "__main__":
    unittest.main()
