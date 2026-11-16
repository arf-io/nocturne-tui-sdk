"""Public adapter contract against pinned RC2 JavaScript and NativeScene."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hosts" / "python"))
sys.path.insert(0, str(ROOT / "bindings" / "python"))

from atelier_application import atelier_window_command  # noqa: E402
from nocturne_native import NativeScene  # noqa: E402


WINDOW_API_RETURN = (
    "return {WINDOW_SHAPES,WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,"
    "shapeContains,validateWindowOptions,WindowManager,windowVertex};"
)


class HistoricalWindowAdapter(unittest.TestCase):
    def test_adapter_defaults_and_validation_match_original_rc2_chromium(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        source = load_rc2_workbench()
        self.assertEqual(source.count(WINDOW_API_RETURN), 1,
                         "pinned source instrumentation anchor changed")
        exposed = source.replace(
            WINDOW_API_RETURN,
            "window.__windowApi={WINDOW_SHAPES,DEFAULT_WINDOW_OPTIONS,validateWindowOptions,WindowManager};" + WINDOW_API_RETURN,
            1,
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__windowApi", timeout=30000)
            oracle = page.evaluate("""() => {
              const a=window.__windowApi, rejects=x=>{try{a.validateWindowOptions(x);return false}catch(_){return true}};
              const endpoints={durationMs:0,opacity:0,depthFade:0,overshoot:0,folds:1,
                explosionDistance:0,anchorX:-2,anchorY:3,controlWidth:5,controlHeight:3,
                seed:0,chrome:'custom',customSide:'left',
                customOrder:'background,close,minimize,maximize',customGlyphs:'a,b,c,d'};
              const upper={durationMs:5000,opacity:1,depthFade:.08,overshoot:.7,folds:20,
                explosionDistance:100,anchorX:3,anchorY:-2,controlWidth:15,controlHeight:6,
                seed:4294967295};
              let endpointsAccepted=true;try{a.validateWindowOptions(endpoints);a.validateWindowOptions(upper)}catch(_){endpointsAccepted=false}
              const invalid=[{depthFade:-.001},{controlWidth:4},{controlHeight:6.1},{folds:1.5},
                {chrome:'macos'},{customSide:'center'},
                {customOrder:'close,minimize,maximize,maximize'},
                {customOrder:'close,minimize,maximize'},
                {customGlyphs:'a,bb,c,d'},{customGlyphs:'a,\\u0001,c,d'},
                {durationMs:5001},{seed:4294967296},{misspelled:true}];
              let polygonRejected=false;try{a.validateWindowOptions({shape:'polygon'})}catch(_){polygonRejected=true}
              let cloudRejected=false;try{a.validateWindowOptions({shape:'cloud'})}catch(_){cloudRejected=true}
              const m=new a.WindowManager();
              m.configure({chrome:'custom',controlWidth:7,controlHeight:4,customSide:'left',
                customOrder:'background,close,minimize,maximize',customGlyphs:'◇,×,−,□'});
              m.add({id:'adapter-custom',title:'Adapter custom controls'});
              return {shapes:a.WINDOW_SHAPES,defaults:a.DEFAULT_WINDOW_OPTIONS,endpointsAccepted,
                polygonRejected,cloudRejected,customControls:m.controls('adapter-custom').map(c=>({action:c.action,
                  glyph:c.glyph,width:c.width,height:c.height,side:c.side})),
                invalid:invalid.map(rejects)};
            }""")
            defaults = {
                "effect":"genie", "durationMs":850, "chrome":"mac", "shape":"rounded",
                "opacity":.85, "depthFade":.008, "overshoot":.18, "folds":6,
                "explosionDistance":32, "anchorX":.5, "anchorY":1.15,
                "controlWidth":10, "controlHeight":3, "customSide":"right",
                "customOrder":"minimize,maximize,background,close",
                "customGlyphs":"−,□,◇,×", "seed":2030,
            }
            self.assertEqual(oracle["defaults"], defaults)
            self.assertEqual(oracle["shapes"], ["rectangle","rounded","ellipse","hexagon",
                "diamond","capsule","ticket","squircle","petal","wave"])
            self.assertTrue(oracle["polygonRejected"])
            self.assertTrue(oracle["cloudRejected"])
            self.assertEqual(oracle["customControls"], [
                {"action":"background","glyph":"◇","width":7,"height":4,"side":"left"},
                {"action":"close","glyph":"×","width":7,"height":4,"side":"left"},
                {"action":"minimize","glyph":"−","width":7,"height":4,"side":"left"},
                {"action":"maximize","glyph":"□","width":7,"height":4,"side":"left"},
            ])
            self.assertTrue(oracle["endpointsAccepted"])
            self.assertEqual(oracle["invalid"], [True] * 13)
            command = atelier_window_command("rc2-default", "kinetic/fade")
            self.assertTrue(command["sourcePresentation"])
            self.assertEqual({key: command[key] for key in (
                "depthFade", "chrome", "controlWidth", "controlHeight", "customSide",
                "customOrder", "customGlyphs")}, {
                "depthFade":.008, "chrome":"mac", "controlWidth":10, "controlHeight":3,
                "customSide":"right",
                "customOrder":"minimize,maximize,background,close",
                "customGlyphs":"−,□,◇,×",
            })
            browser.close()
        with self.assertRaises(ValueError):
            atelier_window_command("rc2-polygon", "kinetic/fade", shape="polygon")
        with self.assertRaises(ValueError):
            atelier_window_command("rc2-cloud", "kinetic/fade", shape="cloud")

    def test_native_adapter_command_retains_custom_toolbar_and_background_action(self):
        command = atelier_window_command(
            "rc2-custom", "kinetic/fade", duration_ms=0,
            chrome="custom", controlWidth=7, controlHeight=4, customSide="left",
            customOrder="background,close,minimize,maximize", customGlyphs="◇,×,−,□",
            opacity=.63, depthFade=.02,
        )
        scene = NativeScene(2030)
        self.addCleanup(scene.close)
        scene.command({"op":"resize", "width":80, "height":30})
        scene.command(command)
        row = next(w for w in scene.info_complete()["windows"] if w["id"] == command["id"])
        self.assertTrue(row["sourcePresentation"])
        self.assertEqual(row["sourceOptions"], {
            "opacity":.63, "depthFade":.02, "chrome":"custom",
            "controlWidth":7, "controlHeight":4, "customSide":"left",
            "customOrder":["background","close","minimize","maximize"],
            "customGlyphs":[ord("◇"),ord("×"),ord("−"),ord("□")],
        })
        scene.render()
        cell = scene.inspect_character_cell(7, 7)
        self.assertEqual(cell["id"], 0x64000000 | command["id"])
        z_before = row["position"][2]
        scene.command({"op":"pointer", "phase":"down", "x":7, "y":7})
        scene.command({"op":"pointer", "phase":"up", "x":7, "y":7})
        after = next(w for w in scene.info_complete()["windows"] if w["id"] == command["id"])
        self.assertEqual(after["position"][2], z_before - 3)
        self.assertEqual(after["visible"], 1)

    def test_invalid_source_controls_reject_and_atelier_profile_stays_distinct(self):
        invalid = (
            {"depthFade":-.001}, {"depthFade":.0801}, {"controlWidth":4},
            {"controlHeight":6.5}, {"folds":1.5}, {"chrome":"macos"},
            {"customSide":"center"},
            {"customOrder":"close,minimize,maximize,maximize"},
            {"customOrder":"close,minimize,maximize"},
            {"customGlyphs":"a,bb,c,d"}, {"customGlyphs":"a,\x01,c,d"},
            {"sourcePresentation":False,"chrome":"windows"},
            {"sourcePresentation":"true"},
        )
        for patch in invalid:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                atelier_window_command("bad", "kinetic/fade", **patch)
        disabled = atelier_window_command("legacy-kinetic", "kinetic/fade",
                                          sourcePresentation=False)
        self.assertFalse(disabled["sourcePresentation"])
        self.assertNotIn("depthFade", disabled)
        for field in ("depthFade", "chrome", "controlWidth", "controlHeight",
                      "customSide", "customOrder", "customGlyphs"):
            with self.subTest(atelier_field=field), self.assertRaises(ValueError):
                atelier_window_command("bad", "atelier/fade", **{field: {
                    "depthFade":.01, "chrome":"mac", "controlWidth":10,
                    "controlHeight":3, "customSide":"right",
                    "customOrder":"minimize,maximize,background,close",
                    "customGlyphs":"−,□,◇,×",
                }[field]})

        atelier = atelier_window_command(
            "atelier-legacy", "atelier/fade", position=(2,3,4), depth=8,
            bounce=.4, genieBend=11,
        )
        self.assertFalse(atelier["sourcePresentation"])
        self.assertNotIn("sourceOptions", atelier)
        self.assertEqual(atelier["position"], [2,3,12])
        self.assertEqual(atelier["effect"], "window-transition/silk-dissolve")
        self.assertTrue(atelier["sourceGeometry"])
        self.assertEqual(atelier["overshoot"], .4)
        self.assertEqual(atelier["bend"], 11)
        with self.assertRaises(ValueError):
            atelier_window_command("bad", "atelier/fade", sourcePresentation=True)


if __name__ == "__main__":
    unittest.main()
