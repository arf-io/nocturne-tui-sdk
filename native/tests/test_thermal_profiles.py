"""Real native source geometry contracts authored before thermal profile code."""
import struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from thermal_reference import sample
EFFECTS={'embers':'weather/thermal-cinders','leaves':'weather/autumn-drift'}
class ThermalProfiles(unittest.TestCase):
    def scene(self,kind):
        s=NativeScene(2030);self.addCleanup(s.close)
        for c in [{'op':'resize','width':100,'height':40},{'op':'camera','position':[0,10,45],'yaw':0,'pitch':0,'roll':0},
                  {'op':'environment','stars':0},{'op':'emitter','id':1,'effect':EFFECTS[kind],'position':[0,0,0],'count':1,'runningTimeMs':0},
                  {'op':'draft','text':'Thermal source draft','emitWeather':False}]:s.command(c)
        return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('thermalSource')
    def assert_source(self,row,want):
        self.assertIsNotNone(row)
        for key in ('points','segments'):
            self.assertEqual(row[key+'Count'],len(want[key]));self.assertEqual(len(row[key]),min(16,len(want[key])))
            for actual,expected in zip(row[key],want[key][:16]):
                self.assertEqual(len(actual),len(expected))
                for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=5e-5)
    def test_original_geometry_burnout_delays_and_replay(self):
        for kind in EFFECTS:
            for seed in (0,2030,0xffffffff):
                with self.subTest(kind=kind,seed=seed):
                    s=self.scene(kind);s.command({'op':'thermal-style','id':1,'seed':seed});initial=s.snapshot();frames=[]
                    times=(0,10000,230000,450000,900000,2000000,4400000,6000000,6499999,6500000)
                    for us in times:
                        s.advance_to(us);pure=s.snapshot();self.assert_source(self.row(s),sample(kind,seed,us/1000));frames.append(s.render().bytes)
                        self.assertEqual(s.snapshot(),pure);self.assertEqual(s.info_complete()['prompt']['text'],'Thermal source draft')
                    final=s.snapshot();s.restore(initial)
                    for us,frame in zip(times,frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                    self.assertEqual(s.snapshot(),final)
    def test_full_leaf_capacity_and_camera_independent_source(self):
        s=self.scene('leaves');s.command({'op':'thermal-style','id':1,'seed':2030});s.advance_to(1000000)
        row=self.row(s);self.assert_source(row,sample('leaves',2030,1000));self.assertEqual(row['segmentsCount'],400)
        frame=s.render().bytes;s.command({'op':'camera','position':[10,12,45],'yaw':12,'pitch':4,'roll':7})
        self.assert_source(self.row(s),sample('leaves',2030,1000));self.assertNotEqual(s.render().bytes,frame)
    def test_negative_controls_are_atomic(self):
        s=self.scene('embers')
        for patch in ({'seed':-1},{'seed':4294967296},{'seed':.5},{'seed':'2030'},{'lifeMs':199},{'lifeMs':10001},{'lifeMs':True},{'unknown':1},{'id':0},{'id':65535}):
            pure=s.snapshot()
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'thermal-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
    def test_epoch_removal_clear_reuse_and_wrong_family(self):
        s=self.scene('embers');s.command({'op':'thermal-style','id':1});s.advance_to(250000)
        s.command({'op':'thermal-style','id':1,'seed':77});self.assertEqual(self.row(s)['elapsedUs'],250000)
        self.assert_source(self.row(s),sample('embers',77,250));s.command({'op':'remove-thermal-style','id':1});self.assertIsNone(self.row(s))
        generic=s.render().bytes;s.command({'op':'thermal-style','id':1});s.command({'op':'remove-thermal-style','id':1});self.assertEqual(s.render().bytes,generic)
        s.command({'op':'thermal-style','id':1});s.command({'op':'clear-instance','id':1});s.command({'op':'emitter','id':1,'effect':EFFECTS['leaves'],'count':1,'runningTimeMs':0});self.assertIsNone(self.row(s))
        s.command({'op':'thermal-style','id':1});s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':'weather/fractured-sun','count':1,'runningTimeMs':0});pure=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'thermal-style','id':1})
        self.assertEqual(s.snapshot(),pure)
    def old60(self,s):
        data=bytearray(s.snapshot()[:13559240]);struct.pack_into('<I',data,12,0x20261060);struct.pack_into('<I',data,28,0x20261060)
        struct.pack_into('<I',data,16,len(data)-24);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data
    def test_old60_generic_migration_and_nested_new_queue_rejection(self):
        s=self.scene('embers');frame=s.render().bytes;s.restore(self.old60(s));self.assertIsNone(self.row(s));self.assertEqual(s.render().bytes,frame)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'thermal-style','id':1}]}})
        bad=self.old60(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
    def test_world_translation_and_crossing_near_far_segments(self):
        from thermal_reference import projected_segments
        s=self.scene('leaves');s.command({'op':'prompt','active':False});s.command({'op':'thermal-style','id':1,'seed':2030,'paint':'material'});s.advance_to(1000000)
        source=sample('leaves',2030,1000)['segments']
        for camera,near,far in [([0,10,0],.1,200),([0,10,0],.1,2),([0,10,-100],.1,2)]:
            s.command({'op':'camera','position':camera,'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':100,'near':near,'far':far})
            row=self.row(s);want=projected_segments(source,[0,0,0],camera,near,far)
            self.assertEqual(row['projectedSegmentsCount'],len(want));self.assertEqual(len(row['projectedSegments']),min(16,len(want)))
            for actual,expected in zip(row['projectedSegments'],want[:16]):
                for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=5e-5)
            if far==200:
                self.assertTrue(any(min(-r[2],-r[5])<near<max(-r[2],-r[5]) for r in source))
                self.assertGreater(len(want),0);self.assertLess(len(want),400)
            pure=s.snapshot();s.render();self.assertEqual(s.snapshot(),pure)
        # Different emitter origin translates geometry; camera compensation restores projection.
        shifted=self.scene('leaves');shifted.command({'op':'clear-instance','id':1})
        shifted.command({'op':'emitter','id':1,'effect':EFFECTS['leaves'],'position':[7,3,-2],'count':1,'runningTimeMs':0})
        shifted.command({'op':'prompt','active':False});shifted.command({'op':'thermal-style','id':1,'seed':2030,'paint':'material'});shifted.advance_to(1000000)
        shifted.command({'op':'camera','position':[7,13,-2],'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':100,'near':.1,'far':200})
        want=projected_segments(source,[7,3,-2],[7,13,-2]);row=self.row(shifted)
        self.assertEqual(row['projectedSegmentsCount'],len(want))
        for actual,expected in zip(row['projectedSegments'],want[:16]):
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=5e-5)
    def test_source_hues_drive_visible_native_color(self):
        s=self.scene('embers');s.command({'op':'prompt','active':False});s.command({'op':'thermal-style','id':1,'seed':2030});s.advance_to(1500000)
        s.command({'op':'camera','position':[0,10,45],'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':40})
        self.assert_source(self.row(s),sample('embers',2030,1500));frame=s.render()
        colors={s.inspect_character_cell(x,y)['foreground'] for y in range(30) for x in range(100) if s.inspect_character_cell(x,y)['glyph'] in (ord('·'),ord('∙'),ord('✧'))}
        self.assertGreater(len(colors),1)
        s.command({'op':'remove-thermal-style','id':1});self.assertNotEqual(s.render().bytes,frame.bytes)
