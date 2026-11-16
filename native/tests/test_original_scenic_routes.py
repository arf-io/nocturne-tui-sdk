"""Normal original scenic artwork routes, not generic substitute studies."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import sys,unittest,json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'))
from gallery_cases import build_cases
class OriginalScenicRoutes(unittest.TestCase):
 def test_four_original_normal_routes_and_source_defaults(self):
  cases={c['id']:c for c in build_cases()}
  for name,title in [('pearl-cascade','Pearl Cascade'),('copper-causeway','Copper Causeway'),('tidal-glass','Tidal Glass'),('silt','Silt')]:
   self.assertTrue('original-'+name in cases, 'missing original-'+name)
   c=cases['original-'+name];self.assertEqual(c['name'],title);self.assertTrue(c['demo']);self.assertEqual(c['originalScenic'],name)
   a=next(x for x in c['commands'] if x['op']=='scene-art');self.assertEqual(a['scene'],name)
   self.assertEqual(a['controls']['background'],0x101319);self.assertEqual(a['controls']['cameraZ'],-96);self.assertEqual(a['controls']['span'],170 if name=='pearl-cascade' else 220);self.assertEqual(a['controls']['cameraY'],58 if name=='pearl-cascade' else 48)
   self.assertEqual(a['detail'],dict(waveHeight=358/256,wavelength=34,windAngle=22,crossSwell=.48,choppiness=.43,foam=.62,waveSpeed=1,joinRiver=1))
   self.assertTrue(c['provenance']);self.assertEqual(c['viewport'],dict(width=160,height=52))

 def test_original_host_timed_frames_native_and_wasm(self):
  from original_scenic_routes import build_original_scenic_routes
  from native.bindings.python.nocturne_native import NativeScene
  cases=build_original_scenic_routes();run=subprocess.run(['node',str(ROOT/'tests/scenic_original_host_oracle.mjs')],input=json.dumps(cases),text=True,capture_output=True);self.assertEqual(run.returncode,0,run.stderr)
  report=json.loads(run.stdout);self.assertEqual(len(report['cases']),4)
  for case in report['cases']:
   with NativeScene(2030) as scene:
    for c in case['commands']:scene.command(c)
    for step in case['steps']:
     scene.advance_to(step['timeUs']);scene.command(step['command']);
     if 'view' in step:scene.command(dict(op='scene-art',controls=step['view']))
     frame=scene.render();self.assertEqual(hashlib.sha256(frame.bytes).hexdigest(),step['frameSha256'],case['id']+' '+str(step['timeUs']));self.assertEqual(frame.width*frame.height,step['cells'])
