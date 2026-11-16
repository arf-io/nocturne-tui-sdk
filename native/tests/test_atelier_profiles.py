"""Real Atelier primitive interfaces against independent original equations."""
import math,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from atelier_reference import sample
EFFECTS={'nova':'weather/fractured-sun','sparks':'weather/livewire','embers':'weather/copper-cinders','rain':'weather/slantfall','snow':'weather/crystalline-drift'}
class AtelierProfiles(unittest.TestCase):
    def scene(self,kind):
        s=NativeScene(2030);self.addCleanup(s.close);s.command({'op':'emitter','id':1,'effect':EFFECTS[kind],'count':32,'runningTimeMs':0})
        s.command({'op':'draft','text':'Atelier source draft','emitWeather':False});return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('atelier')
    def assert_primitives(self,row,want):
        for key in ('points','segments','glows'):
            self.assertEqual(row[key+'Count'],len(want[key]));self.assertEqual(len(row[key]),min(16,len(want[key])))
            for actual,expected in zip(row[key],want[key][:16]):
                self.assertEqual(len(actual),len(expected))
                for value,target in zip(actual,expected):self.assertAlmostEqual(value,target,delta=5e-5)
    def test_all_five_source_equations_phase_boundaries_and_replay(self):
        for kind in EFFECTS:
            with self.subTest(kind=kind):
                s=self.scene(kind);s.command({'op':'atelier-style','id':1,'seed':4711,'eventId':1,'shockwave':.5});initial=s.snapshot();frames=[]
                times=(0,89999,90000,179999,180000,180001,449999,450000,1100000,4199999,4200000)
                for us in times:
                    s.advance_to(us);pure=s.snapshot();self.assert_primitives(self.row(s),sample(kind,us/1000,shockwave=.5))
                    self.assertEqual(s.info_complete()['prompt']['text'],'Atelier source draft');frames.append(s.render().bytes);self.assertEqual(s.snapshot(),pure)
                final=s.snapshot();s.restore(initial)
                for us,frame in zip(times,frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                self.assertEqual(s.snapshot(),final)
    def test_maximum_ejecta_and_zero_or_reduced_motion(self):
        s=self.scene('nova');s.command({'op':'atelier-style','id':1,'count':256,'ejecta':2,'shockwave':1})
        s.advance_to(200000);row=self.row(s);self.assertEqual((row['pointsCount'],row['segmentsCount'],row['glowsCount']),(513,524,2))
        for patch in [{'reducedMotion':True},{'reducedMotion':False,'intensity':0}]:
            s.command({'op':'atelier-style','id':1,**patch});self.assert_primitives(self.row(s),dict(points=[],segments=[],glows=[]))
        s.command({'op':'atelier-style','id':1,'intensity':.8,'count':0,'ejecta':0,'coreMs':0,'shockwave':0})
        self.assertEqual(self.row(s)['pointsCount'],1);self.assertEqual(self.row(s)['segmentsCount'],12)
    def test_negative_original_controls_are_atomic(self):
        s=self.scene('rain');pure=s.snapshot()
        for patch in [{'count':257},{'count':.5},{'branches':0},{'glitterHz':0},{'ejecta':2.01},{'coreRadius':6.01},{'reducedMotion':1},{'seed':-1},{'lifeMs':199}]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'atelier-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
    def test_visible_topmost_core_glyph_boundaries(self):
        s=self.scene('nova')
        for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},
          {'op':'environment','stars':0},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
          {'op':'atelier-style','id':1,'count':0,'ejecta':0,'coreMs':0,'shockwave':0}]:s.command(c)
        for us,glyph in [(89999,'✶'),(90000,'✹'),(179999,'✹'),(180000,'✧'),(449999,'✧')]:
            s.advance_to(us);row=self.row(s);x,y=map(int,row['center'][:2]);s.render();self.assertEqual(s.inspect_character_cell(x,y)['glyph'],ord(glyph))
        s.advance_to(450000);self.assertEqual(self.row(s)['pointsCount'],0)
    def test_visible_points_and_near_plane_use_original_equations(self):
        for kind in ('rain','snow','embers'):
            with self.subTest(kind=kind):
                s=self.scene(kind)
                for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},
                  {'op':'environment','stars':0},{'op':'atelier-style','id':1,'count':1,'trailMs':0}]:s.command(c)
                s.advance_to(250000);want=sample(kind,250,count=1,trailMs=0);dy=want['points'][0][1]
                s.command({'op':'camera','position':[0,-2*dy,40],'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':100})
                row=self.row(s);cx,cy=row['center'][:2];point=want['points'][0];x,y=math.floor(cx+point[0]),math.floor(cy+point[1])
                self.assertTrue(0<=x<100 and 0<=y<40);s.render();self.assertEqual(s.inspect_character_cell(x,y)['glyph'],point[2])
                s.command({'op':'camera','position':[0,0,-40]});s.render();self.assertFalse(self.row(s)['visible'])
    def test_glow_and_segment_paint_affect_real_frame(self):
        s=self.scene('nova');s.command({'op':'environment','stars':0});s.command({'op':'atelier-style','id':1,'shockwave':1,'coreMs':280})
        s.advance_to(100000);with_core=s.render().bytes;s.command({'op':'atelier-style','id':1,'coreMs':0});self.assertNotEqual(s.render().bytes,with_core)
        s.advance_to(750000);with_ring=s.render().bytes;s.command({'op':'atelier-style','id':1,'shockwave':0});self.assertNotEqual(s.render().bytes,with_ring)
        sparks=self.scene('sparks');sparks.command({'op':'atelier-style','id':1,'branches':1,'jaggedness':0});sparks.advance_to(100000)
        frame=sparks.render().bytes;sparks.command({'op':'remove-atelier-style','id':1});self.assertNotEqual(sparks.render().bytes,frame)
    def test_epoch_remove_clear_reuse_and_wrong_family(self):
        s=self.scene('rain');s.command({'op':'atelier-style','id':1});s.advance_to(250000)
        s.command({'op':'atelier-style','id':1,'speed':4});self.assertEqual(self.row(s)['elapsedUs'],250000)
        s.command({'op':'remove-atelier-style','id':1});self.assertIsNone(self.row(s))
        baseline=s.render().bytes;s.command({'op':'atelier-style','id':1});s.command({'op':'remove-atelier-style','id':1});self.assertEqual(s.render().bytes,baseline)
        s.command({'op':'atelier-style','id':1});s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':EFFECTS['rain'],'count':1,'runningTimeMs':0});self.assertIsNone(self.row(s))
        s.command({'op':'atelier-style','id':1});s.command({'op':'clear-instance','id':1});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':'weather/autumn-drift','count':1,'runningTimeMs':0});pure=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'atelier-style','id':1})
        self.assertEqual(s.snapshot(),pure)
    def old59(self,s):
        data=bytearray(s.snapshot()[:13556808]);struct.pack_into('<I',data,12,0x20261059)
        struct.pack_into('<I',data,28,0x20261059);struct.pack_into('<I',data,16,len(data)-24)
        struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data
    def test_old_layout_retains_generic_and_nested_new_queue_rejects(self):
        s=self.scene('nova');before=s.render().bytes;s.restore(self.old59(s));self.assertIsNone(self.row(s));self.assertEqual(s.render().bytes,before)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'atelier-style','id':1}]}})
        bad=self.old59(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
