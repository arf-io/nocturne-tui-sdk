"""Real independent scenic clock, original frames and genuine94 migration."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,hashlib,json,math,os,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.test_scenic_public import isolate_scenic_renderer,source_command
from native.tests.current_writer_contract import current_schema
from native.tests.constructed_dynamic_legacy_snapshot import layout
from native.tests.original_scenic_samples import OriginalScenicSamples
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence/original-scenic-restoration-20261013'
FIXTURE=ROOT/'tests/fixtures/original-scenic-schema94'
MAX_TIME=9007199254740991
OLD_FIXED=30499728
CLOCK_BYTES=16

def digest(b):return hashlib.sha256(b).hexdigest()
def setup(s,name='pearl-cascade'):
 isolate_scenic_renderer(s);s.command({'op':'scene-art','scene':name,'width':80,'height':32})

def visual(data):
 return b"".join(data[i:i+12] for i in range(0,len(data),16))

class SceneArtClock(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix="scene-clock-reference-")
  cls.addClassCleanup(cls.temp.cleanup);cls.reference=Path(cls.temp.name)
  cls.layout=layout()
  if cls.layout['schema']!=current_schema():raise AssertionError("Current schema disagrees with compiled layout")
  clock=next(x for x in cls.layout['appendFields'] if x['name']=='sceneArtClock')
  if (clock['offset'],clock['bytes'])!=(OLD_FIXED,CLOCK_BYTES):raise AssertionError("Historical94 boundary changed")
  cls.frames=json.loads((EVIDENCE/'ORIGINAL-WORLD-FRAMES.json').read_text())['frames']
  oracle=OriginalScenicSamples(cls.reference)
  for f in cls.frames:
   target=cls.reference/f['cellsFile'];target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(oracle.expected(f,(EVIDENCE/f['cellsFile']).read_bytes()))
  with NativeScene() as scene:
   scene.restore(gzip.decompress((FIXTURE/'snapshot.gz').read_bytes()))
   (cls.reference/'genuine94-current.cells').write_bytes(scene.render().bytes)
  (cls.reference/'contract.json').write_text(json.dumps({'schema':current_schema(),'fixed':cls.layout['fixed'],
     'expected':{f['id']:digest((cls.reference/f['cellsFile']).read_bytes()) for f in cls.frames},
     'genuine94CurrentSha256':digest((cls.reference/'genuine94-current.cells').read_bytes())}))

 def assertBytes(self,a,b):
  self.assertEqual(len(a),len(b));self.assertEqual(digest(a),digest(b))
 def test_independent_clock_preserves_original_frames_and_render_purity(self):
  manifest=json.loads((EVIDENCE/'ORIGINAL-WORLD-FRAMES.json').read_text())
  for fixture in manifest['frames']:
   with self.subTest(frame=fixture['id']),NativeScene(2030) as s:
    isolate_scenic_renderer(s,fixture);command=source_command(fixture);command['timeMs']=fixture['timeMs'];s.command(command);s.advance_to(12345678)
    info=s.info_complete()['sceneArt'];self.assertEqual(info['timeMs'],fixture['timeMs']);self.assertEqual(info['effective']['timeMs'],fixture['timeMs'])
    saved=s.snapshot();a=s.render();self.assertBytes(a.bytes,s.render().bytes);self.assertBytes(saved,s.snapshot())
    expected=(self.reference/fixture['cellsFile']).read_bytes();self.assertBytes(visual(a.bytes),visual(expected));self.assertTrue(all(row[3]==0 for row in a.words()))
 def test_omission_switch_null_and_global_clock(self):
  with NativeScene() as s,NativeScene() as ref:
   setup(s);setup(ref);s.command({'op':'scene-art','timeMs':2000});ref.advance_to(2000000);self.assertBytes(s.render().bytes,ref.render().bytes)
   s.advance_to(9000123);s.command({'op':'scene-art','controls':{'waterAlpha':.8}});self.assertEqual(s.info_complete()['sceneArt']['timeMs'],2000)
   s.command({'op':'scene-art','scene':'tidal-glass'});self.assertEqual(s.info_complete()['sceneArt']['timeMs'],2000)
   s.command({'op':'scene-art','timeMs':None});self.assertIsNone(s.info_complete()['sceneArt']['timeMs']);self.assertEqual(s.info_complete()['sceneArt']['effective']['timeMs'],9000)
   s.command({'op':'scene-art','scene':'pearl-cascade','controls':{'waterAlpha':.94}});ref.advance_to(9000123);self.assertBytes(s.render().bytes,ref.render().bytes)
 def test_safe_integer_boundaries_and_invalid_values_are_atomic(self):
  with NativeScene() as s:
   setup(s)
   for t in [0,1,4294967296,MAX_TIME]:
    s.command({'op':'scene-art','timeMs':t});self.assertEqual(s.info_complete()['sceneArt']['timeMs'],t);self.assertEqual(s.info_complete()['sceneArt']['effective']['timeMs'],t);s.render()
   saved=s.snapshot()
   for v in [-1,.25,MAX_TIME+1,'2000',True,[],{},float('nan'),float('inf'),-float('inf')]:
    with self.subTest(value=repr(v)):
     with self.assertRaises((ValueError,TypeError)):s.command({'op':'scene-art','timeMs':v})
     self.assertBytes(s.snapshot(),saved)
   with self.assertRaises(ValueError):s.command({'op':'model-view','timeMs':0})
   self.assertBytes(s.snapshot(),saved)
 def test_reset_remove_and_scoped_clear_remove_clock(self):
  for clear in [{'op':'reset'},{'op':'remove-scene-art'},{'op':'clear','scope':'scene-art'}]:
   with self.subTest(clear=clear),NativeScene() as s:
    setup(s);s.command({'op':'scene-art','timeMs':1234});s.command(clear);self.assertIsNone(s.info_complete()['sceneArt']);s.command({'op':'scene-art','scene':'silt'});self.assertIsNone(s.info_complete()['sceneArt']['timeMs'])
 def test_scheduled_replay_and_late_batch_rejection(self):
  with NativeScene() as s,NativeScene() as restored:
   setup(s);s.command({'op':'scene-art','timeMs':0});s.schedule(441,500000,{'op':'scene-art','timeMs':777});saved=s.snapshot();restored.restore(saved)
   for scene in [s,restored]:scene.advance_to(500000)
   self.assertBytes(s.snapshot(),restored.snapshot());self.assertBytes(s.render().bytes,restored.render().bytes);self.assertEqual(s.info_complete()['sceneArt']['timeMs'],777)
   saved=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'batch','commands':[{'op':'scene-art','timeMs':9000},{'op':'scene-art','timeMs':-1}]})
   self.assertBytes(saved,s.snapshot())
 def test_clock_footer_corruption_rejected_atomically(self):
  with NativeScene() as s:
   setup(s);s.command({'op':'scene-art','timeMs':1234});saved=s.snapshot();self.assertEqual(struct.unpack_from('<I',saved,12)[0],current_schema())
   for offset,fmt,value in [(0,'I',2),(4,'I',1),(8,'d',-1),(8,'d',.5),(8,'d',float('nan')),(8,'d',float('inf')),(8,'d',MAX_TIME+1)]:
    bad=bytearray(saved);struct.pack_into('<'+fmt,bad,24+OLD_FIXED+offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
    with self.subTest(offset=offset,value=repr(value)):
     with self.assertRaises(ValueError):s.restore(bad)
     self.assertBytes(saved,s.snapshot())
   bad=bytearray(saved);struct.pack_into('<I',bad,24+OLD_FIXED,0);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertBytes(saved,s.snapshot())
 def test_constructed94_pending_clock_rejected_without_promotion(self):
  # Explicit test construction, not a genuine historical-writer fixture.
  with NativeScene() as s:
   setup(s);s.schedule(442,500000,{'op':'scene-art','timeMs':777});saved=s.snapshot()
   self.assertEqual(saved[24+OLD_FIXED:24+self.layout['fixed']],bytes(self.layout['fixed']-OLD_FIXED))
   old=bytearray(saved[:24+OLD_FIXED]+saved[24+self.layout['fixed']:])
   for offset,value in [(12,0x20261094),(28,0x20261094),(16,len(old)-24)]:struct.pack_into('<I',old,offset,value)
   struct.pack_into('<I',old,20,zlib.crc32(old[24:]))
   with self.assertRaises(ValueError):s.restore(old)
   self.assertBytes(saved,s.snapshot())
 def test_genuine94_document_model_modal_camera_frame_migrates(self):
  raw=gzip.decompress((FIXTURE/'snapshot.gz').read_bytes());frame=gzip.decompress((FIXTURE/'frame.gz').read_bytes());proof=json.loads((FIXTURE/'PROVENANCE.json').read_text())
  self.assertEqual(digest(raw),proof['snapshotSha256']);self.assertEqual(digest(frame),proof['frameSha256']);self.assertEqual(struct.unpack_from('<I',raw,12)[0],0x20261094)
  with NativeScene() as s,NativeScene() as r:
   s.restore(raw);info=s.info_complete();self.assertIsNone(info['sceneArt']['timeMs']);self.assertEqual(len(info['prompt']['text']),70005);self.assertEqual(len(info['sourceModal']['query']),80000);self.assertEqual(info['sourceModel']['triangles'],4608);self.assertEqual(info['camera']['controls']['rig'],'spacecraft')
   current_frame=s.render().bytes
   current=s.snapshot();fixed=self.layout['fixed'];self.assertEqual(struct.unpack_from('<I',current,12)[0],current_schema());self.assertEqual(len(current),len(raw)+fixed-OLD_FIXED);self.assertBytes(current[32:24+OLD_FIXED],raw[32:24+OLD_FIXED]);self.assertEqual(current[24+OLD_FIXED:24+fixed],bytes(fixed-OLD_FIXED));self.assertBytes(current[24+fixed:],raw[24+OLD_FIXED:]);r.restore(current);self.assertBytes(r.snapshot(),current);self.assertBytes(r.render().bytes,current_frame)
   # Exact old mixed frame remains checked in explicit half mode; braille's
   # independent eight-sample correction is checked above, not a color mask.
   half=gzip.decompress((FIXTURE/'half-frame.gz').read_bytes());receipt=json.loads((FIXTURE/'HALF-PROVENANCE.json').read_text())
   self.assertEqual(receipt['genuine94SnapshotSha256'],digest(raw));self.assertEqual(receipt['genuine94BrailleFrameSha256'],digest(frame));self.assertTrue(receipt['originalBrailleFrameVerifiedBeforeCommand']);self.assertEqual(digest(half),receipt['frameSha256'])
   self.assertEqual(receipt['commandsAfterRestore'],[{'op':'scene-art','controls':{'sampling':0}}])
   s.command(receipt['commandsAfterRestore'][0]);self.assertBytes(s.render().bytes,half)
 def test_constructed94_compatible_payload_restores_before_rejecting_clock(self):
  # Positive companion ensures the negative is semantic, not a malformed layout.
  with NativeScene() as s:
   setup(s);s.schedule(443,500000,{'op':'scene-art','controls':{'flow':.5}});saved=s.snapshot();fixed=self.layout['fixed']
   self.assertEqual(saved[24+OLD_FIXED:24+fixed],bytes(fixed-OLD_FIXED))
   old=bytearray(saved[:24+OLD_FIXED]+saved[24+fixed:])
   for offset,value in [(12,0x20261094),(28,0x20261094),(16,len(old)-24)]:struct.pack_into('<I',old,offset,value)
   struct.pack_into('<I',old,20,zlib.crc32(old[24:]));s.restore(old);s.advance_to(500000)
   self.assertEqual(s.info_complete()['sceneArt']['controls']['flow'],.5)

 def test_actual_public_wasm_clock_and_genuine94_migration(self):
  result=subprocess.run([os.environ.get('NODE','node'),str(ROOT/'tests/scene_art_clock_wasm.mjs'),str(self.reference)],capture_output=True,text=True,timeout=180)
  self.assertEqual(result.returncode,0,(result.stdout+result.stderr)[-4000:]);report=json.loads(result.stdout);self.assertTrue(report['passed']);self.assertEqual(report['schema'],current_schema());self.assertEqual(report['originalFrames'],16);self.assertTrue(report['genuine94'])
if __name__=='__main__':unittest.main()
