"""Differential against the preserved RC2 Kinetic sampler in a real browser."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hosts" / "python"))
sys.path.insert(0, str(ROOT / "bindings" / "python"))

from atelier_application import TEXT_TRANSITIONS, atelier_text_command  # noqa: E402
from nocturne_native import NativeScene  # noqa: E402
from native.tests.historical_reference import load_rc2_workbench  # noqa: E402

API_RETURN = "return {TEXT_REVEALS,TEXT_HIDES,DEFAULT_TEXT_OPTIONS,TEXT_CONTROLS,validateTextOptions,textDuration,sampleText,TextActor};"


class OriginalKineticBrowserOracle(unittest.TestCase):
    def test_original_sampler_contract_and_timeline_run_without_native_binding(self):
        from playwright.sync_api import sync_playwright

        source = load_rc2_workbench()
        self.assertEqual(source.count(API_RETURN), 1, "source instrumentation anchor changed")
        exposed = source.replace(
            API_RETURN,
            "window.__historicalTextApi={TEXT_REVEALS,TEXT_HIDES,validateTextOptions,sampleText};" + API_RETURN,
            1,
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__historicalTextApi", timeout=30000)
            result = page.evaluate("""() => {
              const api=window.__historicalTextApi;
              const accepted=[];
              const timelines={};
              const options={durationMs:1000,staggerMs:20,jitterMs:0,batchSize:1,
                distanceRows:6,scatterCols:3,speedVariation:0,scrambleHz:10,
                alphabet:' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',cycles:2,wind:1,
                overshoot:.2,seed:42,easing:'smooth',originX:10,originY:15,
                width:120,hueSpread:10};
              for(const effect of ['fall','ash']) for(const phase of ['reveal','hide']) {
                const checked=api.validateTextOptions({...options,effect,phase});
                accepted.push([checked.effect,checked.phase]);
                timelines[effect+'/'+phase]=[0,11,110,370,990,1800].map(ms=>
                  api.sampleText('N',ms,{...checked}));
              }
              return {accepted,reveal:api.TEXT_REVEALS,hide:api.TEXT_HIDES,timelines};
            }""")
            self.assertEqual(result["accepted"], [
                ["fall", "reveal"], ["fall", "hide"], ["ash", "reveal"], ["ash", "hide"]
            ])
            self.assertNotIn("fall", result["reveal"])
            self.assertNotIn("ash", result["reveal"])
            self.assertIn("fall", result["hide"])
            self.assertIn("ash", result["hide"])
            for effect in ("fall", "ash"):
                for phase in ("reveal", "hide"):
                    with self.subTest(effect=effect, phase=phase):
                        frames = result["timelines"][effect + "/" + phase]
                        self.assertEqual(len(frames), 6)
                        self.assertTrue(all(len(frame) == 1 for frame in frames))
                        self.assertTrue(all(frame[0]["glyph"] for frame in frames))
                        expected_terminal = 1 if phase == "reveal" else 0
                        self.assertEqual(frames[-1][0]["opacity"], expected_terminal)
            self.assertEqual(errors, [])
            browser.close()

    def test_original_sampler_accepts_both_phases_and_matches_native_historical_mode(self):
        from playwright.sync_api import sync_playwright

        source = load_rc2_workbench()
        self.assertEqual(source.count(API_RETURN), 1, "source instrumentation anchor changed")
        exposed = source.replace(
            API_RETURN,
            "window.__historicalTextApi={TEXT_REVEALS,TEXT_HIDES,validateTextOptions,sampleText};" + API_RETURN,
            1,
        )
        errors = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__historicalTextApi", timeout=30000)
            source_contract = page.evaluate("""() => {
              const api = window.__historicalTextApi;
              const accepted = [];
              for (const effect of ['fall', 'ash']) for (const phase of ['reveal', 'hide']) {
                const options = api.validateTextOptions({effect, phase});
                accepted.push([options.effect, options.phase]);
              }
              return {accepted, reveal: api.TEXT_REVEALS, hide: api.TEXT_HIDES};
            }""")
            self.assertEqual(source_contract["accepted"], [
                ["fall", "reveal"], ["fall", "hide"], ["ash", "reveal"], ["ash", "hide"]
            ])
            self.assertNotIn("fall", source_contract["reveal"])
            self.assertNotIn("ash", source_contract["reveal"])
            self.assertIn("fall", source_contract["hide"])
            self.assertIn("ash", source_contract["hide"])

            text = "N"
            source_options = {
                "durationMs": 1000, "staggerMs": 20, "jitterMs": 0,
                "batchSize": 1, "distanceRows": 6, "scatterCols": 3,
                "speedVariation": 0, "scrambleHz": 10,
                "alphabet": " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                "cycles": 2, "wind": 1, "overshoot": .2, "seed": 42,
                "easing": "smooth", "originX": 10, "originY": 15,
                "width": 120, "hueSpread": 10,
            }
            times = (0, 11, 110, 370, 990, 1800)
            for effect in ("fall", "ash"):
                for source_phase, native_phase in (("reveal", "show"), ("hide", "hide")):
                    with self.subTest(effect=effect, source_phase=source_phase):
                        reference = page.evaluate("""({text, effect, phase, options, times}) => {
                          const api = window.__historicalTextApi;
                          return times.map(time => api.sampleText(text, time,
                            api.validateTextOptions({...options, effect, phase})));
                        }""", {
                            "text": text, "effect": effect, "phase": source_phase,
                            "options": source_options, "times": times,
                        })
                        command = atelier_text_command(
                            text, f"kinetic/{effect}", {
                                "durationMs": 1000, "staggerMs": 20, "jitterMs": 0,
                                "batchSize": 1, "distance": 6, "scatter": 3,
                                "variation": 0, "scrambleHz": 10,
                                "alphabet": source_options["alphabet"], "cycles": 2,
                                "wind": 1, "overshoot": .2, "seed": 42,
                                "easing": "smooth", "hueSpread": 10,
                            }, identity=4, x=10, y=15, width=120, phase=native_phase,
                        )
                        self.assertEqual(command["phaseModel"], "source-paint")
                        scene = NativeScene(2030)
                        self.addCleanup(scene.close)
                        scene.command({"op": "resize", "width": 120, "height": 72})
                        scene.command(command)
                        for time_ms, poses in zip(times, reference):
                            scene.advance_to(time_ms * 1000)
                            scene.render()
                            for index, expected in enumerate(poses):
                                actual = scene.text_sample(4, index)
                                self.assertEqual(actual[0], ord(expected["glyph"]))
                                self.assertAlmostEqual(actual[3] / 65536, expected["x"], delta=2 / 65536)
                                self.assertAlmostEqual(actual[4] / 65536, expected["y"], delta=2 / 65536)
                                self.assertAlmostEqual(actual[5] / 1_000_000, expected["opacity"], delta=.000002)
                                if expected["opacity"] > 0:
                                    x = math.floor(expected["x"])
                                    y = math.floor(expected["y"])
                                    self.assertEqual(scene.inspect_character_cell(x, y)["glyph"],
                                                     ord(expected["glyph"]))
            self.assertEqual(errors, [])
            browser.close()


if __name__ == "__main__":
    unittest.main()
