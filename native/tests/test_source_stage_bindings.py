import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class SourceStageOwnedBinding(unittest.TestCase):
 def test_original_queries_and_bounds(self):
  with NativeScene() as s:
   s.command({'op':'source-stage-component','id':1,'legacyFlags':100001,'kind':'button','x':2,'y':3,'width':10,'height':3})
   before=s.snapshot();self.assertEqual(s.source_stage_tween(-200,1000,210,420),400);self.assertEqual(s.source_stage_ink_opacity(420,420,768,1536,760),880);self.assertEqual(s.source_stage_hit(3,4),{'id':100001,'item':0});self.assertIsNone(s.source_stage_hit(-1,-1))
   for fn,args in [(s.source_stage_tween,(0,1,0,1,4)),(s.source_stage_tween,(True,1,0,1)),(s.source_stage_tween,(0,1,-1,1)),(s.source_stage_ink_opacity,(0,1,0,-1,0)),(s.source_stage_hit,(4097,0))]:
    with self.assertRaises(ValueError):fn(*args)
   self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main(verbosity=2)
