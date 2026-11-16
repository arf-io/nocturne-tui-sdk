"""Small freestanding compile/link/run probe for the source prompt painter."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from toolchain import discover  # noqa: E402


class PromptSourceFreestandingWasm(unittest.TestCase):
    def test_prompt_source_and_shared_color_math_link_and_run_without_libm(self):
        tools = discover()
        clang = tools["wasmCC"]
        wasm_ld = tools["wasmLD"]
        node = shutil.which("node")
        self.assertTrue(clang, "project WASM clang must be discoverable")
        self.assertTrue(wasm_ld, "project wasm-ld must be discoverable")
        self.assertTrue(node, "Node is required to execute the standalone WASM probe")
        with tempfile.TemporaryDirectory(prefix="prompt-source-wasm-") as directory:
            out = Path(directory)
            sources = [ROOT / "src/prompt_source.c", ROOT / "src/math.c",
                       ROOT / "src/wasm_mem.c", ROOT / "tests/prompt_source_freestanding_probe.c"]
            objects = []
            for source in sources:
                obj = out / (source.stem + ".o")
                subprocess.run([clang, "--target=wasm32", "-std=c11", "-O2",
                    "-ffp-contract=off", "-fno-fast-math", "-fno-strict-aliasing",
                    "-Wall", "-Wextra", "-Wno-misleading-indentation",
                    "-Iinclude", "-Isrc", "-nostdlib", "-ffreestanding",
                    "-fno-builtin", "-Ifreestanding", "-c", str(source), "-o", str(obj)],
                    cwd=ROOT, check=True, capture_output=True, text=True)
                objects.append(str(obj))
            wasm = out / "prompt-source-probe.wasm"
            subprocess.run([wasm_ld, "--no-entry", "--export=prompt_source_freestanding_probe",
                "--stack-first", "-z", "stack-size=1048576", "--initial-memory=16777216",
                *objects, "-o", str(wasm)], cwd=ROOT, check=True, capture_output=True, text=True)
            script = "const fs=require('fs');WebAssembly.instantiate(fs.readFileSync(process.argv[1]),{}).then(({instance})=>{const n=instance.exports.prompt_source_freestanding_probe();if(n!==0)process.exitCode=n;}).catch(e=>{console.error(e);process.exitCode=1;});"
            subprocess.run([node, "-e", script, str(wasm)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
