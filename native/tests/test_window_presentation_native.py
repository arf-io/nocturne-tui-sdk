"""Public RC2 window presentation, selected theatre toolbar, and replay tests.

These tests intentionally use NativeScene's public command, snapshot, metadata,
render, and pointer interfaces. They must run only after the aligned schema-67
core is available; a stale NativeScene binary is not evidence for this concern.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bindings" / "python"))

from nocturne_native import NativeScene  # noqa: E402


DEFAULT_SOURCE_OPTIONS = {
    "opacity": .85,
    "depthFade": .008,
    "chrome": "mac",
    "controlWidth": 10,
    "controlHeight": 3,
    "customSide": "right",
    "customOrder": ["minimize", "maximize", "background", "close"],
    "customGlyphs": [0x2212, 0x25a1, 0x25c7, 0xd7],
}


def window_row(scene, identity=1):
    return next(row for row in scene.info_complete()["windows"] if row["id"] == identity)


class WindowPresentationNative(unittest.TestCase):
    def scene(self):
        scene = NativeScene(2030)
        self.addCleanup(scene.close)
        scene.command({"op": "resize", "width": 100, "height": 40})
        scene.command({"op": "window", "id": 1, "title": "Source window",
                       "text": "Window presentation remains retained.",
                       "position": [0, 0, 0], "width": 30, "height": 16,
                       "durationMs": 0})
        return scene

    def test_opt_in_defaults_partial_updates_alpha_depth_and_snapshot(self):
        scene = self.scene()
        legacy = window_row(scene)
        self.assertFalse(legacy["sourcePresentation"])
        self.assertIsNone(legacy["sourceOptions"])
        self.assertAlmostEqual(legacy["effectiveOpacity"], legacy["alpha"], places=6)

        scene.command({"op": "window", "id": 1, "sourcePresentation": True})
        enabled = window_row(scene)
        self.assertTrue(enabled["sourcePresentation"])
        self.assertEqual(enabled["sourceOptions"], DEFAULT_SOURCE_OPTIONS)
        self.assertEqual(enabled["alpha"], .85)
        self.assertEqual(enabled["effectiveOpacity"], .85)

        scene.command({"op": "window", "id": 1, "depthFade": .04,
                       "chrome": "windows", "customSide": "left"})
        partial = window_row(scene)
        self.assertEqual(partial["sourceOptions"]["depthFade"], .04)
        self.assertEqual(partial["sourceOptions"]["chrome"], "windows")
        self.assertEqual(partial["sourceOptions"]["customSide"], "left")
        self.assertEqual(partial["sourceOptions"]["controlWidth"], 10)
        self.assertEqual(partial["sourceOptions"]["opacity"], partial["alpha"])

        scene.command({"op": "window", "id": 1, "alpha": .42,
                       "position": [0, 0, -10]})
        faded = window_row(scene)
        self.assertEqual(faded["sourceOptions"]["opacity"], .42)
        self.assertAlmostEqual(faded["effectiveOpacity"], .42 * .6, places=6)
        scene.render()
        faded_body = scene.inspect_character_cell(50, 20)

        saved = scene.snapshot()
        scene.command({"op": "window", "id": 1, "depthFade": 0})
        scene.restore(saved)
        self.assertEqual(window_row(scene), faded)
        scene.render()
        self.assertEqual(scene.inspect_character_cell(50, 20), faded_body)

    def test_source_options_change_rendered_window_and_clear_retained_mode(self):
        baseline = self.scene()
        baseline.command({"op": "window", "id": 1, "position": [0, 0, -10], "alpha": .42})
        baseline_words = baseline.render().words()
        baseline_window = [word for word in baseline_words if word[3] == (0x20000000 | 1)]
        source = self.scene()
        source.command({"op": "window", "id": 1, "position": [0, 0, -10], "alpha": .42,
                        "sourcePresentation": True, "depthFade": .04})
        source_words = source.render().words()
        source_window = [word for word in source_words if word[3] == (0x20000000 | 1)]
        self.assertTrue(baseline_window)
        self.assertEqual(len(source_window), len(baseline_window))
        self.assertNotEqual(source_window, baseline_window,
                            "source opacity/depth fade must alter window-owned common cells")
        before_clear = source.snapshot()
        source.command({"op": "window", "id": 1, "sourcePresentation": False})
        cleared = window_row(source)
        self.assertFalse(cleared["sourcePresentation"])
        self.assertIsNone(cleared["sourceOptions"])
        self.assertEqual(cleared["alpha"], .42, "clearing presentation must keep canonical alpha")
        self.assertNotEqual(source.snapshot(), before_clear)
        source.restore(before_clear)
        self.assertTrue(window_row(source)["sourcePresentation"])

    def test_selected_theatre_toolbar_hits_close_minimize_maximize_and_background(self):
        # RC2's mac profile is left ordered close/minimize/maximize/background;
        # the theatre painter exposes each complete source rectangle as a hit.
        expected = [
            (0x60000000, "close"),
            (0x61000000, "minimize"),
            (0x62000000, "maximize"),
            (0x64000000, "background"),
        ]
        for index, (family, action) in enumerate(expected):
            with self.subTest(action=action):
                scene = self.scene()
                scene.command({"op": "window", "id": 2, "title": "Second",
                               "position": [0, 0, 4], "durationMs": 0})
                scene.command({"op": "window", "id": 1, "sourcePresentation": True})
                frame_before_action = scene.render().bytes
                x, y = 3 + index * 11 + 5, 7
                cell = scene.inspect_character_cell(x, y)
                self.assertEqual(cell["id"], family | 1)
                before = window_row(scene)
                scene.command({"op": "pointer", "phase": "down", "x": x, "y": y})
                scene.command({"op": "pointer", "phase": "up", "x": x, "y": y})
                after = window_row(scene)
                if action in ("close", "minimize"):
                    self.assertEqual(after["visible"], 0)
                elif action == "background":
                    self.assertEqual(after["position"][2], -3,
                                     "source +Z background depth maps to canonical max-Z minus 3")
                    self.assertEqual(after["visible"], before["visible"],
                                     "source background changes stacking only")
                else:
                    self.assertNotEqual(scene.render().bytes, frame_before_action,
                                        "maximize hit must change rendered window geometry")

    def test_source_window_order_is_retained_and_background_raises_z_by_three(self):
        scene = self.scene()
        scene.command({"op": "window", "id": 2, "title": "Second",
                       "text": "Second layer", "position": [0, 0, 0],
                       "width": 30, "height": 16, "durationMs": 0})
        scene.command({"op": "window", "id": 1, "sourcePresentation": True})
        scene.command({"op": "window", "id": 2, "sourcePresentation": True})
        first_order, second_order = window_row(scene, 1)["sourceOrder"], window_row(scene, 2)["sourceOrder"]
        self.assertLess(first_order, second_order,
                        "the source manager assigns monotonically increasing order on add/select")
        scene.render()
        before = scene.inspect_character_cell(50, 20)
        self.assertEqual(before["id"] & 0xffff, 2,
                         "same-depth windows paint in ascending order; later order is on top")
        scene.command({"op": "window-action", "id": 2, "action": "background"})
        backgrounded = window_row(scene, 2)
        self.assertEqual(backgrounded["position"][2], -3,
                         "source max worldZ + 3 maps through the canonical Z reflection")
        self.assertEqual(backgrounded["visible"], 1)
        scene.render()
        after = scene.inspect_character_cell(50, 20)
        self.assertEqual(after["id"] & 0xffff, 1,
                         "background raises the selected window's depth so the other window covers it")

    def test_invalid_source_fields_reject_atomically_and_false_cannot_combine(self):
        scene = self.scene()
        scene.command({"op": "window", "id": 1, "sourcePresentation": True})
        before = scene.snapshot()
        for patch in (
            {"sourcePresentation": False, "chrome": "windows"},
            {"sourcePresentation": "true"}, {"depthFade": .0801},
            {"chrome": "macos"}, {"controlWidth": 4},
            {"controlHeight": 6.5}, {"customSide": "center"},
            {"customOrder": ["close", "minimize", "maximize", "maximize"]},
            {"customGlyphs": ["a", "ab", "c", "d"]},
        ):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                scene.command({"op": "window", "id": 1, **patch})
            self.assertEqual(scene.snapshot(), before)

if __name__ == "__main__":
    unittest.main()
