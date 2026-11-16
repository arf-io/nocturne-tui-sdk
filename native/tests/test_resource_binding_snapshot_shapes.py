"""Checksum-correct snapshots reject malformed authored binding shapes."""
from pathlib import Path
import sys,unittest,struct,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ResourceBindingSnapshotShapes(unittest.TestCase):
 def test_schema31_old_pending_binding_promotes_executes_and_replays(self):
  with NativeScene(42) as s:
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'define','path':'/alpha','value':.5,'binding':{'family':'material','id':0,'field':'alpha'}}})
   good=s.snapshot();old=bytearray(good[:24+5266400])
   struct.pack_into('<I',old,28,0x20261031);struct.pack_into('<III',old,12,0x20261031,5266400,zlib.crc32(old[24:]))
   source=bytes(old);s.restore(old);self.assertEqual(bytes(old),source);promoted=s.snapshot()
   s.advance_to(500000);self.assertEqual(s.info()['values']['/alpha'],.5)
   self.assertEqual(s.info()['valueDescriptors']['/alpha']['binding'],{'family':'material','id':0,'field':'alpha'})
   final=s.snapshot();frame=s.render().bytes;s.restore(promoted);s.advance_to(500000)
   self.assertEqual(s.snapshot(),final);self.assertEqual(s.render().bytes,frame)
 def test_schema31_pending_command_cannot_introduce_new_binding_field(self):
  with NativeScene(42) as s:
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'define','path':'/future','value':.5,'binding':{'family':'material','id':0,'field':'alpha.rate'}}})
   good=s.snapshot();old=bytearray(good[:24+5266400])
   struct.pack_into('<I',old,28,0x20261031);struct.pack_into('<III',old,12,0x20261031,5266400,zlib.crc32(old[24:]))
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),good)
 def test_schema31_preserves_valid_old_bindings_without_live_targets(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/legacy-shape','value':1});good=s.snapshot();base=good.index(b'/legacy-shape\0')-16
   for family,identity,field,name in [(1,7,'alpha','material'),(2,12345,'windX','emitter'),
    (3,12345,'alpha','widget'),(4,0,'yaw','camera'),(5,12345,'alpha','window'),
    (6,12345,'material','text'),(7,12345,'alpha','area'),(8,0,'alpha','floor'),(9,12345,'active','state')]:
    old=bytearray(good[:24+5266400]);struct.pack_into('<ii',old,base+8,family,identity)
    encoded=field.encode();old[base+144:base+176]=encoded+b'\0'*(32-len(encoded))
    struct.pack_into('<I',old,28,0x20261031);struct.pack_into('<III',old,12,0x20261031,5266400,zlib.crc32(old[24:]))
    original=bytes(old);s.restore(old);self.assertEqual(bytes(old),original)
    self.assertEqual(s.info()['valueDescriptors']['/legacy-shape']['binding'],{'family':name,'id':identity,'field':field})
    promoted=s.snapshot();s.restore(promoted);self.assertEqual(s.snapshot(),promoted)
 def test_schema31_rejects_new_fields_inside_existing_families(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/legacy-shape','value':1});good=s.snapshot();base=good.index(b'/legacy-shape\0')-16
   for family,identity,field in [(1,0,'alpha.rate'),(2,1,'gravity.y'),(3,1,'border'),
    (5,1,'group'),(6,1,'width'),(7,1,'layout'),(8,0,'height')]:
    old=bytearray(good[:24+5266400]);struct.pack_into('<ii',old,base+8,family,identity)
    encoded=field.encode();old[base+144:base+176]=encoded+b'\0'*(32-len(encoded))
    struct.pack_into('<I',old,28,0x20261031);struct.pack_into('<III',old,12,0x20261031,5266400,zlib.crc32(old[24:]))
    with self.subTest(field=field),self.assertRaises(ValueError):s.restore(old)
    self.assertEqual(s.snapshot(),good)
 def test_material_and_emitter_shapes_restore_without_live_targets(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/dormant','value':1});good=s.snapshot();base=good.index(b'/dormant\0')-16
   for family,identity,field in [(1,7,'alpha'),(1,7,'channels.r.rate'),(2,12345,'wind.y'),(2,12345,'birthOrientation.z')]:
    source=bytearray(good);struct.pack_into('<ii',source,base+8,family,identity)
    encoded=field.encode();source[base+144:base+176]=encoded+b'\0'*(32-len(encoded))
    struct.pack_into('<I',source,20,zlib.crc32(source[24:]));s.restore(source)
    self.assertEqual(s.snapshot(),source)
    with self.assertRaises(ValueError):s.command({'op':'set','path':'/dormant','value':2})
    self.assertEqual(s.snapshot(),source)
 def test_accessibility_numeric_flag_corruption_rejects(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/flag','value':0,'binding':{'family':'accessibility','field':'reducedMotion'}})
   good=s.snapshot();base=good.index(b'/flag\0')-16
   for value in [-1,.5,2]:
    damaged=bytearray(good);struct.pack_into('<d',damaged,base+176,value)
    struct.pack_into('<I',damaged,20,zlib.crc32(damaged[24:]))
    with self.assertRaises(ValueError):s.restore(damaged)
    self.assertEqual(s.snapshot(),good)
 def test_unknown_fields_and_invalid_id_shapes_reject_without_committing(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/shape-fixture','value':1})
   good=s.snapshot();base=good.index(b'/shape-fixture\0')-16;frame=s.render().bytes
   for family,identity,field in [(1,9999,'alpha'),(1,0,'channels.q'),(1,0,'alpha.missing'),
    (1,0,'channels.r.rate.extra'),(2,0,'alpha'),(2,1,'missing'),(2,1,'position.w'),(2,1,'position.x.extra'),
    (3,1,'data.00'),(3,1,'data.128'),(3,0,'alpha'),(3,1,'missing'),
    (4,0,'missing'),(5,0,'alpha'),(5,1,'missing'),(6,0,'x'),(6,1,'missing'),
    (7,0,'alpha'),(7,1,'missing'),(8,1,'alpha'),(8,0,'missing'),(9,0,'active'),(9,1,'unknown'),
    (10,0,'color'),(10,1,'missing'),(11,0,'cursor'),(11,1,'missing'),(12,1,'alpha'),(12,0,'missing'),
    (13,1,'background'),(13,0,'missing'),(14,0,'x'),(14,1,'missing'),(15,1,'missing'),(16,0,'friction'),(17,1,'waves.00.phase'),
    (17,1,'waves.32.phase'),(18,0,'mass'),(19,0,'decay'),(20,1,'alpha'),
    (21,0,'sampling'),(21,65535,'alpha'),(22,0,'alpha'),(23,1,'reducedMotion'),(23,0,'unknown'),(24,0,'reducedMotion')]:
    damaged=bytearray(good);struct.pack_into('<ii',damaged,base+8,family,identity)
    encoded=field.encode();damaged[base+144:base+176]=encoded+b'\0'*(32-len(encoded))
    struct.pack_into('<I',damaged,20,zlib.crc32(damaged[24:]))
    with self.subTest(family=family,identity=identity,field=field),self.assertRaises(ValueError):s.restore(damaged)
    self.assertEqual(good,s.snapshot())
    self.assertEqual(frame,s.render().bytes)
 def test_valid_dormant_binding_restores_then_write_rejects(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1});s.command({'op':'surface-waves','surfaceId':1,'waves':[[1,0,0,0,0]]})
   s.command({'op':'define','path':'/wave','value':1,'binding':{'family':'surface-wave','id':1,'field':'waves.0.amplitude'}})
   s.command({'op':'surface-waves','surfaceId':1,'waves':[]});saved=s.snapshot()
   s.restore(saved);self.assertEqual(saved,s.snapshot())
   self.assertEqual(s.info()['valueDescriptors']['/wave']['binding'],{'family':'surface-wave','id':1,'field':'waves.0.amplitude'})
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/wave','value':2})
   self.assertEqual(saved,s.snapshot());s.command({'op':'bind','path':'/wave','binding':None})
   s.command({'op':'set','path':'/wave','value':2});self.assertEqual(s.info()['values']['/wave'],2)
 def test_schema31_cannot_carry_new_binding_family(self):
  with NativeScene(42) as s:
   s.command({'op':'flow','id':1,'flux':2,'stages':[{'name':'fall'}]})
   s.command({'op':'define','path':'/flux','value':2,'binding':{'family':'flow','id':1,'field':'flux'}})
   good=s.snapshot();old=bytearray(good[:24+5266400])
   struct.pack_into('<I',old,24+4,0x20261031);struct.pack_into('<III',old,12,0x20261031,5266400,zlib.crc32(old[24:]))
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(good,s.snapshot())
if __name__=='__main__':unittest.main()
