from pathlib import Path
import ctypes as C
import sys,unittest,zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class IntegratedSDKTests(unittest.TestCase):
    def setUp(self):
        self.s=NativeScene();self.addCleanup(self.s.close)
        self.s.command({'op':'environment','background':0x808080,'stars':0,'style':'solid','sampling':'cell'})
    def test_crc_unchanged_against_independent_zlib(self):
        fn=self.s._lib.nrCrc;fn.argtypes=[C.c_void_p,C.c_uint32];fn.restype=C.c_uint32
        for text in [b'',b'123456789',bytes(range(256))*128]:self.assertEqual(fn(text,len(text)),zlib.crc32(text))
    def test_public_sampling_is_owned_and_pure(self):
        self.s.batch([{'op':'text','id':1,'text':'A','local':True},{'op':'window','id':1}]);before=self.s.snapshot()
        self.assertEqual(self.s.text_sample(1,0)[:2],(65,65));self.assertEqual(self.s.window_sample(1,.5,.5,1)[:3],(0,0,0));self.assertEqual(before,self.s.snapshot())
        with self.assertRaises(ValueError):self.s.window_sample(1,float('nan'),.5,1)
        with self.assertRaises(ValueError):self.s.text_sample(1,4096)
    def test_material_blend_affects_the_rendered_glyph(self):
        self.s.batch([{'op':'material','id':5,'space':'rgb','channels':{'r':1,'g':.5,'b':.25},'alpha':1,'blend':'normal'}, {'op':'widget','id':1,'kind':'text','text':'A','x':3,'y':8,'width':4,'height':1,'alpha':0,'material':5}])
        f=self.s.render();normal=f.words()[8*f.width+3][1]
        self.s.command({'op':'material','id':5,'blend':'multiply'});f=self.s.render();multiply=f.words()[8*f.width+3][1]
        self.assertNotEqual(normal,multiply);self.assertEqual(multiply,self.s.composite(0x808080,normal,blend=1)[0])
    def test_background_material_and_active_state_reach_pixels(self):
        self.s.batch([{'op':'material','id':5,'space':'rgb','channels':{'r':.1,'g':.2,'b':.8},'alpha':1},{'op':'widget','id':1,'kind':'box','x':3,'y':8,'width':4,'height':1,'alpha':1,'backgroundMaterial':5}])
        f=self.s.render();self.assertEqual(f.words()[8*f.width+3][2],0x1a33cc)
        before=f.bytes;self.s.command({'op':'widget','id':1,'active':True});self.assertNotEqual(before,self.s.render().bytes)
    def test_inspector_scroll_does_not_consume_camera_gestures_elsewhere(self):
        self.s.command({'op':'node','id':1,'label':'Full label','detail':' '.join(['long record']*25),'sha':'a'*64,'status':'status '*15})
        self.s.command({'op':'select','id':1});self.s.render();camera=self.s.info()['camera']
        self.s.command({'op':'wheel','delta':-1,'x':self.s.render().width-10,'y':8});self.assertEqual(camera,self.s.info()['camera']);self.assertEqual(self.s.info()['inspectorScroll'],0)
        self.s.command({'op':'key','key':'PageUp'});self.assertEqual(self.s.info()['inspectorScroll'],0)
        self.s.command({'op':'inspector-scroll','rows':30});before=self.s.snapshot();self.s.render();self.assertEqual(before,self.s.snapshot())
        self.assertEqual(self.s.info()['nodes'][0]['sha'],'a'*64)
    def test_modal_precedence_prevents_hidden_reader_commands(self):
        self.s.command({'op':'window','id':1,'text':'reader'});self.s.command({'op':'key','key':'F1'});before=self.s.snapshot()
        for key in ['F6','PageDown','PageUp']:self.s.command({'op':'key','key':key})
        self.assertEqual(before,self.s.snapshot())

    def test_measured_graph_spacing_at_distant_default_camera(self):
        self.s.command({'op':'camera','position':[0,8,162],'pitch':0,'yaw':0,'fov':64})
        for i in range(1,5):self.s.command({'op':'node','id':i,'label':'Complete node label with retained data','kind':'Action','status':'ready','sha':'a'*64})
        for i in range(2,5):self.s.command({'op':'edge','from':1,'to':i,'kind':'contains'})
        self.s.command({'op':'layout','mode':'layered','dimensions':3,'spacing':30});self.s.advance_to(900000)
        from collections import Counter
        frame=self.s.render();counts=Counter(w[3] for w in frame.words())
        # All four complete cards fit this authored view. Empty cells are owned too.
        for i in range(1,5):self.assertGreaterEqual(counts[0x10000000|i],40*7)
        info=self.s.info_complete();self.assertEqual(info['graph']['layoutProfile'],'measured');self.assertEqual(info['graph']['dimensions'],3)
        self.assertGreater(len({n['targetPosition'][2]for n in info['nodes']}),1)
        for node in info['nodes']:
            self.assertEqual(node['sha'],'a'*64);self.assertEqual(node['card']['width'],44);self.assertEqual(node['card']['height'],9)
            visible=''.join(chr(w[0])for w in frame.words()if w[3]==0x10000000|node['id'])
            for text in ['Complete node label with retained data','Action','ready']:self.assertIn(text,visible)
        saved=self.s.snapshot();self.assertEqual(self.s.render().bytes,frame.bytes);self.assertEqual(self.s.snapshot(),saved)
    def test_front_window_blank_cells_occlude_rear_document_ink(self):
        self.s.command({'op':'camera','position':[0,8,40],'pitch':0,'yaw':0})
        self.s.command({'op':'window','id':1,'title':'back','text':'Z'*120,'position':[0,8,0],'width':80,'height':30})
        self.s.command({'op':'window','id':2,'title':'front','text':'A','position':[0,8,0],'width':80,'height':30})
        self.s.command({'op':'window-action','id':1,'action':'read'})
        self.s.command({'op':'window-action','id':2,'action':'read'});self.s.advance_to(1000000)
        frame=self.s.render();owned=[w[0] for w in frame.words() if w[3]==0x20000002]
        self.assertTrue(owned);self.assertNotIn(ord('Z'),owned)
