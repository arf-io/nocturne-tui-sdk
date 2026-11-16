"""Shared renderer: original subpixel geometry with RC2 dot encoding; exact half frames."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C
import struct
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/original-scenic-restoration-20261013"
sys.path.insert(0, str(ROOT / "scripts"))
from toolchain import discover
from native.tests.original_scenic_samples import OriginalScenicSamples

SOURCES = ["render.c", "sampling.c", "source_compositor.c", "scenic_native_raster.c",
           "scenic_source_raster.c", "scenic_native.c", "scenic_art.c", "math.c",
           "blend.c", "color_spaces.c", "material_pattern.c", "source_material_sampler.c", "character_selectors.c", "motion.c", "camera_original.c", "camera_controls.c", "commands.c"]
SOURCES += [p.name for p in sorted((ROOT / "src").glob("original_math_*.c"))]


def assert_cells(test, actual, expected, label):
    test.assertEqual(len(actual), len(expected), label)
    for at in range(0, len(expected), 16):
        test.assertEqual(actual[at:at+16], expected[at:at+16],
                         f"{label}, first differing cell {at//16}: "
                         f"actual={actual[at:at+16].hex()} expected={expected[at:at+16].hex()}")


class ScenicCompositor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="scenic-shared-compositor-")
        cls.out = pathlib.Path(cls.temp.name)
        cls.binary = cls.out / "contract"
        command = ["cc", "-std=c11", "-O2", "-ffunction-sections", "-fdata-sections",
                   "-ffp-contract=off", "-I", str(ROOT / "src"), "-I", str(ROOT / "include"),
                   str(ROOT / "tests/scenic_compositor_contract.c")]
        command += [str(ROOT / "src" / source) for source in SOURCES]
        command += ["-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections",
                    "-lm", "-o", str(cls.binary)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(error.stderr) from error

        cls.original = OriginalScenicSamples(cls.out)
        cls.reference = cls.out / "current-encoding-reference"
        cls.reference.mkdir()
        manifest = json.loads((EVIDENCE / "ORIGINAL-WORLD-FRAMES.json").read_text())
        (cls.reference / "ORIGINAL-WORLD-FRAMES.json").write_text(json.dumps(manifest))
        for frame in manifest["frames"]:
            archived = (EVIDENCE/frame["cellsFile"]).read_bytes()
            (cls.reference/frame["cellsFile"]).write_bytes(cls.original.expected(frame, archived))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_order_thresholds_mixed_depth_half_samples_and_unchanged_explicit_braille(self):
        result = subprocess.run([str(self.binary)], check=True, capture_output=True, text=True)
        self.assertIn("source order, thresholds, mixed depth", result.stdout)

    def test_all_sixteen_original_sample_frames_match_corrected_braille_and_exact_half(self):
        subprocess.run([str(self.binary), str(EVIDENCE / "ORIGINAL-WORLD-FRAMES.tsv"), str(self.out)],
                       check=True, capture_output=True, text=True)
        manifest = json.loads((EVIDENCE / "ORIGINAL-WORLD-FRAMES.json").read_text())
        self.assertEqual(len(manifest["frames"]), 16)
        for frame in manifest["frames"]:
            with self.subTest(frame=frame["id"]):
                expected = (self.reference / frame["cellsFile"]).read_bytes()
                actual = (self.out / frame["cellsFile"]).read_bytes()
                assert_cells(self, actual, expected, frame["id"])

    def test_one_changed_original_cell_is_rejected(self):
        manifest = json.loads((EVIDENCE / "ORIGINAL-WORLD-FRAMES.json").read_text())
        original = (EVIDENCE / manifest["frames"][0]["cellsFile"]).read_bytes()
        altered = bytearray(original)
        altered[16*12+4] ^= 1
        with self.assertRaisesRegex(AssertionError, "first differing cell 12"):
            assert_cells(self, bytes(altered), original, "corrupt reference")

    def test_shared_renderer_wasm_matches_original_geometry_corrected_encoding_without_imports(self):
        tools = discover()
        objects = []
        sources = [ROOT / "src" / source for source in SOURCES]
        sources += [ROOT / "src/wasm_mem.c", ROOT / "tests/scenic_compositor_wasm.c"]
        for source in sources:
            obj = self.out / (source.stem + ".o")
            subprocess.run([tools["wasmCC"], "--target=wasm32", "-std=c11", "-O2",
                            "-ffunction-sections", "-fdata-sections", "-ffp-contract=off",
                            "-fno-fast-math", "-nostdlib", "-ffreestanding", "-fno-builtin",
                            "-Iinclude", "-Isrc", "-Ifreestanding", "-c", str(source), "-o", str(obj)],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            objects.append(str(obj))
        wasm = self.out / "shared-scenic.wasm"
        subprocess.run([tools["wasmLD"], "--no-entry", "--export-memory", "--export=scenic_config",
                        "--export=scenic_detail", "--export=scenic_records", "--export=scenic_render",
                        "--stack-first", "-z", "stack-size=1048576",
                        *objects, "-o", str(wasm)], check=True, capture_output=True, text=True)
        script = r'''
const fs = require('fs'), path = require('path');
const moduleBytes = fs.readFileSync(process.argv[1]);
const module = new WebAssembly.Module(moduleBytes);
if (WebAssembly.Module.imports(module).length) throw Error('unexpected imports');
const e = new WebAssembly.Instance(module, {}).exports;
const dir = process.argv[2];
const frames = JSON.parse(fs.readFileSync(path.join(dir, 'ORIGINAL-WORLD-FRAMES.json'))).frames;
for (const f of frames) {
  new Int32Array(e.memory.buffer, e.scenic_config(), 24).set(f.worldQ);
  new Int32Array(e.memory.buffer, e.scenic_detail(), 8).set(f.detailQ);
  const count = e.scenic_render(f.timeMs);
  if (count !== f.width*f.height) throw Error(`${f.id}: render ${count}`);
  const actual = Buffer.from(e.memory.buffer, e.scenic_records(), count*16);
  const expected = fs.readFileSync(path.join(dir, f.cellsFile));
  if (!actual.equals(expected)) {
    let i=0; while (i<actual.length && actual[i]===expected[i]) i++;
    throw Error(`${f.id}: cell ${Math.floor(i/16)} byte ${i%16}`);
  }
}
console.log(`${frames.length} original WASM frames match current shared-renderer WASM`);
'''
        result = subprocess.run([shutil.which("node"), "-e", script, str(wasm), str(self.reference)],
                                check=True, capture_output=True, text=True)
        self.assertIn("16 original WASM frames match", result.stdout)


if __name__ == "__main__":
    unittest.main()
