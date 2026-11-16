"""Independent original source hashes, analytic offsets, glyphs and opacity."""
import math,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
EFFECTS={'rain':'weather/rain-threads','snow':'weather/snow-dust','embers':'weather/lantern-motes','sparks':'weather/pinfire'}
def random_at(seed,index):
    v=(seed^(((index+1)*0x9e3779b9)&0xffffffff))&0xffffffff
    v=((v^(v>>16))*0x7feb352d)&0xffffffff;v=((v^(v>>15))*0x846ca68b)&0xffffffff
    return (v^(v>>16))/4294967296
def expected(kind,index,t,seed=73,speed=12,intensity=.5):
    r=random_at(seed,index);r2=random_at(seed+7919,index)
    if kind=='rain':x=(r-.5)*20;y=-r2*14+t*speed;glyph=0x2571 if index%2 else 0x2502
    elif kind=='snow':x=(r-.5)*24+math.sin(t*2+r2*math.tau)*2;y=-12-r2*8+t*speed*.4;glyph=(0xb7,0x2219,0x22c5)[index%3]
    elif kind=='embers':x=(r-.5)*t*8;y=-t*speed*(.2+r2*.4);glyph=0x2219
    else:x=math.cos(r*math.tau)*t*speed*r2;y=math.sin(r*math.tau)*t*speed*r2/2+t*t*2;glyph=0xb7
    return [index,x,y,glyph,intensity*max(0,1-t/2.4)**2*(.5+.5*r)]
class ObservatoryProfiles(unittest.TestCase):
    def scene(self,effect,position=None):
        s=NativeScene(2030);self.addCleanup(s.close)
        s.command({'op':'emitter','id':1,'effect':effect,'count':32,'runningTimeMs':0,**({'position':position} if position is not None else {})})
        s.command({'op':'draft','text':'Observatory source draft','emitWeather':False});return s
    def row(self,s):return next(e for e in s.info_complete()['emitters'] if e['id']==1).get('observatory')
    def test_original_equations_all_four_profiles_and_pure_replay(self):
        for kind,effect in EFFECTS.items():
            with self.subTest(kind=kind):
                s=self.scene(effect);s.command({'op':'observatory-style','id':1,'seed':73,'speed':12,'intensity':.5,'durationMs':2400})
                initial=s.snapshot();frames=[]
                for us in (0,250000,1000000,2400000):
                    s.advance_to(us);pure=s.snapshot();row=self.row(s)
                    self.assertEqual(row['profile'],kind);self.assertEqual(row['count'],28)
                    self.assertEqual(len(row['samples']),16 if us<2400000 else 0)
                    for index,sample in enumerate(row['samples']):
                        for actual,want in zip(sample,expected(kind,index,us/1e6)):self.assertAlmostEqual(actual,want,delta=2e-5)
                    frames.append(s.render().bytes);self.assertEqual(s.info_complete()['prompt']['text'],'Observatory source draft');self.assertEqual(s.snapshot(),pure)
                final=s.snapshot();s.restore(initial)
                for us,frame in zip((0,250000,1000000,2400000),frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                self.assertEqual(s.snapshot(),final)
    def test_retarget_epoch_removal_and_invalid_controls(self):
        s=self.scene(EFFECTS['rain']);s.command({'op':'observatory-style','id':1});s.advance_to(250000)
        s.command({'op':'observatory-style','id':1,'speed':4});self.assertEqual(self.row(s)['elapsedUs'],250000)
        pure=s.snapshot()
        for patch in [{'speed':-1},{'intensity':1.01},{'durationMs':0},{'durationMs':.0001},{'seed':-1},{'id':65535}]:
            with self.assertRaises(ValueError):s.command({'op':'observatory-style','id':1,**patch})
            self.assertEqual(s.snapshot(),pure)
        s.command({'op':'remove-observatory-style','id':1});self.assertIsNone(self.row(s))
        other=self.scene('weather/autumn-drift');pure=other.snapshot()
        with self.assertRaises(ValueError):other.command({'op':'observatory-style','id':1})
        self.assertEqual(other.snapshot(),pure)
    def test_visible_glyphs_from_independent_equations_and_near_plane(self):
        for kind,effect in EFFECTS.items():
            with self.subTest(kind=kind):
                s=self.scene(effect,position=[0,-10,0])
                for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},
                  {'op':'environment','stars':0},{'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
                  {'op':'observatory-style','id':1,'seed':73,'intensity':.5,'paint':'material'}]:s.command(c)
                s.advance_to(250000);row=self.row(s);cx,cy=row['center'][:2];frame=s.render();occupied={}
                # Explicit material mode preserves prior direct placement; the source
                # integration oracle separately verifies original tile rounding.
                # Later indices paint last where source trajectories coincide.
                for index in range(28):
                    _,dx,dy,glyph,_=expected(kind,index,.25)
                    x,y=math.floor(cx+dx),math.floor(cy+dy)
                    if 0<=x<100 and 0<=y<40:occupied[(x,y)]=glyph
                self.assertGreater(len(occupied),0)
                for (x,y),glyph in occupied.items():self.assertEqual(frame.words()[y*100+x][0],glyph)
                s.command({'op':'camera','position':[0,0,-40]});s.render();self.assertFalse(self.row(s)['visible'])
    def test_clear_remove_and_generation_reuse(self):
        s=self.scene(EFFECTS['snow']);s.command({'op':'observatory-style','id':1})
        s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['emitters'],[])
        s.command({'op':'emitter','id':1,'effect':EFFECTS['snow'],'count':1,'runningTimeMs':0});self.assertIsNone(self.row(s))
        s.command({'op':'observatory-style','id':1});s.command({'op':'clear-instance','id':1});self.assertEqual(s.info_complete()['emitters'],[])
    def old57(self,s):
        data=bytearray(s.snapshot()[:13549512]);struct.pack_into('<I',data,12,0x20261057)
        struct.pack_into('<I',data,28,0x20261057);struct.pack_into('<I',data,16,len(data)-24)
        struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data
    def test_old_snapshot_retains_generic_and_rejects_queued_new_profile(self):
        s=self.scene(EFFECTS['rain']);before=s.render().bytes;s.restore(self.old57(s))
        self.assertIsNone(self.row(s));self.assertEqual(s.render().bytes,before)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'observatory-style','id':1}]}})
        invalid=self.old57(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(invalid)
        self.assertEqual(s.snapshot(),pure)
