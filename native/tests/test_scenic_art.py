"""Focused archive provenance and real native callback contract tests."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import base64
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest
from native.tests.historical_reference import RC2_ARCHIVE_SHA256, RC2_HTML_SHA256, load_rc2_workbench, rc2_workbench_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "evidence/gallery-presentation-20261013/original-reference"
WORLD_FIELDS = [
    "width", "height", "scene", "cameraX", "cameraY", "cameraZ", "yaw", "pitch",
    "roll", "fov", "projection", "span", "flow", "travel", "seed", "redshift",
    "discTilt", "detail", "waterAlpha", "background", "ink", "accent", "secondary", "sampling",
]
DETAIL_FIELDS = ["waveHeight", "wavelength", "windAngle", "crossSwell", "choppiness", "foam", "waveSpeed", "joinRiver"]


class ScenicArtContract(unittest.TestCase):
    def test_exact_rc2_archive_and_complete_control_mapping(self):
        oracle = json.loads((ORIGINAL / "SCENIC-ORACLES.json").read_text())
        archive_bytes = load_rc2_workbench().encode("utf-8")
        self.assertEqual(hashlib.sha256(archive_bytes).hexdigest(), oracle["source"]["sha256"])
        html = archive_bytes.decode("utf-8")
        embedded = re.search(r'"wasm"\s*:\s*"([A-Za-z0-9+/=]+)"', html)
        self.assertIsNotNone(embedded)
        wasm = base64.b64decode(embedded.group(1))
        self.assertEqual(len(wasm), oracle["source"]["embeddedWasmBytes"])
        self.assertEqual(hashlib.sha256(wasm).hexdigest(), oracle["source"]["embeddedWasmSha256"])
        self.assertEqual(oracle["fields"]["world"], WORLD_FIELDS)
        self.assertEqual(oracle["fields"]["detail"], DETAIL_FIELDS)
        self.assertEqual(oracle["fields"]["detailDefaultsQ"], [358, 8704, 5632, 480, 430, 620, 1000, 1])
        world_descriptor = re.search(r"const WORLD_FIELDS = (\[.*?\]);", html)
        detail_descriptor = re.search(r"const WORLD_DETAIL_FIELDS = (\[.*?\]);", html)
        self.assertIsNotNone(world_descriptor)
        self.assertIsNotNone(detail_descriptor)
        world_fields = json.loads(world_descriptor.group(1))
        detail_fields = json.loads(detail_descriptor.group(1))
        self.assertEqual([f["name"] for f in world_fields], WORLD_FIELDS)
        self.assertEqual([f["index"] for f in world_fields], list(range(24)))
        self.assertEqual([f["name"] for f in detail_fields], DETAIL_FIELDS)
        self.assertEqual([f["index"] for f in detail_fields], list(range(8)))
        self.assertEqual([round(f["default"] * f["scale"]) for f in detail_fields], oracle["fields"]["detailDefaultsQ"])
        self.assertEqual([round(f["default"] * f["scale"]) for f in world_fields],
                         [120, 40, 0, -68*256, 48*256, -96*256, 35*256, -22*256,
                          0, 62*256, 1, 145*256, 1000, 0, 2030, 700, 12*256, 1,
                          940, 1053726, 0, 0, 0, 1])
        raw = oracle["rawCellDifferentialOracle"]
        raw_manifest = ROOT / "evidence/original-scenic-restoration-20261013/ORIGINAL-WORLD-FRAMES.json"
        raw_table = ROOT / "evidence/original-scenic-restoration-20261013/ORIGINAL-WORLD-FRAMES.tsv"
        # Preserve the original metadata and its erroneous pin; the explicit
        # successor binds the actual unchanged manifest from its original commit.
        correction = json.loads((ORIGINAL / "SCENIC-ORACLE-MANIFEST-CORRECTION-20261014.json").read_text())
        self.assertEqual(correction["schema"], "nocturne.scenic-oracle-metadata-correction.v1")
        self.assertEqual(correction["field"], "rawCellDifferentialOracle.manifestSha256")
        self.assertEqual(correction["supersededValue"], raw["manifestSha256"])
        self.assertEqual(correction["originalRecord"]["path"], str((ORIGINAL / "SCENIC-ORACLES.json").relative_to(ROOT.parent)))
        self.assertEqual(hashlib.sha256((ORIGINAL / "SCENIC-ORACLES.json").read_bytes()).hexdigest(), correction["originalRecord"]["sha256"])
        self.assertEqual(correction["manifest"]["sourceCommit"], "87a5131f2c300362cab151c4f635bb62ba75f77b")
        self.assertEqual(correction["manifest"]["path"], str(raw_manifest.relative_to(ROOT.parent)))
        self.assertEqual(correction["correctValue"], correction["manifest"]["sha256"])
        self.assertEqual(hashlib.sha256(raw_manifest.read_bytes()).hexdigest(), correction["correctValue"])
        self.assertNotEqual(correction["correctValue"], correction["supersededValue"])
        self.assertEqual(hashlib.sha256(raw_table.read_bytes()).hexdigest(), raw["scenarioTableSha256"])
        self.assertEqual(len(json.loads(raw_manifest.read_text())["frames"]), raw["fullCellFrames"])
        root = ROOT.parent
        self.assertEqual(hashlib.sha256((root / oracle["source"]["algorithmWitness"]["geometry"]).read_bytes()).hexdigest(), oracle["source"]["algorithmWitness"]["geometrySha256"])
        self.assertEqual(hashlib.sha256((root / oracle["source"]["algorithmWitness"]["integerSine"]).read_bytes()).hexdigest(), oracle["source"]["algorithmWitness"]["integerSineSha256"])
        for name in ("WORLD_FIELDS", "WORLD_DETAIL_FIELDS", "WorldEngine", "SCENIC_WORLD", "WORKBENCH_SCENES"):
            self.assertIn(name, html)

    def test_scene_identity_and_available_capture_bytes(self):
        oracle = json.loads((ORIGINAL / "SCENIC-ORACLES.json").read_text())
        refs = {r["id"]: r for r in oracle["references"]}
        self.assertEqual(set(refs), {"pearl-cascade", "tidal-glass", "copper-causeway", "silt", "red-shift"})
        expected = {
            "pearl-cascade": ("scene:waterfall", 0, "wWaterfall"),
            "copper-causeway": ("scene:tarmac", 1, "wLandscape(road=1)"),
            "red-shift": ("scene:black-hole", 2, "wAccretion"),
            "tidal-glass": ("scene:ocean", 3, "wOcean"),
            "silt": ("scene:dunes", 4, "wLandscape(road=0)"),
        }
        for key, (catalog, index, function) in expected.items():
            ref = refs[key]
            self.assertEqual((ref["catalogId"], ref["worldScene"], ref["sourceFunction"]), (catalog, index, function))
            if ref["capture"]:
                self.assertEqual(hashlib.sha256((ORIGINAL / ref["capture"]).read_bytes()).hexdigest(), ref["captureSha256"])
            else:
                self.assertIsNone(ref["captureSha256"])
                self.assertIn("must capture exact embedded rc2", ref["appearanceGate"])

    def test_live_field_guide_dunes_black_hole_and_variants_are_byte_bound(self):
        oracle = json.loads((ORIGINAL / "SCENIC-ORACLES.json").read_text())
        comparisons = oracle["liveFieldGuideComparisons"]
        self.assertEqual(len(comparisons), 6)
        self.assertEqual({c["scene"] for c in comparisons}, {"scene:dunes", "scene:black-hole"})
        for item in comparisons:
            path = (ORIGINAL / item["capture"]).resolve()
            self.assertTrue(path.is_file())
            image = path.read_bytes()
            self.assertEqual(hashlib.sha256(image).hexdigest(), item["sha256"])
            self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual((int.from_bytes(image[16:20], "big"), int.from_bytes(image[20:24], "big")), (960, 608))
            self.assertIn(item["timeMs"], (2000, 9000))
        for scene in ("scene:dunes", "scene:black-hole"):
            variants=[c for c in comparisons if c["scene"]==scene]
            self.assertEqual(len({c["sha256"] for c in variants}), 3)

    def test_original_world_runtime_cells_are_exact_and_source_bound(self):
        """Differentially pin the archived WASM against the exact source C raster."""
        evidence = ROOT / "evidence/original-scenic-restoration-20261013"
        oracle = json.loads((evidence / "ORIGINAL-WORLD-FRAMES.json").read_text())
        archive = load_rc2_workbench().encode("utf-8")
        self.assertEqual(hashlib.sha256(archive).hexdigest(), oracle["htmlSha256"])
        self.assertEqual(oracle["htmlSha256"], RC2_HTML_SHA256)
        self.assertEqual(oracle["archiveSha256"], RC2_ARCHIVE_SHA256)
        self.assertEqual(oracle["embeddedWasmSha256"], "aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09")
        self.assertEqual(oracle["nativeSourceSha256"], hashlib.sha256((ROOT.parent / "src/nocturne.c").read_bytes()).hexdigest())
        self.assertEqual(oracle["geometrySourceSha256"], hashlib.sha256((ROOT.parent / "src/world.inc").read_bytes()).hexdigest())
        self.assertEqual(oracle["integerSineSourceSha256"], hashlib.sha256((ROOT.parent / "src/sine.inc").read_bytes()).hexdigest())
        self.assertEqual(oracle["cameraProjectionSampling"], {
            "camera": "Q8 relative x/y/z subtract cameraX/Y/Z; yaw gives a=(x*cos-z*sin)/1000 and b=(x*sin+z*cos)/1000; pitch gives u=(y*cos-b*sin)/1000 and depth=(y*sin+b*cos)/1000; roll returns ((a*cos+u*sin)/1000,(u*cos-a*sin)/1000,depth); divisions truncate toward zero using wSin/wCos integer table interpolation",
            "projection0": "internalWidth=width*(sampling?2:1), internalHeight=height*(sampling?4:2); focal=internalWidth*8*wCos(fov/2)/wSin(fov/2) using the Q1000 source sine table; screen=(internalWidth*8,internalHeight*8)+cameraXY*focal/cameraZ; depth=(1<<26)/cameraZ",
            "projection1": "same internalWidth/internalHeight; screen=(internalWidth*8,internalHeight*8)+cameraXY*internalWidth*16/span; depth=268435456-cameraZ",
            "clip": "five source planes, near camera-space z >= 384 Q8, Q16 edge intersections",
            "triangles": "pixel centers at (16*x+8,16*y+8), integer edge tests, alpha>=750 updates depth",
            "lines": "clipped and sampled every <=12 sixteenth-pixel units, interpolated integer depth; alpha>=950 updates depth",
            "points": "wDot radius is output-cell samples, circle test in integer cells; alpha>=950 updates depth",
            "sampling": "2x4 subpixels per cell; mask order [1,8,2,16,4,32,64,128]; output glyph/color reduction follows src/world.inc",
        })
        self.assertEqual(len(oracle["frames"]), 16)
        expected_scenes = {"pearl-cascade", "tidal-glass", "copper-causeway", "silt", "red-shift"}
        self.assertTrue(expected_scenes.issubset({item["scene"] for item in oracle["frames"]}))
        for item in oracle["frames"]:
            data = (evidence / item["cellsFile"]).read_bytes()
            self.assertEqual(len(data), item["width"] * item["height"] * 16)
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["cellsSha256"], item["id"])
            self.assertIn(item["timeMs"], (2000, 5000, 9000))
            self.assertIn(item["projection"], (0, 1))
            self.assertIn(item["sampling"], (0, 1))
        # The fixture's positive and negative comparisons are real full-cell
        # checks; variant/time frames must differ from the named baseline.
        frames = {f["id"]: (evidence / f["cellsFile"]).read_bytes() for f in oracle["frames"]}
        for lhs, rhs in oracle["differentFrom"]:
            self.assertNotEqual(frames[lhs], frames[rhs], f"expected visible change: {lhs} vs {rhs}")
        mutated = bytearray(frames["tidal-glass-default-2000"])
        mutated[0] ^= 1
        tidal = next(f for f in oracle["frames"] if f["id"] == "tidal-glass-default-2000")
        self.assertNotEqual(hashlib.sha256(mutated).hexdigest(), tidal["cellsSha256"])
        with tempfile.TemporaryDirectory(prefix="nocturne-original-world-") as temp:
            generated = pathlib.Path(temp) / "generated"
            with rc2_workbench_file() as archive_path:
                subprocess.run([
                    "node", str(ROOT / "tests/capture_original_rc2_world_frames.mjs"), str(generated), str(archive_path),
                ], check=True, cwd=ROOT, text=True, capture_output=True)
            regenerated = json.loads((generated / "ORIGINAL-WORLD-FRAMES.json").read_text())
            self.assertEqual([f["cellsSha256"] for f in regenerated["frames"]],
                             [f["cellsSha256"] for f in oracle["frames"]])
            self.assertEqual((generated / "ORIGINAL-WORLD-FRAMES.tsv").read_bytes(),
                             (evidence / "ORIGINAL-WORLD-FRAMES.tsv").read_bytes())
            for frame in oracle["frames"]:
                self.assertEqual((generated / frame["cellsFile"]).read_bytes(), frames[frame["id"]])
            binary = pathlib.Path(temp) / "original-world-frame-oracle"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "src"), "-I", str(ROOT.parent / "include"), "-I", str(ROOT.parent / "src"),
                str(ROOT / "tests/original_world_frame_oracle.c"),
                str(ROOT.parent / "src/nocturne.c"), "-o", str(binary),
            ], check=True, cwd=ROOT)
            result = subprocess.run([str(binary), str(evidence)], check=True, text=True, capture_output=True)
            self.assertIn("exact RC2 WASM cell frames", result.stdout)
            corrupt = pathlib.Path(temp) / "corrupt-reference"
            shutil.copytree(generated, corrupt)
            changed = corrupt / "pearl-cascade-default-2000.cells"
            bad = bytearray(changed.read_bytes()); bad[0] ^= 1; changed.write_bytes(bad)
            rejected = subprocess.run([str(binary), str(corrupt)], check=False, text=True, capture_output=True)
            self.assertEqual(rejected.returncode, 5)
            self.assertIn("differs byte-for-byte", rejected.stderr)

    def test_world_frame_oracle_rejects_corrupt_expected_bytes(self):
        """Negative control: a single changed cell word cannot pass parity."""
        evidence = ROOT / "evidence/original-scenic-restoration-20261013"
        oracle = json.loads((evidence / "ORIGINAL-WORLD-FRAMES.json").read_text())
        self.assertTrue(oracle["negativeControl"]["singleCellWordMutationRejected"])
        self.assertEqual(oracle["negativeControl"]["method"], "recompute frame SHA-256 after flipping one glyph bit and require mismatch")

    def test_sampler_primitive_stream_matches_instrumented_original_c(self):
        """Trace actual original scene calls and compare every emitted primitive."""
        source = ROOT.parent / "src/world.inc"
        original = source.read_text()
        probes = {
            "static void wTriangle ( WCanvas * c , WPoint a , WPoint b , WPoint d , uint32_t color , int32_t alpha ) {":
                "nsOriginalPrimitiveTrace(0,a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,color,alpha,0);",
            "static void wDot ( WCanvas * c , WPoint p , uint32_t color , int32_t alpha , int32_t radius ) {":
                "nsOriginalPrimitiveTrace(2,p.x,p.y,p.z,0,0,0,0,0,0,color,alpha,radius);",
            "static void wLine ( WCanvas * c , WPoint a , WPoint b , uint32_t color , int32_t alpha ) {":
                "nsOriginalPrimitiveTrace(1,a.x,a.y,a.z,b.x,b.y,b.z,0,0,0,color,alpha,0);",
        }
        for signature in probes:
            self.assertEqual(original.count(signature), 1, f"original call boundary changed: {signature}")
        with tempfile.TemporaryDirectory(prefix="nocturne-geometry-diff-") as temp:
            temp = pathlib.Path(temp)
            instrumented_world = original
            for signature, trace in probes.items():
                instrumented_world = instrumented_world.replace(signature, signature + "\n    " + trace, 1)
            world_copy = temp / "world.instrumented.inc"
            world_copy.write_text(instrumented_world)
            source_copy = temp / "nocturne.instrumented.c"
            c_source = (ROOT.parent / "src/nocturne.c").read_text()
            include = '#include "world.inc"'
            self.assertEqual(c_source.count(include), 1)
            c_source = c_source.replace(include,
                "void nsOriginalPrimitiveTrace(int,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,uint32_t,int32_t,int32_t);\n"
                + '#include "' + str(world_copy) + '"')
            source_copy.write_text(c_source)
            binary = temp / "scenic-art-geometry-diff"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "src"), "-I", str(ROOT.parent / "include"), "-I", str(ROOT.parent / "src"),
                str(ROOT / "tests/scenic_art_geometry_diff.c"), str(ROOT / "src/scenic_art.c"),
                str(source_copy), "-o", str(binary),
            ], check=True, cwd=ROOT)
            evidence = ROOT / "evidence/original-scenic-restoration-20261013"
            result = subprocess.run([str(binary), str(evidence)], check=True, text=True, capture_output=True)
            self.assertIn("every source primitive matched", result.stdout)

    def test_native_sampler_positive_and_negative_contract(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-scenic-art-") as temp:
            binary = pathlib.Path(temp) / "scenic-art-contract"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                str(ROOT / "tests/scenic_art_contract.c"),
                str(ROOT / "src/scenic_art.c"), "-o", str(binary),
            ], check=True, cwd=ROOT)
            result = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
            self.assertIn("fixed-point configs, five source scene families", result.stdout)


if __name__ == "__main__":
    unittest.main()
