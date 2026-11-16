"""Real unified-SDK coverage for original Atelier text/window applications."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hosts" / "python"))
sys.path.insert(0, str(ROOT / "bindings" / "python"))

from atelier_application import (  # noqa: E402
    ATELIER_TEXT_EFFECTS,
    SPATIAL_WINDOW_EFFECTS,
    TEXT_TRANSITIONS,
    atelier_text_command,
    atelier_window_command,
    atelier_application_commands,
    atelier_prompt_command,
)
from nocturne_native import NativeScene  # noqa: E402
from native.tests.historical_reference import (  # noqa: E402
    RC2_ARCHIVE_SHA256, RC2_HTML_SHA256, load_rc2_archive, load_rc2_workbench,
)


class HistoricalAtelierApplication(unittest.TestCase):
    def scene(self):
        scene = NativeScene(2030)
        self.addCleanup(scene.close)
        return scene

    def test_source_custody_and_complete_original_effect_families(self):
        original_html = load_rc2_workbench().encode("utf-8")
        self.assertEqual(hashlib.sha256(original_html).hexdigest(), RC2_HTML_SHA256)
        sources = {
            ROOT.parent / "legacy/atelier-v0.5/bindings/typescript/window_fx.ts":
                "8845b78de8fe76e98145483667b695d47fcc9d8e71c4f12ca2b329140a04488a",
            ROOT.parent / "bindings/continuity/atelier-text.js":
                "94ecb216860c5256ea3b9b565a9d740f32cec65db8f8458f6dc52999cf78cb47",
            ROOT.parent / "bindings/continuity/kinetic-windows.js":
                "b81a33c320177de29aca912e4e16b3ec4f165c3e95a6d447fca30d9d472545c2",
        }
        for path, expected in sources.items():
            with self.subTest(source=path.name):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
        self.assertEqual(len(ATELIER_TEXT_EFFECTS), 18)
        self.assertEqual(len(SPATIAL_WINDOW_EFFECTS), 43)
        self.assertEqual(len({v for v in ATELIER_TEXT_EFFECTS.values()}), 18)
        self.assertEqual(len({v for v in SPATIAL_WINDOW_EFFECTS.values()}), 43)
        ledger = json.loads((ROOT / "port-ledger.json").read_text())
        expected_text = {row["oldId"].removeprefix("text/"): row["newId"]
                         for row in ledger["entries"] if row.get("nativeContract") == "TextTransition"}
        expected_window = {row["oldId"].removeprefix("window/"): row["newId"]
                           for row in ledger["entries"] if row.get("nativeContract") == "WindowTransition"}
        self.assertEqual(TEXT_TRANSITIONS, expected_text)
        self.assertEqual(SPATIAL_WINDOW_EFFECTS, expected_window)
        edition_ref = json.loads((ROOT / "evidence/gallery-presentation-20261013/original-reference/EDITIONS.json").read_text())
        self.assertEqual(edition_ref["archiveSha256"], RC2_ARCHIVE_SHA256)
        editions = edition_ref["editions"]
        self.assertEqual(len(editions), 32)
        with zipfile.ZipFile(io.BytesIO(load_rc2_archive())) as bundle:
            self.assertEqual(set(bundle.namelist()),
                             {row["entry"] for row in editions} | {"README.txt"})
            for row in editions:
                content = bundle.read(row["entry"])
                with self.subTest(edition=row["entry"]):
                    self.assertEqual(len(content), row["bytes"])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), row["sha256"])
            self.assertEqual(bundle.read("Nocturne-Workbench-Docs.html"), original_html)

    def test_every_original_text_effect_executes_in_native_scene(self):
        for old_effect in ATELIER_TEXT_EFFECTS:
            with self.subTest(effect=old_effect):
                scene = self.scene()
                command = atelier_text_command(
                    "ATELIER / EVERY LETTER HAS A WAY HOME", old_effect,
                    {"durationMs": 1000, "staggerMs": 20, "seed": 6137,
                     "easing": "linear", "trailLength": 0},
                )
                scene.command({"op": "prompt", "active": True, "alpha": 0})
                scene.command({"op": "draft", "text": "NOCTURNE > RETAIN THIS LINE", "emitWeather": False})
                scene.command(command)
                scene.advance_to(410000)
                before = scene.snapshot()
                middle = scene.render().bytes
                self.assertEqual(scene.snapshot(), before, "sampling changed authored state")
                scene.advance_to(1000000)
                settled = scene.render().bytes
                if old_effect != "instant":
                    self.assertNotEqual(middle, settled, "transition did not affect the native frame")
                self.assertEqual(scene.info()["prompt"]["text"], "NOCTURNE > RETAIN THIS LINE")

    def test_native_poses_match_preserved_original_36_effect_formula_samples(self):
        reference = json.loads((ROOT / "tests/fixtures/text-reference.json").read_text())
        self.assertEqual(len(reference["rows"]), 72)
        for path, expected_hash in reference["sources"].items():
            self.assertEqual(hashlib.sha256((ROOT.parent / path).read_bytes()).hexdigest(), expected_hash)
        reverse = {native: old for old, native in TEXT_TRANSITIONS.items()}
        self.assertEqual(len(reverse), 36)
        for row in reference["rows"]:
            old = reverse[row["id"]]
            family, effect = old.split("/", 1)
            base = dict(reference["config"])
            if family == "atelier":
                options = {
                    "durationMs": base["durationMs"], "staggerMs": base["staggerMs"],
                    "delayMs": 0, "batchSize": 1, "seed": base["seed"],
                    "travelRows": base["distance"], "spreadColumns": base["scatter"],
                    "drift": base["wind"], "speedJitter": base["variation"],
                    "alphabet": base["alphabet"], "cycleHz": base["scrambleHz"],
                    "reverseOrder": False, "randomOrder": False,
                    "trailLength": 0, "overshoot": base["overshoot"],
                    "turns": base["cycles"], "hueSpread": base["hueSpread"],
                }
            else:
                options = {**base, "reverseOrder": False,
                           "randomOrder": False, "trailLength": 0, "local": False}
            phase = row["phase"]
            with self.subTest(effect=old, phase=phase):
                scene = self.scene()
                command = atelier_text_command(reference["text"], old, options,
                                               identity=7, x=0, y=0, width=120,
                                               phase=phase)
                if family == "kinetic" and effect in {"fall", "ash"}:
                    self.assertEqual(command["phaseModel"], "source-paint")
                scene.command(command)
                for time_ms, expected in zip(reference["times"], row["poses"]):
                    scene.advance_to(time_ms * 1000)
                    for index, pose in enumerate(expected):
                        native = scene.text_sample(7, index)
                        self.assertEqual(native[0], ord(pose["glyph"]))
                        self.assertAlmostEqual(native[3] / 65536, pose["x"], delta=2 / 65536)
                        self.assertAlmostEqual(native[4] / 65536, pose["y"], delta=2 / 65536)
                        self.assertAlmostEqual(native[5] / 1_000_000, pose["alpha"], delta=.000002)

    def test_kinetic_fall_ash_sampler_semantics_are_distinct_from_native_reverse_show(self):
        for effect in ("kinetic/fall", "kinetic/ash"):
            with self.subTest(effect=effect):
                for phase in ("show", "hide"):
                    command = atelier_text_command("SOURCE PHASE CONTRACT", effect, phase=phase)
                    self.assertEqual(command["phase"], phase)
                    self.assertEqual(command["phaseModel"], "source-paint")
                # Absent mode and explicit reverse-show retain the RC4-native
                # extension; source mode restores RC2's accepted sampler.
                scenes = [self.scene(), self.scene(), self.scene()]
                commands = (
                    {"op": "text", "id": 10, "text": "SOURCE PHASE CONTRACT",
                     "effect": TEXT_TRANSITIONS[effect], "phase": "show"},
                    {"op": "text", "id": 10, "text": "SOURCE PHASE CONTRACT",
                     "effect": TEXT_TRANSITIONS[effect], "phase": "show", "phaseModel": "reverse-show"},
                    {"op": "text", "id": 10, "text": "SOURCE PHASE CONTRACT",
                     "effect": TEXT_TRANSITIONS[effect], "phase": "show", "phaseModel": "source"},
                )
                for scene, command in zip(scenes, commands):
                    scene.command(command)
                    scene.advance_to(370000)
                self.assertEqual(scenes[0].text_sample(10, 0), scenes[1].text_sample(10, 0))
                self.assertNotEqual(scenes[0].text_sample(10, 0), scenes[2].text_sample(10, 0))

    def test_text_phase_model_rejects_unknown_or_unrelated_use_atomically(self):
        scene = self.scene()
        scene.command({"op": "text", "id": 12, "text": "KEEP THE PRIOR LINE",
                       "effect": "text/ink-dissolve"})
        before = scene.snapshot()
        for command in (
            {"op": "text", "id": 12, "effect": "text/glyph-fall", "phaseModel": "invented"},
            {"op": "text", "id": 12, "effect": "text/ink-dissolve", "phaseModel": "source"},
            {"op": "text", "id": 12, "effect": "text/ink-dissolve", "phaseModel": "reverse-show"},
            {"op": "text", "id": 12, "effect": "text/glyph-fall", "phaseModel": "source",
             "phase": "invalid-phase"},
        ):
            with self.subTest(command=command), self.assertRaises((TypeError, ValueError)):
                scene.command(command)
            self.assertEqual(scene.snapshot(), before, "invalid model partially changed text state")

    def test_every_original_spatial_window_effect_executes_with_retained_prompt(self):
        for old_effect in SPATIAL_WINDOW_EFFECTS:
            with self.subTest(effect=old_effect):
                scene = self.scene()
                scene.command({"op": "resize", "width": 84, "height": 30})
                scene.command({"op": "environment", "stars": 0})
                scene.command({"op": "prompt", "active": True, "alpha": 0})
                scene.command({"op": "draft", "text": "NOCTURNE > EDITABLE LOCAL PROMPT", "emitWeather": False})
                window = atelier_window_command(
                    "workbench", old_effect, title="ATELIER / SPATIAL TYPE",
                    text="Every transition keeps its own geometry.\nThe input plane remains local.",
                    position=(0, 1, 0), width=34, height=15, duration_ms=600,
                )
                scene.command(window)
                scene.advance_to(300000)
                moving = scene.render().bytes
                self.assertEqual(scene.info()["prompt"]["text"], "NOCTURNE > EDITABLE LOCAL PROMPT")
                scene.advance_to(600000)
                settled = scene.render().bytes
                self.assertNotEqual(moving, settled)
                scene.command({"op": "window-action", "id": window["id"], "action": "close", "durationMs": 0})
                self.assertEqual(scene.info()["prompt"]["text"], "NOCTURNE > EDITABLE LOCAL PROMPT")
                closed = scene.render().bytes
                self.assertNotEqual(settled, closed, "closed window remained in the scene")
                scene.command({"op": "window-action", "id": window["id"], "action": "restore", "durationMs": 0})
                restored = scene.render().bytes
                self.assertEqual(settled, restored, "restored window changed its settled artwork")

    def test_application_composition_keeps_local_input_above_animated_windows(self):
        commands = atelier_application_commands(
            text="PEARL / signal comes home", text_effect="comet-stitch",
            window_effect="genie", draft="NOCTURNE > typed text is immediate",
        )
        self.assertEqual([c["op"] for c in commands],
                         ["resize", "environment", "prompt", "draft", "window", "text"])
        scene = self.scene()
        for command in commands:
            scene.command(command)
        scene.advance_to(410000)
        initial = scene.snapshot()
        frame = scene.render().bytes
        scene.advance_to(850000)
        final = scene.snapshot()
        settled = scene.render().bytes
        scene.restore(initial)
        self.assertEqual(scene.render().bytes, frame)
        scene.advance_to(850000)
        self.assertEqual(scene.snapshot(), final)
        self.assertEqual(scene.render().bytes, settled)
        self.assertEqual(scene.info()["prompt"]["text"], "NOCTURNE > typed text is immediate")

    def test_prompt_adapter_preserves_rc2_appearance_with_unbounded_default(self):
        defaults = {
            "alpha": .32, "background": "#10161e", "foreground": "#dedbd2",
            "accent": "#8ccfc4", "border": "rounded", "paddingX": 1,
            "paddingY": 0, "margin": 1, "minRows": 1, "maxRows": 7,
            "inlineRows": 12, "inlineWidth": 88, "lineNumbers": True,
            "active": True, "selected": False, "hueStep": 0, "hueSpeed": 0,
            "huePeriodMs": 1000, "maxChars": 0, "selectionColor": "#385763",
        }
        for mode in ("marquee", "grow", "vim-inline", "vim-full"):
            with self.subTest(mode=mode):
                command = atelier_prompt_command(mode)
                self.assertEqual(command["op"], "prompt")
                self.assertEqual(command["mode"], mode)
                self.assertEqual(command["presentation"], "framed")
                self.assertEqual({k: command[k] for k in defaults}, defaults)

        controls = {
            "alpha": .75, "background": "#010203", "foreground": "#a0b0c0",
            "accent": "#c0b0a0", "border": "double", "padding": 3,
            "paddingX": 5, "paddingY": 2, "margin": 4, "minRows": 2,
            "maxRows": 9, "inlineRows": 18, "inlineWidth": 112,
            "lineNumbers": False, "active": False, "selected": True,
            "hueStep": -45.5, "hueSpeed": 90, "huePeriodMs": 250,
            "maxChars": 65536, "selectionColor": "#123456",
        }
        command = atelier_prompt_command("vim-inline", controls)
        for key, expected in controls.items():
            if key != "padding":
                self.assertEqual(command[key], expected, key)
        self.assertEqual((command["paddingX"], command["paddingY"]), (5, 2))
        alias_only = atelier_prompt_command("grow", {"padding": 4})
        self.assertEqual((alias_only["paddingX"], alias_only["paddingY"]), (4, 4))

    def test_prompt_adapter_accepts_source_domain_endpoints(self):
        low = atelier_prompt_command("marquee", {
            "alpha": 0, "paddingX": 0, "paddingY": 0, "margin": 0,
            "minRows": 1, "maxRows": 1, "inlineRows": 5, "inlineWidth": 24,
            "hueStep": -360, "hueSpeed": -360, "huePeriodMs": 1, "maxChars": 1,
            "lineNumbers": False, "active": False, "selected": False,
        })
        high = atelier_prompt_command("vim-full", {
            "alpha": 1, "paddingX": 8, "paddingY": 4, "margin": 6,
            "minRows": 24, "maxRows": 60, "inlineRows": 80, "inlineWidth": 240,
            "hueStep": 360, "hueSpeed": 360, "huePeriodMs": 120000, "maxChars": 65536,
            "lineNumbers": True, "active": True, "selected": True,
        })
        self.assertEqual((low["paddingX"], low["inlineWidth"], low["maxChars"]), (0, 24, 1))
        self.assertEqual((high["paddingX"], high["inlineWidth"], high["maxChars"]), (8, 240, 65536))

    def test_prompt_adapter_rejects_out_of_source_domain(self):
        for controls in (
            {"alpha": True}, {"paddingX": 9}, {"paddingY": 5}, {"margin": 7},
            {"minRows": 8, "maxRows": 7}, {"inlineRows": 4},
            {"inlineWidth": 23}, {"hueStep": 361}, {"hueSpeed": float("nan")},
            {"huePeriodMs": 0}, {"maxChars": -1}, {"maxChars": 0x80000000},
            {"background": "red"}, {"selectionColor": "#12345g"},
            {"lineNumbers": 1}, {"selected": "true"}, {"unsupported": 1},
        ):
            with self.subTest(controls=controls), self.assertRaises((TypeError, ValueError)):
                atelier_prompt_command("marquee", controls)

    def test_application_prompt_defaults_and_custom_controls_are_not_dropped(self):
        defaults = atelier_application_commands(
            text="composition", text_effect="instant", window_effect="fade", draft="local"
        )[2]
        self.assertEqual(defaults, atelier_prompt_command("marquee"))
        custom = atelier_application_commands(
            text="composition", text_effect="instant", window_effect="fade", draft="local",
            prompt_mode="vim-full", prompt_options={"inlineWidth": 120, "hueSpeed": 30},
        )[2]
        self.assertEqual((custom["mode"], custom["inlineWidth"], custom["hueSpeed"]),
                         ("vim-full", 120, 30))

    def test_window_adapter_uses_each_original_family_default_profile(self):
        kinetic = atelier_window_command("k", "kinetic/fade")
        self.assertEqual((kinetic["durationMs"], kinetic["seed"], kinetic["alpha"],
                          kinetic["overshoot"], kinetic["folds"], kinetic["scatter"],
                          kinetic["anchorX"], kinetic["anchorY"]),
                         (850, 2030, .85, .18, 6, 32, .5, 1.15))
        atelier = atelier_window_command("a", "atelier/fade")
        self.assertEqual((atelier["durationMs"], atelier["seed"], atelier["alpha"],
                          atelier["overshoot"], atelier["scatter"], atelier["bend"]),
                         (950, 6001, .88, .18, 24, 9))
        self.assertTrue(kinetic["sourceGeometry"])
        self.assertTrue(atelier["sourceGeometry"])
        with self.assertRaises(ValueError):
            atelier_window_command("k", "kinetic/fade", shape="polygon")
        polygon = atelier_window_command("a", "atelier/fade", shape="polygon")
        self.assertEqual(polygon["polygon"], [[.05,.2],[.35,0],[.9,.12],[1,.8],[.65,1],[0,.85]])

    def test_window_adapter_maps_original_control_names_and_rejects_bad_domains(self):
        kinetic = atelier_window_command(
            "k", "kinetic/explosion", opacity=.4, explosionDistance=99,
            folds=20, anchorX=-2, anchorY=3, overshoot=.7, seed=42,
        )
        self.assertEqual((kinetic["alpha"], kinetic["scatter"], kinetic["folds"],
                          kinetic["anchorX"], kinetic["anchorY"], kinetic["overshoot"],
                          kinetic["seed"]),
                         (.4, 99, 20, -2, 3, .7, 42))
        atelier = atelier_window_command("a", "atelier/genie", bounce=.6,
                                          scatter=80, genieBend=-30)
        self.assertEqual((atelier["overshoot"], atelier["scatter"], atelier["bend"]),
                         (.6, 80, -30))
        source_window = atelier_window_command(
            "k", "kinetic/fade", depthFade=.01, chrome="custom",
            controlWidth=12, controlHeight=5, customSide="left",
            customOrder="background,close,minimize,maximize",
            customGlyphs="◇,×,−,□",
        )
        self.assertTrue(source_window["sourcePresentation"])
        self.assertEqual((source_window["depthFade"], source_window["chrome"],
                          source_window["controlWidth"], source_window["controlHeight"],
                          source_window["customSide"], source_window["customOrder"],
                          source_window["customGlyphs"]),
                         (.01, "custom", 12, 5, "left",
                          "background,close,minimize,maximize", "◇,×,−,□"))
        self.assertFalse(atelier["sourcePresentation"])
        for effect, controls in (
            ("kinetic/fade", {"opacity": 1.1}), ("kinetic/fade", {"explosionDistance": 101}),
            ("kinetic/fade", {"folds": 0}), ("kinetic/fade", {"anchorX": 3.1}),
            ("atelier/fade", {"bounce": .61}), ("atelier/fade", {"genieBend": -31}),
            ("atelier/fade", {"invented": 1}), ("kinetic/fade", {"bounce": .2}),
            ("kinetic/fade", {"genieBend": 2}), ("atelier/fade", {"explosionDistance": 12}),
            ("atelier/fade", {"depthFade": .01}), ("atelier/fade", {"chrome": "custom"}),
            ("atelier/fade", {"controlWidth": 12}), ("atelier/fade", {"customOrder": "close,minimize,maximize,background"}),
            ("atelier/fade", {"fadeFloor": .2}),
        ):
            with self.subTest(effect=effect, controls=controls), self.assertRaises((TypeError, ValueError)):
                atelier_window_command("bad", effect, **controls)

    def test_unknown_styles_and_controls_reject_without_partial_command(self):
        for call in (
            lambda: atelier_text_command("X", "borrowed-style"),
            lambda: atelier_text_command("X", "rain", {"fps": 60}),
            lambda: atelier_text_command("X", "rain", {"seed": True}),
            lambda: atelier_window_command("bad id", "genie"),
            lambda: atelier_window_command("w", "borrowed-style"),
            lambda: atelier_window_command("w", "genie", shape="borrowed-shape"),
        ):
            with self.subTest(call=call), self.assertRaises((TypeError, ValueError)):
                call()


if __name__ == "__main__":
    unittest.main()
