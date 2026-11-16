"""Braille coverage at every declared capture tick and for every family default.

AGENTS.md (Pearl regression): scene/plot braille coverage is geometric, never a
contrast-based full-block substitution; test all 256 masks (test_braille_fidelity)
and every declared capture tick (this module). GOAL-NOCTURNE-1.0.0.md: requested
full eight-dot braille stays U+28FF regardless of brightness, density or owner
selection; test the actual composition and the family defaults, not only the
pure encoder. Glyph policies are local (MIXED-LAYERS.md): braille layers must not
restyle their neighbours and no layer is globally forced to braille.

Covered declarations (ticks and captures are read from them, never copied here):
  * native/scripts/capture.py: the default --scenes, --fps and --seconds and the
    per-scene start offsets, 13 scenes x 120 ticks = 1560 ticks, every one judged.
  * docs/current/images/CAPTURES.json: each capture is replayed, excluded by name
    (EXCLUDED_CAPTURES) or requests neither policy; nothing is skipped silently.
    Replayed: captures whose composition requests braille or hybrid sampling, or
    weather with its default braille sampling (32 of 100 at this commit), each at
    its recorded clock, reproducing the recorded cell SHA-256. Model resources are
    uploaded as the template does. Excluded (16), not native command sequences: 8
    original scenic and 2 Pearl Fleet stage captures run in JavaScript sessions,
    and 6 captures of 3 project presets are assembled by the JavaScript composition
    editor (composition_presets.mjs). Requesting neither policy: 52.
Not covered (follow-up): the clocks capture_scene_media.py --through-timeline
declares, each gallery case's sampleTimesUs and action times. Under the selection
above that is 965 of the 6000 gallery_cases.build_cases() cases (4 of them
JavaScript sessions) with 4339 declared clocks (distinct within each case), all at
or before 6.5 s. An opt-in or exhaustive-step sweep of them is not in this module.
Scenes are driven through the public C ABI with the command sequence of the
gallery template's load()/hold()/advance() (native/web/template.html), which
capture.py and capture_reference_components.py drive in the browser. Family
defaults are read from the MIXED-LAYERS.md policy table.

Ownership is the encoder's own choice, read through the public semantic owner
plane: the judged scene registers every emitter, widget, floor and mesh
(state-register) and nrInspectCharacterCell names the registered owner of each
cell. Each owner is judged under the policy the engine reports for it; every
explicit sampling request of the composition must be that layer's stored policy,
and without a sampling style rule its effective one too. A geometric widget draws
no text and its plot is clipped inside padding and border (ui.c drawWidgets;
BRAILLE.md: a border can still own its visible outline), so box drawing is
accepted only on the outer ring of a bordered widget, as the exact glyph
patternBox draws at that position. A twin replaces the backdrop with solid white,
so a brightness or contrast classifier would change glyphs that geometry must
keep. At the first, middle and last tick of each composition the judged scene
proves that rendering, the capture pause bracket and owner registration leave its
state and frame unchanged.

Rule limits: 'full' counts U+28FF glyphs on braille owners; the geometric mask is
not recomputed here (the 256-mask encoder test and the recorded hashes back it).
A hybrid owner is judged as the class the MIXED-LAYERS.md "Hybrid dictation" table
names for its family (operator directive 2026-11-01: hybrid never replaces U+28FF
and never mixes one object between braille and block). Hybrid plots and weather
follow the braille rules, so U+28FF is required on filled hybrid plots instead of
being rejected; hybrid floor and mesh follow the half rules; and the white-backdrop
twin applies to hybrid owners like every other.

Not attributable through the public owner plane: stars, graph edges, electrical
arcs, surface meshes and float bodies (no registrable family), and source-profile
emitters (kinetic, studio-nova, world, thermal, atelier and observatory styles),
which paint their retained source glyphs instead of drawing through the emitter
sampler. They are checked only under a braille environment, where none may show a
block; under the default hybrid environment, or cell or half, they get no
glyph-class check.

Independent compositions run in up to NOCTURNE_BRAILLE_TICK_WORKERS processes
(default 4; 1 runs them in this process). Every assertion is made here.
"""
import ast
import ctypes as C
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unittest
from array import array
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
ROOT = NATIVE.parent
sys.path.insert(0, str(NATIVE / 'bindings/python'))
from nocturne_native import NativeScene

SPACE = 0x20
FULL = 0x28ff
HALF = 0x2580
CELL_PLOT = 0x2588
WHITE = 0xffffff
SEED = 2030
# Widget kind order of commands.c: progress, bars, pie, donut, scatter, line, digits, edge.
GEOMETRIC_KINDS = frozenset(range(6, 14))
GEOMETRIC_NAMES = ('progress', 'bars', 'pie', 'donut', 'scatter', 'line', 'digits', 'edge')
# Kinds whose plot fills whole cells at the family-default data, so a braille plot must show U+28FF.
FILLED_KINDS = ('progress', 'bars', 'pie', 'donut')
GEOMETRY_FAMILIES = ('emitter', 'widget', 'floor', 'mesh')
POLICIES = {-1: 'inherit', 0: 'cell', 1: 'half', 2: 'braille', 3: 'hybrid'}
SAMPLINGS = ('cell', 'half', 'braille', 'hybrid')
PROBE_ROLE = 'braille-probe'
INSPECT_BYTES = 408
PATH_BYTES = slice(278, 406)
UNOWNED = b'/screen/background'
PEARL_DATA_WIDGET = {'instruments': 2, 'pearl-curves': 8}
REFERENCE_ID = 65000
# Glyphs patternBox and nrBox draw for widget border 1 rounded, 2 square, 3 double, 4 heavy (ui.c, render.c):
# top-left, top-right, bottom-left and bottom-right corners, then the horizontal and vertical edges.
BORDER_GLYPHS = {1: (0x256d, 0x256e, 0x2570, 0x256f, 0x2500, 0x2502),
                 2: (0x250c, 0x2510, 0x2514, 0x2518, 0x2500, 0x2502),
                 3: (0x2554, 0x2557, 0x255a, 0x255d, 0x2550, 0x2551),
                 4: (0x250f, 0x2513, 0x2517, 0x251b, 0x2501, 0x2503)}
BORDER_NAMES = ('none', 'rounded', 'square', 'double', 'heavy')
# Layer commands whose sampling field is that layer's authored policy (commands.c), by owner family.
SAMPLING_OPS = {'widget': 'widget', 'emitter': 'emitter', 'emitter-style': 'emitter', 'floor': 'floor',
                'mesh': 'mesh', 'environment': 'environment'}
# CAPTURES.json captures that are not native command sequences, by name and reason. Nothing else is skipped.
EXCLUDED_CAPTURES = {
    **{f'{scene}/{state}': 'original scenic JavaScript session'
       for scene in ('pearl-cascade', 'copper-causeway', 'tidal-glass', 'silt') for state in ('default', 'advanced')},
    **{f'stage/{state}': 'Pearl source JavaScript session' for state in ('default', 'advanced')},
    **{f'project-{project}/{state}': 'JavaScript composition-editor project preset'
       for project in ('signal-desk', 'flight-deck', 'tidal-console') for state in ('default', 'advanced')},
}


def is_braille(glyph):
    return 0x2800 <= glyph <= 0x28ff


def is_block(glyph):
    return 0x2580 <= glyph <= 0x259f


def is_border(glyph):
    """Box drawing (U+2500..U+257F)."""
    return 0x2500 <= glyph <= 0x257f


def ring_glyph(frame, cx, cy):
    """The glyph patternBox/nrBox draws at cell (cx, cy) of a widget frame (x, y, width, height, border),
    or None when the widget has no border or the cell is not on the frame's outer ring."""
    x, y, width, height, border = frame
    right, bottom = x + width - 1, y + height - 1
    if not border or not (x <= cx <= right and y <= cy <= bottom) or (x < cx < right and y < cy < bottom):
        return None
    top_left, top_right, bottom_left, bottom_right, horizontal, vertical = BORDER_GLYPHS[border]
    # Corners are drawn last; a one-column frame has no right corners and a one-row frame no bottom ones.
    if cy == y and cx == x:
        return top_left
    if cy == y and cx == right:
        return top_right
    if cy == bottom and cx == x:
        return bottom_left
    if cy == bottom and cx == right:
        return bottom_right
    return horizontal if cy in (y, bottom) else vertical


def widget_frames(info):
    """Widget id -> (x, y, width, height, border style) as drawWidgets places its border (ui.c)."""
    return {w['id']: (w['x'], w['y'], w['width'], w['height'], w['border']) for w in info['widgets']}


def layer_commands(commands):
    """Commands in application order, batches flattened."""
    for command in commands:
        if command.get('op') == 'batch':
            yield from layer_commands(command['commands'])
        else:
            yield command


def explicit_sampling(commands):
    """(family, target) -> the sampling the composition last requested explicitly for that layer."""
    out = {}
    for command in layer_commands(commands):
        op = command.get('op')
        if op == 'reset':
            out.clear()
        elif op == 'clear' and command.get('scope', 'weather') == 'weather':
            out = {key: value for key, value in out.items() if key[0] != 'emitter'}
        elif op in SAMPLING_OPS and 'sampling' in command:
            family = SAMPLING_OPS[op]
            out[(family, command['id'] if family in ('widget', 'emitter') else 0)] = command['sampling']
    return out


def restyles_sampling(value):
    """True when a style rule anywhere in the composition overrides sampling."""
    if isinstance(value, dict):
        if value.get('op') == 'style-rule' and 'sampling' in (value.get('style') or {}):
            return True
        return any(restyles_sampling(v) for v in value.values())
    if isinstance(value, list):
        return any(restyles_sampling(v) for v in value)
    return False


def action_commands(action):
    """Commands apply_script_action() applies for one action: host steps first; an expected rejection applies nothing."""
    out = [command for step in action.get('hostSteps', []) for command in action_commands(step)]
    return out if action.get('expectedError') else out + [action['command']]


def send(scene, command):
    """The gallery's cmd(): repeat a bounded catch-up until it completes."""
    while scene.command(command) == 1:
        pass


def capture_plan():
    """Read capture.py's declared scenes and ticks from its own argument defaults."""
    tree = ast.parse((NATIVE / 'scripts/capture.py').read_text())
    defaults, offsets = {}, []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == 'add_argument' and node.args and isinstance(node.args[0], ast.Constant):
            for keyword in node.keywords:
                if keyword.arg == 'default':
                    defaults[node.args[0].value] = ast.literal_eval(keyword.value)
        if node.func.attr == 'get' and isinstance(node.func.value, ast.Dict):
            offsets.append(ast.literal_eval(node.func.value))
    if len(offsets) != 1 or not {'--fps', '--seconds', '--scenes'} <= set(defaults):
        raise AssertionError('capture.py no longer declares its ticks in the parsed form')
    fps, seconds = defaults['--fps'], defaults['--seconds']
    per = int(seconds * fps)
    return [(scene, [offsets[0].get(scene, 0) + tick * 1_000_000 // fps for tick in range(per)])
            for scene in defaults['--scenes'].split(',')]


def documented_defaults():
    """Family -> default policy from the MIXED-LAYERS.md 'Explicit policies and defaults' table."""
    out = {}
    for line in (NATIVE / 'docs/MIXED-LAYERS.md').read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) == 3 and re.fullmatch(r'\w+\.sampling( or [\w-]+\.sampling)?', cells[1]):
            out[cells[1].split('.')[0]] = re.match(r'\w+', cells[2]).group(0)
    return out


def hybrid_dictation():
    """Owner family -> the class hybrid encodes it as, from the MIXED-LAYERS.md 'Hybrid dictation' table."""
    out, inside = {}, False
    for line in (NATIVE / 'docs/MIXED-LAYERS.md').read_text().splitlines():
        if line.startswith('## '):
            inside = line.strip() == '## Hybrid dictation'
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if inside and len(cells) == 2 and cells[1] in ('braille', 'half'):
            out[re.match(r'\w+', cells[0]).group(0)] = cells[1]
    return out


def model_records(recipe):
    """The template's reset() uploads a recipe's model resource after reset, before its commands."""
    if 'modelRecords' not in recipe:
        return None
    sys.path.insert(0, str(NATIVE / 'examples'))
    from source_model_studies import decode_model_records
    return decode_model_records(recipe)


def pearl_data():
    """The original data sample the gallery injects into its two Pearl data recipes."""
    script = ("import{pathToFileURL}from'node:url';"
              "const{StudioDataSource,observatorySample}=await import(pathToFileURL(process.argv[1]).href);"
              "const studio=new StudioDataSource().advanceTo(0),sample=observatorySample(0);"
              "console.log(JSON.stringify({bus:sample.bus,reference:sample.reference,"
              "waveform:sample.waveform.map(v=>Math.max(0,Math.min(1,.5+v*.42))),"
              "studioValue:Math.round(studio.value/10),studioLevel:studio.displayValue/1000}));")
    run = subprocess.run(['node', '--input-type=module', '-e', script,
                          str(NATIVE / 'bindings/typescript/pearl_data.mjs')],
                         capture_output=True, text=True, timeout=60)
    if run.returncode:
        raise RuntimeError('Pearl data source did not run: ' + run.stderr)
    return json.loads(run.stdout)


class GalleryHost:
    """Native mirror of the template's load(), reset(), startPearlSource() and hold().

    reset() keeps the previous prompt draft, applies pearlCommands(recipe), resizes
    to the viewport fields, reapplies the prompt alpha/mode fields (an authored
    prompt updates them for every later load), sets accessibility and unpauses;
    startPearlSource() applies the original data sample at 0 ms; hold() pauses.
    """

    def __init__(self, pearl=None, alpha=.22, mode='marquee'):
        self.pearl, self.alpha, self.mode = pearl, alpha, mode

    @staticmethod
    def data_widget(recipe):
        widget = PEARL_DATA_WIDGET.get(recipe.get('id'))
        if widget is None:
            return None, None
        return widget, next(c for c in recipe['commands'] if c.get('op') == 'widget' and c.get('id') == widget)

    def commands(self, recipe):
        widget, source = self.data_widget(recipe)
        if widget is None:
            return list(recipe['commands'])
        reference = {**source, 'id': REFERENCE_ID, 'material': 15, 'data': self.pearl['reference']}
        out = [{'op': 'define', 'path': '/pearl/' + row['source'], 'value': row['value']} for row in self.pearl['bus']]
        for command in recipe['commands']:
            if command is source:
                out += [{'op': 'material', 'id': 15, 'space': 'oklch', 'channels': {'l': .83, 'c': .1, 'h': 300}},
                        reference, command]
            else:
                out.append(command)
        return out

    def source_updates(self, recipe):
        widget, source = self.data_widget(recipe)
        if widget is None:
            return []
        out = []
        if recipe['id'] == 'instruments':
            out.append({'op': 'batch', 'commands': [
                {'op': 'widget', 'id': 1, 'value': self.pearl['studioValue']},
                {'op': 'set', 'path': '/demo/level', 'value': self.pearl['studioLevel']}]})
        out.append({'op': 'batch', 'commands': [
            {'op': 'widget', 'id': widget, 'data': self.pearl['waveform']},
            {'op': 'widget', 'id': REFERENCE_ID, 'data': self.pearl['reference'], 'alpha': source.get('alpha', 1)},
            *[{'op': 'set', 'path': '/pearl/' + row['source'], 'value': row['value']} for row in self.pearl['bus']]]})
        return out

    def prompt_fields(self, recipe):
        prompts = [c for c in recipe['commands'] if c.get('op') == 'prompt']
        if prompts and 'mode' in prompts[-1]:
            self.mode = prompts[-1]['mode']
        if prompts and 'alpha' in prompts[-1]:
            self.alpha = prompts[-1]['alpha']
        return self.alpha, self.mode

    def load(self, scene, recipe, draft, viewport):
        """Apply the template's load sequence; return the commands sent, in order."""
        sent = []

        def put(command):
            send(scene, command)
            sent.append(command)
        put({'op': 'reset', 'seed': SEED})
        records = model_records(recipe)
        if records is not None:
            scene.set_model_records(records)
        for command in self.commands(recipe):
            put(command)
        if draft:
            put({'op': 'draft', 'text': draft, 'emitWeather': False})
        put({'op': 'resize', 'width': viewport[0], 'height': viewport[1]})
        alpha, mode = self.prompt_fields(recipe)
        put({'op': 'prompt', 'alpha': alpha, 'mode': mode})
        put({'op': 'accessibility', 'reducedMotion': False, 'screenReader': False})
        put({'op': 'pause', 'paused': False})
        for command in self.source_updates(recipe):
            put(command)
        put({'op': 'pause', 'paused': True})
        return sent


def capture_states(plan, recipes):
    """Prompt alpha/mode fields and draft each declared scene inherits from the scenes before it."""
    host, draft, out = GalleryHost(), '', []
    for scene, _ in plan:
        out.append((host.alpha, host.mode, draft))
        recipe = recipes[scene]
        host.prompt_fields(recipe)
        own = [c['text'] for c in recipe['commands'] if c.get('op') == 'draft']
        draft = draft or (own[-1] if own else '')
    return out, draft


def apply_script_action(scene, action, depth=0):
    """The template's applyScriptAction(): ordered host steps, then one command."""
    if 'hostSteps' in action:
        if depth >= 8:
            raise AssertionError('Invalid ordered host steps')
        for step in action['hostSteps']:
            apply_script_action(scene, step, depth + 1)
    expected = action.get('expectedError')
    try:
        send(scene, action['command'])
    except ValueError as error:
        if not expected or expected not in str(error):
            raise
    else:
        if expected:
            raise AssertionError('Expected rejection: ' + expected)


def register_layers(scene, info=None):
    """Name every emitter, widget, floor and mesh in the owner plane; keep authored registrations."""
    info = info or scene.info()
    states = info['registeredStates']
    known = {(r['family'], r['targetId']) for r in states}
    used = {r['id'] for r in states}
    wanted = ([('emitter', e['id']) for e in info['emitters']] + [('widget', w['id']) for w in info['widgets']]
              + [('floor', 0), ('mesh', 0)])
    batch, ident = [], 65535
    for family, target in wanted:
        if (family, target) in known:
            continue
        while ident in used:
            ident -= 1
        used.add(ident)
        batch.append({'op': 'state-register', 'id': ident, 'path': f'/braille-probe/{family}/{target}',
                      'role': PROBE_ROLE, 'target': {'family': family, 'id': target}})
    if batch:
        send(scene, {'op': 'batch', 'commands': batch})
    return bool(batch)


def unregister_probes(scene):
    batch = [{'op': 'state-unregister', 'id': r['id']} for r in scene.info()['registeredStates'] if r['role'] == PROBE_ROLE]
    if batch:
        send(scene, {'op': 'batch', 'commands': batch})


def owner_plane(scene, width, height):
    """(cell index, owner path) for each cell of the latest render with a registered owner (public C ABI)."""
    inspect, context = scene._lib.nrInspectCharacterCell, scene._context
    buffer, out, index = C.create_string_buffer(INSPECT_BYTES), [], 0
    for y in range(height):
        for x in range(width):
            if inspect(context, x, y, buffer, INSPECT_BYTES):
                raise AssertionError('Owner plane unavailable after render')
            path = buffer.raw[PATH_BYTES].split(b'\0', 1)[0]
            if path != UNOWNED:
                out.append((index, path))
            index += 1
    return out


def layer_table(info):
    """Registered geometry path -> (family, target, resolved policy, widget kind); environment policy."""
    environment = info['environment']['sampling']
    kinds = {w['id']: w['kind'] for w in info['widgets']}
    table = {}
    for row in info['registeredStates']:
        if not row['exists'] or row['family'] not in GEOMETRY_FAMILIES:
            continue
        policy = POLICIES[int(row['effective']['sampling'])]
        kind = kinds.get(row['targetId']) if row['family'] == 'widget' else None
        table[row['path'].encode()] = (row['family'], row['targetId'], environment if policy == 'inherit' else policy,
                                       kind)
    return environment, table


def check_requests(checks, info, requests, restyled, label, reported):
    """Each explicit request is the layer's stored (authored) policy, and without a sampling style rule the
    effective policy the judge applies is the authored one. Reports each layer once per composition."""
    rows = {(r['family'], r['targetId']): r for r in info['registeredStates'] if r['exists']}
    for (family, target), wanted in requests.items():
        if family == 'environment':
            stored = info['environment']['sampling']
        elif (family, target) in rows:
            value = rows[(family, target)]['authored'].get('sampling')
            stored = 'unreported' if value is None else POLICIES.get(int(value), value)
        else:
            continue
        if stored != wanted and (family, target) not in reported:
            reported.add((family, target))
            checks.true(False, f'{label}: {family}/{target} requested {wanted} sampling but stores {stored}')
    if restyled:
        return
    for (family, target), row in rows.items():
        if family in GEOMETRY_FAMILIES and row['effective'].get('sampling') != row['authored'].get('sampling') \
                and (family, target) not in reported:
            reported.add((family, target))
            checks.true(False, f'{label}: {family}/{target} resolves {row["effective"].get("sampling")} sampling '
                               f'over authored {row["authored"].get("sampling")} without a sampling rule')


def owns_geometry(info):
    """True when a registrable layer can own scene or plot cells."""
    return bool(info['emitters']) or info['floor']['renderVisible'] or info['geometry']['triangles'] > 0 or \
        any(w['kind'] in GEOMETRIC_KINDS for w in info['widgets'])


class Checks:
    """Failure collector usable in worker processes; the test asserts it stayed empty."""

    def __init__(self, result):
        self.failures = result['failures']

    def true(self, condition, message):
        if not condition:
            self.failures.append(message)
        return condition


class Judge:
    """Per-cell local policy rules; collects violations and non-vacuity counts."""

    def __init__(self, name):
        self.name, self.violations, self.tally = name, [], Counter()
        self.dictation = hybrid_dictation()

    @property
    def counts(self):
        out = Counter()
        for (_, key), n in self.tally.items():
            out[key] += n
        return dict(out)

    @property
    def owners(self):
        out = {}
        for (owner, key), n in self.tally.items():
            out.setdefault(owner, {})[key] = n
        return out

    def fail(self, us, index, width, owner, policy, glyph, reason):
        self.tally[(owner, 'violations')] += 1
        if len(self.violations) < 40:
            self.violations.append((self.name, us, index % width, index // width, owner, policy, hex(glyph), reason))

    def cells(self, us, glyphs, hits, twins, width, owners, environment, table, frames):
        owned, tally = set(), self.tally
        for index, path in owners:
            layer = table.get(path)
            if layer is None:
                continue
            owned.add(index)
            family, target, policy, kind = layer
            if family == 'widget' and kind not in GEOMETRIC_KINDS:
                continue  # Text, borders, cursors and scrollbar thumbs are not geometric sampling.
            plot = family == 'widget'
            glyph, owner = glyphs[index], f'{family}/{target}'
            # Hybrid dictates one class per owner family (module docstring); the owner is then held to
            # that class's rules exactly as if it had requested it explicitly.
            rule = self.dictation[family] if policy == 'hybrid' else policy
            label = policy if rule == policy else f'{policy} ({rule})'
            # A geometric widget draws no text. Its plot is clipped inside padding and border (ui.c
            # drawWidgets), so box drawing is its own only as the glyph patternBox draws at that position
            # of a bordered widget's outer ring.
            if plot and glyph == ring_glyph(frames[target], index % width, index // width):
                allowed = True
                tally[(owner, 'border')] += 1
            elif rule == 'braille':
                allowed = is_braille(glyph) or glyph == SPACE
                if is_braille(glyph):
                    tally[(owner, 'braille')] += 1
                    tally[(owner, 'full' if glyph == FULL else 'partial')] += 1
                    if policy == 'hybrid':
                        tally[(owner, 'hybrid')] += 1
            elif rule == 'half':
                allowed = glyph in (HALF, SPACE)
                if glyph == HALF:
                    tally[(owner, 'half')] += 1
                    if policy == 'hybrid':
                        tally[(owner, 'hybrid')] += 1
            elif rule == 'cell':
                allowed = glyph in ((CELL_PLOT, SPACE) if plot else (SPACE,))
                if glyph == (CELL_PLOT if plot else SPACE):
                    tally[(owner, 'cell')] += 1
            else:
                raise AssertionError(f'{owner}: no glyph rule for {label} sampling')
            if not allowed:
                self.fail(us, index, width, owner, label, glyph, f'{label} owner rendered a ' +
                          ('box-drawing glyph that is not its border' if plot and is_border(glyph) else
                           'foreign glyph class'))
            if twins[index] != glyph:
                self.fail(us, index, width, owner, label, glyph,
                          f'glyph became {twins[index]:#x} when only the backdrop brightness changed')
        if environment == 'braille':
            # The environment owns the remaining cells (or a layer the owner plane cannot name does).
            for index, glyph in enumerate(glyphs):
                if 0x2580 <= glyph <= 0x259f and hits[index] == 0 and index not in owned:
                    self.fail(us, index, width, 'environment', environment, glyph,
                              'unowned scene cell under braille sampling is a block')


def environment_fields(info):
    environment = dict(info['environment'])
    environment.pop('style')
    environment.pop('background')
    return environment


def first_difference(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None if len(a) == len(b) else min(len(a), len(b)))


def checkpoint(checks, real, frame, label, bracket):
    """Render purity, capture pause-bracket neutrality and owner-registration neutrality."""
    before = real.snapshot()
    checks.true(real.render().bytes == frame.bytes, label + ': repeated render differs')
    checks.true(real.snapshot() == before, label + ': rendering changed the authoritative state')
    if bracket:  # capture.py pauses and unpauses around every advance.
        send(real, {'op': 'pause', 'paused': True})
        send(real, {'op': 'pause', 'paused': False})
        checks.true(real.snapshot() == before, label + ': the capture pause bracket changed state')
    unregister_probes(real)
    plain = real.render()
    checks.true(first_difference(plain.bytes, frame.bytes) is None, label + ': owner registration changed the frame')
    real.restore(before)


def judge_composition(checks, real, twin, judge, ticks, label, checkpoints=None, bracket=False, requests=None,
                      restyled=False):
    """Judge every tick of the registered scene against its white-backdrop twin and its explicit requests."""
    if checkpoints is None:
        checkpoints = {ticks[0], ticks[len(ticks) // 2], ticks[-1]}
    register_layers(real)
    authored = environment_fields(real.info())
    # Only compositions with a registrable geometry layer need the brightness twin.
    twin = twin if owns_geometry(real.info()) else None
    if twin is not None:
        send(twin, {'op': 'environment', 'style': 'solid', 'background': WHITE})
        checks.true(environment_fields(twin.info()) == authored, label + ': backdrop edit changed sampling or stars')
        send(twin, {'op': 'pause', 'paused': False})
    send(real, {'op': 'pause', 'paused': False})
    changed_backdrop, reported = False, set()
    for us in ticks:
        real.advance_to(us)
        info = real.info()
        if register_layers(real, info):
            info = real.info()
        check_requests(checks, info, requests or {}, restyled, f'{label} at {us} us', reported)
        frame = real.render()
        checks.true(real.render().bytes == frame.bytes, f'{label} at {us} us: rendering twice differs')
        environment, table = layer_table(info)
        words, owners, twins = array('I', frame.bytes), [], None
        if owns_geometry(info):
            if not checks.true(twin is not None, f'{label} at {us} us: a geometry layer appeared without its twin'):
                break
            owners = owner_plane(real, frame.width, frame.height)
        if twin is not None:
            twin.advance_to(us)
            shown = array('I', twin.render().bytes)
            changed_backdrop = changed_backdrop or words[2::4] != shown[2::4]
            twins = shown[0::4]
        judge.cells(us, words[0::4], words[3::4], twins, frame.width, owners, environment, table, widget_frames(info))
        if us in checkpoints:
            checkpoint(checks, real, frame, f'{label} at {us} us', bracket)
    checks.true(twin is None or changed_backdrop, label + ': the white backdrop changed no cell')


def capture_job(job, result):
    host = GalleryHost(job['pearl'], job['alpha'], job['mode'])
    real, twin = NativeScene(SEED), NativeScene(SEED)
    try:
        for scene in (real, twin):
            sent = host.load(scene, job['recipe'], job['draft'], (160, 48))
        judge, requests = Judge(job['label']), explicit_sampling(sent)  # The twin received the same commands.
        judge_composition(Checks(result), real, twin, judge, job['ticks'], job['label'], bracket=True,
                          requests=requests, restyled=restyles_sampling(job['recipe']))
        result.update(counts=judge.counts, owners=judge.owners, violations=judge.violations,
                      finalDraft=real.info()['prompt']['text'], requested=len(requests))
    finally:
        real.close()
        twin.close()


def reference_job(job, result):
    recipe, time_us = job['recipe'], job['timeUs']
    real, twin = NativeScene(SEED), NativeScene(SEED)
    try:
        for scene in (real, twin):
            # capture_reference_components.py: reset, load, hold, then advance(timeUs) with auto actions.
            send(scene, {'op': 'reset', 'seed': SEED})
            applied = GalleryHost().load(scene, recipe, '', (recipe['viewport']['width'], recipe['viewport']['height']))
            if time_us:
                send(scene, {'op': 'pause', 'paused': False})
                for action in sorted(recipe.get('actions', []) if recipe.get('autoActions') else [],
                                     key=lambda a: a['timeUs']):
                    if action['timeUs'] <= time_us:
                        scene.advance_to(action['timeUs'])
                        scene.render()
                        apply_script_action(scene, action)
                        applied += action_commands(action)
        judge, requests = Judge(job['label']), explicit_sampling(applied)  # The twin received the same commands.
        judge_composition(Checks(result), real, twin, judge, [time_us], job['label'], checkpoints={time_us},
                          requests=requests, restyled=restyles_sampling(recipe))
        unregister_probes(real)
        result.update(counts=judge.counts, owners=judge.owners, violations=judge.violations,
                      cellSha256=hashlib.sha256(real.render().bytes).hexdigest(), requested=len(requests))
    finally:
        real.close()
        twin.close()


def default_job(job, result):
    """A composition built only from family defaults plus the stated environment policy."""
    real, twin = NativeScene(SEED), NativeScene(SEED)
    try:
        for scene in (real, twin):
            for command in job['commands']:
                send(scene, command)
        judge, requests = Judge(job['label']), explicit_sampling(job['commands'])
        judge_composition(Checks(result), real, twin, judge, job['ticks'], job['label'], checkpoints={job['ticks'][-1]},
                          requests=requests, restyled=restyles_sampling(job['commands']))
        info = real.info()
        result.update(counts=judge.counts, owners=judge.owners, violations=judge.violations, requested=len(requests),
                      deposits=len(info['deposits']), live=sum(e['active'] for e in info['emitters']),
                      environmentCells=environment_cells(real) if job.get('environmentCells') else None)
    finally:
        real.close()
        twin.close()


def environment_cells(scene):
    """Glyph classes of the scene cells (hit ID zero) that no registrable layer owns."""
    frame = scene.render()
    _, table = layer_table(scene.info())
    owned = {index for index, path in owner_plane(scene, frame.width, frame.height) if path in table}
    out = {}
    for index, (glyph, _, _, hit) in enumerate(frame.words()):
        if hit or index in owned:
            continue
        key = 'full' if glyph == FULL else 'braille' if is_braille(glyph) else 'half' if glyph == HALF else \
            'block' if is_block(glyph) else 'space' if glyph == SPACE else 'other'
        out[key] = out.get(key, 0) + 1
    return out


JOBS = {'capture': capture_job, 'reference': reference_job, 'default': default_job}


def run_job(job):
    result = {'label': job['label'], 'counts': {}, 'owners': {}, 'violations': [], 'failures': []}
    started = time.monotonic()
    try:
        JOBS[job['kind']](job, result)
    except Exception as error:  # Reported to the parent as a failure, never skipped.
        result['failures'].append(f"{job['label']}: {type(error).__name__}: {error}")
    result['seconds'] = round(time.monotonic() - started, 3)
    return result


def run_jobs(jobs):
    value = os.environ.get('NOCTURNE_BRAILLE_TICK_WORKERS', '4')
    if not value.isdigit() or not 1 <= int(value) <= 8:
        raise ValueError('NOCTURNE_BRAILLE_TICK_WORKERS must be an integer from 1 to 8')
    workers = min(int(value), len(jobs), os.cpu_count() or 1)
    if workers <= 1:
        return [run_job(job) for job in jobs]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run_job, jobs))


class Results:
    def assert_clean(self, results):
        for result in results:
            with self.subTest(composition=result['label']):
                self.assertEqual(result['failures'], [])
                self.assertEqual(result['violations'], [])


class CaptureTicks(unittest.TestCase, Results):
    """Every declared tick of capture.py's real compositions."""

    @classmethod
    def setUpClass(cls):
        cls.recipes = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
        cls.plan = capture_plan()

    def test_capture_plan_is_read_from_its_declaration(self):
        self.assertEqual(len(self.plan), 13)
        self.assertTrue(all(len(ticks) == 120 for _, ticks in self.plan))
        self.assertEqual(dict(self.plan)['autumn'][:2], [3500000, 3516666])
        self.assertTrue({scene for scene, _ in self.plan} <= set(self.recipes))

    def test_every_declared_capture_tick_keeps_geometric_braille_and_local_policies(self):
        pearl = pearl_data()
        states, last = capture_states(self.plan, self.recipes)
        jobs = [{'kind': 'capture', 'label': 'capture ' + scene, 'recipe': self.recipes[scene], 'ticks': ticks,
                 'alpha': alpha, 'mode': mode, 'draft': draft, 'pearl': pearl}
                for (scene, ticks), (alpha, mode, draft) in zip(self.plan, states)]
        results = run_jobs(jobs)
        self.assert_clean(results)
        # The template carries each scene's final prompt draft into the next load.
        for result, draft in zip(results, [draft for _, _, draft in states[1:]] + [last]):
            self.assertEqual(result.get('finalDraft'), draft, result['label'])
        counts = {scene: result['counts'] for (scene, _), result in zip(self.plan, results)}
        # Non-vacuity: scenes owning braille geometry show it, including full eight-dot cells.
        for scene in ('autumn', 'rain', 'pearl-curves', 'instruments', 'leaf-anatomy', 'mixed-materials',
                      'condition-console'):
            self.assertGreater(counts[scene].get('braille', 0), 0, scene)
        for scene in ('autumn', 'pearl-curves', 'instruments', 'leaf-anatomy', 'mixed-materials',
                      'condition-console'):
            self.assertGreater(counts[scene].get('full', 0), 0, scene + ' never kept U+28FF')
        # Mixed layers keep their own families beside braille in the same frames.
        self.assertGreater(counts['leaf-anatomy'].get('half', 0), 0, 'half-block floor')
        self.assertGreater(counts['mixed-materials'].get('cell', 0), 0, 'cell donut and progress')
        self.assertGreater(counts['mixed-materials'].get('half', 0), 0, 'half donut')
        self.assertGreater(counts['selector-studio'].get('half', 0), 0, 'half gauge')
        # Explicit requests (Pearl braille plots, half floor, cell/half/braille plots) were checked as stored.
        requested = {scene: result.get('requested', 0) for (scene, _), result in zip(self.plan, results)}
        for scene in ('instruments', 'pearl-curves', 'leaf-anatomy', 'mixed-materials', 'condition-console',
                      'selector-studio'):
            self.assertGreater(requested[scene], 0, scene)


def sampling_requests(value):
    if isinstance(value, dict):
        return [v for k, v in value.items() if k == 'sampling'] + [s for v in value.values() for s in sampling_requests(v)]
    if isinstance(value, list):
        return [s for v in value for s in sampling_requests(v)]
    return []


class ReferenceCaptures(unittest.TestCase, Results):
    """Recorded reference captures (CAPTURES.json): replayed, excluded by name, or requesting neither policy."""

    @staticmethod
    def captures():
        return json.loads((ROOT / 'docs/current/images/CAPTURES.json').read_text())

    def ledger(self):
        """(replayed (capture, recipe) rows, excluded {name: reason}, names requesting neither policy)."""
        recipes = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
        sys.path.insert(0, str(NATIVE / 'examples'))
        from gallery_cases import build_cases
        gallery = {case['id']: case for case in build_cases()}
        rows, excluded, neither = [], {}, []
        for capture in self.captures()['captures']:
            request, name = capture['request'], f"{capture['component']}/{capture['state']}"
            if 'commands' in request:
                recipe = {'commands': request['commands'], 'viewport': {'width': 80, 'height': 24}}
            elif request.get('recipeId') in recipes or request.get('recipeId') in gallery:
                recipe = recipes.get(request['recipeId']) or gallery[request['recipeId']]
                # JavaScript sessions (original scenic, Pearl stage/observatory) and the streamed Pearl data
                # source are not native command sequences. A model resource is uploaded natively.
                reason = ('original scenic JavaScript session' if recipe.get('originalScenic') else
                          'Pearl source JavaScript session' if recipe.get('pearlSource') else
                          'streamed Pearl data source' if recipe['id'] in PEARL_DATA_WIDGET else None)
                if reason:
                    excluded[name] = reason
                    continue
                recipe = {**recipe, 'viewport': recipe.get('viewport') or {'width': 160, 'height': 52}}
            else:
                excluded[name] = ('JavaScript composition-editor project preset' if 'projectId' in request
                                  else 'unrecognised capture request')
                continue
            requested = set(sampling_requests(recipe['commands']))
            weather = any(c.get('op') == 'emitter' and 'sampling' not in c for c in recipe['commands'])
            if requested & {'braille', 'hybrid'} or weather:
                rows.append((capture, recipe))
            else:
                neither.append(name)
        return rows, excluded, neither

    def test_every_capture_is_replayed_excluded_by_name_or_requests_neither(self):
        captures = self.captures()
        rows, excluded, neither = self.ledger()
        self.assertEqual(excluded, EXCLUDED_CAPTURES)
        self.assertEqual(len(rows) + len(excluded) + len(neither), len(captures['captures']))
        self.assertEqual(len(captures['captures']), captures['captureCount'])

    def test_recorded_braille_and_hybrid_captures_replay_exactly_and_keep_local_policies(self):
        rows = self.ledger()[0]
        self.assertGreaterEqual(len(rows), 32)
        self.assertTrue(any('modelRecords' in recipe for _, recipe in rows), 'no model-resource capture judged')
        jobs = [{'kind': 'reference', 'label': f"reference {c['component']}/{c['state']}", 'recipe': recipe,
                 'timeUs': c['request'].get('timeUs', 0)} for c, recipe in rows]
        results = run_jobs(jobs)
        self.assert_clean(results)
        for (capture, _), result in zip(rows, results):
            self.assertEqual(result.get('cellSha256'), capture['cellSha256'], result['label'] + ' is not the recorded capture')
        self.assertGreater(sum(r['counts'].get('full', 0) for r in results), 0)


class FamilyDefaults(unittest.TestCase, Results):
    """Each family default renders the glyph class MIXED-LAYERS.md declares for it."""

    def test_documented_default_table_is_the_native_default(self):
        documented = documented_defaults()
        self.assertEqual(set(documented), {'environment', 'emitter', 'floor', 'mesh', 'widget'})
        scene = NativeScene(SEED)
        self.addCleanup(scene.close)
        send(scene, {'op': 'emitter', 'id': 1, 'effect': 'weather/autumn-drift', 'count': 1})
        send(scene, {'op': 'widget', 'id': 2, 'kind': 'donut', 'x': 1, 'y': 1, 'width': 20, 'height': 10, 'data': [1]})
        register_layers(scene)
        info = scene.info()
        registry = {r['family']: POLICIES[int(r['authored']['sampling'])] for r in info['registeredStates']}
        native = {'environment': info['environment']['sampling'], 'emitter': info['emitters'][0]['sampling'],
                  'floor': registry['floor'], 'mesh': registry['mesh'], 'widget': info['widgets'][0]['plot']['sampling']}
        self.assertEqual(native, documented)

    def test_default_weather_family_keeps_braille_beside_the_default_hybrid_environment(self):
        catalogue = json.loads((NATIVE / 'catalogue.json').read_text())
        effects = [entry['id'] for entry in catalogue if entry['contract'] == 'ParticleEmitter']
        self.assertGreaterEqual(len(effects), 20)
        jobs = [{'kind': 'default', 'label': 'default weather ' + effect, 'ticks': [50000, 350000, 900000],
                 'commands': [{'op': 'resize', 'width': 80, 'height': 28},
                              {'op': 'emitter', 'id': 1, 'effect': effect, 'count': 16, 'runningTimeMs': 0}]}
                for effect in effects]
        results = run_jobs(jobs)
        self.assert_clean(results)
        for effect, result in zip(effects, results):
            self.assertGreater(result['counts'].get('braille', 0), 0, effect + ' drew no default braille')

    def test_default_floor_mesh_and_settled_deposit_policies(self):
        leaf = {'op': 'emitter', 'id': 2, 'effect': 'weather/autumn-drift', 'count': 1, 'runningTimeMs': 0,
                'position': [0, 1, 0], 'extent': [0, 0, 0], 'velocity': [0, -10, 0], 'spread': [0, 0, 0],
                'gravity': [0, -20, 0], 'wind': [0, 0, 0], 'windVariation': [0, 0, 0], 'drag': 0, 'lift': 0,
                'tumble': [0, 0, 0], 'flutterHz': 0, 'flutterAmount': 0, 'sizeMin': 6, 'sizeMax': 6,
                'deposit': True, 'collision': True, 'lifetimeMinMs': 10000, 'lifetimeMaxMs': 10000, 'birthFadeMs': 0}
        mesh = {'op': 'mesh', 'triangles': [{'a': [-8, 0, -8], 'b': [8, 0, -8], 'c': [8, 6, 8], 'color': 0x8a9a7b, 'alpha': 1},
                                            {'a': [-8, 0, -8], 'b': [8, 6, 8], 'c': [-8, 6, 8], 'color': 0x8a9a7b, 'alpha': 1}]}
        camera = {'op': 'camera', 'position': [0, 18, 35], 'yaw': 0, 'pitch': -25}
        base = [{'op': 'resize', 'width': 96, 'height': 40},
                {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': 0x101010}]
        jobs = [{'kind': 'default', 'label': 'default floor', 'ticks': [0, 500000],
                 'commands': base + [camera, {'op': 'floor', 'visible': True, 'alpha': .4}]},
                {'kind': 'default', 'label': 'default mesh', 'ticks': [0, 500000], 'commands': base + [camera, mesh]},
                {'kind': 'default', 'label': 'default settled deposit', 'ticks': [1500000, 2500000],
                 'commands': base + [dict(camera, orthographic=True, span=32),
                                     {'op': 'floor', 'enabled': True, 'visible': False}, leaf]}]
        results = run_jobs(jobs)
        self.assert_clean(results)
        floor, mesh_result, deposit = results
        self.assertGreater(floor['owners'].get('floor/0', {}).get('half', 0), 0, 'default floor is not half-block')
        self.assertGreater(mesh_result['owners'].get('mesh/0', {}).get('half', 0), 0, 'default mesh is not half-block')
        # Judged only after settling: the one deposit, not a live particle, owns the braille cells.
        self.assertEqual((deposit['deposits'], deposit['live']), (1, 0))
        self.assertGreater(deposit['owners'].get('emitter/2', {}).get('braille', 0), 0, 'settled default deposit lost braille')
        for result in (floor, mesh_result):
            self.assertEqual(result['counts'].get('braille', 0), 0, result['label'] + ' was forced to braille')

    def test_default_geometric_widgets_inherit_the_environment_policy(self):
        widgets = [{'op': 'widget', 'id': 31 + i, 'kind': kind, 'x': 2 + i % 4 * 39, 'y': 2 + i // 4 * 22,
                    'width': 36, 'height': 20, 'padding': 0, 'alpha': 0, 'data': [.2, .9, .4, .7, .6],
                    'value': 88 if kind == 'digits' else .67} for i, kind in enumerate(GEOMETRIC_NAMES)]
        environments = (None, *SAMPLINGS)
        jobs = [{'kind': 'default', 'label': f'default plots under {environment or "default"} environment', 'ticks': [0],
                 'commands': [{'op': 'resize', 'width': 160, 'height': 48},
                              {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': 0x101010},
                              *([{'op': 'environment', 'sampling': environment}] if environment else []), *widgets]}
                for environment in environments]
        results = run_jobs(jobs)
        self.assert_clean(results)
        for environment, result in zip(environments, results):
            policy = environment or 'hybrid'
            for i, kind in enumerate(GEOMETRIC_NAMES):
                with self.subTest(kind=kind, environment=policy):
                    owner = result['owners'].get(f'widget/{31 + i}', {})
                    self.assertGreater(owner.get(policy, 0), 0, f'{kind} did not inherit {policy}')
                    if policy in ('braille', 'hybrid') and kind in FILLED_KINDS:
                        # Hybrid dictates braille for plots: a filled plot keeps U+28FF (operator directive
                        # 2026-11-01), no longer replaced by a block.
                        self.assertGreater(owner.get('full', 0), 0, f'{kind} under {policy} never kept U+28FF')
                    elif policy in ('cell', 'half'):
                        self.assertEqual(owner.get('full', 0), 0)

    def test_bordered_geometric_widgets_keep_their_policy_inside_the_exact_border(self):
        """Every border style around every geometric kind under every explicit policy, on the real patternBox."""
        widgets = [{'op': 'widget', 'id': 51 + 8 * style + i, 'kind': kind, 'x': 2 + 20 * i, 'y': 2 + 12 * style,
                    'width': 19, 'height': 11, 'border': BORDER_NAMES[1 + style], 'padding': 0, 'alpha': 0,
                    'data': [.2, .9, .4, .7, .6], 'value': 88 if kind == 'digits' else .67}
                   for style in range(4) for i, kind in enumerate(GEOMETRIC_NAMES)]
        jobs = [{'kind': 'default', 'label': f'bordered plots requesting {policy}', 'ticks': [0],
                 'commands': [{'op': 'resize', 'width': 164, 'height': 52},
                              {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': 0x101010},
                              *[dict(widget, sampling=policy) for widget in widgets]]}
                for policy in SAMPLINGS]
        results = run_jobs(jobs)
        self.assert_clean(results)
        for policy, result in zip(SAMPLINGS, results):
            self.assertEqual(result.get('requested'), len(widgets))
            for widget in widgets:
                with self.subTest(policy=policy, kind=widget['kind'], border=widget['border']):
                    owner = result['owners'].get(f"widget/{widget['id']}", {})
                    self.assertEqual(owner.get('border', 0), 2 * 19 + 2 * 11 - 4, 'the whole ring is its border')
                    self.assertGreater(owner.get(policy, 0), 0, f"{widget['kind']} lost {policy} inside its border")

    def test_surface_fields_follow_the_environment_policy(self):
        catalogue = json.loads((NATIVE / 'catalogue.json').read_text())
        fields = [entry['id'] for entry in catalogue if entry['contract'] == 'SurfaceField']
        self.assertGreaterEqual(len(fields), 4)
        environments = (None, *SAMPLINGS)
        jobs = [{'kind': 'default', 'label': f'surface fields under {environment or "default"} environment',
                 'ticks': [350000], 'environmentCells': True,
                 'commands': [{'op': 'resize', 'width': 160, 'height': 48}, {'op': 'environment', 'stars': 0},
                              *([{'op': 'environment', 'sampling': environment}] if environment else []),
                              *[{'op': 'field', 'effect': effect, 'x': 20 + 40 * i, 'y': 14 + 10 * (i % 2), 'lifeMs': 2000}
                                for i, effect in enumerate(fields)]]}
                for environment in environments]
        results = run_jobs(jobs)
        self.assert_clean(results)
        # Spaces are not judged: the default workbench header's word gaps are unowned hit-0 text.
        allowed = {'cell': set(), 'half': {'half'}, 'braille': {'braille', 'full'}, 'hybrid': {'braille', 'half'}}
        for environment, result in zip(environments, results):
            policy = environment or 'hybrid'
            with self.subTest(environment=policy):
                cells = result['environmentCells']
                geometric = {key for key in cells if key in ('full', 'braille', 'half', 'block')}
                self.assertLessEqual(geometric, allowed[policy], cells)
                self.assertTrue(geometric if policy != 'cell' else cells.get('space'), cells)


class JudgeDiscrimination(unittest.TestCase):
    """Oracle check on a real frame: the judge accepts it and flags each injected fault class.

    One cell of a real rendered frame (real glyphs, owner plane and widget frames) is replaced; the
    engine is not changed. RED for these tests is the judge without the corresponding rule.
    """

    @classmethod
    def setUpClass(cls):
        data = [.1, .8, .3, .95, .2, .7, .5, .9, .15, .6]
        scene = NativeScene(SEED)
        try:
            for command in ({'op': 'resize', 'width': 96, 'height': 30},
                            {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': 0x101010},
                            {'op': 'widget', 'id': 41, 'kind': 'line', 'x': 2, 'y': 2, 'width': 44, 'height': 14,
                             'border': 'rounded', 'padding': 0, 'alpha': 0, 'sampling': 'braille', 'data': data},
                            {'op': 'widget', 'id': 42, 'kind': 'line', 'x': 50, 'y': 2, 'width': 44, 'height': 14,
                             'padding': 0, 'alpha': 0, 'sampling': 'braille', 'data': data}):
                send(scene, command)
            register_layers(scene)
            cls.info = scene.info()
            frame = scene.render()
            words = array('I', frame.bytes)
            cls.width, cls.glyphs, cls.hits = frame.width, words[0::4], words[3::4]
            cls.owners = owner_plane(scene, frame.width, frame.height)
            cls.environment, cls.table = layer_table(cls.info)
            cls.frames = widget_frames(cls.info)
        finally:
            scene.close()

    def judged(self, faults=()):
        glyphs = array('I', self.glyphs)
        for index, glyph in faults:
            glyphs[index] = glyph
        judge = Judge('oracle')
        judge.cells(0, glyphs, self.hits, glyphs, self.width, self.owners, self.environment, self.table, self.frames)
        return judge

    def plot_cells(self, target):
        """Owned braille cells of a widget: (index, on its frame's outer ring)."""
        x, y, width, height, _ = self.frames[target]
        out = []
        for index, path in self.owners:
            if self.table.get(path, ())[:2] == ('widget', target) and is_braille(self.glyphs[index]):
                cx, cy = index % self.width, index // self.width
                out.append((index, cx in (x, x + width - 1) or cy in (y, y + height - 1)))
        return out

    def assert_flagged(self, index, glyph):
        violations = self.judged([(index, glyph)]).violations
        self.assertEqual([v[2:4] for v in violations], [(index % self.width, index // self.width)], hex(glyph))

    def test_the_real_frame_is_accepted_with_its_whole_border(self):
        judge = self.judged()
        self.assertEqual(judge.violations, [])
        self.assertEqual(judge.owners['widget/41'].get('border'), 2 * 44 + 2 * 14 - 4)
        self.assertNotIn('border', judge.owners['widget/42'])
        for owner in ('widget/41', 'widget/42'):
            self.assertGreater(judge.owners[owner].get('braille', 0), 0, owner)

    def test_box_drawing_inside_a_bordered_plot_is_flagged(self):
        interior = [index for index, ring in self.plot_cells(41) if not ring]
        self.assertTrue(interior)
        for glyph in (0x2500, 0x2502, 0x2571, 0x256d, 0x2550):
            with self.subTest(glyph=hex(glyph)):
                self.assert_flagged(interior[0], glyph)

    def test_a_ring_cell_holds_only_the_glyph_patternbox_draws_there(self):
        x, y, width, height, border = self.frames[41]
        self.assertEqual(border, 1)
        corner, top, side = y * self.width + x, y * self.width + x + 3, (y + 3) * self.width + x
        self.assertEqual([self.glyphs[i] for i in (corner, top, side)], [0x256d, 0x2500, 0x2502])
        for index, glyph in ((corner, 0x2500), (corner, 0x250c), (top, 0x2550), (top, 0x2502), (side, 0x2500),
                             (side, 0x2551)):
            with self.subTest(cell=(index % self.width, index // self.width), glyph=hex(glyph)):
                self.assert_flagged(index, glyph)

    def test_a_borderless_plot_owns_no_box_drawing(self):
        cells = sorted(self.plot_cells(42), key=lambda cell: not cell[1])  # Frame-edge cells first.
        self.assertTrue(cells)
        for glyph in (0x2500, 0x2502, 0x256d):
            with self.subTest(glyph=hex(glyph)):
                self.assert_flagged(cells[0][0], glyph)

    def test_bullets_and_blocks_in_a_braille_plot_are_flagged(self):
        interior = [index for index, ring in self.plot_cells(41) if not ring]
        for glyph in (0x2022, 0x2588, 0x2580, 0x2584):
            with self.subTest(glyph=hex(glyph)):
                self.assert_flagged(interior[0], glyph)

    def requests_reported(self, edit, restyled=False):
        info = json.loads(json.dumps(self.info))
        edit({(r['family'], r['targetId']): r for r in info['registeredStates']})
        result = {'failures': []}
        check_requests(Checks(result), info, explicit_sampling([{'op': 'widget', 'id': 41, 'sampling': 'braille'}]),
                       restyled, 'oracle', set())
        return result['failures']

    def test_an_explicit_request_must_be_the_stored_and_effective_policy(self):
        self.assertEqual(self.requests_reported(lambda rows: None), [])

        def stored_hybrid(rows):
            rows[('widget', 41)]['authored']['sampling'] = rows[('widget', 41)]['effective']['sampling'] = 3
        self.assertEqual(len(self.requests_reported(stored_hybrid)), 1)

        def resolved_hybrid(rows):
            rows[('widget', 41)]['effective']['sampling'] = 3
        self.assertEqual(len(self.requests_reported(resolved_hybrid)), 1)
        # Only a sampling style rule may make the effective policy differ from the authored one.
        self.assertEqual(self.requests_reported(resolved_hybrid, restyled=True), [])


class HybridJudgeDiscrimination(unittest.TestCase):
    """The judge on a real hybrid frame: hybrid plots are held to braille, a hybrid floor to half blocks.

    An explicit-hybrid pie and a donut inheriting the default hybrid environment sit above a hybrid floor.
    The real frame must be accepted with U+28FF on both plots (operator directive 2026-11-01), and each
    injected fault must be flagged at exactly its cell. RED before the engine change: the real frame then
    showed U+2580 and contrast masks on the hybrid plots and contrast braille on the hybrid floor.
    """

    @classmethod
    def setUpClass(cls):
        scene = NativeScene(SEED)
        try:
            for command in ({'op': 'resize', 'width': 96, 'height': 30},
                            {'op': 'environment', 'stars': 0, 'style': 'solid', 'background': 0x101010},
                            {'op': 'camera', 'position': [0, 18, 35], 'yaw': 0, 'pitch': -25},
                            {'op': 'floor', 'visible': True, 'alpha': .4, 'sampling': 'hybrid'},
                            {'op': 'widget', 'id': 43, 'kind': 'pie', 'x': 2, 'y': 1, 'width': 40, 'height': 12,
                             'padding': 0, 'alpha': 0, 'sampling': 'hybrid', 'data': [3, 2, 4]},
                            {'op': 'widget', 'id': 44, 'kind': 'donut', 'x': 52, 'y': 1, 'width': 40, 'height': 12,
                             'padding': 0, 'alpha': 0, 'data': [5, 2, 3]}):
                send(scene, command)
            register_layers(scene)
            info = scene.info()
            frame = scene.render()
            words = array('I', frame.bytes)
            cls.width, cls.glyphs, cls.hits = frame.width, words[0::4], words[3::4]
            cls.owners = owner_plane(scene, frame.width, frame.height)
            cls.environment, cls.table = layer_table(info)
            cls.frames = widget_frames(info)
        finally:
            scene.close()

    def judged(self, faults=(), twin_faults=()):
        glyphs, twins = array('I', self.glyphs), array('I', self.glyphs)
        for index, glyph in faults:
            glyphs[index] = twins[index] = glyph
        for index, glyph in twin_faults:
            twins[index] = glyph
        judge = Judge('hybrid oracle')
        judge.cells(0, glyphs, self.hits, twins, self.width, self.owners, self.environment, self.table, self.frames)
        return judge

    def owned(self, family, target, predicate):
        return [index for index, path in self.owners
                if self.table.get(path, ())[:2] == (family, target) and predicate(self.glyphs[index])]

    def assert_flagged(self, judge, index):
        self.assertEqual([v[2:4] for v in judge.violations], [(index % self.width, index // self.width)])

    def test_the_real_hybrid_frame_is_accepted_with_u28ff_on_both_plots(self):
        self.assertEqual({self.table[path][:3] for _, path in self.owners if path in self.table},
                         {('widget', 43, 'hybrid'), ('widget', 44, 'hybrid'), ('floor', 0, 'hybrid')})
        judge = self.judged()
        self.assertEqual(judge.violations, [])
        for owner in ('widget/43', 'widget/44'):
            self.assertGreater(judge.owners[owner].get('full', 0), 0, owner + ' never kept U+28FF')
            self.assertGreater(judge.owners[owner].get('hybrid', 0), 0, owner)
        self.assertGreater(judge.owners['floor/0'].get('half', 0), 0)
        self.assertNotIn('braille', judge.owners['floor/0'])

    def test_a_block_in_a_hybrid_plot_is_flagged(self):
        full = self.owned('widget', 43, lambda glyph: glyph == FULL)
        self.assertTrue(full)
        for glyph in (0x2588, HALF, 0x2584):
            with self.subTest(glyph=hex(glyph)):
                self.assert_flagged(self.judged([(full[0], glyph)]), full[0])

    def test_braille_on_a_hybrid_floor_is_flagged(self):
        floor = self.owned('floor', 0, lambda glyph: glyph == HALF)
        self.assertTrue(floor)
        for glyph in (FULL, 0x2857, 0x2801):
            with self.subTest(glyph=hex(glyph)):
                self.assert_flagged(self.judged([(floor[0], glyph)]), floor[0])

    def test_a_hybrid_glyph_that_follows_the_backdrop_is_flagged(self):
        full = self.owned('widget', 44, lambda glyph: glyph == FULL)
        floor = self.owned('floor', 0, lambda glyph: glyph == HALF)
        self.assertTrue(full, 'the inherited hybrid donut shows no U+28FF')
        self.assertTrue(floor, 'the hybrid floor shows no half block')
        for index, twin in ((full[0], 0x2857), (floor[0], 0x2857)):
            with self.subTest(cell=(index % self.width, index // self.width)):
                self.assert_flagged(self.judged(twin_faults=[(index, twin)]), index)


if __name__ == '__main__':
    unittest.main()
