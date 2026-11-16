"""Real six-profile world primitive contracts authored before native code."""
import math,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from world_particle_reference import sample
from thermal_reference import projected_segments
EFFECTS={'firework':'weather/starburst','sparks':'weather/forked-voltage','embers':'weather/solar-cinders','leaves':'weather/leaf-ribbon','rain':'weather/storm-volume','snow':'weather/snowfall-volume'}
class WorldParticleProfiles(unittest.TestCase):
    def scene(self,kind,origin=None):
        s=NativeScene(2030);self.addCleanup(s.close)
        for c in [{'op':'resize','width':100,'height':40},{'op':'camera','position':[0,0,45],'yaw':0,'pitch':0,'roll':0},
                  {'op':'environment','stars':0},{'op':'emitter','id':1,'effect':EFFECTS[kind],'position':origin or [0,0,0],'count':1,'runningTimeMs':0},
                  {'op':'draft','text':'World source draft','emitWeather':False}]:s.command(c)
        return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('worldSource')
    def assert_source(self,row,want):
        self.assertIsNotNone(row)
        for key in ('points','segments'):
            self.assertEqual(row[key+'Count'],len(want[key]));self.assertEqual(len(row[key]),min(16,len(want[key])))
            for actual,expected in zip(row[key],want[key][:16]):
                self.assertEqual(len(actual),len(expected))
                for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=5e-5)
    def test_all_six_equations_birth_strike_expiry_and_replay(self):
        for kind in EFFECTS:
            for seed in (0,2030,0xffffffff):
                with self.subTest(kind=kind,seed=seed):
                    s=self.scene(kind);s.command({'op':'world-style','id':1,'seed':seed});initial=s.snapshot();frames=[]
                    times=(0,60000,120000,849999,850000,1000000,3000000,4999999,5000000)
                    for us in times:
                        s.advance_to(us);pure=s.snapshot();self.assert_source(self.row(s),sample(kind,us/1000,seed=seed));frames.append(s.render().bytes)
                        self.assertEqual(s.snapshot(),pure);self.assertEqual(s.info_complete()['prompt']['text'],'World source draft')
                    final=s.snapshot();s.restore(initial)
                    for us,frame in zip(times,frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                    self.assertEqual(s.snapshot(),final)
    def test_full_capacity_and_controls_retain_epoch(self):
        for kind in EFFECTS:
            s=self.scene(kind);s.command({'op':'world-style','id':1,'count':1200,'scale':.75,'gravity':0,'lifeMs':10000});s.advance_to(2000000)
            self.assert_source(self.row(s),sample(kind,2000,count=1200,scale=.75,gravity=0,life_ms=10000));self.assertEqual(self.row(s)['pointsCount'],1200)
            s.command({'op':'world-style','id':1,'count':1,'seed':77,'scale':2,'gravity':12,'lifeMs':4000});self.assertEqual(self.row(s)['elapsedUs'],2000000)
            self.assert_source(self.row(s),sample(kind,2000,count=1,seed=77,scale=2,gravity=12,life_ms=4000))
    def test_negative_domains_are_atomic(self):
        s=self.scene('firework')
        for patch in ({'count':0},{'count':1201},{'count':1.5},{'seed':-1},{'seed':4294967296},{'seed':.5},{'scale':0},{'scale':1001},{'lifeMs':199},{'lifeMs':10001},{'gravity':-1},{'gravity':101},{'gravity':True},{'count':'64'},{'unknown':1},{'id':0},{'id':65535}):
            pure=s.snapshot()
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'world-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
    def test_connected_world_clipping_translation_and_camera_invariance(self):
        origin=[7,3,-2];s=self.scene('firework',origin);s.command({'op':'prompt','active':False});s.command({'op':'world-style','id':1,'count':64,'paint':'material'});s.advance_to(1000000)
        source=sample('firework',1000)
        for camera,near,far in [([7,3,0],.1,200),([7,3,0],.1,2),([7,3,-100],.1,2)]:
            s.command({'op':'camera','position':camera,'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':100,'near':near,'far':far});row=self.row(s)
            self.assert_source(row,source);want=projected_segments(source['segments'],origin,camera,near,far)
            self.assertEqual(row['projectedSegmentsCount'],len(want));self.assertEqual(len(row['projectedSegments']),min(16,len(want)))
            for actual,expected in zip(row['projectedSegments'],want[:16]):
                for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=5e-5)
            pure=s.snapshot();s.render();self.assertEqual(s.snapshot(),pure)
    def test_visible_original_point_glyph_and_near_plane_rejection(self):
        for kind in ('firework','rain','snow','leaves'):
            s=self.scene(kind);s.command({'op':'prompt','active':False});s.command({'op':'world-style','id':1,'count':1,'paint':'material'});s.advance_to(250000)
            point=sample(kind,250,count=1)['points'][0]
            # Center source point explicitly: independent zero-angle orthographic camera.
            s.command({'op':'camera','position':[point[0],point[1],point[2]+40],'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':100})
            s.render();self.assertEqual(s.inspect_character_cell(50,18)['glyph'],point[3])
            frame=s.render().bytes;s.command({'op':'camera','position':[point[0],point[1],point[2]-40]});self.assertNotEqual(s.render().bytes,frame)
    def test_remove_clear_reuse_wrong_family_preserve_generic(self):
        s=self.scene('rain');s.command({'op':'world-style','id':1});s.advance_to(250000);s.command({'op':'remove-world-style','id':1});self.assertIsNone(self.row(s))
        frame=s.render().bytes;s.command({'op':'world-style','id':1});s.command({'op':'remove-world-style','id':1});self.assertEqual(s.render().bytes,frame)
        s.command({'op':'world-style','id':1});s.command({'op':'clear-instance','id':1});s.command({'op':'emitter','id':1,'effect':EFFECTS['snow'],'count':1,'runningTimeMs':0});self.assertIsNone(self.row(s))
        s.command({'op':'world-style','id':1});s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['emitters'],[])
        # Ejecta Shell now supports explicit original Nova world-style; retain wrong-family rejection on Kinetic.
        s.command({'op':'emitter','id':1,'effect':'weather/chrysanthemum','count':1,'runningTimeMs':0});pure=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'world-style','id':1})
        self.assertEqual(s.snapshot(),pure)
    def old61(self,s):
        data=bytearray(s.snapshot()[:13559752]);struct.pack_into('<I',data,12,0x20261061);struct.pack_into('<I',data,28,0x20261061)
        struct.pack_into('<I',data,16,len(data)-24);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data
    def test_old61_migration_and_nested_new_queue_rejection(self):
        s=self.scene('firework');frame=s.render().bytes;s.restore(self.old61(s));self.assertIsNone(self.row(s));self.assertEqual(s.render().bytes,frame)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'world-style','id':1}]}});bad=self.old61(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
