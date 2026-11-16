import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
import hashlib

ROOT=Path(__file__).resolve().parents[2]

class CompositionValidationCli(unittest.TestCase):
    def execute(self,document,*arguments):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'composition.json';path.write_text(document)
            return subprocess.run(['node',str(ROOT/'native/scripts/validate_composition.mjs'),str(path),*arguments],
                                  capture_output=True,text=True,timeout=30,cwd=ROOT)
    def testRealWasmValidationIsReproducibleAndIdentified(self):
        doc=json.dumps({'schema':'nocturne.composition.v1','seed':19,'commands':[{'op':'input','text':'Agent draft'}]})
        a=self.execute(doc);b=self.execute(doc)
        self.assertEqual(a.returncode,0,a.stderr);self.assertEqual(b.returncode,0,b.stderr)
        first=json.loads(a.stdout);second=json.loads(b.stdout)
        self.assertTrue(first['passed']);self.assertEqual(first['abiVersion'],1)
        self.assertEqual(first['snapshotSchema'],hex(current_schema()))
        self.assertEqual(first['snapshotSha256'],second['snapshotSha256'])
        self.assertEqual(first['frameSha256'],second['frameSha256'])
        self.assertEqual(len(first['wasmSha256']),64)
    def testMalformedAndNativeRejectedDocumentsFail(self):
        for text in ('not json','{}',json.dumps({'schema':'nocturne.composition.v1','seed':19,'commands':[{'op':'unknown-agent-command'}]})):
            with self.subTest(text=text):
                result=self.execute(text);self.assertNotEqual(result.returncode,0)
                self.assertFalse(json.loads(result.stdout)['passed'])
    def testExplicitMissingRuntimeDoesNotFallback(self):
        result=self.execute(json.dumps({'schema':'nocturne.composition.v1','seed':19,'commands':[]}),
                            '--wasm',str(ROOT/'native/dist/missing-agent-runtime.wasm'))
        self.assertNotEqual(result.returncode,0);self.assertFalse(json.loads(result.stdout)['passed'])
    def testExplicitPreviewClockAndInvalidClock(self):
        doc=json.dumps({'schema':'nocturne.composition.v1','seed':19,'commands':[]})
        valid=self.execute(doc,'--time-us','400000')
        self.assertEqual(valid.returncode,0,valid.stderr)
        self.assertEqual(json.loads(valid.stdout)['timeUs'],400000)
        baseline=self.execute(doc)
        self.assertNotEqual(json.loads(valid.stdout)['snapshotSha256'],json.loads(baseline.stdout)['snapshotSha256'])
        for value in ('-1','not-a-number','1.5'):
            with self.subTest(value=value):
                invalid=self.execute(doc,'--time-us',value)
                self.assertNotEqual(invalid.returncode,0);self.assertFalse(json.loads(invalid.stdout)['passed'])
    def testOwnedExportFilesHaveExactSourceAndVerifiedHashes(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'screen'
            doc=json.dumps({'schema':'nocturne.composition.v1','seed':19,'commands':[{'op':'input','text':'Exported source'}]},indent=2)
            result=self.execute(doc,'--output',str(output));self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            manifest=json.loads((output/'MANIFEST.json').read_text())
            self.assertEqual((output/'composition.json').read_text(),doc)
            self.assertEqual(set(manifest['files']),{'composition.json','scene.cells','scene.snapshot','scene-info.json'})
            for name,record in manifest['files'].items():
                data=(output/name).read_bytes();self.assertEqual(len(data),record['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),record['sha256'])
            info=json.loads((output/'scene-info.json').read_text());self.assertEqual(info['prompt']['text'],'Exported source')
            self.assertEqual(manifest['wasmSha256'],json.loads(result.stdout)['wasmSha256'])
            script="""import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {NativeScene} from 'BINDING';
const scene=await NativeScene.create(readFileSync(process.argv[1]),0);
try {scene.restore(readFileSync(process.argv[2]));assert.deepEqual(scene.render().bytes,new Uint8Array(readFileSync(process.argv[3])));}
finally {scene.close();}""".replace('BINDING',(ROOT/'native/bindings/typescript/native_scene.mjs').as_uri())
            restored=subprocess.run(['node','--input-type=module','-e',script,str(ROOT/'native/dist/nocturne_native.wasm'),
                str(output/'scene.snapshot'),str(output/'scene.cells')],capture_output=True,text=True,timeout=30)
            self.assertEqual(restored.returncode,0,restored.stderr)
            again=self.execute(doc,'--output',str(output));self.assertNotEqual(again.returncode,0)
            self.assertEqual((output/'composition.json').read_text(),doc)
    def testNativeRejectedCompositionDoesNotCreateExport(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'screen';doc=json.dumps({'schema':'nocturne.composition.v1','seed':19,'commands':[{'op':'unknown-export-command'}]})
            result=self.execute(doc,'--output',str(output));self.assertNotEqual(result.returncode,0);self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
