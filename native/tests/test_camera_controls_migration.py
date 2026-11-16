"""Actual published epoch93 migrates without losing any variable payload."""
import gzip, struct, sys, unittest, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from current_writer_contract import current_schema
class CameraControlsMigration(unittest.TestCase):
 def test_genuine93_keeps_document_modal_model_and_frame(self):
  fix=ROOT/'tests/fixtures/original-modal-schema93'
  raw=gzip.decompress((fix/'snapshot.gz').read_bytes())
  self.assertEqual(struct.unpack_from('<I',raw,12)[0],0x20261093)
  with NativeScene() as a, NativeScene() as b:
   a.restore(raw);info=a.info_complete()
   self.assertFalse(info['camera']['controls']['enabled'])
   self.assertEqual(a.render().bytes,gzip.decompress((fix/'frame.gz').read_bytes()))
   self.assertEqual(len(info['sourceModal']['query']),80000)
   self.assertEqual(info['sourceModel']['triangles'],4608)
   self.assertGreater(len(info['prompt']['text']),65536)
   saved=a.snapshot();self.assertEqual(struct.unpack_from('<I',saved,12)[0],current_schema())
   b.restore(saved);self.assertEqual(b.snapshot(),saved)
   self.assertEqual(b.info_complete(),info)
 def test_invalid_footer_rejected_atomically(self):
  with NativeScene() as s:
   s.command({'op':'camera-controls','rig':'spacecraft'})
   saved=s.snapshot();bad=bytearray(saved)
   struct.pack_into('<I',bad,24+30499432+4,6)
   struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(saved,s.snapshot())
if __name__=='__main__':unittest.main()
