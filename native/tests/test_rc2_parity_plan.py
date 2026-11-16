"""The release replay exercises changed contracts through the real SDK."""
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from parity import representativePlan
class RC2ParityPlan(unittest.TestCase):
 def test_replay_accepts_every_declared_transaction_and_preserves_document(self):
  commands=representativePlan()
  self.assertLess(len(commands),600);self.assertGreater(len(commands),200)
  with NativeScene() as scene:
   for index,command in enumerate(commands):
    with self.subTest(index=index,op=command['op']):scene.command(command)
   self.assertEqual(scene.info()['prompt']['text'],'界é 🪷'+('x'*70000))
   self.assertEqual(scene.info()['prompt']['appearance']['weather']['style'],'snow')
   before=scene.snapshot();frame=scene.render().bytes;self.assertEqual(scene.snapshot(),before)
   scene.restore(before);self.assertEqual(scene.render().bytes,frame)
 def test_plan_names_every_rig_and_widget_without_recipe_cartesian_product(self):
  commands=representativePlan()
  self.assertEqual({x['rig'] for x in commands if x['op']=='camera-controls' and 'rig'in x},{'orbit','head','dolly','crane','follow','spacecraft'})
  self.assertEqual(len({x['kind'] for x in commands if x['op']=='widget'}),18)
  def commands_recursive(rows):
   for x in rows:
    yield x
    if x['op']=='batch':yield from commands_recursive(x['commands'])
  self.assertEqual({x['scene'] for x in commands_recursive(commands) if x['op']=='scene-art' and 'scene'in x},{'pearl-cascade','copper-causeway','tidal-glass','silt'})
if __name__=='__main__':unittest.main()
