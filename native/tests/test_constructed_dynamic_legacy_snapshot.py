"""Actual native snapshot tests for explicitly constructed legacy layouts."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import struct,unittest,zlib
from native.tests.constructed_dynamic_legacy_snapshot import construct_dynamic_legacy_snapshot,layout
from nocturne_native import NativeScene
class ConstructedDynamicLegacy(unittest.TestCase):
 def test_actual_layout_and_each_supported_epoch_preserve_unicode_history(self):
  q=layout();self.assertEqual(q['schema45Fixed'],13478952);self.assertEqual(q['legacyFixed'],30478240);self.assertLess(q['fixed'],q['stateSize']);self.assertEqual(q['fixed'],q['legacyFixed']+q['omittedBytes'])
  with NativeScene() as s:
   s.command({'op':'draft','text':'first é界😀','emitWeather':False});s.command({'op':'draft','text':'second 👩‍🚀אב','emitWeather':False});saved=s.snapshot();frame=s.render().bytes
   for epoch in [0x20261077,0x20261078,0x20261079,0x20261081,0x20261083]:
    with self.subTest(epoch=hex(epoch)):
     old=construct_dynamic_legacy_snapshot(saved,epoch);self.assertEqual(len(old),len(saved)-q['omittedBytes']);self.assertEqual(old[24+q['legacyFixed']:],saved[24+q['fixed']:]);self.assertEqual(struct.unpack_from('<I',old,16)[0],len(old)-24);self.assertEqual(struct.unpack_from('<I',old,20)[0],zlib.crc32(old[24:]));s.restore(old);self.assertEqual(s.snapshot(),saved);self.assertEqual(s.render().bytes,frame)
 def test_every_actual_append_is_accounted_and_nonzero_bytes_rejected(self):
  q=layout();expected=['atelierWindows','atelierApplicationParticles','sourceGraphLayout','sourceSky','firstPromptSource','sourceModel','sourceStageScene','observatoryOverlay','sourceModal','cameraControls','sceneArtClock','promptAppearance','occlusionControls','promptSourceLayer']
  self.assertEqual([f['name'] for f in q['appendFields']],expected)
  cursor=q['legacyFixed']
  with NativeScene() as s:
   saved=s.snapshot()
   for field in q['appendFields']:
    self.assertEqual(field['offset'],cursor);self.assertGreater(field['bytes'],0);cursor+=field['bytes']
    bad=bytearray(saved);bad[24+field['offset']]=1;struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
    with self.subTest(field=field['name']):
     with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(bad,0x20261083)
   self.assertEqual(cursor,q['fixed'])
 def test_active_camera_controls_cannot_be_discarded_and_disabled_roundtrips(self):
  with NativeScene() as s:
   empty=s.snapshot();s.command({'op':'camera-controls','rig':'spacecraft','head':{'rotation':[0,25,0]}});active=s.snapshot()
   with self.assertRaisesRegex(ValueError,'Cannot discard active newer fixed-layout fields'):
    construct_dynamic_legacy_snapshot(active,0x20261083)
   self.assertEqual(s.snapshot(),active)
   s.command({'op':'camera-controls','enabled':False});disabled=s.snapshot();self.assertFalse(s.info()['camera']['controls']['enabled'])
   self.assertNotEqual(disabled,empty,'disabling must retain the actual composed camera view')
   old=construct_dynamic_legacy_snapshot(disabled,0x20261083);s.restore(old);self.assertEqual(s.snapshot(),disabled)
 def test_active_scenic_clock_cannot_be_discarded_and_null_roundtrips(self):
  with NativeScene() as s:
   s.command({'op':'scene-art','scene':'pearl-cascade','timeMs':1234});active=s.snapshot()
   with self.assertRaisesRegex(ValueError,'Cannot discard active newer fixed-layout fields'):
    construct_dynamic_legacy_snapshot(active,0x20261083)
   self.assertEqual(s.snapshot(),active)
   s.command({'op':'remove-scene-art'});disabled=s.snapshot();old=construct_dynamic_legacy_snapshot(disabled,0x20261083);s.restore(old);self.assertEqual(s.snapshot(),disabled)
 def test_refuses_wrong_epoch_crc_length_and_nonzero_omitted_fields(self):
  with NativeScene() as s:
   saved=s.snapshot();q=layout()
   with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(saved,0x20261073)
   bad=bytearray(saved);bad[20]^=1
   with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(bad,0x20261078)
   with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(saved[:-1],0x20261078)
   bad=bytearray(saved);bad[24+q['legacyFixed']]=1;struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(bad,0x20261078)
   bad=bytearray(saved+b'\0\0\0\0');struct.pack_into('<I',bad,16,len(bad)-24);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(bad,0x20261078)
   bad=bytearray(saved);struct.pack_into('<I',bad,12,0x20261078)
   with self.assertRaises(ValueError):construct_dynamic_legacy_snapshot(bad,0x20261078)
if __name__=='__main__':unittest.main()
