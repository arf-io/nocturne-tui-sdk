"""Genuine epoch88 camera/graph/sky fixture remains loadable after additive epochs."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import base64,gzip,hashlib,json,struct,subprocess,tempfile,unittest,zlib
from pathlib import Path
from native.bindings.python.nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'tests/fixtures/camera-graph-sky-schema88'
class CameraGraphSnapshot88(unittest.TestCase):
 def test_actual88_native_wasm_frame_and_footer_rejection(self):
  meta=json.loads((FIXTURE/'PROVENANCE.json').read_text());snapshot=gzip.decompress((FIXTURE/'snapshot.gz').read_bytes());frame=gzip.decompress((FIXTURE/'frame.gz').read_bytes());layout=json.loads((FIXTURE/'LAYOUT.json').read_text())
  self.assertTrue(meta['genuineWriter']);self.assertEqual(struct.unpack_from('<I',snapshot,12)[0],0x20261088);self.assertEqual(hashlib.sha256(snapshot).hexdigest(),meta['snapshotSha256']);self.assertEqual(hashlib.sha256(frame).hexdigest(),meta['frameSha256'])
  bad=bytearray(snapshot);struct.pack_into('<d',bad,24+layout['sourceSky']+16,float('nan'));struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
  with NativeScene(2030)as scene:
   scene.restore(snapshot);self.assertEqual(scene.render().bytes,frame);self.assertEqual(scene.info()['graph']['sourceLayout']['edgeWeights'][0]['weight'],2.5);self.assertIsNotNone(scene.info()['camera']['grabbed']);saved=scene.snapshot()
   with self.assertRaises(ValueError):scene.restore(bad)
   self.assertEqual(scene.snapshot(),saved)
  requests=[{'id':'genuine88','snapshot':base64.b64encode(snapshot).decode(),'badSnapshot':base64.b64encode(bad).decode(),'timeUs':900000}]
  with tempfile.TemporaryDirectory()as folder:
   p=Path(folder);(p/'in.json').write_text(json.dumps(requests));subprocess.run(['node',str(ROOT/'tests/spatial_contract_wasm.mjs'),str(p/'in.json'),str(p/'out.json')],check=True,capture_output=True);actual=json.loads((p/'out.json').read_text())[0]
  self.assertEqual(actual['words'],list(memoryview(frame).cast('I')));self.assertEqual(actual['info']['sourceSky']['worldSeed'],2030)
