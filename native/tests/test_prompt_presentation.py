import ctypes as C,struct,zlib,unittest
from nocturne_native import NativeScene
class PromptPresentation(unittest.TestCase):
 def scene(self,text='Aé界Z',width=8,mode='grow',**extra):
  s=NativeScene();self.addCleanup(s.close);s.command({'op':'resize','width':width,'height':18});s.command({'op':'prompt','layout':'grapheme','mode':mode,'minRows':2,'maxRows':3,**extra});s.command({'op':'draft','text':text,'emitWeather':False});return s
 def test_wrap_wide_combining_source_spans_and_purity(self):
  s=self.scene();before=s.snapshot();rows=s.prompt_layout();self.assertEqual([r[:5] for r in rows],[[0,1,0,0,1],[1,3,1,0,1],[3,4,2,0,2],[4,5,0,1,1]])
  frame=s.render();cells=frame.words()
  for row in rows:
   a,b,col,line,w,x,y,visible=map(int,row);self.assertEqual(visible,1);self.assertEqual(cells[y*frame.width+x][0],ord('Aé界Z'[a]));self.assertEqual(s.inspect_character_cell(x,y)['index'],a)
   if w==2:self.assertEqual(cells[y*frame.width+x+1][0],32)
  self.assertEqual(s.text_run_source(0,0),'Aé界Z');self.assertEqual(s.snapshot(),before);rows[0][0]=99;self.assertEqual(s.prompt_layout()[0][0],0)
 def test_pointer_only_cluster_edges_and_width_navigation(self):
  s=self.scene();rows=s.prompt_layout();x,y=map(int,rows[1][5:7])
  for phase in ['down','up']:s.command({'op':'pointer','phase':phase,'x':x,'y':y})
  self.assertEqual(s.info()['prompt']['caret'],1)
  s.command({'op':'draft','text':'界X\nAB','caret':1,'emitWeather':False});s.command({'op':'key','key':'ArrowDown'});self.assertEqual(s.info()['prompt']['caret'],5)
  s.command({'op':'draft','text':'AéZ','emitWeather':False});s.command({'op':'key','key':'ArrowLeft'});self.assertEqual(s.info()['prompt']['caret'],3)
 def test_ambiguity_tab_crlf_and_hidden(self):
  s=self.scene('·\tA\r\n界',width=12,ambiguousWidth=2);self.assertEqual([r[:5] for r in s.prompt_layout()],[[0,1,0,0,2],[1,2,2,0,2],[2,3,4,0,1],[3,5,5,0,0],[5,6,0,1,2]])
  s.command({'op':'prompt','active':False});self.assertTrue(all(r[7]==0 for r in s.prompt_layout()))
 def test_marquee_cluster_paging_and_scroll(self):
  s=self.scene('界界界éZ',width=8,mode='marquee');rows=s.prompt_layout();self.assertTrue(all(r[3]==0 for r in rows));self.assertTrue(all(r[5]+r[4]<=7 for r in rows if r[7]));self.assertGreater(rows[-1][7],0)
  s.command({'op':'prompt','mode':'grow','minRows':2,'maxRows':2});s.command({'op':'draft','text':'界\nA\nB\nZ','emitWeather':False});r=s.prompt_layout();self.assertEqual(r[-1][7],1);self.assertEqual(r[0][7],0)
 def test_negative_atomic_restore_and_old_default(self):
  s=self.scene();before=s.snapshot()
  for patch in [{'layout':'bad'},{'ambiguousWidth':0},{'ambiguousWidth':3},{'ambiguousWidth':True}]:
   with self.assertRaises(ValueError):s.command({'op':'prompt',**patch})
   self.assertEqual(before,s.snapshot())
  bad=bytearray(before);struct.pack_into('<I',bad,24+13497384,3);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
  with self.assertRaises(ValueError):s.restore(bad)
  self.assertEqual(before,s.snapshot())
  with NativeScene() as old:
   old.command({'op':'draft','text':'Aé界','emitWeather':False});frame=old.render();b=bytearray(old.snapshot()[:13497408]);struct.pack_into('<I',b,12,0x20261049);struct.pack_into('<I',b,28,0x20261049);struct.pack_into('<I',b,16,len(b)-24);struct.pack_into('<I',b,20,zlib.crc32(b[24:]));old.restore(b);self.assertEqual(frame,old.render());self.assertEqual(old.prompt_layout(),[])
 def test_real_C_output_canaries_probe_and_alias(self):
  s=self.scene();fn=s._lib.nrPromptLayout;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];fn.restype=C.c_int;self.assertEqual(fn(s._context,None,0),4);out=(C.c_double*40)(*([99]*40));before=s.snapshot()
  for ptr,cap in [(out,3),(C.c_void_p(C.addressof(out)+1),4),(s._context,4)]:self.assertEqual(fn(s._context,ptr,cap),-1)
  self.assertEqual(list(out),[99]*40);self.assertEqual(fn(s._context,out,4),4);self.assertEqual(list(out)[32:],[99]*8);self.assertEqual(before,s.snapshot())

 def test_trailing_hard_break_keeps_empty_caret_row_visible(self):
  s=self.scene('A\n',minRows=1,maxRows=4);self.assertEqual(s.prompt_layout()[0][6],14);self.assertEqual(s.prompt_layout()[0][7],1)
 def test_nested_queued_new_presentation_rejects_old_prefix(self):
  with NativeScene() as s:
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'prompt','layout':'grapheme','ambiguousWidth':2}]}});before=s.snapshot();b=bytearray(before[:13497408]);struct.pack_into('<I',b,12,0x20261049);struct.pack_into('<I',b,28,0x20261049);struct.pack_into('<I',b,16,len(b)-24);struct.pack_into('<I',b,20,zlib.crc32(b[24:]));
   with self.assertRaises(ValueError):s.restore(b)
   self.assertEqual(before,s.snapshot());s.advance_to(1000000);done=s.snapshot();s.restore(before)
   for t in [250000,500000,750000,1000000]:s.advance_to(t)
   self.assertEqual(done,s.snapshot());self.assertEqual(s.info()['prompt']['layout'],'grapheme')
