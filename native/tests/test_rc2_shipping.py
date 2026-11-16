"""Shipping comparison rejects changed real replay bytes and stale source bindings."""
import sys,tempfile,unittest,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from finish_rc2 import replayBinding,requireSameReplay
class RC2Shipping(unittest.TestCase):
 def test_real_replay_bytes_are_bound_in_each_language(self):
  with tempfile.TemporaryDirectory() as d,NativeScene() as scene:
   root=Path(d);frame=scene.render().bytes;record={'index':0,'frame':hashlib.sha256(frame).hexdigest(),'state':hashlib.sha256(scene.snapshot()).hexdigest(),'metadata':scene.info(),'motions':scene.particle_motions()}
   # Each fixture contains a real scene record; this tests file binding, not language equivalence.
   for language in ['python','typescript','go','rust']:(root/('parity-'+language+'.jsonl')).write_text(json.dumps(record)+'\n')
   before=replayBinding(root);requireSameReplay(before,replayBinding(root))
   (root/'parity-go.jsonl').write_text(json.dumps({**record,'frame':'0'*64})+'\n')
   with self.assertRaisesRegex(ValueError,'go'):requireSameReplay(before,replayBinding(root))
   (root/'parity-rust.jsonl').unlink()
   with self.assertRaises(FileNotFoundError):replayBinding(root)
if __name__=='__main__':unittest.main()
