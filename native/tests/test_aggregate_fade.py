"""Real render oracles for receiver-owned aggregate retention fading."""
import unittest
import test_surface_geometry as geometry
from nocturne_native import NativeScene


def author(scene, mesh, count=8, fade=500, retention=1000):
    scene.command({'op':'environment','stars':0,'style':'solid'})
    policy=dict(maxIndividual=0,maxTiles=4,overflow='merge-to-field',
                reentrainWindSpeed=0,retentionMs=retention,fadeMs=fade)
    helper=geometry.SurfaceGeometry();helper.scene=scene
    if mesh:
        scene.command({'op':'floor','enabled':False})
        helper.surface(renderVisible=False,**policy)
        helper.mesh([helper.wall()])
        scene.command({'op':'camera','position':[30,0,0],'yaw':-90,'pitch':0})
        patch=dict(position=[1,0,0],velocity=[-240,0,0],colliders={'surfaces':[1]})
    else:
        scene.command({'op':'floor','enabled':True,'visible':False,**policy})
        scene.command({'op':'camera','position':[0,15,15],'yaw':0,'pitch':-45})
        patch=dict(position=[0,1,0],velocity=[0,-240,0],colliders=None)
    helper.particle(effect='weather/snowglobe',count=count,deposit=True,**patch)
    scene.advance_to(8333)
    assert scene.info_complete()['particles']['aggregated']==count


class AggregateFade(unittest.TestCase):
    def test_half_fade_matches_independent_half_count_on_each_receiver(self):
        for mesh in (False,True):
            with self.subTest(mesh=mesh),NativeScene() as actual,NativeScene() as reference:
                author(actual,mesh);author(reference,mesh,count=4,fade=0)
                actual.advance_to(758333);reference.advance_to(758333)
                before=actual.snapshot()
                self.assertEqual(actual.render().bytes,reference.render().bytes)
                self.assertEqual(actual.info_complete()['particles']['aggregated'],8)
                self.assertEqual(actual.snapshot(),before)
                visible=actual.render().bytes
                actual.command({'op':'clear','scope':'deposits'})
                self.assertNotEqual(visible,actual.render().bytes,'Fade equality must compare visible coverage')

    def test_pre_fade_zero_fade_and_infinite_retention_keep_legacy_coverage(self):
        for mesh in (False,True):
            for fade,retention,time in ((500,1000,258333),(0,1000,758333),(500,0,1758333)):
                with self.subTest(mesh=mesh,fade=fade,retention=retention),NativeScene() as actual,NativeScene() as reference:
                    author(actual,mesh,fade=fade,retention=retention)
                    author(reference,mesh,fade=0,retention=retention)
                    actual.advance_to(time);reference.advance_to(time)
                    self.assertEqual(actual.render().bytes,reference.render().bytes)

    def test_expiry_and_partition_replay_preserve_accounting(self):
        for mesh in (False,True):
            with self.subTest(mesh=mesh),NativeScene() as scene:
                author(scene,mesh);start=scene.snapshot()
                scene.advance_to(758333);expected=scene.snapshot();frame=scene.render().bytes
                scene.restore(start)
                for time in (108333,508333,758333):scene.advance_to(time);scene.render();scene.info_complete()
                self.assertEqual(scene.snapshot(),expected);self.assertEqual(scene.render().bytes,frame)
                scene.advance_to(1008333)
                self.assertEqual(scene.info_complete()['particles']['aggregated'],0)
                self.assertEqual(scene.info_complete()['particles']['born'],8)

    def test_invalid_receiver_fade_rejects_without_loss(self):
        for mesh in (False,True):
            with self.subTest(mesh=mesh),NativeScene() as scene:
                author(scene,mesh);before=scene.snapshot()
                command={'op':'surface','id':1} if mesh else {'op':'floor'}
                with self.assertRaises(ValueError):scene.command({**command,'retentionMs':100,'fadeMs':101})
                self.assertEqual(scene.snapshot(),before)
