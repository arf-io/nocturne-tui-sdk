"""All sixteen v0.1 prompt surfaces (layouts 0-4) against the v0.1 page's own kernel.

Two oracles, neither built from the implementation under test:
- the page: legacy/editions/0.1-Nocturne-Gallery.html evaluated verbatim in Node
  (its embedded WebAssembly, NocturneEngine, SCHEMA, PRESETS, presetConfig and
  the modal / next-selection / data-feed handlers, see v01_page_wasm_oracle.mjs);
- the archived C kernel compiled from native/tests/fixtures/first-prompt-v01.
For every frame the page's cells must equal the archived C kernel's cells, and the
engine's frame must equal them except for the documented fourth-word adaptation
(native input cells carry the prompt owner ID)."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import base64,ctypes as C,hashlib,json,math,os,struct,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import node_executable
from native.tests.test_first_prompt_source import compile_original,Config,Cell,INDICES,NR_ID_PROMPT
PAGE=ROOT.parent/'legacy/editions/0.1-Nocturne-Gallery.html'
PRESETS=json.loads((ROOT/'tests/fixtures/first-prompt-v01/presets.json').read_text())
HERO_TEXT='Make something that feels alive.' # The page's prompt input for presets without text.
LONG=''.join(chr(33+i%94)for i in range(300)) # Under the page's 512-point limit; wider than every input row.
VIEWPORTS=[(84,28),(160,48)]
# (timeMs, action): actions accumulate, as clicks on the one page config do.
STEPS=[(0,None),(33,None),(1200,None),(1234,None),(2400,None),(5000,None), # 33/1200/2400/5000 lie on the page's 30 Hz motion grid, 1234 does not
 (5001,'modal'),(5033,None),(5100,'selection'),(5133,'selection'),(5166,'selection'),(5200,'selection'),(5233,'selection'),(5266,'selection'),
 (5300,{'feedMs':5300}),(5301,{'feedMs':6100}),(5302,{'feedMs':333}),(6000,'modal'),(6000,'selection'),(7777,{'feedMs':7777})]
def js_round(x):return math.floor(x+0.5) # Math.round
def stamps(values,width,height,length):
 """Input cells exactly where the archived layout functions paint them."""
 layout=values['layout']
 if layout==2 and width>=64 and height>=26:column,row,cap=7,height-5,width-12
 elif layout in(1,2):
  x=5 if width>12 else 0;column,cap=x+2,width-x-4;focus=values['focusRow'];row=height//2 if focus<0 else min(focus,height-1)
 elif layout==3:
  n=min(length,max(0,width-4));return [((width-n)//2+i,height//2)for i in range(n+1)]
 else:return []
 n=min(length,max(0,cap));return [(column+i,row)for i in range(n+1)]
def effective(page):
 """The words the page's render() writes: the count fields always come from the array lengths."""
 return {**page['values'],'paletteCount':len(page['palette']),'starPaletteCount':len(page['starPalette']),'glyphCount':0}
def arrays(preset):return {k:[int(x.lstrip('#'),16)for x in preset[k]]for k in('palette','starPalette')if k in preset}
class V01PromptSurfaces(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='nocturne-v01-surfaces-');cls.out=Path(cls.temp.name)
  cls.original=compile_original(cls.out,'original',False);cls.lifted=None
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def scene(self):return NativeScene(library=os.environ.get('NOCTURNE_FIRST_LIBRARY',ROOT/'dist'/('libnocturne_native.dylib'if sys.platform=='darwin'else'libnocturne_native.so')))
 def page(self,cases):
  if not PAGE.is_file():return [self.page_config(case)for case in cases]
  src=self.out/'cases.json';dst=self.out/'page.json';src.write_text(json.dumps(cases))
  subprocess.run([node_executable(),str(ROOT/'tests/v01_page_wasm_oracle.mjs'),str(PAGE),str(src),str(dst)],check=True,timeout=600)
  return json.loads(dst.read_text())
 def page_config(self,case):
  """A packaged SDK has no legacy/: the page's presetConfig and handlers, restated, feed the archived C kernel alone
  (the page and the kernel defaults are compared field by field where the page is present)."""
  q=Config();self.original.nsDefaultConfig(C.byref(q));values={n:q.values[i]for n,i in INDICES.items()}
  preset=next(p for p in PRESETS if p['id']==case['preset']);values.update(preset['values'],width=case['width'],height=case['height'])
  for action in case['actions']:
   if action=='modal':values.update(layout=2,modalOpen=1-values['modalOpen'])
   elif action=='selection':values.update(layout=2,selection=(values['selection']+1)%6)
   else:values['valuePermille']=js_round(500+470*math.sin(action['feedMs']/750))
  hexes=lambda field,count:['#%06X'%field[i]for i in range(count)]
  return {'values':values,'palette':preset.get('palette',hexes(q.palette,4)),'starPalette':preset.get('starPalette',hexes(q.starPalette,6)),'frame':None}
 def kernel(self,oracle,page,width,height,text,time_ms):
  """The archived C kernel given the page's final config words."""
  q=Config();oracle.nsDefaultConfig(C.byref(q))
  for name,value in page['values'].items():q.values[INDICES[name]]=value
  for name,count in(('palette',39),('starPalette',40)):
   field=getattr(q,name);items=page[name];q.values[count]=len(items)
   for i in range(8):field[i]=int(items[i].lstrip('#'),16)if i<len(items)else 0
  q.values[41]=0
  data=(C.c_uint32*max(1,len(text)))(*map(ord,text));cells=(Cell*(width*height))()
  self.assertEqual(oracle.nsRender(C.byref(q),time_ms,data,len(text),cells,len(cells)),len(cells));return bytes(cells)
 def expected(self,raw,values,width,height,text):
  out=bytearray(raw)
  for x,y in stamps(values,width,height,len(text)):struct.pack_into('<I',out,((y*width+x)*16)+12,NR_ID_PROMPT)
  return bytes(out)
 def drive(self,s,action):
  """The page's handlers, expressed as existing prompt-source value patches."""
  v=s.info()['prompt']['firstPromptSource']['values']
  if action=='modal':patch={'layout':2,'modalOpen':1-v[42]}
  elif action=='selection':patch={'layout':2,'selection':(v[34]+1)%6}
  else:patch={'valuePermille':js_round(500+470*math.sin(action['feedMs']/750))}
  clock=s.info()['clock'];s.command({'op':'prompt-source','values':patch})
  # Data is event-driven: a value patch never advances motion.
  self.assertEqual(s.info()['clock'],clock)
 @unittest.skipUnless(PAGE.is_file(),'the v0.1 page lives in the source repository legacy/ tree, not a packaged SDK')
 def test_page_oracle_is_the_archived_kernel_and_presets(self):
  html=PAGE.read_text();start=html.index('const PRESETS=')+len('const PRESETS=');page_presets,_=json.JSONDecoder().raw_decode(html[start:])
  self.assertEqual(page_presets,PRESETS);self.assertEqual(len(PRESETS),16)
  self.assertEqual(sorted({p['values']['layout']for p in PRESETS}),[0,1,2,3,4])
 def test_every_preset_every_layout_interactive_sequence(self):
  cases=[];plan=[]
  for preset in PRESETS:
   text=preset.get('text',HERO_TEXT)
   for width,height in VIEWPORTS:
    actions=[]
    for time_ms,action in STEPS:
     if action is not None:actions.append(action)
     cases.append({'preset':preset['id'],'width':width,'height':height,'text':text,'timeMs':time_ms,'actions':list(actions)});plan.append((preset,width,height,text,time_ms,action))
  pages=self.page(cases);self.assertEqual(len(pages),len(plan));proof={};wasm=[]
  index=0
  for preset in PRESETS:
   for width,height in VIEWPORTS:
    with self.scene()as s:
     s.command({'op':'resize','width':width,'height':height});s.command({'op':'prompt-source','enabled':False})
     s.command({'op':'prompt-source','values':preset['values'],**arrays(preset)});s.command({'op':'draft','text':preset.get('text',HERO_TEXT),'emitWeather':False})
     for time_ms,action in STEPS:
      _,_,_,text,_,_=plan[index];page=pages[index];index+=1
      with self.subTest(preset=preset['id'],width=width,height=height,timeMs=time_ms,action=action):
       if action is not None:self.drive(s,action)
       s.advance_to(time_ms*1000)
       raw=self.kernel(self.original,page,width,height,text,time_ms)
       if page['frame']is not None:self.assertEqual(base64.b64decode(page['frame']),raw,'page WebAssembly differs from the archived C kernel')
       if page['frame']is not None:restated=self.page_config(cases[index-1]);self.assertEqual(effective(restated),effective(page));self.assertEqual([x.upper()for x in restated['palette']],[x.upper()for x in page['palette']]);self.assertEqual([x.upper()for x in restated['starPalette']],[x.upper()for x in page['starPalette']])
       values=s.info()['prompt']['firstPromptSource']['values'];self.assertEqual({n:values[INDICES[n]]&0xffffffff for n in page['values']},{n:v&0xffffffff for n,v in effective(page).items()}) # info prints int32 words unsigned
       frame=s.render().bytes;self.assertEqual(frame,self.expected(raw,page['values'],width,height,text))
       proof.setdefault((preset['id'],width,height),[]).append(hashlib.sha256(frame).hexdigest()[:8])
       if index%3==0:wasm.append({'width':width,'height':height,'values':{k:v for k,v in effective(page).items()if k not in('width','height','paletteCount','starPaletteCount','glyphCount')},'arrays':{k:[int(x.lstrip('#'),16)for x in page[k]]for k in('palette','starPalette')},'text':text,'timeUs':time_ms*1000,'expected':base64.b64encode(frame).decode()})
  evidence=os.environ.get('NOCTURNE_V01_EVIDENCE')
  if evidence:Path(evidence).write_text(json.dumps({f'{k[0]}@{k[1]}x{k[2]}':v for k,v in proof.items()},indent=1))
  self.assertEqual(len(proof),32)
  # The same frames from the actual WebAssembly build, each from one prompt-source of the final words.
  payload=self.out/'wasm.json';payload.write_text(json.dumps(wasm));self.assertGreater(len(wasm),200)
  subprocess.run([node_executable(),str(ROOT/'tests/first_prompt_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(payload)],check=True,timeout=600)
 def test_long_text_tail_head_and_pointer_hit_for_text_layouts(self):
  cases=[{'preset':p['id'],'width':w,'height':h,'text':LONG,'timeMs':1200,'actions':[]}for p in PRESETS for w,h in VIEWPORTS]
  pages=self.page(cases);index=0
  for preset in PRESETS:
   for width,height in VIEWPORTS:
    page=pages[index];index+=1
    with self.subTest(preset=preset['id'],width=width,height=height),self.scene()as s:
     s.command({'op':'resize','width':width,'height':height});s.command({'op':'prompt-source','values':preset['values'],**arrays(preset)});s.command({'op':'draft','text':LONG,'emitWeather':False});s.advance_to(1200000)
     raw=self.kernel(self.original,page,width,height,LONG,1200)
     if page['frame']is not None:self.assertEqual(base64.b64decode(page['frame']),raw)
     cells=self.expected(raw,page['values'],width,height,LONG);self.assertEqual(s.render().bytes,cells)
     marks=stamps(page['values'],width,height,len(LONG));info=s.info()['prompt']['firstPromptSource']
     if not marks:
      self.assertEqual([info['column'],info['row']],[-1,-1]);before=s.info()['prompt']['caret']
      s.command({'op':'pointer','phase':'down','x':10,'y':height//2,'button':0});s.command({'op':'pointer','phase':'up','x':10,'y':height//2,'button':0});self.assertEqual(s.info()['prompt']['caret'],before);continue
     shown=len(marks)-1;self.assertEqual([info['column'],info['row']],list(marks[0]))
     # Layout 3 keeps the head of the text (ribbonI), layouts 1 and 2 its tail (inputI).
     first=0 if page['values']['layout']==3 else len(LONG)-shown;self.assertEqual([info['visibleStart'],info['visibleEnd']],[first,first+shown])
     k=shown//2;x,y=marks[k];cell=s.inspect_character_cell(x,y);self.assertEqual([cell['glyph'],cell['id'],cell['index']],[ord(LONG[first+k]),NR_ID_PROMPT,first+k])
     s.command({'op':'pointer','phase':'down','x':x,'y':y,'button':0});s.command({'op':'pointer','phase':'up','x':x,'y':y,'button':0});self.assertEqual(s.info()['prompt']['caret'],first+k)
 def test_snapshot_restores_every_layout_and_modal_state(self):
  for preset in PRESETS:
   with self.subTest(preset=preset['id']):
    with self.scene()as s:
     s.command({'op':'resize','width':84,'height':28});s.command({'op':'prompt-source','values':preset['values'],**arrays(preset)});s.command({'op':'draft','text':'kept','emitWeather':False})
     s.command({'op':'prompt-source','values':{'selection':4,'valuePermille':321}});s.advance_to(1500000);frame=s.render().bytes;snap=s.snapshot()
    with self.scene()as t:
     t.restore(snap);self.assertEqual(t.render().bytes,frame);self.assertEqual(t.snapshot(),snap)
 def test_out_of_domain_layout_and_selection_reject_atomically(self):
  with self.scene()as s:
   s.command({'op':'resize','width':84,'height':28});s.command({'op':'prompt-source','values':{'layout':2}});before=s.snapshot()
   for values in({'layout':5},{'layout':-1},{'selection':6},{'modalOpen':2},{'valuePermille':1001}):
    with self.subTest(values=values):
     with self.assertRaises(ValueError):s.command({'op':'prompt-source','values':values})
     self.assertEqual(s.snapshot(),before)
 def test_widget_layouts_beyond_the_archived_extent(self):
  lifted=compile_original(self.out,'lifted',True)
  for layout,extra in((0,{'pixelMode':4}),(2,{'modalOpen':1,'selection':5}),(3,{}),(4,{})):
   values={'layout':layout,'stars':1,**extra}
   with self.subTest(layout=layout),self.scene()as s:
    s.command({'op':'resize','width':520,'height':30});s.command({'op':'prompt-source','values':values});s.command({'op':'draft','text':LONG,'emitWeather':False});s.advance_to(900000)
    q=Config();lifted.nsDefaultConfig(C.byref(q));q.values[0]=520;q.values[1]=30
    for name,value in values.items():q.values[INDICES[name]]=value
    full={n:q.values[i]for n,i in INDICES.items()}
    shown=stamps(full,520,30,len(LONG));n=max(0,len(shown)-1);text=LONG[:n]if layout==3 else LONG[len(LONG)-n:]if n else ''
    data=(C.c_uint32*max(1,len(text)))(*map(ord,text));cells=(Cell*(520*30))();self.assertEqual(lifted.nsRender(C.byref(q),900,data,len(text),cells,len(cells)),len(cells))
    self.assertEqual(s.render().bytes,self.expected(bytes(cells),full,520,30,text))
 def test_every_layout_inside_a_bounded_layer_region(self):
  """Each layout is laid out in the layer rectangle's own viewport (input row per layout), offset by its origin."""
  W,H=160,48
  for rect in({'x':5,'y':6,'width':84,'height':28},{'x':70,'y':3,'width':40,'height':12}): # full controls; controlsI's promptI fallback
   for preset in PRESETS:
    text=preset.get('text',HERO_TEXT)
    with self.subTest(rect=rect,preset=preset['id']),self.scene()as s:
     s.command({'op':'resize','width':W,'height':H});s.command({'op':'prompt-source','values':preset['values'],**arrays(preset),'layer':{'region':rect}});s.command({'op':'draft','text':text,'emitWeather':False})
     actions=[]
     for time_ms,action in((0,None),(1200,'modal'),(1300,'selection'),(2400,{'feedMs':2400}),(2500,'modal')):
      if action is not None:self.drive(s,action);actions.append(action)
      s.advance_to(time_ms*1000);page=self.page_config({'preset':preset['id'],'width':rect['width'],'height':rect['height'],'actions':actions})
      raw=self.kernel(self.original,page,rect['width'],rect['height'],text,time_ms);expected=self.expected(raw,page['values'],rect['width'],rect['height'],text)
      frame=s.render().bytes;region=b''.join(frame[((rect['y']+r)*W+rect['x'])*16:((rect['y']+r)*W+rect['x']+rect['width'])*16]for r in range(rect['height']))
      self.assertEqual(region,expected,f"{preset['id']} {actions}")
     marks=stamps(page['values'],rect['width'],rect['height'],len(text));info=s.info()['prompt']['firstPromptSource']
     if marks:
      self.assertEqual([info['column'],info['row']],[rect['x']+marks[0][0],rect['y']+marks[0][1]])
      k=len(marks)//2;x,y=rect['x']+marks[k][0],rect['y']+marks[k][1];s.command({'op':'pointer','phase':'down','x':x,'y':y,'button':0});s.command({'op':'pointer','phase':'up','x':x,'y':y,'button':0})
      first=0 if page['values']['layout']==3 else len(text)-(len(marks)-1);self.assertEqual(s.info()['prompt']['caret'],first+k) # a clipped tail starts past 0
     else:self.assertEqual([info['column'],info['row']],[-1,-1])
if __name__=='__main__':unittest.main()
