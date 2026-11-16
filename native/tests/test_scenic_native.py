"""Focused positive/negative tests for the private scene-art native command seam."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from toolchain import discover  # noqa: E402


class ScenicNativeContract(unittest.TestCase):
    def test_native_scene_art_command_and_effective_view_contract(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-scenic-native-") as temp:
            binary = pathlib.Path(temp) / "scenic-native-contract"
            dead_strip = ["-Wl,-dead_strip"] if sys.platform == "darwin" else ["-Wl,--gc-sections"]
            subprocess.run([
                "cc", "-std=c11", "-O2", "-fno-math-errno", "-Wall", "-Wextra", "-Werror",
                "-ffunction-sections", "-fdata-sections",
                "-I", str(ROOT / "src"), "-I", str(ROOT / "include"),
                str(ROOT / "tests/scenic_native_contract.c"),
                str(ROOT / "src/scenic_native.c"), str(ROOT / "src/scenic_art.c"),
                str(ROOT / "src/source_model.c"),
                str(ROOT / "src/scenic_source_raster.c"),
                str(ROOT / "src/json.c"), str(ROOT / "src/json_numbers.c"),
                str(ROOT / "src/math.c"), str(ROOT / "src/motion.c"),
                str(ROOT / "src/camera_original.c"), str(ROOT / "src/camera_controls.c"),
                str(ROOT / "src/commands.c"),
                *[str(p) for p in sorted((ROOT / "src").glob("original_math_*.c"))],
                *dead_strip, "-o", str(binary),
            ], check=True, cwd=ROOT)
            result = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
            self.assertIn("source defaults, JS Q rounding, canonical view", result.stdout)

    def test_shared_projection_callback_adapter_compiles_as_one_object(self):
        """Keep the new sink bridge buildable without pulling in the full SDK."""
        with tempfile.TemporaryDirectory(prefix="nocturne-scenic-raster-") as temp:
            obj = pathlib.Path(temp) / "scenic-native-raster.o"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-fno-math-errno", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "src"), "-I", str(ROOT / "include"),
                "-c", str(ROOT / "src/scenic_native_raster.c"), "-o", str(obj),
            ], check=True, cwd=ROOT)
            self.assertGreater(obj.stat().st_size, 0)

    def test_freestanding_wasm_module_links_and_node_checks_rounding_sampling_and_q8(self):
        tools = discover()
        clang, wasm_ld = tools["wasmCC"], tools["wasmLD"]
        node = shutil.which("node")
        self.assertTrue(clang, "project WASM clang must be discoverable")
        self.assertTrue(wasm_ld, "project wasm-ld must be discoverable")
        self.assertTrue(node, "Node is required for the actual WASM probe")
        with tempfile.TemporaryDirectory(prefix="scene-native-wasm-") as directory:
            out = pathlib.Path(directory)
            sources = [
                ROOT / "src/scenic_native.c", ROOT / "src/scenic_art.c",
                ROOT / "src/source_model.c",
                ROOT / "src/scenic_source_raster.c",
                ROOT / "src/json.c", ROOT / "src/json_numbers.c",
                ROOT / "src/math.c", ROOT / "src/motion.c", ROOT / "src/wasm_mem.c",
                ROOT / "tests/scenic_native_freestanding_probe.c",
            ]
            sources += [ROOT / "src/camera_original.c", ROOT / "src/camera_controls.c",
                        ROOT / "src/commands.c", *sorted((ROOT / "src").glob("original_math_*.c"))]
            objects = []
            for source in sources:
                obj = out / (source.stem + ".o")
                subprocess.run([
                    clang, "--target=wasm32", "-std=c11", "-O2",
                    "-ffp-contract=off", "-fno-fast-math", "-fno-strict-aliasing",
                    "-Wall", "-Wextra", "-Wno-misleading-indentation",
                    "-ffunction-sections", "-fdata-sections",
                    "-Iinclude", "-Isrc", "-nostdlib", "-ffreestanding",
                    "-fno-builtin", "-Ifreestanding", "-c", str(source), "-o", str(obj),
                ], cwd=ROOT, check=True, capture_output=True, text=True)
                objects.append(str(obj))
            wasm = out / "scene-native-probe.wasm"
            subprocess.run([
                wasm_ld, "--no-entry", "--export=scene_native_freestanding_probe",
                "--gc-sections",
                "--stack-first", "-z", "stack-size=1048576", "--initial-memory=33554432",
                *objects, "-o", str(wasm),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            script = (
                "const fs=require('fs');"
                "WebAssembly.instantiate(fs.readFileSync(process.argv[1]),{}).then(({instance})=>{"
                "const result=instance.exports.scene_native_freestanding_probe();"
                "if(result!==0){console.error('scene native probe failed '+result);process.exitCode=result;}})"
                ".catch(e=>{console.error(e);process.exitCode=1;});"
            )
            probe = subprocess.run([node, "-e", script, str(wasm)], check=False,
                                   capture_output=True, text=True)
            self.assertEqual(probe.returncode, 0, probe.stderr)


if __name__ == "__main__":
    unittest.main()
