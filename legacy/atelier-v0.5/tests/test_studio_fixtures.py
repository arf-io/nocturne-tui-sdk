import json,hashlib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from studio import Studio,Node,Impulse
class StudioReferenceTests(unittest.TestCase):
 def testAcceptedReferences(self):
  for c in json.loads((ROOT/'tests/studio.fixtures.json').read_text()):
   with self.subTest(case=c['name']):
    f=Studio(**c['config']).render(c['timeMs'],nodes=[Node(**n) for n in c['nodes']],events=[Impulse(**e) for e in c['events']]);self.assertEqual(hashlib.sha256(f.tobytes()).hexdigest(),c['sha256'])
