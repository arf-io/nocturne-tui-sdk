"""Real Studio source integer contracts authored before native implementation."""
import math,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from studio_nova_reference import core,ring,ring_color,STAR_PALETTE
class StudioNova(unittest.TestCase):
    def scene(self):
        s=NativeScene(2030);self.addCleanup(s.close)
        for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},{'op':'environment','stars':0},
          {'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0,'orthographic':True,'span':100},
          {'op':'emitter','id':1,'effect':'weather/pearl-bloom','position':[0,0,0],'count':1,'runningTimeMs':0}]:s.command(c)
        return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('studioNova')
    def test_integer_core_phases_visible_glyph_purity_and_replay(self):
        s=self.scene();s.command({'op':'studio-style','id':1});initial=s.snapshot();frames=[]
        times=(0,1000,90000,431999,432000,863999,864000,1000000,1800000,3000000,3599999,3600000)
        for us in times:
            s.advance_to(us);pure=s.snapshot();row=self.row(s);want=core(us//1000)
            self.assertEqual(row['envelope'],want['envelope']);self.assertEqual(row['glyph'],want['glyph']);self.assertEqual(row['glyphIndex'],want['index'])
            frames.append(s.render().bytes)
            if want['envelope']>0:
                # Original EffectPainter.local rounds the projected tile origin.
                x,y=(math.floor(v+.5) for v in row['center'][:2]);self.assertEqual(s.inspect_character_cell(x,y)['glyph'],want['glyph'])
            self.assertEqual(s.snapshot(),pure)
        final=s.snapshot();s.restore(initial)
        for us,frame in zip(times,frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
        self.assertEqual(s.snapshot(),final)
    def test_integer_ring_samples_and_seed_palette(self):
        for seed in (0,2030,0xffffffff):
            s=self.scene();s.command({'op':'studio-style','id':1,'seed':seed});s.advance_to(750000);row=self.row(s)
            self.assertEqual(row['coreColor'],STAR_PALETTE[seed%6])
            # Public fixed Q8 radial samples, independent of camera/framebuffer.
            self.assertEqual(len(row['radialSamples']),16)
            for x,opacity,color in row['radialSamples']:
                self.assertEqual(opacity,ring(750,x,0));self.assertEqual(color,ring_color(seed,x,0))
            before=s.render().bytes;s.command({'op':'studio-style','id':1,'rippleOpacity':0});self.assertNotEqual(s.render().bytes,before)
    def test_control_bounds_negative_atomicity_and_custom_glyphs(self):
        s=self.scene()
        for patch in ({'novaDurationMs':99},{'novaDurationMs':30001},{'rippleSpeed':0},{'rippleWidth':15},{'rippleRings':0},{'rippleRings':7},{'cellAspect':499},{'rippleOpacity':1001},{'strength':-1},{'seed':-1},{'seed':.5},{'glyphs':''},{'glyphs':'x'*17},{'rippleWidth':True},{'unknown':1},{'id':65535}):
            pure=s.snapshot()
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'studio-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
        s.command({'op':'studio-style','id':1,'glyphs':'ABC','novaDurationMs':1000});s.advance_to(240000);self.assertEqual(self.row(s)['glyph'],ord('C'))
    def test_epoch_remove_clear_reuse_and_near_plane(self):
        s=self.scene();s.command({'op':'studio-style','id':1});s.advance_to(250000);s.command({'op':'studio-style','id':1,'seed':77});self.assertEqual(self.row(s)['elapsedUs'],250000)
        s.command({'op':'camera','position':[0,0,-40]});self.assertFalse(self.row(s)['visible'])
        s.command({'op':'remove-studio-style','id':1});self.assertIsNone(self.row(s));generic=s.render().bytes
        s.command({'op':'studio-style','id':1});s.command({'op':'remove-studio-style','id':1});self.assertEqual(s.render().bytes,generic)
        s.command({'op':'studio-style','id':1});s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':'weather/pearl-bloom','count':1,'runningTimeMs':0});self.assertIsNone(self.row(s))
        s.command({'op':'clear-instance','id':1});s.command({'op':'emitter','id':1,'effect':'weather/starburst','count':1,'runningTimeMs':0});pure=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'studio-style','id':1})
        self.assertEqual(s.snapshot(),pure)
    def old62(self,s):
        d=bytearray(s.snapshot()[:13560520]);struct.pack_into('<I',d,12,0x20261062);struct.pack_into('<I',d,28,0x20261062);struct.pack_into('<I',d,16,len(d)-24);struct.pack_into('<I',d,20,zlib.crc32(d[24:]));return d
    def test_old62_and_nested_new_queue_migration(self):
        s=self.scene();frame=s.render().bytes;s.restore(self.old62(s));self.assertIsNone(self.row(s));self.assertEqual(s.render().bytes,frame)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'studio-style','id':1}]}});bad=self.old62(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
    def test_positive_control_endpoints_and_palette_updates(self):
        bounds={'novaDurationMs':(100,30000),'rippleSpeed':(1,262144),'rippleWidth':(16,8192),'rippleOpacity':(0,1000),'rippleRings':(1,6),'cellAspect':(500,4000),'strength':(0,1000),'waveScale':(64,262144),'seed':(0,0xffffffff)}
        for key,values in bounds.items():
            for value in values:
                with self.subTest(key=key,value=value):
                    s=self.scene();s.command({'op':'studio-style','id':1,key:value});self.assertEqual(self.row(s)['controls'][key],value)
                    s.advance_to(50000);pure=s.snapshot();s.render();self.assertEqual(s.snapshot(),pure)
        s=self.scene();s.command({'op':'studio-style','id':1,'palette':[0xff0000],'starPalette':[0x00ff00],'waveScale':6144,'glyphs':'XYZ'});s.advance_to(864000)
        row=self.row(s);self.assertEqual(row['coreColor'],0x00ff00);self.assertEqual(row['glyph'],ord('Z'))
        self.assertTrue(all(v[2]==0xff0000 for v in row['radialSamples']))
        before=s.render().bytes;s.command({'op':'studio-style','id':1,'palette':[0x0000ff],'starPalette':[0xff0000]});self.assertNotEqual(s.render().bytes,before)
        self.assertEqual(self.row(s)['elapsedUs'],864000)
    def test_palette_wave_scale_and_scalar_rejections_are_atomic(self):
        s=self.scene()
        for patch in ({'waveScale':63},{'waveScale':262145},{'waveScale':1.5},{'palette':[]},{'palette':[0]*33},{'palette':[-1]},{'palette':[0x1000000]},{'palette':[True]},{'starPalette':[]},{'starPalette':['red']},{'glyphs':'\ud800'},{'rippleRings':1.5},{'novaDurationMs':100.5}):
            pure=s.snapshot()
            with self.subTest(patch=patch),self.assertRaises((ValueError,UnicodeEncodeError)):s.command({'op':'studio-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
