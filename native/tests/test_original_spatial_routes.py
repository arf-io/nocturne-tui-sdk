"""Normal picker routes select original spatial artwork and choreography."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy,json,unittest
from pathlib import Path
from native.bindings.python.nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1]
class OriginalSpatialRoutes(unittest.TestCase):
 def test_normal_flight_picker_variants_use_original_paths_and_trails(self):
  recipes={r['id']:r for r in json.loads((ROOT/'recipes.json').read_text())}
  for key in ['flight','flight-banked','flight-flat','flight-climb-roll-dive']:
   self.assertIn(key,recipes)
   commands=recipes[key]['commands'];self.assertTrue(any(c.get('starProfile')=='source' for c in commands));self.assertTrue(any(c.get('op')=='flight'and c.get('profile')=='original'for c in commands))
   with NativeScene() as scene:
    for c in commands:scene.command(c)
    scene.advance_to(2000000);before=scene.info()['camera'];scene.command({'op':'camera','yaw':before['yaw']+7});scene.advance_to(3000000);after=scene.info()['camera'];self.assertTrue(after['flightActive']);self.assertNotEqual(before['position'],after['position']);self.assertEqual(scene.info()['sourceSky']['trailMs'],100)
  turns=[next(c for c in recipes[k]['commands']if c.get('op')=='flight')['steps'][0]for k in ['flight-banked','flight-flat']]
  self.assertTrue(turns[0]['coordinated']);self.assertFalse(turns[1]['coordinated'])
  self.assertEqual([s['kind']for s in next(c for c in recipes['flight-climb-roll-dive']['commands']if c.get('op')=='flight')['steps']],['climb','roll','dive'])
 def test_normal_task_graph_source_layout_fit_and_flat_readability(self):
  recipes={r['id']:r for r in json.loads((ROOT/'recipes.json').read_text())};commands=[json.loads(l)for l in (ROOT/'examples/task_graph.ndjson').read_text().splitlines()if l];self.assertEqual(recipes['task-graph']['commands'],commands)
  self.assertTrue(any(c.get('op')=='layout'and c.get('profile')=='source'and c.get('dimensions')==3 for c in commands))
  with NativeScene() as scene:
   for c in commands:scene.command(c)
   scene.advance_to(900000);spatial=scene.render().bytes;info=scene.info();self.assertEqual(info['camera']['yaw'],-28);self.assertEqual(info['graph']['layoutProfile'],'source');self.assertGreater(len({round(n['position'][2],3)for n in info['nodes']}),2)
   metadata=copy.deepcopy([(n['id'],n['label'],n['sha'],n['detail'])for n in info['nodes']])
   for c in [{'op':'camera','profile':'default','position':[0,8,162],'yaw':0,'pitch':0,'roll':0,'fov':64,'orthographic':False},{'op':'layout','mode':'layered','dimensions':2,'spacing':30}]:scene.command(c)
   scene.advance_to(1900000);flat=scene.render();self.assertNotEqual(flat.bytes,spatial);self.assertEqual(metadata,[(n['id'],n['label'],n['sha'],n['detail'])for n in scene.info()['nodes']]);screen=''.join(chr(w[0])for w in flat.words())
   for node in info['nodes']:self.assertIn(node['label'],screen)
