"""Real public frames prove depth scale, draw order and hit ownership."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy,gzip,json,unittest
from pathlib import Path
from native.bindings.python.nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1]
def setup(s):
    for c in [{'op':'resize','width':120,'height':48},{'op':'environment','presentation':'canvas','stars':0},{'op':'prompt','active':False},{'op':'floor','visible':False},{'op':'camera','position':[0,0,90],'yaw':0,'pitch':0}]:s.command(c)
def bounds(frame,id):
    positions=[(i%frame.width,i//frame.width) for i,w in enumerate(frame.words()) if w[3]==0x10000000|id]
    return min(x for x,y in positions),min(y for x,y in positions),max(x for x,y in positions),max(y for x,y in positions)
class SpatialGraphRender(unittest.TestCase):
    def test_perspective_card_scale_and_orthographic_stability(self):
        with NativeScene() as s:
            setup(s);s.command({'op':'node','id':1,'label':'Depth sample','position':[0,0,0],'pinned':True});s.command({'op':'layout','profile':'source','dimensions':3});s.advance_to(800000)
            near=bounds(s.render(),1);s.command({'op':'camera','position':[0,0,180]});far=bounds(s.render(),1)
            self.assertGreater(near[2]-near[0],far[2]-far[0],'perspective nodes must scale with depth, not only project their centers')
            s.command({'op':'camera','orthographic':True,'span':150});a=bounds(s.render(),1);s.command({'op':'camera','position':[0,0,240]});self.assertEqual(bounds(s.render(),1),a)
    def test_orthographic_3d_honors_measured_full_card_fields(self):
        label='Complete contextual request name with all of its characters'
        with NativeScene() as s:
            setup(s)
            s.command({'op':'camera','orthographic':True,'span':150})
            s.command({'op':'node','id':1,'label':label,'kind':'Request','status':'waiting','detail':'Retained complete detail','sha':'a'*64,'shaPrefix':12,'position':[0,0,0],'pinned':True,'minColumns':70,'maxColumns':80,'padding':1})
            s.command({'op':'layout','dimensions':3});s.advance_to(800000)
            before=s.snapshot();record=copy.deepcopy(s.info()['nodes'][0]);frame=s.render()
            owned=''.join(chr(w[0])for w in frame.words()if w[3]==0x10000001)
            for text in [label,'Request','waiting','Retained complete detail','SHA '+'a'*12]:self.assertIn(text,owned)
            box=bounds(frame,1);self.assertEqual(box[2]-box[0]+1,record['card']['width']);self.assertEqual(box[3]-box[1]+1,record['card']['height']);self.assertEqual(record['card']['width'],70)
            self.assertEqual(s.info()['nodes'][0],record);self.assertEqual(record['sha'],'a'*64);self.assertEqual(s.snapshot(),before)
            s.command({'op':'camera','position':[0,0,240]});self.assertEqual(bounds(s.render(),1),box)
            s.restore(before);self.assertEqual(s.render().bytes,frame.bytes)
    def test_orthographic_3d_full_cards_keep_depth_hit_order(self):
        frames=[]
        for order in ((1,2),(2,1)):
            with self.subTest(order=order),NativeScene() as s:
                setup(s);s.command({'op':'camera','orthographic':True,'span':150})
                for identity in order:s.command({'op':'node','id':identity,'label':'NEAR full measured card'if identity==1 else'FAR full measured card','position':[0,0,30 if identity==1 else-30],'pinned':True,'minColumns':70,'maxColumns':80,'showKind':False,'showDetail':False,'showSha':False,'showStatus':False})
                s.command({'op':'layout','dimensions':3});s.advance_to(800000)
                frame=s.render();frames.append(frame.bytes);box=bounds(frame,1)
                self.assertEqual(box[2]-box[0]+1,70)
                self.assertEqual(list(frame.words())[24*120+60][3],0x10000001)
                positions={n['id']:n['position']for n in s.info()['nodes']};self.assertEqual(positions,{1:[0,0,30],2:[0,0,-30]})
                s.command({'op':'pointer','phase':'down','x':60,'y':24});s.command({'op':'pointer','phase':'up','x':60,'y':24});self.assertEqual(s.info()['selection'],1)
        self.assertEqual(frames[0],frames[1])
    def test_measured_perspective_full_cards_keep_depth_and_hit_order(self):
        frames=[]
        for order in ((1,2),(2,1)):
            with self.subTest(order=order),NativeScene() as s:
                setup(s)
                for identity in order:s.command({'op':'node','id':identity,'label':'NEAR complete perspective label'if identity==1 else'FAR complete perspective label','position':[0,0,30 if identity==1 else-30],'pinned':True,'minColumns':70,'maxColumns':80,'showKind':False,'showDetail':False,'showSha':False,'showStatus':False})
                s.command({'op':'layout','dimensions':3});s.advance_to(800000)
                info=s.info_complete();self.assertEqual(info['graph']['layoutProfile'],'measured');self.assertEqual({n['id']:n['position']for n in info['nodes']},{1:[0,0,30],2:[0,0,-30]})
                frame=s.render();frames.append(frame.bytes);box=bounds(frame,1);self.assertEqual(box[2]-box[0]+1,70)
                self.assertIn('NEAR complete perspective label',''.join(chr(w[0])for w in frame.words()if w[3]==0x10000001));self.assertEqual(frame.words()[24*120+60][3],0x10000001)
                saved=s.snapshot();self.assertEqual(s.render().bytes,frame.bytes);self.assertEqual(saved,s.snapshot())
                s.command({'op':'pointer','phase':'down','x':60,'y':24});s.command({'op':'pointer','phase':'up','x':60,'y':24});self.assertEqual(s.info()['selection'],1)
        self.assertEqual(frames[0],frames[1])
    def test_overlapping_near_owner_wins_reversed_insertion(self):
        frames=[]
        for order in ((1,2),(2,1)):
            with NativeScene() as s:
                setup(s)
                for id in order:s.command({'op':'node','id':id,'label':'NEAR' if id==1 else 'FAR','position':[0,0,30 if id==1 else -30],'pinned':True})
                s.command({'op':'layout','dimensions':3});s.advance_to(800000);frame=s.render();frames.append(frame.bytes)
                center=list(frame.words())[24*120+60];self.assertEqual(center[3],0x10000001)
                s.command({'op':'pointer','phase':'down','x':60,'y':24});s.command({'op':'pointer','phase':'up','x':60,'y':24});self.assertEqual(s.info()['selection'],1)
        self.assertEqual(frames[0],frames[1])
if __name__=='__main__':unittest.main()
