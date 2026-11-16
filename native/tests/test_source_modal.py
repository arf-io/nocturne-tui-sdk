"""Original Workbench modal controller: real current ABI, not reader emulation."""
import ctypes as C,gzip,json,os,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
LIB=Path(os.environ.get('NOCTURNE_MODAL_LIBRARY',ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')))
KINDS=['center','fullscreen','drawer-left','drawer-right','drawer-top','drawer-bottom','corner','toast','error','confirmation','dropdown']
def push(kind='center',id='same',**kw):
 e=dict(id=id,kind=kind,title='title',body='body',atMs=0,dismissible=True);e.update(kw.pop('entry',{}))
 return dict(op='source-modal',action='push',entry=e,context=kw.pop('context','commands'),**kw)
class SourceModal(unittest.TestCase):
 def scene(self):return NativeScene(library=LIB)
 def state(self,s):return s.info_complete()['sourceModal']
 def test_original_nested_restoration_and_duplicate_ids(self):
  with self.scene() as s:
   s.command(push(id='node',context='node',workspace='dag'));self.assertFalse(self.state(s)['blocking'])
   s.command(push());s.command(dict(op='source-modal',action='edit',query='camera',selected=3))
   s.command(push('confirmation'));self.assertEqual(self.state(s)['depth'],3)
   s.command(dict(op='source-modal',action='dismiss'));a=self.state(s);self.assertEqual((a['context'],a['query'],a['selected']),('commands','camera',3));self.assertTrue(a['blocking'])
   s.command(dict(op='key',key='Escape'));self.assertEqual(self.state(s)['depth'],1);self.assertFalse(self.state(s)['blocking'])
 def test_source_kinds_eight_depth_nondismissible_and_atomic_failures(self):
  with self.scene() as s:
   for kind in KINDS:
    s.command(push(kind));self.assertEqual(self.state(s)['entries'][-1]['kind'],kind);s.command(dict(op='source-modal',action='clear'))
   for _ in range(8):s.command(push())
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(push())
   self.assertEqual(before,s.snapshot());s.command(dict(op='source-modal',action='clear'));s.command(push(entry={'dismissible':False}));before=s.snapshot();s.command(dict(op='key',key='Escape'));self.assertEqual(before,s.snapshot())
   for command in [push(entry={'id':'bad id'}),push(entry={'atMs':-1}),push(entry={'body':None}),dict(op='source-modal',action='edit',query=None),dict(op='source-modal',action='edit',selected=-1),dict(op='batch',commands=[dict(op='source-modal',action='edit',query='changed'),dict(op='bad')])]:
    with self.subTest(command=command):
     with self.assertRaises(ValueError):s.command(command)
     self.assertEqual(before,s.snapshot())
 def test_unbounded_unicode_embedded_nul_four_text_fields_and_snapshot(self):
  text='🙂A\0אב\n'*14001
  with self.scene() as a,self.scene() as b:
   a.command(push(context=text,entry={'title':text,'body':text}));a.command(dict(op='source-modal',action='edit',query=text))
   info=self.state(a);self.assertEqual(info['context'],text);self.assertEqual(info['query'],text);self.assertEqual(info['entries'][0]['title'],text);self.assertEqual(info['entries'][0]['body'],text)
   snap=a.snapshot();a.render();self.assertEqual(snap,a.snapshot());b.restore(snap);self.assertEqual(self.state(a),self.state(b));self.assertEqual(snap,b.snapshot())
 def test_owner_gates_physical_input_and_preserves_help(self):
  with self.scene() as s:
   s.command(dict(op='input',text='original'));s.command(push());initial=s.info_complete()['prompt']['text'];camera=s.info_complete()['camera']
   for command in [dict(op='input',text='bad'),dict(op='paste',text='bad'),dict(op='key',key='a'),dict(op='wheel',x=1,y=1,delta=2),dict(op='pointer',phase='down',button=2,x=1,y=1),dict(op='pointer',phase='move',button=2,x=10,y=5)]:s.command(command)
   self.assertEqual(s.info_complete()['prompt']['text'],initial);self.assertEqual(s.info_complete()['camera'],camera)
   s.command(dict(op='key',key='F1'));s.command(dict(op='key',key='Escape'));self.assertEqual(self.state(s)['depth'],1);s.command(dict(op='key',key='Escape'));self.assertEqual(self.state(s)['depth'],0)
 def test_genuine92_and_malformed93_atomic(self):
  fix=ROOT/'tests/fixtures/original-observatory-schema92';raw=gzip.decompress((fix/'snapshot.gz').read_bytes());frame=gzip.decompress((fix/'frame.gz').read_bytes())
  with self.scene() as s:
   s.restore(raw);self.assertEqual(s.render().bytes,frame);self.assertEqual(self.state(s)['depth'],0);s.command(push());before=s.snapshot();self.assertEqual(struct.unpack_from('<I',before,12)[0],s.info_complete()['contract']['snapshotSchema'])
   bad=bytearray(before);struct.pack_into('<I',bad,len(bad)-4,0xd800);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(before,s.snapshot())
 def test_genuine93_full_document_model_and_modal_fixture(self):
  fix=ROOT/'tests/fixtures/original-modal-schema93';raw=gzip.decompress((fix/'snapshot.gz').read_bytes());frame=gzip.decompress((fix/'frame.gz').read_bytes())
  with self.scene() as s:s.restore(raw);self.assertEqual(struct.unpack_from('<I',s.snapshot(),12)[0],s.info_complete()['contract']['snapshotSchema']);self.assertEqual(s.render().bytes,frame);self.assertEqual(len(self.state(s)['query']),80000);self.assertEqual(self.state(s)['depth'],2)
 def test_required_storage_retry_and_cross_arena_output_alias(self):
  with self.scene() as s:
   lib=s._lib
   for name in ['nrModalMemorySize','nrModalMemoryCapacity','nrSetModalMemory']:self.assertTrue(hasattr(lib,name),name)
   raw=json.dumps(push(entry={'body':'x'*70000})).encode();before=s.snapshot();code=lib.nrCommand(s._context,raw,len(raw));self.assertLess(code,0);self.assertEqual(lib.nrError(s._context),b'Modal storage required');self.assertEqual(before,s.snapshot())
   need=lib.nrModalMemorySize(s._context);self.assertGreater(need,0);self.assertLess(lib.nrSetModalMemory(s._context,s._context,need),0)
   s.command(json.loads(raw));pointer=(C.addressof(s._modal_memory)+7)&~7;before=s.snapshot();self.assertLess(lib.nrSave(s._context,pointer,len(before)),0);self.assertEqual(before,s.snapshot())
 def test_associated_original_nodes_paint_once_and_block_obscured_hits(self):
  with self.scene() as a,self.scene() as b:
   setup=[dict(op='environment',presentation='canvas',stars=0,background=0x214365),dict(op='floor',enabled=False,visible=False),dict(op='prompt',active=False)]
   nodes=[dict(op='source-stage-component',id=49999,kind='box',legacyFlags=49999,x=4,y=4,width=24,height=9,fg=0xabcdee,bg=0x101721,bgOpacity=700,text='Modal'),dict(op='source-stage-component',id=47999,kind='item',legacyFlags=47999,x=6,y=10,width=20,height=1,text='Close',bgOpacity=900)]
   for x in (a,b):
    for c in setup:x.command(c)
   for c in nodes:b.command(c)
   a.command(push());
   for c in nodes:a.command(c)
   a.command(dict(op='source-modal',action='associate',componentIds=[49999,47999],boxId=49999))
   self.assertEqual([row[:3] for row in a.render().words()],[row[:3] for row in b.render().words()])
   self.assertEqual(a.source_stage_hit(7,10),{'id':47999,'item':0})
   a.command(dict(op='source-stage-component',id=3,kind='item',legacyFlags=123,x=6,y=10,width=20,height=1,text='Underneath'))
   self.assertEqual(a.source_stage_hit(7,10),{'id':47999,'item':0});self.assertIsNone(a.source_stage_hit(0,0))
   a.command(dict(op='source-modal',action='dismiss'));self.assertIsNone(a.source_stage_hit(7,5));self.assertNotEqual(a.render().bytes,b.render().bytes)
 def test_inspector_current_geometry_capture_cancel_and_authoring(self):
  with self.scene() as s:
   s.command(dict(op='pointer',phase='down',button=2,x=1,y=1));s.command(push(id='node',context='node',workspace='dag'))
   s.command(dict(op='source-stage-component',id=49999,kind='box',legacyFlags=49999,x=5,y=4,width=20,height=10,bgOpacity=800))
   s.command(dict(op='source-modal',action='associate',componentIds=[49999],boxId=49999));before=s.info_complete()['camera']
   s.command(dict(op='pointer',phase='move',button=2,x=30,y=20));self.assertEqual(before,s.info_complete()['camera'])
   s.command(dict(op='wheel',x=10,y=7,delta=1));self.assertEqual(before,s.info_complete()['camera'])
   s.command(dict(op='source-stage-component',id=49999,kind='box',legacyFlags=49999,x=40,y=4,width=20,height=10,bgOpacity=800))
   s.command(dict(op='wheel',x=10,y=7,delta=1));self.assertNotEqual(before,s.info_complete()['camera'])
   s.command(push());s.command(dict(op='draft',text='authoring remains explicit',emitWeather=False));self.assertEqual(s.info_complete()['prompt']['text'],'authoring remains explicit')
 def test_complete_metadata_and_cell_query_cannot_write_modal_arena(self):
  for query in ['metadata','cell']:
   with self.subTest(query=query),self.scene() as s:
    s.command(push(entry={'body':'x'*70000}));s.render();before=s.snapshot();pointer=(C.addressof(s._modal_memory)+7)&~7
    if query=='metadata':
     fn=s._lib.nrInfoPage;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32];fn.restype=C.c_int;result=fn(s._context,0,None,0,pointer,4)
    else:result=s._lib.nrInspectCharacterCell(s._context,0,0,pointer,4096)
    self.assertLess(result,0);self.assertEqual(before,s.snapshot())
 def test_removed_component_reuse_does_not_inherit_modal_ownership(self):
  with self.scene() as s:
   s.command(push());s.command(dict(op='source-stage-component',id=49999,kind='box',legacyFlags=49999,x=5,y=4,width=20,height=10,bgOpacity=800));s.command(dict(op='source-modal',action='associate',componentIds=[49999],boxId=49999));s.command(dict(op='source-modal',action='dismiss'));s.command(dict(op='remove-source-stage-component',id=49999));s.command(dict(op='source-stage-component',id=49999,kind='item',legacyFlags=10,x=5,y=4,width=20,height=1,text='New ordinary owner'))
   self.assertEqual(s.source_stage_hit(6,4),{'id':10,'item':0})
 def test_identifier_nul_and_blocked_modifier_are_atomic(self):
  with self.scene() as s:
   for identifier in ['a\0','a\0b','\0']:
    before=s.snapshot()
    with self.subTest(identifier=repr(identifier)):
     with self.assertRaises(ValueError):s.command(push(entry={'id':identifier}))
     self.assertEqual(before,s.snapshot())
   s.command(dict(op='prompt',mode='vim-inline'));s.command(dict(op='draft',text='abcdef',emitWeather=False));s.command(dict(op='key',key='Escape'));s.command(dict(op='key',key='3'));s.command(push());before=s.snapshot()
   s.command(dict(op='key',key='x',ctrl=True));self.assertEqual(before,s.snapshot())
 def test_original_complete_modal_artwork_and_source_color(self):
  oracle=json.loads(gzip.decompress((ROOT/'tests/fixtures/source-modal/COMPOSED.json.gz').read_bytes()))
  with self.scene() as s:
   for l,c,h,color in oracle['colors']:self.assertEqual(s.source_stage_oklch(l,c,h),color)
   for row in oracle['rows']:
    with self.subTest(kind=row['kind'],time=row['time']):
     s.command(dict(op='reset'));s.command(dict(op='resize',width=100,height=40));s.command(dict(op='environment',presentation='canvas',stars=0,background=0x214365));s.command(dict(op='floor',enabled=False,visible=False));s.command(dict(op='prompt',active=False));s.command(push(row['kind'],context=row['context'],entry={k:v for k,v in row['entry'].items() if k!='returnContext'}))
     ids=[]
     for i,node in enumerate(row['nodes']):
      node=dict(node);legacy=node.pop('id',0);id=60000+i;ids.append(id);s.command(dict(op='source-stage-component',id=id,legacyFlags=legacy,**node))
     s.command(dict(op='source-modal',action='associate',componentIds=ids,boxId=ids[0]));before=s.snapshot();actual=s.render().bytes;expected=struct.pack('<'+'I'*len(row['currentIdentityFrame']),*row['currentIdentityFrame']);self.assertEqual(actual,expected);self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
