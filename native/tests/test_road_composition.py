"""Current native road geometry, named contact and retained path travel."""
from pathlib import Path
import sys,unittest
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'examples'),str(ROOT/'bindings/python')]
from nocturne_native import NativeScene
from road_scene import RoadConfig,install_road

class RoadComposition(unittest.TestCase):
    def test_independent_straight_corner_and_reverse_positions(self):
        configs=[(RoadConfig(),1000000,[0,1.7,-2]),
                 (replace(RoadConfig(),points=((0,0,0),(3,0,0),(3,0,-4)),speed=5),1000000,[3,1.7,-2]),
                 (replace(RoadConfig(),mode='reverse'),6000000,[0,1.7,-8])]
        for config,time,expected in configs:
            with self.subTest(config=config),NativeScene() as s:
                install_road(s,config);s.advance_to(time)
                self.assertEqual(s.info_complete()['camera']['position'],expected)
                for ident in (config.road_surface_id,config.edge_surface_id,config.marking_surface_id,config.terrain_surface_id):
                    self.assertGreater(len(s.surface_triangles(ident)),0)
    def test_real_particle_contact_uses_road_surface_not_global_floor(self):
        with NativeScene() as s:
            c=RoadConfig();install_road(s,c)
            s.command({'op':'emitter','id':1,'effect':'weather/rain-threads','count':1,
                       'runningTimeMs':0,'shape':'point','position':[0,1,-1],'extent':[0,0,0],
                       'velocity':[0,-10,0],'spread':[0,0,0],'gravity':[0,0,0],
                       'wind':[0,0,0],'windVariation':[0,0,0],'drag':0,'lift':0,
                       'collision':True,'deposit':True,
                       'colliders':{'floor':False,'surfaces':[c.road_surface_id]},
                       'lifetimeMinMs':2000,'lifetimeMaxMs':2000})
            s.advance_to(200000)
            surface=next(q for q in s.info_complete()['surfaces'] if q['id']==c.road_surface_id)
            self.assertGreater(surface['impacts'],0)
    def test_invalid_geometry_or_missing_target_rolls_back_complete_install(self):
        for c in (replace(RoadConfig(),width=0),replace(RoadConfig(),points=((0,0,0),(0,0,0))),
                  replace(RoadConfig(),target_family='node',target_id=999)):
            with self.subTest(config=c),NativeScene() as s:
                before=s.snapshot()
                with self.assertRaises(ValueError):install_road(s,c)
                self.assertEqual(s.snapshot(),before)
    def test_application_ownership_freeze_and_partition_replay(self):
        with NativeScene() as s:
            s.command({'op':'window','id':90,'text':'Retained road application','position':[10,4,-4],'width':20,'height':8})
            s.command({'op':'draft','text':'NOC travel draft','emitWeather':False})
            c=RoadConfig();install_road(s,c);s.advance_to(1000000);start=s.snapshot()
            s.advance_to(3000000);expected=s.snapshot();frame=s.render().bytes
            info=s.info_complete();self.assertEqual(info['prompt']['text'],'NOC travel draft')
            self.assertEqual(info['windows'][0]['text'],'Retained road application')
            self.assertEqual(s.snapshot(),expected)
            s.restore(start)
            for t in (1500000,2000000,2500000,3000000):s.advance_to(t);s.render();s.info_complete()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
            position=s.info_complete()['camera']['position']
            s.command({'op':'remove-path-travel','id':c.actor_id});s.advance_to(4000000)
            self.assertEqual(s.info_complete()['camera']['position'],position)
    def test_coexists_with_waterfall_geometry_and_flow_ownership(self):
        from waterfall_scene import WaterfallConfig,install_waterfall
        with NativeScene() as s:
            water=WaterfallConfig();install_waterfall(s,water)
            road=replace(RoadConfig(),points=((10,0,5),(10,0,-5)),road_surface_id=4,
                         edge_surface_id=5,terrain_surface_id=6,marking_surface_id=7)
            before=s.surface_triangles(water.channel_surface_id);install_road(s,road)
            self.assertEqual(s.surface_triangles(water.channel_surface_id),before)
            s.advance_to(1000000);self.assertEqual(s.info_complete()['camera']['position'],[10,1.7,3])
            s.command({'op':'set','path':water.control_path,'value':0});s.advance_to(2000000)
            self.assertEqual(s.info_complete()['camera']['position'],[10,1.7,1])
            self.assertAlmostEqual(s.info_complete()['flows'][0]['deliveredVolume'],2)
