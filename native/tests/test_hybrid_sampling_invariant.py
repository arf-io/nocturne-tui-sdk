"""Hybrid sampling dictates one glyph class per object and never replaces U+28FF.

Operator directive, 2026-11-01, relayed verbatim by the hybrid-braille-invariant work order:
"Hybrid sampling ALWAYS EMITS U+28FF. That's my desire; I've said the opposite is an invariant.
U+28FF should NEVER be replaced by a full block. Block samples are block samples. Braille samples
are braille samples. A hybrid sample dictates what should be a block sample vs what should be a
braille sample, and then does not 'mix' the object between the two surfaces. It allows multiple
types of objects to exist in the same sampling space; it doesn't change the nature of the sampling
on a specific object."

The dictation is read from the MIXED-LAYERS.md "Hybrid dictation" table: geometric plots and
weather (particles, burst cores, leaves, settled deposits) are braille objects; the floor (plane,
grid lines, aggregate tiles) and meshes (triangles, surface tiles, float bodies) are half-block
objects. A hybrid object is encoded exactly as its dictated explicit policy.

  (a) Pure encoder: sampling 3 with geometric coverage is the braille identity U+2800+mask for every
      nonempty mask and colour pair, U+28FF included; in compositions braille owners keep U+28FF.
  (b) Block-dictated owners show only U+2580; the half-block encoder never yields braille.
  (c) A composition of hybrid objects (a floor under an airborne leaf, a settled deposit, a mesh, an
      inherited and an explicit hybrid plot, bars drawn over the floor) renders byte-identically, at
      every tick and over dark and white backdrops, to the same composition with each object set to
      its dictated policy. So do overflowing deposits merged into aggregate floor tiles and into
      surface tiles on a mesh: a tile is painted as its receiver (floor or mesh), never as the braille
      emitter whose matter it holds. A receiver that stores cell, half or braille keeps that class for its
      tiles; hybrid is not a constant half. Through the public owner plane, no braille object shows a
      block and no block object shows braille in the cells where the objects demonstrably overlap.
  (d) Under hybrid, rendering is pure and snapshots round-trip, including into a fresh context.
  (e) The family defaults that declare hybrid: the MIXED-LAYERS.md environment row (its inherited
      plot style, every geometric kind, at capture.py's declared ticks) and every recipes.json
      composition requesting the hybrid environment, at its capture.py-declared ticks under the
      capture-tick judge (test_braille_capture_ticks), which applies the same dictation.

Unchanged and not asserted as dictated: a cell no object owns (the background field, surface fields,
source paint) has no geometric coverage and keeps the pre-Contracts-5 environment reducer. The guard
below only pins that it never shows U+28FF and that a flat cell stays U+2580.
"""
import ctypes as C
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

TESTS = Path(__file__).resolve().parent
NATIVE = TESTS.parent
sys.path[:0] = [str(TESTS), str(NATIVE / 'bindings/python')]
import test_braille_capture_ticks as ticks  # noqa: E402  (owner plane, gallery host, judge, declared ticks)
from nocturne_native import NativeScene  # noqa: E402

DOTS = (1, 8, 2, 16, 4, 32, 64, 128)
HALF_POLICY, BRAILLE, HYBRID = 1, 2, 3
FULL, HALF, SPACE = 0x28ff, 0x2580, 0x20
WIDTH, HEIGHT = 120, 40
TICKS = [k * 1_000_000 // 30 for k in range(76)]  # 0 to 2.5 s at 30 Hz: reveals, deposition, settling.
# Ink over ground, chosen so that a luminance classifier would invert, flatten or split the mask.
COLOURS = ((0xd9e8ed, 0x101010), (0x101010, 0xd9e8ed), (0x808080, 0x808080), (0xc1c1c1, 0xc0c0c0),
           (0xff3030, 0x30ff30), (0xffffff, 0xffffff), (0x000000, 0x000000))
MESH = [{'a': [-30, 0, -6], 'b': [-14, 0, -6], 'c': [-14, 5, 8], 'color': 0x8a9a7b, 'alpha': 1},
        {'a': [-30, 0, -6], 'b': [-14, 5, 8], 'c': [-30, 5, 8], 'color': 0x8a9a7b, 'alpha': 1}]
LEAF = {'op': 'emitter', 'effect': 'weather/autumn-drift', 'count': 1, 'runningTimeMs': 0, 'extent': [0, 0, 0],
        'spread': [0, 0, 0], 'wind': [0, 0, 0], 'windVariation': [0, 0, 0], 'drag': 0, 'lift': 0,
        'tumble': [0, 0, 0], 'flutterHz': 0, 'flutterAmount': 0, 'lifetimeMinMs': 10000, 'lifetimeMaxMs': 10000,
        'birthFadeMs': 0}


class Cell(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in ('glyph', 'foreground', 'background', 'id')]


def is_braille(glyph):
    return 0x2800 <= glyph <= 0x28ff


def glyph_class(glyph):
    return 'braille' if is_braille(glyph) else 'half' if glyph == HALF else 'block' if 0x2580 <= glyph <= 0x259f \
        else 'space' if glyph == SPACE else 'other'


def composition(fields, backdrop):
    """The overlapping composition; fields maps each layer to its sampling field (None omits it)."""
    def sampled(command, layer):
        return {**command, 'sampling': fields[layer]} if fields[layer] is not None else dict(command)
    return [
        {'op': 'resize', 'width': WIDTH, 'height': HEIGHT},
        {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': backdrop, 'sampling': 'hybrid'},
        {'op': 'camera', 'position': [0, 18, 35], 'yaw': 0, 'pitch': -25},
        sampled({'op': 'floor', 'visible': True, 'alpha': .4}, 'floor'),
        sampled({'op': 'mesh', 'triangles': MESH}, 'mesh'),
        # Held above the floor, so its silhouette covers floor cells on screen. An opaque, veinless blade
        # fills whole cells, as in test_braille_floor_regressions, so its interior must keep U+28FF.
        sampled({**LEAF, 'id': 1, 'position': [6, 6, 10], 'velocity': [0, 0, 0], 'gravity': [0, 0, 0], 'sizeMin': 8,
                 'sizeMax': 8, 'surfaceAlpha': 1, 'veinContrast': 0, 'initialOrientation': [0, 0, 0], 'deposit': False,
                 'collision': False}, 'emitter'),
        # Falls and settles on the floor as a deposit that keeps the emitter's policy.
        sampled({**LEAF, 'id': 2, 'position': [-4, 1, 6], 'velocity': [0, -10, 0], 'gravity': [0, -20, 0],
                 'sizeMin': 6, 'sizeMax': 6, 'deposit': True, 'collision': True}, 'emitter'),
        sampled({'op': 'widget', 'id': 31, 'kind': 'pie', 'x': 86, 'y': 2, 'width': 32, 'height': 15,
                 'data': [3, 2, 4], 'revealMs': 1200, 'padding': 0, 'alpha': 0}, 'inherited plot'),
        sampled({'op': 'widget', 'id': 32, 'kind': 'donut', 'x': 86, 'y': 20, 'width': 32, 'height': 15,
                 'data': [5, 2, 3], 'innerRadius': .6, 'revealMs': 1200, 'padding': 0, 'alpha': 0}, 'plot'),
        # Drawn over the floor: plot cells replace floor cells in the same terminal cells.
        sampled({'op': 'widget', 'id': 33, 'kind': 'bars', 'x': 6, 'y': 27, 'width': 40, 'height': 9,
                 'data': [.3, .9, .6, 1, .5], 'revealMs': 800, 'padding': 0, 'alpha': 0}, 'inherited plot'),
    ]


HYBRID_FIELDS = {'floor': 'hybrid', 'mesh': 'hybrid', 'emitter': 'hybrid', 'inherited plot': None, 'plot': 'hybrid'}


def dictated_fields():
    dictation = ticks.hybrid_dictation()
    return {'floor': dictation['floor'], 'mesh': dictation['mesh'], 'emitter': dictation['emitter'],
            'inherited plot': dictation['widget'], 'plot': dictation['widget']}


# Aggregate tiles (weather.c) are painted by their receiver, not by the emitter whose matter they merge.
WALL = {'a': [0, -10, -10], 'b': [0, 10, -10], 'c': [0, 0, 10], 'surfaceId': 1}
SNOW = {**LEAF, 'id': 1, 'effect': 'weather/snowglobe', 'count': 8, 'shape': 'point', 'position': [1, 0, 0],
        'velocity': [-240, 0, 0], 'gravity': [0, 0, 0], 'sizeMin': .1, 'sizeMax': .1, 'deposit': True,
        'collision': True, 'colliders': {'surfaces': [1]}}
TILE_TICKS = [k * 100_000 for k in range(31)]  # 0 to 3 s: the tiles form within the first 0.3 s.


def tile_composition(receiver, fields, backdrop, individual=1):
    """Overflowing deposits merged into aggregate tiles on a floor ('floor') or a mesh surface ('mesh').

    individual is how many floor deposits stay whole; with 0 the tiles are the floor's only deposits.
    """
    def sampled(command, layer):
        return {**command, 'sampling': fields[layer]}
    head = [{'op': 'resize', 'width': WIDTH, 'height': HEIGHT},
            {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': backdrop, 'sampling': 'hybrid'}]
    if receiver == 'floor':
        # `individual` leaves stay whole; every further leaf merges into one of at most 16 floor tiles.
        return head + [
            {'op': 'camera', 'position': [0, 18, 35], 'yaw': 0, 'pitch': -25},
            sampled({'op': 'floor', 'enabled': True, 'visible': True, 'alpha': .4, 'maxIndividual': individual,
                     'maxTiles': 16, 'cellSize': 4, 'overflow': 'merge-to-field', 'reentrainWindSpeed': 0}, 'floor'),
            sampled({**LEAF, 'id': 5, 'count': 60, 'position': [0, 2, 4], 'extent': [24, 0, 16],
                     'velocity': [0, -20, 0], 'gravity': [0, -20, 0], 'sizeMin': 2, 'sizeMax': 2, 'deposit': True,
                     'collision': True}, 'emitter')]
    # No individual deposits: every snow particle that strikes the wall merges into a surface tile.
    return head + [
        {'op': 'floor', 'enabled': False},
        {'op': 'surface', 'id': 1, 'restitution': 1, 'friction': 0, 'evaporation': 0, 'cooling': 0,
         'thermalEvaporation': 0, 'reentrainWindSpeed': 0, 'maxIndividual': 0, 'maxTiles': 4,
         'overflow': 'merge-to-field', 'retentionMs': 100000, 'renderVisible': False},
        sampled({'op': 'mesh', 'triangles': [WALL]}, 'mesh'),
        {'op': 'camera', 'position': [30, 0, 0], 'yaw': -90, 'pitch': 0},
        sampled(SNOW, 'emitter')]


def scene_with(commands):
    scene = NativeScene(ticks.SEED)
    for command in commands:
        ticks.send(scene, command)
    return scene


def differing_cells(a, b):
    return [i for i in range(len(a) // 16) if a[i * 16:i * 16 + 16] != b[i * 16:i * 16 + 16]]


def owner_classes(scene):
    """(cell index -> (family, target, policy)), glyphs of the latest render through the public owner plane."""
    frame = scene.render()
    _, table = ticks.layer_table(scene.info())
    owned = {}
    for index, path in ticks.owner_plane(scene, frame.width, frame.height):
        if path in table:
            family, target, policy, kind = table[path]
            if family != 'widget' or kind in ticks.GEOMETRIC_KINDS:
                owned[index] = (family, target, policy)
    return owned, [word[0] for word in frame.words()]


def hybrid_recipes():
    """Recipe ids whose commands request the hybrid environment (recipes.json declarations)."""
    out = []
    for recipe in json.loads((NATIVE / 'recipes.json').read_text()):
        if any(c.get('op') == 'environment' and c.get('sampling') == 'hybrid'
               for c in ticks.layer_commands(recipe['commands'])):
            out.append(recipe['id'])
    return out


def declares_hybrid(value):
    if isinstance(value, dict):
        return value.get('sampling') == 'hybrid' or any(declares_hybrid(v) for v in value.values())
    if isinstance(value, list):
        return any(declares_hybrid(v) for v in value)
    return False


class HybridEncoder(unittest.TestCase):
    """(a), (b): the pure current-contract encoder and the source compositor, through the C ABI."""

    @classmethod
    def setUpClass(cls):
        cls.scene = NativeScene(ticks.SEED)
        fn = cls.scene._lib.nrResolveSamples
        fn.argtypes = [C.POINTER(Cell), C.POINTER(C.c_uint32), C.POINTER(C.c_uint32), C.c_uint32, C.c_int]
        fn.restype = None
        cls.fn = fn

    @classmethod
    def tearDownClass(cls):
        cls.scene.close()

    def encode(self, pixels, base, coverage, sampling):
        cell = Cell()
        self.fn(C.byref(cell), (C.c_uint32 * 8)(*pixels), (C.c_uint32 * 8)(*base), coverage, sampling)
        return cell.glyph, cell.foreground, cell.background

    def test_hybrid_coverage_is_the_braille_identity_for_every_mask_and_colour(self):
        wrong = []
        for ink, ground in COLOURS:
            for mask in range(1, 256):
                pixels, base = [ink if mask & dot else ground for dot in DOTS], [ground] * 8
                hybrid, braille = self.encode(pixels, base, mask, HYBRID), self.encode(pixels, base, mask, BRAILLE)
                if hybrid != braille or hybrid[0] != 0x2800 + mask:
                    wrong.append((hex(ink), hex(ground), mask, hex(hybrid[0])))
        self.assertEqual(wrong[:6], [], f'{len(wrong)} of {255 * len(COLOURS)} hybrid masks are not U+2800+mask')

    def test_a_full_hybrid_mask_is_u28ff_at_every_brightness(self):
        for colour in (0x000000, 0x101010, 0x808080, 0xd9e8ed, 0xffffff):
            for ground in (0x000000, 0xffffff, colour):
                with self.subTest(colour=hex(colour), ground=hex(ground)):
                    glyph, foreground, background = self.encode([colour] * 8, [ground] * 8, 255, HYBRID)
                    self.assertEqual((hex(glyph), foreground, background), (hex(FULL), colour, ground))

    def test_block_dictated_cells_encode_only_the_half_block(self):
        for ink, ground in COLOURS:
            for mask in range(256):
                pixels = [ink if mask & dot else ground for dot in DOTS]
                self.assertEqual(self.encode(pixels, [ground] * 8, mask, HALF_POLICY)[0], HALF, (hex(ink), mask))

    def test_unowned_hybrid_cells_keep_the_environment_reducer_without_u28ff(self):
        """Guard for the unchanged path: no geometric coverage, so no braille object and no full mask."""
        self.assertEqual(self.encode([0x334455] * 8, [0x334455] * 8, 0, HYBRID), (HALF, 0x334455, 0x334455))
        for pattern in range(256):
            pixels = [0xf0f0f0 if pattern & dot else 0x101010 for dot in DOTS]
            glyph = self.encode(pixels, pixels, 0, HYBRID)[0]
            self.assertTrue(glyph == HALF or 0x2800 < glyph < FULL, (pattern, hex(glyph)))

    def test_source_braille_keeps_full_occupancy(self):
        fn = self.scene._lib.nrResolveSourceSamples
        fn.argtypes = [C.POINTER(Cell), C.POINTER(C.c_uint32), C.POINTER(C.c_int32), C.c_uint32, C.c_int]
        fn.restype = C.c_uint32
        cell = Cell()
        fn(C.byref(cell), (C.c_uint32 * 8)(*[0xd9e8ed] * 8), (C.c_int32 * 8)(*[1] * 8), 0x101319, 1)
        self.assertEqual((hex(cell.glyph), cell.foreground, cell.background), (hex(FULL), 0xd9e8ed, 0x101319))


class HybridComposition(unittest.TestCase):
    """(a)-(d) on real compositions through the public C ABI."""

    def scene(self, fields, backdrop=0x101010):
        scene = scene_with(composition(fields, backdrop))
        self.addCleanup(scene.close)
        return scene

    def test_the_composition_is_hybrid_and_settles_a_deposit(self):
        scene = self.scene(HYBRID_FIELDS)
        scene.advance_to(TICKS[-1])
        info = scene.info()
        self.assertEqual(info['environment']['sampling'], 'hybrid')
        self.assertEqual([e['sampling'] for e in info['emitters']], ['hybrid', 'hybrid'])
        self.assertEqual({w['id']: w['plot']['sampling'] for w in info['widgets']},
                         {31: 'inherit', 32: 'hybrid', 33: 'inherit'})
        self.assertEqual(len(info['deposits']), 1, 'the falling leaf did not settle')
        self.assertTrue(info['floor']['renderVisible'])
        self.assertGreater(info['geometry']['triangles'], 0)

    def test_hybrid_objects_render_byte_identically_to_their_dictated_policies(self):
        """(c): the class is the dictation's, not brightness, contrast, coverage, overlap or owner selection."""
        for backdrop in (0x101010, 0xffffff):
            # A native context holds about 170 MiB: each pair is closed before the next backdrop is built.
            with self.subTest(backdrop=hex(backdrop)), scene_with(composition(HYBRID_FIELDS, backdrop)) as hybrid, \
                    scene_with(composition(dictated_fields(), backdrop)) as dictated:
                differing = []
                for us in TICKS:
                    hybrid.advance_to(us)
                    dictated.advance_to(us)
                    cells = differing_cells(hybrid.render().bytes, dictated.render().bytes)
                    if cells:
                        differing.append((us, len(cells)))
                self.assertEqual(differing[:5], [], f'{len(differing)} of {len(TICKS)} ticks differ from the dictation')

    def test_hybrid_aggregate_tiles_render_as_their_receivers_dictated_policy(self):
        """(b), (c) for aggregate tiles: floor tiles and surface tiles are half-block objects of their receiver.

        Mutation check: with weather.c painting a floor tile or a surface tile at the raw hybrid policy
        instead of the dictated one, sampling 3 with coverage encodes the tile as braille and the
        matching receiver below differs at every tick after the tiles form. A constant half policy passes
        here, because both receivers dictate half; test_aggregate_tiles_follow_an_explicit_receiver_policy
        pins that.
        """
        dictation = ticks.hybrid_dictation()
        for receiver in ('floor', 'mesh'):
            for backdrop in (0x101010, 0xffffff):
                hybrid_commands = tile_composition(receiver, {receiver: 'hybrid', 'emitter': 'hybrid'}, backdrop)
                dictated_commands = tile_composition(
                    receiver, {receiver: dictation[receiver], 'emitter': dictation['emitter']}, backdrop)
                # Each pair of contexts is closed before the next is built.
                with self.subTest(receiver=receiver, backdrop=hex(backdrop)), scene_with(hybrid_commands) as hybrid, \
                        scene_with(dictated_commands) as dictated:
                    differing = []
                    for us in TILE_TICKS:
                        hybrid.advance_to(us)
                        dictated.advance_to(us)
                        cells = differing_cells(hybrid.render().bytes, dictated.render().bytes)
                        if cells:
                            differing.append((us, len(cells)))
                    self.assertEqual(differing[:5], [],
                                     f'{len(differing)} of {len(TILE_TICKS)} ticks differ from the dictation')
                    # Non-vacuity: the tiles formed on the intended receiver and are visible.
                    info = hybrid.info()
                    self.assertTrue(info['aggregateMaterials'], 'no aggregate tile formed')
                    self.assertEqual(len(info['surfaceTiles']), len(info['aggregateMaterials']) if receiver == 'mesh'
                                     else 0)
                    frame = hybrid.render().bytes
                    ticks.send(hybrid, {'op': 'clear', 'scope': 'deposits'})
                    self.assertNotEqual(hybrid.render().bytes, frame, 'the tiles drew no cell')

    def test_aggregate_tiles_follow_an_explicit_receiver_policy(self):
        """(b) for tiles on a receiver that stores cell, half or braille: the tile takes that class.

        The hybrid scenes above cannot tell 'a tile follows its receiver' from 'a tile is a half block':
        floor and mesh both dictate half. Here a braille receiver can only keep braille tiles, and a cell
        receiver blank ones, by following its stored policy, whatever the hybrid emitter whose matter the
        tiles hold. A tile cell is a cell that changes when a twin of the scene has its deposits cleared.
        At every tick after the matter has settled each one must show the receiver's glyph class, and
        braille tiles must keep U+28FF.

        Mutation check: with weather.c painting tiles at a constant policy instead of their receiver's,
        the receivers of every other class fail on the floor and on the mesh. Constant half fails the
        braille and cell receivers, constant braille the half and cell receivers, constant cell the half
        and braille receivers. The floor line and the mesh line fail independently.
        """
        for receiver in ('floor', 'mesh'):
            for policy, wanted in (('cell', 'space'), ('half', 'half'), ('braille', 'braille')):
                for backdrop in (0x101010, 0xffffff):
                    commands = tile_composition(receiver, {receiver: policy, 'emitter': 'hybrid'}, backdrop,
                                                individual=0)
                    with self.subTest(receiver=receiver, policy=policy, backdrop=hex(backdrop)), \
                            scene_with(commands) as scene, scene_with(commands) as twin:
                        settled, wrong, full, tile = False, [], 0, []
                        for us in TILE_TICKS:
                            scene.advance_to(us)
                            twin.advance_to(us)
                            if not settled:
                                particles = scene.info()['particles']
                                if not particles['born'] or particles['active']:
                                    continue
                                # Every leaf has landed or merged, so the tiles are final. Only the twin loses them.
                                settled = True
                                ticks.send(twin, {'op': 'clear', 'scope': 'deposits'})
                            frame = scene.render()
                            words = frame.words()
                            tile = differing_cells(frame.bytes, twin.render().bytes)
                            wrong += [(us, i % WIDTH, i // WIDTH, hex(words[i][0])) for i in tile
                                      if glyph_class(words[i][0]) != wanted]
                            full += sum(words[i][0] == FULL for i in tile)
                        # Non-vacuity: the matter settled into tiles on the intended receiver, and they are visible.
                        self.assertTrue(settled, 'the matter never settled')
                        info = scene.info()
                        self.assertTrue(info['aggregateMaterials'], 'no aggregate tile formed')
                        formed = len(info['aggregateMaterials'])
                        self.assertEqual(len(info['surfaceTiles']), formed if receiver == 'mesh' else 0)
                        self.assertTrue(tile, 'the tiles drew no cell')
                        self.assertEqual(wrong[:5], [], f'{len(wrong)} tile cells left the {policy} class')
                        if policy == 'braille':
                            self.assertGreater(full, 0, 'no braille tile cell kept U+28FF')

    def test_each_owner_keeps_its_dictated_class_where_objects_overlap(self):
        """(a), (b), (c) per owner: braille objects never show a block and block objects never show braille."""
        dictation = ticks.hybrid_dictation()
        full = self.scene(HYBRID_FIELDS)
        # The same composition without the leaves and plots shows which cells the floor and mesh own alone.
        bare = scene_with([c for c in composition(HYBRID_FIELDS, 0x101010) if c['op'] not in ('emitter', 'widget')])
        self.addCleanup(bare.close)
        for scene in (full, bare):
            ticks.register_layers(scene)
        seen, overlap, mixed = {}, Counter(), []
        for us in TICKS:
            full.advance_to(us)
            bare.advance_to(us)
            owned, glyphs = owner_classes(full)
            under, _ = owner_classes(bare)
            for index, (family, target, policy) in owned.items():
                self.assertEqual(policy, 'hybrid', (family, target))
                cls, wanted = glyph_class(glyphs[index]), dictation[family]
                if cls != 'space':
                    seen.setdefault(f'{family}/{target}', Counter())[cls] += 1
                    if glyphs[index] == FULL:
                        seen[f'{family}/{target}']['full'] += 1
                if cls not in (wanted, 'space'):
                    mixed.append((us, index % WIDTH, index // WIDTH, f'{family}/{target}', hex(glyphs[index])))
                if index in under and under[index][0] in ('floor', 'mesh') and family in ('emitter', 'widget'):
                    overlap[(family, under[index][0])] += 1
        self.assertEqual(mixed[:8], [], f'{len(mixed)} owned cells left their dictated class')
        # Non-vacuity: every family drew its class, filled braille kept U+28FF, and objects shared cells.
        for owner, family in (('emitter/1', 'emitter'), ('emitter/2', 'emitter'), ('widget/31', 'widget'),
                              ('widget/32', 'widget'), ('widget/33', 'widget'), ('floor/0', 'floor'),
                              ('mesh/0', 'mesh')):
            self.assertGreater(seen.get(owner, {}).get(dictation[family], 0), 0, owner)
        for owner in ('emitter/1', 'widget/31', 'widget/32', 'widget/33'):
            self.assertGreater(seen[owner]['full'], 0, owner + ' never kept U+28FF')
        self.assertGreater(overlap[('emitter', 'floor')], 0, 'no leaf cell lay over a floor cell')
        self.assertGreater(overlap[('widget', 'floor')], 0, 'no plot cell lay over a floor cell')

    def test_hybrid_rendering_is_pure_and_snapshots_round_trip(self):
        """(d)."""
        scene = self.scene(HYBRID_FIELDS)
        for us in (0, 600000, 1500000, 2500000):
            with self.subTest(us=us):
                scene.advance_to(us)
                saved, before = scene.snapshot(), scene.info()
                first = scene.render()
                self.assertEqual(scene.render().bytes, first.bytes)
                self.assertEqual(scene.snapshot(), saved, 'rendering changed the authoritative state')
                after = scene.info()
                for key in ('clock', 'particles', 'emitters', 'deposits', 'widgets', 'floor', 'environment'):
                    self.assertEqual(after[key], before[key], key)
                scene.advance_to(us + 400000)
                scene.render()
                scene.restore(saved)
                self.assertEqual(scene.render().bytes, first.bytes)
                self.assertEqual(scene.snapshot(), saved)
                with NativeScene(1) as fresh:
                    fresh.restore(saved)
                    self.assertEqual(fresh.render().bytes, first.bytes)
                    self.assertEqual(fresh.snapshot(), saved)


class HybridFamilyDefaults(unittest.TestCase):
    """(e): every declaration of hybrid as a family default, at its declared capture ticks."""

    def test_hybrid_family_defaults_are_read_from_their_declarations(self):
        documented = ticks.documented_defaults()
        self.assertEqual(documented['environment'], 'hybrid')
        self.assertEqual(documented['widget'], 'inherit')
        self.assertEqual(set(ticks.hybrid_dictation()), set(ticks.GEOMETRY_FAMILIES))
        self.assertLessEqual(set(ticks.hybrid_dictation().values()), {'braille', 'half'})
        recipes, plan = hybrid_recipes(), dict(ticks.capture_plan())
        self.assertTrue(recipes)
        self.assertLessEqual(set(recipes), set(plan), 'a hybrid recipe has no declared capture ticks')
        catalogue = json.loads((NATIVE / 'catalogue.json').read_text())
        self.assertGreater(len(catalogue), 20)
        self.assertEqual([entry['id'] for entry in catalogue if declares_hybrid(entry)], [],
                         'a catalogue profile now declares hybrid: judge it here')

    def test_the_inherited_plot_style_is_braille_at_the_declared_capture_ticks(self):
        """MIXED-LAYERS.md: environment.sampling hybrid is also the inherited plot style."""
        plan = ticks.capture_plan()
        declared = [us - plan[0][1][0] for us in plan[0][1]]  # capture.py's per-scene tick schedule
        widgets = [{'op': 'widget', 'id': 31 + i, 'kind': kind, 'x': 2 + i % 4 * 39, 'y': 2 + i // 4 * 22,
                    'width': 36, 'height': 20, 'padding': 0, 'alpha': 0, 'data': [.2, .9, .4, .7, .6],
                    'value': 88 if kind == 'digits' else .67, 'revealMs': 1500}
                   for i, kind in enumerate(ticks.GEOMETRIC_NAMES)]
        base = [{'op': 'resize', 'width': 160, 'height': 48},
                {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': 0x101010}]
        inherited = scene_with(base + widgets)
        self.addCleanup(inherited.close)
        dictated = scene_with(base + [{**w, 'sampling': ticks.hybrid_dictation()['widget']} for w in widgets])
        self.addCleanup(dictated.close)
        self.assertEqual(inherited.info()['environment']['sampling'], 'hybrid')
        differing, blocks, full = [], [], Counter()
        for us in declared:
            inherited.advance_to(us)
            dictated.advance_to(us)
            frame = inherited.render()
            cells = differing_cells(frame.bytes, dictated.render().bytes)
            if cells:
                differing.append((us, len(cells)))
            for glyph, _, _, ident in frame.words():
                if ident & 0xff000000 != 0x30000000:  # Widget hit IDs; these plots draw no text or border.
                    continue
                if 0x2580 <= glyph <= 0x259f:
                    blocks.append((us, ident & 0xffff, hex(glyph)))
                full[ident & 0xffff] += glyph == FULL
        self.assertEqual(differing[:5], [], f'{len(differing)} of {len(declared)} declared ticks differ from braille')
        self.assertEqual(blocks[:5], [], 'an inherited hybrid plot showed a block')
        for i, kind in enumerate(ticks.GEOMETRIC_NAMES):
            if kind in ticks.FILLED_KINDS:
                self.assertGreater(full[31 + i], 0, kind + ' never kept U+28FF')

    def test_hybrid_environment_recipes_keep_dictated_classes_at_their_declared_capture_ticks(self):
        recipes = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
        plan = ticks.capture_plan()
        states, _ = ticks.capture_states(plan, recipes)
        chosen = set(hybrid_recipes())
        jobs = [{'kind': 'capture', 'label': 'hybrid environment ' + scene, 'recipe': recipes[scene], 'ticks': us,
                 'alpha': alpha, 'mode': mode, 'draft': draft, 'pearl': None}
                for (scene, us), (alpha, mode, draft) in zip(plan, states) if scene in chosen]
        self.assertEqual(len(jobs), len(chosen))
        results = ticks.run_jobs(jobs)
        for result in results:
            with self.subTest(composition=result['label']):
                self.assertEqual(result['failures'], [])
                self.assertEqual(result['violations'], [])
        self.assertGreater(sum(r['counts'].get('full', 0) for r in results), 0, 'no braille owner kept U+28FF')


if __name__ == '__main__':
    unittest.main()
