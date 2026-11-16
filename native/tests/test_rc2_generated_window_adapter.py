"""Generated RC2 window command mapping against the pinned original model."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "hosts" / "python"))
sys.path.insert(0, str(ROOT / "bindings" / "python"))

from atelier_application import rc2_window_commands  # noqa: E402
from nocturne_native import NativeScene  # noqa: E402
from native.tests.historical_reference import load_rc2_workbench  # noqa: E402


KINETIC_MODEL_RETURN = (
    "return {KINETIC_SCENES,DEFAULT_KINETIC_GRAPH,KineticModel,"
    "exportKineticConfiguration,applyKineticConfiguration};"
)
RGB_EXPORT_ANCHOR = "/** Stateful configuration is owned by the caller. Calls are synchronous, non-reentrant."
OPTION_KEYS = (
    "lightness", "chroma", "brightness", "hueOffset", "feather",
    "textLightness", "textChroma", "lockLightness", "stopWidths",
)


class Rc2GeneratedWindowAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright

        source = load_rc2_workbench()
        if source.count(KINETIC_MODEL_RETURN) != 1:
            raise AssertionError("pinned RC2 KineticModel export anchor changed")
        if source.count(RGB_EXPORT_ANCHOR) != 1:
            raise AssertionError("pinned RC2 RGB helper instrumentation anchor changed")
        source = source.replace(RGB_EXPORT_ANCHOR, "window.__rc2Rgb=rgb;\n" + RGB_EXPORT_ANCHOR, 1)
        source = source.replace(
            KINETIC_MODEL_RETURN,
            "window.__rc2GeneratedWindow={KineticModel,DEFAULT_WINDOW_OPTIONS,"
            "DEFAULT_OBSERVATORY_OPTIONS};" + KINETIC_MODEL_RETURN,
            1,
        )
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        cls.page = cls.browser.new_page()
        cls.page.set_content(source, wait_until="domcontentloaded", timeout=30000)
        cls.page.wait_for_function(
            "window.fieldGuide && window.__rc2GeneratedWindow", timeout=30000
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def original_state(self, item=None, palette=None, options=None,
                       appearance=None, waveform=None):
        return self.page.evaluate(
            """args => {
              const a=window.__rc2GeneratedWindow, model=new a.KineticModel();
              if(args.appearance)model.spaceWindows.configure(args.appearance);
              if(args.palette)model.palette={...model.palette,...args.palette};
              if(args.options)model.configure(args.options);
              if(args.waveform)model.waveform=args.waveform;
              const item=args.item||{id:'default',title:'Default window'};
              model.spaceWindows.add(item);
              return {item:model.spaceWindows.get(item.id),appearance:model.spaceWindows.options,
                palette:model.palette,options:model.options,waveform:model.waveform,
                paletteRgb:{colors:model.palette.colors.map(window.__rc2Rgb),
                  background:window.__rc2Rgb(model.palette.background),ink:window.__rc2Rgb(model.palette.ink)},
                defaults:a.DEFAULT_WINDOW_OPTIONS,observatoryDefaults:a.DEFAULT_OBSERVATORY_OPTIONS};
            }""",
            {"item": item, "palette": palette, "options": options,
             "appearance": appearance, "waveform": waveform},
        )

    def original_transition_states(self, appearance, item=None):
        return self.page.evaluate(
            """args => {
              const a=window.__rc2GeneratedWindow, model=new a.KineticModel();
              model.spaceWindows.configure(args.appearance);
              const item=args.item||{id:'transition-check',title:'Transition check'};
              model.spaceWindows.add(item);
              const itemWindow=model.spaceWindows.get(item.id), initial={...itemWindow.transition};
              model.spaceWindows.act(item.id,'minimize',0);
              return {initial,afterMinimize:{...itemWindow.transition},options:model.spaceWindows.options};
            }""",
            {"appearance": appearance, "item": item},
        )

    def test_original_model_defaults_and_native_initial_state(self):
        original = self.original_state()
        self.assertEqual(original["item"]["x"], 0)
        self.assertEqual(original["item"]["y"], 0)
        self.assertEqual(original["item"]["z"], 0)
        self.assertEqual(original["item"]["width"], 30)
        self.assertEqual(original["item"]["height"], 16)
        self.assertEqual(original["item"]["content"], "A surface for your application.")
        self.assertEqual(original["item"]["transition"]["effect"], "fade")
        self.assertEqual(original["waveform"], [0] * 128)
        self.assertEqual(original["appearance"]["durationMs"], 850)
        commands = rc2_window_commands({"id": "default", "title": "Default window"})
        self.assertEqual(len(commands), 3)
        self.assertEqual(commands[0]["effect"], "window-transition/glass-dissolve")
        self.assertEqual(commands[0]["durationMs"], 0)
        self.assertEqual(commands[2], {
            "op": "window", "id": commands[0]["id"],
            "effect": "window-transition/lamp-genie", "durationMs": 850,
        })
        self.assertEqual(commands[0]["text"], original["item"]["content"])
        self.assertEqual(commands[1]["text"], original["item"]["content"])

        with NativeScene(2030) as scene:
            for command in commands:
                scene.command(command)
            row = next(w for w in scene.info_complete()["windows"] if w["id"] == commands[0]["id"])
            self.assertEqual(row["position"], [0, 0, 0])
            self.assertEqual(row["visible"], 1)
            self.assertEqual(row["content"]["text"], original["item"]["content"])
            scene.command({"op": "window-action", "id": commands[0]["id"], "action": "minimize"})
            scene.advance_to(425000)
            halfway = next(w for w in scene.info_complete()["windows"] if w["id"] == commands[0]["id"])
            self.assertGreater(halfway["visible"], 0)
            self.assertLess(halfway["visible"], 1)
            scene.advance_to(850000)
            latest = next(w for w in scene.info_complete()["windows"] if w["id"] == commands[0]["id"])
            self.assertEqual(latest["visible"], 0)

    def test_source_pose_utf16_palette_controls_waveform_and_explicit_id(self):
        item = {"id": "Pearl.Signal-1", "title": "PEARL 🚀",
                "content": "Signal 👩\u200d🚀\nMeasured source", "x": 2.5, "y": -3,
                "z": 4, "width": 37, "height": 18, "yaw": 12,
                "pitch": -9, "roll": 4, "shape": "diamond"}
        palette = {"id": "test-palette", "name": "Test", "colors": ["#123456", 0xabcdef],
                   "background": "#010203", "ink": "#f0e0d0"}
        options = {"lightness": .7, "chroma": .21, "brightness": .4,
                   "hueOffset": -12, "feather": .5, "textLightness": .8,
                   "textChroma": .11, "lockLightness": False,
                   "stopWidths": [.5, 2]}
        appearance = {"effect": "roll-up", "durationMs": 725, "chrome": "custom",
                      "shape": "ellipse", "opacity": .63, "depthFade": .02,
                      "overshoot": .22, "folds": 8, "explosionDistance": 17,
                      "anchorX": .75, "anchorY": 1.2, "controlWidth": 7,
                      "controlHeight": 4, "customSide": "left",
                      "customOrder": "background,close,minimize,maximize",
                      "customGlyphs": "◇,×,−,□", "seed": 101}
        waveform = [((i % 19) - 9) / 10 for i in range(128)]
        original = self.original_state(item, palette, options, appearance, waveform)
        self.assertEqual(original["paletteRgb"], {
            "colors": [0x123456, 0xabcdef], "background": 0x010203, "ink": 0xf0e0d0,
        })
        commands = rc2_window_commands(item, source_index=7, options=options,
                                       palette=palette, appearance=appearance,
                                       waveform=waveform, native_id=404)
        window, content, duration = commands
        self.assertEqual(window["id"], 404)
        self.assertEqual(window["position"], [2.5, -3, -4])
        self.assertEqual([window[k] for k in ("width", "height", "yaw", "pitch", "roll")],
                         [37, 18, 12, -9, 4])
        self.assertEqual(window["shape"], "diamond")
        self.assertEqual(window["effect"], "window-transition/glass-dissolve")
        self.assertEqual(window["durationMs"], 0)
        self.assertEqual(duration, {
            "op": "window", "id": 404,
            "effect": "window-transition/scroll-up", "durationMs": 725,
        })
        self.assertEqual(content["sourceIndex"], 7)
        self.assertEqual(content["label"], item["id"])
        self.assertEqual(content["text"], original["item"]["content"])
        self.assertEqual(content["colors"], [0x123456, 0xabcdef])
        self.assertEqual(content["background"], 0x010203)
        self.assertEqual(content["ink"], 0xf0e0d0)
        self.assertEqual(content["waveform"], waveform)
        for key in OPTION_KEYS:
            self.assertEqual(content[key], options[key])

        with NativeScene(2030) as scene:
            for command in commands:
                scene.command(command)
            row = next(w for w in scene.info_complete()["windows"] if w["id"] == 404)
            self.assertEqual(row["position"], [2.5, -3, -4])
            self.assertEqual(row["yaw"], 12)
            self.assertEqual(row["pitch"], -9)
            self.assertEqual(row["roll"], 4)
            self.assertEqual(row["shape"], 4)  # Native window-shape enum: diamond.
            self.assertEqual(row["visible"], 1)
            self.assertEqual(row["content"]["label"], item["id"])
            self.assertEqual(row["content"]["sourceIndex"], 7)
            self.assertEqual(row["content"]["text"], item["content"])
            self.assertEqual(row["content"]["waveform"], waveform)

    def test_configured_explosion_keeps_original_add_fade_and_drives_later_minimize(self):
        item = {"id": "Pearl.Explosion", "title": "Pearl", "shape": "ellipse"}
        appearance = {"effect": "explosion", "durationMs": 850}
        original = self.original_transition_states(appearance, item)
        self.assertEqual(original["options"]["effect"], "explosion")
        self.assertEqual(original["initial"]["effect"], "fade")
        self.assertEqual(original["initial"]["from"], 1)
        self.assertEqual(original["initial"]["to"], 1)
        self.assertEqual(original["initial"]["durationMs"], 0)
        self.assertEqual(original["afterMinimize"]["effect"], "explosion")
        self.assertEqual(original["afterMinimize"]["from"], 1)
        self.assertEqual(original["afterMinimize"]["to"], 0)
        self.assertEqual(original["afterMinimize"]["durationMs"], 850)

        commands = rc2_window_commands(item, appearance=appearance, native_id=405)
        self.assertEqual(commands[0]["effect"], "window-transition/glass-dissolve")
        self.assertEqual(commands[1]["op"], "window-content")
        self.assertEqual(commands[2], {
            "op": "window", "id": 405,
            "effect": "window-transition/shard-burst", "durationMs": 850,
        })
        with NativeScene(2030) as scene:
            for command in commands:
                scene.command(command)
            row = next(w for w in scene.info_complete()["windows"] if w["id"] == 405)
            self.assertEqual(row["visible"], 1)
            self.assertEqual(row["durationUs"], 850000)
            scene.command({"op": "window-action", "id": 405, "action": "minimize"})
            scene.advance_to(425000)
            halfway = next(w for w in scene.info_complete()["windows"] if w["id"] == 405)
            self.assertGreater(halfway["visible"], 0)
            self.assertLess(halfway["visible"], 1)

    def test_long_generated_documents_survive_native_create_attach_and_remove(self):
        documents = (
            "x" * 4096,
            "x" * 4094 + "😀",  # exactly 4096 UTF-16 units, 4095 scalars
        )
        for index, text in enumerate(documents):
            with self.subTest(index=index):
                item = {"id": f"long-{index}", "title": "Long source", "content": text,
                        "x": 1, "y": 2, "z": 3, "width": 30, "height": 16}
                palette = {"colors": ["#123456"], "background": "#010203", "ink": "#f0e0d0"}
                options = {"stopWidths": [.5]}
                appearance = {"durationMs": 850}
                waveform = [0.0] * 128
                before = copy.deepcopy((item, palette, options, appearance, waveform))
                commands = rc2_window_commands(item, palette=palette, options=options,
                                               appearance=appearance, waveform=waveform,
                                               native_id=500 + index)
                self.assertEqual((item, palette, options, appearance, waveform), before)
                self.assertEqual(commands[0]["text"], "")
                self.assertEqual(commands[1]["text"], text)
                with NativeScene(2030) as scene:
                    for command in commands:
                        scene.command(command)
                    row = next(w for w in scene.info_complete()["windows"] if w["id"] == 500 + index)
                    self.assertEqual(row["text"], text)
                    self.assertEqual(row["content"]["text"], text)
                    scene.command({"op": "remove-window-content", "id": 500 + index})
                    fallback = next(w for w in scene.info_complete()["windows"] if w["id"] == 500 + index)
                    self.assertEqual(fallback["text"], "")

    def test_invalid_source_inputs_reject_without_partial_commands(self):
        invalid_items = (
            {"id": "bad id", "title": "Title"},
            {"id": "x" * 65, "title": "Title"},
            {"id": "valid", "title": "x" * 161},
            {"id": "valid", "title": "x" * 159 + "😀"},
            {"id": "valid", "title": "Title", "content": "😀" * 2049},
            {"id": "valid", "title": "Title", "x": 1001},
            {"id": "valid", "title": "Title", "z": 1001},
            {"id": "valid", "title": "Title", "width": 101},
            {"id": "valid", "title": "Title", "yaw": 1001},
            {"id": "valid", "title": "Title", "shape": "cloud"},
            {"id": "valid", "title": "Title", "unexpected": 1},
        )
        for item in invalid_items:
            with self.subTest(item=item), self.assertRaises(ValueError):
                rc2_window_commands(item)
        for kwargs in (
            {"source_index": 32}, {"native_id": 0}, {"native_id": 65536},
            {"palette": {"colors": ["red"]}},
            {"options": {"unknown": 1}},
            {"options": {"stopWidths": [0]}},
            {"appearance": {"unknown": 1}},
            {"appearance": {"durationMs": 5001}},
            {"waveform": [0] * 127},
            {"waveform": [float("nan")] * 128},
            {"waveform": [33] + [0] * 127},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                rc2_window_commands({"id": "valid", "title": "Title"}, **kwargs)


if __name__ == "__main__":
    unittest.main()
