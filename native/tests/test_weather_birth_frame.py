"""Independent right-handed birth transforms and immutable old-snapshot migration."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import gzip
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


class WeatherBirthFrame(unittest.TestCase):
    def command(self, orientation=None):
        value = dict(op='emitter', id=1, effect='weather/autumn-drift',
                     seed=51, count=16, runningTimeMs=0, position=[1, 10, 2],
                     shape='line', extent=[4, 0, 0], velocity=[2, 0, 0],
                     spread=[0, 0, 0], gravity=[0, 0, 0], wind=[0, 0, 0],
                     windVariation=[0, 0, 0], drag=0, lift=0, flutterAmount=0,
                     collision=False, deposit=False)
        if orientation is not None:
            value['birthOrientation'] = orientation
        return value

    def testQuarterTurnRotatesBirthVolumeAndVelocityAroundWorldOriginOfEmitter(self):
        with NativeScene(51) as original, NativeScene(51) as rotated:
            original.command(self.command())
            rotated.command(self.command([0, 0, 90]))
            for scene in (original, rotated): scene.advance_to(8333)
            self.assertEqual(len(rotated.particles()), 16)
            for a, b in zip(original.particles(), rotated.particles()):
                self.assertEqual(a[:3], b[:3])
                # Independent Rz(+90): x -> y, y -> -x, z unchanged.
                self.assertAlmostEqual(b[3], 65536, delta=2)
                self.assertAlmostEqual(b[4]-10*65536, a[3]-65536, delta=2)
                self.assertAlmostEqual(b[5], a[5], delta=2)
                self.assertEqual(b[6:9], (0, 2*65536, 0))

    def testRotationOrderIsXThenYThenZ(self):
        command = self.command([90, 90, 90])
        command.update(shape='point', extent=[0, 0, 0], velocity=[0, 1, 0])
        with NativeScene() as scene:
            scene.command(command);scene.advance_to(8333)
            # +Y -> +Z by Rx; +Z -> +X by Ry; +X -> +Y by Rz.
            self.assertEqual(scene.particles()[0][6:9], (0, 65536, 0))

    def testNestedOrientationCompilesToTheSameNativeFrame(self):
        flat = self.command([0, 90, 0])
        nested = dict(op='weather-author', schema='nocturne.weather-authoring/v1',
                      id=1, effect=flat['effect'],
                      emission={k: flat[k] for k in ('seed','count','runningTimeMs')},
                      birth={k: flat[k] for k in ('shape','position','extent','velocity','spread')},
                      forces={k: flat[k] for k in ('gravity','wind','windVariation','drag','lift','flutterAmount')},
                      collision=dict(enabled=False, deposit=False))
        nested['birth']['orientation'] = flat['birthOrientation']
        with NativeScene(51) as a, NativeScene(51) as b:
            a.command(flat);b.command(nested)
            self.assertEqual(a.snapshot(), b.snapshot())
            a.advance_to(500000);b.advance_to(500000)
            self.assertEqual(a.snapshot(), b.snapshot())

    def testZeroOrientationRetainsExistingStateAndMetadata(self):
        with NativeScene() as a, NativeScene() as b:
            a.command(self.command());b.command(self.command([0,0,0]))
            self.assertEqual(a.snapshot(), b.snapshot())
            self.assertEqual(a.info()['emitters'][0]['birthOrientation'], [0,0,0])

    def testInvalidFramesRejectAtomicallyAndDoNotPoisonNextEmitter(self):
        for bad in ([0,0], [0,0,3601], [0,'90',0], [0,None,0]):
            with self.subTest(bad=bad), NativeScene() as scene:
                before=scene.snapshot()
                with self.assertRaises(ValueError): scene.command(self.command(bad))
                self.assertEqual(scene.snapshot(), before)
                scene.command(self.command())
                self.assertEqual(scene.info()['emitters'][0]['birthOrientation'], [0,0,0])

    def testClearAndReuseResetsTheBirthFrame(self):
        with NativeScene() as scene:
            scene.command(self.command([0,0,90]))
            scene.command(dict(op='clear-instance',id=1))
            scene.command(self.command())
            self.assertEqual(scene.info()['emitters'][0]['birthOrientation'],[0,0,0])

    def testClearWeatherLeavesARestorableEmptyEmitterState(self):
        with NativeScene() as scene:
            scene.command(self.command([0,0,90]))
            scene.command(dict(op='clear',scope='weather'))
            saved=scene.snapshot()
            scene.restore(saved)
            self.assertEqual(saved,scene.snapshot())

    def testFrameSnapshotReplayPreservesBirthsAndRenderPurity(self):
        command=self.command([0,0,90]);command['runningTimeMs']=1000
        with NativeScene() as a, NativeScene() as b:
            a.command(command);a.advance_to(500000)
            saved=a.snapshot();a.render();a.info_complete()
            self.assertEqual(saved,a.snapshot())
            b.restore(saved)
            for scene in (a,b):scene.advance_to(1000000)
            self.assertEqual(a.snapshot(),b.snapshot())
            self.assertEqual(a.render().bytes,b.render().bytes)

    def testOldSchema06LoadsWithoutModifyingInputAndDefaultsToIdentity(self):
        payload=gzip.decompress((ROOT/'tests/fixtures/schema-20261006-weather-birth.snapshot.gz').read_bytes())
        with NativeScene() as scene:
            scene.restore(payload)
            self.assertEqual(scene.info()['emitters'][0]['birthOrientation'],[0,0,0])
            saved=scene.snapshot()
            self.assertEqual(int.from_bytes(saved[12:16],'little'),current_schema())
            self.assertEqual(saved[24:28],payload[24:28])
            self.assertEqual(saved[32:24+4642648],payload[32:])
            self.assertEqual(len(saved),snapshot_size(scene))

    def testForgedNonfiniteFrameSnapshotRejectsDespiteValidChecksum(self):
        with NativeScene() as scene:
            scene.command(self.command([0,0,90]))
            before=scene.snapshot();bad=bytearray(before)
            struct.pack_into('<d',bad,24+4642648,float('nan'))
            struct.pack_into('<I',bad,20,zlib.crc32(bad[24:])&0xffffffff)
            with self.assertRaises(ValueError):scene.restore(bad)
            self.assertEqual(scene.snapshot(),before)
