"""Real RC2 browser plus live native scene integration for framed prompts."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bindings" / "python"))
sys.path.insert(0, str(ROOT / "hosts" / "python"))

from atelier_application import atelier_prompt_command  # noqa: E402
from nocturne_native import NativeScene  # noqa: E402
from native.tests.historical_reference import load_rc2_workbench  # noqa: E402


class HistoricalFramedPromptIntegration(unittest.TestCase):
    def original_prompt_api(self):
        from playwright.sync_api import sync_playwright

        html = load_rc2_workbench()
        api_anchor = "return {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument};"
        paint_anchor = "return {PROMPT_IDS,WORKBENCH_SCENES,WorkbenchModel,paintPrompt,WorkbenchRenderer,activateWorkbench};"
        self.assertEqual(html.count(api_anchor), 1)
        self.assertEqual(html.count(paint_anchor), 1)
        html = html.replace(api_anchor,
            "window.__rc2PromptApi={PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,promptLayout,PromptDocument};" + api_anchor, 1)
        html = html.replace(paint_anchor,
            "window.__rc2PromptPaint={paintPrompt};" + paint_anchor, 1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__rc2PromptApi && window.__rc2PromptPaint", timeout=30000)
            result = page.evaluate("""() => {
              const api=window.__rc2PromptApi, modes=api.PROMPT_MODES;
              const doc=new api.PromptDocument('Type light into this surface.',api.DEFAULT_PROMPT);
              const geometries={};
              for (const mode of modes) { doc.mode=mode;const l=api.promptLayout(doc,100,40);
                geometries[mode]={rect:l.rect,inner:l.inner,visibleRows:l.visibleRows,
                  border:l.border,numberWidth:l.numberWidth,prefix:l.prefix}; }
              const model=fieldGuide.model,renderer=fieldGuide.renderer;
              model.width=100;model.height=40;model.motionMs=0;model.dataMs=0;
              model.document.text='Type light into this surface.';model.document.mode='marquee';
              model.document.options=api.validatePrompt({});model.document.caret=0;model.document.anchor=null;
              const cells=renderer.render(model,0).frame.cells;
              const cell=(x,y)=>{const i=(y*100+x)*4;return [...cells.slice(i,i+4)];};
              const d=new api.PromptDocument('kept draft',api.DEFAULT_PROMPT);d.setMode('grow');d.setMode('vim-inline');
              const actions=[];d.action('minimize');actions.push([d.mode,d.minimizedMode]);
              d.action('restore');actions.push([d.mode,d.minimizedMode]);
              d.action('maximize');actions.push([d.mode,d.minimizedMode]);
              d.action('close');actions.push([d.mode,d.vimState,d.minimizedMode,d.text]);
              const endpoint=new api.PromptDocument('',api.DEFAULT_PROMPT);
              endpoint.mode='vim-full';endpoint.options=api.validatePrompt({alpha:1,background:'#000000',
                foreground:'#FFFFFF',accent:'#010203',selectionColor:'#A1B2C3',border:'heavy',
                paddingX:8,paddingY:4,margin:6,minRows:24,maxRows:60,inlineRows:80,inlineWidth:240,
                lineNumbers:false,active:false,selected:true,hueStep:-360,hueSpeed:360,
                huePeriodMs:120000,maxChars:65536});
              model.document=endpoint;
              const endpointFrame=renderer.render(model,0).frame.cells;
              const endpointIndex=(4*100+6)*4;
              const endpointCell=Array.from(endpointFrame.slice(endpointIndex,endpointIndex+4));
              return {geometries,border:cell(1,35),title:cell(4,35),prefix:cell(3,36),body:cell(5,36),actions,endpointCell};
            }""")
            browser.close()
        return result

    def scene(self):
        scene = NativeScene(2030)
        self.addCleanup(scene.close)
        scene.command({"op": "resize", "width": 100, "height": 40})
        return scene

    def test_native_geometry_and_frame_cells_match_real_rc2_for_all_modes(self):
        original = self.original_prompt_api()
        modes = ("marquee", "grow", "vim-inline", "vim-full")
        expected = {
            "marquee": (1, 35, 98, 3, 5, 36, 92, 1),
            "grow": (1, 35, 98, 3, 5, 36, 92, 1),
            "vim-inline": (6, 26, 88, 12, 11, 27, 81, 9),
            "vim-full": (1, 3, 98, 35, 6, 4, 91, 32),
        }
        for mode in modes:
            with self.subTest(mode=mode):
                scene = self.scene()
                command = atelier_prompt_command(mode)
                scene.command({"op": "prompt", "layout": "grapheme", **command})
                scene.command({"op": "draft", "text": "Type light into this surface.", "caret": 0, "emitWeather": False})
                scene.render()
                g = expected[mode]
                border = scene.inspect_character_cell(g[0], g[1])
                self.assertEqual(border["glyph"], ord("╭"))
                self.assertEqual(border["foreground"], 0x8ccfc4)
                body = scene.inspect_character_cell(g[4], g[5])
                self.assertEqual(body["glyph"], ord("T"), "source caret must preserve typed ink")
                self.assertEqual(body["foreground"], 0xdedbd2)
                self.assertEqual((body["id"], body["index"]), (0x40000000, 0))
                title = scene.inspect_character_cell(g[0] + 3, g[1])
                self.assertEqual(title["glyph"], ord("V" if mode.startswith("vim-") else "G" if mode == "grow" else "S"))
                source = original["geometries"][mode]
                self.assertEqual((source["rect"]["x"], source["rect"]["y"], source["rect"]["width"], source["rect"]["height"],
                                  source["inner"]["x"], source["inner"]["y"], source["inner"]["width"], source["visibleRows"]), g)
        self.assertEqual(original["border"][0], ord("╭"))
        self.assertEqual(original["title"][0], ord("S"))
        self.assertEqual(original["prefix"][0], ord(">"))
        self.assertEqual(original["body"][0], ord("T"))
        self.assertEqual(original["actions"], [["grow","vim-inline"],["vim-inline",None],
                         ["vim-full",None],["grow","normal",None,"kept draft"]])

    def test_all_source_options_survive_defaults_partial_updates_and_axis_alias(self):
        scene = self.scene()
        scene.command({"op":"prompt", **atelier_prompt_command(options={"hueSpeed":90,"huePeriodMs":250,"padding":2,"paddingY":1})})
        info = scene.info()["prompt"]
        self.assertEqual(info["presentation"], "framed")
        self.assertEqual((info["sourceVimState"], info["minimizedRestoreMode"], info["normalMode"]), (0, 0, 0))
        opts = info["sourceOptions"]
        self.assertEqual(set(opts), {"alpha","background","foreground","accent","selectionColor","border",
            "paddingX","paddingY","margin","minRows","maxRows","inlineRows","inlineWidth",
            "lineNumbers","active","selected","hueStep","hueSpeed","huePeriodMs","maxChars"})
        self.assertEqual((opts["paddingX"], opts["paddingY"]), (2, 1))
        self.assertEqual((opts["hueSpeed"], opts["huePeriodMs"]), (90, 250))
        scene.command({"op":"prompt","presentation":"framed","accent":"#ff00aa"})
        self.assertEqual(scene.info()["prompt"]["sourceOptions"]["hueSpeed"], 90)
        self.assertEqual(scene.info()["prompt"]["sourceOptions"]["accent"], 0xff00aa)

    def test_every_original_option_endpoint_round_trips_in_native_state(self):
        values = {"alpha":1,"background":"#000000","foreground":"#FFFFFF",
            "accent":"#010203","selectionColor":"#A1B2C3","border":"heavy",
            "paddingX":8,"paddingY":4,"margin":6,"minRows":24,"maxRows":60,
            "inlineRows":80,"inlineWidth":240,"lineNumbers":False,"active":False,
            "selected":True,"hueStep":-360,"hueSpeed":360,"huePeriodMs":120000,
            "maxChars":65536}
        scene = self.scene()
        scene.command({"op":"prompt", **atelier_prompt_command("vim-full", values)})
        got = scene.info()["prompt"]["sourceOptions"]
        expected = dict(values)
        for key in ("background","foreground","accent","selectionColor"):
            expected[key] = int(values[key][1:], 16)
        self.assertEqual(got, expected)
        scene.render()
        original = self.original_prompt_api()
        self.assertEqual(scene.inspect_character_cell(6, 4)["glyph"], original["endpointCell"][0])

    def test_compact_is_backward_compatible_and_rejects_framed_only_controls(self):
        compact = self.scene()
        implicit = self.scene()
        compact.command({"op":"prompt","presentation":"compact"})
        compact.command({"op":"draft","text":"plain prompt","emitWeather":False})
        implicit.command({"op":"draft","text":"plain prompt","emitWeather":False})
        self.assertEqual(compact.render().bytes, implicit.render().bytes)
        self.assertEqual(compact.info()["prompt"]["sourceOptions"], None)
        before = compact.snapshot()
        with self.assertRaises(ValueError):
            compact.command({"op":"prompt","presentation":"compact","hueSpeed":20})
        self.assertEqual(compact.snapshot(), before)
        compact.command({"op":"prompt", **atelier_prompt_command(options={"hueSpeed":25})})
        compact.command({"op":"prompt","presentation":"compact"})
        self.assertEqual(compact.info()["prompt"]["presentation"], "compact")
        self.assertIsNone(compact.info()["prompt"]["sourceOptions"])

    def test_selection_hit_and_cursor_keep_document_and_native_editing(self):
        scene = self.scene()
        scene.command({"op":"prompt", **atelier_prompt_command("grow")})
        scene.command({"op":"draft","text":"one two three four five six seven eight nine","caret":0,"emitWeather":False})
        scene.render()
        scene.command({"op":"pointer","phase":"down","x":8,"y":36})
        scene.command({"op":"pointer","phase":"up","x":8,"y":36})
        self.assertEqual(scene.info()["prompt"]["caret"], 3)
        scene.command({"op":"pointer","phase":"down","x":12,"y":36,"shift":True})
        scene.command({"op":"pointer","phase":"up","x":12,"y":36,"shift":True})
        self.assertEqual((scene.info()["prompt"]["anchor"],scene.info()["prompt"]["caret"]),(3,7))
        scene.command({"op":"select","anchor":0,"caret":3})
        self.assertEqual(scene.info()["prompt"]["text"], "one two three four five six seven eight nine")
        scene.render()
        selected = scene.inspect_character_cell(5, 36)
        self.assertEqual(selected["glyph"], ord("o"))
        self.assertNotEqual(selected["background"], 0)
        self.assertNotEqual(selected["background"], scene.inspect_character_cell(8, 36)["background"])
        scene.command({"op":"prompt","layout":"grapheme"})
        scene.command({"op":"draft","text":"e\u0301日本","caret":2,"emitWeather":False})
        scene.command({"op":"key","key":"ArrowRight"})
        self.assertEqual(scene.info()["prompt"]["caret"], 3)
        self.assertEqual(scene.info()["prompt"]["text"], "e\u0301日本")

    def test_original_vim_chrome_actions_and_restore_keep_mode_and_document(self):
        original = self.original_prompt_api()
        self.assertEqual(original["geometries"]["vim-inline"]["rect"],
                         {"x": 6, "y": 26, "width": 88, "height": 12})
        scene = self.scene()
        scene.command({"op":"prompt", **atelier_prompt_command("grow")})
        scene.command({"op":"prompt", **atelier_prompt_command("vim-inline")})
        scene.command({"op":"draft","text":"kept draft","caret":4,"emitWeather":False})
        scene.render()
        # RC2 button groups begin at rect.x + rect.width - 17. The native
        # pointer route uses the same source cell IDs as source paint.
        def click(x, y):
            scene.command({"op":"pointer","phase":"down","x":x,"y":y})
            scene.command({"op":"pointer","phase":"up","x":x,"y":y})
        click(77, 26)  # minimize
        prompt = scene.info()["prompt"]
        self.assertEqual(prompt["mode"], 1, "minimize restores the remembered grow mode")
        self.assertEqual(prompt["minimizedRestoreMode"], 2)
        self.assertEqual(prompt["normalMode"], 1)
        self.assertEqual((prompt["text"], prompt["caret"]), ("kept draft", 4))
        click(8, 35)  # [ VIM restore ]
        self.assertEqual(scene.info()["prompt"]["mode"], 2)
        self.assertEqual(scene.info()["prompt"]["minimizedRestoreMode"], 0)
        click(82, 26)  # maximize toggles inline to fullscreen
        self.assertEqual(scene.info()["prompt"]["mode"], 3)
        click(92, 3)   # close restores normal mode from fullscreen chrome
        prompt = scene.info()["prompt"]
        self.assertEqual(prompt["mode"], 1)
        self.assertEqual(prompt["vimMode"], "normal")
        self.assertEqual(prompt["text"], "kept draft")

    def test_invalid_source_controls_and_queued_invalid_commands_are_atomic(self):
        scene = self.scene()
        before = scene.snapshot()
        for patch in ({"alpha":1.01},{"paddingX":9},{"paddingY":5},{"maxChars":-1},
                      {"border":"unknown"},{"lineNumbers":1},{"presentation":"unknown"}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                scene.command({"op":"prompt","presentation":"framed",**patch})
            self.assertEqual(scene.snapshot(), before)
        with self.assertRaises(ValueError):
            scene.command({"op":"schedule","id":71,"atUs":100000,
                "command":{"op":"batch","commands":[{"op":"prompt","presentation":"framed","maxChars":-1}]}})
        self.assertEqual(scene.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
