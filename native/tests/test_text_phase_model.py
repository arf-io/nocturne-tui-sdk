"""Retained source phases through actual public native interfaces; no mocks."""
import struct
import sys
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

SCHEMA66_BYTES = 13_578_976
MODE_OFFSET = 24 + SCHEMA66_BYTES


def checksum(data):
    struct.pack_into('<I', data, 20, zlib.crc32(data[24:]))
    return data


class TextPhaseModel(unittest.TestCase):
    def scene(self, model='source', effect='text/glyph-fall', phase='show', text='A\u0301B'):
        scene = NativeScene(42)
        self.addCleanup(scene.close)
        scene.command({'op': 'resize', 'width': 100, 'height': 40})
        scene.command({'op': 'environment', 'stars': 0})
        scene.command({'op': 'prompt', 'active': False})
        command = {'op': 'text', 'id': 1, 'effect': effect, 'phase': phase,
                   'text': text, 'x': 20, 'y': 16, 'width': 80, 'seed': 42,
                   'durationMs': 1000, 'staggerMs': 0, 'jitterMs': 0,
                   'delayMs': 100, 'variation': 0, 'easing': 'linear'}
        if model is not None:
            command['phaseModel'] = model
        scene.command(command)
        return scene

    def row(self, scene, identity=1):
        return next(row for row in scene.info_complete()['textRuns'] if row['id'] == identity)

    def test_source_delay_terminal_and_cluster_frame_readback(self):
        for effect in ('text/glyph-fall', 'text/ash-type'):
            for phase in ('show', 'hide'):
                with self.subTest(effect=effect, phase=phase):
                    scene = self.scene(effect=effect, phase=phase, text='N')
                    for time_us, alpha in ((0, 0 if phase == 'show' else 1_000_000),
                                           (350000, 750000), (700000, 400000),
                                           (1200000, 1_000_000 if phase == 'show' else 0)):
                        scene.advance_to(time_us)
                        before = scene.snapshot()
                        pose = scene.text_sample(1, 0)
                        cluster = scene.text_cluster_sample(1, 0)
                        self.assertEqual(pose[5], alpha)
                        self.assertEqual(cluster[3:7], pose[3:7])
                        self.assertEqual(cluster[0], pose[2])
                        scene.render()
                        if alpha:
                            x = (pose[3] + 32768) // 65536
                            y = (pose[4] + 32768) // 65536
                            self.assertEqual(scene.inspect_character_cell(x, y)['glyph'], pose[0])
                        self.assertEqual(scene.snapshot(), before)

    def test_legacy_default_and_explicit_reverse_show_match(self):
        for effect in ('text/glyph-fall', 'text/ash-type'):
            for phase in ('show', 'hide'):
                a = self.scene(None, effect, phase)
                b = self.scene('reverse-show', effect, phase)
                for time in (0, 350000, 700000, 1200000):
                    a.advance_to(time)
                    b.advance_to(time)
                    self.assertEqual(a.text_sample(1, 0), b.text_sample(1, 0))
                    self.assertEqual(a.render().bytes, b.render().bytes)
                self.assertFalse(self.row(a)['phaseModelExplicit'])
                self.assertTrue(self.row(b)['phaseModelExplicit'])

    def test_partial_updates_and_switches_preserve_retarget_pose_and_identity(self):
        scene = self.scene()
        scene.advance_to(370000)
        for command in ({'x': 30}, {'phaseModel': 'reverse-show'}, {'phaseModel': 'source'},
                        {'text': 'A\u0301BC'}, {'effect': 'text/ink-dissolve'}):
            before = scene.text_sample(1, 0)
            scene.command({'op': 'text', 'id': 1, **command})
            self.assertEqual(scene.text_sample(1, 0)[:7], before[:7])
        self.assertFalse(self.row(scene)['phaseModelExplicit'])
        self.assertEqual(self.row(scene)['phaseModel'], 'reverse-show')

    def test_numeric_and_typed_bindings_retarget_using_source_mode(self):
        scene = self.scene(text='N')
        scene.command({'op': 'define', 'path': '/x', 'value': 20,
                       'binding': {'family': 'text', 'id': 1, 'field': 'x'}})
        scene.command({'op': 'define', 'path': '/text', 'type': 'string', 'value': 'N',
                       'binding': {'family': 'text', 'id': 1, 'field': 'text'}})
        scene.advance_to(370000)
        for command in ({'op': 'set', 'path': '/x', 'value': 28},
                        {'op': 'set', 'path': '/text', 'value': 'NEW'}):
            pose = scene.text_sample(1, 0)
            scene.command(command)
            self.assertEqual(scene.text_sample(1, 0)[:7], pose[:7])
            self.assertEqual(self.row(scene)['phaseModel'], 'source')

    def test_schedule_full_capacity_replay_and_clear_reuse(self):
        scene = self.scene(text='N')
        scene.command({'op': 'clear', 'scope': 'text'})
        for identity in range(1, 25):
            scene.command({'op': 'text', 'id': identity, 'text': 'N',
                           'effect': 'text/ash-type', 'phaseModel': 'source'})
        scene.command({'op': 'define', 'path': '/future', 'value': 'N',
                       'binding': {'family': 'text', 'id': 1, 'field': 'text'}})
        scene.command({'op': 'schedule', 'id': 2, 'atUs': 500000, 'command':
                       {'op': 'set', 'path': '/future', 'value': 'NEW'}})
        self.assertEqual(len(scene.info_complete()['textRuns']), 24)
        self.assertTrue(all(row['phaseModel'] == 'source' for row in scene.info_complete()['textRuns']))
        saved = scene.snapshot()
        scene.restore(saved)
        self.assertEqual(scene.snapshot(), saved)
        scene.command({'op': 'cancel-schedule', 'id': 2})
        scene.command({'op': 'schedule', 'id': 3, 'atUs': 500000,
                       'command': {'op': 'text', 'id': 1, 'x': 22}})
        saved = scene.snapshot()
        scene.advance_to(650000)
        frame, final = scene.render().bytes, scene.snapshot()
        scene.restore(saved)
        scene.advance_to(650000)
        self.assertEqual(scene.render().bytes, frame)
        self.assertEqual(scene.snapshot(), final)
        for clear in ({'op': 'clear', 'scope': 'text'}, {'op': 'reset'}):
            scene.command(clear)
            scene.command({'op': 'text', 'id': 1, 'text': 'N'})
            self.assertFalse(self.row(scene)['phaseModelExplicit'])

    def test_invalid_commands_and_rechecksummed_modes_reject_atomically(self):
        scene = self.scene()
        for value in ('invented', '', 0, True, None):
            before = scene.snapshot()
            with self.subTest(value=value), self.assertRaises(ValueError):
                scene.command({'op': 'text', 'id': 1, 'phaseModel': value})
            self.assertEqual(scene.snapshot(), before)
        for slot, value in ((0, 4), (0, 0xffffffff), (1, 1)):
            before = scene.snapshot()
            bad = bytearray(before)
            struct.pack_into('<I', bad, MODE_OFFSET + slot * 4, value)
            with self.assertRaises(ValueError):
                scene.restore(checksum(bad))
            self.assertEqual(scene.snapshot(), before)

    def test_schema66_import_preserves_default_and_rejects_new_nested_commands(self):
        scene = self.scene(None, text='N')
        scene.advance_to(370000)
        def old_snapshot():
            old = bytearray(scene.snapshot()[:24 + SCHEMA66_BYTES])
            struct.pack_into('<I', old, 12, 0x20261066)
            struct.pack_into('<I', old, 28, 0x20261066)
            struct.pack_into('<I', old, 16, SCHEMA66_BYTES)
            return checksum(old)
        pose, frame = scene.text_sample(1, 0), scene.render().bytes
        scene.restore(old_snapshot())
        self.assertEqual(scene.text_sample(1, 0), pose)
        self.assertEqual(scene.render().bytes, frame)
        self.assertFalse(self.row(scene)['phaseModelExplicit'])
        scene.command({'op': 'schedule', 'id': 1, 'atUs': 500000, 'command':
                       {'op': 'batch', 'commands': [{'op': 'text', 'id': 1,
                        'phaseModel': 'source'}]}})
        before = scene.snapshot()
        with self.assertRaises(ValueError):
            scene.restore(old_snapshot())
        self.assertEqual(scene.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
