"""Native indexed import, independent transform and actual collider acceptance."""
import copy
import gzip
import struct
import zlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

class ModelImport(unittest.TestCase):
    def model(self,**changes):
        c=dict(op='model-import',schema='nocturne.model/v1',units='meters',
               coordinates='right-handed-y-up',vertices=[[0,0,0],[2,0,0],[0,2,0]],
               materials=[dict(color=0x123456,alpha=.75)],
               triangles=[dict(indices=[0,1,2],material=0)])
        c.update(changes);return c

    def testIndependentTransformMatchesAuthoredMeshExactly(self):
        with NativeScene(17) as imported,NativeScene(17) as authored:
            imported.command(self.model(units='centimeters',transform=dict(position=[1,2,3],orientation=[0,0,90],scale=[100,200,300])))
            authored.command(dict(op='mesh',triangles=[dict(a=[1,2,3],b=[1,4,3],c=[-3,2,3],color=0x123456,alpha=.75)]))
            self.assertEqual(imported.snapshot(),authored.snapshot())
            self.assertEqual(imported.render().bytes,authored.render().bytes)

    def testImportedWallParticipatesInActualSweptCollision(self):
        with NativeScene() as scene:
            scene.command(dict(op='floor',enabled=False))
            scene.command(dict(op='surface',id=1,restitution=1,friction=0))
            scene.command(self.model(vertices=[[0,-10,-10],[0,10,-10],[0,0,10]],triangles=[dict(indices=[0,1,2],material=0,surfaceId=1)]))
            scene.command(dict(op='emitter',id=1,count=1,runningTimeMs=0,shape='point',position=[1,0,0],velocity=[-240,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterAmount=0,collision=True,deposit=False,colliders=dict(surfaces=[1])))
            scene.advance_to(8333);p=scene.particles()[0]
            self.assertAlmostEqual(p[3]/65536,1.001,delta=2/65536)
            self.assertEqual(p[6:9],(240*65536,0,0))

    def testMaterialsAreResolvedPerTriangleAndCallerInputIsUnmodified(self):
        with NativeScene() as a,NativeScene() as b:
            model=self.model(materials=[dict(color=1,alpha=.2),dict(color=2,alpha=.8)],triangles=[dict(indices=[0,1,2],material=1)])
            original=copy.deepcopy(model);a.command(model)
            b.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[2,0,0],c=[0,2,0],color=2,alpha=.8)]))
            self.assertEqual(model,original);self.assertEqual(a.snapshot(),b.snapshot())

    def testRejectsUnknownHostileReferencesAndMalformedDocumentsAtomically(self):
        patches=[dict(uri='https://example.invalid/model'),dict(script='run'),dict(schema='other'),dict(units='feet'),dict(coordinates='left-handed'),dict(vertices=[]),dict(vertices=[[0,0],[2,0,0],[0,2,0]]),dict(vertices=[[0,0,0],[0,0,0],[0,2,0]]),dict(vertices=[[16001,0,0],[2,0,0],[0,2,0]]),dict(materials=[]),dict(materials=[dict(color=0x1000000)]),dict(materials=[dict(texture='../secret')]),dict(triangles=[dict(indices=[0,1,3],material=0)]),dict(triangles=[dict(indices=[0,1,2],material=1)]),dict(triangles=[dict(indices=[0,1,2],material=0,surfaceId=1)]),dict(triangles=[dict(indices=[0,1,2,0],material=0)]),dict(triangles=[dict(indices=[0,.5,2],material=0)]),dict(transform=dict(scale=[0,1,1])),dict(transform=dict(position=[16000,0,0])),dict(transform=dict(matrix=[]))]
        with NativeScene() as scene:
            scene.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[1,0,0],c=[0,1,0])]))
            before=scene.snapshot()
            for patch in patches:
                with self.subTest(patch=patch):
                    with self.assertRaises(ValueError):scene.command(self.model(**patch))
                    self.assertEqual(before,scene.snapshot())
            bad=self.model();bad['vertices'][0][0]=float('nan')
            with self.assertRaises(ValueError):scene.command(bad)
            self.assertEqual(before,scene.snapshot())

    def testOversizedPoolsRejectWithoutMutation(self):
        with NativeScene() as scene:
            before=scene.snapshot()
            for patch in (dict(vertices=[[0,0,0]]*1025),dict(materials=[dict(color=1)]*33),dict(triangles=[dict(indices=[0,1,2],material=0)]*257)):
                with self.assertRaises(ValueError):scene.command(self.model(**patch))
                self.assertEqual(before,scene.snapshot())

    def testSnapshotReplayAndRenderPurity(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(self.model());saved=a.snapshot();a.render();a.info_complete()
            self.assertEqual(saved,a.snapshot());b.restore(saved)
            self.assertEqual(a.render().bytes,b.render().bytes)
            a.advance_to(100000);b.advance_to(100000)
            self.assertEqual(a.snapshot(),b.snapshot())

    def testXYZRotationOrderUsesRightHandedIndependentOracle(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(self.model(transform=dict(orientation=[90,90,90])))
            b.command(dict(op='mesh',triangles=[dict(a=[0,0,0],b=[0,0,-2],c=[0,2,0],color=0x123456,alpha=.75)]))
            self.assertEqual(a.snapshot(),b.snapshot())

    def testMaximumPoolsAndEmptyTriangleReplacementAreBounded(self):
        with NativeScene() as scene:
            scene.command(self.model(vertices=[[0,0,0],[2,0,0],[0,2,0]]+[[0,0,0]]*1021,
                materials=[dict(color=i) for i in range(32)],
                triangles=[dict(indices=[0,1,2],material=i%32) for i in range(256)]))
            self.assertEqual(scene.info()['geometry']['triangles'],256)
            scene.command(self.model(triangles=[]))
            self.assertEqual(scene.info()['geometry']['triangles'],0)

    def testRequiredDeclarationsAndRawNonfiniteNumbersReject(self):
        with NativeScene() as scene:
            before=scene.snapshot()
            for key in ('schema','units','coordinates','vertices','materials','triangles'):
                model=self.model();del model[key]
                with self.assertRaises(ValueError):scene.command(model)
                self.assertEqual(before,scene.snapshot())
            with self.assertRaises(ValueError):scene.command_raw(b'{"op":"model-import","schema":"nocturne.model/v1","units":"meters","coordinates":"right-handed-y-up","vertices":[[1e309,0,0],[2,0,0],[0,2,0]],"materials":[{"color":1}],"triangles":[{"indices":[0,1,2],"material":0}]}')
            self.assertEqual(before,scene.snapshot())

    def testSchema06GeometryPrefixMigratesBeforeBirthFrames(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(dict(op='surface',id=1,restitution=.5))
            a.command(self.model(triangles=[dict(indices=[0,1,2],material=0,surfaceId=1)]))
            before=a.snapshot()
            old=bytearray(before[:24+4642648])
            struct.pack_into('<I',old,12,0x20261006)
            struct.pack_into('<I',old,16,4642648)
            struct.pack_into('<I',old,28,0x20261006)
            struct.pack_into('<I',old,20,zlib.crc32(old[24:]))
            b.restore(old)
            self.assertEqual(before,b.snapshot())

    def testSchema06RetainedIntentAndGeometryMigrateTogether(self):
        fixture=Path(__file__).parent/'fixtures/schema-20261004-intent-action.snapshot.gz'
        with NativeScene() as a,NativeScene() as b:
            a.restore(gzip.decompress(fixture.read_bytes()))
            a.command(dict(op='surface',id=1,restitution=.5))
            a.command(self.model(triangles=[dict(indices=[0,1,2],material=0,surfaceId=1)]))
            before=a.snapshot();old=bytearray(before[:24+4642648])
            struct.pack_into('<I',old,12,0x20261006)
            struct.pack_into('<I',old,16,4642648)
            struct.pack_into('<I',old,28,0x20261006)
            struct.pack_into('<I',old,20,zlib.crc32(old[24:]))
            b.restore(old)
            self.assertEqual(before,b.snapshot())
