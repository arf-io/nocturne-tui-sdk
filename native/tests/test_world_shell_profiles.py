"""Independent original world shell equations through the real native SDK."""
from pathlib import Path
import math,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

def command(effect='weather/ejecta-shell',**patch):
    return {'op':'emitter','id':1,'effect':effect,'seed':73,'count':32,'runningTimeMs':0,
            'position':[0,0,0],'velocity':[0,0,0],'radius':2,'wind':[0,0,0],
            'spread':[0,0,0],
            'windVariation':[0,0,0],'collision':False,'deposit':False,
            'lifetimeMinMs':5000,'lifetimeMaxMs':5000,**patch}
def original(index,count,seed,scale,time,clumpy=True):
    y=1-2*(index+.5)/count;ring=math.sqrt(1-y*y);angle=index*2.399963229728653+seed*.0001
    variation=1+.13*math.sin(angle*3+y*8+seed) if clumpy else 1
    radius=scale*(1+time*4.2)*variation
    return [math.cos(angle)*ring*radius,y*radius,math.sin(angle)*ring*radius]

class WorldShellProfiles(unittest.TestCase):
    def test_original_clumpy_nova_positions_at_native_clock_boundaries(self):
        with NativeScene() as s:
            s.command(command())
            for time in (8333,250000,750000):
                s.advance_to(time);age=s.info()['clock']['step']/120
                for i,row in enumerate(s.particles()):
                    expected=original(i,32,73,2,age)
                    for actual,want in zip(row[3:6],expected):self.assertAlmostEqual(actual/65536,want,delta=.0015)
    def test_pressure_shell_has_equal_radii_and_full_world_depth(self):
        with NativeScene() as s:
            s.command(command('weather/pressure-shell'));s.advance_to(750000)
            expected=2*(1+s.info()['clock']['step']/120*4.2);rows=s.particles()
            radii=[math.sqrt(sum((v/65536)**2 for v in row[3:6])) for row in rows]
            self.assertTrue(all(abs(r-expected)<.0015 for r in radii))
            self.assertTrue(any(row[5]>65536 for row in rows));self.assertTrue(any(row[5]<-65536 for row in rows))
    def test_owned_profile_metadata_and_explicit_generic_topology_override(self):
        with NativeScene() as s:
            s.command(command(topology=1));q=s.info_complete()['emitters'][0]['worldShellProfile']
            self.assertEqual(q['shape'],'clumpy-fibonacci');self.assertFalse(q['active']);before=s.snapshot()
            q['shape']='caller changed';s.render();self.assertEqual(s.snapshot(),before)
            self.assertEqual(s.info()['emitters'][0]['worldShellProfile']['shape'],'clumpy-fibonacci')
            s.advance_to(8333);self.assertTrue(all(abs(row[8]/65536)<.15 for row in s.particles()))
    def test_authored_gravity_and_render_snapshot_replay_remain_real(self):
        with NativeScene() as s:
            s.command(command('weather/pressure-shell',gravity=[0,-2,0]));start=s.snapshot()
            s.advance_to(750000);expected=s.snapshot();frame=s.render().bytes;s.info_complete();self.assertEqual(s.snapshot(),expected)
            s.restore(start)
            for t in (100000,250000,500000,750000):s.advance_to(t);s.render()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
            self.assertLess(sum(r[4]/65536 for r in s.particles())/32,-.4)
    def test_invalid_topology_preserves_existing_live_shell(self):
        with NativeScene() as s:
            s.command(command());s.advance_to(250000);before=s.snapshot()
            with self.assertRaises(ValueError):s.command(command(id=2,topology=6))
            self.assertEqual(s.snapshot(),before)
    def test_explicit_spread_retains_real_birth_velocity(self):
        with NativeScene() as plain,NativeScene() as spread:
            plain.command(command());spread.command(command(spread=[1,0,0]))
            plain.advance_to(8333);spread.advance_to(8333)
            pairs=list(zip(plain.particles(),spread.particles()))
            self.assertTrue(any(a[6]!=b[6] for a,b in pairs))
            self.assertTrue(all(a[7:9]==b[7:9] for a,b in pairs))
