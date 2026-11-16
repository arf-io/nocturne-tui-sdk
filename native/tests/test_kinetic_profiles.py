"""Real native source primitive tables versus independent host-math equations."""
import math,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from kinetic_reference import sample
EFFECTS={'embers':'weather/hearth-spray','sparks':'weather/branchlight','nova':'weather/chrysanthemum','rain':'weather/wire-rain','snow':'weather/pearl-flurry'}
class KineticProfiles(unittest.TestCase):
    def scene(self,kind):
        s=NativeScene(2030);self.addCleanup(s.close)
        s.command({'op':'emitter','id':1,'effect':EFFECTS[kind],'count':32,'runningTimeMs':0})
        s.command({'op':'draft','text':'Kinetic source draft','emitWeather':False});return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('kinetic')
    def test_all_source_primitive_tables_and_exact_replay(self):
        for kind in EFFECTS:
            with self.subTest(kind=kind):
                s=self.scene(kind);s.command({'op':'kinetic-style','id':1,'seed':2030,'eventId':1,'shockwave':.4});initial=s.snapshot();frames=[]
                for us in (0,90000,150000,260000,520000,1000000,4999999,5000000):
                    s.advance_to(us);pure=s.snapshot();row=self.row(s);want=sample(kind,us/1000,shockwave=.4)
                    for key in ('core','radius','shockwave'):self.assertAlmostEqual(row[key],want[key],delta=2e-5)
                    for key in ('points','segments'):
                        self.assertEqual(row[key+'Count'],len(want[key]));self.assertEqual(len(row[key]),min(16,len(want[key])))
                        for actual,expected in zip(row[key],want[key][:16]):
                            self.assertEqual(len(actual),len(expected))
                            for value,target in zip(actual,expected):self.assertAlmostEqual(value,target,delta=5e-5)
                    self.assertEqual(s.info_complete()['prompt']['text'],'Kinetic source draft');frames.append(s.render().bytes);self.assertEqual(s.snapshot(),pure)
                final=s.snapshot();s.restore(initial)
                for us,frame in zip((0,90000,150000,260000,520000,1000000,4999999,5000000),frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                self.assertEqual(s.snapshot(),final)
    def test_negative_source_control_domains_are_atomic(self):
        s=self.scene('embers');pure=s.snapshot()
        for patch in [{'count':0},{'count':1.5},{'branches':13},{'arcSegments':2},{'drag':-1},{'seed':-1},{'glyphs':''},{'glyphs':'\n'},{'lifeMs':99},{'brightness':1.01}]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'kinetic-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
    def test_zero_drag_core_flicker_and_endpoint_controls(self):
        s=self.scene('nova');patch={'drag':0,'coreMs':0,'flickerHz':0,'trailMs':0,'count':1,'brightness':1,'glyphs':'界','shockwave':1}
        s.command({'op':'kinetic-style','id':1,**patch});s.advance_to(250000);row=self.row(s);want=sample('nova',250,**patch)
        self.assertEqual(row['core'],0);self.assertEqual(row['pointsCount'],1)
        for actual,expected in zip(row['points'][0],want['points'][0]):self.assertAlmostEqual(actual,expected,delta=5e-5)
        self.assertEqual(row['points'][0][4],ord('界'));self.assertEqual(row['segmentsCount'],1)
    def test_retarget_remove_clear_reuse_and_wrong_family(self):
        s=self.scene('rain');s.command({'op':'kinetic-style','id':1});s.advance_to(250000)
        s.command({'op':'kinetic-style','id':1,'wind':0});self.assertEqual(self.row(s)['elapsedUs'],250000)
        s.command({'op':'remove-kinetic-style','id':1});self.assertIsNone(self.row(s))
        baseline=s.render().bytes;s.command({'op':'kinetic-style','id':1});s.command({'op':'remove-kinetic-style','id':1});self.assertEqual(s.render().bytes,baseline)
        s.command({'op':'kinetic-style','id':1});s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':EFFECTS['rain'],'count':1,'runningTimeMs':0});self.assertIsNone(self.row(s))
        s.command({'op':'kinetic-style','id':1});s.command({'op':'clear-instance','id':1});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':'weather/autumn-drift','count':1,'runningTimeMs':0});pure=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'kinetic-style','id':1})
        self.assertEqual(s.snapshot(),pure)
    def old58(self,s):
        data=bytearray(s.snapshot()[:13550280]);struct.pack_into('<I',data,12,0x20261058)
        struct.pack_into('<I',data,28,0x20261058);struct.pack_into('<I',data,16,len(data)-24)
        struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data
    def test_old_source_layout_and_nested_queue_rejection(self):
        s=self.scene('nova');frame=s.render().bytes;s.restore(self.old58(s));self.assertIsNone(self.row(s));self.assertEqual(s.render().bytes,frame)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'kinetic-style','id':1}]}})
        bad=self.old58(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
    def test_visible_source_points_and_camera_projection(self):
        for kind in ('rain','snow','embers'):
            with self.subTest(kind=kind):
                s=self.scene(kind)
                for command in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},
                  {'op':'environment','stars':0},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
                  {'op':'kinetic-style','id':1,'count':1,'trailMs':0,'brightness':1,'glyphs':'X'}]:s.command(command)
                s.advance_to(3000000);want=sample(kind,3000,count=1,trailMs=0,brightness=1,glyphs='X')
                s.command({'op':'camera','position':[0,-2*want['points'][0][1],40],'orthographic':True,'span':100})
                row=self.row(s);cx,cy=row['center'][:2];frame=s.render()
                self.assertGreater(len(want['points']),0)
                for x,y,alpha,heat,glyph,size in want['points']:
                    px,py=math.floor(cx+x),math.floor(cy+y)
                    self.assertTrue(0<=px<100 and 0<=py<40);self.assertEqual(frame.words()[py*100+px][0],glyph)
                s.command({'op':'camera','position':[0,0,-40]});s.render();self.assertFalse(self.row(s)['visible'])
    def test_connected_spark_segments_match_source_and_core(self):
        s=self.scene('sparks');s.command({'op':'kinetic-style','id':1,'branches':1,'arcSegments':3,'count':1,'coreMs':260,'brightness':1})
        s.advance_to(90000);row=self.row(s);want=sample('sparks',90,branches=1,arcSegments=3,count=1,coreMs=260,brightness=1)
        self.assertEqual(row['segmentsCount'],4);self.assertEqual(row['pointsCount'],2)
        for actual,expected in zip(row['segments'],want['segments']):
            for value,target in zip(actual,expected):self.assertAlmostEqual(value,target,delta=5e-5)
        self.assertEqual(row['segments'][0][:2],[0,0]);self.assertEqual(row['segments'][0][2:4],row['segments'][1][:2])
        self.assertEqual(row['segments'][1][2:4],row['segments'][2][:2]);self.assertGreater(row['core'],0)
    def test_core_and_shockwave_controls_have_real_frame_effect(self):
        s=self.scene('nova')
        for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},
          {'op':'environment','stars':0},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
          {'op':'kinetic-style','id':1,'count':1,'brightness':1,'coreMs':260,'shockwave':.8}]:s.command(c)
        s.advance_to(90000);with_core=s.render().bytes;s.command({'op':'kinetic-style','id':1,'coreMs':0})
        self.assertNotEqual(with_core,s.render().bytes)
        s.advance_to(750000);with_wave=s.render().bytes;s.command({'op':'kinetic-style','id':1,'shockwave':0})
        self.assertNotEqual(with_wave,s.render().bytes)
    def test_spark_segment_background_differs_from_generic_scene(self):
        s=self.scene('sparks')
        for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},
          {'op':'environment','stars':0},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
          {'op':'kinetic-style','id':1,'branches':1,'arcSegments':3,'count':1,'coreMs':0,'brightness':1}]:s.command(c)
        s.advance_to(90000);source=s.snapshot();painted=s.render().words();cx,cy=self.row(s)['center'][:2]
        segments=sample('sparks',90,branches=1,arcSegments=3,count=1,coreMs=0,brightness=1)['segments']
        pixels=set()
        for x,y,xx,yy,*_ in segments:
            steps=math.floor(abs(xx-x)+abs(yy-y))+1
            for i in range(steps+1):pixels.add((math.floor(cx+x+(xx-x)*i/steps),math.floor(cy+y+(yy-y)*i/steps)))
        s.command({'op':'remove-kinetic-style','id':1});base=s.render().words();s.restore(source)
        self.assertTrue(any(0<=x<100 and 0<=y<40 and painted[y*100+x][2]!=base[y*100+x][2] for x,y in pixels))
