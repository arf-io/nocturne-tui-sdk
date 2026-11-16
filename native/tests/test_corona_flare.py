"""Source-derived Corona Flare controls and exact temporal boundaries."""
import math,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class CoronaFlare(unittest.TestCase):
    def corona(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('corona')
    def scene(self,effect='weather/corona-flare'):
        s=NativeScene(2030);self.addCleanup(s.close)
        s.command({'op':'emitter','id':1,'effect':effect,'count':32,'runningTimeMs':0})
        s.command({'op':'draft','text':'Accepted corona draft','emitWeather':False});return s
    def test_independent_envelope_and_exact_core_thresholds(self):
        s=self.scene();s.command({'op':'corona-style','id':1,'speed':12,'width':1.7,'intensity':.28,'durationMs':2400})
        for us,glyph in [(0,0x2219),(199999,0x2219),(200000,0x2726),(429999,0x2726),(430000,0x2727),(649999,0x2727),(650000,0),(2400000,0)]:
            s.advance_to(us);pure=s.snapshot();info=s.info_complete();row=next(e for e in info['emitters'] if e['id']==1)['corona']
            self.assertEqual(row['coreGlyph'],glyph);self.assertEqual(row['elapsedUs'],us)
            self.assertAlmostEqual(row['radius'],12*us/1e6,delta=1e-6)
            self.assertAlmostEqual(row['envelope'],(1-us/2400000)**2 if us<2400000 else 0,delta=1e-6)
            self.assertEqual(info['prompt']['text'],'Accepted corona draft');s.render();self.assertEqual(s.snapshot(),pure)
    def test_negative_controls_are_atomic(self):
        s=self.scene();before=s.snapshot()
        for patch in [{'speed':-1},{'width':0},{'intensity':1.01},{'durationMs':0},{'durationMs':.0001},{'id':65535}]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({'op':'corona-style','id':1,**patch})
            self.assertEqual(s.snapshot(),before)
        other=self.scene('weather/autumn-drift');before=other.snapshot()
        with self.assertRaises(ValueError):other.command({'op':'corona-style','id':1})
        self.assertEqual(other.snapshot(),before)
    def test_retarget_epoch_removal_and_replay(self):
        s=self.scene();s.command({'op':'corona-style','id':1});initial=s.snapshot()
        s.advance_to(250000);s.command({'op':'corona-style','id':1,'speed':4,'width':2,'intensity':.6})
        row=self.corona(s);self.assertEqual(row['elapsedUs'],250000);self.assertEqual(row['radius'],1)
        self.assertEqual((row['width'],row['intensity']),(2,.6));pure=s.snapshot();frame=s.render().bytes
        self.assertEqual(s.snapshot(),pure);s.restore(initial);s.advance_to(250000)
        s.command({'op':'corona-style','id':1,'speed':4,'width':2,'intensity':.6})
        self.assertEqual(s.snapshot(),pure);self.assertEqual(s.render().bytes,frame)
        s.command({'op':'remove-corona-style','id':1});self.assertIsNone(self.corona(s))
        baseline=s.render().bytes;s.command({'op':'corona-style','id':1});s.command({'op':'remove-corona-style','id':1})
        self.assertEqual(s.render().bytes,baseline)
        s.command({'op':'corona-style','id':1});s.command({'op':'clear','scope':'weather'})
        self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':'weather/corona-flare','count':1,'runningTimeMs':0})
        self.assertIsNone(self.corona(s))
    def test_independent_gaussian_samples_and_visible_core(self):
        s=self.scene();s.command({'op':'resize','width':80,'height':30})
        s.command({'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0})
        s.command({'op':'corona-style','id':1,'paint':'material','intensity':1})
        for us,glyph in [(199999,0x2219),(200000,0x2726),(430000,0x2727),(650000,0)]:
            s.advance_to(us);pure=s.snapshot();row=self.corona(s)
            envelope=(1-us/2400000)**2
            # Samples annotate radial distances0,radius,radius+width.
            for distance,value in row['radialSamples']:
                self.assertAlmostEqual(value,math.exp(-((distance-12*us/1e6)/1.7)**2)*envelope*.65,delta=2e-6)
            frame=s.render();x,y=map(int,row['center'][:2]);cell=s.inspect_character_cell(x,y)
            if glyph:self.assertEqual(cell['glyph'],glyph)
            self.assertEqual(s.snapshot(),pure)
        s.command({'op':'camera','position':[0,0,-40]});s.render();self.assertFalse(self.corona(s)['visible'])
    def test_density_independent_corona_envelope(self):
        rows=[]
        for count in (1,32):
            s=NativeScene(2030);self.addCleanup(s.close)
            s.command({'op':'emitter','id':1,'effect':'weather/corona-flare','count':count,'runningTimeMs':0})
            s.command({'op':'corona-style','id':1});s.advance_to(250000);row=self.corona(s)
            rows.append((row['radius'],row['envelope'],row['coreGlyph'],row['radialSamples']))
        self.assertEqual(rows[0],rows[1])
    def test_independent_cell_and_half_block_ring_colors(self):
        def mix(base,alpha):return sum(int(((base>>shift)&255)+(255-((base>>shift)&255))*alpha+.5)<<shift for shift in (0,8,16))
        for sampling in ('cell','half'):
            s=NativeScene(2030);self.addCleanup(s.close)
            for c in [{'op':'resize','width':80,'height':30},{'op':'prompt','active':False},
              {'op':'environment','stars':0,'style':'linear','sampling':sampling},
              {'op':'material','id':7,'space':'rgb','channels':{'r':1,'g':1,'b':1},'alpha':1},
              {'op':'emitter','id':1,'effect':'weather/corona-flare','count':1,'runningTimeMs':0,'material':7,'alpha':1},
              {'op':'corona-style','id':1,'paint':'material','intensity':1}]:s.command(c)
            s.advance_to(750000);source=s.snapshot();row=self.corona(s);cx,cy=row['center'][:2];x,y=int(cx)+4,int(cy)
            actual=s.render().words()[y*80+x];s.command({'op':'remove-corona-style','id':1});base=s.render().words()[y*80+x];s.restore(source)
            radius=9;envelope=(1-.75/2.4)**2
            def alpha(offset):return math.exp(-((math.hypot(x-cx,2*(y+offset-cy))-radius)/1.7)**2)*envelope*.65
            self.assertEqual(actual[0],base[0]);self.assertEqual(actual[3],base[3])
            self.assertEqual(actual[2],mix(base[2],alpha(.75 if base[0]==0x2580 else .5)))
            self.assertEqual(actual[1],mix(base[1],alpha(.25)) if base[0]==0x2580 else base[1])
    def old56(self,s):
        data=bytearray(s.snapshot()[:13548744]);struct.pack_into('<I',data,12,0x20261056)
        struct.pack_into('<I',data,28,0x20261056);struct.pack_into('<I',data,16,len(data)-24)
        struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data
    def test_old_snapshot_preserves_generic_frame_and_rejects_queued_new_style(self):
        s=self.scene();before=s.render().bytes;old=self.old56(s);s.restore(old)
        self.assertIsNone(self.corona(s));self.assertEqual(s.render().bytes,before)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'corona-style','id':1}]}})
        invalid=self.old56(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(invalid)
        self.assertEqual(s.snapshot(),pure)
