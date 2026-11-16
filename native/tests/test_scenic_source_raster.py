"""Source raster callback traces against the instrumented original C renderer."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from toolchain import discover  # noqa: E402


class ScenicSourceRasterDifferential(unittest.TestCase):
    def test_ordered_coverage_matches_original_c_and_mutation_is_rejected(self):
        original_path = ROOT.parent / "src/world.inc"
        source = original_path.read_text()
        probes = {
            "int32_t z = ( int32_t ) ( ( e0 * ip + e1 * iq + e2 * ir ) / area ) ;\n        uint32_t i = ( uint32_t ) y * c -> width + x ;":
                "int32_t z = ( int32_t ) ( ( e0 * ip + e1 * iq + e2 * ir ) / area ) ;\n        nsOriginalRasterCoverage(x,y,z,color,alpha,750);\n        uint32_t i = ( uint32_t ) y * c -> width + x ;",
            "if ( radius && ( ( x - cx ) * ( x - cx ) + ( y - cy ) * ( y - cy ) > radius * radius ) ) continue ;\n        uint32_t i = ( uint32_t ) y * c -> width + x ;":
                "if ( radius && ( ( x - cx ) * ( x - cx ) + ( y - cy ) * ( y - cy ) > radius * radius ) ) continue ;\n        nsOriginalRasterCoverage(x,y,iz,color,alpha,950);\n        uint32_t i = ( uint32_t ) y * c -> width + x ;",
            "int32_t iz = ( int32_t ) ( ( ( int64_t ) wDepth ( c , u . z ) * ( n - k ) + ( int64_t ) wDepth ( c , v . z ) * k ) / n ) ;\n        uint32_t i = ( uint32_t ) y * c -> width + x ;":
                "int32_t iz = ( int32_t ) ( ( ( int64_t ) wDepth ( c , u . z ) * ( n - k ) + ( int64_t ) wDepth ( c , v . z ) * k ) / n ) ;\n        nsOriginalRasterCoverage(x,y,iz,color,alpha,950);\n        uint32_t i = ( uint32_t ) y * c -> width + x ;",
        }
        for needle in probes:
            self.assertEqual(source.count(needle), 1, f"source raster trace seam changed: {needle}")
        instrumented_world = source
        for needle, replacement in probes.items():
            instrumented_world = instrumented_world.replace(needle, replacement, 1)
        with tempfile.TemporaryDirectory(prefix="nocturne-scenic-raster-") as temporary:
            temp = pathlib.Path(temporary)
            world = temp / "world.instrumented.inc"
            world.write_text(instrumented_world)
            c_source = ROOT.parent / "src/nocturne.c"
            source_text = c_source.read_text()
            include = '#include "world.inc"'
            self.assertEqual(source_text.count(include), 1)
            instrumented_source = temp / "nocturne.instrumented.c"
            instrumented_source.write_text(
                "#include <stdint.h>\n"
                "#include <string.h>\n"
                "void nsOriginalRasterCoverage(int32_t,int32_t,int32_t,uint32_t,int32_t,int32_t);\n"
                + source_text.replace(include, '#include "' + str(world) + '"', 1)
                + r'''
int nsOriginalProjectWitness(const int32_t *values,int32_t outputWidth,int32_t outputHeight,
    int32_t x,int32_t y,int32_t z,int32_t *cx,int32_t *cy,int32_t *cz,
    int32_t *sx,int32_t *sy,int32_t *depth) {
    NsWorldConfig config;memcpy(config.v,values,sizeof(config.v));
    WCanvas c;c.config=&config;c.detail=0;
    c.width=outputWidth*(values[NSW_SAMPLING]?2:1);
    c.height=outputHeight*(values[NSW_SAMPLING]?4:2);
    c.sy=wSin(values[NSW_YAW]);c.cy=wCos(values[NSW_YAW]);
    c.sp=wSin(values[NSW_PITCH]);c.cp=wCos(values[NSW_PITCH]);
    c.sr=wSin(values[NSW_ROLL]);c.cr=wCos(values[NSW_ROLL]);
    c.focal=c.width*8*wCos(values[NSW_FOV]/2)/wSin(values[NSW_FOV]/2);
    WPoint p=wCamera(&c,wP(x,y,z));if(p.z<384)return 0;
    WScreen q=wProject(&c,p);*cx=p.x;*cy=p.y;*cz=p.z;
    *sx=q.x;*sy=q.y;*depth=wDepth(&c,p.z);return 1;
}
'''
            )
            binary = temp / "scenic-source-raster-diff"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "src"), "-I", str(ROOT.parent / "include"),
                "-I", str(ROOT.parent / "src"),
                str(ROOT / "tests/scenic_source_raster_diff.c"),
                str(ROOT / "src/scenic_art.c"), str(ROOT / "src/scenic_source_raster.c"),
                str(instrumented_source), "-o", str(binary),
            ], check=True, cwd=ROOT)
            evidence = ROOT / "evidence/original-scenic-restoration-20261013"
            positive = subprocess.run([str(binary), str(evidence)], check=True,
                                      text=True, capture_output=True)
            self.assertIn("ordered original-C coverage traces matched", positive.stdout)
            negative = subprocess.run([str(binary), str(evidence), "--mutate"],
                                      check=False, text=True, capture_output=True)
            self.assertEqual(negative.returncode, 5)
            self.assertIn("coverage trace mismatch", negative.stderr)

    def test_freestanding_wasm_links_with_no_imports_and_runs_source_projection(self):
        tools = discover()
        clang, wasm_ld = tools["wasmCC"], tools["wasmLD"]
        node = shutil.which("node")
        self.assertTrue(clang, "project WASM clang must be discoverable")
        self.assertTrue(wasm_ld, "project wasm-ld must be discoverable")
        self.assertTrue(node, "Node is required to execute the standalone WASM probe")
        with tempfile.TemporaryDirectory(prefix="scenic-source-raster-wasm-") as temporary:
            temp = pathlib.Path(temporary)
            sources = [ROOT / "src/scenic_art.c", ROOT / "src/scenic_source_raster.c",
                       ROOT / "tests/scenic_source_raster_freestanding_probe.c"]
            objects = []
            for source in sources:
                obj = temp / (source.stem + ".o")
                subprocess.run([clang, "--target=wasm32", "-std=c11", "-O2",
                    "-ffp-contract=off", "-fno-fast-math", "-fno-strict-aliasing",
                    "-Wall", "-Wextra", "-Werror", "-nostdlib", "-ffreestanding",
                    "-fno-builtin", "-Ifreestanding", "-Iinclude", "-Isrc",
                    "-Inative/src", "-c", str(source), "-o", str(obj)],
                    cwd=ROOT.parent, check=True, capture_output=True, text=True)
                objects.append(str(obj))
            wasm = temp / "scenic-source-raster-probe.wasm"
            subprocess.run([wasm_ld, "--no-entry", "--export=scenic_source_raster_freestanding_probe",
                "--stack-first", "-z", "stack-size=1048576", "--initial-memory=16777216",
                *objects, "-o", str(wasm)], cwd=ROOT.parent, check=True,
                capture_output=True, text=True)
            script = ("const fs=require('fs');WebAssembly.instantiate(fs.readFileSync(process.argv[1]),{}).then(({instance})=>{"
                      "const r=instance.exports.scenic_source_raster_freestanding_probe();if(r!==0)process.exitCode=r;"
                      "}).catch(e=>{console.error(e);process.exitCode=1;});")
            subprocess.run([node, "-e", script, str(wasm)], check=True,
                           capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
