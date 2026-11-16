"""Public RC4 scene-art command, metadata and rendering differential tests.

These use the released NativeScene API surface. They must run only after the
schema-67 public integration has been built; an existing schema-66 library is
stale and is intentionally not used by this test-first batch.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import hashlib
import json
import pathlib
import subprocess
import struct
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bindings/python"))
from nocturne_native import NativeScene  # noqa: E402

EVIDENCE = ROOT / "evidence/original-scenic-restoration-20261013"
MANIFEST = EVIDENCE / "ORIGINAL-WORLD-FRAMES.json"
SCENE_NAMES = ("pearl-cascade", "copper-causeway", "red-shift", "tidal-glass", "silt")
WORLD_FIELDS = (
    "width", "height", "scene", "cameraX", "cameraY", "cameraZ", "yaw", "pitch",
    "roll", "fov", "projection", "span", "flow", "travel", "seed", "redshift",
    "discTilt", "detail", "waterAlpha", "background", "ink", "accent", "secondary", "sampling",
)
WORLD_SCALE = {
    "cameraX":256,"cameraY":256,"cameraZ":256,"yaw":256,"pitch":256,"roll":256,
    "fov":256,"projection":1,"span":256,"flow":1000,"travel":256,"seed":1,
    "redshift":1000,"discTilt":256,"detail":1,"waterAlpha":1000,"background":1,
    "ink":1,"accent":1,"secondary":1,"sampling":1,
}
DETAIL_FIELDS = ("waveHeight","wavelength","windAngle","crossSwell","choppiness","foam","waveSpeed","joinRiver")
DETAIL_SCALE = (256,256,256,1000,1000,1000,1000,1)


def source_command(frame):
    world = dict(zip(WORLD_FIELDS, frame["worldQ"]))
    controls = {
        name: world[name] / scale
        for name, scale in WORLD_SCALE.items()
    }
    detail = {
        name: q / scale
        for name, q, scale in zip(DETAIL_FIELDS, frame["detailQ"], DETAIL_SCALE)
    }
    return {
        "op": "scene-art", "scene": SCENE_NAMES[world["scene"]],
        "width": frame["width"], "height": frame["height"],
        "controls": controls, "detail": detail,
    }


def isolate_scenic_renderer(scene, frame=None):
    """Exclude SDK default layers from original source-art frame parity."""
    world_q = frame["worldQ"] if frame else [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1053726,0,0,0,1]
    scene.command({"op":"environment","presentation":"canvas","stars":0,
                   "background":world_q[19],"sampling":"braille" if world_q[23] else "half",
                   "style":"solid"})
    scene.command({"op":"prompt","active":False})
    scene.command({"op":"floor","enabled":False,"visible":False})


def cells_file_words(path):
    return tuple(struct.iter_unpack("<IIII", pathlib.Path(path).read_bytes()))


def rgb_glyph_words(data):
    """Read only glyph/FG/BG; word four is an RC2 flag in the fixture and an
    RC4 interactive hit ID in public NrCell, so the domains are never equated.
    """
    return tuple(struct.iter_unpack("<III", b"".join(
        data[offset:offset+12] for offset in range(0, len(data), 16)
    )))


class ScenicPublicContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.frames = cls.manifest["frames"]

    def test_all_sixteen_original_frames_through_public_command_and_renderer(self):
        """Public rendering preserves source glyph and both RGB planes for
        defaults, timing, alpha/crest/travel/color/redshift, projection and
        half-sampling variants. Source reducer flags stay a separate oracle.
        """
        self.assertEqual(len(self.frames), 16)
        self.assertEqual(self.manifest["embeddedWasmSha256"],
                         "aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09")
        for fixture in self.frames:
            with self.subTest(frame=fixture["id"]), NativeScene(2030) as scene:
                isolate_scenic_renderer(scene,fixture)
                scene.command(source_command(fixture))
                scene.advance_to(fixture["timeMs"] * 1000)
                actual = scene.render()
                expected = (EVIDENCE / fixture["cellsFile"]).read_bytes()
                self.assertEqual(hashlib.sha256(expected).hexdigest(), fixture["cellsSha256"])
                self.assertEqual((actual.width, actual.height), (fixture["width"], fixture["height"]))
                self.assertEqual(rgb_glyph_words(actual.bytes), rgb_glyph_words(expected))
                # Public hit identities are independently checked as empty for
                # a source-only scene; fixture flags are not hit IDs.
                self.assertTrue(all(cell[3] == 0 for cell in actual.words()))
                source_flags = tuple(cell[3] for cell in struct.iter_unpack("<IIII", expected))
                self.assertTrue(all(flag in (0, 1) for flag in source_flags))
                self.assertEqual(sum(source_flags), fixture["occupiedCells"])

    def test_current_wasm_binding_matches_all_original_frames_and_complete_metadata(self):
        """The shipped TypeScript binding must load a schema-67 artifact and
        reproduce the actual archived RC2 cells, not only the Python host path.
        The runner returns full metadata and cells on disk to keep IPC bounded.
        """
        with tempfile.TemporaryDirectory(prefix="nocturne-scenic-wasm-") as output:
            result = subprocess.run(
                ["node", str(ROOT / "tests/scenic_public_wasm_runner.mjs"), output],
                cwd=ROOT / "bindings/typescript", text=True, capture_output=True,
                check=False,
            )
            partial_report = (pathlib.Path(output) / "report.json")
            diagnostic = result.stdout + result.stderr
            if partial_report.exists():
                diagnostic += "\nPartial WASM errors:\n" + json.dumps(json.loads(partial_report.read_text())["errors"])
            self.assertEqual(result.returncode, 0, diagnostic)
            report = json.loads((pathlib.Path(output) / "report.json").read_text())
            self.assertEqual(report["snapshotSchema"], current_schema())
            self.assertEqual(report["sourceSchema"], current_schema())
            self.assertEqual(len(report["frames"]), 16)
            by_id = {frame["id"]: frame for frame in report["frames"]}
            self.assertEqual(set(by_id), {frame["id"] for frame in self.frames})
            for fixture in self.frames:
                with self.subTest(wasm_frame=fixture["id"]):
                    actual_path = pathlib.Path(output) / by_id[fixture["id"]]["cellsFile"]
                    expected = (EVIDENCE / fixture["cellsFile"]).read_bytes()
                    self.assertEqual(rgb_glyph_words(actual_path.read_bytes()),
                                     rgb_glyph_words(expected))
                    public_ids = tuple(cell[3] for cell in cells_file_words(actual_path))
                    self.assertTrue(all(ident == 0 for ident in public_ids))
                    self.assertEqual(by_id[fixture["id"]]["infoComplete"]["contract"]["snapshotSchema"],
                                     current_schema())

            # Public native and WASM hosts receive the same ordered commands.
            # Compare full mixed output directly while using known material
            # color and a fixed camera to test scenic-depth occlusion.
            mixed = {row["id"]: row for row in report["mixed"]}
            fixture = self.frames[0]

            def native_view():
                scene = NativeScene(2030)
                isolate_scenic_renderer(scene, fixture)
                scene.command(source_command(fixture))
                scene.command({"op":"camera","position":[0,0,96],"yaw":0,"pitch":0,
                               "roll":0,"fov":62,"near":0.1,"far":10000,"orthographic":True})
                scene.command({"op":"material","id":15,"space":"rgb",
                               "channels":{"r":1,"g":0,"b":1},"alpha":1})
                return scene

            baseline = pathlib.Path(output) / mixed["mixed-baseline"]["cellsFile"]
            with native_view() as scene:
                scene.advance_to(20000)
                native_baseline = scene.render().bytes
                self.assertEqual(native_baseline, baseline.read_bytes())

            magenta_counts = {}
            for case, z in (("mesh-near",90),("mesh-far",-1000)):
                with native_view() as scene:
                    scene.command({"op":"mesh","sampling":"braille","triangles":[
                        {"a":[-70,-55,z],"b":[70,-55,z],"c":[0,70,z],"color":0xff00ff,"alpha":1}
                    ]})
                    native_bytes = scene.render().bytes
                wasm_bytes = (pathlib.Path(output) / mixed[case]["cellsFile"]).read_bytes()
                self.assertEqual(native_bytes, wasm_bytes, case)
                magenta_counts[case] = sum(
                    1 for c in struct.iter_unpack("<IIII",native_bytes)
                    if c[1] == 0xff00ff or c[2] == 0xff00ff
                )
            self.assertGreater(magenta_counts["mesh-near"],0)
            self.assertGreater(magenta_counts["mesh-near"],magenta_counts["mesh-far"])

            emitter_args = {"op":"emitter","id":1,"effect":"weather/rain-threads","count":1,
                "runningTimeMs":0,"shape":"point","extent":[0,0,0],"velocity":[0,0,0],
                "spread":[0,0,0],"gravity":[0,0,0],"wind":[0,0,0],"windVariation":[0,0,0],
                "drag":0,"lift":0,"collision":False,"deposit":False,"sizeMin":3,"sizeMax":3,
                "lifetimeMinMs":10000,"lifetimeMaxMs":10000,"material":15,
                "birthFadeMs":0,"deathFadeMs":0,"alpha":1}
            emitter_changed = {}
            for case, z in (("emitter-near",90),("emitter-far",-1000)):
                with native_view() as scene:
                    scene.command({**emitter_args,"position":[0,0,z]})
                    scene.advance_to(20000)
                    self.assertTrue(scene.particles(),case)
                    native_bytes = scene.render().bytes
                    if case == "emitter-far":
                        scene.command({"op":"remove-scene-art"})
                        exposed = scene.render().bytes
                        self.assertTrue(any(c[1] == 0xff00ff for c in struct.iter_unpack("<IIII",exposed)),
                                        "far particle must render when its source occluder is removed")
                        self.assertEqual(exposed,(pathlib.Path(output) / mixed["emitter-far-exposed"]["cellsFile"]).read_bytes())
                wasm_bytes = (pathlib.Path(output) / mixed[case]["cellsFile"]).read_bytes()
                self.assertEqual(native_bytes,wasm_bytes,case)
                b,a = rgb_glyph_words(native_baseline),rgb_glyph_words(native_bytes)
                emitter_changed[case] = sum(before != after for before,after in zip(b,a))
            self.assertGreater(emitter_changed["emitter-near"],0)
            self.assertGreater(emitter_changed["emitter-near"],emitter_changed["emitter-far"])

    def test_partial_patch_scene_switch_rejection_snapshot_and_remove(self):
        with NativeScene(2030) as scene:
            self.assertEqual(scene.info_complete()["environment"]["presentation"],"workbench")
            isolate_scenic_renderer(scene)
            first = self.frames[0]
            scene.command(source_command(first))
            scene.advance_to(2_000_000)
            initial_info = scene.info_complete()
            initial = initial_info["sceneArt"]
            self.assertEqual(initial["scene"], "pearl-cascade")
            self.assertTrue(initial["hasWorldDetail"])
            self.assertEqual(initial["worldQ"], first["worldQ"])
            self.assertEqual(initial["detailQ"], first["detailQ"])
            self.assertEqual((initial["controls"]["width"],initial["controls"]["height"],initial["controls"]["scene"]),(120,40,0))
            self.assertEqual(initial["effective"]["controls"],initial["controls"])
            authored_frame = scene.render().bytes

            scene.command({"op":"scene-art","controls":{"waterAlpha":0.55},"detail":{"foam":0.2}})
            patched = scene.info_complete()["sceneArt"]
            self.assertEqual(patched["scene"], "pearl-cascade")
            self.assertEqual(patched["controls"]["flow"], initial["controls"]["flow"])
            self.assertEqual(patched["controls"]["waterAlpha"], 0.55)
            self.assertEqual(patched["detail"]["waveHeight"], initial["detail"]["waveHeight"])
            self.assertNotEqual(scene.render().bytes, authored_frame)

            saved = scene.snapshot()
            good_frame = scene.render().bytes
            with self.assertRaises(ValueError):
                scene.command({"op":"scene-art","controls":{"waterAlpha":1.01}})
            self.assertEqual(scene.snapshot(), saved)
            self.assertEqual(scene.render().bytes, good_frame)
            with self.assertRaises(ValueError):
                scene.command({"op":"scene-art","scene":"not-a-scene"})
            self.assertEqual(scene.snapshot(), saved)

            scene.command({"op":"scene-art","scene":"tidal-glass","controls":{"detail":2}})
            switched = scene.info_complete()["sceneArt"]
            self.assertEqual(switched["scene"], "tidal-glass")
            self.assertEqual(switched["controls"]["waterAlpha"], 0.55)
            self.assertEqual(switched["controls"]["detail"], 2)
            self.assertNotEqual(scene.render().bytes, good_frame)

            scene.restore(saved)
            self.assertEqual(scene.snapshot(), saved)
            self.assertEqual(scene.render().bytes, good_frame)
            scene.command({"op":"remove-scene-art"})
            self.assertIsNone(scene.info_complete()["sceneArt"])
            self.assertNotEqual(scene.render().bytes, good_frame)
            with self.assertRaises(ValueError):
                scene.command({"op":"remove-scene-art","scene":"silt"})

    def test_canonical_camera_flight_resize_and_presentation_policy(self):
        with NativeScene(2030) as scene:
            isolate_scenic_renderer(scene)
            scene.command({"op":"scene-art","scene":"silt","width":120,"height":40,
                           "controls":{"cameraZ":-96,"yaw":35,"pitch":-22,"fov":62}})
            authored = scene.info_complete()["sceneArt"]["worldQ"]
            scene.command({"op":"flight","steps":[{"kind":"cruise","durationMs":2000,"speed":5}]})
            observed = []
            for time_us in (0,1_000_000,2_000_000):
                scene.advance_to(time_us)
                info = scene.info_complete()
                scenic = info["sceneArt"]
                observed.append(scenic["effective"]["worldQ"][5])
                self.assertEqual(scenic["worldQ"], authored)
                self.assertEqual(scenic["effective"]["worldQ"][5],
                                 round(-info["camera"]["position"][2] * 256))
            self.assertGreater(len(set(observed)), 1)

            scene.command({"op":"resize","width":151,"height":47})
            resized = scene.info_complete()["sceneArt"]
            self.assertEqual((resized["effective"]["width"],resized["effective"]["height"]),(151,47))
            self.assertEqual(resized["effective"]["worldQ"][0:2],[151,47])
            self.assertEqual((resized["effective"]["controls"]["width"],resized["effective"]["controls"]["height"]),(151,47))
            self.assertEqual(resized["worldQ"],authored)
            frame = scene.render()
            self.assertEqual((frame.width,frame.height),(151,47))

            scene.command({"op":"environment","presentation":"workbench"})
            workbench = scene.render()
            scene.command({"op":"environment","presentation":"canvas"})
            canvas = scene.render()
            self.assertEqual((workbench.width,workbench.height),(canvas.width,canvas.height))
            self.assertNotEqual(workbench.bytes,canvas.bytes)
            self.assertEqual(scene.info_complete()["environment"]["presentation"],"canvas")

    def test_explicit_source_camera_patch_samples_flight_pose_and_cancels_flight(self):
        with NativeScene(2030) as scene:
            scene.command({"op":"environment","presentation":"canvas"})
            scene.command({"op":"scene-art","scene":"silt","width":120,"height":40,
                           "controls":{"cameraZ":-96,"yaw":35,"pitch":-22,"fov":62}})
            authored_before = scene.info_complete()["sceneArt"]["worldQ"]
            scene.command({"op":"flight","steps":[{"kind":"cruise","durationMs":2000,"speed":5}]})
            scene.advance_to(750_000)
            flight_pose = scene.info_complete()["camera"]
            self.assertNotEqual(flight_pose["position"],[-68,48,96])

            target_yaw = flight_pose["yaw"] + 11
            scene.command({"op":"scene-art","controls":{"yaw":target_yaw}})
            patched_info = scene.info_complete()
            patched_pose = patched_info["camera"]
            self.assertEqual(patched_pose["position"],flight_pose["position"])
            self.assertEqual(patched_pose["pitch"],flight_pose["pitch"])
            self.assertEqual(patched_pose["yaw"],target_yaw)
            authored_after = patched_info["sceneArt"]["worldQ"]
            self.assertEqual(authored_after[3:6],authored_before[3:6])
            self.assertEqual(authored_after[6],round(target_yaw*256))
            self.assertEqual(authored_after[7:],authored_before[7:])

            scene.advance_to(1_750_000)
            self.assertEqual(scene.info_complete()["camera"],patched_pose,
                             "source camera edit must cancel the prior flight")

    def test_non_camera_source_patch_preserves_existing_flight(self):
        scenes = [NativeScene(2030),NativeScene(2030)]
        try:
            for scene in scenes:
                scene.command({"op":"environment","presentation":"canvas"})
                scene.command({"op":"scene-art","scene":"silt","width":120,"height":40,
                               "controls":{"cameraZ":-96,"yaw":35,"pitch":-22,"fov":62}})
                scene.command({"op":"flight","steps":[{"kind":"cruise","durationMs":2000,"speed":5}]})
                scene.advance_to(750_000)
            unpatched, patched = scenes
            before = unpatched.info_complete()["camera"]
            patched_before = patched.info_complete()["camera"]
            self.assertEqual(patched_before,before)
            authored = patched.info_complete()["sceneArt"]["worldQ"]
            patched.command({"op":"scene-art","controls":{"waterAlpha":0.42},
                             "detail":{"foam":0.3}})
            after_patch = patched.info_complete()
            self.assertEqual(after_patch["camera"],before)
            changed_world = after_patch["sceneArt"]["worldQ"]
            self.assertTrue(all(changed_world[i] == authored[i] for i in range(24) if i != 18))
            self.assertEqual(changed_world[18],420)
            self.assertEqual(after_patch["sceneArt"]["detailQ"][5],300)

            for scene in scenes:
                scene.advance_to(2_000_000)
            self.assertEqual(patched.info_complete()["camera"],unpatched.info_complete()["camera"],
                             "a non-camera source patch must leave flight origin and progress intact")
            self.assertNotEqual(patched.info_complete()["camera"],before)
        finally:
            for scene in scenes:
                scene.close()

    def test_first_source_activation_resets_view_and_cancels_flight(self):
        with NativeScene(2030) as scene:
            scene.command({"op":"flight","steps":[{"kind":"cruise","durationMs":2000,"speed":5}]})
            scene.advance_to(750_000)
            moving = scene.info_complete()["camera"]
            scene.command({"op":"scene-art","scene":"silt"})
            activated = scene.info_complete()
            self.assertEqual(activated["camera"]["position"],[-68,48,96])
            self.assertEqual(activated["camera"]["yaw"],35)
            self.assertEqual(activated["camera"]["pitch"],-22)
            self.assertEqual(activated["sceneArt"]["worldQ"][3:9],[-17408,12288,-24576,8960,-5632,0])
            scene.advance_to(1_750_000)
            self.assertEqual(scene.info_complete()["camera"],activated["camera"],
                             "first source activation must cancel any prior flight")
            self.assertNotEqual(moving,activated["camera"])

    def test_explicit_authored_viewport_and_extreme_valid_canonical_camera(self):
        with NativeScene(2030) as scene:
            isolate_scenic_renderer(scene)
            scene.command({"op":"scene-art","scene":"pearl-cascade","width":91,"height":33,
                           "controls":{"cameraX":-11,"cameraY":9,"cameraZ":-27}})
            original = scene.info_complete()["sceneArt"]
            self.assertEqual(original["worldQ"][0:2],[91,33])
            self.assertEqual((original["controls"]["width"],original["controls"]["height"]),(91,33))
            authored = original["worldQ"]

            scene.command({"op":"camera","position":[16000,-16000,16000],"yaw":36000,
                           "pitch":89.9,"roll":-36000,"near":0.001,"far":10000,
                           "fov":10,"span":0.1,"orthographic":True})
            current = scene.info_complete()["sceneArt"]
            self.assertEqual(current["worldQ"],authored)
            effective = current["effective"]["worldQ"]
            self.assertEqual(effective[3:12],[4096000,-4096000,-4096000,9216000,
                                               23014,-9216000,2560,1,26])
            self.assertEqual(current["effective"]["controls"]["width"],91)
            self.assertEqual(current["effective"]["controls"]["height"],33)
            frame = scene.render()
            self.assertEqual((frame.width,frame.height),(91,33))

            saved = scene.snapshot()
            with self.assertRaises(ValueError):
                scene.command({"op":"camera","yaw":36001})
            self.assertEqual(scene.snapshot(),saved)
            self.assertEqual(scene.render().width,91)

            scene.command({"op":"resize","width":76,"height":29})
            resized = scene.info_complete()["sceneArt"]
            self.assertEqual(resized["worldQ"],authored)
            self.assertEqual(resized["effective"]["worldQ"][0:2],[76,29])


if __name__ == "__main__":
    unittest.main()
