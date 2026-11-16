"""A restore's pending-command probe runs under the snapshot's own schema (native/src/transactions.c promotePendingProbe).

The probe used to normalise every schema newer than 0x20261067 down to 0x20261067, so a newer snapshot whose queue held
a command that needs a newer epoch (a prompt-source command, which needs 0x20261089), or whose prompt source was
enabled while anything was queued, was rejected on restore although its writer accepted it. Layer fields stay refused
in a schema-97 queue (test_bounded_prompt_source.test_schema97_cannot_carry_pending_layer_commands).
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import struct
import unittest

from native.tests.test_bounded_prompt_source import NativeScene, TIDEPOOL, as_schema97, current_schema, preset_command  # noqa: E402


class PendingProbeSchema(unittest.TestCase):
    def restore_and_run(self, old):
        with NativeScene() as other:
            other.restore(old)
            self.assertEqual(struct.unpack_from('<I', other.snapshot(), 12)[0], current_schema())
            other.advance_to(600_000)
            return other.info()

    def test_schema97_queue_with_a_prompt_source_command_restores_and_runs(self):
        with NativeScene() as scene:
            scene.schedule(7, 500_000, preset_command(TIDEPOOL))
            old = as_schema97(scene.snapshot())
        info = self.restore_and_run(old)
        self.assertIsNotNone(info['prompt']['firstPromptSource'])

    def test_schema97_enabled_source_with_a_queued_command_restores_and_runs(self):
        with NativeScene() as scene:
            scene.command(preset_command(TIDEPOOL))
            scene.schedule(7, 500_000, {'op': 'environment', 'stars': 9})
            old = as_schema97(scene.snapshot())
        info = self.restore_and_run(old)
        self.assertEqual(info['environment']['stars'], 9)
        self.assertIsNotNone(info['prompt']['firstPromptSource'])

    def test_the_same_queues_at_the_current_schema_restore(self):
        for queued in (preset_command(TIDEPOOL), {'op': 'environment', 'stars': 9}):
            with self.subTest(op=queued['op']), NativeScene() as scene:
                scene.command(preset_command(TIDEPOOL))
                scene.schedule(7, 500_000, queued)
                with NativeScene() as other:
                    other.restore(scene.snapshot())


if __name__ == '__main__':
    unittest.main()
