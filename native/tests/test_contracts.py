"""Independent native invariants. Normal tests never bless reference outputs."""
import ctypes as C
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))

class NativeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from nocturne_native import NativeScene
        cls.Scene=NativeScene
    def setUp(self): self.s=self.Scene(seed=2030)
    def tearDown(self): self.s.close()
    def test_render_is_pure_and_owned(self):
        a=self.s.snapshot(); f=self.s.render(); self.assertEqual(a,self.s.snapshot()); self.assertEqual(f,self.s.render())
        self.s.command({'op':'input','text':'hello'}); self.assertNotEqual(f,self.s.render()); self.assertEqual(f.width,160)
    def test_reject_is_atomic(self):
        for cmd in [{'op':'resize','width':0,'height':40},{'op':'camera','near':10,'far':2},{'op':'unknown'}, {'op':'input','text':'lost','unexpected':1}]:
            before=self.s.snapshot()
            with self.assertRaises(ValueError): self.s.command(cmd)
            self.assertEqual(before,self.s.snapshot())
    def test_held_input_true_endpoints(self):
        self.s.command({'op':'pause','paused':True}); self.s.command({'op':'input','text':'abcd'})
        self.s.command({'op':'key','key':'a','ctrl':True});self.s.command({'op':'input','text':'X'})
        self.s.command({'op':'key','key':'e','ctrl':True});self.s.command({'op':'input','text':'Y'})
        self.assertEqual(self.s.info()['prompt']['text'],'XabcdY'); self.assertEqual(self.s.info()['clock']['timeUs'],0)
    def test_document_preserved_all_views(self):
        self.s.command({'op':'input','text':'a long\nretained document'})
        for mode in ['grow','vim-inline','vim-full','marquee']:
            self.s.command({'op':'prompt','mode':mode});self.s.render();self.assertEqual(self.s.info()['prompt']['text'],'a long\nretained document')
    def test_snapshot_roundtrip_and_tamper_rejection(self):
        self.s.command({'op':'input','text':'retained'}); a=self.s.snapshot();self.s.command({'op':'input','text':' more'}); self.s.restore(a)
        self.assertEqual(self.s.info()['prompt']['text'],'retained'); b=bytearray(a);b[-1]^=1
        with self.assertRaises(ValueError):self.s.restore(b)
        self.assertEqual(a,self.s.snapshot())
    def test_seeded_weather_replay_frame_rate(self):
        command={'op':'emitter','id':1,'effect':'weather/autumn-drift','count':12,'runningTimeMs':600,'position':[0,10,0]}
        self.s.command(command)
        other=self.Scene(seed=2030);other.command(command)
        try:
            for i in range(1,31):self.s.advance_to(i*1000000//30)
            for i in range(1,61):other.advance_to(i*1000000//60)
            self.assertEqual(self.s.snapshot(),other.snapshot());self.assertEqual(self.s.render().bytes,other.render().bytes)
        finally:other.close()
    def test_look_does_not_change_weather(self):
        self.s.command({'op':'emitter','id':1,'effect':'weather/autumn-drift','count':10,'runningTimeMs':0})
        self.s.advance_to(500000);before=self.s.particles();self.s.command({'op':'look','yaw':180});self.s.render();self.assertEqual(before,self.s.particles())
    def test_no_click_weather(self):
        self.s.render();before=self.s.info()['fieldCount'];self.s.command({'op':'pointer','phase':'down','x':10,'y':10});self.s.command({'op':'pointer','phase':'move','x':25,'y':10});self.s.command({'op':'pointer','phase':'up','x':25,'y':10});self.assertEqual(before,self.s.info()['fieldCount'])
    def test_opposite_wheel(self):
        a=self.s.info()['camera']['position'];self.s.command({'op':'wheel','delta':1});b=self.s.info()['camera']['position'];self.s.command({'op':'wheel','delta':-1});self.assertEqual(a,self.s.info()['camera']['position']);self.assertNotEqual(a,b)
    def test_local_weather_distinct(self):
        self.s.command({'op':'input','text':'abc'});self.assertEqual(self.s.info()['fieldCount'],3)
        before=self.s.info()['fields'];self.s.command({'op':'input','text':'d'});self.assertEqual(before,self.s.info()['fields'][:3])
    def test_graph_retains_full_source(self):
        text='Project '+('full descriptive name '*5)
        self.s.command({'op':'node','id':1,'label':text,'kind':'Project','status':'ready','sha':'f'*64});self.s.render()
        self.assertEqual(self.s.info()['nodes'][0]['label'],text)
    def test_deposits_survive_emitter_stop(self):
        self.s.command({'op':'floor','height':0,'maxIndividual':50,'enabled':True})
        self.s.command({'op':'emitter','id':1,'effect':'weather/autumn-drift','count':8,'runningTimeMs':0,'position':[0,0.2,0],'extent':[1,0,1],'gravity':[0,-9,0],'wind':[0,0,0],'windVariation':[0,0,0],'velocity':[0,-1,0],'spread':[0,0,0],'lifetimeMinMs':10000,'lifetimeMaxMs':10000})
        self.s.advance_to(4000000);n=self.s.info()['particles']['deposited'];self.assertGreater(n,0)
        self.s.command({'op':'stop','id':1,'style':'drain'});self.assertEqual(n,self.s.info()['particles']['deposited'])
    def test_color_boundary(self):
        self.assertEqual(self.s.oklch(0,0,0),0);self.assertEqual(self.s.oklch(1,0,0),0xffffff)
    def test_scene_support_is_truthful(self):
        self.assertEqual(len({e['id'] for e in self.s.catalogue()}),len(self.s.catalogue()))
        with self.assertRaises(ValueError):self.s.command({'op':'emitter','id':1,'effect':'weather/nonexistent'})

if __name__=='__main__':unittest.main()
