"""Public current SourceStage contract, verified against original source."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C, gzip, json, os, sys, unittest, struct, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
LIB=Path(os.environ.get('NOCTURNE_STAGE_LIBRARY',str(ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'))))
class SourceStageQueries(unittest.TestCase):
 def scene(self):return NativeScene(library=LIB)
 def test_original_pure_query_exports_exist(self):
  with self.scene() as s:
   for name in ('nrSourceStageTween','nrSourceStageInkOpacity','nrSourceStageHit'):
    with self.subTest(name=name):self.assertTrue(hasattr(s._lib,name),name)
 def test_full_original_scene_command_exists(self):
  with self.scene() as s:
   s.command({'op':'source-stage','timeMs':0})
   self.assertTrue(s.info()['sourceStage']['enabled'])
 def test_actual_original_message_id_domain(self):
  with self.scene() as s:
   s.command({'op':'source-stage-component','id':1,'legacyFlags':100001,'kind':'text','width':20,'height':1,'text':'original message'})
   self.assertEqual(s.info()['sourceStageComponents'][0]['legacyFlags'],100001)

FIX=ROOT/'tests/fixtures/source-stage'
def scene_command(row):
 config=json.loads(json.dumps(row['config']))
 for key in ('palette','starPalette'):config[key]=[int(v[1:],16) if isinstance(v,str) else v for v in config[key]]
 for key in ('glyphs','novaGlyphs'):config[key]=[ord(v) if isinstance(v,str) else v for v in config[key]]
 return {'op':'source-stage','config':config,'timeMs':row['timeMs'],'events':row.get('events',[])}
def component(n,i):
 n=dict(n);legacy=n.pop('id',0)
 for k in ('fg','bg'):
  if isinstance(n.get(k),str):n[k]=int(n[k][1:],16)
 return dict(n,op='source-stage-component',id=i+1,legacyFlags=legacy)
class SourceStageOriginal(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.oracle=json.loads((FIX/'ORACLE.json').read_text())
 def scene(self):return NativeScene(library=LIB)
 def api(self,s):
  for name,args in [('nrSourceStageTween',[C.c_int32,C.c_int32,C.c_uint64,C.c_uint32,C.c_int32]),('nrSourceStageInkOpacity',[C.c_uint32,C.c_uint32,C.c_int32,C.c_int32,C.c_int32]),('nrSourceStageHit',[C.c_void_p,C.c_int32,C.c_int32,C.c_void_p,C.c_uint32])]:
   f=getattr(s._lib,name);f.argtypes=args;f.restype=C.c_int32
  return s._lib
 def configure(self,s,row):
  s.command({'op':'reset'});v=row['config']['values'];s.command({'op':'resize','width':v['width'],'height':v['height']});s.command({'op':'environment','presentation':'canvas','stars':0});s.command({'op':'prompt','active':False});s.command({'op':'floor','enabled':False,'visible':False});s.command(scene_command(row))
  for i,n in enumerate(row['nodes']):s.command(component(n,i))
 def test_original_all_full_frames_no_pixel_masks(self):
  with self.scene() as s:
   for row in self.oracle['cases']:
    with self.subTest(case=row['id']):
     self.configure(s,row);saved=s.snapshot();actual=s.render().bytes;expected=gzip.decompress((FIX/(row['id']+'.bin.gz')).read_bytes());self.assertEqual(len(actual),len(expected))
     # Original flags contain legacy IDs; current fourth word owns a native component.
     # Every glyph and both RGB words are compared at every cell, without spatial masks.
     for cell in range(0,len(actual),16):self.assertEqual(actual[cell:cell+12],expected[cell:cell+12],(row['id'],cell//16))
     self.assertEqual(saved,s.snapshot())
 def test_original_all_scalar_queries(self):
  with self.scene() as s:
   lib=self.api(s);saved=s.snapshot()
   for key,name in [('tween','nrSourceStageTween'),('opacity','nrSourceStageInkOpacity')]:
    for row in self.oracle[key]:self.assertEqual(getattr(lib,name)(*row['args']),row['expected'],row)
   self.assertEqual(lib.nrSourceStageInkOpacity(1,1,0,-1,0),-1);self.assertEqual(lib.nrSourceStageInkOpacity(1,1,0,0,1001),-1);self.assertEqual(saved,s.snapshot())
 def test_original_geometric_hits_and_owned_output(self):
  with self.scene() as s:
   lib=self.api(s)
   for i,n in enumerate(self.oracle['hitNodes']):s.command(component(n,i))
   before=s.snapshot();out=(C.c_int32*2)(-123,-456)
   for row in self.oracle['hits']:
    out[:]=[-123,-456];status=lib.nrSourceStageHit(s._context,row['x'],row['y'],out,2);e=row['expected'];self.assertEqual(status,1 if e else 0,row)
    self.assertEqual(list(out),[e['id'],e['item']] if e else [-123,-456],row)
   for ptr,cap in [(None,2),(C.addressof(out)+1,2),(C.addressof(out),1),(s._context.value,2),(2**(C.sizeof(C.c_void_p)*8)-4,2)]:self.assertEqual(lib.nrSourceStageHit(s._context,1,1,ptr,cap),-1)
   s.render()
   for memory in (s._render_memory,s._prompt_memory,s._model_memory):
    if memory is not None:self.assertEqual(lib.nrSourceStageHit(s._context,1,1,C.addressof(memory),2),-1)
   self.assertEqual(lib.nrSourceStageHit(s._context,4097,0,out,2),-1);self.assertEqual(before,s.snapshot())
 def test_scene_patch_disable_reset_and_atomic_rejection(self):
  with self.scene() as s:
   s.command({'op':'source-stage','timeMs':2**32+7,'events':[{'x':1.5,'y':-2.5,'atMs':2**53-1,'id':2147483647}]});info=s.info_complete()['sourceStage'];self.assertEqual(info['timeMs'],2**32+7);self.assertEqual(info['events'][0]['atMs'],2**53-1)
   before=s.snapshot()
   # One column past the scene's int32 arithmetic limit (see test_source_stage_extent); 513x30 is now admitted.
   for command in [{'op':'source-stage','config':{'values':{'bad':1}}},{'op':'source-stage','events':[{'x':0,'y':0,'atMs':2**53}]},{'op':'source-stage','config':{'glyphs':[0xd800]}},{'op':'source-stage','enabled':False,'timeMs':0},{'op':'source-stage','events':[{'x':0,'y':0,'atMs':0}]*129},{'op':'source-stage','config':{'values':{'paletteCount':6}}},{'op':'resize','width':8384513,'height':30}]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(before,s.snapshot())
   s.command({'op':'prompt','active':False});s.command({'op':'environment','presentation':'canvas'});s.command({'op':'source-stage','config':{'values':{'motion':0}}});frame=s.render().bytes;s.advance_to(1000000);self.assertEqual(frame,s.render().bytes)
   s.command({'op':'source-stage','enabled':False});self.assertFalse(s.info_complete()['sourceStage']['enabled']);s.command({'op':'source-stage'});s.command({'op':'reset'});self.assertFalse(s.info_complete()['sourceStage']['enabled'])
 def test_original_event_rounding_and_late_batch_atomicity(self):
  with self.scene() as s:
   s.command({'op':'source-stage','events':[{'x':4096+1/1024,'y':-4096-1/512,'atMs':0}]});event=s.info_complete()['sourceStage']['events'][0];self.assertEqual(event['x'],4096);self.assertEqual(event['y'],-4096)
   before=s.snapshot()
   bad={'op':'source-stage','timeMs':123,'events':[{'x':0,'y':0,'atMs':0},{'x':4096+1/512,'y':0,'atMs':0}]}
   with self.assertRaises(ValueError):s.command({'op':'batch','commands':[{'op':'source-stage-component','id':1,'legacyFlags':100001,'kind':'button','width':3,'height':2},bad]})
   self.assertTrue(before==s.snapshot())
 def test_fresh_count_without_array_rejected(self):
  with self.scene() as s:
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'source-stage','config':{'values':{'paletteCount':6}}})
   self.assertEqual(before,s.snapshot())
 def test_event_max_safe_snapshot_and_semantic_corruption(self):
  import zlib
  with self.scene() as s:
   s.command({'op':'source-stage','timeMs':2**53-1,'events':[{'x':1.5,'y':-2.5,'atMs':2**53-1,'id':2147483647,'kind':1}]});saved=s.snapshot();s.command({'op':'reset'});s.restore(saved);self.assertEqual(saved,s.snapshot());self.assertEqual(s.info_complete()['sourceStage']['events'][0]['atMs'],2**53-1)
   # Actual static-asserted scene offset+original event word7; repair CRC to
   # exercise semantic validation, not merely checksum rejection.
   bad=bytearray(saved);struct.pack_into('<I',bad,24+30489392+720+28,1);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]));before=s.snapshot()
   with self.assertRaises(ValueError):s.restore(bytes(bad))
   self.assertEqual(before,s.snapshot())
 def test_all_owned_arena_aliases_reject_without_mutation(self):
  with self.scene() as s:
   s.restore(gzip.decompress((ROOT/'tests/fixtures/source-stage-schema91/snapshot.gz').read_bytes()));s.command({'op':'resize','width':200,'height':121});s.render();lib=self.api(s);before=s.snapshot()
   for memory,capacity in ((s._memory,lib.nrContextSize()),(s._render_memory,lib.nrRenderMemoryCapacity(s._context)),(s._prompt_memory,lib.nrPromptMemoryCapacity(s._context)),(s._model_memory,lib.nrModelMemoryCapacity(s._context))):
    self.assertIsNotNone(memory);base=(C.addressof(memory)+7)&~7
    for offset in (0,8,capacity-4):self.assertEqual(lib.nrSourceStageHit(s._context,2,1,base+offset,2),-1)
   self.assertTrue(before==s.snapshot())
 def test_transient_native_overlay_keeps_global_clock_and_base(self):
  from native.tests.test_source_stage_public_integration import source_node
  def draw(enabled,state=0):
   with self.scene() as s:
    for cmd in ({'op':'resize','width':32,'height':12},{'op':'environment','presentation':'canvas','stars':0,'background':0x11100e},{'op':'prompt','active':False},{'op':'floor','enabled':False,'visible':False}):s.command(cmd)
    s.advance_to(1000000)
    if enabled:s.command({'op':'source-stage','timeMs':0,'config':{'values':{'pattern':0,'baseColor':0x551100,'starDensity':0}}})
    s.render()
    node,text,_=source_node('text',x=2,y=3,width=10,height=1,text='native UI',state=state,colorAnimation=1,hueSpeed=47,fgOpacity=1000,bgOpacity=1000,bg=0x11100e)
    fn=s._lib.nrSourceStageDrawTransient;fn.argtypes=[C.c_void_p,C.POINTER(C.c_int32),C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.c_uint32];fn.restype=C.c_int
    before=s.snapshot();self.assertEqual(fn(s._context,(C.c_int32*32)(*node),(C.c_uint32*len(text))(*map(ord,text)),len(text),15,12),0);self.assertEqual(before,s.snapshot())
    raw=C.string_at(s._lib.nrCells(s._context),32*12*16)
    return [raw[(3*32+x)*16:(3*32+x)*16+12] for x in range(2,11)]
  for state in (0,3):
   with self.subTest(state=state):self.assertEqual(draw(False,state),draw(True,state))
 def test_genuine90_dynamic_model_and_document_migrate(self):
  fix=ROOT/'tests/fixtures/source-stage-schema90';raw=gzip.decompress((fix/'snapshot.gz').read_bytes());proof=json.loads((fix/'PROVENANCE.json').read_text())
  with self.scene() as s:
   s.restore(raw);self.assertEqual(s.render().bytes,gzip.decompress((fix/'frame.gz').read_bytes()));self.assertEqual(hashlib.sha256(s.model_records()).hexdigest(),proof['modelSha256']);self.assertEqual(len(s.info_complete()['prompt']['text']),70005);self.assertFalse(s.info_complete()['sourceStage']['enabled'])
   before=s.snapshot();bad=bytearray(before);bad[-1]^=1
   with self.assertRaises(ValueError):s.restore(bytes(bad))
   self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main(verbosity=2)

