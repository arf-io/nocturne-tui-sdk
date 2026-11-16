"""Public framed prompt retention, compatibility and atomic rejection."""
import struct
import sys
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


class PromptFramedLifecycle(unittest.TestCase):
    def scene(self):
        scene = NativeScene(42)
        self.addCleanup(scene.close)
        scene.command({'op': 'resize', 'width': 100, 'height': 40})
        scene.command({'op': 'draft', 'text': 'A retained prompt', 'emitWeather': False})
        return scene

    def test_source_defaults_partial_overrides_alias_and_owned_metadata(self):
        scene = self.scene()
        self.assertEqual(scene.info()['prompt']['presentation'], 'compact')
        scene.command({'op': 'prompt', 'presentation': 'framed'})
        prompt = scene.info()['prompt']
        self.assertEqual(prompt['presentation'], 'framed')
        self.assertEqual(prompt['sourceOptions'], {
            'alpha': .32, 'background': 0x10161e, 'foreground': 0xdedbd2,
            'accent': 0x8ccfc4, 'selectionColor': 0x385763, 'border': 'rounded',
            'paddingX': 1, 'paddingY': 0, 'margin': 1, 'minRows': 1, 'maxRows': 7,
            'inlineRows': 12, 'inlineWidth': 88, 'lineNumbers': True,
            'active': True, 'selected': False, 'hueStep': 0, 'hueSpeed': 0,
            'huePeriodMs': 1000, 'maxChars': 0,
        })
        before=scene.snapshot()
        with self.assertRaises(ValueError):
            scene.command({'op': 'prompt', 'maxChars': 1})
        self.assertEqual(scene.snapshot(),before)
        scene.command({'op':'draft','text':'','emitWeather':False})
        scene.command({'op': 'prompt', 'maxChars': 1})
        self.assertEqual(scene.info()['prompt']['sourceOptions']['maxChars'], 1)
        scene.restore(before)
        scene.command({'op': 'prompt', 'padding': 2, 'paddingX': 3,
                       'foreground': '#123456', 'selected': True})
        options = scene.info()['prompt']['sourceOptions']
        self.assertEqual((options['paddingX'], options['paddingY']), (3, 2))
        self.assertEqual(options['foreground'], 0x123456)
        scene.command({'op': 'prompt', 'hueSpeed': 27, 'huePeriodMs': 700})
        self.assertEqual(scene.info()['prompt']['sourceOptions']['foreground'], 0x123456)
        self.assertEqual(scene.info()['prompt']['text'], 'A retained prompt')
        options['foreground'] = 0
        self.assertEqual(scene.info()['prompt']['sourceOptions']['foreground'], 0x123456)

    def test_snapshot_schedule_replay_switch_and_reset(self):
        scene = self.scene()
        scene.command({'op': 'prompt', 'presentation': 'framed', 'mode': 'vim-inline'})
        scene.command({'op': 'schedule', 'id': 1, 'atUs': 500000,
                       'command': {'op': 'prompt', 'foreground': '#123456', 'margin': 2}})
        saved = scene.snapshot()
        scene.advance_to(650000)
        before = scene.snapshot()
        frame = scene.render().bytes
        self.assertEqual(scene.snapshot(), before)
        scene.restore(saved)
        scene.advance_to(650000)
        self.assertEqual(scene.snapshot(), before)
        self.assertEqual(scene.render().bytes, frame)
        scene.command({'op': 'prompt', 'presentation': 'compact'})
        self.assertEqual(scene.info()['prompt']['presentation'], 'compact')
        self.assertIsNone(scene.info()['prompt']['sourceOptions'])
        self.assertEqual(scene.info()['prompt']['text'], 'A retained prompt')
        scene.command({'op': 'reset'})
        self.assertEqual(scene.info()['prompt']['presentation'], 'compact')

    def test_invalid_settings_and_old_schema_pending_command_reject(self):
        scene = self.scene()
        for command in ({'presentation': 'unknown'}, {'foreground': '#123456'},
                        {'presentation': 'framed', 'lineNumbers': 1},
                        {'presentation': 'framed', 'maxChars': -1},
                        {'presentation': 'framed', 'background': 'blue'},
                        {'presentation': 'framed', 'inlineWidth': -1}):
            before = scene.snapshot()
            with self.subTest(command=command), self.assertRaises(ValueError):
                scene.command({'op': 'prompt', **command})
            self.assertEqual(scene.snapshot(), before)
        scene.command({'op': 'schedule', 'id': 1, 'atUs': 500000, 'command':
                       {'op': 'batch', 'commands': [{'op': 'prompt', 'presentation': 'framed'}]}})
        before = scene.snapshot()
        old = bytearray(before[:24 + 13578976])
        struct.pack_into('<I', old, 12, 0x20261066)
        struct.pack_into('<I', old, 28, 0x20261066)
        struct.pack_into('<I', old, 16, len(old) - 24)
        struct.pack_into('<I', old, 20, zlib.crc32(old[24:]))
        with self.assertRaises(ValueError):
            scene.restore(old)
        self.assertEqual(scene.snapshot(), before)

    def test_checkpoint_snapshot_rejects_hidden_tail_and_capacity_mismatch(self):
        scene = self.scene()
        scene.command({'op': 'prompt', 'presentation': 'framed', 'mode': 'vim-inline'})
        footer = 24 + 13579072
        checkpoint_text = footer + 4432
        def reject_changed(offset, value):
            before = scene.snapshot()
            changed = bytearray(before)
            struct.pack_into('<I', changed, offset, value)
            struct.pack_into('<I', changed, 20, zlib.crc32(changed[24:]))
            with self.assertRaises(ValueError):
                scene.restore(changed)
            self.assertEqual(scene.snapshot(), before)
        # A disabled checkpoint cannot retain hidden text, even in a framed prompt.
        reject_changed(checkpoint_text, ord('X'))
        for key in (':', 'w', 'Enter'):
            scene.command({'op': 'key', 'key': key})
        self.assertEqual(scene.info()['prompt']['sourceCheckpoint']['text'], 'A retained prompt')
        # PromptFramed.minimizedRestoreMode is the second control word after
        # its options; only 0, inline, and fullscreen are valid restore targets.
        reject_changed(footer + 148, 3)
        # Active checkpoints also have canonical tails and respect their saved options.
        reject_changed(checkpoint_text + 65535 * 4, ord('X'))
        reject_changed(footer + 4296 + 128, 1)


if __name__ == '__main__':
    unittest.main()
