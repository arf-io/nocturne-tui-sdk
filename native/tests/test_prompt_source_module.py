"""Differential tests for the production, standalone RC2 prompt source module."""
from __future__ import annotations

import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes
import math
import os
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "prompt_source.c"
HEADER = ROOT / "src" / "prompt_source.h"


class Options(ctypes.Structure):
    _fields_ = [
        ("alpha", ctypes.c_double),
        ("background", ctypes.c_uint32), ("foreground", ctypes.c_uint32),
        ("accent", ctypes.c_uint32), ("selectionColor", ctypes.c_uint32),
        ("border", ctypes.c_int),
        ("paddingX", ctypes.c_int64), ("paddingY", ctypes.c_int64),
        ("margin", ctypes.c_int64), ("minRows", ctypes.c_int64),
        ("maxRows", ctypes.c_int64), ("inlineRows", ctypes.c_int64),
        ("inlineWidth", ctypes.c_int64),
        ("lineNumbers", ctypes.c_int), ("active", ctypes.c_int),
        ("selected", ctypes.c_int),
        ("hueStep", ctypes.c_double), ("hueSpeed", ctypes.c_double),
        ("huePeriodMs", ctypes.c_int64), ("maxChars", ctypes.c_uint32),
    ]


class Input(ctypes.Structure):
    _fields_ = [
        ("scalars", ctypes.POINTER(ctypes.c_uint32)),
        ("scalarCount", ctypes.c_size_t), ("caret", ctypes.c_size_t),
        ("selectionStart", ctypes.c_size_t), ("selectionEnd", ctypes.c_size_t),
        ("hasSelection", ctypes.c_int),
        ("statusScalars", ctypes.POINTER(ctypes.c_uint32)),
        ("statusCount", ctypes.c_size_t),
        ("width", ctypes.c_int64), ("height", ctypes.c_int64),
        ("timeMs", ctypes.c_uint64), ("mode", ctypes.c_int),
        ("vimState", ctypes.c_int), ("minimizedRestoreMode", ctypes.c_int),
        ("options", Options),
    ]


class Layout(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int32) for name in (
        "rectX rectY rectWidth rectHeight innerX innerY innerWidth innerHeight "
        "caretX caretY visibleRows border numberWidth prefix top offset extraRows "
        "sceneHeight full vim").split()]


BackgroundFn = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint32,
    ctypes.c_double, ctypes.c_int, ctypes.c_int,
)
GlyphFn = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint32,
    ctypes.c_uint32, ctypes.c_double, ctypes.c_int, ctypes.c_int,
)


class Sink(ctypes.Structure):
    _fields_ = [("context", ctypes.c_void_p), ("background", BackgroundFn),
                ("glyph", GlyphFn)]


def source_options(**patch):
    values = dict(alpha=.32, background=0x10161e, foreground=0xdedbd2,
                  accent=0x8ccfc4, selectionColor=0x385763, border=1,
                  paddingX=1, paddingY=0, margin=1, minRows=1, maxRows=7,
                  inlineRows=12, inlineWidth=88, lineNumbers=1, active=1,
                  selected=0, hueStep=0, hueSpeed=0, huePeriodMs=1000,
                  maxChars=65536)
    values.update(patch)
    return Options(**values)


def native_options(source):
    values = dict(source)
    if isinstance(values.get("border"), str):
        values["border"] = {"none": 0, "rounded": 1, "square": 2,
                             "double": 3, "heavy": 4}[values["border"]]
    return source_options(**values)


def make_input(text="Type light into this surface.", mode=0, width=100, height=40,
               caret=0, options=None, selection=None, time_ms=0,
               vim_state=0, minimized=0, status=""):
    scalars = (ctypes.c_uint32 * len(text))(*(ord(ch) for ch in text))
    status_scalars = (ctypes.c_uint32 * len(status))(*(ord(ch) for ch in status))
    start, end = selection if selection else (0, 0)
    inp = Input(scalars, len(text), caret, start, end, int(selection is not None),
                status_scalars, len(status), width, height, time_ms, mode,
                vim_state, minimized, options or source_options())
    return inp, scalars, status_scalars


def mix_color(a, b, alpha):
    channels = []
    for shift in (16, 8, 0):
        x, y = (a >> shift) & 255, (b >> shift) & 255
        channels.append(math.floor(x * (1 - alpha) + y * alpha + .5))
    return (channels[0] << 16) | (channels[1] << 8) | channels[2]


def module_frame(lib, inp, initial=(32, 0xEEEEEE, 0x123456, 0)):
    layout = Layout()
    if lib.nrPromptSourceLayout(ctypes.byref(inp), ctypes.byref(layout)) != 0:
        raise AssertionError("source module rejected a valid frame")
    cells = [[*initial] for _ in range(inp.width * inp.height)]
    owners = {1: 910001, 2: 910002, 3: 910003, 4: 910004, 5: 910005, 6: 910006}
    def background(_ctx, x, y, rgb, alpha, kind, owner):
        cell = cells[y * inp.width + x]
        if kind == 1:  # panel: RC2 clears non-art glyphs and mixes both channels
            if cell[0] not in (32, 0x2580, 0x2584, 0x258C, 0x2590) and not 0x2800 <= cell[0] <= 0x28FF:
                cell[0] = 32
            cell[1] = mix_color(cell[1], rgb, alpha)
            cell[2] = mix_color(cell[2], rgb, alpha)
            cell[3] = owners[owner]
        elif kind in (2, 3):
            cell[2] = mix_color(cell[2], rgb, alpha)
    def glyph(_ctx, x, y, scalar, foreground, _alpha, _kind, owner):
        cell = cells[y * inp.width + x]
        cell[0] = scalar
        cell[1] = foreground
        cell[3] = owners[owner]
    bg_callback = BackgroundFn(background)
    glyph_callback = GlyphFn(glyph)
    result = lib.nrPromptSourcePaint(ctypes.byref(inp), ctypes.byref(layout),
                                     Sink(None, bg_callback, glyph_callback))
    if result != 0:
        raise AssertionError("source module rejected paint after layout")
    return layout, [channel for cell in cells for channel in cell]


class PromptSourceModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="nr-prompt-source-")
        output = Path(cls.temp.name) / ("prompt_source.dylib" if platform.system() == "Darwin"
                                        else "prompt_source.so")
        cc = os.environ.get("CC", "cc")
        command = [cc, "-std=c11", "-O0", "-fPIC", "-I", str(ROOT / "include"),
                   "-I", str(ROOT / "src"),
                   "-dynamiclib" if platform.system() == "Darwin" else "-shared",
                   str(SOURCE), str(ROOT / "src" / "math.c"), "-lm", "-o", str(output)]
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(output))
        cls.lib.nrPromptSourceLayout.argtypes = [ctypes.POINTER(Input), ctypes.POINTER(Layout)]
        cls.lib.nrPromptSourceLayout.restype = ctypes.c_int
        cls.lib.nrPromptSourcePaint.argtypes = [ctypes.POINTER(Input), ctypes.POINTER(Layout), Sink]
        cls.lib.nrPromptSourcePaint.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def layout(self, inp):
        out = Layout()
        self.assertEqual(self.lib.nrPromptSourceLayout(ctypes.byref(inp), ctypes.byref(out)), 0)
        return out

    def test_original_chromium_layouts_match_native_module_for_all_four_modes(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        api_anchor = "return {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument};"
        self.assertEqual(html.count(api_anchor), 1)
        exposed = html.replace(api_anchor,
            "window.__promptApi={PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,promptLayout,PromptDocument};" + api_anchor, 1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__promptApi", timeout=30000)
            source = page.evaluate("""() => {
              const api=window.__promptApi,doc=new api.PromptDocument('Type light into this surface.', api.DEFAULT_PROMPT);
              doc.caret=0;
              return api.PROMPT_MODES.map((mode,index)=>{doc.mode=mode;const l=api.promptLayout(doc,100,40);
                return {mode,index,rect:l.rect,inner:l.inner,visibleRows:l.visibleRows,border:l.border,
                  numberWidth:l.numberWidth,prefix:l.prefix,caret:l.caret};});
            }""")
            native = []
            for row in source:
                inp, *_ = make_input(mode=row["index"])
                l = self.layout(inp)
                native.append({"mode": row["mode"],
                    "rect": {"x": l.rectX, "y": l.rectY, "width": l.rectWidth, "height": l.rectHeight},
                    "inner": {"x": l.innerX, "y": l.innerY, "width": l.innerWidth, "height": l.innerHeight},
                    "visibleRows": l.visibleRows, "border": l.border,
                    "numberWidth": l.numberWidth, "prefix": l.prefix,
                    "caret": {"x": l.caretX, "y": l.caretY}})
            self.assertEqual(native, [{key: row[key] for key in native[0]} for row in source])
            browser.close()

    def test_source_painter_emits_original_chrome_selection_and_glyph_preserving_cursor(self):
        text = "Type light into this surface."
        inp, text_storage, _ = make_input(text, caret=0, selection=(0, 2))
        layout = self.layout(inp)
        operations = []
        background = BackgroundFn(lambda _ctx, x, y, rgb, alpha, kind, owner:
                                  operations.append(("bg", x, y, rgb, alpha, kind, owner)))
        glyph = GlyphFn(lambda _ctx, x, y, scalar, rgb, alpha, kind, owner:
                        operations.append(("glyph", x, y, scalar, rgb, alpha, kind, owner)))
        self.assertEqual(self.lib.nrPromptSourcePaint(
            ctypes.byref(inp), ctypes.byref(layout), Sink(None, background, glyph)), 0)
        self.assertTrue(any(op[0] == "glyph" and op[3] == ord("╭") and op[4] == 0x8ccfc4 for op in operations))
        self.assertTrue(any(op[0] == "glyph" and op[3] == ord("S") for op in operations))
        self.assertTrue(any(op[0] == "glyph" and op[3] == ord(">") for op in operations))
        typed = [op for op in operations if op[0] == "glyph" and op[3] == ord("T")
                 and (op[1], op[2]) == (layout.innerX, layout.innerY)]
        self.assertEqual(len(typed), 1, "the cursor must keep the source glyph under it")
        self.assertTrue(any(op[0] == "bg" and op[4] == .32 for op in operations))
        self.assertTrue(any(op[0] == "bg" and op[4] == .8 for op in operations))
        self.assertTrue(any(op[0] == "bg" and op[4] == .18 for op in operations))
        self.assertTrue(any(op[0] == "glyph" and op[3] == ord("T") and op[4] == 0xdedbd2 for op in operations))

    def test_actual_rc2_paint_prompt_frames_match_native_module_cells(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        paint_anchor = "return {PROMPT_IDS,WORKBENCH_SCENES,WorkbenchModel,paintPrompt,WorkbenchRenderer,activateWorkbench};"
        api_anchor = "return {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument};"
        self.assertEqual(html.count(paint_anchor), 1)
        self.assertEqual(html.count(api_anchor), 1)
        exposed = html.replace(paint_anchor,
            "window.__promptPaint={paintPrompt};" + paint_anchor, 1)
        exposed = exposed.replace(api_anchor,
            "window.__promptApi={PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,promptLayout,PromptDocument};" + api_anchor, 1)
        cases = [
            dict(text="Type light into this surface.", mode=0, caret=2, selection=(0, 2), time=0),
            dict(text="first row\nsecond row\nthird row", mode=1, caret=27, selection=None, time=0),
            dict(text="alpha\nbeta\ngamma\ndelta", mode=2, caret=9, selection=(6, 10), time=0, vim=2, status="-- VISUAL --"),
            dict(text="full screen\ntext", mode=3, caret=9, selection=None, time=0, vim=1, status="-- INSERT --"),
            dict(text="Hue motion across the prompt", mode=0, caret=10, selection=None, time=500,
                 options={"hueStep": 19, "hueSpeed": 90, "huePeriodMs": 250}),
            dict(text="A界e\u0301\nZ\t\u200b", mode=1, caret=5, selection=None, time=0),
            dict(text="large viewport", mode=3, caret=7, selection=None, time=0, width=300, height=100,
                 status="Esc NORMAL · i INSERT · :w checkpoint · :q close view · drag ↘ resize"),
            dict(text="minimized draft", mode=1, caret=6, selection=None, time=0, minimized=2),
            dict(text="control endpoints", mode=2, caret=4, selection=None, time=0,
                 vim=0, status="Esc NORMAL · i INSERT · :w checkpoint · :q close view · drag ↘ resize",
                 options={"alpha": 1, "border": "none", "paddingX": 8, "paddingY": 4,
                          "margin": 6, "minRows": 24, "maxRows": 60, "inlineRows": 80,
                          "inlineWidth": 240, "lineNumbers": False, "active": False,
                          "selected": True, "hueStep": -360, "hueSpeed": 360,
                          "huePeriodMs": 120000, "maxChars": 65536}),
            *[dict(text="border sample", mode=1, caret=3, selection=None, time=0,
                   options={"border": border})
              for border in ("square", "double", "heavy")],
        ]
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__promptPaint && window.__promptApi", timeout=30000)
            for case in cases:
                with self.subTest(mode=case["mode"], text=case["text"]):
                    source = page.evaluate("""cfg => {
                      const api=window.__promptApi, paint=window.__promptPaint.paintPrompt;
                      const options=api.validatePrompt(cfg.options||{}), d=new api.PromptDocument(cfg.text,options);
                      d.mode=api.PROMPT_MODES[cfg.mode];d.caret=cfg.caret;
                      d.anchor=cfg.selection?cfg.selection[0]:null;d.vimState=api.PROMPT_MODES[cfg.mode].startsWith('vim-')?['normal','insert','visual','command'][cfg.vim||0]:'normal';
                      d.minimizedMode=cfg.minimized?'vim-full':null;
                      d.message=cfg.status||'';
                      const frame={width:cfg.width||100,height:cfg.height||40,
                        cells:new Uint32Array((cfg.width||100)*(cfg.height||40)*4)};
                      for(let i=0;i<frame.cells.length;i+=4){frame.cells[i]=32;frame.cells[i+1]=0xeeeeee;frame.cells[i+2]=0x123456;frame.cells[i+3]=0;}
                      const result=paint(frame,d,cfg.time,fieldGuide.renderer.engine);
                      return {cells:Array.from(frame.cells),layout:{rect:result.layout.rect,inner:result.layout.inner,
                        caret:result.layout.caret,visibleRows:result.layout.visibleRows,top:result.layout.top,offset:result.layout.offset,
                        numberWidth:result.layout.numberWidth,prefix:result.layout.prefix}};
                    }""", case)
                    selection = case.get("selection")
                    options = native_options(case.get("options", {}))
                    inp, scalars, status = make_input(case["text"], mode=case["mode"], width=case.get("width",100),
                        height=case.get("height",40), caret=case["caret"], options=options, selection=selection,
                        time_ms=case["time"], vim_state=case.get("vim", 0), minimized=case.get("minimized",0), status=case.get("status", ""))
                    layout, actual = module_frame(self.lib, inp)
                    expected_layout = {"rect":{"x":layout.rectX,"y":layout.rectY,"width":layout.rectWidth,"height":layout.rectHeight},
                        "inner":{"x":layout.innerX,"y":layout.innerY,"width":layout.innerWidth,"height":layout.innerHeight},
                        "caret":{"x":layout.caretX,"y":layout.caretY},"visibleRows":layout.visibleRows,
                        "top":layout.top,"offset":layout.offset,"numberWidth":layout.numberWidth,"prefix":layout.prefix}
                    self.assertEqual(expected_layout, source["layout"])
                    differences = [(i // 4, i % 4, actual[i], source["cells"][i])
                                   for i in range(len(actual)) if actual[i] != source["cells"][i]][:12]
                    self.assertEqual(differences, [], "first native/original frame differences (cell channel index)")
            browser.close()

    def test_vim_multiline_minimized_and_hue_motion_are_streamed_without_document_caps(self):
        text = "alpha\nbeta\ngamma\ndelta"
        for mode, expected_height in ((2, 9), (3, 32)):
            inp, storage, _ = make_input(text, mode=mode, height=40, caret=len(text),
                                          vim_state=0)
            layout = self.layout(inp)
            self.assertEqual(layout.innerHeight, expected_height)
            self.assertLessEqual(layout.caretY, layout.innerY + layout.innerHeight - 1)
        minimized, storage, _ = make_input("restored", mode=0, minimized=2)
        layout = self.layout(minimized)
        operations = []
        bg = BackgroundFn(lambda *_args: None)
        glyph = GlyphFn(lambda _ctx, x, y, scalar, rgb, alpha, kind, owner:
                        operations.append((x, y, scalar, rgb, alpha, kind, owner)))
        self.assertEqual(self.lib.nrPromptSourcePaint(
            ctypes.byref(minimized), ctypes.byref(layout), Sink(None, bg, glyph)), 0)
        self.assertTrue(any(op[2] == ord("[") and op[6] == 5 for op in operations))

        plain, plain_storage, _ = make_input("Hue", options=source_options(hueSpeed=90), time_ms=0)
        later, later_storage, _ = make_input("Hue", options=source_options(hueSpeed=90), time_ms=500)
        def colors(inp):
            l = self.layout(inp); out = []
            callback = GlyphFn(lambda _ctx, _x, _y, scalar, rgb, _alpha, _kind, _owner:
                               out.append((scalar, rgb)))
            self.assertEqual(self.lib.nrPromptSourcePaint(
                ctypes.byref(inp), ctypes.byref(l), Sink(None, BackgroundFn(lambda *_: None), callback)), 0)
            return out
        self.assertNotEqual(colors(plain), colors(later))

        long_text = "x" * 65536
        long_doc, long_storage, _ = make_input(long_text, mode=0, caret=len(long_text))
        self.assertEqual(long_doc.scalarCount, 65536)
        self.assertEqual(self.lib.nrPromptSourceLayout(ctypes.byref(long_doc), ctypes.byref(Layout())), 0)

    def test_invalid_and_unrepresentable_inputs_fail_atomically_before_callbacks(self):
        bad_values = [
            make_input("x", mode=4)[0],
            make_input("x", options=source_options(border=9))[0],
            make_input("x", caret=2)[0],
            make_input("x", selection=(0, 2))[0],
            make_input("x", width=0)[0],
            make_input("x", options=source_options(alpha=1.01))[0],
            make_input("xx", options=source_options(maxChars=1))[0],
        ]
        for inp in bad_values:
            out = Layout()
            ctypes.memset(ctypes.byref(out), 0x5A, ctypes.sizeof(out))
            before = bytes(out)
            self.assertEqual(self.lib.nrPromptSourceLayout(ctypes.byref(inp), ctypes.byref(out)), -1)
            self.assertEqual(bytes(out), before)
        huge, storage, _ = make_input("x", width=(1 << 40), height=(1 << 40))
        self.assertEqual(self.lib.nrPromptSourceLayout(ctypes.byref(huge), ctypes.byref(Layout())), -1)


if __name__ == "__main__":
    unittest.main()
