"""Camera and coordinate-space acceptance: RC4-016 and the open camera part of RC4-003.

Every expectation below is derived from the written contract, not from current output:

* GOAL-NOCTURNE-1.0.0.md: pivot at the mouse's grabbed scene location, not only a
  centre-of-window rotation; preserve pan, flight, path ownership and input; preserve
  logical dimensions and accurate pointer coordinates in the gallery.
* native/docs/API.md "Time and space" (+X right, +Y up, +Z toward the viewer, forward -Z,
  degrees, cells x-right/y-down) and "Camera rigs and input mapping".
* native/docs/TDD-CAMERA-CONTROLS.md: the mouse-down pick is one fixed world point; orbit
  rotates position and orientation rigidly about it and never moves the pick toward the
  current pointer; pan is an explicit translation.
* native/docs/ORIGINAL-CAMERA.md and TDD-original-camera-graph-sky-20261015.md: the pick
  uses the actual rendered depth, empty background uses the retained target depth, every
  drag retains that world point in perspective and orthographic views, cancellation
  releases the grab, replay and snapshot restore retain behaviour. Every input that ends
  pointer capture releases the grab and commits during a drag in both camera profiles.
* native/docs/TDD-original-workbench-pointer.md:14: "Current native pan dy 0.6 [is]
  intentional current API". No horizontal pan rate is written down, so the pan test asks
  for one constant positive rate along -right in both profiles and projections. Camera
  edits keep flights running; brake is the explicit stop.
* native/docs/RIBBONS.md "Retained native travel": camera path travel owns position while
  its actor exists; look/orientation remains separately authored; remove-path-travel
  leaves the current target position.
* docs/current/Input-and-Motion.md: an explicit anchor is persistent; a null anchor lets a
  pointer gesture pick the actual world surface.
* docs/rc4-contracts7/TDD.md: rendering and info are pure; pointer hit testing uses the
  same rendered cells.
* RC4-BACKLOG.json RC4-016: camera visibility changes no particle identities.

Tolerances. No cell tolerance is written down for the pointer round trip. Public pose
readback has six decimals (ORIGINAL-CAMERA.md); at these scales that bounds analytic
reprojection error far below CELL, the 1e-4 cell precision already used by
test_camera_anchor_default and test_original_camera. Render-grounded checks locate a
landmark by its lit braille dots; one dot is 0.5 x 0.25 cell, so DOT bounds the centroid
of a symmetric landmark. The oracle below is an independent implementation of the written
conventions; the landmark checks tie it to actual rendered output.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import base64
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from native.bindings.python.nocturne_native import NativeScene
from native.examples.original_scenic_routes import build_original_scenic_routes
from native.examples.rc2_window_studies import build_rc2_window_studies

CELL = 1e-4
DOT = 0.3
RADIUS = 1e-5
LANDMARK = 0xfd01fe
BRAILLE_BITS = (1, 8, 2, 16, 4, 32, 64, 128)  # subcell k -> (k % 2, k // 2)
POSE = {'position': [4, 7, 64], 'yaw': 17, 'pitch': -9, 'roll': 13, 'fov': 63, 'span': 100}
PATH = {'op': 'path-travel', 'id': 7, 'target': {'family': 'camera', 'id': 0},
        'points': [[0, 0, 60], [40, 0, 60], [40, 20, 30]], 'speed': 4}
NON_SQUARE = ((120, 48), (97, 23), (40, 60), (203, 31))
POSE_KEYS = ('position', 'yaw', 'pitch', 'roll', 'near', 'far', 'fov', 'span', 'orthographic')


def node_executable():
    return os.environ.get('NODE') or shutil.which('node')


def basis(camera):
    """API.md: forward is -Z before rotations; yaw, pitch, roll in degrees."""
    yaw, pitch, roll = (math.radians(camera[k]) for k in ('yaw', 'pitch', 'roll'))
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    forward = [sy * cp, sp, -cy * cp]
    right0, up0 = [cy, 0, sy], [-sy * sp, cp, cy * sp]
    right = [right0[i] * cr + up0[i] * sr for i in range(3)]
    up = [up0[i] * cr - right0[i] * sr for i in range(3)]
    return right, up, forward


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def project(point, camera, width, height, fov='vertical'):
    """Independent world -> cell oracle for the analytic projections.

    Cells are twice as tall as wide. Perspective field of view is vertical over the
    scene height, horizontal over the scene width when the original profile shows a
    graph, and horizontal over the full screen for the original window application.
    Orthographic span is the world width across the scene viewport.
    """
    right, up, forward = basis(camera)
    d = [point[i] - camera['position'][i] for i in range(3)]
    if camera['orthographic']:
        scale = width / camera['span']
        return [width / 2 + dot(d, right) * scale, height / 2 - dot(d, up) * scale / 2]
    depth = dot(d, forward)
    cot = 1 / math.tan(math.radians(camera['fov']) / 2)
    focal = height * cot if fov == 'vertical' else width * cot / 2
    return [width / 2 + dot(d, right) * focal / depth, height / 2 - dot(d, up) * focal / (2 * depth)]


def landmark(point, camera, half):
    """Two triangles in the camera's right/up plane, centred on a world point."""
    right, up, _ = basis(camera)
    corner = lambda a, b: [point[i] + (a * right[i] + b * up[i]) * half for i in range(3)]
    return [{'a': corner(-1, -1), 'b': corner(1, -1), 'c': corner(1, 1), 'color': LANDMARK, 'alpha': 1},
            {'a': corner(-1, -1), 'b': corner(1, 1), 'c': corner(-1, 1), 'color': LANDMARK, 'alpha': 1}]


def landmark_centroid(frame):
    """Cell-space centroid of every lit braille dot painted in the landmark colour."""
    total_x = total_y = count = 0
    for index, (glyph, foreground, _background, _hit) in enumerate(frame.words()):
        if foreground != LANDMARK or not 0x2800 <= glyph <= 0x28ff:
            continue
        column, row = index % frame.width, index // frame.width
        for k, bit in enumerate(BRAILLE_BITS):
            if glyph & bit:
                total_x += column + (k % 2 + .5) / 2
                total_y += row + (k // 2 + .5) / 4
                count += 1
    return (total_x / count, total_y / count, count) if count else None


def setup_commands(width, height, orthographic=False, profile='default', presentation='canvas',
                   graph=False, rig=False, pose=POSE):
    commands = [{'op': 'resize', 'width': width, 'height': height},
                {'op': 'environment', 'stars': 0, 'presentation': presentation},
                {'op': 'prompt', 'active': False}, {'op': 'floor', 'visible': False},
                {'op': 'camera', **pose, 'orthographic': orthographic, **({'profile': 'original'} if profile == 'original' else {})}]
    if graph:
        commands.append({'op': 'node', 'id': 1, 'label': 'ANCHOR', 'position': [-14, 3, 0], 'pinned': True,
                         'showKind': False, 'showStatus': False, 'showSha': False})
    if rig:
        commands.append({'op': 'camera-controls', 'rig': 'orbit', 'mode': 'orbit', 'anchor': None})
    return commands


def configure(scene, *args, **kwargs):
    commands = setup_commands(*args, **kwargs)
    for command in commands:
        scene.command(command)
    return commands


ANALYTIC_MODES = (
    # name, profile, orthographic, graph, configured rig, perspective field of view
    ('default-perspective', 'default', False, False, False, 'vertical'),
    ('default-orthographic', 'default', True, False, False, 'vertical'),
    ('original-perspective', 'original', False, False, False, 'vertical'),
    ('original-orthographic', 'original', True, False, False, 'vertical'),
    ('original-graph-perspective', 'original', False, True, False, 'horizontal'),
    ('original-graph-orthographic', 'original', True, True, False, 'horizontal'),
    ('configured-orbit-perspective', 'default', False, False, True, 'vertical'),
    ('configured-orbit-orthographic', 'default', True, False, True, 'vertical'),
)


def scenic_commands(route, width, height, projection, profile='original'):
    commands = []
    for command in copy.deepcopy(route['commands']):
        if command['op'] == 'resize':
            command.update(width=width, height=height)
        if command['op'] == 'scene-art':
            command.update(width=width, height=height)
            command['controls']['projection'] = projection
        if profile == 'default' and command['op'] in ('camera', 'camera-controls'):
            continue
        commands.append(command)
    return commands


def window_application_commands(width, height):
    study = next(c for c in build_rc2_window_studies() if c['id'] == 'rc2-windows-isolated')
    commands = copy.deepcopy(study['commands'])
    commands.append({'op': 'window-application', 'paletteWindowId': 1, 'scene': 'windows'})
    commands.append({'op': 'resize', 'width': width, 'height': height})
    commands.append({'op': 'camera', 'profile': 'original', 'position': [0, 2, 48], 'yaw': 0, 'pitch': 0, 'roll': 0})
    return commands


def camera_press(frame, x, y):
    """Nearest press on background, a window body or a graph card.

    Window controls, the prompt and docks keep their own actions (ORIGINAL-CAMERA.md:
    left-button window controls remain available), so they are not camera picks.
    """
    best = None
    for index, word in enumerate(frame.words()):
        if word[3] & 0xff000000 not in (0, 0x10000000, 0x20000000):
            continue
        cx, cy = index % frame.width, index // frame.width
        distance = (cx - int(x)) ** 2 + (cy - int(y)) ** 2
        if best is None or distance < best[0]:
            best = (distance, cx + x - int(x), cy + y - int(y))
    return best[1], best[2]


NR_ID_WINDOW, NR_ID_PROMPT, NR_ID_SOURCE_STAGE = 0x20000000, 0x40000000, 0x65000000


def hit_cell(frame, family, ident=None, near=(0, 0), glyph=None):
    """Press coordinates inside the rendered cell of one hit family (optionally one ID or
    glyph) nearest `near`. Pointer hit testing uses the same rendered cells (TDD.md)."""
    best = None
    for index, word in enumerate(frame.words()):
        if word[3] & 0xff000000 != family or (ident is not None and word[3] & 0xffff != ident) or (glyph and word[0] != ord(glyph)):
            continue
        cx, cy = index % frame.width, index // frame.width
        distance = (cx - near[0]) ** 2 + (cy - near[1]) ** 2
        if best is None or distance < best[0]:
            best = (distance, cx + .3, cy + .4)
    if best is None:
        raise AssertionError(f'no rendered cell of hit family {family:#x}')
    return best[1], best[2]


def second_press_cases():
    """Presses during a camera grab that end its capture or start a different gesture.

    Each row: label, logical size, setup, press target, button, shift. The target is a hit
    family with an optional ID or glyph, or a fixed cell. The framed prompt uses the RC2
    vim-inline chrome at 100x40, rect (6, 26, 88, 12): its button group begins at
    rect.x + rect.width - 17, so (77, 26) is MINIMIZE (test_historical_prompt_framed_integration).
    """
    window = {'op': 'window', 'id': 1, 'title': 'W', 'position': [-30, 10, 0], 'width': 20, 'height': 10}
    stage = {'op': 'source-stage-component', 'id': 1, 'legacyFlags': 100001, 'kind': 'button', 'x': 2, 'y': 3, 'width': 10, 'height': 3}
    return [
        ('selected reader window', (120, 48), [window, {'op': 'window-action', 'id': 1, 'action': 'read'}], (NR_ID_WINDOW, 1, None), 1, False),
        ('source-stage control', (120, 48), [stage], (NR_ID_SOURCE_STAGE, None, None), 0, False),
        ('framed prompt minimize', (100, 40), [{'op': 'prompt', 'active': True}, {'op': 'prompt', 'presentation': 'framed', 'mode': 'vim-inline'}],
         (77.3, 26.4), 0, False),
        ('prompt selection', (120, 48), [{'op': 'prompt', 'active': True}, {'op': 'draft', 'text': 'hello world'}], (NR_ID_PROMPT, None, 'w'), 0, False),
        ('window drag', (120, 48), [window, {'op': 'time', 'timeUs': 2000000}], (NR_ID_WINDOW, 1, None), 0, False),
        ('shift pan', (120, 48), [], (0, None, None), 0, True),
    ]


def second_press_points(frame, target, width, height):
    """The first (camera) press on empty background, then the second press target."""
    first = hit_cell(frame, 0, near=(width * .8, height * .4))
    if isinstance(target[0], float):
        return first, target
    return first, hit_cell(frame, target[0], target[1], near=(width / 2, height / 2), glyph=target[2])


def drag_paths(x, y):
    """Several distinct gestures: straight, steep, zigzag, a closed loop and large jumps."""
    return {
        'horizontal': [(x + i * 1.5, y) for i in range(1, 13)],
        'vertical': [(x, y + i * 2.5) for i in range(1, 17)],
        'zigzag': [(x + i * .7 + (3 if i % 2 else -3), y + i * .4) for i in range(1, 25)],
        'loop': [(x + 8 * math.cos(t / 8 * math.pi) - 8, y + 5 * math.sin(t / 8 * math.pi)) for t in range(1, 17)],
        'jumps': [(x + 40, y - 10), (x - 35, y + 12), (x + 5, y - 20), (x, y)],
    }


class CameraCoordinateSpaceAcceptance(unittest.TestCase):
    def assertCell(self, actual, expected, tolerance, message=''):
        self.assertLessEqual(max(abs(actual[0] - expected[0]), abs(actual[1] - expected[1])), tolerance,
                             f'{message}: {actual} vs {expected}')

    def assertRestorable(self, scene):
        saved = scene.snapshot()
        with NativeScene(2030) as fresh:
            fresh.restore(saved)
            self.assertEqual(fresh.snapshot(), saved)

    # Rule: screen cell -> scene point -> screen cell, every projection, non-square sizes.
    def test_screen_point_round_trip_in_every_analytic_projection_and_logical_size(self):
        fractions = ((.13, .21), (.71, .18), (.37, .83), (.9, .62), (.5, .5))
        for name, profile, orthographic, graph, rig, fov in ANALYTIC_MODES:
            for width, height in NON_SQUARE:
                with self.subTest(mode=name, size=(width, height)), NativeScene(2030) as scene:
                    configure(scene, width, height, orthographic, profile, graph=graph, rig=rig)
                    for fx, fy in fractions:
                        x, y = width * fx + .3, height * fy + .4
                        scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y})
                        camera = scene.info()['camera']
                        self.assertIsNotNone(camera['grabbed'], 'a camera press must pick a world point')
                        self.assertCell(project(camera['grabbed'], camera, width, height, fov), (x, y), CELL, f'{name} pick')
                        scene.command({'op': 'pointer', 'phase': 'cancel', 'x': x, 'y': y})
                        self.assertIsNone(scene.info()['camera']['grabbed'], 'cancellation releases the grab')
        for width, height in ((136, 44), (151, 47)):
            with self.subTest(mode='original-window-application', size=(width, height)), NativeScene(2030) as scene:
                for command in window_application_commands(width, height):
                    scene.command(command)
                frame = scene.render()
                for fx, fy in fractions:
                    x, y = camera_press(frame, width * fx + .3, height * fy + .4)
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y})
                    camera = scene.info()['camera']
                    self.assertIsNotNone(camera['grabbed'])
                    self.assertCell(project(camera['grabbed'], camera, width, height, 'horizontal'), (x, y), CELL, 'window application pick')
                    scene.command({'op': 'pointer', 'phase': 'cancel', 'x': x, 'y': y})
        for width, height in ((136, 44), (151, 47)):
            with self.subTest(mode='original-window-application-orthographic', size=(width, height)), \
                    NativeScene(2030) as scene, NativeScene(2030) as perspective:
                for s in (scene, perspective):
                    for command in window_application_commands(width, height):
                        s.command(command)
                scene.command({'op': 'camera', 'orthographic': True})
                self.assertTrue(scene.info()['camera']['orthographic'])
                frame = scene.render()
                self.assertEqual(frame.bytes, perspective.render().bytes,
                                 'the window application renders through its perspective-only source projection')
                for fx, fy in fractions:
                    x, y = camera_press(frame, width * fx + .3, height * fy + .4)
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y})
                    camera = scene.info()['camera']
                    self.assertIsNotNone(camera['grabbed'])
                    self.assertCell(project(camera['grabbed'], {**camera, 'orthographic': False}, width, height, 'horizontal'), (x, y), CELL,
                                    'so its picks use the same perspective inverse')
                    scene.command({'op': 'pointer', 'phase': 'cancel', 'x': x, 'y': y})

    # Rule: the same round trip grounded in actual rendered output, including source scenes.
    def test_rendered_landmark_round_trip_screen_scene_screen(self):
        cases = [(name, profile, orthographic, graph, rig, fov, 'canvas', size)
                 for name, profile, orthographic, graph, rig, fov in ANALYTIC_MODES for size in ((97, 31), (61, 44))]
        cases += [('workbench-' + kind, 'default', kind == 'orthographic', False, False, None, 'workbench', (97, 31))
                  for kind in ('perspective', 'orthographic')]
        for name, profile, orthographic, graph, rig, fov, presentation, (width, height) in cases:
            with self.subTest(mode=name, presentation=presentation, size=(width, height)), NativeScene(2030) as scene:
                configure(scene, width, height, orthographic, profile, presentation, graph=graph, rig=rig)
                camera = scene.info()['camera']
                right, up, forward = basis(camera)
                depth = 40
                point = [camera['position'][i] + forward[i] * depth + right[i] * 4 + up[i] * 2 for i in range(3)]
                self.landmark_round_trip(scene, camera, point, 1.0, depth,
                                         None if fov is None else (lambda p, c: project(p, c, width, height, fov)))
        for route in build_original_scenic_routes()[:2]:
            for projection in (0, 1):
                for width, height in ((160, 52), (121, 37)):
                    with self.subTest(mode='scene-art', scene=route['id'], projection=projection, size=(width, height)), NativeScene(2030) as scene:
                        for command in scenic_commands(route, width, height, projection):
                            scene.command(command)
                        scene.render()
                        camera = scene.info()['camera']
                        right, up, forward = basis(camera)
                        distance = math.dist(camera['position'], camera['target'])
                        depth = distance * .35
                        point = [camera['position'][i] + forward[i] * depth + right[i] * distance * .05 + up[i] * distance * .02 for i in range(3)]
                        self.landmark_round_trip(scene, camera, point, distance * .02, depth, None)

    def landmark_round_trip(self, scene, camera, point, half, depth, oracle):
        scene.command({'op': 'mesh', 'sampling': 'braille', 'triangles': landmark(point, camera, half)})
        first = landmark_centroid(scene.render())
        self.assertIsNotNone(first, 'the authored landmark must actually render')
        self.assertGreaterEqual(first[2], 4)
        if oracle:
            self.assertCell(oracle(point, camera), first[:2], DOT, 'oracle agrees with the renderer')
        scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': first[0], 'y': first[1]})
        grabbed = scene.info()['camera']['grabbed']
        self.assertIsNotNone(grabbed)
        _, _, forward = basis(camera)
        self.assertAlmostEqual(dot([grabbed[i] - camera['position'][i] for i in range(3)], forward), depth, delta=.01,
                               msg='the pick uses the rendered landmark depth')
        scene.command({'op': 'pointer', 'phase': 'cancel', 'x': first[0], 'y': first[1]})
        scene.command({'op': 'mesh', 'sampling': 'braille', 'triangles': landmark(grabbed, camera, half)})
        second = landmark_centroid(scene.render())
        self.assertIsNotNone(second, 'a landmark at the picked point must render')
        self.assertCell(second[:2], first[:2], DOT, 'picked scene point renders back under the pointer')

    # Rule: pivot at the grabbed scene location, held at its press pixel through every drag.
    def test_pivot_at_grab_holds_the_picked_point_at_its_press_pixel_on_several_paths(self):
        modes = [m for m in ANALYTIC_MODES]
        for name, profile, orthographic, graph, rig, fov in modes:
            for width, height in ((120, 48), (83, 37)):
                x0, y0 = width * .3 + .3, height * .35 + .4
                for path, points in drag_paths(x0, y0).items():
                    with self.subTest(mode=name, size=(width, height), path=path), NativeScene(2030) as scene:
                        configure(scene, width, height, orthographic, profile, graph=graph, rig=rig)
                        before = scene.info()['camera']
                        scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x0, 'y': y0})
                        grabbed = scene.info()['camera']['grabbed']
                        self.assertIsNotNone(grabbed)
                        radius = math.dist(before['position'], grabbed)
                        right, up, forward = basis(before)
                        centre = [before['position'][i] + forward[i] * dot([grabbed[k] - before['position'][k] for k in range(3)], forward) for i in range(3)]
                        for x, y in points:
                            scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x, 'y': y})
                            camera = scene.info()['camera']
                            self.assertEqual(camera['grabbed'], grabbed, 'no re-pick after the first input')
                            self.assertCell(project(grabbed, camera, width, height, fov), (x0, y0), CELL,
                                            f'{name}/{path}: the grabbed point must stay at its press pixel')
                            self.assertAlmostEqual(math.dist(camera['position'], grabbed), radius, delta=RADIUS * max(1, radius))
                        if path == 'horizontal':
                            moved = project(centre, camera, width, height, fov)
                            self.assertGreater(math.dist(moved, (width / 2, height / 2)), .05,
                                               'the pivot is the grabbed point, not the window centre')
                        scene.command({'op': 'pointer', 'phase': 'up', 'x': x, 'y': y})
                        self.assertIsNone(scene.info()['camera']['grabbed'])

    # Rule: centre-of-window rotation remains available where documented.
    def test_centre_of_window_rotation_remains_available_where_documented(self):
        for orthographic in (False, True):
            for width, height in ((120, 48), (97, 23)):
                with self.subTest(case='original rotate and views', orthographic=orthographic, size=(width, height)), NativeScene(2030) as scene:
                    configure(scene, width, height, orthographic, 'original')
                    camera = scene.info()['camera']
                    target = camera['target']
                    distance = math.dist(camera['position'], target)
                    actions = [{'action': 'rotate', 'yaw': 23, 'pitch': -11}, {'action': 'rotate', 'yaw': -140, 'pitch': 30}]
                    actions += [{'action': 'view', 'name': name} for name in ('front', 'back', 'left', 'right', 'top', 'bottom', 'iso')]
                    for action in actions:
                        previous = scene.info()['camera']
                        scene.command({'op': 'camera-action', **action})
                        camera = scene.info()['camera']
                        self.assertEqual(camera['target'], target, 'orbit rotation uses the retained target')
                        self.assertAlmostEqual(math.dist(camera['position'], target), distance, delta=1e-5)
                        self.assertCell(project(target, camera, width, height), (width / 2, height / 2), CELL, f'{action}: target at window centre')
                        if action['action'] == 'rotate':
                            expected_yaw = (previous['yaw'] + action['yaw'] + 180) % 360 - 180
                            self.assertAlmostEqual(camera['yaw'], expected_yaw, places=5)
                            self.assertAlmostEqual(camera['pitch'], max(-89, min(89, previous['pitch'] + action['pitch'])), places=5)
        with self.subTest(case='fly navigation rotates about the eye'), NativeScene(2030) as scene:
            configure(scene, 120, 48, False, 'original')
            scene.command({'op': 'camera', 'navigation': 'fly'})
            before = scene.info()['camera']
            scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4})
            self.assertIsNone(scene.info()['camera']['grabbed'])
            scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 40.3, 'y': 23.4})
            after = scene.info()['camera']
            self.assertEqual(after['position'], before['position'])
            self.assertNotEqual(after['yaw'], before['yaw'])
        for orthographic in (False, True):
            with self.subTest(case='explicit anchor at window centre', orthographic=orthographic), NativeScene(2030) as scene:
                configure(scene, 97, 31, orthographic)
                camera = scene.info()['camera']
                _, _, forward = basis(camera)
                anchor = [round(camera['position'][i] + forward[i] * 60, 6) for i in range(3)]
                scene.command({'op': 'camera-controls', 'rig': 'orbit', 'anchor': anchor})
                distance = math.dist(camera['position'], anchor)
                scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 12.3, 'y': 5.4})
                for key, value in zip(('grabbed',), (anchor,)):
                    for a, b in zip(scene.info()['camera'][key], value):
                        self.assertAlmostEqual(a, b, places=6)
                for x, y in drag_paths(12.3, 5.4)['zigzag']:
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x, 'y': y})
                    camera = scene.info()['camera']
                    self.assertCell(project(anchor, camera, 97, 31), (97 / 2, 31 / 2), CELL, 'explicit anchor stays at window centre')
                    self.assertAlmostEqual(math.dist(camera['position'], anchor), distance, delta=1e-4)
                scene.command({'op': 'pointer', 'phase': 'up', 'x': x, 'y': y})
                for a, b in zip(scene.info()['camera']['controls']['anchor'], anchor):
                    self.assertAlmostEqual(a, b, places=6, msg='an explicit anchor is persistent')
        with self.subTest(case='flight look'), NativeScene(2030) as scene:
            configure(scene, 120, 48)
            scene.command({'op': 'flight', 'steps': [{'kind': 'cruise', 'durationMs': 5000, 'speed': 10}]})
            scene.advance_to(1000000)
            before = scene.info()['camera']
            scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4})
            self.assertIsNone(scene.info()['camera']['grabbed'], 'flight drag is a look, not a grab orbit')
            scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 40.3, 'y': 20.4})
            looked = scene.info()['camera']
            self.assertTrue(looked['flightActive'])
            self.assertAlmostEqual(looked['yaw'], before['yaw'] + 6.5, places=5)
            scene.advance_to(2000000)
            self.assertGreater(math.dist(scene.info()['camera']['position'], looked['position']), 9.99)

    # Rule: pan is an explicit translation; it keeps orientation, the grab and the scene.
    def test_pan_is_explicit_translation_preserving_orientation_grab_and_scene(self):
        horizontal = []
        for profile in ('default', 'original'):
            for orthographic in (False, True):
                with self.subTest(case='right-button pan', profile=profile, orthographic=orthographic), NativeScene(2030) as scene:
                    configure(scene, 97, 31, orthographic, profile)
                    scene.command({'op': 'node', 'id': 3, 'label': 'Scene', 'position': [-30, -12, 0], 'pinned': True,
                                   'showKind': False, 'showStatus': False, 'showSha': False})
                    nodes = scene.info()['nodes']
                    x, y = 60.3, 12.4
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 2, 'x': x, 'y': y})
                    self.assertIsNone(scene.info()['camera']['grabbed'], 'right-button pan never starts a grab orbit')
                    for nx, ny in drag_paths(x, y)['zigzag'][:10]:
                        before = scene.info()['camera']
                        scene.command({'op': 'pointer', 'phase': 'move', 'button': 2, 'x': nx, 'y': ny})
                        after = scene.info()['camera']
                        dx, dy = nx - x, ny - y
                        x, y = nx, ny
                        for key in ('yaw', 'pitch', 'roll', 'fov', 'span'):
                            self.assertEqual(after[key], before[key], 'pan keeps orientation and projection')
                        right, up, forward = basis(before)
                        moved = [after['position'][i] - before['position'][i] for i in range(3)]
                        # TDD-original-workbench-pointer.md:14: the native pan's dy 0.6 is intentional current API.
                        self.assertAlmostEqual(dot(moved, up), dy * .6, delta=4e-6)
                        self.assertAlmostEqual(dot(moved, forward), 0, delta=4e-6, msg='pan translates in the view plane')
                        if dx:
                            horizontal.append(-dot(moved, right) / dx)
                        if profile == 'original':
                            for i in range(3):
                                self.assertAlmostEqual(after['target'][i] - before['target'][i], after['position'][i] - before['position'][i], delta=2e-6,
                                                       msg='original pan moves camera and target together')
                    self.assertEqual(scene.info()['nodes'], nodes, 'pan never moves scene objects')
        self.assertGreater(min(horizontal), 0, 'dragging right pans the camera along -right')
        self.assertLess(max(horizontal) - min(horizontal), 1e-5, 'one horizontal pan rate in both profiles and projections')
        for orthographic in (False, True):
            with self.subTest(case='configured pan mode keeps the pick', orthographic=orthographic), NativeScene(2030) as scene:
                configure(scene, 97, 31, orthographic)
                scene.command({'op': 'camera-controls', 'rig': 'orbit', 'mode': 'pan'})
                axes = scene.info()['camera']['controls']['inputAxes']
                x, y = 30.3, 12.4
                scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y})
                grabbed = scene.info()['camera']['grabbed']
                self.assertIsNotNone(grabbed)
                for nx, ny in drag_paths(x, y)['loop']:
                    before = scene.info()['camera']
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': nx, 'y': ny})
                    after = scene.info()['camera']
                    dx, dy = nx - x, ny - y
                    x, y = nx, ny
                    self.assertEqual(after['grabbed'], grabbed, 'pan keeps the captured pick')
                    for key in ('yaw', 'pitch', 'roll'):
                        self.assertEqual(after[key], before[key])
                    right, up, _ = basis(before)
                    sx = axes['x']['sensitivity'] * (-1 if axes['x']['invert'] else 1) * dx
                    sy = axes['y']['sensitivity'] * (-1 if axes['y']['invert'] else 1) * dy
                    self.assertEqual((axes['x']['action'], axes['y']['action']), ('pan-x', 'pan-y'))
                    expected = [before['position'][i] + right[i] * sx + up[i] * sy for i in range(3)]
                    for a, b in zip(after['position'], expected):
                        self.assertAlmostEqual(a, b, delta=2e-6)

    # Rule: flight ownership; drag looks during travel, brake is the detach and keeps the pose.
    def test_flight_detach_by_brake_preserves_pose_and_returns_pointer_ownership(self):
        for profile in ('default', 'original'):
            with self.subTest(profile=profile), NativeScene(2030) as scene:
                configure(scene, 120, 48, False, profile)
                flight = {'op': 'flight', 'steps': [{'kind': 'turn', 'durationMs': 5000, 'speed': 10, 'yaw': 40}]}
                if profile == 'original':
                    flight['profile'] = 'original'
                scene.command(flight)
                scene.advance_to(1000000)
                for button, (x, y) in ((1, (37.3, 24.4)), (2, (34.3, 22.4))):
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': button, 'x': 30.3, 'y': 20.4})
                    self.assertIsNone(scene.info()['camera']['grabbed'])
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': button, 'x': x, 'y': y})
                    scene.command({'op': 'pointer', 'phase': 'up', 'x': x, 'y': y})
                    self.assertTrue(scene.info()['camera']['flightActive'], 'camera edits keep the flight running')
                scene.advance_to(1500000)
                before = scene.info()['camera']
                scene.command({'op': 'brake'})
                after = scene.info()['camera']
                for key in POSE_KEYS:
                    self.assertEqual(after[key], before[key], f'brake captures the current {key}')
                self.assertFalse(after['flightActive'])
                scene.advance_to(2500000)
                self.assertEqual(scene.info()['camera']['position'], after['position'])
                scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4})
                grabbed = scene.info()['camera']['grabbed']
                self.assertIsNotNone(grabbed, 'after the detach the pointer pivots at the grab again')
                scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 41.3, 'y': 25.4})
                self.assertCell(project(grabbed, scene.info()['camera'], 120, 48), (30.3, 20.4), CELL)

    # Rule: path ownership; a conflicting pointer gesture cannot move a path-owned camera.
    def test_path_owned_camera_position_is_not_moved_by_conflicting_gestures(self):
        for profile in ('default', 'original'):
            for configured in (False, True, 'head', 'dolly', 'crane', 'follow', 'spacecraft'):
                for orthographic in (False, True):
                    with self.subTest(profile=profile, configured=configured, orthographic=orthographic), \
                            NativeScene(2030) as scene, NativeScene(2030) as control:
                        for s in (scene, control):
                            configure(s, 120, 48, orthographic, profile, rig=configured is True)
                            if isinstance(configured, str):
                                s.command({'op': 'camera-controls', 'rig': configured})
                            s.command(PATH)
                            s.advance_to(1000000)
                        rig = scene.info()['camera']['controls']
                        gestures = [
                            ('orbit drag', [{'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4}]
                             + [{'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x, 'y': y} for x, y in drag_paths(30.3, 20.4)['zigzag'][:8]]
                             + [{'op': 'pointer', 'phase': 'up', 'x': 1, 'y': 1}]),
                            ('right pan', [{'op': 'pointer', 'phase': 'down', 'button': 2, 'x': 30.3, 'y': 20.4},
                                           {'op': 'pointer', 'phase': 'move', 'button': 2, 'x': 37.3, 'y': 24.4},
                                           {'op': 'pointer', 'phase': 'up', 'x': 37.3, 'y': 24.4}]),
                            ('shift pan', [{'op': 'pointer', 'phase': 'down', 'button': 0, 'shift': True, 'x': 30.3, 'y': 20.4},
                                           {'op': 'pointer', 'phase': 'move', 'button': 0, 'x': 25.3, 'y': 14.4},
                                           {'op': 'pointer', 'phase': 'cancel', 'x': 25.3, 'y': 14.4}]),
                            ('wheel', [{'op': 'wheel', 'delta': 3, 'x': 30, 'y': 20}, {'op': 'wheel', 'delta': -5, 'x': 70, 'y': 30}]),
                        ]
                        if configured:
                            gestures.append(('camera-input', [{'op': 'camera-input', 'delta': [7, 4, 2]},
                                                              {'op': 'camera-input', 'delta': [3, -2, 1], 'pan': True}]))
                        for label, commands in gestures:
                            for command in commands:
                                scene.command(command)
                                camera = scene.info()['camera']
                                self.assertEqual(camera['position'], control.info()['camera']['position'],
                                                 f'{label}: path travel owns the camera position')
                                self.assertEqual(camera['position'], scene.info()['pathActors'][0]['position'])
                                if configured:
                                    # Crane pivot/boom, follow offset and head position are authored rig
                                    # state; only a head-targeted look may turn the head.
                                    controls = copy.deepcopy(camera['controls'])
                                    if controls['inputTarget'] == 'head':
                                        controls['head']['rotation'] = rig['head']['rotation']
                                    self.assertEqual(controls, rig, f'{label}: gestures never re-author a path-owned {configured} rig')
                        self.assertRestorable(scene)
                        scene.command({'op': 'look', 'yaw': 5, 'pitch': 2})
                        self.assertEqual(scene.info()['camera']['position'], control.info()['camera']['position'],
                                         'look/orientation stays separately authored')
                        for s in (scene, control):
                            s.advance_to(2500000)
                        self.assertEqual(scene.info()['camera']['position'], control.info()['camera']['position'])
                        self.assertEqual(scene.info()['camera']['position'], scene.info()['pathActors'][0]['position'])

    # Rule: the documented detach (remove-path-travel) leaves the current pose.
    def test_path_detach_preserves_the_current_pose_and_returns_pointer_ownership(self):
        flights = {None: None,
                   'default': {'op': 'flight', 'steps': [{'kind': 'cruise', 'durationMs': 5000, 'speed': 10}]},
                   'original': {'op': 'flight', 'profile': 'original', 'cruise': {'speed': 10}}}
        for profile in ('default', 'original'):
            for flight, command in flights.items():
                with self.subTest(profile=profile, flight_during_ownership=flight), NativeScene(2030) as scene:
                    configure(scene, 120, 48, False, profile)
                    scene.command(PATH)
                    scene.advance_to(1000000)
                    if command:
                        scene.command(command)
                    scene.advance_to(1500000)
                    owned = scene.info()['camera']
                    scene.command({'op': 'look', 'yaw': 4, 'pitch': -3})
                    looked = scene.info()['camera']
                    self.assertEqual(looked['position'], owned['position'], 'look never moves a path-owned camera')
                    self.assertAlmostEqual(looked['yaw'], owned['yaw'] + 4, places=5, msg='look/orientation remains separately authored')
                    self.assertAlmostEqual(looked['pitch'], owned['pitch'] - 3, places=5)
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4})
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 38.3, 'y': 23.4})
                    scene.command({'op': 'pointer', 'phase': 'up', 'x': 38.3, 'y': 23.4})
                    before = scene.info()['camera']
                    self.assertEqual(before['position'], owned['position'], 'a drag never moves a path-owned camera')
                    self.assertNotEqual((before['yaw'], before['pitch']), (looked['yaw'], looked['pitch']),
                                        'a drag changes the orientation of a path-owned camera')
                    scene.command({'op': 'remove-path-travel', 'id': 7})
                    after = scene.info()['camera']
                    self.assertNotIn('pathActors', scene.info())
                    for key in POSE_KEYS:
                        self.assertEqual(after[key], before[key], f'detach leaves the current {key}')
                    scene.advance_to(2500000)
                    held = scene.info()['camera']
                    for key in POSE_KEYS:
                        self.assertEqual(held[key], before[key], f'no residual travel moves {key} after the detach')
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4})
                    grabbed = scene.info()['camera']['grabbed']
                    self.assertIsNotNone(grabbed)
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 39.3, 'y': 24.4})
                    moved = scene.info()['camera']
                    self.assertNotEqual(moved['position'], held['position'], 'pointer ownership returns after the detach')
                    self.assertCell(project(grabbed, moved, 120, 48), (30.3, 20.4), CELL)

    # Rule: viewport changes during a gesture commit; the grab does not outlive its capture.
    def test_capture_ending_inputs_commit_mid_gesture_and_release_the_grab(self):
        window = {'op': 'window', 'id': 1, 'title': 'W', 'position': [-30, 10, 0], 'width': 20, 'height': 10}
        selection = [{'op': 'prompt', 'active': True}, {'op': 'draft', 'text': 'hello world'}, {'op': 'select', 'anchor': 0, 'caret': 5}]
        bound = [{'op': 'define', 'path': '/border', 'value': 0, 'binding': {'family': 'prompt', 'field': 'border'}}]
        cases = [
            ('resize', [], {'op': 'resize', 'width': 97, 'height': 31}),
            ('F6 reader', [window], {'op': 'key', 'key': 'F6'}),
            ('window read', [window], {'op': 'window-action', 'id': 1, 'action': 'read'}),
            ('prompt', [], {'op': 'prompt', 'active': False}),
            ('Escape selection', selection, {'op': 'key', 'key': 'Escape'}),
            ('prompt value', bound, {'op': 'set', 'path': '/border', 'value': 1}),
        ]
        for profile in ('default', 'original'):
            for label, prefix, command in cases:
                with self.subTest(profile=profile, input=label), NativeScene(2030) as scene:
                    configure(scene, 120, 48, False, profile)
                    for c in prefix:
                        scene.command(c)
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 100.3, 'y': 20.4})
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 103.3, 'y': 21.4})
                    self.assertIsNotNone(scene.info()['camera']['grabbed'])
                    scene.command(command)
                    camera = scene.info()['camera']
                    self.assertIsNone(camera['grabbed'], 'ending pointer capture releases the grab')
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 110.3, 'y': 30.4})
                    self.assertEqual(scene.info()['camera'], camera, 'the ended gesture no longer drives the camera')
                    self.assertRestorable(scene)
            with self.subTest(profile=profile, input='scene-art resize'), NativeScene(2030) as scene:
                for command in scenic_commands(build_original_scenic_routes()[0], 160, 52, 1, profile):
                    scene.command(command)
                scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 50.3, 'y': 20.4})
                self.assertIsNotNone(scene.info()['camera']['grabbed'])
                resize = copy.deepcopy(next(c for c in scenic_commands(build_original_scenic_routes()[0], 121, 37, 1, profile) if c['op'] == 'scene-art'))
                resize.pop('timeMs', None)
                scene.command(resize)
                self.assertIsNone(scene.info()['camera']['grabbed'])
                self.assertRestorable(scene)
            for label, (width, height), prefix, target, button, shift in second_press_cases():
                with self.subTest(profile=profile, input='second press: ' + label), NativeScene(2030) as scene:
                    configure(scene, width, height, False, profile)
                    for c in prefix:
                        scene.command(c)
                    (x, y), (tx, ty) = second_press_points(scene.render(), target, width, height)
                    scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y})
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x + 1, 'y': y + 1})
                    before = scene.info()
                    self.assertIsNotNone(before['camera']['grabbed'])
                    press = {'op': 'pointer', 'phase': 'down', 'button': button, 'x': tx, 'y': ty, **({'shift': True} if shift else {})}
                    scene.command(press)  # commits during the drag: no rejection in either profile
                    after = scene.info()
                    self.assertIsNone(after['camera']['grabbed'], 'a press that ends or replaces the capture releases the grab')
                    if label == 'selected reader window':
                        self.assertTrue(after['windows'][0]['reader'])
                        self.assertEqual(after['selectedWindow'], 1, 'the reader keeps its input ownership')
                    elif label == 'framed prompt minimize':
                        self.assertEqual(after['prompt']['mode'], before['prompt']['normalMode'], 'minimize returns to the normal mode')
                        self.assertEqual(after['prompt']['minimizedRestoreMode'], before['prompt']['mode'])
                    elif label == 'prompt selection':
                        self.assertEqual((after['prompt']['anchor'], after['prompt']['caret']), (6, 6), 'the press starts a selection at "w"')
                    elif label == 'window drag':
                        self.assertEqual(after['selectedWindow'], 1)
                    scene.command({'op': 'pointer', 'phase': 'move', 'button': button, 'x': tx + 3, 'y': ty})
                    moved = scene.info()
                    self.assertIsNone(moved['camera']['grabbed'])
                    if label == 'shift pan':
                        for key in ('yaw', 'pitch', 'roll'):
                            self.assertEqual(moved['camera'][key], after['camera'][key], 'the new gesture is a pan, not an orbit')
                        self.assertNotEqual(moved['camera']['position'], after['camera']['position'])
                    else:
                        self.assertEqual(moved['camera'], after['camera'], 'the released grab no longer drives the camera')
                    if label == 'window drag':
                        self.assertNotEqual(moved['windows'][0]['position'], after['windows'][0]['position'], 'the new gesture drags the window')
                    if label == 'prompt selection':
                        self.assertEqual((moved['prompt']['anchor'], moved['prompt']['caret']), (6, 9), 'the new gesture extends the selection')
                    self.assertRestorable(scene)

    # Rule: pointer coordinates stay accurate after resize (logical dimensions).
    def test_pointer_coordinates_follow_each_resize_of_the_logical_viewport(self):
        for profile in ('default', 'original'):
            for orthographic in (False, True):
                with self.subTest(profile=profile, orthographic=orthographic), NativeScene(2030) as scene:
                    configure(scene, 120, 48, orthographic, profile)
                    for width, height in ((203, 31), (40, 60), (97, 23), (7, 3), (120, 48)):
                        scene.command({'op': 'resize', 'width': width, 'height': height})
                        for fx, fy in ((.2, .3), (.77, .61), (.5, .5)):
                            x, y = width * fx + .3, height * fy + .2
                            scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y})
                            camera = scene.info()['camera']
                            self.assertCell(project(camera['grabbed'], camera, width, height), (x, y), CELL, f'after resize to {width}x{height}')
                            scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x + 2, 'y': y + 1})
                            self.assertCell(project(camera['grabbed'], scene.info()['camera'], width, height), (x, y), CELL)
                            scene.command({'op': 'pointer', 'phase': 'up', 'x': x, 'y': y})

    # Rule: inputs commit atomically; a render between events changes nothing.
    def test_inputs_commit_atomically_and_renders_between_events_change_nothing(self):
        events = [{'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4}]
        events += [{'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x, 'y': y} for x, y in drag_paths(30.3, 20.4)['loop'][:6]]
        events += [{'op': 'wheel', 'delta': 2, 'x': 40, 'y': 20}, {'op': 'pointer', 'phase': 'up', 'x': 1, 'y': 1},
                   {'op': 'pointer', 'phase': 'down', 'button': 2, 'x': 60.3, 'y': 30.4},
                   {'op': 'pointer', 'phase': 'move', 'button': 2, 'x': 64.3, 'y': 33.4}, {'op': 'pointer', 'phase': 'cancel', 'x': 1, 'y': 1}]
        for profile, rig in (('default', False), ('original', False), ('default', True)):
            for orthographic in (False, True):
                with self.subTest(profile=profile, rig=rig, orthographic=orthographic), NativeScene(2030) as plain, NativeScene(2030) as rendered:
                    for s in (plain, rendered):
                        configure(s, 97, 31, orthographic, profile, rig=rig)
                    for event in events + ([{'op': 'camera-input', 'delta': [3, 2, 1]}] if rig else []):
                        plain.command(event)
                        saved = rendered.snapshot()
                        rendered.render()
                        self.assertEqual(rendered.snapshot(), saved, 'render is pure')
                        rendered.command(event)
                        saved = rendered.snapshot()
                        rendered.render()
                        rendered.info()
                        rendered.render()
                        self.assertEqual(rendered.snapshot(), saved, 'render and info are pure')
                        self.assertEqual(plain.snapshot(), rendered.snapshot(), 'renders between events change nothing')
                    self.assertEqual(plain.render().bytes, rendered.render().bytes)
        rejected = [b'{"op":"pointer","phase":"drag","x":40,"y":20}',
                    b'{"op":"pointer","phase":"move","button":3,"x":40,"y":20}',
                    b'{"op":"pointer","phase":"move","x":1e999,"y":20}',
                    b'{"op":"pointer","phase":"move","x":1e10,"y":20}',
                    b'{"op":"pointer","phase":"move","x":40,"y":20,"pressure":1}',
                    b'{"op":"wheel","delta":101,"x":40,"y":20}',
                    b'{"op":"wheel","delta":1,"x":40,"y":20,"phase":"move"}',
                    b'{"op":"batch","commands":[{"op":"pointer","phase":"move","x":40,"y":20}]}',
                    b'{"op":"camera-input","delta":[1,2]}',
                    b'{"op":"camera-input","delta":[1,2,3e6]}']
        for rig in (False, True):
            with self.subTest(case='rejected inputs mid-gesture', rig=rig), NativeScene(2030) as scene, NativeScene(2030) as control:
                for s in (scene, control):
                    configure(s, 97, 31, False, rig=rig)
                    s.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4})
                    s.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 33.3, 'y': 21.4})
                for raw in rejected:
                    before = scene.snapshot()
                    with self.assertRaises(ValueError, msg=raw):
                        scene.command_raw(raw)
                    self.assertEqual(scene.snapshot(), before, f'{raw!r} rejected without partial change')
                for s in (scene, control):
                    s.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 41.3, 'y': 25.4})
                self.assertEqual(scene.snapshot(), control.snapshot(), 'the gesture continues as if rejections never happened')

    # Rule: snapshot restore preserves pose, ownership and the in-progress gesture.
    def test_snapshot_restore_preserves_pose_ownership_and_gesture_in_native_and_wasm(self):
        scenarios = self.restore_scenarios()
        requests, expected = [], []
        for label, setup, prefix, suffix, final_us in scenarios:
            with self.subTest(scenario=label), NativeScene(2030) as scene, NativeScene(2030) as restored:
                for command in setup + prefix:
                    scene.command(command)
                saved = scene.snapshot()
                restored.restore(saved)
                for key in ('camera', 'pathActors', 'clock'):
                    self.assertEqual(restored.info().get(key), scene.info().get(key), f'{label}: restored {key}')
                for s in (scene, restored):
                    for command in suffix:
                        s.command(command)
                    s.advance_to(final_us)
                self.assertEqual(restored.snapshot(), scene.snapshot(), f'{label}: continuation after restore')
                frame = scene.render()
                self.assertEqual(restored.render().bytes, frame.bytes)
                requests.append({'id': label, 'snapshot': base64.b64encode(saved).decode(), 'commands': suffix, 'timeUs': final_us})
                expected.append((scene.info(), [w for word in frame.words() for w in word]))
        node = node_executable()
        self.assertIsNotNone(node, 'node is required for the WASM cross-check')
        with tempfile.TemporaryDirectory(prefix='camera-restore-wasm-') as folder:
            request, response = Path(folder) / 'in.json', Path(folder) / 'out.json'
            request.write_text(json.dumps(requests))
            run = subprocess.run([node, str(ROOT / 'tests/spatial_contract_wasm.mjs'), str(request), str(response)],
                                 capture_output=True, text=True, timeout=180)
            self.assertEqual(run.returncode, 0, run.stderr[-4000:])
            results = json.loads(response.read_text())
        for (label, *_), (info, words), result in zip(scenarios, expected, results):
            with self.subTest(scenario=label, backend='wasm'):
                self.assertEqual(result['info'], info)
                self.assertEqual(result['words'], words)

    def restore_scenarios(self):
        def base(orthographic=False, profile='default', graph=False, rig=False):
            return setup_commands(97, 31, orthographic, profile, graph=graph, rig=rig)
        def moves(points, button=1):
            return [{'op': 'pointer', 'phase': 'move', 'button': button, 'x': x, 'y': y} for x, y in points]
        loop = drag_paths(30.3, 20.4)['loop']
        down = {'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4}
        scenarios = []
        for label, orthographic, profile, graph, rig in (('default orbit', False, 'default', False, False),
                                                       ('original orthographic orbit', True, 'original', False, False),
                                                       ('original graph orthographic orbit', True, 'original', True, False),
                                                       ('configured orbit', False, 'default', False, True)):
            scenarios.append((label, base(orthographic, profile, graph, rig), [down] + moves(loop[:5]), moves(loop[5:]), 0))
        anchored = base(True, rig=True) + [{'op': 'camera-controls', 'anchor': [1, 2, 3]}]
        scenarios.append(('explicit anchor orbit', anchored, [down] + moves(loop[:4]), moves(loop[4:]) + [{'op': 'wheel', 'delta': 2, 'x': 30, 'y': 20}], 0))
        scenarios.append(('pan', base(), [{'op': 'pointer', 'phase': 'down', 'button': 2, 'x': 30.3, 'y': 20.4}] + moves(loop[:3], 2), moves(loop[3:], 2), 0))
        owned = base() + [PATH, {'op': 'time', 'timeUs': 1000000}]
        scenarios.append(('path owned', owned, [{'op': 'look', 'yaw': 3}, down] + moves(loop[:3]), moves(loop[3:]) + [{'op': 'pointer', 'phase': 'up', 'x': 1, 'y': 1}], 2500000))
        flying = base(profile='original') + [{'op': 'flight', 'profile': 'original', 'cruise': {'speed': 6}}, {'op': 'time', 'timeUs': 500000}]
        scenarios.append(('original flight look', flying, [down] + moves(loop[:3]), moves(loop[3:]), 1500000))
        return scenarios

    # Rule: the WASM path executes the same gestures with the same results (sibling harness).
    def test_native_and_wasm_replay_agree_and_satisfy_the_same_assertions(self):
        commands, checks = [], []

        def scenario(setup, steps, size):
            commands.append({'op': 'reset', 'seed': 2030})
            commands.extend(setup)
            for step, check in steps:
                commands.append(step)
                checks.append((len(commands) - 1, check, size))

        for name, profile, orthographic, graph, rig, fov in ANALYTIC_MODES:
            steps = [({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4}, ('pick', fov, (30.3, 20.4)))]
            steps += [({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x, 'y': y}, ('pick', fov, (30.3, 20.4)))
                      for x, y in drag_paths(30.3, 20.4)['zigzag'][:6]]
            scenario(setup_commands(97, 31, orthographic, profile, graph=graph, rig=rig), steps, (97, 31))
        scenario(setup_commands(97, 31) + [PATH, {'op': 'time', 'timeUs': 1000000}],
                 [({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4}, ('owned',)),
                  ({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 38.3, 'y': 24.4}, ('owned',)),
                  ({'op': 'pointer', 'phase': 'up', 'x': 1, 'y': 1}, ('owned',)),
                  ({'op': 'wheel', 'delta': 4, 'x': 30, 'y': 20}, ('owned',)),
                  ({'op': 'flight', 'profile': 'original', 'cruise': {'speed': 10}}, ('owned',)),
                  ({'op': 'time', 'timeUs': 1500000}, ('owned',)),
                  ({'op': 'remove-path-travel', 'id': 7}, ('detached',)),
                  ({'op': 'time', 'timeUs': 2500000}, ('held',))], (97, 31))
        for flight in ({'op': 'flight', 'steps': [{'kind': 'cruise', 'durationMs': 5000, 'speed': 10}]},
                       {'op': 'flight', 'profile': 'original', 'cruise': {'speed': 10}}):
            scenario(setup_commands(97, 31) + [PATH, {'op': 'time', 'timeUs': 1000000}, flight],
                     [({'op': 'look', 'yaw': 4, 'pitch': -3}, ('looked', 4, -3)),
                      ({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3, 'y': 20.4}, ('owned',)),
                      ({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 38.3, 'y': 23.4}, ('turned',)),
                      ({'op': 'pointer', 'phase': 'up', 'x': 38.3, 'y': 23.4}, ('owned',)),
                      ({'op': 'remove-path-travel', 'id': 7}, ('detached',))], (97, 31))
        scenario(setup_commands(120, 48),
                 [({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 100.3, 'y': 20.4}, ('pick', 'vertical', (100.3, 20.4))),
                  ({'op': 'resize', 'width': 97, 'height': 31}, ('released',)),
                  ({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 60.3, 'y': 10.4}, ('pick', 'vertical', (60.3, 10.4)))], (120, 48))
        window = {'op': 'window', 'id': 1, 'title': 'W', 'position': [-30, 10, 0], 'width': 20, 'height': 10}
        selection = [{'op': 'prompt', 'active': True}, {'op': 'draft', 'text': 'hello world'}, {'op': 'select', 'anchor': 0, 'caret': 5}]
        bound = [{'op': 'define', 'path': '/border', 'value': 0, 'binding': {'family': 'prompt', 'field': 'border'}}]
        down = {'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 100.3, 'y': 20.4}
        for profile in ('default', 'original'):
            for prefix, ending in (([], {'op': 'resize', 'width': 97, 'height': 31}), ([window], {'op': 'key', 'key': 'F6'}),
                                   ([window], {'op': 'window-action', 'id': 1, 'action': 'read'}), ([], {'op': 'prompt', 'active': False}),
                                   (selection, {'op': 'key', 'key': 'Escape'}), (bound, {'op': 'set', 'path': '/border', 'value': 1})):
                scenario(setup_commands(120, 48, profile=profile) + prefix,
                         [(down, ('grab',)), ({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 103.3, 'y': 21.4}, ('grab',)),
                          (ending, ('released',)), ({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 110.3, 'y': 30.4}, ('unchanged',))], (120, 48))
            route = build_original_scenic_routes()[0]
            resize = next(c for c in scenic_commands(route, 121, 37, 1, profile) if c['op'] == 'scene-art')
            resize.pop('timeMs', None)
            scenario(scenic_commands(route, 160, 52, 1, profile),
                     [({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 50.3, 'y': 20.4}, ('grab',)), (resize, ('released',))], (160, 52))
            for label, (width, height), prefix, target, button, shift in second_press_cases():
                if label not in ('selected reader window', 'framed prompt minimize', 'shift pan'):
                    continue
                setup = setup_commands(width, height, profile=profile) + prefix
                with NativeScene(2030) as probe:
                    for command in setup:
                        probe.command(command)
                    (x, y), (tx, ty) = second_press_points(probe.render(), target, width, height)
                second = {'op': 'pointer', 'phase': 'down', 'button': button, 'x': tx, 'y': ty, **({'shift': True} if shift else {})}
                scenario(setup, [({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': x, 'y': y}, ('grab',)),
                                 ({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': x + 1, 'y': y + 1}, ('grab',)), (second, ('released',)),
                                 ({'op': 'pointer', 'phase': 'move', 'button': button, 'x': tx + 3, 'y': ty}, ('panned',) if shift else ('unchanged',))],
                         (width, height))
        payload = ''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in commands)
        node = node_executable()
        self.assertIsNotNone(node, 'node is required for the WASM cross-check')
        records = []
        for argv in ([sys.executable, str(ROOT / 'scripts/replay.py')], [node, str(ROOT / 'scripts/replay.mjs')]):
            result = subprocess.run(argv, cwd=ROOT, input=payload, text=True, capture_output=True, timeout=300, env=os.environ.copy())
            self.assertEqual(result.returncode, 0, f'{argv[0]} rejected a gesture sequence: {result.stderr[-3000:]}')
            rows = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows), len(commands))
            records.append(rows)
        self.assertTrue(records[0] == records[1], 'native and WASM replay differ')
        wasm = records[1]
        for index, check, (width, height) in checks:
            info = wasm[index]['metadata']
            camera = info['camera']
            with self.subTest(row=index, check=check[0]):
                if check[0] == 'pick':
                    if commands[index]['op'] == 'pointer' and commands[index]['phase'] == 'down' and index > 0 and commands[index - 1]['op'] == 'resize':
                        width, height = commands[index - 1]['width'], commands[index - 1]['height']
                    self.assertIsNotNone(camera['grabbed'])
                    self.assertCell(project(camera['grabbed'], camera, width, height, check[1]), check[2], CELL, 'WASM pick')
                elif check[0] == 'owned':
                    self.assertEqual(camera['position'], info['pathActors'][0]['position'], 'path owns the WASM camera position')
                elif check[0] == 'detached':
                    previous = wasm[index - 1]['metadata']['camera']
                    for key in POSE_KEYS:
                        self.assertEqual(camera[key], previous[key], f'WASM detach keeps {key}')
                elif check[0] == 'looked':
                    previous = wasm[index - 1]['metadata']['camera']
                    self.assertEqual(camera['position'], previous['position'], 'WASM look never moves a path-owned camera')
                    self.assertAlmostEqual(camera['yaw'], previous['yaw'] + check[1], places=5, msg='WASM look/orientation remains separately authored')
                    self.assertAlmostEqual(camera['pitch'], previous['pitch'] + check[2], places=5)
                elif check[0] == 'turned':
                    previous = wasm[index - 1]['metadata']['camera']
                    self.assertEqual(camera['position'], previous['position'], 'a WASM drag never moves a path-owned camera')
                    self.assertNotEqual((camera['yaw'], camera['pitch']), (previous['yaw'], previous['pitch']), 'a WASM drag turns a path-owned camera')
                elif check[0] == 'held':
                    previous = wasm[index - 1]['metadata']['camera']
                    for key in POSE_KEYS:
                        self.assertEqual(camera[key], previous[key], f'no WASM travel after detach: {key}')
                elif check[0] == 'released':
                    self.assertIsNone(camera['grabbed'])
                elif check[0] == 'grab':
                    self.assertIsNotNone(camera['grabbed'])
                elif check[0] == 'unchanged':
                    self.assertEqual(camera, wasm[index - 1]['metadata']['camera'], 'the ended gesture no longer drives the WASM camera')
                elif check[0] == 'panned':
                    previous = wasm[index - 1]['metadata']['camera']
                    self.assertIsNone(camera['grabbed'])
                    for key in ('yaw', 'pitch', 'roll'):
                        self.assertEqual(camera[key], previous[key], 'the new WASM gesture is a pan, not an orbit')
                    self.assertNotEqual(camera['position'], previous['position'])

    # Rule (RC4-016): camera motion and visibility change no particle identities.
    def test_camera_gestures_never_change_particle_identity(self):
        def run(gestures):
            with NativeScene(2030) as scene:
                configure(scene, 120, 48)
                scene.command({'op': 'emitter', 'id': 1, 'effect': 'weather/autumn-drift', 'count': 40, 'position': [0, 10, 0]})
                rows = []
                for k in range(1, 7):
                    if gestures:
                        scene.command({'op': 'pointer', 'phase': 'down', 'button': 1, 'x': 30.3 + k, 'y': 20.4})
                        scene.command({'op': 'pointer', 'phase': 'move', 'button': 1, 'x': 60.3 + k * 9, 'y': 10.4 + k})
                        scene.command({'op': 'pointer', 'phase': 'up', 'x': 1, 'y': 1})
                        scene.command({'op': 'wheel', 'delta': 3, 'x': 40, 'y': 20})
                        scene.command({'op': 'pointer', 'phase': 'down', 'button': 2, 'x': 10.3, 'y': 10.4})
                        scene.command({'op': 'pointer', 'phase': 'move', 'button': 2, 'x': 30.3, 'y': 15.4})
                        scene.command({'op': 'pointer', 'phase': 'cancel', 'x': 1, 'y': 1})
                    scene.advance_to(k * 250000)
                    scene.render()
                    rows.append(scene.particles())
                return rows, scene.info()['camera']['position']
        still, still_camera = run(False)
        moved, moved_camera = run(True)
        self.assertNotEqual(still_camera, moved_camera)
        self.assertGreater(sum(map(len, still)), 0, 'the emitter must actually produce particles')
        self.assertEqual(moved, still)

    # Rule: gallery pointer coordinates are exact under device-scale and CSS size changes.
    def test_gallery_pointer_mapping_is_logical_under_device_scale_and_css_resize(self):
        from playwright.sync_api import sync_playwright
        gallery = Path(os.environ.get('NOCTURNE_CAMERA_GALLERY_PATH', ROOT / 'Nocturne-Test-Harness.html')).resolve()
        self.assertTrue(gallery.is_file(), f'{gallery} must be built by build-native.sh')
        width, height = 97, 31
        setup = setup_commands(width, height)
        targets = ((12.25, 5.5), (80.75, 7.25), (48.5, 15.5), (30.125, 27.75))
        launch = {'headless': True, 'args': ['--no-sandbox']}
        if os.environ.get('CHROMIUM'):
            launch['executable_path'] = os.environ['CHROMIUM']
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**launch)
            try:
                for scale in (1, 2, 3):
                    for viewport in ({'width': 1440, 'height': 1000}, {'width': 900, 'height': 700}):
                        with self.subTest(deviceScaleFactor=scale, viewport=viewport):
                            context = browser.new_context(device_scale_factor=scale, viewport=viewport)
                            page = context.new_page()
                            errors = []
                            page.on('pageerror', lambda e: errors.append(str(e)))
                            page.goto(gallery.as_uri())
                            page.wait_for_function('window.nativeLab')
                            page.select_option('#scenes', 'work-graph')
                            page.evaluate("""commands=>{nativeLab.hold();const s=nativeLab.scene;
                                s.command({op:'reset',seed:2030});for(const c of commands){let p;do{p=s.command(c);}while(p===1);}
                                window.__pointerLog=[];const original=s.command.bind(s);
                                s.command=c=>{if(c&&c.op==='pointer')window.__pointerLog.push(c);return original(c);};nativeLab.draw();}""", setup)
                            canvas = page.locator('#canvas')
                            canvas.scroll_into_view_if_needed()
                            box = canvas.bounding_box()
                            self.assertEqual(page.evaluate('[window.nativeView.frame.width,window.nativeView.frame.height]'), [width, height],
                                             'the gallery maps through the logical frame dimensions')
                            css_cell = max(box['width'] / width, box['height'] / height)
                            for x, y in targets:
                                page.mouse.move(box['x'] + x * box['width'] / width, box['y'] + y * box['height'] / height)
                                page.mouse.down()
                                state = page.evaluate("({camera:nativeLab.scene.info().camera,log:window.__pointerLog.filter(c=>c.phase==='down')})")
                                page.mouse.up()
                                sent = state['log'][-1]
                                self.assertLessEqual(abs(sent['x'] - x), 1 / css_cell + CELL, 'logical x within one CSS pixel')
                                self.assertLessEqual(abs(sent['y'] - y), 1 / css_cell + CELL, 'logical y within one CSS pixel')
                                camera = state['camera']
                                self.assertIsNotNone(camera['grabbed'])
                                self.assertCell(project(camera['grabbed'], camera, width, height), (sent['x'], sent['y']), CELL, 'gallery pick reprojects to its logical pointer')
                            self.assertFalse(errors)
                            context.close()
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
