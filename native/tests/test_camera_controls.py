"""Physical camera rigs: actual public native state and independent geometry."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy, math, unittest
from native.bindings.python.nocturne_native import NativeScene
from native.tests.test_camera_anchor_default import configure, project

def rotate(v, axis, degrees):
    a=math.radians(degrees);c,s=math.cos(a),math.sin(a);x,y,z=v
    return ([x,c*y-s*z,s*y+c*z] if axis=='x' else [c*x+s*z,y,-s*x+c*z] if axis=='y' else [c*x-s*y,s*x+c*y,z])

def drag(scene, dx, dy=0):
    scene.render();scene.command({'op':'pointer','phase':'down','button':1,'x':25.3,'y':18.4})
    scene.command({'op':'pointer','phase':'move','button':1,'x':25.3+dx,'y':18.4+dy})

def mapping(action,sensitivity=1):
    return {'x':{'action':action,'sensitivity':sensitivity,'invert':False,'enabled':True},'y':{'enabled':False},'z':{'enabled':False}}

class CameraControls(unittest.TestCase):
    def vectorEqual(self,a,b):
        for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=5)
    def test_all_world_orbit_axes_keep_one_world_pick_and_original_pixel(self):
        for ortho in (False,True):
            for axis in 'xyz':
                with self.subTest(ortho=ortho,axis=axis),NativeScene() as scene:
                    configure(scene,ortho);scene.command({'op':'camera-controls','rig':'orbit','inputAxes':mapping('orbit-'+axis)})
                    scene.render();before=scene.info()['camera'];scene.command({'op':'pointer','phase':'down','button':1,'x':25.3,'y':18.4});anchor=scene.info()['camera']['grabbed']
                    scene.command({'op':'pointer','phase':'move','button':1,'x':32.3,'y':18.4});after=scene.info()['camera']
                    expected=rotate([before['position'][i]-anchor[i] for i in range(3)],axis,7)
                    self.vectorEqual(after['position'],[expected[i]+anchor[i] for i in range(3)])
                    self.vectorEqual(project(anchor,after),project(anchor,before));self.assertEqual(after['grabbed'],anchor)
                    self.assertAlmostEqual(math.dist(before['position'],anchor),math.dist(after['position'],anchor),places=5)
    def test_head_keeps_position_and_rolls_without_orbiting(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera','yaw':0,'pitch':0,'roll':0})
            scene.command({'op':'camera-controls','rig':'head','inputAxes':mapping('look-z')});before=scene.info()['camera'];drag(scene,17)
            after=scene.info()['camera'];self.assertEqual(after['position'],before['position']);self.assertAlmostEqual(after['roll'],17,places=5)
    def test_dolly_translation_does_not_rotate_mount(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera','yaw':0,'pitch':0,'roll':0});scene.command({'op':'camera-controls','rig':'dolly','inputAxes':mapping('pan-z')});before=scene.info()['camera'];drag(scene,6)
            after=scene.info()['camera'];self.vectorEqual(after['position'],[before['position'][0],before['position'][1],before['position'][2]-6]);self.vectorEqual([after[k] for k in ('yaw','pitch','roll')],[0,0,0])
    def test_crane_boom_rotates_around_pivot_without_mount_rotation(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera','yaw':0,'pitch':0,'roll':0});scene.command({'op':'camera-controls','rig':'crane','crane':{'pivot':[3,4,5],'boom':[0,0,60]},'inputAxes':mapping('orbit-y',10)})
            drag(scene,9);camera=scene.info()['camera'];self.vectorEqual(camera['position'],[63,4,5]);self.vectorEqual([camera[k] for k in ('yaw','pitch','roll')],[0,0,0])
    def test_follow_tracks_moving_node_and_preserves_authored_offset(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'node','id':31,'label':'moving target','position':[0,0,0]})
            scene.command({'op':'camera-controls','rig':'follow','follow':{'target':{'kind':'node','id':31},'offset':[0,3,40],'track':True}})
            self.vectorEqual(scene.info()['camera']['position'],[0,3,40]);scene.command({'op':'node','id':31,'position':[9,4,-2]})
            after=scene.info()['camera'];self.vectorEqual(after['position'],[9,7,38]);self.assertAlmostEqual(after['yaw'],0,places=5)
            self.assertAlmostEqual(after['pitch'],-math.degrees(math.atan2(3,40)),places=5)
    def test_follow_orbit_after_target_motion_uses_current_target(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'node','id':31,'position':[0,0,0]})
            scene.command({'op':'camera-controls','rig':'follow','follow':{'target':{'kind':'node','id':31},'offset':[0,3,40]},'inputAxes':mapping('orbit-y')})
            scene.command({'op':'node','id':31,'position':[9,4,-2]});scene.command({'op':'camera-input','delta':[90,0,0]})
            self.vectorEqual(scene.info()['camera']['position'],[49,7,-2])
            scene.command({'op':'node','id':31,'position':[12,8,-7]});self.vectorEqual(scene.info()['camera']['position'],[52,11,-7])
    def test_follow_reconfiguration_and_rig_switch_do_not_teleport(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'node','id':31,'position':[0,0,0]})
            scene.command({'op':'camera-controls','rig':'follow','follow':{'target':{'kind':'node','id':31},'offset':[0,3,40]}})
            scene.command({'op':'node','id':31,'position':[9,4,-2]});expected=scene.info()['camera']['position']
            scene.command({'op':'camera-controls','rig':'follow'});self.vectorEqual(scene.info()['camera']['position'],expected)
            scene.command({'op':'node','id':31,'position':[12,8,-7]});expected=scene.info()['camera']
            scene.command({'op':'camera-controls','rig':'head'});after=scene.info()['camera'];self.vectorEqual(after['position'],expected['position']);self.vectorEqual([after[k] for k in ('yaw','pitch','roll')],[expected[k] for k in ('yaw','pitch','roll')])
    def test_spacecraft_has_independent_head_and_carrier(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'roll':0})
            scene.command({'op':'camera-controls','rig':'spacecraft','head':{'position':[2,3,4],'rotation':[0,30,0]},'inputAxes':mapping('look-z')})
            before=scene.info()['camera'];self.vectorEqual(before['position'],[2,3,56]);self.assertAlmostEqual(before['yaw'],30,places=5)
            drag(scene,12);self.vectorEqual(scene.info()['camera']['position'],before['position'])
            scene.command({'op':'camera-controls','head':{'position':[0,0,0],'rotation':[0,0,0]}})
            after=scene.info()['camera'];self.vectorEqual(after['position'],[0,0,60]);self.vectorEqual([after[k] for k in ('yaw','pitch','roll')],[0,0,0])
    def test_axis_disabled_inverted_and_snapshot_replayed(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera-controls','rig':'head','inputAxes':mapping('look-z',2)})
            scene.command({'op':'camera-controls','inputAxes':{'x':{'enabled':False}}});before=scene.info()['camera'];drag(scene,9);self.assertEqual(before['position'],scene.info()['camera']['position']);self.assertEqual(before['roll'],scene.info()['camera']['roll'])
            scene.command({'op':'pointer','phase':'cancel','x':34.3,'y':18.4});scene.command({'op':'camera-controls','inputAxes':{'x':{'enabled':True,'invert':True}}});scene.render();scene.command({'op':'pointer','phase':'down','button':1,'x':25.3,'y':18.4});snapshot=scene.snapshot();command={'op':'pointer','phase':'move','button':1,'x':32.3,'y':18.4};scene.command(command);expected=scene.info()['camera'];scene.restore(snapshot);scene.command(command);self.assertEqual(scene.info()['camera'],expected)
    def test_flight_continues_through_head_and_body_controls(self):
        for rig in ('head','dolly','spacecraft'):
            with self.subTest(rig=rig),NativeScene() as scene:
                configure(scene);scene.command({'op':'camera','profile':'original','position':[0,0,60],'yaw':0,'pitch':0,'roll':0});scene.command({'op':'flight','profile':'original','cruise':{'speed':10}});scene.advance_to(1000000)
                scene.command({'op':'camera-controls','rig':rig});drag(scene,7,2);before=scene.info()['camera'];self.assertTrue(before['flightActive']);scene.advance_to(2000000);after=scene.info()['camera'];self.assertTrue(after['flightActive']);self.assertGreater(math.dist(before['position'],after['position']),9.99)
    def test_explicit_input_pole_and_spacecraft_body_head_independence(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'roll':0})
            scene.command({'op':'camera-controls','rig':'orbit','anchor':[0,0,0],'inputAxes':mapping('orbit-x')})
            scene.command({'op':'camera-input','delta':[90,0,0]});pole=scene.info()['camera'];self.vectorEqual(pole['position'],[0,-60,0]);self.assertAlmostEqual(pole['pitch'],90,places=6)
            scene.command({'op':'camera-input','delta':[-90,0,0]});self.vectorEqual(scene.info()['camera']['position'],[0,0,60])
            scene.command({'op':'camera-controls','rig':'spacecraft','inputTarget':'head','inputAxes':mapping('look-z')});scene.command({'op':'camera-input','delta':[20,0,0]})
            self.assertAlmostEqual(scene.info()['camera']['controls']['head']['rotation'][2],20,places=6)
            scene.command({'op':'camera-controls','inputTarget':'body'});scene.command({'op':'camera-input','delta':[15,0,0]})
            self.assertAlmostEqual(scene.info()['camera']['controls']['head']['rotation'][2],20,places=6)
            scene.command({'op':'camera-controls','head':{'rotation':[0,0,0]}});self.assertAlmostEqual(scene.info()['camera']['roll'],15,places=6)
    def test_invalid_controls_are_atomic(self):
        with NativeScene() as scene:
            configure(scene);scene.command({'op':'camera-controls','rig':'orbit'});before=scene.snapshot()
            for patch in ({'rig':'foley'},{'inputAxes':{'x':{'action':'slide'}}},{'inputAxes':{'x':{'sensitivity':-1}}},{'inputAxes':{'x':{'invert':1}}},{'inputAxes':None},{'head':{'rotation':[1,2]}},{'crane':{'pivot':[0,0,float('nan')]}},{'follow':{'target':{'kind':'node','id':65535}}},{'anchor':[0,0,float('inf')]},{'enabled':False,'rig':'head'}):
                with self.subTest(patch=patch):
                    with self.assertRaises(ValueError):scene.command({'op':'camera-controls',**patch})
                    self.assertEqual(scene.snapshot(),before)
if __name__=='__main__':unittest.main()
