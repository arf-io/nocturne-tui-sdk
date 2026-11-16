"""Pinned real-browser contract for the original RC2 prompt authoring API."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hosts" / "python"))
sys.path.insert(0, str(ROOT / "bindings" / "python"))

from atelier_application import atelier_prompt_command, atelier_window_command  # noqa: E402
from nocturne_native import NativeScene  # noqa: E402

PROMPT_API_RETURN = "return {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument};"


class OriginalPromptBrowserOracle(unittest.TestCase):
    def test_original_browser_defaults_domains_and_geometry_are_preserved(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        source = load_rc2_workbench()
        self.assertEqual(source.count(PROMPT_API_RETURN), 1, "prompt source instrumentation anchor changed")
        exposed = source.replace(
            PROMPT_API_RETURN,
            "window.__historicalPromptApi={PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,promptLayout,PromptDocument};" + PROMPT_API_RETURN,
            1,
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--no-sandbox"],
            )
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__historicalPromptApi", timeout=30000)
            contract = page.evaluate("""() => {
              const api = window.__historicalPromptApi;
              const modes = api.PROMPT_MODES;
              const defaults = api.DEFAULT_PROMPT;
              const accepted = api.validatePrompt({});
              const rejection = patch => {
                try { api.validatePrompt(patch); return false; }
                catch (error) { return error instanceof RangeError; }
              };
              const base = new api.PromptDocument('Type light into this surface.', defaults);
              const geometries = {};
              for (const mode of modes) {
                base.mode = mode;
                const l = api.promptLayout(base, 100, 40);
                geometries[mode] = {rect:l.rect, inner:l.inner, visibleRows:l.visibleRows,
                  border:l.border, numberWidth:l.numberWidth, prefix:l.prefix};
              }
              return {modes, borders:api.PROMPT_BORDERS, defaults, accepted, geometries,
                endpoints:[
                  !!api.validatePrompt({alpha:0,paddingX:0,paddingY:0,margin:0,minRows:1,maxRows:1,inlineRows:5,inlineWidth:24,hueStep:-360,hueSpeed:-360,huePeriodMs:1,maxChars:1,background:'#000000'}),
                  !!api.validatePrompt({alpha:1,paddingX:8,paddingY:4,margin:6,minRows:24,maxRows:60,inlineRows:80,inlineWidth:240,hueStep:360,hueSpeed:360,huePeriodMs:120000,maxChars:65536,selectionColor:'#FFFFFF'})
                ],
                rejected:[
                  rejection({paddingX:9}), rejection({paddingY:5}), rejection({margin:7}),
                  rejection({inlineRows:4}), rejection({inlineWidth:23}), rejection({huePeriodMs:0}),
                  rejection({maxChars:65537}), rejection({minRows:8,maxRows:7}),
                  rejection({background:'red'}), rejection({selected:1}), rejection({misspelled:true})
                ]};
            }""")
            expected_defaults = {
                "alpha": .32, "background": "#10161e", "foreground": "#dedbd2",
                "accent": "#8ccfc4", "border": "rounded", "paddingX": 1,
                "paddingY": 0, "margin": 1, "minRows": 1, "maxRows": 7,
                "inlineRows": 12, "inlineWidth": 88, "lineNumbers": True,
                "active": True, "selected": False, "hueStep": 0, "hueSpeed": 0,
                "huePeriodMs": 1000, "maxChars": 65536, "selectionColor": "#385763",
            }
            self.assertEqual(contract["modes"], ["marquee", "grow", "vim-inline", "vim-full"])
            self.assertEqual(contract["borders"], ["none", "rounded", "square", "double", "heavy"])
            self.assertEqual(contract["defaults"], expected_defaults)
            self.assertEqual(contract["accepted"], expected_defaults)
            self.assertEqual(contract["endpoints"], [True, True])
            self.assertEqual(contract["rejected"], [True] * 11)
            self.assertEqual(contract["geometries"], {
                "marquee": {"rect":{"x":1,"y":35,"width":98,"height":3},
                            "inner":{"x":5,"y":36,"width":92,"height":1},
                            "visibleRows":1,"border":1,"numberWidth":0,"prefix":2},
                "grow": {"rect":{"x":1,"y":35,"width":98,"height":3},
                         "inner":{"x":5,"y":36,"width":92,"height":1},
                         "visibleRows":1,"border":1,"numberWidth":0,"prefix":2},
                "vim-inline": {"rect":{"x":6,"y":26,"width":88,"height":12},
                               "inner":{"x":11,"y":27,"width":81,"height":9},
                               "visibleRows":9,"border":1,"numberWidth":3,"prefix":0},
                "vim-full": {"rect":{"x":1,"y":3,"width":98,"height":35},
                             "inner":{"x":6,"y":4,"width":91,"height":32},
                             "visibleRows":32,"border":1,"numberWidth":3,"prefix":0},
            })
            self.assertEqual(errors, [])
            browser.close()

    def test_all_original_prompt_modes_have_native_command_and_cell_oracles(self):
        expected = {
            "marquee": (1, 35, 98, 3, 5, 36, 92, 1),
            "grow": (1, 35, 98, 3, 5, 36, 92, 1),
            "vim-inline": (6, 26, 88, 12, 11, 27, 81, 9),
            "vim-full": (1, 3, 98, 35, 6, 4, 91, 32),
        }
        for mode, geometry in expected.items():
            with self.subTest(mode=mode):
                command = atelier_prompt_command(mode)
                self.assertEqual(command["presentation"], "framed")
                scene = NativeScene(2030)
                self.addCleanup(scene.close)
                scene.command({"op":"resize", "width":100, "height":40})
                scene.command({"op":"prompt", "layout":"grapheme", **command})
                scene.command({"op":"draft", "text":"Type light into this surface.", "emitWeather":False})
                # The command includes the exact RC2 geometry controls. The public
                # prompt row oracle checks authored text survives layout and paint.
                rows = scene.prompt_layout()
                visible = [row for row in rows if row[7]]
                self.assertTrue(visible)
                self.assertEqual(scene.info()["prompt"]["text"], "Type light into this surface.")
                scene.render()
                body = scene.inspect_character_cell(geometry[4], geometry[5])
                self.assertEqual(body["glyph"], ord("T"), "caret must preserve authored text")
                self.assertEqual(body["foreground"], 0xdedbd2)
                corner = scene.inspect_character_cell(geometry[0], geometry[1])
                self.assertEqual(corner["glyph"], ord("╭"))
                self.assertEqual(corner["foreground"], 0x8ccfc4)
                title = scene.inspect_character_cell(geometry[0] + 3, geometry[1])
                self.assertEqual(title["glyph"], ord("V" if mode.startswith("vim-")
                                                       else "G" if mode == "grow" else "S"))
                if not mode.startswith("vim-"):
                    prefix = scene.inspect_character_cell(geometry[4] - 2, geometry[5])
                    self.assertEqual(prefix["glyph"], ord(">"))

    def test_original_renderer_keeps_frame_chrome_selection_cursor_and_hue(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        source = load_rc2_workbench()
        expose_anchor = "return {PROMPT_IDS,WORKBENCH_SCENES,WorkbenchModel,paintPrompt,WorkbenchRenderer,activateWorkbench};"
        self.assertEqual(source.count(expose_anchor), 1)
        exposed = source.replace(
            expose_anchor,
            "window.__historicalPromptPaint={paintPrompt};" + expose_anchor,
            1,
        )
        exposed = exposed.replace(
            PROMPT_API_RETURN,
            "window.__historicalPromptApi={PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,promptLayout,PromptDocument};" + PROMPT_API_RETURN,
            1,
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--no-sandbox"],
            )
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__historicalPromptApi", timeout=30000)
            visual = page.evaluate("""() => {
              const m=fieldGuide.model, r=fieldGuide.renderer;
              m.width=100; m.height=40; m.motionMs=0; m.dataMs=0;
              const d=m.document; d.mode='marquee'; d.text='Type light into this surface.';
              d.options=window.__historicalPromptApi.validatePrompt({});
              d.vimState='normal'; d.anchor=null; d.caret=0;
              const render=(at)=>{m.motionMs=at; m.dataMs=at; return r.render(m,at);};
              const at0=render(0), first=at0.frame.cells;
              d.caret=2; d.anchor=0; d.vimState='visual';
              const selected=render(0), selectedCells=selected.frame.cells;
              d.options=window.__historicalPromptApi.validatePrompt({hueSpeed:90,huePeriodMs:250});
              d.anchor=null; d.caret=0; d.vimState='normal';
              const hue0=render(0).frame.cells, hue1=render(500).frame.cells;
              const cell=(cells,x,y)=>{const k=(y*100+x)*4;return [...cells.slice(k,k+4)];};
              return {layout:at0.prompt, border:cell(first,1,35), header:cell(first,4,35),
                prefix:cell(first,3,36), body:cell(first,5,36), caretGlyph:cell(first,5,36)[0],
                selected:cell(selectedCells,5,36), selectedNext:cell(selectedCells,8,36),
                hue0:cell(hue0,6,36), hue1:cell(hue1,6,36)};
            }""")
            self.assertEqual(visual["border"][0], ord("╭"))
            self.assertEqual(visual["header"][0], ord("S"))
            self.assertEqual(visual["prefix"][0:2], [ord(">"), 0x8ccfc4])
            self.assertEqual(visual["body"][0], ord("T"), "caret must preserve the typed glyph")
            self.assertNotEqual(visual["selected"][2], visual["selectedNext"][2],
                                "selectionColor must mark selected text only")
            self.assertNotEqual(visual["hue0"][1], visual["hue1"][1],
                                "configured prompt hue motion must change glyph color")
            browser.close()

    def test_original_rc2_window_vertices_match_native_source_geometry(self):
        from playwright.sync_api import sync_playwright
        from native.tests.historical_reference import load_rc2_workbench

        source = load_rc2_workbench()
        window_anchor = "return {WINDOW_SHAPES,WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,shapeContains,validateWindowOptions,WindowManager,windowVertex};"
        self.assertEqual(source.count(window_anchor), 1)
        exposed = source.replace(
            window_anchor,
            "window.__historicalWindowApi={WINDOW_EFFECTS,DEFAULT_WINDOW_OPTIONS,WINDOW_CONTROLS,validateWindowOptions,windowVertex};" + window_anchor,
            1,
        )
        controls = {"durationMs": 850, "shape": "rectangle", "opacity": .85,
                    "depthFade": .008, "overshoot": .24, "folds": 7,
                    "explosionDistance": 27, "anchorX": .2, "anchorY": 1.3,
                    "seed": 42}
        uvs = ((0, 0), (.2, .3), (.5, .5), (.83, .71), (1, 1))
        phases = (0, .04, .08, .23, .5, .91, 1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--no-sandbox"],
            )
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            page.set_content(exposed, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("window.fieldGuide && window.__historicalWindowApi", timeout=30000)
            source_samples = page.evaluate("""({controls,uvs,phases}) => {
              const api=window.__historicalWindowApi,W=30,H=16;
              let acceptedEndpoints=true;
              try { api.validateWindowOptions({durationMs:0,opacity:1,depthFade:.08,overshoot:.7,
                folds:20,explosionDistance:100,anchorX:3,anchorY:-2,controlWidth:15,
                controlHeight:6,seed:4294967295}); }
              catch (_) { acceptedEndpoints=false; }
              const rejects=patch=>{try{api.validateWindowOptions(patch);return false;}catch(_){return true;}};
              return {defaults:api.DEFAULT_WINDOW_OPTIONS, controls:api.WINDOW_CONTROLS,
                acceptedEndpoints, rejected:[rejects({opacity:1.01}),rejects({depthFade:.081}),
                  rejects({overshoot:.71}),rejects({folds:21}),rejects({explosionDistance:101}),
                  rejects({anchorX:3.1}),rejects({controlWidth:16}),rejects({seed:4294967296}),
                  rejects({unknown:1})],
                effects:api.WINDOW_EFFECTS.map(effect=>{
                const options=api.validateWindowOptions({...controls,effect});
                const samples=[];
                for(const p of phases)for(const [u,v] of uvs){
                  const q=api.windowVertex({effect,width:W,height:H,visibility:p,
                    yaw:0,pitch:0,roll:0,x:0,y:0,z:0,opacity:1},u,v,options);
                  samples.push({u,v,p,expected:[q.x,q.y,q.z,q.opacity]});
                }
                return {effect,samples};
              })};
            }""", {"controls": controls, "uvs": uvs, "phases": phases})
            self.assertEqual(source_samples["defaults"], {
                "effect":"genie", "durationMs":850, "chrome":"mac", "shape":"rounded",
                "opacity":.85, "depthFade":.008, "overshoot":.18, "folds":6,
                "explosionDistance":32, "anchorX":.5, "anchorY":1.15,
                "controlWidth":10, "controlHeight":3, "customSide":"right",
                "customOrder":"minimize,maximize,background,close", "customGlyphs":"−,□,◇,×",
                "seed":2030,
            })
            self.assertEqual(source_samples["controls"], {
                "durationMs":[0,5000,25,"ms"], "opacity":[0,1,.01,"mix"],
                "depthFade":[0,.08,.001,"per world unit"],
                "overshoot":[0,.7,.01,"fraction"], "folds":[1,20,1,"folds"],
                "explosionDistance":[0,100,1,"world units"],
                "anchorX":[-2,3,.05,"window widths"], "anchorY":[-2,3,.05,"window heights"],
                "controlWidth":[5,15,1,"cells"], "controlHeight":[3,6,1,"rows"],
                "seed":[0,4294967295,1,"integer"],
            })
            self.assertTrue(source_samples["acceptedEndpoints"])
            self.assertEqual(source_samples["rejected"], [True] * 9)
            self.assertEqual(len(source_samples["effects"]), 21)
            for row in source_samples["effects"]:
                with self.subTest(effect=row["effect"]):
                    command = atelier_window_command(
                        "rc2-" + row["effect"], "kinetic/" + row["effect"],
                        width=30, height=16, shape="rectangle", duration_ms=850,
                        seed=42, opacity=.85, overshoot=.24, folds=7,
                        explosionDistance=27, anchorX=.2, anchorY=1.3,
                    )
                    scene = NativeScene(2030)
                    self.addCleanup(scene.close)
                    scene.command(command)
                    for sample in row["samples"]:
                        actual = scene.window_sample(command["id"], sample["u"],
                                                     sample["v"], sample["p"])
                        observed = [actual[0]/65536, actual[1]/65536,
                                    actual[2]/65536, actual[3]/1_000_000]
                        for axis, (got, expected) in enumerate(zip(observed, sample["expected"])):
                            # Input UV/visibility samples quantize exactly to 1e-6.
                            # Q16 output rounds by <= 1/2 LSB (0.00000763 cells).
                            # For h=2π/4096, linear sine interpolation error is
                            # <=h²/8 + 2^-30 < 2.95e-7. Bounding the combined
                            # trigonometric coefficient L1 norm by 128 cells at
                            # this 30x16 geometry gives <0.0000455 total error.
                            self.assertAlmostEqual(got, expected, delta=.00005,
                                                   msg=f"{sample['p']=}, {sample['u']=}, {sample['v']=}, axis={axis}")
            browser.close()


if __name__ == "__main__":
    unittest.main()
