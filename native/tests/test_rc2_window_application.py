"""Whole original RC2 application oracle: no substituted background or masked chrome."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy
import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "bindings/python"))
from nocturne_native import NativeScene
from native.tests.test_rc2_window_compositions import original_runtime_source
from native.examples.rc2_window_studies import build_rc2_window_studies

WIDTH, HEIGHT = 136, 44


def application_commands(scene_name="windows", options=None, chrome=None):
    study = next(c for c in build_rc2_window_studies() if c["id"] == f"rc2-{scene_name}-isolated")
    commands = copy.deepcopy(study["commands"])
    if chrome:
        for command in commands:
            if command["op"] == "window": command["chrome"] = chrome
    commands.append({"op": "window-application", "paletteWindowId": 1,
                     "scene": scene_name, **(options or {})})
    return commands


def rgb_cells(words):
    return tuple(tuple(words[i:i+3]) for i in range(0, len(words), 4))


class OriginalWindowApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        cls.page = cls.browser.new_page()
        cls.page.set_content(original_runtime_source(), wait_until="domcontentloaded", timeout=30000)
        cls.page.wait_for_function("window.__rc2WindowComposition && window.fieldGuide", timeout=30000)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def original(self, scene_name, time_us, options=None, actions=None, chrome=None, draft="", events=None, particles=None, extra_windows=None):
        return self.page.evaluate("""request => {
          const api=window.__rc2WindowComposition, model=new api.KineticModel();
          model.resize(136,44); model.setScene(request.scene);
          if(request.options)model.configure(request.options);
          if(request.chrome)model.spaceWindows.configure({chrome:request.chrome});
          for(const item of request.extraWindows||[])model.spaceWindows.add(item);
          for(const action of request.actions||[]){
            if(action.timeUs>request.timeUs)continue;
            model.setTime(action.timeUs/1000);
            if(action.kind==='configure')model.configure(action.options);
            else if(action.kind==='select')model.spaceWindows.select(action.id);
            else model.spaceWindows.act(action.id,action.kind,action.timeUs/1000);
          }
          if(request.particles)Object.assign(model.particles,request.particles);
          if(request.events)model.events=request.events;
          model.draft=request.draft; model.setTime(request.timeUs/1000);
          const result=new api.KineticRenderer(fieldGuide.engine).render(model,request.timeUs/1000);
          return {words:Array.from(result.frame.cells),actions:result.actions,
                  windows:model.spaceWindows.list(),notice:model.notice};
        }""", {"scene":scene_name,"timeUs":time_us,"options":options,"actions":actions,
                 "chrome":chrome,"draft":draft,"events":events,"particles":particles,"extraWindows":extra_windows})

    def scene(self, scene_name="windows", options=None, chrome=None):
        library=os.environ.get("NOCTURNE_REVIEW_LIBRARY")
        scene=NativeScene(2030, library=library)
        self.addCleanup(scene.close)
        for command in application_commands(scene_name, options, chrome):scene.command(command)
        return scene

    def assert_original(self, scene, scene_name, time_us, **kwargs):
        before=scene.snapshot()
        actual=list(memoryview(scene.render().bytes).cast("I"))
        self.assertEqual(scene.snapshot(),before,"Rendering changed authoritative state")
        expected=self.original(scene_name,time_us,**kwargs)["words"]
        destination=os.environ.get("NOCTURNE_WINDOW_APPLICATION_CAPTURE_DIR")
        if destination:
            directory=Path(destination);directory.mkdir(parents=True,exist_ok=True)
            key=hashlib.sha256(json.dumps([self._testMethodName,scene_name,time_us,kwargs],sort_keys=True).encode()).hexdigest()[:12]
            with gzip.open(directory/f"{key}.json.gz","wt") as output:
                json.dump({"test":self._testMethodName,"scene":scene_name,"timeUs":time_us,"width":WIDTH,"height":HEIGHT,"configuration":kwargs,"original":expected,"native":actual},output,separators=(",",":"))
        a,b=rgb_cells(actual),rgb_cells(expected)
        differences=[(i,b[i],a[i]) for i in range(len(b)) if a[i]!=b[i]]
        self.assertEqual(len(differences),0,
                         f"{scene_name}@{time_us}: {len(differences)} whole-frame cells differ; first={differences[:12]}")
        return actual

    def test_complete_original_default_windows_and_shapes(self):
        for scene_name in ("windows","shapes"):
            with self.subTest(scene=scene_name):
                scene=self.scene(scene_name)
                for time_us in (0,425000,1700000,1700123):
                    scene.advance_to(time_us)
                    self.assert_original(scene,scene_name,time_us)

    def test_complete_original_chrome_and_window_lifecycle(self):
        ids={"pearl":1,"atlas":2,"iris":3}
        for chrome in ("mac","windows","gnome","custom"):
            with self.subTest(chrome=chrome):
                scene=self.scene(chrome=chrome)
                actions=[]
                for at,kind in ((1000000,"minimize"),(3000000,"restore"),(5000000,"maximize"),(7000000,"close"),(9000000,"restore")):
                    scene.advance_to(at)
                    scene.command({"op":"window-action","id":1,"action":kind})
                    actions.append({"timeUs":at,"kind":kind,"id":"pearl"})
                    scene.advance_to(at+425000)
                    self.assert_original(scene,"windows",at+425000,actions=actions,chrome=chrome)

    def test_original_background_controls_and_sampling(self):
        for style in ("linear","double-axis","wave","plasma","caustics","vortex","contours","aurora","woven","moire","tunnel","diamond","bilinear","checker"):
            with self.subTest(style=style):
                options={"backgroundStyle":style,"gradientAngle":27,"pivotX":.2,"pivotY":.7,"starDensity":.1}
                scene=self.scene(options=options);scene.advance_to(1700000)
                self.assert_original(scene,"windows",1700000,options=options)
        for sampling in ("half","vertical","braille","cell"):
            options={"sampling":sampling,"orbitMode":"pendulum"}
            with self.subTest(sampling=sampling):
                scene=self.scene(options=options);scene.advance_to(1700000)
                self.assert_original(scene,"windows",1700000,options=options)

    def test_dock_controls_target_original_window_and_snapshot_replays(self):
        scene=self.scene();scene.advance_to(1700000)
        frame=scene.render(); words=list(memoryview(frame.bytes).cast("I"))
        # Original first dock button occupies x=3..30,y=35..37 at 136x44.
        self.assertEqual(words[(36*WIDTH+5)*4+3],0x50000001)
        scene.command({"op":"window-action","id":1,"action":"minimize"})
        scene.advance_to(2700000);scene.render()
        scene.command({"op":"pointer","phase":"down","x":5,"y":36})
        scene.command({"op":"pointer","phase":"up","x":5,"y":36})
        scene.advance_to(3700000)
        self.assertTrue(next(w for w in scene.info()["windows"] if w["id"]==1)["visible"]==1)
        saved=scene.snapshot();first=scene.render().bytes
        scene.command({"op":"window-application","backgroundStyle":"checker"})
        scene.restore(saved);self.assertEqual(scene.render().bytes,first)

    def test_original_weather_events_and_automatic_novas(self):
        for kind in ("embers","sparks","nova","rain","snow","ripples"):
            with self.subTest(kind=kind):
                scene=self.scene()
                event={"kind":kind,"id":41,"x":60,"y":20,"atMs":0}
                scene.command({"op":"window-application-event",**event})
                for time_us in (90000,500000,1700000):
                    scene.advance_to(time_us)
                    self.assert_original(scene,"windows",time_us,events=[event])
        for time_us in (20090000,20500000,21700000,40500000):
            with self.subTest(automatic=time_us):
                scene=self.scene();scene.advance_to(time_us)
                self.assert_original(scene,"windows",time_us)

    def test_whole_original_frames_through_import_free_wasm(self):
        studies=[]; expected={}
        for name in ("windows","shapes"):
            studies.append({"id":name,"commands":application_commands(name),"times":[0,425000,1700000,20500000]})
            for t in studies[-1]["times"]:expected[(name,t)]=self.original(name,t)["words"]
        for kind in ("embers","sparks","nova","rain","snow","ripples"):
            event={"kind":kind,"id":41,"x":60,"y":20,"atMs":0}
            studies.append({"id":kind,"commands":application_commands()+[{"op":"window-application-event",**event}],"times":[90000,500000,1700000]})
            for t in studies[-1]["times"]:expected[(kind,t)]=self.original("windows",t,events=[event])["words"]
        with tempfile.TemporaryDirectory() as d:
            request=Path(d)/"request.json";response=Path(d)/"response.json"
            request.write_text(json.dumps(studies))
            subprocess.run(["node",str(ROOT/"tests/rc2_window_application_wasm_runner.mjs"),str(request),str(response)],check=True)
            for frame in json.loads(response.read_text()):
                self.assertEqual(rgb_cells(frame["words"]),rgb_cells(expected[(frame["id"],frame["timeUs"])]),(frame["id"],frame["timeUs"]))

    def test_original_application_gallery_selects_full_renderer(self):
        studies=build_rc2_window_studies()
        for case in studies:
            ops=[c["op"] for c in case["commands"]]
            if case["mode"]=="application":
                self.assertIn("window-application",ops)
                self.assertTrue(all(c.get("text","")=="" for c in case["commands"] if c["op"]=="draft"))
            else:self.assertNotIn("window-application",ops)
        self.assertTrue(next(c for c in studies if c["id"]=="rc2-windows-application")["demo"])

    def test_application_readback_event_capacity_and_old_snapshot_migration(self):
        import struct,zlib
        scene=self.scene()
        self.assertEqual(scene.info()["windowApplication"]["backgroundStyle"],"double-axis")
        for i in range(130):scene.command({"op":"window-application-event","id":i,"kind":"snow","x":2,"y":3})
        app=scene.info()["windowApplication"]
        self.assertEqual(len(app["events"]),128);self.assertEqual(app["events"][0]["id"],2)
        self.assertEqual(app["particles"]["lifeMs"],5000)
        current=scene.snapshot();archived=gzip.decompress((ROOT/"tests/fixtures/window-application-schema69.bin.gz").read_bytes());old=bytearray(archived[:24+15388552])
        struct.pack_into("<I",old,12,0x20261068);struct.pack_into("<I",old,28,0x20261068)
        struct.pack_into("<I",old,16,15388552);struct.pack_into("<I",old,20,zlib.crc32(old[24:]))
        scene.restore(old);self.assertIsNone(scene.info()["windowApplication"])
        scene.restore(current);self.assertEqual(scene.snapshot(),current)

    def test_original_maximized_dock_selects_without_restoring(self):
        scene=self.scene();scene.advance_to(1000000)
        scene.command({"op":"window-action","id":1,"action":"maximize"})
        scene.advance_to(2000000);scene.render()
        scene.command({"op":"pointer","phase":"down","x":5,"y":36})
        scene.command({"op":"pointer","phase":"up","x":5,"y":36})
        scene.advance_to(3000000)
        self.assertEqual(scene.info()["windows"][0]["content"]["maximized"],1)

    def test_original_motion_option_retains_explicit_absolute_clock(self):
        scene=self.scene();actions=[]
        for at,enabled in ((1700000,False),(3700000,True)):
            scene.advance_to(at);scene.command({"op":"window-application","motion":enabled})
            actions.append({"kind":"configure","timeUs":at,"options":{"motion":enabled}})
            scene.advance_to(at+1000000)
            self.assert_original(scene,"windows",at+1000000,actions=actions)

    def test_original_warp_background(self):
        for options in ({"backgroundStyle":"warp"},{"backgroundStyle":"warp","starCount":90,"starSpeed":12,"travelYaw":28,"travelPitch":-12,"trailMs":250}):
            scene=self.scene(options=options)
            for at in (0,1700000,7000000):
                scene.advance_to(at);self.assert_original(scene,"windows",at,options=options)

    def test_rejected_controls_leave_state_unchanged(self):
        scene=self.scene()
        for bad in ({"gradientScreens":0},{"starDensity":1},{"backgroundStyle":"missing"},{"paletteWindowId":999},{"unrecognized":1}):
            with self.subTest(bad=bad):
                before=scene.snapshot()
                with self.assertRaises(ValueError):scene.command({"op":"window-application",**bad})
                self.assertEqual(scene.snapshot(),before)

if __name__ == "__main__":unittest.main()
