"""Ordinary public camera gestures retain the actual off-centre world anchor."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy,gzip,hashlib,json,math,os,struct,subprocess,tempfile,unittest,zlib
from pathlib import Path
from native.bindings.python.nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1]
WIDTH,HEIGHT=120,48
def configure(scene,orthographic=False):
    for command in [{'op':'resize','width':WIDTH,'height':HEIGHT},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'prompt','active':False},{'op':'floor','visible':False},{'op':'camera','position':[4,7,64],'yaw':17,'pitch':-9,'roll':13,'fov':63,'span':100,'orthographic':orthographic}]:scene.command(command)
    scene.render()
def project(point,camera):
    y,p,r=[math.radians(camera[k]) for k in ('yaw','pitch','roll')];cy,sy,cp,sp,cr,sr=math.cos(y),math.sin(y),math.cos(p),math.sin(p),math.cos(r),math.sin(r)
    forward=[sy*cp,sp,-cy*cp];right0=[cy,0,sy];up0=[-sy*sp,cp,cy*sp];right=[right0[i]*cr+up0[i]*sr for i in range(3)];up=[up0[i]*cr-right0[i]*sr for i in range(3)]
    d=[point[i]-camera['position'][i] for i in range(3)];dot=lambda a,b:sum(x*y for x,y in zip(a,b));depth=dot(d,forward)
    scale=WIDTH*2/camera['span'] if camera['orthographic'] else HEIGHT*2/math.tan(math.radians(camera['fov'])/2)/depth
    return [WIDTH/2+dot(d,right)*scale/2,HEIGHT/2-dot(d,up)*scale/4]
class DefaultCameraAnchor(unittest.TestCase):
    def test_default_perspective_and_orthographic_anchor_stays_at_original_pixel(self):
        for orthographic in (False,True):
            with self.subTest(orthographic=orthographic),NativeScene(2030) as scene:
                configure(scene,orthographic);initial=scene.info()['camera'];x,y=25.3,18.4
                scene.command({'op':'pointer','phase':'down','button':0,'x':x,'y':y});camera=scene.info()['camera'];point=camera.get('grabbed')
                self.assertIsNotNone(point,'ordinary camera must capture the world anchor without original profile opt-in')
                self.assertEqual(camera['profile'],'default')
                for actual,expected in zip(project(point,camera),(x,y)):self.assertAlmostEqual(actual,expected,places=4)
                radius=math.dist(initial['position'],point);picked_pixel=(x,y)
                for dx,dy in ((7.5,2.1),(-3.2,1.3),(2,-4)):
                    x+=dx;y+=dy;scene.command({'op':'pointer','phase':'move','button':0,'x':x,'y':y});camera=scene.info()['camera']
                    self.assertEqual(camera['profile'],'default')
                    for actual,expected in zip(project(point,camera),picked_pixel):self.assertAlmostEqual(actual,expected,places=4)
                    self.assertEqual(camera['grabbed'],point)
                    self.assertAlmostEqual(math.dist(camera['position'],point),radius,places=4)
                scene.command({'op':'pointer','phase':'cancel','x':x,'y':y});held=scene.info()['camera'];self.assertIsNone(held.get('grabbed'))
                scene.command({'op':'pointer','phase':'move','x':x+12,'y':y+5});self.assertEqual(scene.info()['camera'],held)
                scene.command({'op':'camera','fov':145,'pitch':89.5});self.assertEqual(scene.info()['camera']['profile'],'default')
    def test_native_wasm_anchor_snapshot_and_flight_parity(self):
        requests=[]
        for ortho in (False,True):
            cs=[{'op':'resize','width':WIDTH,'height':HEIGHT},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'prompt','active':False},{'op':'floor','visible':False},{'op':'camera','position':[4,7,64],'yaw':17,'pitch':-9,'roll':13,'fov':63,'span':100,'orthographic':ortho}]
            requests.append({'id':str(ortho),'commands':cs,'drag':[{'op':'pointer','phase':'down','button':0,'x':25.3,'y':18.4},{'op':'pointer','phase':'move','button':0,'x':32.8,'y':20.5}]})
        with tempfile.TemporaryDirectory()as folder:
            p=Path(folder);(p/'in.json').write_text(json.dumps(requests));subprocess.run(['node',str(ROOT/'tests/spatial_contract_wasm.mjs'),str(p/'in.json'),str(p/'out.json')],check=True);results=json.loads((p/'out.json').read_text())
        for request,result in zip(requests,results):
            with NativeScene(2030)as scene:
                for c in request['commands']:scene.command(c)
                scene.render()
                for c in request['drag']:scene.command(c)
                self.assertEqual(scene.info(),result['info']);self.assertEqual(list(memoryview(scene.render().bytes).cast('I')),result['words'])
    def test_mid_drag_snapshot_replay_and_default_domains(self):
        with NativeScene(2030) as scene:
            configure(scene);scene.command({'op':'pointer','phase':'down','x':28,'y':20});self.assertIsNotNone(scene.info()['camera'].get('grabbed'))
            snapshot=scene.snapshot();move={'op':'pointer','phase':'move','x':36,'y':23};scene.command(move);expected=scene.info()['camera'];frame=scene.render().bytes
            scene.restore(snapshot);scene.command(move);self.assertEqual(scene.info()['camera'],expected);self.assertEqual(scene.render().bytes,frame)
            scene.command({'op':'camera','fov':145});self.assertIsNone(scene.info()['camera'].get('grabbed'));self.assertEqual(scene.info()['camera']['fov'],145)
    def test_primary_node_selection_and_middle_button_orbit_preserve_nodes(self):
        with NativeScene(2030) as scene:
            configure(scene);scene.command({'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'roll':0})
            scene.command({'op':'node','id':1,'label':'ANCHOR','position':[-14,0,0],'pinned':True,'showKind':False,'showStatus':False,'showSha':False});frame=scene.render();words=list(frame.words());index=next(i for i,w in enumerate(words) if w[3]==0x10000001);x,y=index%WIDTH+.4,index//WIDTH+.4;nodes=copy.deepcopy(scene.info()['nodes'])
            scene.command({'op':'pointer','phase':'down','button':1,'x':x,'y':y});point=scene.info()['camera'].get('grabbed');self.assertIsNotNone(point);self.assertEqual(scene.info()['selection'],0)
            scene.command({'op':'pointer','phase':'move','button':1,'x':x+5,'y':y+3});self.assertEqual(scene.info()['nodes'],nodes)
            scene.command({'op':'pointer','phase':'up','button':1,'x':x+5,'y':y+3});scene.render()
            index=next(i for i,w in enumerate(scene.render().words()) if w[3]==0x10000001);x,y=index%WIDTH,index//WIDTH
            scene.command({'op':'pointer','phase':'down','button':0,'x':x,'y':y});scene.command({'op':'pointer','phase':'up','button':0,'x':x,'y':y});self.assertEqual(scene.info()['selection'],1)
    def test_genuine87_migration_and_disabled_record_validation(self):
        fixture=ROOT/'tests/fixtures/camera-anchor-schema87';snapshot=gzip.decompress((fixture/'snapshot.gz').read_bytes());expected=gzip.decompress((fixture/'frame.gz').read_bytes());meta=json.loads((fixture/'PROVENANCE.json').read_text());layout=json.loads((fixture/'LAYOUT.json').read_text())
        self.assertEqual(hashlib.sha256(snapshot).hexdigest(),meta['snapshotSha256']);self.assertEqual(struct.unpack_from('<I',snapshot,12)[0],0x20261087)
        with NativeScene(2030) as scene:
            scene.restore(snapshot);self.assertEqual(scene.render().bytes,expected);self.assertEqual(struct.unpack_from('<I',scene.snapshot(),12)[0],scene.info()['contract']['snapshotSchema'])
            before=scene.snapshot();bad=bytearray(snapshot);struct.pack_into('<I',bad,24+layout['originalCamera']+layout['grabActive'],1);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
            with self.assertRaises(ValueError):scene.restore(bad)
            self.assertEqual(scene.snapshot(),before)
            scene.command({'op':'pointer','phase':'down','x':25,'y':18});active=scene.snapshot();self.assertEqual(struct.unpack_from('<I',active,12)[0],scene.info()['contract']['snapshotSchema'])
            bad=bytearray(active);struct.pack_into('<d',bad,24+layout['originalCamera']+layout['grabbed'],float('nan'));struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
            with self.assertRaises(ValueError):scene.restore(bad)
            self.assertEqual(scene.snapshot(),active)
    def test_original_camera_fit_uses_original_extents(self):
        points=[[-30,-15,-8],[30,15,8],[-10,25,3]]
        with NativeScene() as scene:
            scene.command({'op':'camera','profile':'original','position':[0,0,40],'yaw':0,'pitch':0,'fov':70})
            scene.command({'op':'camera-action','action':'view','name':'iso'})
            scene.command({'op':'camera-action','action':'fit','points':points,'width':120,'height':34,'padding':1.24})
            camera=scene.info()['camera'];target=[0,5,0];self.assertEqual(camera['target'],target)
            yaw,pitch=map(math.radians,(-28,-18));forward=[math.sin(yaw)*math.cos(pitch),math.sin(pitch),-math.cos(yaw)*math.cos(pitch)];right=[math.cos(yaw),0,math.sin(yaw)];up=[-math.sin(yaw)*math.sin(pitch),math.cos(pitch),math.cos(yaw)*math.sin(pitch)];tan=math.tan(math.radians(35));distance=8
            for point in points:
                d=[point[i]-target[i] for i in range(3)];dot=lambda v:sum(d[i]*v[i] for i in range(3));z=dot(forward);distance=max(distance,abs(dot(right))*1.24/tan-z,abs(dot(up))*1.24/(tan*34*2/120)-z,1-z)
            for a,b in zip(camera['position'],[target[i]-forward[i]*distance for i in range(3)]):self.assertAlmostEqual(a,b,places=5)
            saved=scene.snapshot()
            for patch in [{'points':[[0,float('nan'),0]]},{'padding':.9},{'width':0},{'points':[[1,2]]}]:
                with self.assertRaises(ValueError):scene.command({'op':'camera-action','action':'fit',**patch})
                self.assertEqual(scene.snapshot(),saved)
    def test_manual_camera_and_pan_preserve_original_flight_progress(self):
        for profile in ('default','original'):
            with self.subTest(profile=profile),NativeScene() as scene:
                configure(scene)
                if profile=='original':scene.command({'op':'camera','profile':'original'})
                scene.command({'op':'flight',**({'profile':'original'} if profile=='original' else {}),'steps':[{'kind':'cruise','durationMs':5000,'speed':10}]})
                scene.advance_to(1000000);before=scene.info()['camera'];scene.command({'op':'camera','yaw':before['yaw']+15,'position':[before['position'][0]+2,before['position'][1]+3,before['position'][2]]});moved=scene.info()['camera'];self.assertTrue(moved['flightActive'],'camera controls must not silently brake ongoing Oblique Flight')
                scene.advance_to(2000000);after=scene.info()['camera'];self.assertGreater(math.dist(after['position'],moved['position']),9.99)
                scene.render();scene.command({'op':'pointer','phase':'down','button':2,'x':3,'y':20});scene.command({'op':'pointer','phase':'move','button':2,'x':7,'y':22});self.assertTrue(scene.info()['camera']['flightActive']);scene.command({'op':'pointer','phase':'cancel','x':7,'y':22});scene.command({'op':'brake'});self.assertFalse(scene.info()['camera']['flightActive'])
    def test_pan_and_flight_keep_existing_ownership(self):
        with NativeScene(2030) as scene:
            configure(scene);before=scene.info()['camera'];scene.command({'op':'pointer','phase':'down','button':2,'x':25,'y':18});scene.command({'op':'pointer','phase':'move','button':2,'x':28,'y':19});after=scene.info()['camera'];self.assertNotEqual(before['position'],after['position']);self.assertEqual(before['yaw'],after['yaw']);self.assertEqual(after['profile'],'default')
            scene.command({'op':'pointer','phase':'cancel','x':28,'y':19});scene.command({'op':'flight','steps':[{'kind':'cruise','durationMs':5000,'speed':3}]});scene.advance_to(1000000);scene.render();scene.command({'op':'pointer','phase':'down','x':10,'y':10});scene.command({'op':'pointer','phase':'move','x':15,'y':12});self.assertTrue(scene.info()['camera']['flightActive']);self.assertIsNone(scene.info()['camera'].get('grabbed'))
if __name__=='__main__':unittest.main()
