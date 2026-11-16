"""Retained original pattern controls through the actual native scene."""
import struct
import sys
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


def checksum(data):
    struct.pack_into('<I', data, 20, zlib.crc32(data[24:]))
    return data


class MaterialPatternRetention(unittest.TestCase):
    def scene(self):
        scene = NativeScene(42)
        self.addCleanup(scene.close)
        scene.command({'op': 'resize', 'width': 100, 'height': 40})
        return scene

    def patterns(self, scene):
        return scene.info_complete()['materialPatterns']

    def test_original_defaults_partial_edits_owned_metadata_and_clear(self):
        scene = self.scene()
        self.assertEqual(self.patterns(scene), [])
        scene.command({'op': 'material', 'id': 5, 'pattern': {}})
        value = self.patterns(scene)[0]
        self.assertEqual(value['id'], 5)
        self.assertEqual(value['kind'], 'plasma')
        self.assertEqual((value['focusXQ8'], value['focusYQ8']), (12800, 4096))
        self.assertEqual((value['periodMs'], value['scaleQ8']), (5000, 6144))
        self.assertEqual((value['baseRgb'], value['inkRgb']), (0x11100e, 0xe2d9c9))
        self.assertEqual(len(value['palette']), 5)
        scene.command({'op': 'material', 'id': 5, 'pattern': {
            'kind': 'wave', 'focusMode': 'radial', 'palette': [0x123456, 0xffeecc]}})
        scene.command({'op': 'material', 'id': 5, 'alpha': .75})
        value = self.patterns(scene)[0]
        self.assertEqual(value['periodMs'], 5000)
        self.assertEqual(value['kind'], 'wave')
        self.assertEqual(value['palette'], [0x123456, 0xffeecc])
        value['palette'][0] = 0
        self.assertEqual(self.patterns(scene)[0]['palette'][0], 0x123456)
        scene.command({'op': 'material', 'id': 5, 'pattern': None})
        self.assertEqual(self.patterns(scene), [])
        scene.command({'op': 'material', 'id': 5, 'pattern': {}})
        self.assertEqual(self.patterns(scene)[0]['kind'], 'plasma')
        scene.command({'op': 'reset'})
        self.assertEqual(self.patterns(scene), [])

    def test_complete_controls_and_scheduled_snapshot_replay(self):
        scene = self.scene()
        authored = dict(kind='interference', focusMode='diagonal-band',
            focusXQ8=7283, focusYQ8=-9431, periodMs=731,
            saturationMilli=1731, brightnessMilli=387, speedFalloffMilli=743,
            saturationFalloffMilli=389, brightnessFalloffMilli=973,
            cellAspectMilli=2407, scaleQ8=4291, angleMilliDegrees=-14729,
            pivotXQ8=-8203, pivotYQ8=6347, rotationPeriodMs=1379,
            rotationMode='pendulum', swingMilliDegrees=27031, phase1024=-73,
            seed=98317, baseRgb=0x173945, inkRgb=0xceca73,
            palette=[0x123456, 0x789abc, 0xffeecc], gradientWrap='mirror',
            interpolation='linear', colorMode='rgb-sine', hueOffsetDegrees=-347,
            motion=False, originXCells=971, originYCells=-831,
            waveAmplitudeMilli=1873, reverse=True)
        scene.command({'op': 'material', 'id': 9, 'pattern': authored})
        self.assertEqual(self.patterns(scene), [{'id': 9, **authored}])
        scene.command({'op': 'schedule', 'id': 1, 'atUs': 500000,
            'command': {'op': 'material', 'id': 9, 'pattern': {'motion': True}}})
        saved = scene.snapshot()
        scene.advance_to(600000)
        final = scene.snapshot()
        self.assertTrue(self.patterns(scene)[0]['motion'])
        frame = scene.render().bytes
        self.assertEqual(scene.snapshot(), final)
        scene.restore(saved)
        scene.advance_to(600000)
        self.assertEqual(scene.snapshot(), final)
        self.assertEqual(scene.render().bytes, frame)

    def test_invalid_commands_batch_rollback_and_rechecksummed_footer(self):
        scene = self.scene()
        scene.command({'op': 'material', 'id': 9, 'pattern': {
            'kind': 'interference', 'focusMode': 'diagonal-band', 'focusXQ8': 7283}})
        before = scene.snapshot()
        for value in ({'kind': 'invented'}, {'unknown': 1}, {'motion': 1},
                      {'palette': []}, {'palette': [0xffffff] * 33},
                      {'baseRgb': 0x1000000}, {'periodMs': 49},
                      {'focusXQ8': 1.5}, [], True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                scene.command({'op': 'batch', 'commands': [
                    {'op': 'material', 'id': 9, 'pattern': {'kind': 'solid'}},
                    {'op': 'material', 'id': 9, 'pattern': value}]})
            self.assertEqual(scene.snapshot(), before)
        # Locate this unique fixed-layout record by its authored identity. No
        # dependence on other concerns' unreleased footer sizes is needed.
        prefix = struct.pack('<IIIII', 1, 0, 9, 4, 7283)
        self.assertEqual(before.count(prefix), 1)
        offset = before.index(prefix)
        for relative, value in ((0, 2), (4, 1), (8, 12)):
            changed = bytearray(before)
            struct.pack_into('<I', changed, offset + relative, value)
            with self.assertRaises(ValueError):
                scene.restore(checksum(changed))
            self.assertEqual(scene.snapshot(), before)

    def test_schema66_promotion_and_unknown_pending_field_rejection(self):
        scene = self.scene()
        def old_snapshot():
            old = bytearray(scene.snapshot()[:24 + 13578976])
            struct.pack_into('<I', old, 12, 0x20261066)
            struct.pack_into('<I', old, 28, 0x20261066)
            struct.pack_into('<I', old, 16, len(old) - 24)
            return checksum(old)
        scene.restore(old_snapshot())
        self.assertEqual(self.patterns(scene), [])
        scene.command({'op': 'schedule', 'id': 1, 'atUs': 500000,
            'command': {'op': 'batch', 'commands': [
                {'op': 'material', 'id': 9, 'pattern': {'kind': 'wave'}}]}})
        before = scene.snapshot()
        with self.assertRaises(ValueError):
            scene.restore(old_snapshot())
        self.assertEqual(scene.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
