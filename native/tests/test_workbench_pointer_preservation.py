"""Real current SDK regressions for retained Workbench gestures; no fake hit map."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import math, os, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LIBRARY=os.environ.get('NOCTURNE_NATIVE_LIBRARY')
sys.path.insert(0,str(ROOT))
from native.bindings.python.nocturne_native import NativeScene
W,H=120,48
class WorkbenchPointerPreservation(unittest.TestCase):
 def scene(self,profile):
  s=NativeScene(2030,library=LIBRARY);self.addCleanup(s.close)
  for c in [{'op':'resize','width':W,'height':H},{'op':'environment','stars':0},{'op':'floor','visible':False},{'op':'prompt','active':False},{'op':'camera','profile':profile,'position':[0,0,60],'yaw':0,'pitch':0,'roll':0}]:s.command(c)
  return s
 def point(self,s,id):
  index=next(i for i,w in enumerate(s.render().words()) if w[3]==id)
  return {'x':index%W+.25,'y':index//W+.25}
 def test_right_button_over_node_pans_without_selection(self):
  for profile in ('default','original'):
   with self.subTest(profile=profile):
    s=self.scene(profile);s.command({'op':'node','id':1,'label':'Source node','position':[-14,0,0],'pinned':True,'showKind':False,'showStatus':False,'showSha':False});p=self.point(s,0x10000001);before=s.info()['camera']
    s.command({'op':'pointer','phase':'down','button':2,**p});s.command({'op':'pointer','phase':'move','button':2,'x':p['x']+3,'y':p['y']+2})
    self.assertEqual(s.info()['selection'],0,'right-button pan must not select a graph node')
    after=s.info()['camera'];self.assertNotEqual(after['position'],before['position']);self.assertEqual(after['yaw'],before['yaw']);self.assertEqual(after['pitch'],before['pitch'])
 def test_alt_window_drag_changes_yaw_pitch_and_preserves_roll(self):
  for profile in ('default','original'):
   with self.subTest(profile=profile):
    s=self.scene(profile);s.command({'op':'window','id':1,'title':'Original','position':[0,0,0],'width':30,'height':18,'yaw':3,'pitch':4,'roll':5});s.advance_to(1000000);p=self.point(s,0x20000001);before=s.info()['windows'][0]
    s.command({'op':'pointer','phase':'down','button':0,'alt':True,**p});s.command({'op':'pointer','phase':'move','button':0,'alt':True,'x':p['x']+2,'y':p['y']+1});after=s.info()['windows'][0]
    self.assertEqual(after['roll'],before['roll'],'original Alt drag rotates yaw/pitch, not roll')
    self.assertAlmostEqual(after['yaw'],7.8,places=5);self.assertAlmostEqual(after['pitch'],-.8,places=5);self.assertEqual(after['position'],before['position'])
 def test_wheel_keeps_active_cruise_and_explicit_brake_still_stops(self):
  for profile in ('default','original'):
   with self.subTest(profile=profile):
    s=self.scene(profile);s.command({'op':'flight',**({'profile':'original'}if profile=='original'else{}),'steps':[{'kind':'cruise','durationMs':5000,'speed':10}]});s.advance_to(1000000);s.render();before=s.info()['camera']
    s.command({'op':'wheel','delta':1,'x':5,'y':10});after=s.info()['camera'];self.assertTrue(after['flightActive'],'wheel must not silently brake original cruise');self.assertNotEqual(after['position'],before['position'])
    s.advance_to(2000000);moving=s.info()['camera'];self.assertGreater(math.dist(after['position'],moving['position']),9.99);s.command({'op':'brake'});self.assertFalse(s.info()['camera']['flightActive'])
 def test_primary_node_selection_and_middle_orbit_stay_available(self):
  for profile in ('default','original'):
   with self.subTest(profile=profile):
    s=self.scene(profile);s.command({'op':'node','id':1,'label':'Source node','position':[-14,0,0],'pinned':True,'showKind':False,'showStatus':False,'showSha':False});p=self.point(s,0x10000001)
    s.command({'op':'pointer','phase':'down','button':1,**p});self.assertEqual(s.info()['selection'],0);self.assertIsNotNone(s.info()['camera'].get('grabbed'));s.command({'op':'pointer','phase':'cancel',**p});p=self.point(s,0x10000001)
    s.command({'op':'pointer','phase':'down','button':0,**p});self.assertEqual(s.info()['selection'],1)
 def test_alt_clamps_match_genuine_original_source_rows(self):
  import gzip,json
  fixture=Path(__file__).parent/'fixtures/original-workbench-pointer/ORIGINAL-GESTURE-ORACLE.json.gz'
  source=json.loads(gzip.decompress(fixture.read_bytes()))
  for row in source['rows']:
   if not row['id'].startswith('alt-window-'):continue
   original=next(w for w in row['after']['windows'] if w['id']==row['intent']['windowId'])
   for profile in ('default','original'):
    with self.subTest(row=row['id'],profile=profile):
     s=self.scene(profile);s.command({'op':'window','id':1,'title':'Source angle','position':[0,0,0],'width':30,'height':18,'yaw':3,'pitch':4,'roll':5});s.advance_to(1000000);p=self.point(s,0x20000001)
     s.command({'op':'pointer','phase':'down','button':0,'alt':True,**p});dx,dy=row['delta'];s.command({'op':'pointer','phase':'move','button':0,'alt':True,'x':p['x']+dx,'y':p['y']+dy});window=s.info()['windows'][0]
     self.assertAlmostEqual(window['yaw'],original['yaw']);self.assertAlmostEqual(window['pitch'],original['pitch']);self.assertEqual(window['roll'],5)
 def test_right_pan_modifier_precedence_and_up_cancel_end_capture(self):
  for end in ('up','cancel'):
   for profile in ('default','original'):
    with self.subTest(end=end,profile=profile):
     s=self.scene(profile);s.command({'op':'node','id':1,'label':'Source node','position':[-14,0,0],'pinned':True,'showKind':False,'showStatus':False,'showSha':False});p=self.point(s,0x10000001)
     s.command({'op':'pointer','phase':'down','button':2,'alt':True,'shift':True,**p});s.command({'op':'pointer','phase':'move','button':2,'x':p['x']+2,'y':p['y']+1});self.assertEqual(s.info()['selection'],0)
     s.command({'op':'pointer','phase':end,'button':2,'x':p['x']+2,'y':p['y']+1});camera=s.info()['camera'];s.command({'op':'pointer','phase':'move','button':2,'x':p['x']+8,'y':p['y']+7});self.assertEqual(s.info()['camera'],camera)
 def test_wheel_flight_snapshot_replay_and_late_batch_rejection(self):
  for profile in ('default','original'):
   with self.subTest(profile=profile):
    s=self.scene(profile);s.command({'op':'flight',**({'profile':'original'}if profile=='original'else{}),'steps':[{'kind':'turn','durationMs':5000,'speed':10,'yaw':55,'bank':28},{'kind':'climb','durationMs':2000,'speed':10,'pitch':25}]});s.advance_to(1000000);s.render();before=s.snapshot();frame=s.render().bytes
    with self.assertRaises(ValueError):s.command({'op':'batch','commands':[{'op':'wheel','delta':1,'x':5,'y':10},{'op':'this-is-not-a-command'}]})
    self.assertEqual(s.snapshot(),before);self.assertEqual(s.render().bytes,frame)
    s.command({'op':'wheel','delta':1,'x':5,'y':10});self.assertTrue(s.info()['camera']['flightActive']);saved=s.snapshot();s.advance_to(3000000);expected=s.info()['camera'];frame=s.render().bytes
    s.restore(saved);s.advance_to(3000000);self.assertEqual(s.info()['camera'],expected);self.assertEqual(s.render().bytes,frame);self.assertTrue(expected['flightActive'])
 def test_prompt_plane_and_help_modal_keep_wheel_ownership(self):
  for profile in ('default','original'):
   with self.subTest(profile=profile):
    s=self.scene(profile);s.command({'op':'prompt','active':True});s.command({'op':'draft','text':'Preserved prompt'});s.render();before=s.info()['camera'];s.command({'op':'wheel','delta':1,'x':5,'y':H-2});self.assertEqual(s.info()['camera'],before)
    s.command({'op':'key','key':'F1'});s.render();s.command({'op':'wheel','delta':1,'x':5,'y':10});self.assertEqual(s.info()['camera'],before);self.assertEqual(s.info()['prompt']['text'],'Preserved prompt')
 def test_native_wasm_replays_every_focused_public_call(self):
  import tempfile,subprocess,json
  with tempfile.TemporaryDirectory(prefix='nocturne-pointer-trace-') as folder:
   folder=Path(folder);trace=folder/'trace.json';result=folder/'wasm.json'
   subprocess.run([sys.executable,'-B',str(ROOT/'native/tests/workbench_pointer_trace.py'),str(ROOT),str(trace)],check=True,capture_output=True,text=True)
   subprocess.run([os.environ.get('NODE','node'),str(ROOT/'native/tests/original_workbench_pointer_wasm.mjs'),str(trace),str(result)],check=True,capture_output=True,text=True)
   data=json.loads(result.read_text());self.assertTrue(data['passed']);self.assertEqual(data['contexts'],22);self.assertEqual(data['steps'],328);self.assertEqual(data['frames'],34);self.assertEqual(data['snapshots'],6);self.assertEqual(data['rejections'],2)
if __name__=='__main__':unittest.main(verbosity=2)
