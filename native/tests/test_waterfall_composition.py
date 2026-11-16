"""Real complete waterfall assembly and independent delayed conservation oracles."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'examples'),str(ROOT/'bindings/python')]
from nocturne_native import NativeScene
from waterfall_scene import WaterfallConfig, build_waterfall_commands, install_waterfall
from dataclasses import replace

def q(scene):return scene.info_complete()
class WaterfallComposition(unittest.TestCase):
    def test_one_control_drives_both_depths_and_outlet_allocation(self):
        with NativeScene(42) as s:
            c=WaterfallConfig(channel_delay_us=250000,sheet_delay_us=250000,tail_us=0,evaporation_us=0)
            install_waterfall(s,c);s.advance_to(1000000);info=q(s)
            self.assertAlmostEqual(info['flows'][0]['injectedVolume'],2)
            self.assertAlmostEqual(info['flows'][0]['deliveredVolume'],1)
            self.assertAlmostEqual(info['flowSinks'][0]['receivedVolume'],.75)
            self.assertAlmostEqual(info['flowSprays'][0]['receivedVolume'],.25)
            self.assertAlmostEqual(s.flow_thickness(c.channel_surface_id)[1],c.flux/(c.width*c.channel_speed))
            self.assertAlmostEqual(s.flow_thickness(c.sheet_surface_id)[1],c.flux/(c.width*c.sheet_speed))
            s.command({'op':'set','path':c.control_path,'value':0})
            s.advance_to(2000000);info=q(s)
            self.assertAlmostEqual(info['flows'][0]['injectedVolume'],2)
            self.assertAlmostEqual(info['flows'][0]['deliveredVolume'],2)
            self.assertAlmostEqual(info['flowSinks'][0]['receivedVolume'],1.5)
            self.assertAlmostEqual(info['flowSprays'][0]['receivedVolume'],.5)
            self.assertEqual(s.flow_thickness(c.channel_surface_id)[1],0)
            self.assertEqual(s.flow_thickness(c.sheet_surface_id)[1],0)
            s.command({'op':'set','path':c.control_path,'value':1});s.advance_to(3000000)
            self.assertAlmostEqual(q(s)['flows'][0]['deliveredVolume'],2.5)

    def test_actual_spray_impacts_basin_and_retains_conserved_water(self):
        with NativeScene() as s:
            c=WaterfallConfig();install_waterfall(s,c);s.advance_to(3000000);info=q(s)
            spray=info['flowSprays'][0];sink=info['flowSinks'][0]
            self.assertGreater(spray['impactedVolume'],0)
            self.assertGreater(info['surfaces'][c.basin_surface_id-1]['impacts'],0)
            water=next(row for row in info['surfaceWater'] if row['surfaceId']==c.basin_surface_id)
            self.assertGreater(water['retainedVolume'],0)
            self.assertAlmostEqual(water['receivedVolume'],water['retainedVolume']+water['evaporatedVolume']+water['exportedVolume']+water['transferredVolume'],places=6)
            self.assertAlmostEqual(spray['receivedVolume'],spray['emittedVolume']+spray['pendingVolume'],places=6)
            self.assertAlmostEqual(spray['emittedVolume'],sum(spray[k] for k in ('liveVolume','expiredVolume','impactedVolume','exportedVolume','legacyUnresolvedVolume')),places=6)
            self.assertAlmostEqual(sink['receivedVolume'],sink['retainedVolume']+sink['evaporatedVolume'],places=6)

    def test_shared_lip_is_exact_before_extrusion_and_geometry_is_not_replaced(self):
        with NativeScene() as s:
            c=WaterfallConfig();commands=build_waterfall_commands(c)
            at=next(i for i,x in enumerate(commands) if x['op']=='flow-thickness')
            for command in commands[:at]:s.command(command)
            channel=s.surface_triangles(c.channel_surface_id);sheet=s.surface_triangles(c.sheet_surface_id)
            channel_vertices={tuple(row[i:i+3]) for row in channel for i in (0,3,6)}
            for row in sheet:
                for i in (0,3,6):
                    xyz=tuple(row[i:i+3])
                    if xyz[1]==c.height:self.assertIn(xyz,channel_vertices)

    def test_invalid_installation_rolls_back_all_surfaces_geometry_and_values(self):
        for c in (replace(WaterfallConfig(),width=0),replace(WaterfallConfig(),spray_fraction=1.5),replace(WaterfallConfig(),sheet_surface_id=1)):
            with self.subTest(config=c),NativeScene() as s:
                before=s.snapshot()
                with self.assertRaises(ValueError):install_waterfall(s,c)
                self.assertEqual(before,s.snapshot())

    def test_existing_application_source_survives_stop_restart_and_partition_replay(self):
        with NativeScene() as s:
            s.command({'op':'window','id':90,'text':'Application source','position':[10,4,-4],'width':20,'height':8})
            s.command({'op':'draft','text':'NOC operator draft','emitWeather':False})
            c=WaterfallConfig();install_waterfall(s,c);s.advance_to(1000000)
            s.command({'op':'set','path':c.control_path,'value':0});start=s.snapshot()
            s.advance_to(2500000);expected=s.snapshot();frame=s.render().bytes
            self.assertEqual(q(s)['prompt']['text'],'NOC operator draft')
            self.assertEqual(q(s)['windows'][0]['text'],'Application source')
            self.assertEqual(s.snapshot(),expected)
            s.restore(start)
            for t in (1200000,1500000,2000000,2500000):s.advance_to(t);s.render();q(s)
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)

    def test_two_compositions_keep_ids_geometry_and_controls_independent(self):
        with NativeScene() as s:
            first=WaterfallConfig();second=replace(first,flow_id=2,emitter_id=2,
                channel_surface_id=4,sheet_surface_id=5,basin_surface_id=6,
                control_path='/other-waterfall/flux',x=10)
            install_waterfall(s,first);original=s.surface_triangles(first.channel_surface_id)
            install_waterfall(s,second)
            self.assertEqual(s.surface_triangles(first.channel_surface_id),original)
            s.command({'op':'set','path':first.control_path,'value':0});s.advance_to(1000000)
            flows={row['id']:row for row in q(s)['flows']}
            self.assertEqual(flows[1]['injectedVolume'],0)
            self.assertEqual(flows[2]['injectedVolume'],2)
            self.assertEqual(q(s)['values'][second.control_path],2)

    def test_existing_owned_channel_cannot_be_reassembled(self):
        with NativeScene() as s:
            c=WaterfallConfig();install_waterfall(s,c);before=s.snapshot()
            with self.assertRaises(ValueError):
                s.command({'op':'waterfall','channelSurfaceId':c.channel_surface_id,
                           'sheetSurfaceId':c.sheet_surface_id,'flowId':c.flow_id,
                           'channelStage':'channel','sheetStage':'sheet','referenceFlux':2,'drop':3})
            self.assertEqual(s.snapshot(),before)
