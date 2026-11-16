"""Actual original full Atelier application frames versus the current public SDK."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,math,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from native.tests.presentation_copy_reference import assert_snapshot_presentation
from native.tests.host_environment import failure_record
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'hosts/python'))
from nocturne_native import NativeScene
from native.tests.presentation_copy_reference import current_presentation
from atelier_application import SPATIAL_WINDOW_EFFECTS
EFFECTS=[k.split('/')[1] for k in SPATIAL_WINDOW_EFFECTS if k.startswith('atelier/')]
WIDTH,HEIGHT=136,44

def commands(effect='genie',style=None,draft=''):
 out=[{'op':'resize','width':WIDTH,'height':HEIGHT},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'floor','visible':False},{'op':'prompt','active':False},{'op':'draft','text':draft,'emitWeather':False},{'op':'camera','profile':'original','position':[0,0,WIDTH/(2*math.tan(68*math.pi/360))],'target':[0,0,0],'yaw':0,'pitch':0,'roll':0,'fov':68,'near':.2,'far':20000}]
 specs=[('PEARL / SIGNAL',5,9,52,23,'rounded',0),('ATLAS / OPS',54,15,56,21,'hexagon',5),('IRIS / ARCHIVE',86,7,42,18,'ellipse',14)]
 for index,(title,x,y,w,h,shape,depth) in enumerate(specs):
  identity=index+1
  out.extend([{'op':'window','id':identity,'title':title,'shape':shape,'effect':SPATIAL_WINDOW_EFFECTS['atelier/'+effect],'position':[x+w/2-WIDTH/2,(HEIGHT/2-y-h/2)*2,-depth],'width':w,'height':h*2,'durationMs':0,'alpha':.88,'overshoot':.18,'scatter':24,'bend':9,'seed':6001}, {'op':'window-content','id':identity,'profile':'atelier','label':'w'+str(identity),'sourceIndex':index,'brightness':.16,**(style or {})},{'op':'window','id':identity,'durationMs':950}])
 out.extend([{'op':'window-action','id':1,'action':'restore','durationMs':0},{'op':'window','id':1,'durationMs':950},{'op':'window-application','paletteWindowId':1,'scene':'atelier-windows','starDensity':.024,'novaRegularity':0}]);return out

def map_hits(words):
 words=list(words)
 for i in range(3,len(words),4):
  hit=words[i]
  if 19000<hit<19100:words[i]=0x50000000+(hit-19000)
  elif 10000<hit<10400:
   identity=(hit-10000)//10;action=(hit-10000)%10
   words[i]=[0x20000000,0x61000000,0x62000000,0x64000000,0x60000000][action]+identity
 return words

class OriginalAtelierWindows(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  source=gzip.decompress((ROOT/'tests/fixtures/original-atelier-spatial-v0.5.html.gz').read_bytes());assert hashlib.sha256(source).hexdigest()=='01500ccd3106f40a7f0b3e21fe4a580f1e0666980e998930feaf94bff730aced'
  cls.captures=[];cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(headless=True);cls.page=cls.browser.new_page();cls.page.set_content(current_presentation(source.decode(),"atelier"),wait_until='domcontentloaded');cls.page.wait_for_function('window.atelierApp');cls.page.evaluate('atelierApp.stop()')
 @classmethod
 def tearDownClass(cls):
  cls.browser.close();cls.p.stop()
  if os.environ.get('NOCTURNE_ATELIER_WINDOWS_CAPTURE'):
   p=Path(os.environ['NOCTURNE_ATELIER_WINDOWS_CAPTURE']);p.mkdir(parents=True,exist_ok=True);(p/'frames.json.gz').write_bytes(gzip.compress(json.dumps(cls.captures,separators=(',',':')).encode(),mtime=0))
 def wasm_compare(self,captures):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cases.json';p.write_text(json.dumps([c['case'] for c in captures]));run=subprocess.run(['node',str(ROOT/'tests/atelier_windows_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(p)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);wasm=json.loads(run.stdout)
  self.assertEqual(len(wasm),len(captures))
  for capture,actual in zip(captures,wasm):
   expected=capture['expected'];diff=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b];self.assertEqual(len(actual),len(expected));self.assertEqual(len(diff),0,capture['case']['name']+' WASM '+str(diff[:12]));capture['wasm']=actual
  self.captures.extend(captures)
 def original(self,effect,time,actions,style=None,draft=''):
  return self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');m.workspace.configure({effect:r.effect,...r.style});m.draft=r.draft;for(const a of r.actions){if(a.at>r.time)continue;m.setTime(a.at/1000);if(a.action==='restore')m.workspace.restore(a.id||1,a.at/1000);else if(a.action==='roll-up'||a.action==='roll-down')m.workspace.toggleRoll(a.id||1,a.at/1000);else m.workspace.action(a.id||1,a.action,a.at/1000)}m.setTime(r.time/1000);return Array.from(atelierApp.renderer.render(m).frame.cells)}""",dict(effect=effect,time=time,actions=actions,style=style or {},draft=draft))
 def compare(self,scene,effect,time,actions,style=None,draft=''):
  before=scene.snapshot();actual=list(memoryview(scene.render().bytes).cast('I'));self.assertEqual(scene.snapshot(),before);original=self.original(effect,time,actions,style,draft);expected=map_hits(original);different=[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
  if different:failure_record('atelier-window-failure.json',dict(effect=effect,time=time,actions=actions,actual=actual,original=original,expected=expected))
  self.assertEqual(len(different),0,f'{effect}@{time}: '+str(different[:12]));return actual,original,expected
 def test_tool_styles_recovery_maximize_fade_roll_and_draft(self):
  captures=[]
  variants=[{},dict(chrome='windows',toolWidth=5,toolHeight=3),dict(chrome='gnome',toolWidth=10,toolHeight=4),dict(chrome='custom',customSide='left',customOrder=['fade','close','maximize','minimize'],customGlyphs=['a','b','c','d'],toolColors=dict(minimize=0xff0000,maximize=0x00ff00,fade=0x0000ff,close=0xabcdef),fadeFloor=.35)]
  actions=[dict(at=1000000,action='maximize'),dict(at=2500000,action='fade'),dict(at=4000000,action='roll-up'),dict(at=5500000,action='restore'),dict(at=7000000,action='maximize'),dict(at=8500000,action='close'),dict(at=10000000,action='restore')]
  for style in variants:
   with self.subTest(style=style),NativeScene(2030) as scene:
    initial=commands('genie',style,'original Unicode ñΩ╳界 🌙')
    for c in initial:scene.command(c)
    ai=0
    for time in [0]+[a['at']+475000 for a in actions]+[11000000]:
     while ai<len(actions) and actions[ai]['at']<=time:
      a=actions[ai];scene.advance_to(a['at']);scene.command(dict(op='window-action',id=1,action=a['action']));ai+=1
     scene.advance_to(time);actual,original,expected=self.compare(scene,'genie',time,actions,style,'original Unicode ñΩ╳界 🌙');captures.append(dict(case=dict(name='controls-'+style.get('chrome','mac')+'-'+str(time),commands=initial,actions=actions,timeUs=time),native=actual,original=original,expected=expected))
  self.wasm_compare(captures)
 def test_all_original_shapes_and_tilted_depth_order(self):
  captures=[]
  polygon=[[.05,.2],[.35,0],[.9,.12],[1,.8],[.65,1],[0,.85]]
  for shape in ('rectangle','rounded','ellipse','hexagon','diamond','capsule','ticket','cloud','polygon'):
   with self.subTest(shape=shape),NativeScene(2030) as scene:
    initial=commands()+[dict(op='window',id=identity,shape=shape,polygon=polygon,yaw=identity*11,pitch=identity*-7,roll=identity*3) for identity in (1,2,3)]+[dict(op='window-action',id=1,action='restore',durationMs=0)]
    for c in initial:scene.command(c)
    scene.advance_to(1700000)
    expected=self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');m.workspace.configure({polygon:r.polygon});for(const w of m.workspace.windows){w.shape=r.shape;w.yaw=w.id*11;w.pitch=w.id*-7;w.roll=w.id*3}m.setTime(1700);return Array.from(atelierApp.renderer.render(m).frame.cells)}""",dict(shape=shape,polygon=polygon))
    actual=list(memoryview(scene.render().bytes).cast('I'));original=expected;expected=map_hits(expected);diff=[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b];self.assertEqual(diff,[],str(diff[:12]));captures.append(dict(case=dict(name='shape-'+shape,commands=initial,actions=[],timeUs=1700000),original=original,expected=expected,native=actual))
  self.wasm_compare(captures)
 def test_original_default_polygon_is_available_without_a_replacement(self):
  with NativeScene(2030) as scene:
   initial=commands()+[dict(op='window',id=i,shape='polygon') for i in (1,2,3)]+[dict(op='window-action',id=1,action='restore',durationMs=0)]
   for c in initial:scene.command(c)
   scene.advance_to(1700000)
   original=self.page.evaluate("""()=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');for(const w of m.workspace.windows)w.shape='polygon';m.setTime(1700);return Array.from(atelierApp.renderer.render(m).frame.cells)}""")
   actual=list(memoryview(scene.render().bytes).cast('I'));expected=map_hits(original);self.assertEqual(actual,expected)
   self.wasm_compare([dict(case=dict(name='default-original-polygon',commands=initial,actions=[],timeUs=1700000),original=original,expected=expected,native=actual)])
 def test_normal_catalogue_routes_select_full_application(self):
  sys.path.insert(0,str(ROOT/'examples'));from gallery_cases import build_cases
  cases={c['id']:c for c in build_cases()}
  for entry in json.loads((ROOT/'catalogue.json').read_text()):
   if not (entry.get('sourceIdentity') or '').startswith('window/atelier/'):continue
   for mode in ('isolated','application'):
    identity='study-'+entry['id'].replace('/','-')+'-'+mode;c=cases[identity]
    self.assertEqual(c['viewport'],dict(width=136,height=44));self.assertEqual(next(c for c in c['commands'] if c['op']=='window-application')['scene'],'atelier-windows')
    self.assertEqual([c['profile'] for c in c['commands'] if c['op']=='window-content'],['atelier']*3);self.assertIn(identity+'-compact',cases)
 def test_pointer_tool_hits_match_original_action_and_dock_recovery(self):
  for action,family in [('minimize',0x61000000),('maximize',0x62000000),('fade',0x64000000),('close',0x60000000)]:
   with self.subTest(action=action),NativeScene(2030) as scene:
    for c in commands():scene.command(c)
    cells=list(memoryview(scene.render().bytes).cast('I'));hit=next(i//4 for i in range(3,len(cells),4) if cells[i]==family+2)
    scene.command(dict(op='pointer',phase='down',x=hit%WIDTH,y=hit//WIDTH,button=0));scene.command(dict(op='pointer',phase='up',x=hit%WIDTH,y=hit//WIDTH,button=0));scene.advance_to(475000)
    actions=[dict(at=0,action=action,id=2)];self.compare(scene,'genie',475000,actions)
    scene.advance_to(1000000);cells=list(memoryview(scene.render().bytes).cast('I'));hit=next(i//4 for i in range(3,len(cells),4) if cells[i]==0x50000002)
    scene.command(dict(op='pointer',phase='down',x=hit%WIDTH,y=hit//WIDTH,button=0));scene.command(dict(op='pointer',phase='up',x=hit%WIDTH,y=hit//WIDTH,button=0));scene.advance_to(1475000);actions.append(dict(at=1000000,action='restore',id=2));self.compare(scene,'genie',1475000,actions)
 def test_genuine_previous_69_72_74_snapshots_keep_full_frames(self):
  for snapshotName,frameName in [('window-application-schema69.bin.gz','window-application-schema69-frame.bin.gz'),('window-capacity-schema72.bin.gz','window-capacity-schema72.frame.bin.gz'),('original-camera-schema74.bin.gz','original-camera-schema74.frame.bin.gz')]:
   with self.subTest(snapshot=snapshotName),NativeScene(5) as scene:
    fixture=ROOT/'tests/fixtures';scene.restore(gzip.decompress((fixture/snapshotName).read_bytes()));assert_snapshot_presentation(self,scene,gzip.decompress((fixture/frameName).read_bytes()))
 def test_genuine_schema80_snapshot_frame_and_metadata(self):
  f=ROOT/'tests/fixtures';name='original-schema80-atelier-windows';m=json.loads((f/(name+'.json')).read_text());snapshot=gzip.decompress((f/(name+'.snapshot.gz')).read_bytes());frame=gzip.decompress((f/(name+'.cells.gz')).read_bytes())
  self.assertEqual(hashlib.sha256(snapshot).hexdigest(),m['snapshotSha256']);self.assertEqual(hashlib.sha256(frame).hexdigest(),m['frameSha256'])
  with NativeScene(5) as scene:
   scene.restore(snapshot);assert_snapshot_presentation(self,scene,frame);self.assertEqual(scene.info()['windowApplication']['scene'],'atelier-windows');self.assertEqual(scene.info()['windows'][0]['content']['profile'],'atelier')
 def test_invalid_styles_and_snapshot_restore(self):
  with NativeScene(2030) as scene:
   for c in commands():scene.command(c)
   for patch in [dict(chrome='wrong'),dict(toolWidth=4),dict(toolHeight=5),dict(toolWidth=5.5),dict(customOrder=['fade']*4),dict(customGlyphs=['界','a','b','c']),dict(fadeFloor=1.1),dict(toolColors=dict(close=0x1000000))]:
    before=scene.snapshot()
    with self.assertRaises(Exception):scene.command(dict(op='window-content',id=1,**patch))
    self.assertEqual(scene.snapshot(),before)
   scene.advance_to(1000000);scene.command(dict(op='window-action',id=1,action='minimize'));scene.advance_to(1425000)
   before=scene.snapshot();frame=scene.render().bytes
   with NativeScene(5) as restored:
    restored.restore(before);self.assertEqual(restored.render().bytes,frame)
 def test_all_22_full_original_windows_native_and_wasm(self):
  captures=[];cases=[]
  for effect in EFFECTS:
   if os.environ.get('NOCTURNE_ATELIER_WINDOW_EFFECT') and effect!=os.environ['NOCTURNE_ATELIER_WINDOW_EFFECT']:continue
   initial=commands(effect);actions=[{'at':1000000,'action':'minimize'},{'at':3000000,'action':'restore'}]
   with NativeScene(2030) as scene:
    for c in initial:scene.command(c)
    ai=0
    for time in (0,1425000,2100000,3425000,4000000):
     while ai<len(actions) and actions[ai]['at']<=time:
      a=actions[ai];scene.advance_to(a['at']);scene.command({'op':'window-action','id':1,'action':a['action']});ai+=1
     scene.advance_to(time);actual,original,expected=self.compare(scene,effect,time,actions);case=dict(name=effect+'-'+str(time),commands=initial,actions=actions,timeUs=time);cases.append(case);captures.append(dict(case=case,original=original,expected=expected,native=actual))
  self.wasm_compare(captures)
if __name__=='__main__':unittest.main()
