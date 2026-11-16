"""RC2 triangle differential: exact original JS method, native C, and import-free WASM."""
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
SOURCE = ROOT / "src/window_texture_source.c"
HEADER = ROOT / "src/window_texture_source.h"
WASM_RUNNER = ROOT / "tests/window_texture_source_wasm_runner.mjs"
SHAPES = {name: i for i, name in enumerate(("rectangle", "rounded", "ellipse", "hexagon",
    "diamond", "capsule", "ticket", "squircle", "petal", "wave"))}


class Vertex(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double),
                ("u", ctypes.c_double), ("v", ctypes.c_double), ("opacity", ctypes.c_double)]


def make_case(**patch):
    width, height = 18, 23
    cells = []
    for y in range(height):
        for x in range(width):
            cells.extend((0x2580 if (x + y) % 5 == 0 else 32,
                          0x202020 + (x * 13 << 8) + y * 7,
                          0x304050 + (y * 11 << 8) + x * 5,
                          (x + 3 * y) % 19))
    texture = []
    for y in range(5):
        for x in range(4):
            glyph = (32, 65, 0x2584, 0x2801)[(x + 2 * y) % 4]
            texture.extend((glyph, 0xE02010 + x * 0x0800 + y * 0x0301,
                            0x102030 + y * 0x0406 + x * 0x0203, 0))
    case = dict(
        vertices=[dict(x=3.15, y=10.25, z=.75, u=0, v=0, opacity=.8),
                  dict(x=15.4, y=11.1, z=2.0, u=1, v=0, opacity=.35),
                  dict(x=8.2, y=21.0, z=1.25, u=.4, v=1, opacity=.95)],
        shape=SHAPES["rectangle"], iris=0, visibility=.6, hitId=42,
        textureWidth=4, textureHeight=5, texture=texture,
        surfaceWidth=width, surfaceHeight=height, surface=cells,
        depth=[12.0] * (width * height), clip=[0, 9, width, height - 11],
        shapeQueries=[],
    )
    case.update(patch)
    return case


def source_triangle(page, case):
    payload = {key: case[key] for key in ("vertices", "shape", "iris", "visibility", "hitId",
        "textureWidth", "textureHeight", "texture", "surfaceWidth", "surfaceHeight",
        "surface", "depth")}
    return page.evaluate("""input => {
      const {KineticRenderer}=window.__nrWindowTextureApi;
      const out={width:input.surfaceWidth,height:input.surfaceHeight,cells:input.surface.slice()};
      const tex={width:input.textureWidth,height:input.textureHeight,cells:input.texture.slice()};
      const depth=input.depth.slice();
      Object.create(KineticRenderer.prototype).triangle(out,tex,depth,input.vertices,
        window.__nrWindowTextureApi.shapes[input.shape],
        {effect:input.iris?'iris':'none',visibility:input.visibility},input.hitId);
      return {surface:out.cells,depth};
    }""", payload)


def c_triangle(lib, case, *, overrides=None):
    vertices = (Vertex * 3)(*(Vertex(**v) for v in case["vertices"]))
    texture = (ctypes.c_uint32 * len(case["texture"]))( *case["texture"] )
    surface = (ctypes.c_uint32 * len(case["surface"]))( *case["surface"] )
    depth = (ctypes.c_double * len(case["depth"]))( *case["depth"] )
    args = [vertices, case["shape"], case["iris"], case["visibility"], case["hitId"],
            case["textureWidth"], case["textureHeight"], texture,
            case["surfaceWidth"], case["surfaceHeight"], *case["clip"], surface, depth]
    if overrides:
        args = overrides(args)
    status = lib.nrWindowTextureTriangle(*args)
    return {"status": status, "surface": list(surface), "depth": list(depth)}


class WindowTextureSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.exists() or not HEADER.exists():
            raise AssertionError("production window texture source module is missing")
        cls.temp = tempfile.TemporaryDirectory(prefix="nr-window-texture-source-")
        out = Path(cls.temp.name)
        suffix = ".dylib" if platform.system() == "Darwin" else ".so"
        shared = out / ("window_texture_source" + suffix)
        cc = os.environ.get("CC", "cc")
        subprocess.run([cc, "-std=c11", "-O0", "-fPIC", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT / "src"), "-dynamiclib" if platform.system() == "Darwin" else "-shared",
            str(SOURCE), "-o", str(shared)], cwd=ROOT, check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(shared))
        cls.lib.nrWindowTextureTriangle.argtypes = [ctypes.POINTER(Vertex), ctypes.c_uint32,
            ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32,
            ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_double)]
        cls.lib.nrWindowTextureTriangle.restype = ctypes.c_int
        cls.lib.nrWindowTextureShapeContains.argtypes = [ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
        cls.lib.nrWindowTextureShapeContains.restype = ctypes.c_int
        cls.wasm = out / "window_texture_source.wasm"
        clang = shutil.which("clang")
        wasm_ld = shutil.which("wasm-ld")
        cls.node = shutil.which("node")
        if not clang or not wasm_ld or not cls.node:
            raise AssertionError("clang, wasm-ld, and Node are required for the actual WASM check")
        obj = out / "window_texture_source.o"
        subprocess.run([clang, "--target=wasm32", "-std=c11", "-O2", "-ffp-contract=off",
            "-fno-fast-math", "-fno-strict-aliasing", "-Wall", "-Wextra", "-Werror",
            "-Iinclude", "-Isrc", "-nostdlib", "-ffreestanding", "-fno-builtin",
            "-Ifreestanding", "-c", str(SOURCE), "-o", str(obj)], cwd=ROOT,
            check=True, capture_output=True, text=True)
        subprocess.run([wasm_ld, "--no-entry", "--export-memory",
            "--export=nrWindowTextureTriangle", "--export=nrWindowTextureShapeContains",
            "--stack-first", "-z", "stack-size=1048576", "--initial-memory=16777216",
            str(obj), "-o", str(cls.wasm)], cwd=ROOT, check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        html = load_rc2_workbench()
        anchor = "return {KineticRenderer,hitKinetic,activateKinetic};"
        self.assertEqual(html.count(anchor), 1)
        exposed = html.replace(anchor,
            "window.__nrWindowTextureApi={KineticRenderer,shapeContains,shapes:WINDOW_SHAPES};" + anchor, 1)
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        self.page = self.browser.new_page()
        self.page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_function("window.fieldGuide && window.__nrWindowTextureApi", timeout=30000)

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def _run_wasm(self, case):
        out = Path(self.temp.name)
        case_path = out / "window-texture-case.json"
        case_path.write_text(json.dumps(case, allow_nan=False))
        result = subprocess.run([self.node, str(WASM_RUNNER), str(self.wasm), str(case_path)],
            check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def _assert_differential(self, case):
        source = source_triangle(self.page, case)
        native = c_triangle(self.lib, case)
        self.assertEqual(native["status"], 0)
        self.assertEqual(native["surface"], source["surface"])
        for actual, expected in zip(native["depth"], source["depth"]):
            self.assertAlmostEqual(actual, expected, delta=1e-14)
        wasm = self._run_wasm(case)
        self.assertEqual(wasm["status"], 0)
        self.assertEqual(wasm["surface"], source["surface"])
        for actual, expected in zip(wasm["depth"], source["depth"]):
            self.assertAlmostEqual(actual, expected, delta=1e-14)
        return source

    def test_original_shape_masks_boundaries_match_c_and_wasm(self):
        queries = []
        for shape in range(10):
            for iu in range(101):
                for iv in range(101):
                    queries.append([shape, iu / 100, iv / 100])
            for u, v in ((0, 0), (.5, .5), (1, 1), (.5, 0), (0, .5),
                         (.075, .5), (.925, .5), (.1, .04), (.9, .94),
                         ("__nan__", .5), (-.001, .5), (1.001, .5)):
                queries.append([shape, u, v])
        source = self.page.evaluate("""qs => qs.map(([shape,u0,v0])=>{
          try {const a=window.__nrWindowTextureApi, u=u0==='__nan__'?NaN:u0, v=v0==='__nan__'?NaN:v0;
            return a.shapeContains(a.shapes[shape],u,v)}catch(_){return -1}
        })""", queries)
        self.assertEqual(len(source), len(queries))
        case = make_case(shapeQueries=queries)
        wasm = self._run_wasm(case)
        for (shape, u, v), expected, actual in zip(queries, source, wasm["shapes"]):
            u = float("nan") if u == "__nan__" else u
            v = float("nan") if v == "__nan__" else v
            with self.subTest(shape=shape, u=u, v=v):
                self.assertEqual(self.lib.nrWindowTextureShapeContains(shape, u, v), expected)
                self.assertEqual(actual, expected)
        self.assertEqual(wasm["status"], 0)

    def test_perspective_uv_depth_flatten_transparency_edge_and_iris_match_original(self):
        cases = [make_case(),
            make_case(shape=SHAPES["ellipse"], iris=1, visibility=.43, hitId=0x10203),
            make_case(vertices=[dict(x=2.1,y=10.1,z=.5,u=0,v=0,opacity=.2),
                                dict(x=16.3,y=10.1,z=1.7,u=1,v=0,opacity=.9),
                                dict(x=8.4,y=21.5,z=2.4,u=.5,v=1,opacity=.6)],
                      shape=SHAPES["petal"]),
            make_case(shape=SHAPES["wave"])]
        for case in cases:
            with self.subTest(shape=case["shape"], iris=case["iris"], clip=case["clip"]):
                self._assert_differential(case)

    def test_full_braille_and_block_cells_retain_distinct_original_glyphs(self):
        # Reported regression: U+28FF must never become U+2588 during sampling.
        for glyph in (0x28ff, 0x2588, 0x2580, 0x2584, 0x258c, 0x2590, 0x1f680):
            case = make_case(textureWidth=1, textureHeight=1,
                             texture=[glyph, 0xfedcba, 0x123456, 0])
            for vertex in case["vertices"]:
                vertex["opacity"] = 1
            with self.subTest(glyph=hex(glyph)):
                original = self._assert_differential(case)
                owned = [original["surface"][i:i+4]
                         for i in range(0, len(original["surface"]), 4)
                         if original["surface"][i+3] == case["hitId"]]
                self.assertTrue(owned)
                self.assertEqual({cell[0] for cell in owned}, {glyph})
                self.assertEqual({cell[1] for cell in owned}, {0xfedcba})
                self.assertEqual({cell[2] for cell in owned}, {0x123456})

    def test_degenerate_and_fully_offscreen_triangles_are_successful_noops(self):
        base = make_case()
        for vertices in (
            [dict(x=4,y=10,z=1,u=0,v=0,opacity=1), dict(x=8,y=10,z=1,u=1,v=0,opacity=1),
             dict(x=12,y=10,z=1,u=0,v=1,opacity=1)],
            [dict(x=-20,y=-20,z=1,u=0,v=0,opacity=1), dict(x=-15,y=-20,z=1,u=1,v=0,opacity=1),
             dict(x=-18,y=-15,z=1,u=0,v=1,opacity=1)],
        ):
            case = make_case(vertices=vertices)
            with self.subTest(vertices=vertices):
                source = self._assert_differential(case)
                self.assertEqual(source["surface"], case["surface"])
                self.assertEqual(source["depth"], case["depth"])

    def test_overlapping_depth_tie_and_clipping_match_original(self):
        first = make_case()
        self._assert_differential(first)
        source = source_triangle(self.page, first)
        layered = make_case(surface=source["surface"], depth=source["depth"],
            vertices=[dict(x=3.1,y=10.2,z=.751,u=0,v=0,opacity=.7),
                      dict(x=15.2,y=11.2,z=2.001,u=1,v=0,opacity=.7),
                      dict(x=8.3,y=20.9,z=1.251,u=.4,v=1,opacity=.7)])
        self._assert_differential(layered)
        same_depth = make_case(surface=source["surface"], depth=source["depth"])
        self._assert_differential(same_depth)
        below_cutoff = make_case(vertices=[dict(v, opacity=.004) for v in first["vertices"]])
        cutoff_source = self._assert_differential(below_cutoff)
        self.assertEqual(cutoff_source["surface"], below_cutoff["surface"])
        self.assertEqual(cutoff_source["depth"], below_cutoff["depth"])
        rejected = make_case(surface=source["surface"], depth=source["depth"],
            vertices=[dict(x=3.1,y=10.2,z=8,u=0,v=0,opacity=.7),
                      dict(x=15.2,y=11.2,z=8,u=1,v=0,opacity=.7),
                      dict(x=8.3,y=20.9,z=8,u=.4,v=1,opacity=.7)])
        self._assert_differential(rejected)

    def test_explicit_clip_is_half_open_and_does_not_touch_outside_cells(self):
        case = make_case(clip=[5, 12, 10, 16])
        native = c_triangle(self.lib, case)
        wasm = self._run_wasm(case)
        self.assertEqual(native["status"], 0)
        self.assertEqual(wasm["status"], 0)
        self.assertEqual(native["surface"], wasm["surface"])
        for y in range(case["surfaceHeight"]):
            for x in range(case["surfaceWidth"]):
                index = (y * case["surfaceWidth"] + x) * 4
                if not (5 <= x < 10 and 12 <= y < 16):
                    self.assertEqual(native["surface"][index:index + 4], case["surface"][index:index + 4])
                    self.assertEqual(native["depth"][y * case["surfaceWidth"] + x],
                                     case["depth"][y * case["surfaceWidth"] + x])

    def test_fractional_minimum_reaches_last_clipped_sample_row(self):
        # RC2 starts at floor(minY), ends at ceil(maxY), and includes both.
        # Row 11 is the final row in [9, 12); minY=11.2 still samples its
        # center at 11.5. A raw-minimum fast-cull incorrectly drops it.
        vertices = [dict(x=3.1, y=11.2, z=1, u=0, v=0, opacity=1),
                    dict(x=15.0, y=11.2, z=1, u=1, v=0, opacity=1),
                    dict(x=8.0, y=20.0, z=1, u=.5, v=1, opacity=1)]
        case = make_case(vertices=vertices)
        source = self._assert_differential(case)
        self.assertTrue(any(source["surface"][i + 3] == case["hitId"]
                            for i in range((11 * case["surfaceWidth"]) * 4,
                                           (12 * case["surfaceWidth"]) * 4, 4)))

    def test_triangle_starting_at_first_excluded_row_is_noop(self):
        vertices = [dict(x=3.1, y=12.0, z=1, u=0, v=0, opacity=1),
                    dict(x=15.0, y=12.0, z=1, u=1, v=0, opacity=1),
                    dict(x=8.0, y=20.0, z=1, u=.5, v=1, opacity=1)]
        case = make_case(vertices=vertices)
        source = self._assert_differential(case)
        self.assertEqual(source["surface"], case["surface"])
        self.assertEqual(source["depth"], case["depth"])

    def test_invalid_inputs_reject_atomically(self):
        good = make_case()
        sentinel_surface = list(good["surface"])
        sentinel_depth = list(good["depth"])
        for patch in (
            {"shape": 10}, {"iris": 2}, {"visibility": float("nan")},
            {"textureWidth": 0}, {"surfaceHeight": 0}, {"clip": [4, 4, 3, 12]},
            {"clip": [-1, 9, 3, 12]},
        ):
            case = make_case(**patch)
            native = c_triangle(self.lib, case)
            with self.subTest(patch=patch):
                self.assertEqual(native["status"], -1)
                self.assertEqual(native["surface"], sentinel_surface)
                self.assertEqual(native["depth"], sentinel_depth)
        bad_vertex = make_case(vertices=[dict(good["vertices"][0], z=0),
            good["vertices"][1], good["vertices"][2]])
        native = c_triangle(self.lib, bad_vertex)
        self.assertEqual(native["status"], -1)
        self.assertEqual(native["surface"], sentinel_surface)
        self.assertEqual(native["depth"], sentinel_depth)
        negative_z = make_case(vertices=[dict(good["vertices"][0], z=-1),
            good["vertices"][1], good["vertices"][2]])
        wasm = self._run_wasm(make_case(shape=10))
        self.assertEqual(wasm["status"], -1)
        self.assertEqual(wasm["surface"], sentinel_surface)
        self.assertEqual(wasm["depth"], sentinel_depth)
        self.assertEqual(c_triangle(self.lib, negative_z)["status"], -1)
        huge = 1.7976931348623157e308
        overflow_triangle = make_case(vertices=[
            dict(x=huge, y=huge, z=1, u=0, v=0, opacity=.5),
            dict(x=-huge, y=-huge, z=1, u=1, v=0, opacity=.5),
            dict(x=huge, y=-huge, z=1, u=0, v=1, opacity=.5)])
        for observed in (c_triangle(self.lib, overflow_triangle), self._run_wasm(overflow_triangle)):
            self.assertEqual(observed["status"], -1)
            self.assertEqual(observed["surface"], sentinel_surface)
            self.assertEqual(observed["depth"], sentinel_depth)

        # This is a word-count the prior check accepted, but its four-byte
        # cell-array span cannot be represented by a WASM32 byte pointer.
        wasm_texture_overflow = self._run_wasm(make_case(textureWidth=268435456, textureHeight=1))
        self.assertEqual(wasm_texture_overflow["status"], -1)
        wasm_surface_overflow = self._run_wasm(make_case(surfaceWidth=268435456, surfaceHeight=1))
        self.assertEqual(wasm_surface_overflow["status"], -1)
        nonfinite = make_case(vertices=[dict(good["vertices"][0], x=float("inf")),
            good["vertices"][1], good["vertices"][2]])
        self.assertEqual(c_triangle(self.lib, nonfinite)["status"], -1)


if __name__ == "__main__":
    unittest.main()
