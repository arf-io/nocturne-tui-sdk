"""Actual original Observatory surfaces, not a Kinetic background substitution."""
import copy,gzip,hashlib,json,os,struct,subprocess,sys,tempfile,unittest,zlib
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'hosts/python'))
from nocturne_native import NativeScene
from atelier_application import rc2_window_commands
FIXTURE=ROOT/'tests/fixtures/original-observatory-background/ORIGINAL-FRAMES-V2.json.gz'
FIELDS=('fps','gradientScreens','gradientAngle','gradientSpeed','gradientPhase','pivotX','pivotY','axisPitch','rotationSpeed','secondAxisSpeed','swingAngle','swingSeconds','starDensity','starGlyphs','starCount','starSpeed','trailMs','travelYaw','travelPitch','weatherIntensity','novaStrength','novaRegularity','backgroundStyle','sampling','orbitMode','motion','weatherLifeMs','weatherSpeed')
PALETTE_FIELDS=('lightness','chroma','brightness','hueOffset','lockLightness','feather','stopWidths','textLightness','textChroma')
@lru_cache(maxsize=1)
def fixture():
 raw=FIXTURE.read_bytes()
 if hashlib.sha256(raw).hexdigest()!='b5ca5d11831a4c88a2fe15d10872b1acf9bb2718191f856392dcf1b1fa32a386':raise ValueError('Original fixture bytes changed')
 rows=json.loads(gzip.decompress(raw))['rows'];queue=(FIXTURE.parent/'ORIGINAL-QUEUE-FRAMES.json.gz').read_bytes()
 if hashlib.sha256(queue).hexdigest()!='c41aea9633ed00a6c7e0c405755c734d8768de9b2656fdd4cfdbf5a4292e9810':raise ValueError('Original queue fixture bytes changed')
 return rows+json.loads(gzip.decompress(queue))['rows']
def commands(row):
 source=row['source'];options=copy.deepcopy(source['options']);w,h=row['request']['size']
 for key,timeline in [('gradientSpeed','travel'),('rotationSpeed','orbit'),('secondAxisSpeed','orbit2'),('starSpeed','warpTravel')]:options[key]=source[timeline][0]['rate']
 result=[{'op':'resize','width':w,'height':h},{'op':'environment','presentation':'canvas','style':'solid','background':int(source['palette']['background'][1:],16),'stars':0},{'op':'floor','enabled':False,'visible':False},{'op':'prompt','active':False,'alpha':0},{'op':'camera','profile':'original','position':[options['cameraX'],options['cameraY'],-options['cameraZ']],'yaw':options['cameraYaw'],'pitch':options['cameraPitch'],'roll':options['cameraRoll'],'near':.2,'far':150,'fov':options['fov'],'orthographic':False}]
 palette=rc2_window_commands({'id':'observatory-palette','title':'Original Observatory palette','content':'','x':0,'y':0,'z':20,'width':2,'height':2},native_id=1,palette=source['palette'],options={k:options[k] for k in PALETTE_FIELDS})
 result.extend(palette);result.append({'op':'window','id':1,'alpha':0})
 result.append({'op':'window-application','scene':'observatory','paletteWindowId':1,**{k:options[k] for k in FIELDS}})
 # The original weather() never reads event.glyph. Retain every consumed field.
 for event in source['events']:
  if set(event)-{'kind','id','x','y','atMs','glyph'}:raise ValueError('Unknown original event metadata')
  result.append({'op':'window-application-event',**{k:v for k,v in event.items() if k!='glyph'}})
 return result
def nodes(row):
 result=[]
 for index,n in enumerate(row.get('composed',{}).get('nodes',[])):
  n=copy.deepcopy(n);legacy=n.pop('id',0);result.append({'op':'source-stage-component','id':index+1,'legacyFlags':legacy,**n})
 return result
def visual(words):return [tuple(words[i:i+3]) for i in range(0,len(words),4)]
@lru_cache(maxsize=1)
def compiled_prefixes():
 # Actual target C layout, not sizeof(State) or a modern-payload retag.
 with tempfile.TemporaryDirectory(prefix='observatory-layout-') as directory:
  root=Path(directory);source=root/'layout.c';exe=root/'layout'
  source.write_text('#include "internal.h"\n#include <stddef.h>\n#include <stdio.h>\nint main(void){printf("%u %zu %zu\\n",NR_STATE_SCHEMA,offsetof(State,sourceStageScene),offsetof(State,dynamicPrompt));return 0;}\n')
  subprocess.run([os.environ.get('CC','cc'),'-std=c11','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(source),'-o',str(exe)],check=True,capture_output=True,text=True)
  schema,prior,current=map(int,subprocess.check_output([str(exe)],text=True).split())
 if schema<0x20261091 or prior!=30489392 or current<=prior:raise AssertionError('Unexpected actual Stage91 append layout')
 return {'schema':schema,'prior':prior,'current':current}
def constructed_schema90(snapshot):
 """Explicit test construction: remove only zero Stage91 footer, keep both arenas."""
 q=compiled_prefixes();data=bytes(snapshot)
 if len(data)<24+q['current'] or struct.unpack_from('<I',data,12)[0]!=q['schema'] or struct.unpack_from('<I',data,28)[0]!=q['schema']:raise AssertionError('Input is not actual current writer')
 if struct.unpack_from('<I',data,16)[0]!=len(data)-24 or struct.unpack_from('<I',data,20)[0]!=zlib.crc32(data[24:]):raise AssertionError('Invalid current wire')
 if any(data[24+q['prior']:24+q['current']]):raise AssertionError('Cannot discard active Stage91 footer')
 result=bytearray(data[:24+q['prior']]+data[24+q['current']:])
 for offset,value in ((12,0x20261090),(28,0x20261090),(16,len(result)-24)):struct.pack_into('<I',result,offset,value)
 struct.pack_into('<I',result,20,zlib.crc32(result[24:]));return bytes(result)
class OriginalObservatoryBackground(unittest.TestCase):
 @contextmanager
 def scene(self,row):
  with NativeScene(2030,library=os.environ.get('NOCTURNE_REVIEW_LIBRARY')) as s:
   for c in commands(row):s.command(c)
   for action in row['request'].get('actions',[]):
    s.advance_to(round(action['atMs']*1000));s.command({'op':'window-application',**action['patch']})
   s.advance_to(round(row['request']['atMs']*1000));yield s
 def assert_frame(self,s,expected,label):
  before=s.snapshot();actual=list(memoryview(s.render().bytes).cast('I'));self.assertEqual(s.snapshot(),before,'Painting mutated state')
  a,b=visual(actual),visual(expected);self.assertEqual(len(a),len(b));diff=[(i,b[i],a[i]) for i in range(len(b)) if a[i]!=b[i]]
  if diff:self.retain('failure-'+label,{'id':label,'expected':expected,'actual':actual,'differentVisualCells':len(diff)})
  self.assertEqual(len(diff),0,f'{label}: {len(diff)} visual cells differ, first={diff[:8]}')
  return actual
 def retain(self,name,rows):
  if os.environ.get('NOCTURNE_OBSERVATORY_BACKGROUND_EVIDENCE'):
   target=Path(os.environ['NOCTURNE_OBSERVATORY_BACKGROUND_EVIDENCE']);target.mkdir(parents=True,exist_ok=True)
   with gzip.open(target/(name+'.json.gz'),'wt') as out:json.dump(rows,out,separators=(',',':'))
 def test_all_original_surface_frames(self):
  observed=[]
  for row in fixture():
   with self.subTest(id=row['id']),self.scene(row) as s:
    actual=self.assert_frame(s,row['surface']['cells'],row['id']);self.assertTrue(all(actual[i]==0 for i in range(3,len(actual),4)),'Surface must not invent hit ownership');observed.append({'id':row['id'],'cells':actual})
  self.retain('native-surfaces',observed);self.assertEqual(len(observed),len(fixture()))
 def test_managed_prompt_scope_and_sensors_complete_frames(self):
  observed=[]
  for row in fixture():
   if 'composed' not in row:continue
   with self.subTest(id=row['id']),self.scene(row) as s:
    for c in nodes(row):s.command(c)
    actual=self.assert_frame(s,row['composed']['frame']['cells'],row['id']);observed.append({'id':row['id'],'cells':actual})
  self.assertEqual(len(observed),6);self.retain('native-compositions',observed)
 def test_snapshot_roundtrip_and_late_batch_rejection(self):
  row=next(r for r in fixture() if r['id']=='warp-camera-xyz-roll-1700')
  with self.scene(row) as s:
   saved=s.snapshot();frame=self.assert_frame(s,row['surface']['cells'],row['id'])
   s.advance_to(3000000);s.restore(saved);self.assertEqual(s.snapshot(),saved);self.assertEqual(list(memoryview(s.render().bytes).cast('I')),frame)
   with self.assertRaises(ValueError):s.command({'op':'batch','commands':[{'op':'window-application','weatherSpeed':50},{'op':'window-application','weatherLifeMs':199}]})
   self.assertEqual(s.snapshot(),saved);self.assertEqual(list(memoryview(s.render().bytes).cast('I')),frame)
 def test_original_weather_bounds_defaults_and_alias_conflicts(self):
  with self.scene(fixture()[0]) as s:
   s.command({'op':'remove-window-application'});s.command({'op':'window-application','scene':'observatory','paletteWindowId':1})
   info=s.info_complete()['windowApplication'];self.assertEqual(info['scene'],'observatory');self.assertEqual([info[k] for k in ('weatherIntensity','novaStrength','weatherLifeMs','weatherSpeed')],[.38,.28,2400,12])
   for life in (200,8000):
    for speed in (1,50):
     s.command({'op':'window-application','weatherLifeMs':life,'weatherSpeed':speed});info=s.info_complete()['windowApplication'];self.assertEqual([info['weatherLifeMs'],info['weatherSpeed']],[life,speed])
   for bad in ({'weatherSpeed':0},{'weatherSpeed':50.01},{'weatherLifeMs':199},{'weatherLifeMs':8001},{'weatherSpeed':12,'particles':{'launchSpeed':13}},{'weatherLifeMs':2400,'particles':{'lifeMs':2401}}):
    before=s.snapshot();frame=s.render().bytes
    with self.assertRaises(ValueError):s.command({'op':'window-application',**bad})
    self.assertEqual(s.snapshot(),before);self.assertEqual(s.render().bytes,frame)
   s.command({'op':'window-application','weatherSpeed':50,'weatherLifeMs':8000,'particles':{'launchSpeed':50,'lifeMs':8000}})
   s.command({'op':'window-application','gradientPhase':.3});info=s.info_complete()['windowApplication'];self.assertEqual([info['weatherSpeed'],info['weatherLifeMs']],[50,8000],'Unrelated edit reset authored Observatory controls')
 def test_constructed90_rejects_new_scene_and_accepts_old_mode(self):
  with self.scene(fixture()[0]) as scene:
   saved=scene.snapshot();before=scene.render().bytes;hostile=constructed_schema90(saved)
   with self.assertRaises(ValueError):scene.restore(hostile)
   self.assertEqual(scene.snapshot(),saved);self.assertEqual(scene.render().bytes,before)
   scene.command({'op':'window-application','scene':'windows'});older=constructed_schema90(scene.snapshot());expected=scene.render().bytes
   scene.restore(older);self.assertEqual(scene.render().bytes,expected)
   scene.command({'op':'remove-window-application'});scene.command({'op':'window-application','scene':'observatory','paletteWindowId':1})
   self.assertEqual(scene.info_complete()['windowApplication']['scene'],'observatory')
 def test_nonfinite_raw_numbers_and_invalid_types_reject_atomically(self):
  with self.scene(fixture()[0]) as scene:
   saved=scene.snapshot();frame=scene.render().bytes
   for value in (None,True,[],{},'12'):
    with self.assertRaises(ValueError):scene.command({'op':'window-application','weatherSpeed':value})
    self.assertEqual(scene.snapshot(),saved);self.assertEqual(scene.render().bytes,frame)
   with self.assertRaises(ValueError):scene.command_raw(b'{"op":"window-application","weatherSpeed":1e999}')
   self.assertEqual(scene.snapshot(),saved);self.assertEqual(scene.render().bytes,frame)
 def test_actual_import_free_wasm_original_frames(self):
  rows=fixture();requests=[{'id':r['id'],'commands':commands(r),'actions':r['request'].get('actions',[]),'atMs':r['request']['atMs'],'nodes':nodes(r)} for r in rows]
  with tempfile.TemporaryDirectory() as directory:
   inp=Path(directory)/'requests.json';out=Path(directory)/'actual.json';inp.write_text(json.dumps({'rows':requests,'layout':compiled_prefixes()}))
   result=subprocess.run([os.environ.get('NODE','node'),str(ROOT/'tests/original_observatory_background_wasm.mjs'),str(inp),str(out)],capture_output=True,text=True,timeout=180)
   self.assertEqual(result.returncode,0,result.stderr[-2000:]);result_data=json.loads(out.read_text());actual=result_data['rows'];self.assertEqual(len(actual),len(rows));self.assertEqual(len(result_data['checks']),7)
   for row,a in zip(rows,actual):
    with self.subTest(id=row['id']):
     self.assertEqual(a['id'],row['id']);self.assertEqual(visual(a['surface']),visual(row['surface']['cells']))
     self.assertTrue(all(a['surface'][i]==0 for i in range(3,len(a['surface']),4)))
     if 'composed' in row:self.assertEqual(visual(a['composed']),visual(row['composed']['frame']['cells']))
   self.retain('wasm',result_data)
if __name__=='__main__':unittest.main()
