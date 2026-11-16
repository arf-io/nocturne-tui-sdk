"""Public canvas lifecycle and exact empty-frame behavior; no mocks."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


class CanvasPresentation(unittest.TestCase):
    def setUp(self):
        self.scene = NativeScene()
        self.addCleanup(self.scene.close)

    def command(self, **command):
        self.scene.command(command)

    def test_defaults_omit_patch_and_snapshot_roundtrip(self):
        self.assertEqual(self.scene.info()['environment']['presentation'], 'workbench')
        default = self.scene.snapshot()
        self.command(op='environment', presentation='canvas')
        self.command(op='environment', background=0x123456)
        saved = self.scene.snapshot()
        self.assertEqual(self.scene.info()['environment']['presentation'], 'canvas')
        self.command(op='environment', presentation='workbench')
        self.scene.restore(saved)
        self.assertEqual(self.scene.info()['environment']['presentation'], 'canvas')
        self.scene.restore(default)
        self.assertEqual(self.scene.info()['environment']['presentation'], 'workbench')

    def test_canvas_fills_every_cell_and_keeps_existing_default_header(self):
        self.command(op='prompt', active=False)
        self.command(op='environment', stars=0, background=0x123456, style='solid', sampling='cell')
        workbench = self.scene.render().bytes
        self.command(op='environment', presentation='canvas')
        for width, height in [(120, 40), (3, 2), (1, 1), (600, 257)]:
            self.command(op='resize', width=width, height=height)
            before = self.scene.snapshot()
            frame = self.scene.render()
            self.assertEqual((frame.width, frame.height), (width, height))
            self.assertEqual(frame.bytes, struct.pack('<4I', 32, 0xcdd9d1, 0x123456, 0)*width*height)
            self.assertEqual(self.scene.snapshot(), before)
        self.command(op='resize', width=160, height=48)
        self.command(op='environment', presentation='workbench')
        self.assertEqual(self.scene.render().bytes, workbench)

    def test_invalid_settings_reject_without_mutation(self):
        for value in [None, True, 1, '', 'fullscreen', [], {}]:
            with self.subTest(value=value):
                before = self.scene.snapshot()
                with self.assertRaises(ValueError):
                    self.command(op='environment', presentation=value)
                self.assertEqual(self.scene.snapshot(), before)

    def test_numeric_binding_updates_presentation_and_rejects_invalid_values(self):
        self.command(op='define', path='/canvas', type='number', value=1,
                     binding={'family': 'environment', 'id': 0, 'field': 'presentation'})
        self.assertEqual(self.scene.info()['environment']['presentation'], 'canvas')
        self.command(op='set', path='/canvas', value=0)
        self.assertEqual(self.scene.info()['environment']['presentation'], 'workbench')
        before = self.scene.snapshot()
        with self.assertRaises(ValueError):
            self.command(op='set', path='/canvas', value=2)
        self.assertEqual(self.scene.snapshot(), before)

    def test_reset_returns_to_workbench_clear_keeps_presentation(self):
        self.command(op='environment', presentation='canvas')
        self.command(op='scene-art', scene='pearl-cascade')
        self.command(op='clear', scope='scene-art')
        self.assertIsNone(self.scene.info()['sceneArt'])
        self.assertEqual(self.scene.info()['environment']['presentation'], 'canvas')
        self.command(op='reset')
        self.assertEqual(self.scene.info()['environment']['presentation'], 'workbench')

    def test_corrupt_flags_and_padding_reject_after_valid_checksum(self):
        before = self.scene.snapshot()
        self.assertEqual(len(before), snapshot_size(self.scene))
        for offset, value in [(13_850_008, 2), (13_850_012, 1)]:
            bad = bytearray(before)
            struct.pack_into('<I', bad, 24 + offset, value)
            struct.pack_into('<I', bad, 20, zlib.crc32(bad[24:]))
            with self.assertRaises(ValueError):
                self.scene.restore(bad)
            self.assertEqual(self.scene.snapshot(), before)

    def test_schema66_pending_new_fields_reject_before_promotion(self):
        def old_snapshot():
            old = bytearray(self.scene.snapshot()[:24 + 13_578_976])
            for offset in (12, 28):
                struct.pack_into('<I', old, offset, 0x20261066)
            struct.pack_into('<I', old, 16, len(old) - 24)
            struct.pack_into('<I', old, 20, zlib.crc32(old[24:]))
            return old
        self.scene.restore(old_snapshot())
        self.assertEqual(self.scene.info()['environment']['presentation'], 'workbench')
        commands = [
            {'op':'environment', 'presentation':'canvas'},
            {'op':'define', 'path':'/canvas', 'value':1,
             'binding':{'family':'environment', 'id':0, 'field':'presentation'}},
            {'op':'clear', 'scope':'scene-art'},
            {'op':'window', 'id':1, 'sourcePresentation':True},
            {'op':'source-stage-component', 'id':1, 'kind':'text',
             'x':0, 'y':0, 'width':4, 'height':1, 'text':'ABCD'},
        ]
        for command in commands:
            self.command(op='reset')
            self.command(op='schedule', id=1, atUs=500000,
                         command={'op':'batch', 'commands':[command]})
            before = self.scene.snapshot()
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.scene.restore(old_snapshot())
            self.assertEqual(self.scene.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
