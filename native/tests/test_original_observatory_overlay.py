"""Exact retained Observatory skyText and orbital connector layers."""
import copy,gzip,hashlib,json,os,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'hosts/python'))
from nocturne_native import NativeScene
from atelier_application import rc2_window_commands
from prompt_wire_layout import layout as current_wire_layout
FIX=ROOT/'tests/fixtures/original-observatory-overlay'
def rows():
 raw=gzip.decompress((FIX/'ORIGINAL-FRAMES.json.gz').read_bytes())
 assert hashlib.sha256(raw).hexdigest()=='f05ad921aa2abf97ff841bb1b116fc62cddab529e832b0e63eb15714bdc835d4'
 out=json.loads(raw)['rows'];warp=gzip.decompress((FIX/'ORIGINAL-WORKSPACE-WARP-FRAMES.json.gz').read_bytes());assert hashlib.sha256(warp).hexdigest()=='7f55fc37b5c8552dcd73a34ccedbafacc5ecf740eb0c5fca0c34df31823f60b7'
 for row in json.loads(warp)['rows']:
  row=copy.deepcopy(row);row['request']['timeMs']=row['request']['atMs'];row['background']=None;row['underlay']=row['surface']['cells'];row['nodes']=row['composed']['nodes'];row['frame']=row['composed']['frame'];out.append(row)
 return out
def commands(row):
 source=row['source'];o=copy.deepcopy(source['options']);w,h=row['request']['size']
 result=[{'op':'resize','width':w,'height':h},{'op':'environment','presentation':'canvas','stars':0,'background':int(source['palette']['background'][1:],16)},{'op':'floor','enabled':False,'visible':False},{'op':'prompt','active':False,'alpha':0},{'op':'camera','profile':'original','position':[o['cameraX'],o['cameraY'],-o['cameraZ']],'yaw':o['cameraYaw'],'pitch':o['cameraPitch'],'roll':o['cameraRoll'],'near':.2,'far':150,'fov':o['fov'],'orthographic':False}]
 palette_fields=('lightness','chroma','brightness','hueOffset','lockLightness','feather','stopWidths','textLightness','textChroma')
 result+=rc2_window_commands({'id':'observatory-palette','title':'Original Observatory palette','content':'','x':0,'y':0,'z':20,'width':2,'height':2},native_id=1,palette=source['palette'],options={k:o[k]for k in palette_fields})
 result.append({'op':'window','id':1,'alpha':0})
 fields=('fps','gradientScreens','gradientAngle','gradientSpeed','gradientPhase','pivotX','pivotY','axisPitch','rotationSpeed','secondAxisSpeed','swingAngle','swingSeconds','starDensity','starGlyphs','starCount','starSpeed','trailMs','travelYaw','travelPitch','weatherIntensity','novaStrength','novaRegularity','backgroundStyle','sampling','orbitMode','motion','weatherLifeMs','weatherSpeed')
 result.append({'op':'window-application','scene':'observatory','paletteWindowId':1,**{k:o[k]for k in fields}})
 for event in source['events']:result.append({'op':'window-application-event',**{k:v for k,v in event.items()if k!='glyph'}})
 return result
def overlay(row):return {'op':'observatory-overlay','kind':row['request']['scene'],**{k:row['source']['options'][k]for k in ('fallMs','hueStep','textHueSpeed','flatNavigation')}}
def node_commands(row):
 out=[]
 for i,n in enumerate(row['nodes']):
  n=copy.deepcopy(n);legacy=n.pop('id',0);out.append({'op':'source-stage-component','id':i+1,'legacyFlags':legacy,**n})
 return out
def visual(words):return [tuple(words[i:i+3])for i in range(0,len(words),4)]
class OriginalObservatoryOverlay(unittest.TestCase):
 def scene(self):return NativeScene(library=os.environ.get('NOCTURNE_REVIEW_LIBRARY'))
 def prepare(self,s,row):
  for c in commands(row):s.command(c)
  s.advance_to(row['request']['timeMs']*1000)
 def assert_frame(self,s,words,label):
  before=s.snapshot();actual=list(memoryview(s.render().bytes).cast('I'));self.assertEqual(s.snapshot(),before,'render purity')
  a,b=visual(actual),visual(words);self.assertEqual(len(a),len(b));diff=[(i,b[i],a[i])for i in range(len(a))if a[i]!=b[i]];self.assertFalse(diff,f'{label}: {len(diff)} cells differ; first {diff[:5]}');return actual
 def test_public_disable_command_exists_and_has_owned_readback(self):
  with self.scene() as s:s.command({'op':'observatory-overlay','enabled':False});self.assertEqual(s.info_complete()['observatoryOverlay'],{'enabled':False})
 def test_warp_workspace_kind_preserves_authored_background(self):
  with self.scene() as s:
   self.prepare(s,rows()[0]);s.command({'op':'observatory-overlay','kind':'warp'});self.assertEqual(s.info_complete()['observatoryOverlay']['kind'],'warp');self.assertEqual(s.info_complete()['windowApplication']['backgroundStyle'],'double-axis')
 def test_all_original_underlays_and_complete_frames(self):
  for row in rows():
   with self.subTest(id=row['id']),self.scene() as s:
    self.prepare(s,row)
    if row['background'] is not None:self.assert_frame(s,row['background'],'background '+row['id'])
    s.command(overlay(row));actual=self.assert_frame(s,row['underlay'],'underlay '+row['id']);self.assertTrue(all(actual[i]==0 for i in range(3,len(actual),4)))
    for c in node_commands(row):s.command(c)
    self.assert_frame(s,row['frame']['cells'],'complete '+row['id'])
 def test_dependencies_domain_and_late_batch_are_atomic(self):
  row=rows()[0]
  with self.scene() as s:
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(overlay(row))
   self.assertEqual(s.snapshot(),before);self.prepare(s,row);s.command(overlay(row));before=s.snapshot();frame=s.render().bytes
   invalid=[{'fallMs':-1},{'fallMs':4001},{'hueStep':-90.1},{'textHueSpeed':90.1},{'flatNavigation':1},{'kind':'windows'},{'enabled':False,'fallMs':1},{'unknown':1}]
   for patch in invalid:
    with self.assertRaises(ValueError):s.command({'op':'observatory-overlay',**patch})
    self.assertEqual(s.snapshot(),before);self.assertEqual(s.render().bytes,frame)
   for bad in [{'op':'remove-window-application'},{'op':'window-application','scene':'windows'},{'op':'remove-window','id':1}]:
    with self.assertRaises(ValueError):s.command(bad)
    self.assertEqual(s.snapshot(),before)
   with self.assertRaises(ValueError):s.command({'op':'batch','commands':[{'op':'observatory-overlay','fallMs':0},{'op':'observatory-overlay','textHueSpeed':91}]})
   self.assertEqual(s.snapshot(),before)
   with self.assertRaises(ValueError):s.command_raw(b'{"op":"observatory-overlay","fallMs":1e999}')
   self.assertEqual(s.snapshot(),before);s.command({'op':'observatory-overlay','enabled':False});s.command({'op':'window-application','scene':'windows'});self.assertEqual(s.info_complete()['observatoryOverlay'],{'enabled':False})
 def test_defaults_patches_snapshot_corruption_and_reset(self):
  row=rows()[0]
  with self.scene() as s:
   self.prepare(s,row);s.command({'op':'observatory-overlay','kind':'text'});info=s.info_complete()['observatoryOverlay'];self.assertEqual([info[k]for k in ('fallMs','hueStep','textHueSpeed','flatNavigation')],[1100,13,12,False]);s.command({'op':'observatory-overlay','fallMs':0,'hueStep':-90,'textHueSpeed':90});self.assertEqual(s.info_complete()['observatoryOverlay']['kind'],'text')
   before=s.snapshot();frame=s.render().bytes;s.command({'op':'reset'});s.restore(before);self.assertEqual(s.snapshot(),before);self.assertEqual(s.render().bytes,frame)
   for offset,value in [(30494208+12,1),(30494208+4,99)]:
    bad=bytearray(before);struct.pack_into('<I',bad,24+offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]));
    with self.assertRaises(ValueError):s.restore(bad)
    self.assertEqual(s.snapshot(),before)
   s.command({'op':'reset'});self.assertFalse(s.info_complete()['observatoryOverlay']['enabled'])
 def assert_migrated_snapshot(self,s,raw,old_fixed):
  saved=s.snapshot();layout=current_wire_layout();fixed=layout['fixed'];schema=layout['schema']
  self.assertEqual(struct.unpack_from('<I',saved,12)[0],schema)
  self.assertEqual(struct.unpack_from('<I',saved,28)[0],schema)
  self.assertEqual(s.info_complete()['contract']['snapshotSchema'],schema)
  self.assertEqual(struct.unpack_from('<I',saved,16)[0],len(saved)-24)
  self.assertEqual(struct.unpack_from('<I',saved,20)[0],zlib.crc32(saved[24:]))
  self.assertGreater(fixed,old_fixed)
  self.assertEqual(len(saved)-len(raw),fixed-old_fixed)
  self.assertTrue(saved[32:24+old_fixed]==raw[32:24+old_fixed],'historical fixed prefix differs')
  self.assertFalse(any(saved[24+old_fixed:24+fixed]),'new appendices must initialize disabled')
  self.assertTrue(saved[24+fixed:]==raw[24+old_fixed:],'complete prompt/model suffix differs')
  s.restore(saved);self.assertTrue(s.snapshot()==saved,'current writer roundtrip differs')
  return saved
 def test_genuine91_whole_document_model_frame_migration(self):
  raw=gzip.decompress((FIX/'genuine91-snapshot.gz').read_bytes());proof=json.loads((FIX/'GENUINE91-PROVENANCE.json').read_text())
  with self.scene() as s:
   s.restore(raw);self.assertEqual(s.render().bytes,gzip.decompress((FIX/'genuine91-frame.gz').read_bytes()));self.assertEqual(len(s.info_complete()['prompt']['text']),70005);self.assertEqual(hashlib.sha256(s.model_records()).hexdigest(),proof['modelSha256']);self.assertFalse(s.info_complete()['observatoryOverlay']['enabled']);self.assert_migrated_snapshot(s,raw,30494208)
 def test_genuine92_whole_document_model_overlay_replay(self):
  fixture=ROOT/'tests/fixtures/original-observatory-schema92';raw=gzip.decompress((fixture/'snapshot.gz').read_bytes());proof=json.loads((fixture/'PROVENANCE.json').read_text());frame=gzip.decompress((fixture/'frame.gz').read_bytes())
  self.assertEqual(hashlib.sha256(raw).hexdigest(),proof['snapshotSha256']);self.assertEqual(hashlib.sha256(frame).hexdigest(),proof['frameSha256'])
  with self.scene() as s:
   s.restore(raw);saved=self.assert_migrated_snapshot(s,raw,30494248);self.assertEqual(s.render().bytes,frame);self.assertEqual(len(s.info_complete()['prompt']['text']),70005);self.assertEqual(hashlib.sha256(s.model_records()).hexdigest(),proof['modelSha256']);self.assertEqual(s.info_complete()['observatoryOverlay']['kind'],'dag');self.assertTrue(s.snapshot()==saved,'render/query changed the migrated snapshot')
 def test_actual_import_free_wasm_complete_frames_and_migration(self):
  source=rows();requests=[{'id':r['id'],'commands':commands(r),'overlay':overlay(r),'nodes':node_commands(r),'atUs':r['request']['timeMs']*1000}for r in source]
  with tempfile.TemporaryDirectory() as d:
   inp=Path(d)/'requests.json';out=Path(d)/'actual.json';inp.write_text(json.dumps(requests));run=subprocess.run([os.environ.get('NODE','node'),str(ROOT/'tests/original_observatory_overlay_wasm.mjs'),str(inp),str(out)],capture_output=True,text=True,timeout=180);self.assertEqual(run.returncode,0,run.stderr[-3000:]);actual=json.loads(out.read_text());self.assertEqual(len(actual),len(source))
   for a,b in zip(actual,source):
    with self.subTest(id=b['id']):self.assertEqual(a['id'],b['id']);self.assertEqual(visual(a['underlay']),visual(b['underlay']));self.assertTrue(all(a['underlay'][i]==0 for i in range(3,len(a['underlay']),4)));self.assertEqual(visual(a['frame']),visual(b['frame']['cells']))
if __name__=='__main__':unittest.main(verbosity=2)
