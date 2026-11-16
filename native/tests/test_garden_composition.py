"""Real garden contacts, registered force control and application ownership."""
from pathlib import Path
from dataclasses import replace
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'examples'),str(ROOT/'bindings/python')]
from nocturne_native import NativeScene
from garden_scene import GardenConfig,install_garden
class GardenComposition(unittest.TestCase):
    def test_registered_forces_match_independent_public_edits(self):
        with NativeScene(42) as s,NativeScene(42) as oracle:
            c=GardenConfig()
            for scene in (s,oracle):install_garden(scene,c);scene.advance_to(250000)
            s.command({'op':'set','path':c.wind_path,'value':2})
            oracle.command({'op':'forces','id':c.leaf_id,'wind':[2,0,0]})
            s.command({'op':'set','path':c.heat_path,'value':.5})
            oracle.command({'op':'forces','id':c.ember_id,'heat':.5})
            for scene in (s,oracle):
                scene.command({'op':'remove-value','path':c.wind_path})
                scene.command({'op':'remove-value','path':c.heat_path})
            self.assertEqual(s.snapshot(),oracle.snapshot())
            for time in (500000,1000000,2000000):
                s.advance_to(time);oracle.advance_to(time)
                self.assertEqual(s.snapshot(),oracle.snapshot())
                self.assertEqual(s.render().bytes,oracle.render().bytes)
    def test_actual_named_contacts_accumulation_and_wet_response(self):
        with NativeScene() as s:
            c=GardenConfig();install_garden(s,c);s.advance_to(3000000);q=s.info_complete()
            surface=next(row for row in q['surfaces'] if row['id']==c.surface_id)
            self.assertGreater(surface['impacts'],0);self.assertGreater(surface['wetness'],0)
            leaves=[row for row in q['deposits'] if row['surfaceId']==c.surface_id]
            self.assertGreater(len(leaves),0)
    def test_invalid_installation_is_atomic(self):
        for c in (replace(GardenConfig(),width=0),replace(GardenConfig(),leaf_id=0),
                  replace(GardenConfig(),wind_path='relative')):
            with self.subTest(config=c),NativeScene() as s:
                before=s.snapshot()
                with self.assertRaises(ValueError):install_garden(s,c)
                self.assertEqual(s.snapshot(),before)
    def test_application_source_owned_queries_and_partition_replay(self):
        with NativeScene() as s:
            s.command({'op':'window','id':90,'text':'Garden application','position':[10,4,-4],'width':20,'height':8})
            s.command({'op':'draft','text':'NOC garden draft','emitWeather':False})
            c=GardenConfig();install_garden(s,c);s.advance_to(1000000);start=s.snapshot()
            s.advance_to(3000000);expected=s.snapshot();frame=s.render().bytes
            q=s.info_complete();self.assertEqual(q['prompt']['text'],'NOC garden draft')
            self.assertEqual(q['windows'][0]['text'],'Garden application')
            q['surfaces'].clear();self.assertTrue(s.info_complete()['surfaces']);self.assertEqual(s.snapshot(),expected)
            s.restore(start)
            for time in (1500000,2000000,2500000,3000000):s.advance_to(time);s.render();s.info_complete()
            self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
