"""Unexecuted text-batch contracts: retained prompt/window grapheme identity."""
import ctypes as C,json,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TextRunIdentities(unittest.TestCase):
 def current_prompt_identity_offsets(self,scene,data):
  # PromptWire has131 used-length arrays and eight-byte struct alignment;
  # source/identity arrays128/129 are active, unlike the historical mirror.
  wire=scene._lib.nrPromptWireSize();footer=scene._lib.nrSnapshotSize()-wire
  lengths_at=footer+wire-((131*4+7)//8)*8;lengths=struct.unpack_from('<131I',data,lengths_at)
  self.assertEqual(footer+wire+sum(lengths)*4,len(data));source=[ord(c) for c in scene.text_run_source(0,0)];rows=scene.text_run_clusters(0,0)
  self.assertEqual((lengths[0],lengths[128],lengths[129]),(len(source),)*3)
  identity=footer+wire+sum(lengths[:129])*4;retained_source=identity-len(source)*4;generation=lengths_at-8
  self.assertEqual(struct.unpack_from('<I',data,lengths_at-12)[0],len(source));self.assertEqual(struct.unpack_from('<I',data,generation)[0],rows[0][3])
  self.assertEqual(list(struct.unpack_from('<'+str(len(source))+'I',data,retained_source)),source)
  identities=[0]*len(source)
  for ident,start,end,_ in rows:identities[start:end]=[ident]*(end-start)
  self.assertEqual(list(struct.unpack_from('<'+str(len(source))+'I',data,identity)),identities)
  return retained_source,identity,generation
 def test_prompt_prefix_suffix_and_cluster_content_change(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='A e\u0301 Z',emitWeather=False));old=s.text_run_clusters(0,0);self.assertEqual([(r[1],r[2]) for r in old],[(0,1),(1,2),(2,4),(4,5),(5,6)])
   s.command(dict(op='draft',text='A X e\u0301 Z',emitWeather=False));new=s.text_run_clusters(0,0)
   self.assertEqual(new[0][0],old[0][0]);self.assertEqual(new[-1][0],old[-1][0]);self.assertEqual(new[-3][0],old[-3][0]);self.assertNotIn(new[2][0],[r[0] for r in old])
   s.command(dict(op='draft',text='A X e\u0300 Z',emitWeather=False));changed=s.text_run_clusters(0,0);self.assertNotEqual(changed[-3][0],new[-3][0]);self.assertEqual(changed[-1][0],new[-1][0])
 def test_window_body_and_title_reflow_and_typed_updates(self):
  with NativeScene() as s:
   s.command(dict(op='window',id=1,title='T 👩\u200d🚀',text='Body e\u0301'));body=s.text_run_clusters(2,1);title=s.text_run_clusters(3,1)
   s.command(dict(op='window',id=1,width=40,height=20));self.assertEqual(s.text_run_clusters(2,1),body);self.assertEqual(s.text_run_clusters(3,1),title)
   s.command(dict(op='define',path='/body',value='Body e\u0301!',binding=dict(family='window',id=1,field='text')))
   self.assertEqual(s.text_run_clusters(2,1)[:-1],body);self.assertEqual(s.text_run_clusters(3,1),title)
 def test_render_query_owned_results_and_rejection(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='x',emitWeather=False));before=s.snapshot();rows=s.text_run_clusters(0,0);rows[0][0]=999;s.render();s.text_run_layout(0,0,80);self.assertEqual(s.snapshot(),before);self.assertNotEqual(s.text_run_clusters(0,0)[0][0],999)
   out=(C.c_uint32*4)(*([123]*4));fn=s._lib.nrTextRunClusters;self.assertEqual(fn(s._context,0,0,out,0),-1);self.assertEqual(list(out),[123]*4)
   with self.assertRaises(ValueError):s.text_run_clusters(2,999)
 def test_scheduled_edits_are_partition_independent(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='A',emitWeather=False))
   for ident,time,text in [(1,250000,'AB'),(2,500000,'AC'),(3,750000,'A')]:s.command(dict(op='schedule',id=ident,atUs=time,command=dict(op='draft',text=text,emitWeather=False)))
   start=s.snapshot();s.advance_to(1000000);finish=s.snapshot();s.restore(start)
   for time in [250000,500000,750000,1000000]:s.advance_to(time)
   self.assertEqual(s.snapshot(),finish)
 def test_schema34_migration_is_deterministic_and_preserves_source(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='e\u0301 👩\u200d🚀',emitWeather=False));data=bytearray(s.snapshot()[:24+12508512]);struct.pack_into('<I',data,28,0x20261034);struct.pack_into('<III',data,12,0x20261034,12508512,zlib.crc32(data[24:]))
   s.restore(data);first=s.snapshot();ids=s.text_run_clusters(0,0);self.assertEqual(s.text_run_source(0,0),'e\u0301 👩\u200d🚀');s.restore(data);self.assertEqual(s.snapshot(),first);self.assertEqual(s.text_run_clusters(0,0),ids)
 def test_animated_text_retains_legacy_cluster_identity(self):
  with NativeScene() as s:
   s.command(dict(op='text',id=1,text='e\u0301x'));rows=s.text_run_clusters(1,1)
   for i,row in enumerate(rows):self.assertEqual(row[0],s.text_cluster_sample(1,i)[0]);self.assertEqual(row[3],0)

 def test_checksum_correct_cached_source_identity_and_generation_corruption(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='éx',emitWeather=False));before=s.snapshot();source,identity,generation=self.current_prompt_identity_offsets(s,before);ids=s.text_run_clusters(0,0)
   s.restore(before);self.assertEqual(s.snapshot(),before);self.assertEqual(s.text_run_clusters(0,0),ids)
   for offset,value in [(source,ord('z')),(identity+4,ids[1][0]),(generation,0),(identity,0)]:
    bad=bytearray(before);struct.pack_into('<I',bad,offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
    with self.assertRaises(ValueError):s.restore(bad)
    self.assertEqual(s.snapshot(),before);self.assertEqual(s.text_run_source(0,0),'éx');self.assertEqual(s.text_run_clusters(0,0),ids)
 def test_full_prompt_capacity_and_empty_runs(self):
  with NativeScene() as s:
   self.assertEqual(s.text_run_clusters(0,0),[]);s.command(dict(op='draft',text='x'*2048,emitWeather=False));rows=s.text_run_clusters(0,0)
   self.assertEqual(len(rows),2048);self.assertEqual(len({r[0] for r in rows}),2048);self.assertEqual(rows[-1][1:3],[2047,2048])
   s.command(dict(op='draft',text='',emitWeather=False));self.assertEqual(s.text_run_clusters(0,0),[])

 def test_paste_undo_and_atomic_batch_preserve_unedited_clusters(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='AZ',caret=1,emitWeather=False));old=s.text_run_clusters(0,0)
   s.command(dict(op='paste',text='é'));inserted=s.text_run_clusters(0,0);self.assertEqual([inserted[0][0],inserted[-1][0]],[old[0][0],old[-1][0]])
   s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(s.text_run_source(0,0),'AZ');self.assertEqual(s.text_run_clusters(0,0),old)
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(dict(op='batch',commands=[dict(op='draft',text='temporary',emitWeather=False),dict(op='window',id=1,width=-1)]))
   self.assertEqual(s.snapshot(),before)

 def test_exhausted_identity_allocator_restores_blocked_edit_for_cancellation(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='A',emitWeather=False));s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='draft',text='AB',emitWeather=False)))
   data=bytearray(s.snapshot());struct.pack_into('<I',data,24+12508512,0xffffffff);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));s.restore(data);blocked=s.snapshot();ids=s.text_run_clusters(0,0)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);self.assertEqual(s.text_run_clusters(0,0),ids)
   s.restore(blocked);self.assertEqual(s.snapshot(),blocked);s.command(dict(op='cancel-schedule',id=1));s.advance_to(500000);self.assertEqual(s.text_run_source(0,0),'A');self.assertEqual(s.text_run_clusters(0,0),ids)
 def test_exhausted_run_generation_restores_pending_window_for_cancellation(self):
  with NativeScene() as s:
   s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='window',id=1,title='New',text='Body')))
   data=bytearray(s.snapshot());struct.pack_into('<I',data,24+12508512+4,0xffffffff);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));s.restore(data);blocked=s.snapshot()
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);s.restore(blocked);self.assertEqual(s.snapshot(),blocked);s.command(dict(op='cancel-schedule',id=1));s.advance_to(500000)
   with self.assertRaises(ValueError):s.text_run_clusters(2,1)

 def test_exhausted_allocator_probe_assigns_distinct_scratch_clusters(self):
  with NativeScene() as s:
   s.command(dict(op='draft',text='A',emitWeather=False));s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='draft',text='A'+'x'*2047,emitWeather=False)))
   data=bytearray(s.snapshot());struct.pack_into('<I',data,24+12508512,0xffffffff);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));s.restore(data);blocked=s.snapshot()
   self.assertEqual(s.text_run_clusters(0,0)[0][1:3],[0,1]);s.restore(blocked);self.assertEqual(s.snapshot(),blocked)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked)

 def test_exhausted_counters_without_queue_preserve_document_and_purity(self):
  for counter in [12508512,12508516]:
   with self.subTest(counter=counter),NativeScene() as s:
    s.command(dict(op='draft',text='éx',emitWeather=False));data=bytearray(s.snapshot());struct.pack_into('<I',data,24+counter,0xffffffff);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));s.restore(data);before=s.snapshot();ids=s.text_run_clusters(0,0)
    s.render();self.assertEqual(s.text_run_source(0,0),'éx');self.assertEqual(s.text_run_clusters(0,0),ids);self.assertEqual(s.snapshot(),before);s.restore(before);self.assertEqual(s.snapshot(),before)
 def test_dynamic_long_prompt_probe_is_pure_atomic_cancellable_and_undoable(self):
  text='A'+'é中👩‍🚀'*11000
  with NativeScene() as s:
   s.command(dict(op='draft',text=text,emitWeather=False));ids=s.text_run_clusters(0,0);before=s.snapshot();capacity=s._lib.nrPromptMemoryCapacity(s._context)
   queued=dict(op='schedule',id=1,atUs=500000,command=dict(op='input',text='X'));raw=json.dumps(queued).encode();buf=C.create_string_buffer(raw)
   self.assertLess(s._lib.nrCommand(s._context,buf,len(raw)),0);self.assertEqual(s._lib.nrError(s._context),b'Prompt storage required');self.assertGreater(s._lib.nrPromptMemorySize(s._context),capacity);self.assertEqual(s.snapshot(),before)
   s.command(queued);self.assertGreater(s._lib.nrPromptMemoryCapacity(s._context),capacity);normal=s.snapshot()
   with self.assertRaisesRegex(ValueError,'Scheduled command fails validation against current state'):s.command(dict(op='schedule',id=2,atUs=600000,command=dict(op='input',text=123)))
   self.assertEqual(s.snapshot(),normal);self.assertEqual(s.text_run_clusters(0,0),ids)
   s.advance_to(500000);self.assertEqual(s.text_run_source(0,0),text+'X');s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(s.text_run_source(0,0),text);self.assertEqual(s.text_run_clusters(0,0),ids);s.command(dict(op='key',key='r',ctrl=True));self.assertEqual(s.text_run_source(0,0),text+'X');s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(s.text_run_source(0,0),text);self.assertEqual(s.text_run_clusters(0,0),ids)
   s.restore(normal);data=bytearray(normal);struct.pack_into('<I',data,24+12508512,0xffffffff);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));s.restore(data);blocked=s.snapshot()
   s.render();self.assertEqual(s.text_run_source(0,0),text);self.assertEqual(s.text_run_clusters(0,0),ids);self.assertEqual(s.snapshot(),blocked)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);self.assertEqual(s.text_run_clusters(0,0),ids);s.restore(blocked);self.assertEqual(s.snapshot(),blocked)
   s.command(dict(op='cancel-schedule',id=1));s.advance_to(500000);self.assertEqual(s.text_run_source(0,0),text);self.assertEqual(s.text_run_clusters(0,0),ids)
