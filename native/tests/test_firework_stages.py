"""Real source-derived firework stages, geometry, ownership and migration."""
from pathlib import Path
import functools,math,os,struct,subprocess,sys,tempfile,unittest,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

@functools.lru_cache(maxsize=1)
def burst_snapshot_layout():
    """Read the restored extension bounds from the actual native State layout."""
    native=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='nocturne-burst-layout-') as directory:
        p=Path(directory);probe=p/'layout.c';executable=p/'layout'
        probe.write_text('#include "internal.h"\n#include <stddef.h>\n#include <stdio.h>\n'
            'int main(void){printf("%zu %zu\\n",offsetof(State,burstControls),'
            'sizeof(((State*)0)->burstControls));return 0;}\n')
        subprocess.run([os.environ.get('CC','cc'),'-std=c11','-I',str(native/'include'),
            '-I',str(native/'src'),str(probe),'-o',str(executable)],check=True,capture_output=True,text=True)
        return tuple(map(int,subprocess.check_output([str(executable)],text=True).split()))

def emitter(**patch):
    return {'op':'emitter','id':1,'effect':'weather/chrysanthemum','seed':73,'count':1,
            'runningTimeMs':0,'shape':'point','position':[0,0,0],'velocity':[0,0,0],
            'extent':[0,0,0],'spread':[0,0,0],'gravity':[0,0,0],'wind':[0,0,0],
            'windVariation':[0,0,0],'drag':0,'lift':0,'flutterAmount':0,'tumble':[0,0,0],
            'deposit':False,'collision':False,'radius':4,'topology':0,'coreMs':200,
            'trailMs':90,'lifetimeMinMs':2000,'lifetimeMaxMs':2000,**patch}
def stages(scene):return scene.info_complete()['emitters'][0]['burstStages']
def source_hash(value):
    v=value&0xffffffff
    v=((v^(v>>16))*0x7feb352d)&0xffffffff
    v=((v^(v>>15))*0x846ca68b)&0xffffffff
    return v^(v>>16)
def source_random(seed,salt):
    # Independent original JS hash32/randomAt/rand reference, exact uint32 rules.
    return source_hash(seed^(salt*2246822519)^2654435761)/4294967296

class FireworkStages(unittest.TestCase):
    def test_source_core_glitter_and_spoke_numbers_at_native_step_boundaries(self):
        with NativeScene() as s:
            s.command(emitter());s.advance_to(8333);birth_step=s.info()['clock']['step']
            for time in (100000,250000,500000,1500000):
                s.advance_to(time);sample=stages(s)['samples'][0];age=(s.info()['clock']['step']-birth_step)/120
                self.assertAlmostEqual(sample[2],age*1e6,delta=.00001)
                self.assertAlmostEqual(sample[3],math.sqrt(max(0,1-age/.2)),delta=1e-5)
                fade=max(0,1-age/2)**1.5
                expected=fade*(.4+.6*source_random(sample[1],math.floor(age*18)+100))
                self.assertAlmostEqual(sample[4],expected,delta=1e-5)
                self.assertAlmostEqual(sample[5],math.exp(-age/.18) if age<.4 else 0,delta=1e-5)
    def test_new_topologies_are_real_crowns_and_stratified_spheres(self):
        values={}
        for topology in range(6):
            with NativeScene() as s:
                s.command(emitter(count=64,topology=topology));s.advance_to(8333);rows=s.particles()
                velocity=[[v/65536 for v in row[6:9]] for row in rows];values[topology]=velocity
                self.assertEqual(len(rows),64)
                if topology==4:
                    self.assertTrue(all(v[1]/math.sqrt(sum(x*x for x in v))>.57 for v in velocity))
                if topology==5:
                    for i,v in enumerate(velocity):self.assertAlmostEqual(v[1]/math.sqrt(sum(x*x for x in v)),1-2*(i+.5)/64,delta=2e-5)
                if topology==1:self.assertTrue(all(abs(v[2])<.15 for v in velocity))
        self.assertNotEqual(values[4],values[0]);self.assertNotEqual(values[5],values[0]);self.assertNotEqual(values[4],values[2])
    def test_core_control_changes_real_coverage_without_particle_reset(self):
        with NativeScene() as s:
            s.command({'op':'environment','style':'solid','stars':0});s.command(emitter());s.advance_to(8333)
            particles=s.particles();visible=s.render().bytes
            s.command({'op':'burst-style','id':1,'coreAlpha':0,'residualAlpha':0})
            self.assertEqual(s.particles(),particles);self.assertEqual(stages(s)['samples'][0][3],0)
            self.assertNotEqual(s.render().bytes,visible)
            s.command({'op':'burst-style','id':1,'coreMs':0,'coreAlpha':1});self.assertEqual(stages(s)['samples'][0][3],0)
    def test_shared_birth_core_does_not_multiply_with_burst_population(self):
        with NativeScene() as one,NativeScene() as many:
            for scene,count in ((one,1),(many,64)):
                scene.command({'op':'environment','style':'solid','stars':0});scene.command(emitter(count=count));scene.advance_to(8333)
            self.assertEqual(one.render().bytes,many.render().bytes)
    def test_custom_controls_capped_owned_readback_and_purity(self):
        with NativeScene() as s:
            s.command(emitter(count=32));s.command({'op':'burst-style','id':1,'glitterHz':0,'glitterDepth':0,'coreAlpha':.25,'residualMs':500,'residualAlpha':.2})
            s.advance_to(100000);q=stages(s);self.assertEqual(q['sampleLimit'],16);self.assertEqual(q['activeBurstParticles'],32);self.assertEqual(len(q['samples']),16)
            sample=q['samples'][0];age=sample[2]/1e6;self.assertAlmostEqual(sample[3],.25*math.sqrt(1-age/.2),delta=1e-5);self.assertAlmostEqual(sample[4],(1-age/2)**1.5,delta=1e-5)
            self.assertAlmostEqual(sample[5],.2*math.exp(-age/.5),delta=1e-5)
            before=s.snapshot();q['samples'][0][3]=999;s.render();s.info_complete();self.assertEqual(s.snapshot(),before);self.assertLess(stages(s)['samples'][0][3],1)
    def test_invalid_authoring_and_family_reject_atomically(self):
        with NativeScene() as s:
            s.command(emitter())
            for patch in ({'glitterHz':61},{'glitterDepth':2},{'coreAlpha':-1},{'residualMs':0},{'residualAlpha':2},{'coreMs':10001},{'glitterHz':True},{'unknown':1}):
                before=s.snapshot()
                with self.assertRaises(ValueError):s.command({'op':'burst-style','id':1,**patch})
                self.assertEqual(s.snapshot(),before)
            s.command(emitter(id=2,effect='weather/snowglobe'))
            before=s.snapshot()
            with self.assertRaises(ValueError):s.command({'op':'burst-style','id':2,'glitterHz':20})
            self.assertEqual(s.snapshot(),before)
    def test_partition_replay_and_clear_reuse_preserve_particle_ownership(self):
        with NativeScene() as s:
            s.command(emitter(topology=5,count=16));s.command({'op':'burst-style','id':1,'glitterHz':30});start=s.snapshot()
            s.advance_to(750000);expected=s.snapshot();frame=s.render().bytes;s.restore(start)
            for t in (100000,250000,500000,750000):s.advance_to(t);s.render();s.info_complete()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
            s.command({'op':'clear-instance','id':1});s.command(emitter());self.assertEqual(stages(s)['glitterHz'],18)
            s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info()['emitters'],[])
    def test_schema52_promotes_defaults_and_nested_new_style_rejects(self):
        with NativeScene() as s:
            s.command(emitter());current=s.snapshot()
            def old(data):
                b=bytearray(data[:24+13515184])
                for offset in (12,28):struct.pack_into('<I',b,offset,0x20261052)
                struct.pack_into('<I',b,16,13515184);struct.pack_into('<I',b,20,zlib.crc32(b[24:])&0xffffffff);return b
            prior=old(current);original=bytes(prior);s.restore(prior);self.assertEqual(bytes(prior),original)
            offset,size=burst_snapshot_layout();self.assertEqual(offset,13515184)
            # Later snapshot extensions have their own defaults and migrations.
            self.assertEqual(s.snapshot()[24+offset:24+offset+size],bytes(size))
            self.assertEqual(stages(s)['glitterHz'],18)
            s.command({'op':'schedule','id':3,'atUs':1000000,'command':{'op':'batch','commands':[{'op':'burst-style','id':1,'glitterHz':30}]}})
            before=s.snapshot()
            with self.assertRaises(ValueError):s.restore(old(before))
            self.assertEqual(s.snapshot(),before)
    def test_seed_fluctuation_reduced_motion_and_crc_valid_corrupt_control(self):
        with NativeScene() as s:
            s.command(emitter());s.command({'op':'burst-style','id':1,'glitterDepth':.9});s.advance_to(250000)
            seed=stages(s)['samples'][0][1];self.assertEqual(seed,source_hash(73))
            s.command({'op':'accessibility','reducedMotion':True});row=stages(s)['samples'][0]
            self.assertAlmostEqual(row[4],(1-row[2]/2000000)**1.5,delta=1e-5)
            before=s.snapshot();bad=bytearray(before)
            struct.pack_into('<d',bad,24+13515184+16,2)
            struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
            with self.assertRaises(ValueError):s.restore(bad)
            self.assertEqual(s.snapshot(),before)
    def test_full_emitter_capacity_pending_probe_preserves_burst_controls(self):
        with NativeScene() as s:
            s.command(emitter(id=999,count=0))
            s.command({'op':'define','path':'/wind','value':0,'binding':{'family':'emitter','id':999,'field':'wind.x'}})
            s.command({'op':'schedule','id':3,'atUs':1000000,'command':{'op':'set','path':'/wind','value':1}})
            s.command({'op':'clear-instance','id':999})
            for ident in range(1,17):
                s.command(emitter(id=ident,count=0));s.command({'op':'burst-style','id':ident,'glitterHz':20})
            saved=s.snapshot();s.restore(saved);self.assertEqual(s.snapshot(),saved)
            self.assertTrue(all(q['burstStages']['glitterHz']==20 for q in s.info_complete()['emitters']))
