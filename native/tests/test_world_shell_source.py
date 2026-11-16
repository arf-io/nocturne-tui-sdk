"""Real opt-in original profiles; tests precede implementation."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class WorldShellSource(unittest.TestCase):
    def create(self,effect):
        s=NativeScene(2030);self.addCleanup(s.close)
        s.command({'op':'emitter','id':1,'effect':effect,'position':[0,0,0],'count':1,'runningTimeMs':0})
        return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1)['worldSource']
    def test_archived_sampler_and_explicit_material_fallback_rows(self):
        # Archived sampleWorldEvent falls through for ripples, but the actual
        # application routes ripples to Studio. Retain this historical sampler
        # fixture only under explicit material mode; source raster tests assert
        # the actual four-ring painter and zero fabricated precipitation rows.
        ref=json.loads((ROOT/'tests/fixtures/world-shell-source-reference.json').read_text())
        for path,digest in ref['sources'].items():self.assertEqual(hashlib.sha256((ROOT.parent/path).read_bytes()).hexdigest(),digest)
        for row in ref['rows']:
            with self.subTest(profile=row['profile'],controls=row['controls']):
                s=self.create(row['effect']);s.command({'op':'world-style','id':1,**row['controls'],**({'paint':'material'} if row['profile']=='ripples' else {})})
                for us,want in zip(ref['times'],row['samples']):
                    s.advance_to(us);actual=self.row(s);self.assertEqual(actual['profile'],row['profile']);self.assertEqual(actual['pointsCount'],want['pointCount']);self.assertEqual(actual['segmentsCount'],0)
                    self.assertEqual(len(actual['points']),len(want['points']))
                    for a,b in zip(actual['points'],want['points']):
                        for x,y in zip(a,b):self.assertAlmostEqual(x,y,delta=5e-5)
                    actual['points'].clear();self.assertEqual(len(self.row(s)['points']),len(want['points']))
    def test_purity_replay_removal_preserves_default_physics_and_frame(self):
        for effect in ('weather/ejecta-shell','weather/pressure-shell'):
            s=self.create(effect);s.advance_to(250000);generic=s.snapshot();particles=s.particles();frame=s.render().bytes
            s.command({'op':'world-style','id':1,'count':64});pure=s.snapshot();s.render();self.row(s);self.assertEqual(s.snapshot(),pure);self.assertEqual(s.particles(),particles)
            s.command({'op':'remove-world-style','id':1});self.assertEqual(s.snapshot(),generic);self.assertEqual(s.render().bytes,frame)
            s.command({'op':'world-style','id':1,'count':64});initial=s.snapshot();s.advance_to(1000000);final=s.snapshot();frame=s.render().bytes
            s.restore(initial);s.advance_to(1000000);self.assertEqual(s.snapshot(),final);self.assertEqual(s.render().bytes,frame)
    def test_negative_controls_epoch_clear_and_recreate(self):
        s=self.create('weather/pressure-shell');s.command({'op':'world-style','id':1});s.advance_to(250000);s.command({'op':'world-style','id':1,'count':1,'scale':2});self.assertEqual(self.row(s)['elapsedUs'],250000)
        for patch in ({'count':0},{'count':1201},{'seed':4294967296},{'scale':0},{'lifeMs':199},{'gravity':101}):
            pure=s.snapshot()
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'world-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
        s.command({'op':'clear-instance','id':1});s.command({'op':'emitter','id':1,'effect':'weather/pressure-shell','count':1,'runningTimeMs':0})
        self.assertNotIn('worldSource',next(e for e in s.info_complete()['emitters'] if e['id']==1))
