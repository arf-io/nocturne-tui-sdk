"""Actual original v0.1 kernel vs current public native prompt surface."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,base64,re,ctypes as C,hashlib,json,os,shutil,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import node_executable
class Config(C.Structure):_fields_=[('values',C.c_int32*64),('palette',C.c_uint32*8),('starPalette',C.c_uint32*8),('glyphs',C.c_uint32*32)]
class Cell(C.Structure):_fields_=[('glyph',C.c_uint32),('foreground',C.c_uint32),('background',C.c_uint32),('id',C.c_uint32)]
class FirstPromptSource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='nocturne-first-prompt-'); cls.out=Path(cls.temp.name)
  orig=ROOT/'tests/fixtures/first-prompt-v01';assert hashlib.sha256((orig/'src/nocturne.c').read_bytes()).hexdigest()=='11911d3466a9fe9a29c5c2672089c7a24fa6a288bf02296eb13aa1ffcae32302'
  lib=cls.out/'original.dylib';subprocess.run([os.environ.get('CC','cc'),'-shared','-fPIC','-O2','-I'+str(orig/'include'),str(orig/'src/nocturne.c'),'-o',str(lib)],check=True)
  cls.oracle=C.CDLL(str(lib));cls.oracle.nsDefaultConfig.argtypes=[C.POINTER(Config)];cls.oracle.nsRender.argtypes=[C.POINTER(Config),C.c_uint64,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(Cell),C.c_uint32]
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def scene(self):return NativeScene(library=os.environ.get('NOCTURNE_FIRST_LIBRARY',ROOT/'dist'/('libnocturne_native.dylib'if sys.platform=='darwin'else'libnocturne_native.so')))
 def setup(self,s,**values):
  s.command({'op':'resize','width':96,'height':40});s.command({'op':'prompt-source','values':{'layout':1,**values}})
 def oracle_frame(self,s,text,values,arrays=None):
  info=s.info();q=Config();self.oracle.nsDefaultConfig(C.byref(q));q.values[0]=96;q.values[1]=40;q.values[3]=1
  indices={x.lower().split('_')[0]+''.join(y.title()for y in x.lower().split('_')[1:]):int(i)for x,i in re.findall(r'NS_(\w+) = (\d+)',(ROOT/'tests/fixtures/first-prompt-v01/include/nocturne.h').read_text())}
  for name,value in values.items():q.values[indices[name]]=value
  for name,colors in (arrays or {}).items():
   field=getattr(q,name);q.values[{'palette':39,'starPalette':40,'glyphs':41}[name]]=len(colors)
   for i,color in enumerate(colors):field[i]=int(color.lstrip('#'),16)if isinstance(color,str)else color
  data=(C.c_uint32*len(text))(*map(ord,text));cells=(Cell*(96*40))();self.assertEqual(self.oracle.nsRender(C.byref(q),info['clock']['timeUs']//1000,data,len(text),cells,len(cells)),len(cells))
  raw=bytes(cells);actual=s.render().bytes
  # The sole fourth-word adaptation is the documented native input owner.
  expected=bytearray(raw);x=7;y=q.values[16]if q.values[16]>=0 else 20;y=min(y,39)
  for i in range(len(text)+1):struct.pack_into('<I',expected,((y*96+x+i)*16)+12,0x40000000)
  self.assertEqual(actual,bytes(expected))
  evidence=os.environ.get('NOCTURNE_FIRST_EVIDENCE')
  if evidence:
   p=Path(evidence);p.mkdir(parents=True,exist_ok=True);label=hashlib.sha256(json.dumps({'values':values,'arrays':arrays},sort_keys=True).encode()).hexdigest()[:12]+f"-{info['clock']['timeUs']}";(p/(label+'-native.cells')).write_bytes(actual);(p/(label+'-original.cells')).write_bytes(raw)
  return bytes(expected)
 def test_original_full_frames_all_cursor_modes_and_clocks(self):
  for cursor in range(4):
   with self.scene()as s:
    v={'effect':1,'stars':0,'cursorMode':cursor,'gradientPeriodMs':1800};self.setup(s,**v);s.command({'op':'draft','text':'Original prompt','emitWeather':False})
    for t in [0,100000,1200000,2400000]:
     s.advance_to(t);before=s.snapshot();self.oracle_frame(s,'Original prompt',v);self.assertEqual(s.snapshot(),before)
    self.assertEqual(s.prompt_visual_layout(),[])
 def test_current_document_long_unicode_caret_selection_and_pointer(self):
  with self.scene()as s:
   self.setup(s,stars=0);text='a'*66001+'e\u0301🪶\u202aאב\u202c終';s.command({'op':'draft','text':text,'emitWeather':False});self.assertEqual(s.info()['prompt']['text'],text)
   s.command({'op':'select','anchor':66001,'caret':66003,'unit':'grapheme'});self.assertEqual(s.selected_text(),'e\u0301');s.render()
   s.command({'op':'key','key':'Home'});self.assertEqual(s.info()['prompt']['caret'],0);s.command({'op':'key','key':'End'});self.assertEqual(s.info()['prompt']['caret'],len(text));s.command({'op':'draft','text':'abcdef','caret':4,'emitWeather':False})
   s.command({'op':'pointer','phase':'down','x':9,'y':20,'button':0});s.command({'op':'pointer','phase':'up','x':9,'y':20,'button':0});self.assertEqual(s.info()['prompt']['caret'],2)
   s.command({'op':'input','text':'Z'});self.assertEqual(s.info()['prompt']['text'],'abZcdef');snap=s.snapshot();frame=s.render().bytes;s.command({'op':'draft','text':'replace','emitWeather':False});s.restore(snap);self.assertEqual(s.render().bytes,frame);self.assertEqual(s.info()['prompt']['text'],'abZcdef')
 def test_atomic_source_config_viewport_and_snapshot_validation(self):
  with self.scene()as s:
   self.setup(s);before=s.snapshot()
   # Beyond the kernel's integer extent (see FirstPromptExtent); 513x40 and 96x257 are now admitted.
   for c in [{'op':'prompt-source','values':{'layout':5}},{'op':'resize','width':2097153,'height':40},{'op':'resize','width':96,'height':2097153},{'op':'prompt-source','values':{'cursorMode':4}},{'op':'prompt-source','glyphs':[0xd800]},{'op':'prompt-source','values':{'bogus':1}}]:
    with self.assertRaises(ValueError):s.command(c)
    self.assertEqual(s.snapshot(),before)
   raw=bytearray(before);probe=self.out/'layout.c';probe.write_text('#include "internal.h"\n#include <stdio.h>\nint main(){printf("%zu",offsetof(State,firstPromptSource));}\n');exe=self.out/'layout';subprocess.run([os.environ.get('CC','cc'),'-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(probe),'-o',str(exe)],check=True);offset=int(subprocess.check_output([str(exe)]));struct.pack_into('<I',raw,24+offset+4,1);struct.pack_into('<I',raw,20,zlib.crc32(raw[24:]));
   with self.assertRaises(ValueError):s.restore(raw)
   self.assertEqual(s.snapshot(),before)
 def test_all_original_prompt_presets(self):
  presets=json.loads((ROOT/'tests/fixtures/first-prompt-v01/presets.json').read_text())
  for preset in presets:
   if preset['values']['layout']!=1:continue
   with self.scene()as s:
    self.setup(s,**preset['values']);arrays={k:preset[k]for k in ['palette','starPalette','glyphs']if k in preset}
    s.command({'op':'prompt-source',**{k:[int(x.lstrip('#'),16)if isinstance(x,str)else x for x in v]for k,v in arrays.items()}});s.command({'op':'draft','text':'source prompt','emitWeather':False})
    for t in [0,100000,1200000,2400000]:s.advance_to(t);self.oracle_frame(s,'source prompt',preset['values'],arrays)
 def test_visible_tail_starts_on_grapheme_and_tracks_middle_caret(self):
  with self.scene()as s:
   self.setup(s,stars=0);text='e\u0301'+'a'*86;s.command({'op':'draft','text':text,'emitWeather':False});info=s.info()['prompt']['firstPromptSource'];self.assertEqual(info['visibleStart'],2);self.assertEqual(info['visibleEnd'],88);self.assertEqual(s.info()['prompt']['text'],text)
   s.command({'op':'draft','text':text,'caret':1,'emitWeather':False});info=s.info()['prompt']['firstPromptSource'];self.assertEqual(info['visibleEnd'],0);self.assertEqual(info['visibleStart'],0);s.command({'op':'input','text':'Z'});self.assertEqual(s.info()['prompt']['text'],'eZ\u0301'+'a'*86)
 def test_genuine_schema88_migrates_without_changing_frame_or_document(self):
  fixture=ROOT/'tests/fixtures/camera-graph-sky-schema88';raw=gzip.decompress((fixture/'snapshot.gz').read_bytes());frame=gzip.decompress((fixture/'frame.gz').read_bytes());self.assertEqual(struct.unpack_from('<I',raw,12)[0],0x20261088)
  with self.scene()as s:
   currentSchema=struct.unpack_from('<I',s.snapshot(),12)[0];s.restore(raw);self.assertEqual(s.render().bytes,frame);self.assertIsNone(s.info()['prompt']['firstPromptSource']);self.assertEqual(struct.unpack_from('<I',s.snapshot(),12)[0],currentSchema);source=s.info()['prompt']['text'];s.command({'op':'prompt-source'});s.command({'op':'prompt-source','enabled':False});self.assertEqual(s.info()['prompt']['text'],source);self.assertEqual(s.render().bytes,frame)
 def test_original_prompt_presets_have_normal_gallery_routes(self):
  sys.path.insert(0,str(ROOT/'examples'));from gallery_cases import build_cases
  presets=json.loads((ROOT/'tests/fixtures/first-prompt-v01/presets.json').read_text());wanted=presets;cases={p['id']:p for p in build_cases()}
  for preset in wanted:
   recipe=cases['first-prompt-'+preset['id']];command=next(x for x in recipe['commands']if x['op']=='prompt-source');self.assertEqual(command['values'],preset['values']);self.assertEqual(recipe['firstPromptPreset'],command);self.assertTrue(recipe['demo'])
 def test_actual_wasm_original_frames_and_long_current_document(self):
  rows=[]
  for cursor in range(4):
   with self.scene()as s:
    values={'effect':1,'stars':0,'cursorMode':cursor,'gradientPeriodMs':1800};self.setup(s,**values);s.command({'op':'draft','text':'Original prompt','emitWeather':False})
    for time in [0,100000,1200000,2400000]:
     s.advance_to(time);rows.append({'values':values,'timeUs':time,'expected':base64.b64encode(self.oracle_frame(s,'Original prompt',values)).decode()})
  presets=json.loads((ROOT/'tests/fixtures/first-prompt-v01/presets.json').read_text())
  for preset in presets:
   if preset['values']['layout']!=1:continue
   with self.scene()as s:
    self.setup(s,**preset['values']);arrays={k:[int(x.lstrip('#'),16)if isinstance(x,str)else x for x in preset[k]]for k in ['palette','starPalette','glyphs']if k in preset};s.command({'op':'prompt-source',**arrays});s.command({'op':'draft','text':'source prompt','emitWeather':False})
    for time in [0,100000,1200000,2400000]:
     s.advance_to(time);rows.append({'values':preset['values'],'arrays':arrays,'text':'source prompt','timeUs':time,'expected':base64.b64encode(self.oracle_frame(s,'source prompt',preset['values'],arrays)).decode()})
  payload=self.out/'wasm-oracle.json';payload.write_text(json.dumps(rows));subprocess.run([node_executable(),str(ROOT/'tests/first_prompt_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(payload)],check=True,timeout=120)
 def test_reserved_config_and_invalid_inactive_arrays_reject(self):
  with self.scene()as s:
   self.setup(s);before=s.snapshot();probe=self.out/'layout-extra.c';probe.write_text('#include "internal.h"\n#include <stdio.h>\nint main(){printf("%zu",offsetof(State,firstPromptSource));}\n');exe=self.out/'layout-extra';subprocess.run([os.environ.get('CC','cc'),'-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(probe),'-o',str(exe)],check=True);offset=int(subprocess.check_output([str(exe)]))
   for word,value in [(2+63,1),(2+64+7,0xffffffff),(2+80+31,0xd800)]:
    raw=bytearray(before);struct.pack_into('<I',raw,24+offset+word*4,value);struct.pack_into('<I',raw,20,zlib.crc32(raw[24:]))
    with self.assertRaises(ValueError):s.restore(raw)
    self.assertEqual(s.snapshot(),before)
 def test_disable_preserves_default_frame_and_recovery_modal(self):
  with self.scene()as s:
   s.command({'op':'resize','width':96,'height':40});s.command({'op':'draft','text':'retained','emitWeather':False});base=s.render().bytes;s.command({'op':'prompt-source'});original=s.render().bytes;self.assertNotEqual(base,original);s.command({'op':'key','key':'F1'});self.assertNotEqual(s.render().bytes,original);self.assertEqual(s.info()['inputOwner'],'modal');s.command({'op':'key','key':'Escape'});self.assertEqual(s.render().bytes,original);s.command({'op':'prompt-source','enabled':False});self.assertEqual(s.render().bytes,base)
EXTENT=2097152 # 2**21: (extent-1)*1024+896 is the kernel's largest int32 Q10 sample coordinate.
CELLS=2147483647 # The kernel indexes y*width+x and counts width*height in int32.
NR_ID_PROMPT=0x40000000
INDICES={x.lower().split('_')[0]+''.join(y.title()for y in x.lower().split('_')[1:]):int(i)for x,i in re.findall(r'NS_(\w+) = (\d+)',(ROOT/'tests/fixtures/first-prompt-v01/include/nocturne.h').read_text())}
LONG=''.join(chr(33+i%94)for i in range(3000)) # Distinct printable cycle: any column slip is visible.
def compile_original(out,name,lifted):
 """Compile the archived v0.1 source as the oracle.

 With lifted=True the copy changes exactly three constants: MAX_VALUES[0..1]
 (512,256) and NS_MAX_TEXT (512). They bound the standalone library's caller
 arrays and enter no equation, table or function body, so the copy evaluates
 the unchanged archived equations at larger extents. It is built from the
 fixture, never from the implementation under test."""
 orig=ROOT/'tests/fixtures/first-prompt-v01';tree=out/name
 shutil.copytree(orig/'src',tree/'src');shutil.copytree(orig/'include',tree/'include')
 assert hashlib.sha256((tree/'src/nocturne.c').read_bytes()).hexdigest()=='11911d3466a9fe9a29c5c2672089c7a24fa6a288bf02296eb13aa1ffcae32302'
 if lifted:
  for path,old,new in [(tree/'src/defaults.inc','MAX_VALUES[] = {512,256,',f'MAX_VALUES[] = {{{EXTENT},{EXTENT},'),(tree/'include/nocturne.h','#define NS_MAX_TEXT 512\n',f'#define NS_MAX_TEXT {EXTENT}\n')]:
   text=path.read_text();assert text.count(old)==1,(path,old);path.write_text(text.replace(old,new,1))
 lib=out/(name+'.so');subprocess.run([os.environ.get('CC','cc'),'-shared','-fPIC','-O2','-I'+str(tree/'include'),str(tree/'src/nocturne.c'),'-o',str(lib)],check=True)
 oracle=C.CDLL(str(lib));oracle.nsDefaultConfig.argtypes=[C.POINTER(Config)];oracle.nsRender.argtypes=[C.POINTER(Config),C.c_uint64,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(Cell),C.c_uint32];oracle.nsRender.restype=C.c_int32
 return oracle
def geometry(width,height,length,focus=-1):
 """Documented layout1 view: a tail ending at the caret, input at column x+2 of the focus row."""
 x=5 if width>12 else 0;room=max(0,width-x-4);return max(0,length-room),length,x+2,height//2 if focus<0 else min(focus,height-1)
class FirstPromptExtent(unittest.TestCase):
 """The source surface follows the native viewport beyond the archived 512x256 library ABI."""
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='nocturne-first-prompt-extent-');cls.out=Path(cls.temp.name)
  cls.original=compile_original(cls.out,'original',False);cls.lifted=compile_original(cls.out,'lifted',True)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def scene(self):return NativeScene(library=os.environ.get('NOCTURNE_FIRST_LIBRARY',ROOT/'dist'/('libnocturne_native.dylib'if sys.platform=='darwin'else'libnocturne_native.so')))
 def source(self,s,width,height,values,arrays=None,text=LONG):
  s.command({'op':'resize','width':width,'height':height});s.command({'op':'prompt-source','enabled':False});s.command({'op':'prompt-source','values':{'layout':1,**values}})
  if arrays:s.command({'op':'prompt-source',**arrays})
  if text is not None:s.command({'op':'draft','text':text,'emitWeather':False})
 def expected(self,oracle,width,height,text,values,time_us,arrays=None):
  q=Config();oracle.nsDefaultConfig(C.byref(q));q.values[0]=width;q.values[1]=height;q.values[3]=1
  for name,value in values.items():q.values[INDICES[name]]=value
  for name,items in (arrays or {}).items():
   field=getattr(q,name);q.values[{'palette':39,'starPalette':40,'glyphs':41}[name]]=len(items)
   for i,item in enumerate(items):field[i]=item
  start,end,column,row=geometry(width,height,len(text),q.values[16]);tail=[ord(ch)for ch in text[start:end]]
  data=(C.c_uint32*max(1,len(tail)))(*tail);cells=(Cell*(width*height))()
  self.assertEqual(oracle.nsRender(C.byref(q),time_us//1000,data,len(tail),cells,len(cells)),len(cells))
  # The sole fourth-word adaptation: native input cells carry the prompt owner ID.
  expected=bytearray(bytes(cells))
  for i in range(end-start+1):struct.pack_into('<I',expected,((row*width+column+i)*16)+12,NR_ID_PROMPT)
  return bytes(expected)
 def test_kernel_include_remains_the_archived_source(self):
  orig=ROOT/'tests/fixtures/first-prompt-v01';proof=json.loads((orig/'PROVENANCE.json').read_text())['kernel']
  kernel=(ROOT/'src/first_prompt_kernel.inc').read_bytes();self.assertEqual(hashlib.sha256(kernel).hexdigest(),proof['adaptedSha256'])
  archived=(orig/'src/nocturne.c').read_text().splitlines();adapted=kernel.decode().splitlines();self.assertEqual(len(archived),len(adapted))
  self.assertEqual([(a,b)for a,b in zip(archived,adapted)if a!=b],[('#include "nocturne.h"','#include "../../include/nocturne.h"'),('#include "defaults.inc"','#include "../../src/defaults.inc"'),('#include "sine.inc"','#include "../../src/sine.inc"')])
 def test_extent_loop_is_the_archived_render_loop_without_its_range_checks(self):
  def function(lines,head):start=lines.index(head);return lines[start:lines.index('}',start)+1]
  signature='(const NsConfig *config, uint64_t motionMs, const uint32_t *text, uint32_t textLength, NsCell *cells, uint32_t capacity)'
  archived=function((ROOT/'src/first_prompt_kernel.inc').read_text().splitlines(),'int32_t nsRender'+signature)
  extent=function((ROOT/'src/first_prompt.c').read_text().splitlines(),'static int32_t extentRender'+signature)
  self.assertEqual(len(archived),len(extent))
  self.assertEqual([(a,b)for a,b in zip(archived,extent)if a!=b],[('int32_t nsRender'+signature,'static int32_t extentRender'+signature),('  if (nsValidateConfig(config))','  if (validateSource(config))'),('  if ((textLength > NS_MAX_TEXT) || ((!text) && textLength))','  if ((!text) && textLength)')])
 def test_viewports_beyond_512x256_paint_original_frames_at_documented_geometry(self):
  values={'effect':1,'stars':1,'cursorMode':3,'gradientPeriodMs':1800}
  for width,height in [(512,256),(513,40),(96,257),(1024,300),(2048,64)]:
   with self.subTest(width=width,height=height),self.scene()as s:
    self.source(s,width,height,values);s.advance_to(1200000);start,end,column,row=geometry(width,height,len(LONG))
    info=s.info()['prompt']['firstPromptSource'];self.assertEqual([info['visibleStart'],info['visibleEnd'],info['column'],info['row']],[start,end,column,row]);self.assertEqual(info['values'][:2],[width,height])
    before=s.snapshot();clock=s.info()['clock'];intents=s.info()['intents'];frame=s.render().bytes;cells=list(struct.iter_unpack('<4I',frame))
    # Every visible tail scalar is painted at the reported row/column, including tails over 512 scalars.
    self.assertEqual([cells[row*width+column+k][0]for k in range(end-start)],[ord(ch)for ch in LONG[start:end]])
    self.assertEqual({cells[row*width+column+k][3]for k in range(end-start+1)},{NR_ID_PROMPT})
    self.assertEqual(frame,self.expected(self.lifted,width,height,LONG,values,1200000))
    if width<=512 and height<=256:self.assertEqual(frame,self.expected(self.original,width,height,LONG,values,1200000))
    # Rendering is pure: identical repeat, no clock, intention or authoritative state change.
    self.assertEqual(s.render().bytes,frame);self.assertEqual(s.snapshot(),before);self.assertEqual(s.info()['clock'],clock);self.assertEqual(s.info()['intents'],intents);self.assertEqual(s.prompt_visual_layout(),[])
 def test_extent_loop_matches_archived_equations_for_every_pixel_mode_and_branch(self):
  palette=[0x416d78,0x896273,0x2a3b4c,0xd0c0b0];stars=[0xffeedd,0x99aabb,0x334455]
  cases=[({'pixelMode':p,'stars':st,'effect':e,'densityPermille':400},None)for p in range(5)for st in (0,1)for e in (2,5)]
  cases+=[({'effect':e,'colorMode':m,'stars':1},{'palette':palette})for e in range(6)for m in range(3)]
  cases+=[({'glyphSet':g,'stars':1,'densityPermille':1000},{'glyphs':[0x2726,0x2a,0x2219],'starPalette':stars})for g in range(5)]
  cases+=[({'cursorMode':m},None)for m in range(4)]
  cases+=[({'focusRow':f,'promptBands':1,'originX':o,'originY':-o,'scaleCells':sc,'cellAspectPermille':a,'grainPermille':1000,'hueStepDegrees':-17,'hueDegreesPerSecond':90,'phaseDegrees':45,'angleDegrees':300,'waveAmplitudePermille':2000,'effect':3},None)for f,o,sc,a in [(3,1000000,2,500),(255,-1000000,512,4000),(0,777,7,1000)]]
  cases+=[({'motion':0,'pixelMode':4,'effect':5},None)]
  for width,height in [(520,24),(24,300)]:
   with self.scene()as s:
    s.command({'op':'resize','width':width,'height':height});s.advance_to(2468000);time_us=s.info()['clock']['timeUs']
    for values,arrays in cases:
     with self.subTest(width=width,height=height,values=values,arrays=arrays):
      self.source(s,width,height,values,arrays,LONG[:700]);self.assertEqual(s.render().bytes,self.expected(self.lifted,width,height,LONG[:700],values,time_us,arrays))
 def test_input_hit_and_character_index_beyond_column_512(self):
  with self.scene()as s:
   self.source(s,1024,40,{'stars':0});start,end,column,row=geometry(1024,40,len(LONG));frame=s.render();k=700
   cell=s.inspect_character_cell(column+k,row);self.assertEqual([cell['glyph'],cell['id'],cell['index']],[ord(LONG[start+k]),NR_ID_PROMPT,start+k])
   s.command({'op':'pointer','phase':'down','x':column+k,'y':row,'button':0});s.command({'op':'pointer','phase':'up','x':column+k,'y':row,'button':0});self.assertEqual(s.info()['prompt']['caret'],start+k)
   info=s.info()['prompt']['firstPromptSource'];self.assertEqual([info['visibleStart'],info['visibleEnd']],[start+k-(end-start),start+k])
   s.command({'op':'input','text':'Z'});self.assertEqual(s.info()['prompt']['text'],LONG[:start+k]+'Z'+LONG[start+k:]);self.assertEqual(s.info()['prompt']['caret'],start+k+1)
 def test_typing_weather_beyond_column_512_preserves_the_prompt_row(self):
  text='q'*597;weather={'op':'prompt-appearance','weather':{'style':'nova','intensity':1,'lifeMs':1800,'speed':12}}
  with self.scene()as live,self.scene()as quiet:
   for s in (live,quiet):self.source(s,1024,40,{'stars':0},text=None);s.command(weather)
   live.command({'op':'draft','text':text,'emitWeather':False});live.command({'op':'input','text':'abc'});quiet.command({'op':'draft','text':text+'abc','emitWeather':False})
   self.assertEqual(live.info()['prompt']['text'],quiet.info()['prompt']['text']);self.assertGreater(live.info()['prompt']['appearance']['weather']['eventCount'],0);self.assertEqual(quiet.info()['prompt']['appearance']['weather']['eventCount'],0)
   live.advance_to(150000);quiet.advance_to(150000);a=list(struct.iter_unpack('<4I',live.render().bytes));b=list(struct.iter_unpack('<4I',quiet.render().bytes))
   start,end,column,row=geometry(1024,40,600);left,right=column-2,column+end-start;self.assertGreater(right-left+1,512)
   changed=[(i//1024,i%1024)for i,(p,q) in enumerate(zip(a,b))if p!=q]
   # Weather paints beyond column 512, including the prompt row after the cursor, but never the protected input span.
   self.assertTrue(any(c>512 and r!=row for r,c in changed));self.assertTrue(any(r==row and c>right for r,c in changed))
   self.assertEqual(a[row*1024+left:row*1024+right+1],b[row*1024+left:row*1024+right+1])
 def test_render_memory_shortfall_reports_storage_diagnostic_without_disabling(self):
  with self.scene()as s:
   self.source(s,1024,300,{'stars':0});lib,ctx=s._lib,s._context;required,capacity=lib.nrRenderMemorySize(ctx),lib.nrRenderMemoryCapacity(ctx);self.assertGreater(required,capacity);before=s.snapshot()
   self.assertEqual(lib.nrRender(ctx),0);self.assertEqual(lib.nrError(ctx),b'Viewport render memory required')
   small=C.create_string_buffer(1<<20);self.assertEqual(lib.nrSetRenderMemory(ctx,C.c_void_p((C.addressof(small)+7)&~7),(1<<20)-8),-1);self.assertEqual(lib.nrRenderMemoryCapacity(ctx),capacity)
   pointer=json.dumps({'op':'pointer','phase':'down','x':20,'y':150,'button':0}).encode();self.assertEqual(lib.nrCommand(ctx,pointer,len(pointer)),-1);self.assertEqual(lib.nrError(ctx),b'Viewport render memory required')
   self.assertEqual(s.snapshot(),before);self.assertEqual(s.info()['prompt']['firstPromptSource']['values'][:2],[1024,300])
   cells=list(struct.iter_unpack('<4I',s.render().bytes));start,end,column,row=geometry(1024,300,len(LONG))
   self.assertEqual([cells[row*1024+column+k][0]for k in range(end-start)],[ord(ch)for ch in LONG[start:end]])
 def test_extent_snapshot_restores_identical_frame(self):
  values={'effect':5,'stars':1,'pixelMode':1}
  with self.scene()as s:
   self.source(s,1024,300,values);s.advance_to(700000);frame=s.render().bytes;snap=s.snapshot();info=s.info()['prompt']['firstPromptSource']
  with self.scene()as t:
   t.restore(snap);self.assertEqual(t.info()['prompt']['firstPromptSource'],info);self.assertEqual(t.render().bytes,frame);self.assertEqual(t.snapshot(),snap)
  self.assertEqual(frame,self.expected(self.lifted,1024,300,LONG,values,700000))
 def test_representation_limits_admit_at_bound_and_reject_beyond_atomically(self):
  probe=self.out/'viewport.c';probe.write_text('#include "internal.h"\n#include <stdio.h>\nint main(){printf("%zu %zu",offsetof(State,width),offsetof(State,height));}\n');exe=self.out/'viewport'
  subprocess.run([os.environ.get('CC','cc'),'-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(probe),'-o',str(exe)],check=True);widthAt,heightAt=map(int,subprocess.check_output([str(exe)]).split())
  admitted=[(EXTENT,1),(1,EXTENT),(EXTENT,1023),(46340,46341)];rejected=[(EXTENT+1,1),(1,EXTENT+1),(EXTENT,1024),(46341,46341)]
  self.assertTrue(all(w*h<=CELLS for w,h in admitted));self.assertTrue(all(w>EXTENT or h>EXTENT or w*h>CELLS for w,h in rejected))
  with self.scene()as s:
   s.command({'op':'resize','width':96,'height':40});s.command({'op':'prompt-source'})
   for width,height in admitted:
    s.command({'op':'resize','width':width,'height':height});self.assertEqual(s.info()['prompt']['firstPromptSource']['values'][:2],[width,height])
   for width,height in rejected:
    with self.subTest(width=width,height=height):
     before=s.snapshot()
     with self.assertRaises(ValueError)as caught:s.command({'op':'resize','width':width,'height':height})
     self.assertEqual(str(caught.exception),'State invariant rejected');self.assertEqual(s.snapshot(),before)
   s.command({'op':'resize','width':EXTENT,'height':1});limit=s.snapshot()
  with self.scene()as t:
   t.restore(limit);self.assertEqual(t.info()['prompt']['firstPromptSource']['values'][:2],[EXTENT,1]);self.assertEqual(t.snapshot(),limit)
   for word,value in [(widthAt,EXTENT+1),(heightAt,1024)]:
    raw=bytearray(limit);struct.pack_into('<I',raw,24+word,value);struct.pack_into('<I',raw,20,zlib.crc32(raw[24:]))
    with self.assertRaises(ValueError):t.restore(bytes(raw))
    self.assertEqual(t.snapshot(),limit)
  # The same viewports remain representable without the source surface; only its kernel bounds them.
  with self.scene()as s:
   s.command({'op':'resize','width':EXTENT,'height':1});plain=s.snapshot()
   for word,value in [(widthAt,EXTENT+1),(heightAt,1024)]:
    raw=bytearray(plain);struct.pack_into('<I',raw,24+word,value);struct.pack_into('<I',raw,20,zlib.crc32(raw[24:]));s.restore(bytes(raw));s.restore(plain)
   for width,height in [(EXTENT+1,1),(EXTENT,1024)]:
    s.command({'op':'resize','width':width,'height':height});before=s.snapshot()
    with self.assertRaises(ValueError)as caught:s.command({'op':'prompt-source'})
    self.assertEqual(str(caught.exception),'Prompt config or viewport is outside source ABI');self.assertEqual(s.snapshot(),before)
 def test_actual_wasm_frames_beyond_512x256_purity_and_render_memory(self):
  values={'effect':1,'stars':1,'cursorMode':3,'gradientPeriodMs':1800};rows=[]
  for width,height in [(1024,300),(2048,64)]:
   rows.append({'width':width,'height':height,'values':values,'text':LONG,'timeUs':1200000,'geometry':list(geometry(width,height,len(LONG))),'expected':base64.b64encode(self.expected(self.lifted,width,height,LONG,values,1200000)).decode()})
  payload=self.out/'wasm-extent.json';payload.write_text(json.dumps({'extent':rows}))
  subprocess.run([node_executable(),str(ROOT/'tests/first_prompt_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(payload)],check=True,timeout=300)
if __name__=='__main__':unittest.main()
