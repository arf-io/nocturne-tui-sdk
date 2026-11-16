"""Genuine original OBJ records and source-frame contract; no synthetic art oracle."""
import ctypes as C
import json
import os
import struct
import sys
import unittest
import hashlib
import tempfile
from original_scenic_samples import OriginalScenicSamples
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
FIX=ROOT/'tests/fixtures/source-model'
LIB=Path(os.environ.get('NOCTURNE_MODEL_LIBRARY',str(ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'))))
class SourceModel(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original_temp=tempfile.TemporaryDirectory(prefix='original-model-samples-')
  cls.addClassCleanup(cls.original_temp.cleanup)
  cls.original=OriginalScenicSamples(cls.original_temp.name)
 def test_original_model_reference_rejects_tampered_fixture_and_geometry(self):
  row=json.loads((FIX/'ORACLE.json').read_text())['frames'][4]
  archived=(FIX/row['id']).read_bytes();records=(FIX/'model-records.bin').read_bytes()
  changed=bytearray(archived);changed[4]^=1
  with self.assertRaisesRegex(AssertionError,'Original source/immutable frame differs'):
   self.original.expected_model({**row,'sha256':hashlib.sha256(changed).hexdigest()},bytes(changed),records)
  changed_records=bytearray(records)
  for at in range(36,len(changed_records),40):struct.pack_into('<I',changed_records,at,0x00ff00)
  with self.assertRaisesRegex(AssertionError,'Original source/immutable frame differs'):
   self.original.expected_model(row,archived,bytes(changed_records))
 def scene(self):return NativeScene(library=LIB)
 def api(self,s):
  lib=s._lib
  for name,args,res in [('nrModelSet',[C.c_void_p,C.c_void_p,C.c_uint32],C.c_int),('nrModelCopy',[C.c_void_p,C.c_void_p,C.c_uint32],C.c_int),('nrModelTriangleCount',[C.c_void_p],C.c_uint32),('nrModelMemorySize',[C.c_void_p],C.c_uint64),('nrModelMemoryCapacity',[C.c_void_p],C.c_uint64),('nrSetModelMemory',[C.c_void_p,C.c_void_p,C.c_uint64],C.c_int)]:
   self.assertTrue(hasattr(lib,name),'Missing actual public source-model API '+name);f=getattr(lib,name);f.argtypes=args;f.restype=res
  return lib
 def upload(self,s,data):
  lib=self.api(s);buf=C.create_string_buffer(data);r=lib.nrModelSet(s._context,buf,len(data)//40)
  while r<0 and lib.nrError(s._context)==b'Model storage required':
   size=lib.nrModelMemorySize(s._context);self.assertGreater(size,lib.nrModelMemoryCapacity(s._context));memory=C.create_string_buffer(size+8);pointer=(C.addressof(memory)+7)&~7;self.assertEqual(lib.nrSetModelMemory(s._context,pointer,size),0);s._test_model_memory=memory;r=lib.nrModelSet(s._context,buf,len(data)//40)
  self.assertEqual(r,0,lib.nrError(s._context));self.assertEqual(lib.nrModelTriangleCount(s._context),len(data)//40)
 def readback(self,s):
  lib=self.api(s);count=lib.nrModelTriangleCount(s._context);buf=C.create_string_buffer(count*40);self.assertEqual(lib.nrModelCopy(s._context,buf,count),count);return bytes(buf.raw)
 def configure(self,s,q):
  s.command(dict(op='environment',presentation='canvas',stars=0,background=q[19],sampling='braille' if q[23] else 'half',style='solid'));s.command(dict(op='prompt',active=False));s.command(dict(op='floor',enabled=False,visible=False))
  s.command(dict(op='model-view',width=q[0],height=q[1],controls=dict(cameraX=q[3]/256,cameraY=q[4]/256,cameraZ=q[5]/256,yaw=q[6]/256,pitch=q[7]/256,roll=q[8]/256,fov=q[9]/256,projection=q[10],span=q[11]/256,background=q[19],sampling=q[23])))
 def test_original_4608_triangles_roundtrip_without_truncation(self):
  data=(FIX/'model-records.bin').read_bytes();self.assertEqual(len(data),4608*40)
  with self.scene() as s:
   self.upload(s,data);self.assertEqual(self.readback(s),data)
   before=s.snapshot();s.render();self.assertEqual(before,s.snapshot())
 def test_original_world_full_frames(self):
  oracle=json.loads((FIX/'ORACLE.json').read_text());oracle['frames']+=json.loads((FIX/'DEPTH-ORACLE.json').read_text())['frames'];data=(FIX/'model-records.bin').read_bytes()
  with self.scene() as s:
   self.upload(s,data)
   for row in oracle['frames']:
    with self.subTest(case=row['id']):
     records=(FIX/row.get('recordsFile','model-records.bin')).read_bytes();self.upload(s,records);self.configure(s,row['config']);before=s.snapshot();actual=s.render().bytes
     expected=bytearray(self.original.expected_model(row,(FIX/row['id']).read_bytes(),records))
     # Original fourth word is source coverage1; public fourth word is interactive hitID0.
     # Compare the entire buffer after this explicit domain mapping; no pixel mask.
     for i in range(12,len(expected),16):struct.pack_into('<I',expected,i,0)
     self.assertTrue(actual==expected,f'{row["id"]}: actual {len(actual)}B {hashlib.sha256(actual).hexdigest()}, expected {len(expected)}B {hashlib.sha256(expected).hexdigest()}');self.assertEqual(before,s.snapshot())
     capture=os.environ.get('NOCTURNE_MODEL_CAPTURE_DIR')
     if capture:
      directory=Path(capture)/'native';directory.mkdir(parents=True,exist_ok=True);(directory/row['id']).write_bytes(actual)

 def test_above_original_limit_last_triangle_is_visible_and_retained(self):
  hidden=struct.pack('<9iI',*([8000000,0,0,8000256,0,0,8000000,256,0]),0xff0000)
  visible=struct.pack('<9iI',-2048,-2048,0,2048,-2048,0,0,2048,0,0x00ff00)
  data=hidden*16001+visible;q=json.loads((FIX/'ORACLE.json').read_text())['frames'][0]['config'];q[4]=0
  with self.scene() as s:
   self.upload(s,hidden*16001);self.configure(s,q);empty=s.render().bytes;self.upload(s,data);full=s.render().bytes
   self.assertNotEqual(empty,full);self.assertIn(struct.pack('<I',0x00ff00),full);self.assertEqual(self.readback(s),data)
 def test_rejected_upload_is_atomic_and_cross_arena_aliases_reject(self):
  data=(FIX/'model-records.bin').read_bytes()
  with self.scene() as s:
   self.upload(s,data);lib=self.api(s);before=s.snapshot();frame=s.render().bytes
   bad=bytearray(data);struct.pack_into('<I',bad,36,0x1000000);raw=C.create_string_buffer(bytes(bad))
   self.assertLess(lib.nrModelSet(s._context,raw,len(bad)//40),0);self.assertEqual(before,s.snapshot());self.assertEqual(frame,s.render().bytes)
   for pointer,size in [(s._context.value,120),(s._context.value+8,120),(C.addressof(s._test_model_memory),lib.nrModelMemorySize(s._context))]:
    with self.subTest(pointer=pointer):self.assertLess(lib.nrSetModelMemory(s._context,pointer,size),0)
   modelptr=(C.addressof(s._test_model_memory)+7)&~7
   self.assertLess(lib.nrModelCopy(s._context,modelptr,4608),0)
   self.assertLess(lib.nrSetPromptMemory(s._context,modelptr,lib.nrModelMemoryCapacity(s._context)),0)
   self.assertLess(lib.nrSetRenderMemory(s._context,modelptr,lib.nrRenderMemorySize(s._context)),0)
   self.assertEqual(before,s.snapshot());self.assertEqual(data,self.readback(s))
 def test_snapshot_restore_needs_both_arenas_without_partial_commit(self):
  data=(FIX/'model-records.bin').read_bytes();text='A🙂אב\n'*14001
  with self.scene() as source,self.scene() as target:
   source.command(dict(op='input',text=text));self.upload(source,data);saved=source.snapshot();lib=self.api(target);before=target.snapshot();frame=target.render().bytes;raw=C.create_string_buffer(saved);seen=[]
   while True:
    rc=lib.nrLoad(target._context,raw,len(saved))
    if rc==0:break
    error=lib.nrError(target._context);seen.append(error);self.assertEqual(before,target.snapshot());self.assertEqual(frame,target.render().bytes)
    if error==b'Prompt storage required':target._ensure_prompt_memory()
    elif error==b'Model storage required':
     size=lib.nrModelMemorySize(target._context);memory=C.create_string_buffer(size+8);self.assertEqual(lib.nrSetModelMemory(target._context,(C.addressof(memory)+7)&~7,size),0);target._test_model_memory=memory
    else:self.fail(error)
   self.assertIn(b'Prompt storage required',seen);self.assertIn(b'Model storage required',seen);self.assertEqual(saved,target.snapshot());self.assertEqual(data,self.readback(target));self.assertEqual(source.render().bytes,target.render().bytes)
 def test_corrupt_model_suffix_rejects_atomically_after_real_crc(self):
  import zlib
  data=(FIX/'model-records.bin').read_bytes()
  with self.scene() as s:
   self.upload(s,data);lib=self.api(s);saved=s.snapshot()
   for mutate in ('color','coordinate','truncate'):
    bad=bytearray(saved)
    if mutate=='color':struct.pack_into('<I',bad,len(bad)-4,0x1000000)
    elif mutate=='coordinate':struct.pack_into('<i',bad,len(bad)-40,8388609)
    else:bad=bad[:-4];struct.pack_into('<I',bad,16,len(bad)-24)
    struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]));raw=C.create_string_buffer(bytes(bad))
    with self.subTest(mutate=mutate):self.assertLess(lib.nrLoad(s._context,raw,len(bad)),0);self.assertEqual(saved,s.snapshot());self.assertEqual(data,self.readback(s))
 def test_render_arena_can_rebind_same_pointer_without_cross_model_alias(self):
  with self.scene() as s:
   lib=self.api(s);size=lib.nrRenderMemorySize(s._context);memory=C.create_string_buffer(size+8)
   pointer=(C.addressof(memory)+7)&~7
   self.assertEqual(lib.nrSetRenderMemory(s._context,pointer,size),0)
   self.assertEqual(lib.nrSetRenderMemory(s._context,pointer,size),0)
 def test_model_info_exposes_owned_resource_and_effective_view(self):
  with self.scene() as s:
   s.set_model_records((FIX/'model-records.bin').read_bytes());info=s.info_complete()
   self.assertEqual(info['sourceModel']['triangles'],4608);self.assertIsNone(info['sourceModel']['view'])
   s.command(dict(op='model-view',controls=dict(cameraZ=-85,sampling=1)))
   view=s.info_complete()['sourceModel']['view'];self.assertEqual(view['controls']['cameraZ'],-85);self.assertEqual(view['controls']['sampling'],1)
   s.command(dict(op='remove-model-view'));self.assertEqual(s.info_complete()['sourceModel'],dict(triangles=4608,view=None))
 def test_genuine_schema89_migrates_complete_frame_and_document(self):
  import gzip
  fixture=ROOT/'tests/fixtures/first-prompt-schema89';raw=gzip.decompress((fixture/'snapshot.gz').read_bytes());expected=gzip.decompress((fixture/'frame.gz').read_bytes());original=json.loads((fixture/'info.json').read_text())
  self.assertEqual(struct.unpack_from('<I',raw,12)[0],0x20261089)
  with self.scene() as s:
   s.restore(raw);self.assertEqual(s.render().bytes,expected);self.assertEqual(s.info()['prompt']['text'],original['prompt']['text']);self.assertEqual(s.model_records(),b'');self.assertEqual(struct.unpack_from('<I',s.snapshot(),12)[0],s.info()['contract']['snapshotSchema'])
 def test_genuine_schema90_fixture_restores_exact_model_frame(self):
  import gzip,hashlib
  fixture=ROOT/'tests/fixtures/original-model-schema90';raw=gzip.decompress((fixture/'snapshot.gz').read_bytes());expected=gzip.decompress((fixture/'frame.gz').read_bytes());proof=json.loads((fixture/'PROVENANCE.json').read_text())
  self.assertEqual(hashlib.sha256(raw).hexdigest(),proof['snapshotSha256']);self.assertEqual(struct.unpack_from('<I',raw,12)[0],0x20261090)
  with self.scene() as s:
   s.restore(raw);self.assertEqual(s.render().bytes,expected);self.assertEqual(s.model_records(),(FIX/'model-records.bin').read_bytes());new=s.snapshot();self.assertEqual(struct.unpack_from('<I',new,12)[0],s.info()['contract']['snapshotSchema']);self.assertEqual(hashlib.sha256(new[32:24+30489392]).hexdigest(),hashlib.sha256(raw[32:24+30489392]).hexdigest());self.assertEqual(new[24+30489392+len(new)-len(raw):],raw[24+30489392:]);s.restore(new);self.assertTrue(s.snapshot()==new)
 def test_python_owned_binding_upload_export_restore(self):
  data=(FIX/'model-records.bin').read_bytes()
  with self.scene() as a,self.scene() as b:
   self.assertTrue(hasattr(a,'set_model_records'));a.set_model_records(data);self.assertEqual(a.model_records(),data);b.restore(a.snapshot());self.assertEqual(b.model_records(),data)
   a.set_model_records(b'');self.assertEqual(a.model_records(),b'');self.assertEqual(b.model_records(),data)
if __name__=='__main__':unittest.main()
