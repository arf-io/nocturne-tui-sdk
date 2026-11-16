"""Real native retained electrical graph geometry and lifecycle oracles."""
from pathlib import Path
import struct,sys,unittest,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

POINTS=[{'position':[0,0,0],'parent':-1},{'position':[3,0,0],'parent':0},
        {'position':[3,4,0],'parent':1},{'position':[3,0,12],'parent':1}]
def arc(**patch):
    return {'op':'electrical-arc','id':7,'points':POINTS,'speed':10,'holdMs':200,
            'fadeMs':300,'jitter':0,'flicker':0,'alpha':.8,**patch}
def info(s):return s.info_complete()['electricalArcs'][0]

class ElectricalGraphs(unittest.TestCase):
    def test_independent_lengths_joint_arrival_and_branch_leaders(self):
        with NativeScene() as s:
            s.command(arc());self.assertEqual(info(s)['segments'],[])
            for time,phase,segments in [
                (200000,'leader',[[0,0,0,2,0,0,1]]),
                (700000,'leader',[[0,0,0,3,0,0,1],[3,0,0,3,4,0,2],[3,0,0,3,0,4,3]]),
                (1500000,'hold',[[0,0,0,3,0,0,1],[3,0,0,3,4,0,2],[3,0,0,3,0,12,3]])]:
                s.advance_to(time);q=info(s);self.assertEqual(q['phase'],phase)
                self.assertEqual(q['segments'],segments);self.assertEqual(q['points'],POINTS)
            s.advance_to(1850000);self.assertEqual(info(s)['phase'],'fade');self.assertAlmostEqual(info(s)['opacity'],.4)
            s.advance_to(2000000);self.assertEqual(info(s)['phase'],'finished');self.assertEqual(info(s)['segments'],[])
    def test_delay_and_repeat_keep_graph_and_epoch(self):
        with NativeScene() as s:
            s.command(arc(delayMs=100,repeatMs=2500));s.advance_to(50000)
            self.assertEqual(info(s)['phase'],'waiting');self.assertEqual(info(s)['segments'],[])
            s.advance_to(2800000);self.assertEqual(info(s)['cycle'],1)
            self.assertEqual(info(s)['segments'],[[0,0,0,2,0,0,1]])
    def test_application_layering_query_purity_and_partition_replay(self):
        with NativeScene() as s:
            s.command({'op':'environment','stars':0,'style':'solid'})
            s.command({'op':'window','id':1,'position':[-10,0,0],'width':20,'height':8,'text':'Retained circuit'})
            s.command({'op':'draft','text':'operator draft','emitWeather':False});s.command(arc())
            start=s.snapshot();s.advance_to(700000);expected=s.snapshot();frame=s.render().bytes
            q=info(s);q['points'][0]['position'][0]=999;s.render();s.info_complete()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(info(s)['points'],POINTS)
            s.command({'op':'remove-electrical-arc','id':7});self.assertNotEqual(s.render().bytes,frame)
            self.assertEqual(s.info_complete()['prompt']['text'],'operator draft')
            s.restore(start)
            for time in (100000,300000,500000,700000):s.advance_to(time);s.render();s.info_complete()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
    def test_invalid_graphs_duplicate_capacity_and_unknowns_are_atomic(self):
        with NativeScene() as s:
            bad=[arc(points=[]),arc(speed=0),arc(repeatMs=1999),arc(alpha=2),arc(jitter=-1),arc(unknown=1),
                 arc(points=[POINTS[0],{'position':[1,0,0],'parent':1}]),
                 arc(points=[POINTS[0],{'position':[0,0,0],'parent':0}]),
                 arc(points=[POINTS[0],{'position':[1,0,0],'parent':0,'extra':1}])]
            for c in bad:
                before=s.snapshot()
                with self.assertRaises(ValueError):s.command(c)
                self.assertEqual(s.snapshot(),before)
            for ident in range(1,17):s.command(arc(id=ident))
            before=s.snapshot()
            for c in (arc(id=1),arc(id=17)):
                with self.assertRaises(ValueError):s.command(c)
                self.assertEqual(s.snapshot(),before)
            s.command({'op':'remove-electrical-arc','id':1});s.command(arc(id=17))
            self.assertEqual(len(s.info_complete()['electricalArcs']),16)
    def test_reduced_motion_keeps_endpoint_geometry_and_clock_state(self):
        with NativeScene() as s:
            s.command(arc(jitter=2,flicker=.5));s.command({'op':'accessibility','reducedMotion':True})
            s.advance_to(200000);q=info(s);before=s.snapshot();s.render();s.render()
            self.assertEqual(s.snapshot(),before);self.assertEqual(q['phase'],'leader')
            self.assertEqual(q['segments'],[[0,0,0,2,0,0,1]])
    def test_seed_variants_keep_shared_joints_and_reduced_motion_removes_fluctuation(self):
        with NativeScene() as first,NativeScene() as second:
            for scene,seed in ((first,1),(second,2)):
                scene.command({'op':'environment','stars':0,'style':'solid'})
                scene.command(arc(seed=seed,jitter=2,flicker=.5));scene.advance_to(700000)
                self.assertEqual(info(scene)['points'],POINTS)
            self.assertEqual(info(first)['segments'],info(second)['segments'])
            self.assertNotEqual(first.render().bytes,second.render().bytes)
            for scene in (first,second):scene.command({'op':'accessibility','reducedMotion':True})
            self.assertEqual(first.render().bytes,second.render().bytes)
            for scene in (first,second):
                before=scene.snapshot();scene.render();scene.info_complete();self.assertEqual(scene.snapshot(),before)
    def test_schema51_promotes_empty_arcs_and_corrupt_parent_rejects(self):
        with NativeScene() as s:
            source=s.snapshot();old=bytearray(source[:24+13497392])
            for offset in (12,28):struct.pack_into('<I',old,offset,0x20261051)
            struct.pack_into('<I',old,16,13497392);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
            original=bytes(old);s.restore(old);self.assertEqual(bytes(old),original)
            self.assertEqual(s.info_complete()['electricalArcs'],[])
            self.assertEqual(s.snapshot()[24+13497392:24+13497392+16*1112+768+32768],bytes(16*1112+768+32768))
            s.command(arc());valid=s.snapshot();bad=bytearray(valid)
            # First circuit:88-byte header; second point's parent after XYZ.
            struct.pack_into('<i',bad,24+13497392+88+32+24,1)
            struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
            with self.assertRaises(ValueError):s.restore(bad)
            self.assertEqual(s.snapshot(),valid)
    def test_weather_clear_preserves_application_and_queued_old_feature_rejects(self):
        with NativeScene() as s:
            s.command({'op':'draft','text':'retain source','emitWeather':False});s.command(arc())
            s.command({'op':'clear','scope':'weather'});self.assertEqual(s.info_complete()['electricalArcs'],[])
            self.assertEqual(s.info_complete()['prompt']['text'],'retain source')
            s.command({'op':'schedule','id':4,'atUs':1000000,'command':arc()})
            current=s.snapshot();old=bytearray(current[:24+13497392])
            for offset in (12,28):struct.pack_into('<I',old,offset,0x20261051)
            struct.pack_into('<I',old,16,13497392);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
            original=bytes(old)
            with self.assertRaises(ValueError):s.restore(old)
            self.assertEqual(bytes(old),original);self.assertEqual(s.snapshot(),current)
    def test_nested_queued_arc_source_schema_gate_and_current_restore(self):
        with NativeScene() as s:
            s.command({'op':'schedule','id':4,'atUs':1000000,'command':{'op':'batch','commands':[arc()]}})
            current=s.snapshot();s.restore(current);s.advance_to(1200000)
            self.assertEqual(info(s)['segments'],[[0,0,0,2,0,0,1]])
            old=bytearray(current[:24+13497392])
            for offset in (12,28):struct.pack_into('<I',old,offset,0x20261051)
            struct.pack_into('<I',old,16,13497392);struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
            before=s.snapshot()
            with self.assertRaises(ValueError):s.restore(old)
            self.assertEqual(s.snapshot(),before)
