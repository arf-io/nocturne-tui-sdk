"""A Workshop project, exported, runs in every target language and draws the same frame.

The Gallery Workshop exports a project as executable programs (native/bindings/typescript/composition_codegen.mjs):
panel-node.mjs on the WASM build, panel.py on the Python binding, main.go on the Go binding, src/main.rs on the Rust
binding, and panel.ts as the typed browser entry. This test exports each of the three ready-made projects exactly as
the Workshop's Export button does, places the directory beside native/ as its README instructs, runs every program at
an explicit clock, and requires the cell frames (glyph, foreground, background, owner words) to be byte-identical.
The TypeScript entry is type-checked in strict mode with the SDK's compiler. Real toolchains only: a missing
toolchain fails the test rather than skipping it, unless NOCTURNE_EXPORT_LANGUAGES names a subset explicitly.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
TIME_US = 1_200_000
LANGUAGES = [x for x in os.environ.get('NOCTURNE_EXPORT_LANGUAGES', 'wasm,python,go,rust,typescript').split(',') if x]
PRESETS = ('signal-desk', 'flight-deck', 'tidal-console')

EXPORT = r"""
import {writeFile,mkdir} from 'node:fs/promises';
import {dirname,join} from 'node:path';
import {createPreset} from '%(ts)s/composition_presets.mjs';
import {generateProjectFiles} from '%(ts)s/composition_codegen.mjs';
const [preset,out]=process.argv.slice(2);
const files=generateProjectFiles(createPreset(preset));
for(const [name,value] of Object.entries(files)){const path=join(out,name);await mkdir(dirname(path),{recursive:true});await writeFile(path,value);}
console.log(Object.keys(files).sort().join(','));
"""


def run(args, cwd, env=None, timeout=900):
    result = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise AssertionError(f"{' '.join(map(str, args))} failed in {cwd}:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
    return result.stdout


class ProjectExportLanguages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for need in ('dist/nocturne_native.wasm',):
            if not (NATIVE / need).is_file():
                raise unittest.SkipTest(f'build the SDK first (sh build-native.sh): missing native/{need}')
        cls.root = Path(tempfile.mkdtemp(prefix='.export-languages-', dir=REPOSITORY))
        cls.script = cls.root / 'export.mjs'
        cls.script.write_text(EXPORT % {'ts': (NATIVE / 'bindings/typescript').as_uri()})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def export(self, preset):
        # The generated programs resolve the SDK as ../native, so the project directory sits beside native/.
        out = REPOSITORY / f'.export-{preset}-{os.getpid()}'
        shutil.rmtree(out, ignore_errors=True)
        self.addCleanup(shutil.rmtree, out, True)
        names = run(['node', str(self.script), preset, str(out)], REPOSITORY).strip().split(',')
        for required in ('panel-node.mjs', 'panel.py', 'main.go', 'src/main.rs', 'panel.ts', 'project.json', 'README.md'):
            self.assertIn(required, names)
        return out

    def frame(self, out, language):
        target = out / 'panel.cells'
        target.unlink(missing_ok=True)
        when = f'--time={TIME_US}'
        if language == 'wasm':
            run(['node', 'panel-node.mjs', when], out)
        elif language == 'python':
            run([os.environ.get('PYTHON', shutil.which('python3')), 'panel.py', when], out)
        elif language == 'go':
            run(['go', 'run', '.', when], out, env={'GOFLAGS': '-mod=mod', 'GOWORK': 'off'})
        elif language == 'rust':
            env = {'CARGO_TARGET_DIR': str(self.root / 'cargo-target')}
            if os.environ.get('NOCTURNE_COVERAGE') == '1':
                # Qualification links the measured shared core (bindings/rust/build.rs); its rpath link argument does
                # not reach a dependent program, so the loader is pointed at native/dist. SDK users link the archive.
                dist = str(NATIVE / 'dist')
                env.update(DYLD_FALLBACK_LIBRARY_PATH=dist, LD_LIBRARY_PATH=dist)
            run(['cargo', 'run', '--quiet', '--offline', '--', when], out, env=env)
        else:
            raise ValueError(language)
        data = target.read_bytes()
        self.assertGreater(len(data), 0)
        self.assertEqual(len(data) % 16, 0)
        return data

    def test_every_language_draws_the_same_frame(self):
        for preset in PRESETS:
            with self.subTest(preset=preset):
                out = self.export(preset)
                frames = {lang: self.frame(out, lang) for lang in LANGUAGES if lang != 'typescript'}
                reference = frames.get('wasm') or next(iter(frames.values()))
                words = len(reference) // 16
                glyphs = {int.from_bytes(reference[i:i + 4], 'little') for i in range(0, len(reference), 16)}
                self.assertGreater(len(glyphs - {0, 32}), 3, f'{preset}: the exported frame is nearly blank')
                for lang, data in frames.items():
                    self.assertEqual(data, reference, f'{preset}: {lang} frame differs from the WASM frame ({words} cells)')

    @unittest.skipUnless('typescript' in LANGUAGES, 'TypeScript not requested')
    def test_typescript_entry_type_checks(self):
        tsc = shutil.which('tsc') or str(REPOSITORY / 'node_modules/.bin/tsc')
        out = self.export('signal-desk')
        (out / 'tsconfig.json').write_text(json.dumps({'compilerOptions': {
            'strict': True, 'noEmit': True, 'target': 'es2022', 'module': 'es2022', 'moduleResolution': 'bundler',
            'allowJs': True, 'checkJs': False, 'skipLibCheck': True, 'lib': ['es2022', 'dom']}, 'files': ['panel.ts']}))
        run([tsc, '-p', 'tsconfig.json'], out)


if __name__ == '__main__':
    unittest.main()
