"""Original world nova appearance equations, real C execution and capture ownership."""
from pathlib import Path
import math,struct,sys,unittest,zlib
import test_world_shell_profiles as shell
from nocturne_native import NativeScene

def h(v):
    v&=0xffffffff;v=((v^(v>>16))*0x7feb352d)&0xffffffff;v=((v^(v>>15))*0x846ca68b)&0xffffffff;return v^(v>>16)
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def reference(i,count,seed,age,life):
    latitude=1-2*(i+.5)/count;angle=i*2.399963229728653+seed*.0001
    clump=.3+.7*math.sin(2*angle+9*latitude+seed)**2
    a=h(seed^(((4*i+1)*0x9e3779b1)&0xffffffff))/4294967296
    return clump,smooth(age/.12)*smooth((1-age/life)*2)*clump,25+260*age/life+60*a
def optics(s):return s.info_complete()['emitters'][0]['novaOptics']

class WorldNovaOptics(unittest.TestCase):
    def test_independent_source_envelope_clump_and_hue(self):
        with NativeScene() as s:
            s.command(shell.command(count=8))
            for t in (8333,100000,250000,3000000,4500000):
                s.advance_to(t);age=s.info()['clock']['step']/120
                for row in optics(s)['samples']:
                    expected=reference(row[3],row[2],row[1],age,5)
                    for actual,want in zip(row[5:8],expected):self.assertAlmostEqual(actual,want,delta=1e-5)
    def test_live_capture_survives_future_count_and_topology_edits(self):
        with NativeScene() as s:
            s.command(shell.command(count=8));s.advance_to(250000);before=optics(s)['samples'];particles=s.particles()
            s.command({'op':'define','path':'/count','value':16,'binding':{'family':'emitter','id':1,'field':'count'}})
            s.command({'op':'define','path':'/topology','value':1,'binding':{'family':'emitter','id':1,'field':'topology'}})
            self.assertEqual(optics(s)['samples'],before);self.assertEqual(s.particles(),particles)
    def test_owned_readback_purity_replay_and_terminal_cleanup(self):
        with NativeScene() as s:
            s.command(shell.command(count=32));start=s.snapshot();s.advance_to(750000)
            q=optics(s);self.assertEqual(q['sampleLimit'],16);self.assertEqual(q['activeCapturedParticles'],32);self.assertEqual(len(q['samples']),16)
            expected=s.snapshot();frame=s.render().bytes;q['samples'][0][6]=999;s.render();s.info_complete();self.assertEqual(s.snapshot(),expected)
            s.restore(start)
            for t in (100000,250000,500000,750000):s.advance_to(t);s.render()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
            s.advance_to(5100000);self.assertEqual(optics(s)['samples'],[]);self.assertEqual(s.snapshot()[24+13515952:24+13515952+32768],bytes(32768))
    def test_schema53_promotes_uncaptured_particles_and_corruption_rejects(self):
        with NativeScene() as s:
            s.command(shell.command(count=8));s.advance_to(250000);source=s.snapshot()
            old=bytearray(source[:24+13515952])
            for off in (12,28):struct.pack_into('<I',old,off,0x20261053)
            struct.pack_into('<I',old,16,13515952);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
            original=bytes(old);particles=s.particles();s.restore(old);self.assertEqual(bytes(old),original);self.assertEqual(s.particles(),particles);self.assertEqual(optics(s)['samples'],[])
            s.restore(source);bad=bytearray(source);struct.pack_into('<I',bad,24+13515952+8,0)
            struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
            with self.assertRaises(ValueError):s.restore(bad)
            self.assertEqual(s.snapshot(),source)
    def test_source_optics_changes_real_frame_and_material_alpha_still_controls(self):
        with NativeScene() as s:
            s.command({'op':'environment','style':'solid','stars':0});s.command(shell.command(count=32,material=2));s.advance_to(750000)
            source=s.snapshot();captured=s.render().bytes;old=bytearray(source[:24+13515952])
            for off in (12,28):struct.pack_into('<I',old,off,0x20261053)
            struct.pack_into('<I',old,16,13515952);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
            s.restore(old);self.assertNotEqual(s.render().bytes,captured)
            s.restore(source);s.command({'op':'material','id':2,'alpha':0});self.assertFalse(s.render().bytes==captured,'Authored material alpha must affect visible source optics')
