"""Real RC2 JavaScript and native differential tests for prompt command mode."""
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


class HistoricalPromptCommandMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright

        html = load_rc2_workbench()
        api_anchor = "return {PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,wrapPrompt,promptLayout,PromptDocument};"
        paint_anchor = "return {PROMPT_IDS,WORKBENCH_SCENES,WorkbenchModel,paintPrompt,WorkbenchRenderer,activateWorkbench};"
        if html.count(api_anchor) != 1 or html.count(paint_anchor) != 1:
            raise AssertionError("Pinned RC2 prompt instrumentation anchors changed")
        html = html.replace(api_anchor,
            "window.__rc2PromptApi={PROMPT_MODES,PROMPT_BORDERS,DEFAULT_PROMPT,validatePrompt,promptLayout,PromptDocument};" + api_anchor, 1)
        html = html.replace(paint_anchor,
            "window.__rc2PromptPaint={paintPrompt};" + paint_anchor, 1)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        cls.page = cls.browser.new_page(viewport={"width": 1400, "height": 900})
        cls.page.set_content(html, wait_until="domcontentloaded", timeout=30000)
        cls.page.wait_for_function("window.fieldGuide && window.__rc2PromptApi && window.__rc2PromptPaint", timeout=30000)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def source(self, script):
        return self.page.evaluate(script)

    def scene(self):
        scene = NativeScene(2031)
        self.addCleanup(scene.close)
        scene.command({"op": "resize", "width": 100, "height": 40})
        scene.command({"op": "prompt", **atelier_prompt_command("vim-inline")})
        scene.command({"op": "draft", "text": "alpha needle / wrapped needle\nomega", "caret": 0, "emitWeather": False})
        return scene

    def test_original_js_command_search_ex_checkpoint_and_visible_status(self):
        result = self.source("""() => {
          const api=window.__rc2PromptApi, paint=window.__rc2PromptPaint.paintPrompt;
          const d=new api.PromptDocument('alpha needle / wrapped needle\\nomega');
          d.mode='vim-inline'; d.normalMode='grow'; d.caret=0;
          const press=key=>d.key({key});
          press(':'); press('w');
          const command=d.command;
          const frame={width:100,height:40,cells:new Uint32Array(100*40*4)};
          for(let i=0;i<frame.cells.length;i+=4){frame.cells[i]=32;frame.cells[i+1]=0xeeeeee;frame.cells[i+2]=0x123456;}
          paint(frame,d,0,fieldGuide.renderer.engine);
          const status=(y,x,n)=>Array.from({length:n},(_,i)=>String.fromCodePoint(frame.cells[(y*100+x+i)*4])).join('');
          const commandRow=status(36,8,16);
          press('Escape'); press('/'); for(const ch of 'needle')press(ch); press('Enter');
          const search={command:d.command,search:d.search,caret:d.caret,vimState:d.vimState};
          const w=new api.PromptDocument('needle then needle');w.mode='vim-inline';w.caret=12;
          w.command='/needle';w.vimState='command';w.key({key:'Enter'});
          const wrapped={search:w.search,caret:w.caret};
          d.caret=10;press('/');for(const ch of 'absent')press(ch);press('Enter');
          const missing={search:d.search,message:d.message,caret:d.caret,vimState:d.vimState};
          d.command=':w';d.vimState='command';press('Enter');
          const written={message:d.message,checkpoint:d.checkpoint,command:d.command,vimState:d.vimState};
          d.command=':wq';d.vimState='command';press('Enter');
          const closed={mode:d.mode,normalMode:d.normalMode,vimState:d.vimState,text:d.text,
            checkpoint:d.checkpoint,search:d.search,message:d.message,command:d.command};
          const e=new api.PromptDocument('one\\ntwo\\nthree');e.mode='vim-inline';e.caret=0;
          e.key({key:':'});e.key({key:'3'});e.key({key:'Enter'});
          const jump={caret:e.caret,options:e.options};
          const q=new api.PromptDocument('kept');q.mode='vim-full';q.normalMode='marquee';
          q.key({key:':'});q.key({key:'q'});q.key({key:'!'});q.key({key:'Enter'});
          return {commandRow,search,wrapped,missing,written,closed,jump,q:{mode:q.mode,text:q.text,command:q.command,
            search:q.search,message:q.message,checkpoint:q.checkpoint}};
        }""")
        self.assertEqual(result["commandRow"][:2], ":w")
        self.assertEqual(result["search"], {"command":"", "search":"needle", "caret":6, "vimState":"normal"})
        self.assertEqual(result["wrapped"], {"search":"needle","caret":0})
        self.assertEqual(result["missing"]["message"], "Pattern not found")
        self.assertEqual(result["written"]["message"], "Checkpoint retained in memory; Export saves to a file.")
        self.assertEqual(result["written"]["checkpoint"]["text"], "alpha needle / wrapped needle\nomega")
        self.assertEqual(result["closed"]["mode"], "grow")
        self.assertEqual(result["closed"]["vimState"], "normal")
        self.assertEqual(result["closed"]["text"], "alpha needle / wrapped needle\nomega")
        self.assertEqual(result["closed"]["search"], "absent")
        self.assertEqual(result["closed"]["checkpoint"]["vimState"], "command")
        self.assertEqual(result["jump"]["caret"], 8)
        self.assertEqual((result["q"]["mode"], result["q"]["text"]), ("marquee", "kept"))

    def test_original_js_escape_backspace_scalar_limit_and_astral_edge(self):
        result = self.source("""() => {
          const D=window.__rc2PromptApi.PromptDocument,d=new D('text');d.mode='vim-inline';
          const press=key=>d.key({key});
          press(':');press('x');press('Backspace');const backspace=d.command;press('Escape');
          press('/');press('😀');press('Backspace');const scalarDelete=d.command;press('Escape');
          press(':');for(let i=0;i<254;i++)press('a');const before=d.command.length;
          press('😀');const afterAstral={units:d.command.length,scalars:[...d.command].length};
          press('z');const afterOverflow={units:d.command.length,scalars:[...d.command].length};
          press('Escape');press(':');for(let i=0;i<255;i++)press('a');press('z');
          return {backspace,scalarDelete,before,afterAstral,afterOverflow,full:{units:d.command.length,scalars:[...d.command].length}};
        }""")
        self.assertEqual(result["backspace"], ":")
        self.assertEqual(result["scalarDelete"], "/")
        self.assertEqual(result["before"], 255)
        self.assertEqual(result["afterAstral"], {"units":257,"scalars":256})
        self.assertEqual(result["afterOverflow"], result["afterAstral"])
        self.assertEqual(result["full"], {"units":256,"scalars":256})

    def test_original_js_ex_subset_and_persistent_reset_rules(self):
        result = self.source("""() => {
          const D=window.__rc2PromptApi.PromptDocument,make=()=>{const d=new D('a\\nb\\nc');d.mode='vim-inline';d.normalMode='grow';return d;};
          const run=(d,keys)=>{d.key({key:':'});for(const key of keys)d.key({key});d.key({key:'Enter'});return d;};
          const numbered=run(make(),['s','e','t',' ','n','u']);
          const settings=run(make(),['s','e','t',' ','n','o','n','u']);
          const help=run(make(),['h','e','l','p']);
          const unknown=run(make(),['z','z']);
          const jump=run(make(),['2']);
          const undo=make();undo.replace('changed',7);run(undo,['u','n','d','o']);
          const redo=make();redo.replace('changed',7);run(redo,['r','e','d','o']);
          const d=make();d.search='b';d.message='old';d.checkpoint={text:'saved'};d.command=':q';d.vimState='command';d.action('minimize');
          const minimized={command:d.command,search:d.search,message:d.message,checkpoint:d.checkpoint,vimState:d.vimState};
          d.action('restore');const restored={command:d.command,vimState:d.vimState,search:d.search,message:d.message,checkpoint:d.checkpoint};
          d.action('close');const closed={command:d.command,search:d.search,message:d.message,checkpoint:d.checkpoint};
          const transition=make();transition.command=':w';transition.vimState='command';transition.setMode('grow');
          const leftVim={command:transition.command,vimState:transition.vimState};
          transition.setMode('vim-full');const reenteredVim={command:transition.command,vimState:transition.vimState};
          const close=run(make(),['q']);const quitForce=run(make(),['q','!']);const exit=run(make(),['x']);
          return {numbered:numbered.options.lineNumbers,settings:settings.options.lineNumbers,help:help.message,unknown:unknown.message,jump:jump.caret,
            close:close.mode,quitForce:quitForce.mode,exit:exit.mode,
            undo:undo.text,redo:redo.text,minimized,restored,closed,leftVim,reenteredVim};
        }""")
        self.assertTrue(result["numbered"])
        self.assertFalse(result["settings"])
        self.assertIn("Close never discards", result["help"])
        self.assertEqual(result["unknown"], "Unsupported command: zz")
        self.assertEqual(result["jump"], 2)
        self.assertEqual((result["close"],result["quitForce"],result["exit"]), ("grow","grow","grow"))
        self.assertEqual(result["undo"], "a\nb\nc")
        self.assertEqual(result["redo"], "changed")
        self.assertEqual(result["minimized"]["command"], ":q")
        self.assertEqual(result["minimized"]["search"], "b")
        self.assertEqual(result["restored"]["command"], ":q")
        self.assertEqual(result["restored"]["vimState"], "normal")
        self.assertEqual(result["closed"]["command"], "")
        self.assertEqual(result["closed"]["search"], "b")
        self.assertEqual(result["closed"]["message"], "old")
        self.assertEqual(result["closed"]["checkpoint"], {"text":"saved"})
        self.assertEqual(result["leftVim"], {"command":":w","vimState":"command"})
        self.assertEqual(result["reenteredVim"], {"command":":w","vimState":"normal"})

    def test_native_command_state_cells_checkpoint_and_compact_compatibility(self):
        scene = self.scene()
        scene.render()
        scene.command({"op":"key","key":":"})
        scene.command({"op":"key","key":"w"})
        prompt = scene.info()["prompt"]
        self.assertEqual(prompt["sourceVimState"], 3)
        self.assertEqual(prompt["sourceCommand"], ":w")
        scene.render()
        self.assertEqual(scene.inspect_character_cell(8,36)["glyph"], ord(":"))
        scene.command({"op":"key","key":"Enter"})
        prompt = scene.info()["prompt"]
        self.assertEqual(prompt["sourceMessage"], "Checkpoint retained in memory; Export saves to a file.")
        self.assertEqual(prompt["sourceCheckpoint"]["text"], "alpha needle / wrapped needle\nomega")
        self.assertEqual(prompt["sourceCheckpoint"]["vimState"], "command")
        scene.render()
        self.assertEqual(scene.inspect_character_cell(8,36)["glyph"], ord("C"))
        snapshot = scene.snapshot()
        restored = self.scene()
        restored.restore(snapshot)
        self.assertEqual(restored.info()["prompt"]["sourceCheckpoint"], prompt["sourceCheckpoint"])
        self.assertEqual(restored.info()["prompt"]["sourceMessage"], prompt["sourceMessage"])
        scene.command({"op":"key","key":"/"})
        for key in "needle":
            scene.command({"op":"key","key":key})
        scene.command({"op":"key","key":"Enter"})
        self.assertEqual(scene.info()["prompt"]["caret"], 6)
        self.assertEqual(scene.info()["prompt"]["sourceSearch"], "needle")
        scene.command({"op":"draft","text":"needle then needle","caret":12,"emitWeather":False})
        scene.command({"op":"key","key":"/"})
        for key in "needle":
            scene.command({"op":"key","key":key})
        scene.command({"op":"key","key":"Enter"})
        self.assertEqual(scene.info()["prompt"]["caret"], 0, "source search wraps forward")
        scene.command({"op":"key","key":"/"})
        for key in "absent":
            scene.command({"op":"key","key":key})
        scene.command({"op":"key","key":"Enter"})
        self.assertEqual(scene.info()["prompt"]["sourceMessage"], "Pattern not found")
        scene.command({"op":"prompt","lineNumbers":True})
        self.assertTrue(scene.info()["prompt"]["sourceOptions"]["lineNumbers"])
        scene.command({"op":"prompt","lineNumbers":False})
        self.assertFalse(scene.info()["prompt"]["sourceOptions"]["lineNumbers"])
        scene.command({"op":"key","key":":"})
        for key in "unsupported":
            scene.command({"op":"key","key":key})
        scene.command({"op":"key","key":"Enter"})
        self.assertEqual(scene.info()["prompt"]["sourceMessage"], "Unsupported command: unsupported")

        compact = NativeScene(2032)
        self.addCleanup(compact.close)
        compact.command({"op":"resize","width":100,"height":40})
        compact.command({"op":"draft","text":"plain","caret":5,"emitWeather":False})
        compact.command({"op":"key","key":":"})
        self.assertEqual(compact.info()["prompt"]["text"], "plain:")

    def test_native_command_key_boundary_and_ex_transitions_match_source(self):
        scene = self.scene()
        # Match the original JS oracle's explicit normalMode='grow'.
        scene.command({"op":"prompt","mode":"grow"})
        scene.command({"op":"prompt","mode":"vim-inline"})
        scene.command({"op":"key","key":":"})
        for _ in range(254):
            scene.command({"op":"key","key":"a"})
        self.assertEqual(len(scene.info()["prompt"]["sourceCommand"]), 255)
        scene.command({"op":"key","key":"😀"})
        self.assertEqual(len(scene.info()["prompt"]["sourceCommand"]), 256)
        scene.command({"op":"key","key":"z"})
        self.assertEqual(len(scene.info()["prompt"]["sourceCommand"]), 256)
        scene.command({"op":"key","key":"Escape"})
        scene.command({"op":"key","key":":"})
        for key in "q!":
            scene.command({"op":"key","key":key})
        scene.command({"op":"key","key":"Enter"})
        prompt = scene.info()["prompt"]
        self.assertEqual((prompt["mode"],prompt["vimMode"]),(1,"normal"))
        self.assertEqual(prompt["text"], "alpha needle / wrapped needle\nomega")
        self.assertEqual(prompt["sourceSearch"], "")

    def test_native_mode_changes_preserve_and_reset_source_command_state(self):
        scene = self.scene()
        scene.command({"op":"key","key":":"})
        scene.command({"op":"key","key":"w"})
        scene.command({"op":"prompt","mode":"grow"})
        prompt = scene.info()["prompt"]
        self.assertEqual((prompt["sourceCommand"],prompt["sourceVimState"]), (":w",3))
        scene.command({"op":"prompt","mode":"vim-full"})
        prompt = scene.info()["prompt"]
        self.assertEqual((prompt["sourceCommand"],prompt["sourceVimState"]), (":w",0))

        scene = self.scene()
        scene.command({"op":"key","key":":"})
        scene.command({"op":"key","key":"w"})
        scene.render()
        def click(x,y):
            scene.command({"op":"pointer","phase":"down","x":x,"y":y})
            scene.command({"op":"pointer","phase":"up","x":x,"y":y})
        click(78,26)
        self.assertEqual((scene.info()["prompt"]["sourceCommand"],scene.info()["prompt"]["sourceVimState"]), (":w",3))
        click(8,35)
        self.assertEqual((scene.info()["prompt"]["sourceCommand"],scene.info()["prompt"]["sourceVimState"]), (":w",0))


if __name__ == "__main__":
    unittest.main()
