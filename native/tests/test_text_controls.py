"""Original source boundaries and real retained control bindings; test first."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

class TextControls(unittest.TestCase):
    def test_original_low_high_source_controls(self):
        ref=json.loads((ROOT/'tests/fixtures/text-control-reference.json').read_text())
        for path,digest in ref['sources'].items():
            self.assertEqual(hashlib.sha256((ROOT.parent/path).read_bytes()).hexdigest(),digest)
        for row in ref['rows']:
            with self.subTest(id=row['id'],phase=row['phase'],boundary=row['boundary']),NativeScene(2030) as scene:
                scene.command({'op':'text','id':1,'text':'NODE','x':0,'y':0,'width':120,'effect':row['id'],'phase':row['phase'],**row['config']})
                for us,poses in zip(ref['times'],row['poses']):
                    scene.advance_to(us)
                    for index,pose in enumerate(poses):
                        actual=scene.text_sample(1,index)
                        self.assertEqual(actual[0],ord(pose['glyph']))
                        expected=(pose['x'],pose['y'],pose.get('alpha',pose.get('opacity')),pose.get('hue',pose.get('hueDelta')))
                        for left,right in zip((actual[3]/65536,actual[4]/65536,actual[5]/1e6,actual[6]/1000),expected):
                            self.assertAlmostEqual(left,right,delta=.0012)
                    self.assertEqual(next(r for r in scene.info_complete()['textRuns'] if r['id']==1)['text'],'NODE')

    def test_wider_scatter_binding_direct_parity_and_replay(self):
        for value in (100,100.5,120):
            with self.subTest(value=value),NativeScene(2030) as scene,NativeScene(2030) as oracle:
                for s in (scene,oracle):
                    s.command({'op':'text','id':1,'text':'NODE','effect':'text/glyph-rain','durationMs':1000,'variation':0,'jitterMs':0})
                    s.advance_to(250000)
                identity=scene.text_sample(1,0)[2]
                scene.command({'op':'define','path':'/scatter','value':value,'binding':{'family':'text','id':1,'field':'scatter'}})
                oracle.command({'op':'text','id':1,'scatter':value})
                scene.command({'op':'remove-value','path':'/scatter'})
                self.assertEqual(scene.snapshot(),oracle.snapshot())
                self.assertEqual(scene.text_sample(1,0)[2],identity)
                initial=scene.snapshot();scene.advance_to(600000);final=scene.snapshot();frame=scene.render().bytes
                scene.restore(initial);scene.advance_to(600000)
                self.assertEqual(scene.snapshot(),final);self.assertEqual(scene.render().bytes,frame)

    def test_invalid_scatter_atomic_and_window_bound_preserved(self):
        with NativeScene(2030) as scene:
            scene.command({'op':'text','id':1,'text':'NODE','effect':'text/glyph-rain'})
            for value in (-1,120.001,float('inf'),float('nan')):
                for command in ({'op':'text','id':1,'scatter':value},{'op':'define','path':'/scatter','value':value,'binding':{'family':'text','id':1,'field':'scatter'}}):
                    saved=scene.snapshot()
                    with self.subTest(command=command),self.assertRaises(ValueError):scene.command(command)
                    self.assertEqual(scene.snapshot(),saved)
            saved=scene.snapshot()
            with self.assertRaises(ValueError):scene.command({'op':'window','id':1,'scatter':101})
            self.assertEqual(scene.snapshot(),saved)

    def test_scheduled_wide_scatter_survives_restore(self):
        with NativeScene(2030) as scene:
            scene.command({'op':'text','id':1,'text':'NODE','effect':'text/glyph-rain'})
            scene.command({'op':'schedule','id':1,'atUs':100000,'command':{'op':'text','id':1,'scatter':120}})
            saved=scene.snapshot();scene.advance_to(200000);final=scene.snapshot();pose=scene.text_sample(1,0)
            scene.restore(saved);scene.advance_to(200000)
            self.assertEqual(scene.snapshot(),final);self.assertEqual(scene.text_sample(1,0),pose)
