"""Real source-clock transactions consumed by the canonical shared replay plan."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "bindings/python"))
import parity
from nocturne_native import NativeScene

NAMES = ("pearl-cascade", "copper-causeway", "tidal-glass", "silt")
DRAFT = "Original scene clock / 文 🪷"


class ScenicClockParity(unittest.TestCase):
    def test_canonical_plan_contains_actual_clock_transactions_for_all_four_scenes(self):
        commands = parity.sceneArtClockPlan()
        self.assertEqual(len(commands), 32)
        self.assertEqual(parity.plan()[-len(commands):], commands)
        names = []
        for start in range(0, len(commands), 8):
            self.assertEqual(commands[start]["op"], "reset")
            setup = commands[start + 1]
            self.assertEqual(setup["op"], "batch")
            self.assertTrue(all(c["op"] not in ("reset", "time", "batch") for c in setup["commands"]))
            artwork = [c for c in setup["commands"] if c["op"] == "scene-art"]
            self.assertEqual(len(artwork), 1)
            names.append(artwork[0]["scene"])
            self.assertEqual(artwork[0]["timeMs"], 425)
            self.assertNotIn("timeMs", commands[start + 3])
            self.assertEqual(commands[start + 4]["timeMs"], 1700)
            self.assertIsNone(commands[start + 6]["timeMs"])
        self.assertEqual(tuple(names), NAMES)

    def test_native_freeze_travel_coexistence_and_snapshot_restore(self):
        commands = parity.sceneArtClockPlan()
        with NativeScene(2030) as scene:
            for start, name in zip(range(0, len(commands), 8), NAMES):
                rows = []
                for offset, command in enumerate(commands[start:start + 8]):
                    scene.command(command)
                    frame = scene.render().bytes
                    info = scene.info()
                    rows.append((frame, info))
                    if offset == 0:
                        continue
                    source = info["sceneArt"]
                    self.assertEqual(source["scene"], name)
                    if offset <= 3:
                        self.assertEqual(source["timeMs"], 425)
                        self.assertEqual(source["effective"]["timeMs"], 425)
                    elif offset <= 5:
                        self.assertEqual(source["timeMs"], 1700)
                        self.assertEqual(source["effective"]["timeMs"], 1700)
                    else:
                        self.assertIsNone(source["timeMs"])
                        self.assertEqual(source["effective"]["timeMs"], info["clock"]["timeUs"] // 1000)
                with self.subTest(scene=name):
                    self.assertTrue(rows[1][0] == rows[2][0], "explicit source time freezes actual artwork")
                    self.assertNotEqual(rows[2][1]["clock"], rows[1][1]["clock"])
                    self.assertEqual(rows[3][1]["sceneArt"]["controls"]["travel"], 9.25)
                    self.assertEqual(rows[5][1]["prompt"]["text"], DRAFT)
                    self.assertEqual(rows[5][1]["camera"]["yaw"], 22)
                    if name == "copper-causeway":
                        # Original road marks depend on authored travel, not time.
                        self.assertTrue(rows[6][0] == rows[7][0], "fixed travel preserves original Copper geometry")
                        self.assertTrue(rows[2][0] != rows[3][0], "actual Copper road marks respond to travel")
                    else:
                        self.assertTrue(rows[6][0] != rows[7][0], "null resumes actual source motion")
                    state = scene.snapshot()
                    scene.command({"op": "scene-art", "timeMs": 0})
                    scene.restore(state)
                    self.assertEqual(scene.info(), rows[-1][1])
                    self.assertTrue(scene.render().bytes == rows[-1][0], "restored frame differs")
                    self.assertTrue(scene.snapshot() == state, "render remains observational")

    def test_actual_python_and_wasm_replay_records_agree(self):
        commands = parity.sceneArtClockPlan()
        payload = "".join(json.dumps(c, separators=(",", ":")) + "\n" for c in commands)
        node = shutil.which("node")
        self.assertIsNotNone(node, "actual Node/WASM runtime required")
        results = []
        for argv in ([sys.executable, str(ROOT / "scripts/replay.py")],
                     [node, str(ROOT / "scripts/replay.mjs")]):
            run = subprocess.run(argv, cwd=ROOT, input=payload, text=True,
                                 capture_output=True, timeout=120, env=os.environ.copy())
            self.assertEqual(run.returncode, 0, run.stderr)
            rows = [json.loads(line) for line in run.stdout.splitlines()]
            self.assertEqual(len(rows), len(commands))
            for index, row in enumerate(rows):
                self.assertEqual(row["index"], index)
                for field in ("frame", "state", "metadata", "motions"):
                    self.assertIn(field, row)
                if commands[index]["op"] != "reset":
                    self.assertIn("timeMs", row["metadata"]["sceneArt"])
            results.append(rows)
        self.assertEqual(results[0], results[1], "real frame/state/metadata/motion replay differs")


if __name__ == "__main__":
    unittest.main()
