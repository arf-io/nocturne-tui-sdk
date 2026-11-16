"""Frozen schema-38 prefix migrates an empty angular append; deferred gate."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import struct,zlib,unittest
from test_hull_immersion import NativeScene
class AngularFluidMigration(unittest.TestCase):
 def schema_39(self,data):
  old=bytearray(data[:24+13325432]);struct.pack_into('<I',old,12,0x20261039);struct.pack_into('<I',old,16,13325432);struct.pack_into('<I',old,28,0x20261039);return self.repaired_checksum(old)
 def test_old_angular_schema_rejects_queued_angular_exports_across_schedules(self):
  for live in [False,True]:
   with self.subTest(live=live),NativeScene() as scene:
    scene.command(dict(op='surface',id=1));scene.command(dict(op='surface-fluid',surfaceId=1,mass=3))
    angular=dict(op='surface-fluid-angular',surfaceId=1,inertia=3)
    if live:scene.command(angular)
    else:scene.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='batch',commands=[angular])))
    scene.command(dict(op='schedule',id=2,atUs=1000000,command=dict(op='batch',commands=[dict(op='export-surface-fluid',surfaceId=1)])))
    valid=scene.snapshot()
    with self.assertRaises(ValueError):scene.restore(self.schema_39(valid))
    self.assertEqual(scene.snapshot(),valid)
 def test_old_angular_schema_preserves_translation_only_export_on_other_surface(self):
  with NativeScene() as scene:
   for surface in [1,2]:
    scene.command(dict(op='surface',id=surface));scene.command(dict(op='surface-fluid',surfaceId=surface,mass=3))
   scene.command(dict(op='surface-fluid-angular',surfaceId=1,inertia=3))
   scene.command(dict(op='schedule',id=1,atUs=1000000,command=dict(op='export-surface-fluid',surfaceId=2)))
   scene.restore(self.schema_39(scene.snapshot()))
   self.assertEqual(scene.surface_fluid_angular(1),[3,0,0,0,0,0,0,0,0,0,0,0])
 def repaired_checksum(self,data):
  struct.pack_into('<I',data,20,zlib.crc32(data[24:])&0xffffffff);return data
 def test_old_history_layout_retains_prefix_and_zeroes_angular_storage(self):
  with NativeScene() as scene:
   current=scene.snapshot();self.assertEqual(len(current),snapshot_size(scene))
   old=bytearray(current[:24+13323768]);struct.pack_into('<I',old,12,0x20261038);struct.pack_into('<I',old,16,13323768);struct.pack_into('<I',old,28,0x20261038);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
   scene.restore(old);migrated=scene.snapshot()
   self.assertEqual(struct.unpack_from('<I',migrated,12)[0],current_schema());self.assertEqual(len(migrated),snapshot_size(scene))
   self.assertEqual(migrated[24+13323768:24+13497384],bytes(13497384-13323768));self.assertEqual(migrated[32:24+13323768],old[32:])
 def test_schema_39_keeps_live_angular_record_and_zeroes_history(self):
  with NativeScene() as scene:
   for command in [dict(op='surface',id=1),dict(op='surface-fluid',surfaceId=1,mass=3),dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[1,2,3])]:scene.command(command)
   current=scene.snapshot();old=bytearray(current[:24+13325432]);struct.pack_into('<I',old,12,0x20261039);struct.pack_into('<I',old,16,13325432);struct.pack_into('<I',old,28,0x20261039);self.repaired_checksum(old)
   scene.restore(old);migrated=scene.snapshot();self.assertEqual(migrated[24+13325432:24+13327224],bytes(1792));self.assertEqual(scene.surface_fluid_angular(1),[3,1,2,3,3,6,9,0,0,0,0,21])
 def test_checksum_correct_record_and_history_corruption_rejects_atomically(self):
  with NativeScene() as scene:
   for command in [dict(op='surface',id=1),dict(op='surface-fluid',surfaceId=1,mass=3),dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[1,2,3])]:scene.command(command)
   valid=scene.snapshot();record=24+13323768
   for offset,fmt,value in [(record,'I',2),(record+4,'I',1),(record+8,'d',0),(record+40,'d',999),(record+88,'d',-1)]:
    bad=bytearray(valid);struct.pack_into('<'+fmt,bad,offset,value);self.repaired_checksum(bad)
    with self.assertRaises(ValueError):scene.restore(bad)
    self.assertEqual(scene.snapshot(),valid)
   scene.command(dict(op='export-surface-fluid',surfaceId=1));valid=scene.snapshot();history=24+13325432
   for offset,fmt,value in [(history,'d',0),(history+16,'d',999),(history+104,'Q',0)]:
    bad=bytearray(valid);struct.pack_into('<'+fmt,bad,offset,value);self.repaired_checksum(bad)
    with self.assertRaises(ValueError):scene.restore(bad)
    self.assertEqual(scene.snapshot(),valid)
 def test_pre_angular_schema_cannot_carry_new_pending_authoring(self):
  with NativeScene() as scene:
   for command in [dict(op='surface',id=1),dict(op='surface-fluid',surfaceId=1,mass=3),dict(op='schedule',id=1,atUs=1000000,command=dict(op='surface-fluid-angular',surfaceId=1,inertia=3))]:scene.command(command)
   valid=scene.snapshot();old=bytearray(valid[:24+13323768]);struct.pack_into('<I',old,12,0x20261038);struct.pack_into('<I',old,16,13323768);struct.pack_into('<I',old,28,0x20261038);self.repaired_checksum(old)
   with self.assertRaises(ValueError):scene.restore(old)
   self.assertEqual(scene.snapshot(),valid)
