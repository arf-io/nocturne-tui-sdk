"""Public retained texture tests; authored before the schema68 implementation."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

CELLS = [[0x28ff, 0xf0c080, 0x112233], [0x2588, 0x55aaee, 0x332211],
         [0x2580, 0xabcdef, 0x123456], [0x1f680, 0xfefefe, 0x224466]]


def texture(scene, identity=1):
    return next(w for w in scene.info_complete()['windows'] if w['id'] == identity)['texture']


def old67(snapshot):
    from native.tests.constructed_legacy_snapshot import construct_legacy_snapshot
    return construct_legacy_snapshot(snapshot,0x20261067,14121280)


class WindowTextureIntegration(unittest.TestCase):
    def scene(self):
        s = NativeScene(2030)
        self.addCleanup(s.close)
        for command in [
            {'op': 'resize', 'width': 100, 'height': 60},
            {'op': 'environment', 'presentation': 'canvas', 'stars': 0,
             'style': 'solid', 'background': 0x112233},
            {'op': 'prompt', 'active': False},
            {'op': 'floor', 'enabled': False, 'visible': False},
            {'op': 'camera', 'position': [0, 0, 60], 'yaw': 0, 'pitch': 0,
             'roll': 0, 'fov': 60},
            {'op': 'window', 'id': 1, 'position': [0, 0, 0], 'width': 40,
             'height': 24, 'alpha': 1, 'durationMs': 0, 'sourceGeometry': True,
             'title': 'Original document', 'text': 'Reader keeps this text.'},
        ]:
            s.command(command)
        return s

    def upload(self, s, identity=1):
        s.command({'op': 'window-texture', 'id': identity, 'width': 2, 'height': 2,
                   'cells': CELLS})

    def test_upload_patch_resize_compaction_and_legacy_restore(self):
        s = self.scene()
        baseline = s.render().words()
        self.assertIsNone(texture(s))
        self.upload(s)
        self.assertEqual(texture(s), {'width': 2, 'height': 2, 'cells': CELLS})
        s.command({'op': 'window', 'id': 2, 'durationMs': 0})
        self.upload(s, 2)
        s.command({'op': 'window-texture', 'id': 1, 'width': 3, 'height': 1,
                   'offset': 1, 'cells': [[65, 1, 2]]})
        self.assertEqual(texture(s)['cells'], [[32, 0, 0], [65, 1, 2], [32, 0, 0]])
        self.assertEqual(texture(s, 2)['cells'], CELLS)
        s.command({'op': 'window-texture', 'id': 2, 'offset': 3,
                   'cells': [[66, 3, 4]]})
        self.assertEqual(texture(s, 2)['cells'][-1], [66, 3, 4])
        s.command({'op': 'remove-window-texture', 'id': 1})
        self.assertIsNone(texture(s))
        self.assertEqual(texture(s, 2)['cells'][-1], [66, 3, 4])
        # Removing the texture alone must restore the exact previous window path.
        alone = self.scene()
        self.upload(alone)
        alone.command({'op': 'remove-window-texture', 'id': 1})
        self.assertEqual(alone.render().words(), baseline)
        self.assertEqual(alone.info_complete()['windows'][0]['text'], 'Reader keeps this text.')

    def test_rendered_cells_hits_rotation_replay_and_reader(self):
        s = self.scene()
        self.upload(s)
        saved = s.snapshot()
        words = s.render().words()
        body = [c for c in words if c[3] == 0x20000001]
        self.assertTrue(body)
        self.assertTrue({c[0] for c in body}.issuperset(row[0] for row in CELLS))
        self.assertEqual(s.snapshot(), saved, 'render must not alter state')
        s.command({'op': 'window', 'id': 1, 'yaw': 35, 'roll': 15})
        self.assertNotEqual(s.render().words(), words)
        s.restore(saved)
        self.assertEqual(s.render().words(), words)
        s.command({'op': 'window-action', 'id': 1, 'action': 'maximize'})
        self.assertGreater(sum(c[3] == 0x20000001 for c in s.render().words()), len(body))
        s.restore(saved)
        s.command({'op': 'window-action', 'id': 1, 'action': 'read'})
        self.assertIn(ord('R'), [c[0] for c in s.render().words()])
        self.assertEqual(texture(s)['cells'], CELLS)

    def test_textured_window_depth_does_not_follow_selection_order(self):
        s = self.scene()
        self.upload(s)
        s.command({'op': 'window', 'id': 2, 'position': [0, 0, -10], 'width': 40,
                   'height': 24, 'alpha': 1, 'durationMs': 0})
        s.command({'op': 'window-texture', 'id': 2, 'width': 1, 'height': 1,
                   'cells': [[90, 0xffffff, 0]]})
        words = s.render().words()
        self.assertEqual(words[30*100+50][3], 0x20000001)
        s.command({'op': 'window', 'id': 1, 'shape': 'diamond'})
        s.command({'op': 'window', 'id': 2})
        self.assertEqual(s.render().words()[30*100+50][3], 0x20000001)
        before = s.snapshot()
        with self.assertRaises(ValueError):
            s.command({'op': 'window', 'id': 1, 'shape': 'cloud'})
        self.assertEqual(s.snapshot(), before)

    def test_invalid_commands_and_batch_are_snapshot_atomic(self):
        s = self.scene()
        self.upload(s)
        invalid = [
            {'id': 99}, {'width': 0, 'height': 2}, {'width': 2},
            {'width': 65537, 'height': 1}, {'width': 256, 'height': 257},
            {'width': True, 'height': 2}, {'offset': -1}, {'offset': 5},
            {'offset': 4, 'cells': [[65, 0, 0]]}, {'cells': [[65, 0]]},
            {'cells': [[0xd800, 0, 0]]}, {'cells': [[31, 0, 0]]},
            {'cells': [[0x110000, 0, 0]]}, {'cells': [[65, 0x1000000, 0]]},
            {'cells': [[65.5, 0, 0]]}, {'cells': 'bad'}, {'unknown': 1},
        ]
        for patch in invalid:
            before = s.snapshot()
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):
                    s.command({'op': 'window-texture', 'id': 1, **patch})
                self.assertEqual(s.snapshot(), before)
        before = s.snapshot()
        with self.assertRaises(ValueError):
            s.command({'op': 'batch', 'commands': [
                {'op': 'remove-window-texture', 'id': 1},
                {'op': 'window-texture', 'id': 99, 'width': 1, 'height': 1}]})
        self.assertEqual(s.snapshot(), before)

    def test_pool_exhaustion_reuse_and_reset(self):
        s = self.scene()
        s.command({'op': 'window-texture', 'id': 1, 'width': 65536, 'height': 1})
        s.command({'op': 'window', 'id': 2})
        before = s.snapshot()
        with self.assertRaises(ValueError):
            s.command({'op': 'window-texture', 'id': 2, 'width': 1, 'height': 1})
        self.assertEqual(s.snapshot(), before)
        s.command({'op': 'remove-window-texture', 'id': 1})
        self.upload(s, 2)
        self.assertEqual(texture(s, 2)['cells'], CELLS)
        s.command({'op': 'reset'})
        s.command({'op': 'window', 'id': 2})
        self.assertIsNone(texture(s, 2))

    def test_schema67_promotes_without_texture_and_rejects_nested_new_command(self):
        s = self.scene()
        old = old67(s.snapshot())
        self.upload(s)
        s.restore(old)
        self.assertIsNone(texture(s))
        s.command({'op': 'schedule', 'id': 2, 'atUs': 500000, 'command': {
            'op': 'window', 'id': 1, 'sourcePresentation': True, 'depthFade': .01}})
        s.restore(old67(s.snapshot()))
        s.command({'op': 'cancel-schedule', 'id': 2})
        s.command({'op': 'schedule', 'id': 1, 'atUs': 1000000, 'command': {
            'op': 'batch', 'commands': [{'op': 'window-texture', 'id': 1,
                                        'width': 1, 'height': 1}]}})
        before = s.snapshot()
        with self.assertRaises(ValueError):
            s.restore(old67(before))
        self.assertEqual(s.snapshot(), before)

    def test_large_viewport_does_not_restrict_world_window_dimensions(self):
        s = self.scene()
        self.upload(s)
        s.command({'op': 'resize', 'width': 600, 'height': 80})
        s.command({'op': 'window', 'id': 1, 'width': 100000, 'height': 100000})
        self.assertTrue(any(c[3] == 0x20000001 for c in s.render().words()))
        self.assertEqual(texture(s)['cells'], CELLS)

    def test_current_wasm_matches_native_frames_and_owned_texture_readback(self):
        commands = [
            {'op': 'resize', 'width': 100, 'height': 60},
            {'op': 'environment', 'presentation': 'canvas', 'stars': 0,
             'style': 'solid', 'background': 0x112233},
            {'op': 'prompt', 'active': False},
            {'op': 'floor', 'enabled': False, 'visible': False},
            {'op': 'camera', 'position': [0, 0, 60], 'yaw': 0, 'pitch': 0,
             'roll': 0, 'fov': 60},
            {'op': 'window', 'id': 1, 'position': [0, 0, 0], 'width': 40,
             'height': 24, 'alpha': 1, 'durationMs': 0, 'sourceGeometry': True},
            {'op': 'window-texture', 'id': 1, 'width': 2, 'height': 2, 'cells': CELLS},
        ]
        changes = [None, {'op': 'window', 'id': 1, 'yaw': 30, 'alpha': .4},
                   {'op': 'window', 'id': 1, 'shape': 'ellipse'},
                   {'op': 'window-texture', 'id': 1, 'offset': 1, 'cells': [[32, 1, 2]]},
                   {'op': 'remove-window-texture', 'id': 1}]
        native = NativeScene(2030)
        self.addCleanup(native.close)
        for command in commands:
            native.command(command)
        expected = []
        for command in changes:
            if command:
                native.command(command)
            expected.append({'words': [word for cell in native.render().words() for word in cell],
                             'texture': texture(native)})
        with tempfile.TemporaryDirectory(prefix='nr-window-texture-') as directory:
            request, response = Path(directory)/'request.json', Path(directory)/'response.json'
            request.write_text(json.dumps({'commands': commands, 'changes': changes}))
            subprocess.run(['node', str(ROOT/'tests/window_texture_wasm_runner.mjs'),
                            str(request), str(response)], check=True, timeout=60)
            self.assertEqual(json.loads(response.read_text())['frames'], expected)


if __name__ == '__main__':
    unittest.main()
