"""Original Stage scene beyond the archived 512x256 library extent (SDK-8).

The oracle is the retained original Studio library in legacy/atelier-v0.5. Its
Stage sources are byte-identical to the repository-root src/ and include/ files
that native/src/source_stage_scene.c consumes. Compiled unchanged it reproduces
the archived source-stage fixture frames. A copy with only its extent constants
lifted evaluates the same equations at larger viewports.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C, gzip, hashlib, json, math, os, shutil, struct, subprocess, tempfile, unittest, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import node_executable
from native.tests.test_source_stage_queries import FIX, scene_command, component
from native.tests.test_source_stage_public_integration import source_node, stage_command

LIB=Path(os.environ.get('NOCTURNE_STAGE_LIBRARY',str(ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'))))
LEGACY=REPO/'legacy/atelier-v0.5'
CUSTODY={
 'src/nocturne.c':'997f5baf3d47be76504c55a817842ab9dcfe8b1bf2cd11463b111ca66da4f745',
 'src/defaults.inc':'5b3705655b10cb99d76b2766bd40e9210cfb2b4fb5cc98e0fd7b4d49dfd6963b',
 'src/sine.inc':'4b953da325588655fe63eb700dff0aa78c32274e048de36f9daf966d50677d96',
 'src/ok_color.inc':'9a2bd7e5fc4c7824140467160ee4676fc51ed5dac2bd9cc412fed1ac963c3833',
 'src/ok_tables.inc':'d0bd25e582443b1f308d4d70b54564ee507d5a996a9e58531737ace141f1e96f',
 'src/studio.inc':'8fbb4e3b7efef930b21a338e70339e137f0d1f3286437973ed11543d6b8a1766',
 'src/studio_defaults.inc':'9b2c5afba73c1bd4fe77fb9c0dcb4182cd977f4a31a9b2ad0343517a979c8a04',
 'src/studio_widgets.inc':'fa806b7d8877119399c75a207d98e97225a6b866da405963a9c70ce2c4fe8cef',
 'include/nocturne.h':'cf591200d62adc38b6f848d3dfed3d0bb5d81afd6515e9d1770ecc217ab0b219',
 'include/nocturne_studio.h':'8018936cc86106f5e09d445b2d8ecb0407daa169a3110bce75b1b33292cf2e62',
}
# The Stage sources the native port includes or retains from the repository root.
ROOT_STAGE=('src/studio.inc','src/studio_defaults.inc','src/studio_widgets.inc','include/nocturne_studio.h')
INT32_MAX=2**31-1;UINT32_MAX=2**32-1
EVENT_Q8=1048576 # Admitted impulse coordinates: +-4096 cells in Q8.
ASPECT=4000 # Largest cellAspect, thousandths.
# Representation limits of the original Stage arithmetic, independent of config:
# stSample forms x-e[0] and (int)((y-e[1])*cellAspect/1000) in int32 for cell
# samples at Q8 (w-1)*256+64 and (h-1)*256+96 against any admitted impulse.
MAX_WIDTH=8384512
MAX_HEIGHT=2093056
LIFTED_ACTIVE=16384 # Lifted oracle scratch; every case asserts its need stays below.
LIFTS=[('src/studio_defaults.inc','ST_MAX[] = {512,256,',f'ST_MAX[] = {{{MAX_WIDTH},{MAX_HEIGHT},'),
       ('src/studio.inc','NsImpulse active[512];',f'NsImpulse active[{LIFTED_ACTIVE}];'),
       ('src/studio.inc','if(count>=512)return count;',f'if(count>={LIFTED_ACTIVE})return count;')]
NAMES=["width","height","pattern","focusMode","focusX","focusY","periodMs","saturation","brightness","speedFalloff","saturationFalloff","brightnessFalloff","cellAspect","scale","angle","pivotX","pivotY","rotationPeriodMs","rotationMode","swing","phase","pixelMode","seed","baseColor","inkColor","paletteCount","gradientWrap","interpolation","colorMode","hueOffset","stars","starDensity","starMinMs","starRangeMs","starDuty","starPeak","starGlyphCount","starColorCount","novaChance","novaCycleMs","novaDurationMs","novaGlyphCount","rippleSpeed","rippleWidth","rippleLifeMs","rippleOpacity","rippleRings","motion","quantize","originX","originY","waveAmplitude","starAttack","reverse"]
COUNTS={'palette':25,'starPalette':37,'glyphs':36,'novaGlyphs':41};CAPS={'palette':32,'starPalette':32,'glyphs':32,'novaGlyphs':16}
NOVA=(0x2726,0x2727) # Nova glyphs absent from the star glyph set, so nova cells are identifiable.
ARRAYS={'palette':[0x28304f,0x785c89,0x367876,0xae7357,0x504565],'starPalette':[0xb6a4c4,0x9fb9b0,0xc7bca7,0x9cacca,0xc6a0aa,0xadbdbb],
        'glyphs':[ord('.'),0xb7,0x2219,0x22c5,0x2801,0x2802,0x2804,0x2840,0x2808,0x2810,0x2820,0x2880],'novaGlyphs':list(NOVA)}
# Every 32x16 world tile carries a live nova; the origin makes both edge tiles partial.
LOAD={'novaChance':1000,'novaCycleMs':1000,'novaDurationMs':3600,'originX':-31,'originY':-10}
TIME_MS=40000

class Config(C.Structure):_fields_=[('values',C.c_int32*64),('palette',C.c_uint32*32),('starPalette',C.c_uint32*32),('glyphs',C.c_uint32*32),('novaGlyphs',C.c_uint32*16)]
class Impulse(C.Structure):_fields_=[('values',C.c_int32*8)]
class Node(C.Structure):_fields_=[('values',C.c_int32*32)]
class Cell(C.Structure):_fields_=[('glyph',C.c_uint32),('foreground',C.c_uint32),('background',C.c_uint32),('flags',C.c_uint32)]

def compile_original(out,name,lifted):
 """Compile the retained original Studio library as the oracle.

 With lifted=True the copy changes exactly three strings. ST_MAX[0..1]
 (512,256) is the declared extent of the standalone library's NsStageConfig.
 The other two are its 512-entry active-impulse scratch: the stack array in
 nsStageRender and the matching cap in stActive. Within 512x256 that scratch
 never holds more than 128 events plus one nova per 32x16 world tile, at most
 17x17 tiles, 417 entries, so the cap cannot fire there. None of the three
 enters an equation, table or function body. The copy is built from the
 retained source, never from the implementation under test."""
 tree=out/name
 for part in ('src','include'):shutil.copytree(LEGACY/part,tree/part)
 for rel,digest in CUSTODY.items():
  if hashlib.sha256((tree/rel).read_bytes()).hexdigest()!=digest:raise AssertionError('retained original custody mismatch: '+rel)
 if lifted:
  for rel,old,new in LIFTS:
   path=tree/rel;text=path.read_text()
   if text.count(old)!=1:raise AssertionError((rel,old))
   path.write_text(text.replace(old,new,1))
 lib=out/(name+'.so')
 subprocess.run([os.environ.get('CC','cc'),'-std=c11','-shared','-fPIC','-O2','-I'+str(tree/'include'),str(tree/'src/nocturne.c'),'-o',str(lib)],check=True)
 oracle=C.CDLL(str(lib))
 oracle.nsStageDefaults.argtypes=[C.POINTER(Config)];oracle.nsStageValidate.argtypes=[C.POINTER(Config)];oracle.nsStageValidate.restype=C.c_int32
 oracle.nsStageRender.argtypes=[C.POINTER(Config),C.c_uint64,C.POINTER(Impulse),C.c_uint32,C.POINTER(Node),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_int32),C.c_uint32,C.POINTER(Cell),C.c_uint32]
 oracle.nsStageRender.restype=C.c_int32
 return oracle

def signed(word):return word-(1<<32) if word&0x80000000 else word
def impulse(e):
 """Original event words: JS Math.round Q8 position, strength, kind, unsigned time words, id."""
 at=e['atMs'];return [math.floor(e['x']*256+.5),math.floor(e['y']*256+.5),e.get('strength',1000),e.get('kind',0),signed(at&0xffffffff),signed(at>>32),e.get('id',0),0]
def events_for(width,height,count=128,time_ms=TIME_MS):
 """Live ripples and novas spread over the whole viewport, including past column 512 and row 256."""
 return [{'x':(i*97)%(width+200)-100+(i%2)*.5,'y':(i*53)%(height+40)-20+(i%4)*.25,'atMs':time_ms-(i*23)%3000,'strength':400+(i*7)%601,'kind':i%2,'id':i*1000+7} for i in range(count)]
def spec(width,height,values=None,events=(),time_ms=TIME_MS,nodes=(),arrays=None):
 return {'width':width,'height':height,'values':dict(values or {}),'events':list(events),'timeMs':time_ms,'nodes':list(nodes),'arrays':dict(ARRAYS if arrays is None else arrays)}
def stage(case):return {'op':'source-stage','timeMs':case['timeMs'],'config':{'values':dict(case['values']),**case['arrays']},'events':case['events']}
def commands(case,enable_first=False):
 view={'op':'resize','width':case['width'],'height':case['height']}
 out=[{'op':'reset'},{'op':'environment','presentation':'canvas','stars':0},{'op':'prompt','active':False},{'op':'floor','enabled':False,'visible':False}]
 out+=[stage(case),view] if enable_first else [view,stage(case)]
 return out+[stage_command(i+1,kind,**values) for i,(kind,values) in enumerate(case['nodes'])]
def configure(s,case,enable_first=False):
 for command in commands(case,enable_first):s.command(command)

def oracle_frame(oracle,case):
 q=Config();oracle.nsStageDefaults(C.byref(q));q.values[0]=case['width'];q.values[1]=case['height']
 for name,value in case['values'].items():q.values[NAMES.index(name)]=value
 for name,items in case['arrays'].items():
  field=getattr(q,name)
  for i in range(CAPS[name]):field[i]=items[i] if i<len(items) else 0
  q.values[COUNTS[name]]=len(items)
 if oracle.nsStageValidate(C.byref(q)):raise AssertionError('original rejects the oracle config')
 events=(Impulse*max(1,len(case['events'])))()
 for i,e in enumerate(case['events']):events[i].values[:]=impulse(e)
 rows,text,data=[],[],[]
 for kind,values in case['nodes']:
  row,t,d=source_node(kind,**values);row[17],row[19]=len(text),len(data);text+=[ord(ch) for ch in t];data+=list(d);rows.append(row)
 nodes=(Node*max(1,len(rows)))()
 for i,row in enumerate(rows):nodes[i].values[:]=row
 words=(C.c_uint32*max(1,len(text)))(*text);scalars=(C.c_int32*max(1,len(data)))(*data)
 count=case['width']*case['height'];cells=(Cell*count)()
 result=oracle.nsStageRender(C.byref(q),case['timeMs'],events,len(case['events']),nodes,len(rows),words,len(text),scalars,len(data),cells,count)
 if result!=count:raise AssertionError(('original render failed',result))
 return bytes(cells)

def hash32(v):
 v^=v>>16;v=v*0x7feb352d&UINT32_MAX;v^=v>>15;v=v*0x846ca68b&UINT32_MAX;return v^(v>>16)
def tile_hash(seed,x,y):return hash32((seed^(x*0x9e3779b9)^(y*0x85ebca6b))&UINT32_MAX)
def tiles(width,height,ox,oy):
 return [(tx,ty) for ty in range(oy//16,(oy+height-1)//16+1) for tx in range(ox//32,(ox+width-1)//32+1)]
def live(case,e):
 """stActive keeps an event while its age is below the nova duration or ripple life (defaults 3600/3200)."""
 age=case['timeMs']-e['atMs'];v=case['values']
 return 0<=age<(v.get('novaDurationMs',3600) if e.get('kind',0) else v.get('rippleLifeMs',3200))
def needed(case):
 """Entries stActive appends: live events, then one live nova per world tile."""
 ox,oy=case['values'].get('originX',0),case['values'].get('originY',0)
 return sum(live(case,e) for e in case['events'])+len(tiles(case['width'],case['height'],ox,oy))
def tile_nova(seed,ox,oy,tx,ty):
 """Documented nova geometry: tile (tx,ty) bursts at world cell (tx*32+1+h%30, ty*16+1+h%14)."""
 h=tile_hash(seed^14593,tx,ty);return tx*32+1+hash32(h^7)%30-ox,ty*16+1+hash32(h^19)%14-oy
def nova_cells(case):
 v=case['values'];ox,oy,seed=v.get('originX',0),v.get('originY',0),v.get('seed',7319)
 out={tile_nova(seed,ox,oy,tx,ty) for tx,ty in tiles(case['width'],case['height'],ox,oy)}
 trunc=lambda q:-(-q//256) if q<0 else q//256 # C integer division
 for e in case['events']:
  if e.get('kind',0) and live(case,e):x,y=impulse(e)[:2];out.add((trunc(x),trunc(y)))
 return {(x,y) for x,y in out if 0<=x<case['width'] and 0<=y<case['height']}
def cells(frame):return list(struct.iter_unpack('<4I',frame))
def colors(frame):return b''.join(frame[i:i+12] for i in range(0,len(frame),16))

class SourceStageExtent(unittest.TestCase):
 """The enabled original Stage scene follows the native viewport to its arithmetic limits."""
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='nocturne-source-stage-extent-');cls.out=Path(cls.temp.name)
  cls.original=compile_original(cls.out,'original',False);cls.lifted=compile_original(cls.out,'lifted',True)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def scene(self):return NativeScene(library=LIB)
 def oracle(self,case):
  self.assertLess(needed(case),LIFTED_ACTIVE,'lifted oracle scratch must never truncate')
  return oracle_frame(self.lifted,case)
 def assertFrame(self,actual,expected,label,colors_only=False):
  """Every cell: all four words, or glyph/foreground/background where nodes carry native ownership IDs."""
  self.assertEqual(len(actual),len(expected),label)
  width=12 if colors_only else 16
  a=[actual[i:i+width] for i in range(0,len(actual),16)];b=[expected[i:i+width] for i in range(0,len(expected),16)]
  bad=[i for i in range(len(a)) if a[i]!=b[i]]
  if bad:self.fail(f'{label}: {len(bad)} cells differ, first {bad[:3]} actual {[struct.unpack("<%dI"%(width//4),a[i]) for i in bad[:3]]} expected {[struct.unpack("<%dI"%(width//4),b[i]) for i in bad[:3]]}')
 def assertNovaGeometry(self,frame,case):
  """Exactly the documented live-nova cells, and no others, show nova glyphs."""
  w=case['width'];actual={(i%w,i//w) for i,c in enumerate(cells(frame)) if c[0] in NOVA};expected=nova_cells(case)
  self.assertEqual(sorted(expected-actual),[],'documented novas missing');self.assertEqual(sorted(actual-expected),[],'undocumented nova glyphs')
  return expected

 def test_oracle_is_the_retained_original_and_reproduces_archived_frames(self):
  for rel in ROOT_STAGE:
   with self.subTest(source=rel):self.assertEqual((REPO/rel).read_bytes(),(LEGACY/rel).read_bytes())
  lifted=self.out/'lifted';changed=[]
  for rel in CUSTODY:
   old,new=(LEGACY/rel).read_text().splitlines(),(lifted/rel).read_text().splitlines()
   self.assertEqual(len(old),len(new),rel);changed+=[(rel,a,b) for a,b in zip(old,new) if a!=b]
  # Three lines change, each by exactly one listed lift and nothing else.
  self.assertEqual(len(changed),3)
  for rel,a,b in changed:
   self.assertEqual(sum(1 for r,old,new in LIFTS if r==rel and a.count(old)==1 and a.replace(old,new,1)==b),1,(rel,a))
  oracle=json.loads((FIX/'ORACLE.json').read_text());checked=0
  for row in oracle['cases']:
   if row['nodes']:continue
   values=row['config']['values'];arrays={k:[int(v[1:],16) if isinstance(v,str) else v for v in row['config'][k]] for k in ('palette','starPalette')}
   arrays.update({k:[ord(v) if isinstance(v,str) else v for v in row['config'][k]] for k in ('glyphs','novaGlyphs')})
   case=spec(values['width'],values['height'],{k:v for k,v in values.items() if k not in ('width','height')},row.get('events',[]),row['timeMs'],arrays=arrays)
   with self.subTest(case=row['id']):self.assertEqual(oracle_frame(self.original,case),gzip.decompress((FIX/(row['id']+'.bin.gz')).read_bytes()));checked+=1
  self.assertEqual(checked,64)

 def test_in_range_archived_fixture_frames_stay_byte_identical(self):
  oracle=json.loads((FIX/'ORACLE.json').read_text())
  with self.scene() as s:
   for row in oracle['cases']:
    with self.subTest(case=row['id']):
     v=row['config']['values']
     for command in [{'op':'reset'},{'op':'resize','width':v['width'],'height':v['height']},{'op':'environment','presentation':'canvas','stars':0},{'op':'prompt','active':False},{'op':'floor','enabled':False,'visible':False},scene_command(row)]:s.command(command)
     for i,n in enumerate(row['nodes']):s.command(component(n,i))
     before=s.snapshot();actual=s.render().bytes;expected=gzip.decompress((FIX/(row['id']+'.bin.gz')).read_bytes())
     # Node-free frames match in all four words; component cells carry native ownership IDs.
     self.assertFrame(actual,expected,row['id'],colors_only=bool(row['nodes']));self.assertEqual(s.snapshot(),before)

 def test_viewports_beyond_512x256_are_accepted_and_paint_the_original_scene(self):
  for width,height in [(512,256),(513,256),(512,257),(513,40),(96,257),(1024,300),(2048,64)]:
   case=spec(width,height,LOAD,events_for(width,height))
   with self.subTest(width=width,height=height),self.scene() as s:
    configure(s,case);info=s.info_complete()['sourceStage']
    self.assertTrue(info['enabled']);self.assertEqual([info['config']['values']['width'],info['config']['values']['height']],[width,height])
    before,clock,meta=s.snapshot(),s.info()['clock'],s.info_complete()['sourceStage'];frame=s.render().bytes
    self.assertFrame(frame,self.oracle(case),f'{width}x{height} lifted original')
    if width<=512 and height<=256:self.assertFrame(frame,oracle_frame(self.original,case),'archived extent')
    # Novas paint at their documented cells across the whole viewport, past column 512 and row 256 too.
    novas=self.assertNovaGeometry(frame,case)
    if width>=1024 or height>=257:self.assertTrue(any(x>=512 or y>=256 for x,y in novas))
    grid=cells(frame);margin=[grid[y*width+x][1:3] for y in range(height) for x in range(width) if x>=512 or y>=256]
    if margin:self.assertGreater(len(set(margin)),1,'the margin past the archived extent is painted, not uniform')
    # Rendering is pure: identical repeat, no clock, scene or authoritative state change.
    self.assertEqual(s.render().bytes,frame);self.assertEqual(s.snapshot(),before);self.assertEqual(s.info()['clock'],clock);self.assertEqual(s.info_complete()['sourceStage'],meta)

 def test_more_than_512_active_impulses_paint_every_documented_nova(self):
  case=spec(1024,300,LOAD,events_for(1024,300))
  self.assertEqual(sum(live(case,e) for e in case['events']),128);self.assertEqual(needed(case),128+33*20);self.assertGreater(needed(case),512)
  with self.scene() as s:
   configure(s,case);frame=s.render().bytes
  self.assertNovaGeometry(frame,case)
  # stActive appends the 128 events, then tiles row by row. A 512-entry list would end after
  # tile 384 and silently drop every later tile's nova; each one inside the viewport is painted.
  ox,oy=LOAD['originX'],LOAD['originY'];grid=cells(frame)
  late=[(x,y) for x,y in (tile_nova(7319,ox,oy,tx,ty) for tx,ty in tiles(1024,300,ox,oy)[512-128:]) if 0<=x<1024 and 0<=y<300]
  self.assertGreater(len(late),200);self.assertEqual([p for p in late if grid[p[1]*1024+p[0]][0] not in NOVA],[])
  self.assertFrame(frame,self.oracle(case),'1024x300 lifted original')

 def test_every_pixel_mode_and_quantization_beyond_the_extent(self):
  for width,height in [(520,24),(24,300)]:
   for pixel in range(4):
    for quantize in range(3):
     case=spec(width,height,{**LOAD,'pixelMode':pixel,'quantize':quantize,'pattern':(pixel*5+quantize)%12},events_for(width,height,48))
     with self.subTest(width=width,height=height,pixelMode=pixel,quantize=quantize),self.scene() as s:
      configure(s,case);frame=s.render().bytes;self.assertFrame(frame,self.oracle(case),f'{width}x{height} pm{pixel} q{quantize}');self.assertNovaGeometry(frame,case)

 def test_narrow_extents_with_full_event_and_nova_load(self):
  # Thinnest frames past each archived dimension: the active list is largest relative to the cell count.
  for width,height in [(513,1),(1,257),(513,2),(2,257)]:
   case=spec(width,height,LOAD,events_for(width,height))
   with self.subTest(width=width,height=height),self.scene() as s:
    configure(s,case);self.assertFrame(s.render().bytes,self.oracle(case),f'{width}x{height}')
  # Beyond 512x256 a viewport always has at least one cell per possible active entry.
  for width in range(1,1100):
   for height in (range(1,300) if width>512 else range(257,300)):
    bound=128+((width-1)//32+2)*((height-1)//16+2)
    if bound>width*height:self.fail((width,height,bound))

 def test_supplied_dimensions_follow_the_viewport_beyond_512(self):
  case=spec(1024,300,LOAD,events_for(1024,300))
  with self.scene() as s:
   configure(s,case);frame=s.render().bytes
   s.command({'op':'source-stage','config':{'values':{'width':1024,'height':300}}});self.assertEqual(s.render().bytes,frame)
   before=s.snapshot()
   for values,message in [({'width':1023},'Source stage dimensions must match viewport'),({'height':301},'Source stage dimensions must match viewport'),({'width':0},'Source stage dimensions must match viewport'),
                          ({'width':MAX_WIDTH+1},'Invalid source stage value'),({'height':MAX_HEIGHT+1},'Invalid source stage value'),({'width':-1},'Invalid source stage value'),({'height':-1},'Invalid source stage value')]:
    with self.subTest(values=values):
     with self.assertRaises(ValueError) as caught:s.command({'op':'source-stage','config':{'values':values}})
     self.assertEqual(str(caught.exception),message);self.assertEqual(s.snapshot(),before)

 def test_enable_then_resize_matches_resize_then_enable_and_shrinks_back(self):
  case=spec(1024,300,LOAD,events_for(1024,300))
  with self.scene() as a,self.scene() as b:
   configure(a,case);configure(b,case,enable_first=True)
   self.assertEqual(b.info_complete()['sourceStage'],a.info_complete()['sourceStage']);self.assertEqual(b.render().bytes,a.render().bytes)
   small=spec(48,22,LOAD,case['events'])
   b.command({'op':'resize','width':48,'height':22});self.assertFrame(b.render().bytes,oracle_frame(self.original,small),'shrunk to 48x22')

 def test_render_memory_shortfall_reports_the_storage_diagnostic_without_disabling(self):
  case=spec(1024,300,LOAD,events_for(1024,300))
  with self.scene() as s:
   configure(s,case);lib,ctx=s._lib,s._context;required,capacity=lib.nrRenderMemorySize(ctx),lib.nrRenderMemoryCapacity(ctx)
   self.assertGreater(required,capacity);before=s.snapshot()
   self.assertEqual(lib.nrRender(ctx),0);self.assertEqual(lib.nrError(ctx),b'Viewport render memory required')
   self.assertEqual(s.snapshot(),before);self.assertTrue(s.info_complete()['sourceStage']['enabled'])
   self.assertFrame(s.render().bytes,self.oracle(case),'after provisioning render memory')

 def test_components_hits_and_snapshot_round_trip_beyond_the_extent(self):
  nodes=[('box',dict(x=600,y=262,width=40,height=6,style=1,fg=0xd0c0b0,bgOpacity=600,legacyFlags=4100)),
         ('text',dict(x=900,y=280,width=60,height=1,text='beyond column 512',legacyFlags=4242)),
         ('bars',dict(x=700,y=200,width=30,height=8,data=[300,700,1000,450],legacyFlags=4300)),
         ('button',dict(x=1000,y=290,width=20,height=3,text='OK',legacyFlags=4400))]
  case=spec(1024,300,LOAD,events_for(1024,300),nodes=nodes)
  with self.scene() as s:
   configure(s,case);frame=s.render().bytes;snap=s.snapshot();meta=s.info_complete()
   self.assertEqual(colors(frame),colors(self.oracle(case)))
   self.assertEqual(s.source_stage_hit(905,280),{'id':4242,'item':0});self.assertEqual(s.source_stage_hit(1005,291),{'id':4400,'item':0})
   self.assertEqual(s.source_stage_hit(605,264),{'id':4100,'item':0})
  with self.scene() as t:
   t.restore(snap);restored=t.info_complete()
   self.assertEqual(restored['sourceStage'],meta['sourceStage']);self.assertEqual(restored['sourceStageComponents'],meta['sourceStageComponents'])
   self.assertEqual(t.render().bytes,frame);self.assertEqual(t.snapshot(),snap)

 def test_representation_limits_admit_at_bound_and_reject_beyond_atomically(self):
  # The two bounds are where the original int32 sample arithmetic stops being representable.
  def x_span(w):return (w-1)*256+64+EVENT_Q8
  def y_span(h):return ((h-1)*256+96+EVENT_Q8)*ASPECT//1000
  self.assertLessEqual(x_span(MAX_WIDTH),INT32_MAX);self.assertGreater(x_span(MAX_WIDTH+1),INT32_MAX)
  self.assertLessEqual(y_span(MAX_HEIGHT),INT32_MAX);self.assertGreater(y_span(MAX_HEIGHT+1),INT32_MAX)
  # Nova impulses sit up to 29 columns and 13 rows past the far edge, 30 and 14 before it.
  self.assertLessEqual((MAX_WIDTH+29)*256,INT32_MAX);self.assertLessEqual(64+(MAX_WIDTH+29)*256,INT32_MAX)
  self.assertLessEqual(((MAX_HEIGHT+13)*256+96)*ASPECT//1000,INT32_MAX)
  probe=self.out/'viewport.c';probe.write_text('#include "internal.h"\n#include <stdio.h>\nint main(){printf("%zu %zu",offsetof(State,width),offsetof(State,height));}\n');exe=self.out/'viewport'
  subprocess.run([os.environ.get('CC','cc'),'-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(probe),'-o',str(exe)],check=True);widthAt,heightAt=map(int,subprocess.check_output([str(exe)]).split())
  admitted=[(MAX_WIDTH,1),(1,MAX_HEIGHT),(MAX_WIDTH,512),(2052,MAX_HEIGHT)];rejected=[(MAX_WIDTH+1,1),(1,MAX_HEIGHT+1)]
  self.assertTrue(all(w*h<=UINT32_MAX for w,h in admitted+rejected))
  with self.scene() as s:
   s.command({'op':'resize','width':96,'height':40});s.command({'op':'source-stage','timeMs':TIME_MS,'config':{'values':LOAD}})
   for width,height in admitted:
    with self.subTest(admitted=(width,height)):
     s.command({'op':'resize','width':width,'height':height});values=s.info_complete()['sourceStage']['config']['values'];self.assertEqual([values['width'],values['height']],[width,height])
   for width,height in rejected:
    with self.subTest(rejected=(width,height)):
     before=s.snapshot()
     with self.assertRaises(ValueError) as caught:s.command({'op':'resize','width':width,'height':height})
     self.assertEqual(str(caught.exception),'State invariant rejected');self.assertEqual(s.snapshot(),before)
   s.command({'op':'resize','width':MAX_WIDTH,'height':1});limit=s.snapshot()
  with self.scene() as t:
   t.restore(limit);self.assertEqual(t.snapshot(),limit);self.assertTrue(t.info_complete()['sourceStage']['enabled'])
   def patched(width,height):
    raw=bytearray(limit);struct.pack_into('<I',raw,24+widthAt,width);struct.pack_into('<I',raw,24+heightAt,height);struct.pack_into('<I',raw,20,zlib.crc32(raw[24:]));return bytes(raw)
   t.restore(patched(1,MAX_HEIGHT));self.assertEqual(t.info_complete()['sourceStage']['config']['values']['height'],MAX_HEIGHT);t.restore(limit)
   for width,height in rejected:
    with self.subTest(restore=(width,height)):
     with self.assertRaises(ValueError):t.restore(patched(width,height))
     self.assertEqual(t.snapshot(),limit)
  # Without the scene the same viewports remain ordinary SDK viewports; enabling the scene there is rejected.
  with self.scene() as s:
   for width,height in rejected:
    with self.subTest(disabled=(width,height)):
     s.command({'op':'resize','width':width,'height':height});before=s.snapshot()
     with self.assertRaises(ValueError) as caught:s.command({'op':'source-stage','timeMs':0})
     self.assertEqual(str(caught.exception),'Invalid source stage scene');self.assertEqual(s.snapshot(),before)

 def test_actual_wasm_frame_beyond_512x256_matches_native_and_original(self):
  nodes=[('text',dict(x=900,y=280,width=60,height=1,text='wasm beyond 512',legacyFlags=4242))]
  case=spec(1024,300,LOAD,events_for(1024,300),nodes=nodes)
  with self.scene() as s:
   configure(s,case);native=s.render().bytes
  request=self.out/'wasm-extent.json';output=self.out/'wasm-extent'
  request.write_text(json.dumps({'commands':commands(case),'timeUs':0,'invalidCommand':{'op':'source-stage','config':{'values':{'width':1023}}}}))
  subprocess.run([node_executable(),str(ROOT/'tests/source_stage_public_wasm_runner.mjs'),str(request),str(output)],check=True,timeout=600)
  report=json.loads((output/'report.json').read_text());self.assertEqual([report['width'],report['height']],[1024,300])
  self.assertTrue(report['invalidRejected']);self.assertTrue(report['snapshotReplayIdentical'])
  wasm=(output/report['cellsFile']).read_bytes();self.assertEqual(wasm,native);self.assertEqual(colors(wasm),colors(self.oracle(case)))

if __name__=='__main__':unittest.main()
