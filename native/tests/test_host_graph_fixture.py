"""Actual native visibility and input routing for the shared host graph fixture."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "native/scripts"))
from native.bindings.python.nocturne_native import NativeScene
from check_host_inputs import fixtureCommands


class HostGraphFixture(unittest.TestCase):
    def test_visible_owner_cells_and_retarget_at_real_host_heights(self):
        for height in (22, 23, 24):
            with self.subTest(height=height):
                with NativeScene(library=os.environ.get("NOCTURNE_NATIVE_LIBRARY")) as scene:
                    scene.command({"op": "reset", "seed": 2030})
                    for command in fixtureCommands("graph"):
                        scene.command(command)
                    scene.command({"op": "resize", "width": 80, "height": height})
                    scene.command({"op": "pause", "paused": True})
                    frame = scene.render()
                    hits = {}
                    for index, (_, _, _, owner) in enumerate(frame.words()):
                        if owner & 0xff000000 == 0x10000000:
                            hits.setdefault(owner & 0xffff, (index % frame.width, index // frame.width))
                    self.assertEqual(set(hits), {11, 12},
                                     "Both actual node owners must remain visible in host content")
                    camera = scene.info()["camera"]
                    for node in (11, 12):
                        # Selection opens the inspector and can reflow native projection.
                        current = scene.render()
                        index = next(i for i, word in enumerate(current.words())
                                     if word[3] == 0x10000000 | node)
                        x, y = index % current.width, index // current.width
                        scene.command({"op": "pointer", "phase": "down", "button": 0, "x": x, "y": y})
                        scene.command({"op": "pointer", "phase": "up", "button": 0, "x": x, "y": y})
                        self.assertEqual(scene.info()["selection"], node)
                    self.assertEqual(scene.info()["camera"], camera)
                    self.assertEqual(scene.info()["clock"]["timeUs"], 0)


if __name__ == "__main__":
    unittest.main()
