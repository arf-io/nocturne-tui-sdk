"""RC4-022 lifecycle and end-transition matrix against the actual native C core.

Every axis is derived from the native tables (commands.c choices, validate.c
bounds, weather.c applicability, the state.c phase vocabulary and the
catalog.inc effect table) and compared with each document that publishes it,
so documentation drift fails this module. Expected terminal behaviour is
computed from the documented rules in EMITTER-CANCEL.md, EMITTER-RESUME.md,
WEATHER-ENDINGS.md, AGGREGATE-FADE.md, manual/LIFECYCLE-AND-TEARDOWN.md and
ARCHITECTURE.md section 11; it is never copied from recorded output. Every case
executes libnocturne_native through the C ABI. Nothing is mocked.
"""
import hashlib
import importlib.util
import json
import re
import sys
import unittest
import zlib
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPO = NATIVE.parent
sys.path.insert(0, str(NATIVE / 'bindings/python'))
from nocturne_native import NativeScene  # noqa: E402

SEED = 2030
TAIL_US = 400000        # 48 simulation steps
ENTRY_US = 250000       # boundary 30: first lifecycle transaction
SECOND_US = 350000      # boundary 42: second transaction of a compound entry
WIND_US = 1000000       # wind above the floor re-entrainment speed
FINAL_US = 2000000
WIND = [20, 0, 0]       # drag stays 0, so live motion is unchanged by this edit
MATRIX_EFFECT = 'weather/thermal-cinders'
DESTRUCTIVE_TO_DRAIN = 'Destructive ending cannot return to drain'
NUMBER_WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7}


def boundary_us(step):
    return step * 1000000 // 120


def last_step_at_or_before(us):
    """The native rational clock inverse (nrStepAt)."""
    return ((us + 1) * 120 - 1) // 1000000


def first_step_at_or_after(us):
    step = last_step_at_or_before(us)
    return step if boundary_us(step) >= us else step + 1


def one(pattern, text, what, flags=0):
    found = re.findall(pattern, text, flags)
    if len(found) != 1:
        raise AssertionError(f'{what}: expected one authoritative match, found {len(found)}')
    return found[0]


def ticks(text):
    return re.findall(r'`([^`]+)`', text)


def flat(text):
    return ' '.join(text.split())


class Vocabulary:
    """Lists read from the native source tables, never typed by hand."""

    def __init__(self):
        commands = (NATIVE / 'src/commands.c').read_text()
        self.emitter_styles = one(r'CHOICE\("endStyle",q->endStyle,"([^"]+)"\)', commands,
                                  'emitter endStyle choice table').split()
        self.stop_styles = one(r'CHOICE\("style",q->endStyle,"([^"]+)"\)', commands,
                               'stop/cancel style choice table').split()
        excluded, self.cancel_error = one(r'CHECK\(!cancel\|\|q->endStyle!=(\d+),"([^"]+)"\)',
                                          commands, 'cancel exclusion')
        self.cancel_excluded = self.stop_styles[int(excluded)]
        self.cancel_styles = [s for s in self.stop_styles if s != self.cancel_excluded]
        self.cancel_default = self.stop_styles[int(one(r'if\(cancel&&q->endStyle==0\)q->endStyle=(\d+);',
                                                       commands, 'cancel default'))]
        lifecycle = commands[commands.index('if(!strcmp(op,"resume"))'):
                             commands.index('if(!strcmp(op,"clear-instance"))')]
        self.resume_error = one(r'CHECK\(q->endStyle==0,"([^"]+)"\)', lifecycle, 'resume rule')
        self.missing_error = sorted(set(re.findall(r'CHECK\(i>=0,"([^"]+)"\)', lifecycle)))
        self.unsupported_error = sorted(set(re.findall(
            r'CHECK\(nrEndStyleSupported\(q->effect,q->endStyle\),"([^"]+)"\)', commands)))
        validate = (NATIVE / 'src/validate.c').read_text()
        self.snapshot_bound = int(one(r'e->endStyle<0\|\|e->endStyle>(\d+)', validate, 'snapshot bound'))
        self.snapshot_checks_support = 'if(!nrEndStyleSupported(e->effect,e->endStyle))return 0;' in validate
        weather = (NATIVE / 'src/weather.c').read_text()
        restricted, algorithms = one(r'return style!=(\d+)((?:\|\|algorithm==\d+)+);', weather,
                                     'ending applicability rule')
        self.restricted_style = self.stop_styles[int(restricted)]
        self.restricted_algorithms = sorted(int(a) for a in re.findall(r'algorithm==(\d+)', algorithms))
        state = (NATIVE / 'src/state.c').read_text()
        self.phases = re.findall(r'"([a-z]+)"', one(r'const char\*phase=([^;]+);', state, 'phase vocabulary'))
        catalog = (NATIVE / 'src/catalog.inc').read_text()
        table = catalog[catalog.index('EFFECTS[]={'):]
        table = table[:table.index('};')]
        self.effects = [(name, int(f), int(a), int(p))
                        for name, f, a, p in re.findall(r'\{"([^"]+)",(\d+),(\d+),(\d+)\}', table)]
        self.particle_effects = [e for e in self.effects if e[1] == 0]

    def supports(self, algorithm, style):
        return style != self.restricted_style or algorithm in self.restricted_algorithms

    def representatives(self):
        """The first catalogue particle effect of every native algorithm, in table order."""
        chosen = {}
        for name, _, algorithm, _ in self.particle_effects:
            chosen.setdefault(algorithm, name)
        return sorted((algorithm, name) for algorithm, name in chosen.items())


def documented_table_row(markdown, field):
    return one(r'^\| `' + re.escape(field) + r'`[^|]*\|(.*)$', markdown, 'manual row ' + field, re.M)


def documented_choices(markdown, section, field):
    block = one(r'^## ' + re.escape(section) + r'\n(.*?)(?=^## |\Z)', markdown, 'parameter section ' + section,
                re.M | re.S)
    row = one(r'^\| `' + re.escape(field) + r'` \|(.*)$', block, 'parameter row ' + field, re.M)
    cells = [cell.strip() for cell in re.split(r'(?<!\\)\|', row)]
    return json.loads(cells[1])


PRELUDE = (
    {'op': 'resize', 'width': 72, 'height': 28},
    {'op': 'camera', 'position': [0, 3, 18], 'yaw': 0, 'pitch': -6, 'fov': 60},
    {'op': 'environment', 'stars': 0, 'background': 0, 'style': 'solid'},
    {'op': 'floor', 'enabled': True, 'visible': False, 'height': 0, 'reentrainWindSpeed': 6},
)


def emitter(effect, **patch):
    command = {'op': 'emitter', 'id': 1, 'effect': effect, 'seed': 4242, 'shape': 'point',
               'position': [0, 4, 0], 'extent': [0, 0, 0], 'velocity': [0, 0, 0],
               'spread': [1.5, 1.5, 1.5], 'gravity': [0, 0, 0], 'wind': [0, 0, 0],
               'windVariation': [0, 0, 0], 'drag': 0, 'lift': 0, 'flutterAmount': 0, 'heat': 0,
               'radius': 10, 'collision': False, 'deposit': False, 'count': 6, 'runningTimeMs': 500,
               'lifetimeMinMs': 300, 'lifetimeMaxMs': 1500, 'tailMs': TAIL_US // 1000, 'endStyle': 'drain'}
    command.update(patch)
    return command


# Each setup is asserted to reach its phase at ENTRY_US before any transaction.
PHASE_SETUPS = {
    'scheduled': {'startTimeUs': 600000, 'runningTimeMs': 300},
    'emitting': {},
    'draining': {'runningTimeMs': 100},
    'settled': {'runningTimeMs': 0, 'position': [0, .05, 0], 'velocity': [0, -1.5, 0], 'spread': [3, 0, 3],
                'collision': True, 'deposit': True, 'lifetimeMinMs': 3000, 'lifetimeMaxMs': 3000},
    'terminal': {'runningTimeMs': 0, 'lifetimeMinMs': 100, 'lifetimeMaxMs': 100},
}
LIVE_PHASES = ('emitting', 'draining')


def observe(scene):
    info = scene.info()
    rows = info['emitters']
    row = rows[0] if rows else None
    counts = info['particles']
    return {
        'clock': (info['clock']['timeUs'], info['clock']['step']),
        'particles': tuple(scene.particles()),
        'deposits': tuple(d['id'] for d in info['deposits']),
        'counts': (counts['active'], counts['deposited'], counts['aggregated'], counts['born']),
        'emitter': None if row is None else (row['phase'], row['attemptedBirths'], row['active'], row['deposited']),
    }


class Run:
    def __init__(self):
        self.records = []
        self.phases = set()
        self.checkpoint = None
        self.checkpoint_index = None
        self.final = None


def run_timeline(test, events, *, model=None, partition=False, restore=None, start=0):
    """Execute a recorded journal in a fresh context. A model makes it the asserting direct run."""
    result = Run()
    with NativeScene(SEED) as scene:
        if restore is not None:
            scene.restore(restore)
        clock = None
        known = None      # a snapshot proven equal to the current authoritative state
        unverified = []   # non-mutating transactions awaiting one snapshot comparison
        for index in range(start, len(events) + 1):
            event = events[index] if index < len(events) else ('end',)
            kind = event[0]
            probe = kind == 'command' and event[2] is not None
            if unverified and not probe:
                test.assertTrue(scene.snapshot() == known,
                                'Transaction changed authoritative state: ' + json.dumps(unverified))
                unverified = []
            if kind == 'end':
                break
            if kind == 'at':
                target = event[1]
                if clock is None:
                    clock = scene.info()['clock']['timeUs']
                part = clock + (target - clock) // 2 + 1
                if partition and clock < part < target:
                    scene.advance_to(part)
                scene.advance_to(target)
                clock = target
                known = None
            elif kind == 'command':
                _, command, expect, keep_rows = event
                if expect is None:
                    before = observe(scene) if model is not None and keep_rows else None
                    scene.command(command)
                    known = None
                    if before is not None:
                        after = observe(scene)
                        test.assertEqual(after['particles'], before['particles'],
                                         'A lifecycle transaction replaced particle rows: ' + json.dumps(command))
                        test.assertEqual(after['deposits'], before['deposits'],
                                         'A lifecycle transaction changed scene-owned deposits')
                    continue
                if model is not None and known is None:
                    known = scene.snapshot()
                if expect == 'same':
                    scene.command(command)
                else:
                    with test.assertRaises(ValueError, msg=json.dumps(command)) as caught:
                        scene.command(command)
                    test.assertEqual(str(caught.exception), expect, json.dumps(command))
                if model is not None:
                    unverified.append(command)
            elif kind == 'mark':
                if model is not None:
                    model.mark(observe(scene))
            elif kind == 'checkpoint':
                if model is not None:
                    result.checkpoint = known if known is not None else scene.snapshot()
                    known = result.checkpoint
                result.checkpoint_index = index
            elif kind == 'sample':
                label = event[1]
                if model is not None and known is None:
                    known = scene.snapshot()
                observed = observe(scene)
                frame = scene.render().bytes
                scene.info()
                scene.info_complete()
                if model is not None:
                    test.assertTrue(scene.snapshot() == known, 'Render/info changed authoritative state at ' + label)
                    test.assertEqual(observe(scene), observed, 'Particle identity or accounting changed across a render')
                    test.assertEqual(scene.render().bytes, frame, 'Repeated rendering is not idempotent at ' + label)
                    model.check(label, observed)
                    if observed['emitter'] is not None:
                        result.phases.add(observed['emitter'][0])
                result.records.append((index, label, observed, hashlib.sha256(frame).hexdigest()))
        result.final = scene.snapshot()
    return result


class Timeline:
    def __init__(self):
        self.events = []

    def command(self, command, expect=None, keep_rows=False):
        self.events.append(('command', command, expect, keep_rows))

    def at(self, us):
        self.events.append(('at', us))

    def sample(self, label):
        self.events.append(('sample', label))

    def mark(self):
        self.events.append(('mark',))

    def checkpoint(self):
        self.events.append(('checkpoint',))


_PENDING_BIRTH = {}


def pending_birth(phase):
    """Births at ENTRY_US and the boundary of the next scheduled birth when never stopped."""
    if phase not in _PENDING_BIRTH:
        authored = emitter(MATRIX_EFFECT, **PHASE_SETUPS[phase])
        with NativeScene(SEED) as scene:
            scene.batch([*PRELUDE, authored])
            scene.advance_to(ENTRY_US)
            births = scene.info()['emitters'][0]['attemptedBirths']
            step, found = last_step_at_or_before(ENTRY_US), None
            # EMITTER-RESUME: a finite schedule that consumed every ordinal stays complete.
            while births < authored['count'] * authored.get('cycles', 1) and found is None:
                step += 1
                scene.advance_to(boundary_us(step))
                if scene.info()['emitters'][0]['attemptedBirths'] > births:
                    found = step
            _PENDING_BIRTH[phase] = (births, found)
    return _PENDING_BIRTH[phase]


def matrix_cells(vocabulary):
    cells = []
    for phase in vocabulary.phases:
        cells += [(phase, 'stop', style) for style in vocabulary.stop_styles]
        cells += [(phase, 'cancel', style) for style in vocabulary.cancel_styles]
    cells += [('emitting', 'natural', style) for style in vocabulary.emitter_styles]
    for phase in LIVE_PHASES:
        cells += [(phase, 'drain-cancel', style) for style in vocabulary.cancel_styles]
        cells += [(phase, 'drain-stop', style) for style in vocabulary.cancel_styles]
    return cells


def cell_timeline(vocabulary, cell):
    """Recorded journal and documented expectations for one matrix cell."""
    phase, entry, style = cell
    drain = vocabulary.cancel_excluded
    setup = dict(PHASE_SETUPS[phase])
    if entry == 'natural':
        setup['endStyle'] = style
    authored = emitter(MATRIX_EFFECT, **setup)
    tail = {'tailMs': TAIL_US // 1000}
    if entry in ('stop', 'cancel'):
        transactions = [(ENTRY_US, {'op': entry, 'id': 1, 'style': style, **tail})]
        origin = ENTRY_US
    elif entry == 'natural':
        # ARCHITECTURE 11: runningTime controls emission and the tail bounds the ending.
        transactions = []
        origin = authored.get('startTimeUs', 0) + authored['runningTimeMs'] * 1000
    else:
        second = 'cancel' if entry == 'drain-cancel' else 'stop'
        transactions = [(ENTRY_US, {'op': 'stop', 'id': 1, 'style': drain, **tail}),
                        (SECOND_US, {'op': second, 'id': 1, 'style': style, **tail})]
        # EMITTER-CANCEL: cancelling suspended drain starts its own ending clock.
        # LIFECYCLE-AND-TEARDOWN: repeating stop keeps the first stop origin.
        origin = SECOND_US if second == 'cancel' else ENTRY_US
    destructive = style != drain
    deadline = origin + TAIL_US
    mid = origin + TAIL_US // 2
    dead = first_step_at_or_after(deadline)
    t = Timeline()
    t.command({'op': 'batch', 'commands': [*PRELUDE, authored]})
    t.at(ENTRY_US)
    t.sample('pre-entry')
    for when, command in transactions:
        if when != ENTRY_US:
            t.at(when)
        t.command(command, keep_rows=True)
        if when == ENTRY_US:
            t.mark()
        t.sample('transaction')
    if entry == 'natural':
        t.at(origin)
        t.mark()
        t.sample('origin')
    t.at(mid)
    t.sample('mid')
    t.checkpoint()
    last = transactions[-1][1] if transactions else None
    if last is not None:
        t.command(last, 'same')
    elif destructive:
        t.command({'op': 'stop', 'id': 1, 'style': style, **tail}, 'same')
    t.command({'op': 'cancel', 'id': 1, 'style': drain}, vocabulary.cancel_error)
    if destructive:
        t.command({'op': 'resume', 'id': 1}, vocabulary.resume_error)
        t.command({'op': 'stop', 'id': 1, 'style': drain}, DESTRUCTIVE_TO_DRAIN)
    elif entry == 'natural':
        t.command({'op': 'resume', 'id': 1}, 'same')
    t.at(boundary_us(dead - 1))
    t.sample('before-deadline')
    t.at(boundary_us(dead))
    t.sample('deadline')
    t.at(WIND_US)
    t.command({'op': 'forces', 'id': 1, 'wind': WIND})
    t.at(WIND_US + 200000)
    t.sample('after-wind')
    t.at(FINAL_US)
    t.sample('final')
    if destructive:
        t.command({'op': 'resume', 'id': 1}, vocabulary.resume_error)
    elif entry == 'natural':
        t.command({'op': 'resume', 'id': 1}, 'same')
    else:
        # EMITTER-RESUME: the stopped interval shifts the schedule, without catch-up births.
        t.command({'op': 'resume', 'id': 1})
        births, step = pending_birth(phase)
        if step is None:
            t.at(FINAL_US + TAIL_US)
            t.sample('resume-complete')
        else:
            elapsed = (FINAL_US - ENTRY_US) * 120 // 1000000
            t.at(boundary_us(step + elapsed - 1))
            t.sample('resume-pending')
            t.at(boundary_us(step + elapsed))
            t.sample('resume-birth')
    return t.events, {'destructive': destructive, 'deadline': deadline, 'origin': origin}


class CellModel:
    """Documented terminal behaviour, evaluated in the direct run only."""

    def __init__(self, test, cell, spec):
        self.test = test
        self.cell = cell
        self.destructive = spec['destructive']
        self.dead_step = first_step_at_or_after(spec['deadline'])
        self.rows = None
        self.natural_deaths = 0
        self.deadline_cuts = 0
        self.drain_survivors = 0

    def mark(self, observed):
        self.rows = {row[0]: (row[9], row[11]) for row in observed['particles']}
        self.births = observed['emitter'][1]
        self.deposits = observed['deposits']
        if self.cell[0] in LIVE_PHASES:
            self.test.assertTrue(self.rows, 'A live phase must have particles at the transaction')
        if self.cell[0] == 'settled':
            self.test.assertTrue(self.deposits, 'The settled phase must own deposits')

    def check(self, label, observed):
        t = self.test
        phase, entry, style = self.cell
        state = observed['emitter']
        if label == 'pre-entry':
            t.assertEqual(state[0], phase, 'Setup did not reach the lifecycle phase under test')
            return
        if self.rows is None:
            t.assertEqual(state[0], 'emitting')
            return
        step = observed['clock'][1]
        if label.startswith('resume-'):
            t.assertEqual(state[1], self.births + (label == 'resume-birth'),
                          'Resume must preserve the remaining interval without catch-up births')
            return
        t.assertEqual(state[1], self.births, 'Births continued after the lifecycle transaction')
        live = {row[0] for row in observed['particles']}
        if phase == 'settled' and not self.destructive and label in ('after-wind', 'final'):
            # Drain retains deposit physics: re-entrainment keeps every identity.
            deposits = set(observed['deposits'])
            t.assertEqual(live | deposits, set(self.deposits))
            t.assertFalse(live & deposits)
            t.assertTrue(live, 'A drain stop must not suspend deposit re-entrainment')
            expected_live, expected_deposits = live, observed['deposits']
        else:
            if self.destructive and step >= self.dead_step:
                expected_live = set()
            else:
                expected_live = {ident for ident, (born, life) in self.rows.items() if born + life > step}
            t.assertEqual(live, expected_live, f'{label}: live identities differ from lifetime/tail rule')
            t.assertEqual(observed['deposits'], self.deposits, f'{label}: an ending changed scene-owned deposits')
            expected_deposits = self.deposits
        if label == 'before-deadline':
            self.natural_deaths += sum(born + life <= step for born, life in self.rows.values())
            self.deadline_cuts += sum(born + life > self.dead_step for born, life in self.rows.values())
        if label == 'deadline' and not self.destructive:
            self.drain_survivors += len(live)
        expected_phase = 'draining' if expected_live else 'settled' if expected_deposits else 'terminal'
        t.assertEqual(state[0], expected_phase, f'{label}: phase does not reflect live/deposited ownership')


class NativeVocabulary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.V = Vocabulary()

    def test_end_policies_derived_from_native_tables_match_every_publication(self):
        V = self.V
        self.assertEqual(V.emitter_styles, V.stop_styles, 'authoring and stop must share one ending table')
        self.assertEqual(len(V.stop_styles), V.snapshot_bound + 1, 'snapshot validation bound drifted')
        self.assertTrue(V.snapshot_checks_support, 'snapshot validation must apply the effect ending guard')
        self.assertEqual(len(V.unsupported_error), 1)
        self.assertEqual(V.cancel_excluded, V.stop_styles[0])
        api = flat((NATIVE / 'docs/API.md').read_text())
        self.assertEqual(re.split(r',\s*|\s+and\s+', one(r'Supported styles: ([^.]+)\.', api, 'API styles')),
                         V.stop_styles)
        manual = (NATIVE / 'docs/manual/LIFECYCLE-AND-TEARDOWN.md').read_text()
        self.assertEqual(ticks(documented_table_row(manual, 'stop.style').split('|')[1]), V.stop_styles)
        cancel = documented_table_row(manual, 'cancel.style')
        self.assertEqual(one(r'except `([^`]+)`', cancel, 'cancel exclusion'), V.cancel_excluded)
        self.assertEqual(one(r'drain becomes (\w+)', cancel, 'cancel default'), V.cancel_default)
        weather = (NATIVE / 'docs/manual/WEATHER-AND-EMITTERS.md').read_text()
        cells = documented_table_row(weather, 'endStyle').split('|')
        self.assertEqual(ticks(cells[0]), [V.emitter_styles[0]], 'documented authoring default')
        self.assertEqual(ticks(cells[1]), V.emitter_styles)
        help_rows = json.loads((REPO / 'docs/current/command-help.json').read_text())['parameters']
        for key in ('emitter.endStyle', 'stop.style'):
            self.assertEqual(ticks(help_rows[key]['description']), V.stop_styles, key)
        self.assertEqual(one(r'except `([^`]+)`', help_rows['cancel.style']['description'], 'help cancel'),
                         V.cancel_excluded)
        self.assertIn('drain becomes ' + V.cancel_default, help_rows['cancel.style']['default'])
        fields = {(row['op'], row['field']): row['choices']
                  for row in json.loads((NATIVE / 'web/workshop_fields.json').read_text())['fields']}
        for key in (('emitter', 'endStyle'), ('stop', 'style'), ('weather-author', 'lifecycle.endStyle')):
            self.assertEqual(fields[key], V.stop_styles, key)
        self.assertEqual(fields['cancel', 'style'], V.cancel_styles)
        parameters = (NATIVE / 'docs/COMMAND-PARAMETERS.md').read_text()
        for section, field, expected in (('emitter', 'endStyle', V.stop_styles), ('stop', 'style', V.stop_styles),
                                         ('cancel', 'style', V.cancel_styles),
                                         ('weather-author', 'lifecycle.endStyle', V.stop_styles)):
            self.assertEqual(documented_choices(parameters, section, field), expected, (section, field))
        contracts = (NATIVE / 'bindings/typescript/contracts.ts').read_text()
        self.assertEqual(re.findall(r"'([a-z]+)'", one(r'export type EndStyle = ([^;]+);', contracts, 'EndStyle')),
                         V.stop_styles)
        self.assertEqual(one(r"op:'cancel';id:number;style\?:Exclude<EndStyle,'([a-z]+)'>", contracts, 'cancel type'),
                         V.cancel_excluded)
        resume = flat((NATIVE / 'docs/EMITTER-RESUME.md').read_text())
        self.assertEqual(re.split(r',\s*|\s+or\s+', one(r'destructive ending \(([^)]+)\)', resume, 'resume')),
                         V.cancel_styles)
        policy = flat((NATIVE / 'docs/TDD-END-POLICIES-20261012.md').read_text())
        stops, cancels = one(r'(\w+) stop styles and (\w+) supported cancel styles', policy, 'end policy counts')
        self.assertEqual((NUMBER_WORDS[stops], NUMBER_WORDS[cancels]), (len(V.stop_styles), len(V.cancel_styles)))

    def test_lifecycle_phases_derived_from_native_info_match_documented_states(self):
        V = self.V
        architecture = flat((NATIVE / 'docs/ARCHITECTURE.md').read_text())
        states = one(r'Separate these states: ([^.]+)\.', architecture, 'ARCHITECTURE section 11').split(', ')
        self.assertEqual(len(states), len(V.phases))
        for documented, native in zip(states, V.phases):
            self.assertIn(native, documented.split('/'), 'native phase vocabulary drifted from ARCHITECTURE 11')
        backlog = json.loads((REPO / 'RC4-BACKLOG.json').read_text())
        item = next(entry for entry in backlog['items'] if entry['id'] == 'RC4-022')
        self.assertEqual(one(r'Distinct ([a-z/]+) states', item['acceptance'], 'RC4-022').split('/'), V.phases)
        self.assertEqual(set(PHASE_SETUPS), set(V.phases), 'every native phase needs a matrix setup')
        self.assertTrue(set(LIVE_PHASES) <= set(V.phases))

    def test_lifecycle_operations_are_the_documented_command_family(self):
        help_rows = json.loads((REPO / 'docs/current/command-help.json').read_text())['parameters']
        section = 'Stop, cancel and resume an emitter'
        operations = {key.split('.')[0] for key, row in help_rows.items() if row['section'] == section}
        styled = {key.split('.')[0] for key, row in help_rows.items()
                  if row['section'] == section and key.endswith('.style')}
        self.assertEqual(operations, {'stop', 'cancel', 'resume'})
        self.assertEqual(styled, {'stop', 'cancel'}, 'only stop and cancel select an ending')
        self.assertEqual(help_rows['emitter.endStyle']['section'], 'Lifetime and ending')
        spec = importlib.util.spec_from_file_location('workshop_help_registry', NATIVE / 'scripts/workshop_help.py')
        workshop_help = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(workshop_help)
        chapter = {operation for operation, filename, _, _ in workshop_help.REGISTRY
                   if filename == 'LIFECYCLE-AND-TEARDOWN.md'}
        backlog = json.loads((REPO / 'RC4-BACKLOG.json').read_text())
        item = next(entry for entry in backlog['items'] if entry['id'] == 'RC4-022')
        accepted = one(r'states; ([a-z/]+);', item['acceptance'], 'RC4-022 operations').split('/')
        self.assertTrue(set(accepted) <= chapter, 'RC4-022 lifecycle operations must be documented commands')
        self.assertTrue(operations <= chapter)

    def test_quench_applicability_rule_matches_the_documented_algorithms(self):
        V = self.V
        endings = flat((NATIVE / 'docs/WEATHER-ENDINGS.md').read_text())
        style, algorithms = one(r'`(\w+)` is supported for [^(]*\(([\d, ]+)\)', endings, 'WEATHER-ENDINGS')
        self.assertEqual(style, V.restricted_style)
        self.assertEqual([int(a) for a in algorithms.split(',')], V.restricted_algorithms)
        with NativeScene(SEED) as scene:
            catalogue = {row['id'] for row in scene.catalogue() if row['contract'] == 'ParticleEmitter'}
        self.assertEqual({name for name, *_ in V.particle_effects}, catalogue)
        algorithm = {name: a for name, _, a, _ in V.particle_effects}[MATRIX_EFFECT]
        self.assertTrue(all(V.supports(algorithm, style) for style in V.stop_styles),
                        'The matrix effect must accept every derived ending')


class EffectEndingApplicability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.V = Vocabulary()

    def test_every_particle_effect_by_every_ending_for_authoring_stop_and_cancel(self):
        V = self.V
        unsupported = V.unsupported_error[0]
        for name, _, algorithm, _ in V.particle_effects:
            with self.subTest(effect=name):
                with NativeScene(SEED) as scene:
                    base = scene.snapshot()
                    accepted = []
                    for index, style in enumerate(V.emitter_styles):
                        flat_command = {'op': 'emitter', 'id': index + 1, 'effect': name, 'count': 0,
                                        'runningTimeMs': 0, 'endStyle': style}
                        nested = {'op': 'weather-author', 'schema': 'nocturne.weather-authoring/v1',
                                  'id': index + 9, 'effect': name, 'emission': {'count': 0, 'runningTimeMs': 0},
                                  'lifecycle': {'endStyle': style}}
                        for command in (flat_command, nested):
                            if V.supports(algorithm, style):
                                accepted.append(command)
                                continue
                            with self.assertRaises(ValueError) as caught:
                                scene.command(command)
                            self.assertEqual(str(caught.exception), unsupported, command)
                            self.assertTrue(scene.snapshot() == base, 'Rejected authoring mutated source')
                    scene.batch(accepted)
                with NativeScene(SEED) as scene:
                    scene.batch([{'op': 'emitter', 'id': ident, 'effect': name, 'count': 0, 'runningTimeMs': 0}
                                 for ident in range(1, 13)])
                    base = scene.snapshot()
                    accepted = []
                    for index, style in enumerate(V.stop_styles):
                        for operation, ident in (('stop', index + 1), ('cancel', index + 7)):
                            command = {'op': operation, 'id': ident, 'style': style, 'tailMs': 250}
                            if operation == 'cancel' and style == V.cancel_excluded:
                                expected = V.cancel_error
                            elif not V.supports(algorithm, style):
                                expected = unsupported
                            else:
                                accepted.append(command)
                                continue
                            with self.assertRaises(ValueError) as caught:
                                scene.command(command)
                            self.assertEqual(str(caught.exception), expected, command)
                            self.assertTrue(scene.snapshot() == base, 'Rejected ending mutated source')
                    scene.batch(accepted)
                    self.assertEqual({row['phase'] for row in scene.info()['emitters']}, {'terminal'})

    def test_malformed_lifecycle_commands_reject_with_their_diagnostic_and_preserve_state(self):
        V = self.V
        with NativeScene(SEED) as scene:
            scene.batch([*PRELUDE, emitter(MATRIX_EFFECT), emitter(MATRIX_EFFECT, id=2)])
            scene.advance_to(ENTRY_US)
            base = scene.snapshot()
            invalid_style = ['unsupported', '', 'DRAIN', ' drain', V.stop_styles[-1] + 's', 4, None, True, ['drain']]
            invalid_tail = [-1, 3600001, 0.0001, '500', None, True, [500]]
            invalid_id = [0, 65536, -1, 1.5, '1', None]
            cases = []
            for operation in ('stop', 'cancel'):
                cases += [({'op': operation, 'id': 1, 'style': value}, 'Invalid choice: style') for value in invalid_style]
                cases += [({'op': operation, 'id': 1, 'tailMs': value}, 'Invalid duration: tailMs') for value in invalid_tail]
                cases += [({'op': operation, 'id': value}, 'Invalid integer parameter: id') for value in invalid_id]
                cases += [({'op': operation, 'id': 3}, V.missing_error[0]),
                          ({'op': operation, 'id': 1, 'force': 1}, 'Unknown or unsupported parameter')]
            cases += [({'op': 'resume', 'id': 3}, V.missing_error[0]), ({'op': 'resume', 'id': 0}, 'Invalid integer parameter: id'),
                      ({'op': 'resume', 'id': 1, 'style': 'drain'}, 'Unknown or unsupported parameter'),
                      ({'op': 'cancel', 'id': 1, 'style': V.cancel_excluded}, V.cancel_error),
                      ({**emitter(MATRIX_EFFECT, id=4), 'endStyle': 'unsupported'}, 'Invalid choice: endStyle'),
                      ({**emitter(MATRIX_EFFECT, id=4), 'tailMs': 3600001}, 'Invalid duration: tailMs'),
                      ({'op': 'batch', 'commands': [{'op': 'cancel', 'id': 1, 'style': V.cancel_styles[0]},
                                                    {'op': 'stop', 'id': 2, 'style': 'unsupported'}]}, None)]
            self.assertEqual(len(V.missing_error), 1)
            for command, expected in cases:
                with self.subTest(command=command):
                    with self.assertRaises(ValueError) as caught:
                        scene.command(command)
                    if expected is not None:
                        self.assertEqual(str(caught.exception), expected)
                    self.assertTrue(scene.snapshot() == base, 'Rejected lifecycle command mutated source')
            for tail in (0, 3600000):
                scene.command({'op': 'stop', 'id': 2, 'style': V.cancel_styles[0], 'tailMs': tail})

    def test_restored_lifecycle_fields_outside_native_tables_reject_atomically(self):
        V = self.V
        drain = V.cancel_excluded

        def snapshot(*steps):
            with NativeScene(SEED) as scene:
                for step in steps:
                    scene.advance_to(step) if isinstance(step, int) else scene.command(step)
                return scene.snapshot()

        def word(a, b, size):
            self.assertEqual(len(a), len(b))
            chunk, changed = 1 << 16, []
            for begin in range(24, len(a), chunk):
                if a[begin:begin + chunk] != b[begin:begin + chunk]:
                    changed += [i for i in range(begin, min(begin + chunk, len(a))) if a[i] != b[i]]
            self.assertTrue(changed, 'differential snapshot found no field')
            offset = changed[0] - (changed[0] - 24) % size
            self.assertTrue(all(offset <= i < offset + size for i in changed), 'field spans more than one word')
            return offset

        def patch(data, offset, size, value):
            out = bytearray(data)
            out[offset:offset + size] = (value % (1 << (8 * size))).to_bytes(size, 'little')
            out[20:24] = zlib.crc32(bytes(out[24:])).to_bytes(4, 'little')
            return bytes(out)

        base = {'op': 'emitter', 'id': 1, 'effect': 'weather/autumn-drift', 'count': 0, 'runningTimeMs': 0,
                'collision': False, 'deposit': False, 'tailMs': 500}
        first, second = V.cancel_styles[:2]
        styles = {style: snapshot({**base, 'endStyle': style}) for style in (first, second)}
        style_at = word(styles[first], styles[second], 4)
        tail_at = word(snapshot(base), snapshot({**base, 'tailMs': 600}), 8)
        stopping_at = word(snapshot(base), snapshot(base, {'op': 'stop', 'id': 1, 'style': drain}), 4)
        stopped_late = snapshot(base, 200000, {'op': 'stop', 'id': 1, 'style': drain})
        stopped_early = snapshot(base, 100000, {'op': 'stop', 'id': 1, 'style': drain}, 200000)
        stop_at = word(stopped_early, stopped_late, 8)
        quench = V.stop_styles.index(V.restricted_style)
        with NativeScene(SEED) as scene:
            scene.command(emitter(MATRIX_EFFECT, id=7))
            scene.advance_to(ENTRY_US)
            owned = scene.snapshot()
            hostile = [patch(styles[first], style_at, 4, len(V.stop_styles)),
                       patch(styles[first], style_at, 4, -1),
                       patch(styles[first], style_at, 4, quench),
                       patch(snapshot(base, {'op': 'stop', 'id': 1, 'style': drain}), stopping_at, 4, 2),
                       patch(stopped_late, stop_at, 8, 200001),
                       patch(styles[first], tail_at, 8, 3600000001)]
            for index, data in enumerate(hostile):
                with self.subTest(hostile=index):
                    with self.assertRaises(ValueError):
                        scene.restore(data)
                    self.assertTrue(scene.snapshot() == owned, 'Rejected restore mutated the owned scene')
            scene.restore(patch(styles[first], style_at, 4, V.stop_styles.index(second)))
            self.assertTrue(scene.snapshot() == styles[second], 'A valid patched index must equal the authored one')
            scene.restore(patch(styles[first], tail_at, 8, 3600000000))
            scene.restore(patch(stopped_late, stop_at, 8, 150000))


_DIRECT = {}


def digest(snapshot):
    """nrSave's own header: magic, ABI, schema, payload length and payload CRC32."""
    return snapshot[:24]


class LifecycleEndMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.V = Vocabulary()

    def test_phase_by_entry_by_style_direct_snapshot_restore_and_replay(self):
        V = self.V
        self.assertEqual((FINAL_US - ENTRY_US) * 120 % 1000000, 0, 'resume shift must be whole simulation steps')
        observed = set()
        separation = {}
        for cell in matrix_cells(V):
            with self.subTest(cell=cell):
                events, spec = cell_timeline(V, cell)
                model = CellModel(self, cell, spec)
                direct = run_timeline(self, events, model=model)
                observed |= direct.phases
                totals = separation.setdefault((cell[0], spec['destructive']), [0, 0, 0])
                totals[0] += model.natural_deaths
                totals[1] += model.deadline_cuts
                totals[2] += model.drain_survivors
                restored = run_timeline(self, events, restore=direct.checkpoint, start=direct.checkpoint_index + 1)
                self.assertEqual(restored.records, [r for r in direct.records if r[0] > direct.checkpoint_index],
                                 'Mid-life snapshot restore diverged')
                self.assertTrue(restored.final == direct.final, 'Mid-life snapshot restore final source diverged')
                replay = run_timeline(self, events, partition=True)
                self.assertEqual(replay.records, direct.records, 'Command-journal replay diverged')
                self.assertTrue(replay.final == direct.final, 'Command-journal replay final source diverged')
                _DIRECT[cell] = (direct.records, digest(direct.final))
        self.assertEqual(observed, set(V.phases), 'The matrix must observe exactly the native phase vocabulary')
        for phase in LIVE_PHASES:
            deaths, cuts, _ = separation.get((phase, True), (0, 0, 0))
            self.assertGreater(deaths, 0, phase + ': no lifetime ended before a tail deadline')
            self.assertGreater(cuts, 0, phase + ': no tail deadline ended a longer lifetime')
            self.assertGreater(separation.get((phase, False), (0, 0, 0))[2], 0,
                               phase + ': drain must outlive the tail deadline')
        # EMITTER-CANCEL: supported styles keep the force, opacity, heat and expiry of stop.
        for phase in V.phases:
            for style in V.cancel_styles:
                with self.subTest(phase=phase, style=style, equivalence='cancel==stop'):
                    stop, cancel = _DIRECT.get((phase, 'stop', style)), _DIRECT.get((phase, 'cancel', style))
                    self.assertIsNotNone(stop)
                    self.assertIsNotNone(cancel)
                    self.assertEqual([r[1:] for r in cancel[0]], [r[1:] for r in stop[0]])
                    self.assertEqual(cancel[1], stop[1])

    def test_two_fresh_contexts_with_the_same_seed_reproduce_every_cell(self):
        for cell in matrix_cells(self.V):
            with self.subTest(cell=cell):
                events, _ = cell_timeline(self.V, cell)
                first = _DIRECT.get(cell)
                if first is None:
                    run = run_timeline(self, events)
                    first = (run.records, digest(run.final))
                second = run_timeline(self, events)
                self.assertEqual(second.records, first[0])
                self.assertEqual(digest(second.final), first[1])


class EndingTerminalBehaviour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.V = Vocabulary()

    def scene(self, *commands):
        scene = NativeScene(SEED)
        scene.batch([*PRELUDE, *commands])
        return scene

    def test_dissolve_opacity_tail_matches_scaled_alpha_references_for_every_algorithm(self):
        """EMITTER-CANCEL/WEATHER-ENDINGS: dissolve multiplies opacity by the remaining tail."""
        V = self.V
        dissolve, drain = 'dissolve', V.cancel_excluded
        self.assertIn(dissolve, V.cancel_styles)
        life = {'count': 6, 'runningTimeMs': 100, 'lifetimeMinMs': 3000, 'lifetimeMaxMs': 3000,
                'radius': 2, 'position': [0, 3, 0]}
        for algorithm, effect in V.representatives():
            for entry in ('stop', 'cancel', 'natural', 'drain-cancel'):
                with self.subTest(effect=effect, entry=entry):
                    def build(alpha, ending):
                        patch = dict(life, alpha=alpha)
                        if entry == 'natural':
                            patch['endStyle'] = ending
                        return self.scene(emitter(effect, **patch))
                    actual, half, quarter, full = build(1, dissolve), build(.5, drain), build(.25, drain), build(1, drain)
                    empty = self.scene()
                    origin = 100000 if entry == 'natural' else ENTRY_US
                    with actual, half, quarter, full, empty:
                        if entry != 'natural':
                            for scene in (actual, half, quarter, full, empty):
                                scene.advance_to(ENTRY_US)
                            first = {'op': 'cancel' if entry == 'cancel' else 'stop', 'id': 1,
                                     'style': drain if entry == 'drain-cancel' else dissolve, 'tailMs': TAIL_US // 1000}
                            actual.command(first)
                            for scene in (half, quarter, full):
                                scene.command({'op': 'stop', 'id': 1, 'style': drain})
                            if entry == 'drain-cancel':
                                origin = SECOND_US
                                for scene in (actual, half, quarter, full, empty):
                                    scene.advance_to(SECOND_US)
                                actual.command({'op': 'cancel', 'id': 1, 'style': dissolve, 'tailMs': TAIL_US // 1000})

                        def frames(us):
                            for scene in (actual, half, quarter, full, empty):
                                scene.advance_to(us)
                            return [scene.render().bytes for scene in (actual, half, quarter, full, empty)]
                        a, h, q, f, e = frames(origin)
                        self.assertEqual(a, f, 'The ending transaction changed presentation immediately')
                        a, h, q, f, e = frames(origin + TAIL_US // 2)
                        self.assertNotEqual(h, e, 'Reference particles must be visible')
                        self.assertNotEqual(a, f, 'Half-way through the tail opacity must be reduced')
                        self.assertEqual(a, h, 'Half-way opacity must equal the half-alpha reference')
                        a, h, q, f, e = frames(origin + 3 * TAIL_US // 4)
                        self.assertEqual(a, q, 'Three-quarter opacity must equal the quarter-alpha reference')
                        a, h, q, f, e = frames(boundary_us(first_step_at_or_after(origin + TAIL_US)))
                        self.assertEqual(actual.particles(), [])
                        self.assertEqual(a, e, 'Expired dissolve particles must not be drawn')

    def test_endings_hand_off_deposits_and_aggregates_and_never_erase_them(self):
        """EMITTER-CANCEL: deposits keep their own clocks; cancel does not erase them."""
        V = self.V
        receiver = {'op': 'floor', 'enabled': True, 'height': 0, 'reentrainWindSpeed': 6, 'maxIndividual': 2,
                    'maxTiles': 4, 'overflow': 'merge-to-field', 'cellSize': 100}
        source = emitter(MATRIX_EFFECT, position=[0, .5, 0], spread=[2, 0, 2], runningTimeMs=0, collision=True,
                         deposit=True, lifetimeMinMs=5000, lifetimeMaxMs=5000)
        tail, entry_us = 1500, 100000
        deadline = boundary_us(first_step_at_or_after(entry_us + tail * 1000))
        handed_off = 0
        for operation, styles in (('stop', V.stop_styles), ('cancel', V.cancel_styles)):
            for style in styles:
                with self.subTest(operation=operation, style=style), self.scene(receiver, source) as scene:
                    scene.advance_to(entry_us)
                    scene.command({'op': operation, 'id': 1, 'style': style, 'tailMs': tail})
                    scene.advance_to(boundary_us(first_step_at_or_after(deadline) - 1))
                    before = observe(scene)
                    scene.advance_to(deadline)
                    at = observe(scene)
                    if style == V.cancel_excluded:
                        self.assertEqual({r[0] for r in at['particles']}, {r[0] for r in before['particles']},
                                         'Drain must not apply the tail deadline')
                        continue
                    self.assertEqual(at['particles'], (), 'A destructive ending outlived its tail deadline')
                    self.assertEqual(at['counts'][1:3], before['counts'][1:3], 'The deadline erased deposits')
                    self.assertEqual(at['deposits'], before['deposits'])
                    handed_off += sum(at['counts'][1:3])
                    scene.command({'op': 'forces', 'id': 1, 'wind': WIND})
                    for us in (deadline + 250000, deadline + 600000):
                        scene.advance_to(us)
                        later = observe(scene)
                        self.assertEqual(later['deposits'], at['deposits'],
                                         'Wind re-entrainment erased deposits of a destructive ending')
                        self.assertEqual(later['counts'][1:3], at['counts'][1:3])
                        self.assertEqual(later['particles'], ())
                        expected = 'settled' if any(at['counts'][1:3]) else 'terminal'
                        self.assertEqual(later['emitter'][0], expected)
        self.assertGreater(handed_off, 0, 'No ending handed matter to the receivers')

    def test_endings_leave_retention_and_aggregate_fade_on_receiver_clocks(self):
        """AGGREGATE-FADE: retention and fade belong to the receiver, not to the ending."""
        V = self.V
        receiver = {'op': 'floor', 'enabled': True, 'height': 0, 'reentrainWindSpeed': 0, 'maxIndividual': 2,
                    'maxTiles': 4, 'overflow': 'merge-to-field', 'cellSize': 100, 'retentionMs': 1200, 'fadeMs': 400}
        source = emitter(MATRIX_EFFECT, **PHASE_SETUPS['settled'])
        samples = list(range(ENTRY_US, 1450001, 50000))
        with self.scene(receiver, source) as reference:
            timeline = []
            for us in samples:
                reference.advance_to(us)
                timeline.append((observe(reference)['counts'], reference.render().bytes))
        self.assertEqual(timeline[0][0][1:3], (2, 4), 'Setup must hand matter to individual and aggregate receivers')
        self.assertEqual(timeline[-1][0][1:3], (0, 0), 'Receiver retention must expire the matter')
        self.assertGreater(len({frame for _, frame in timeline}), 2, 'Aggregate fade must change presentation')
        for operation, styles in (('stop', V.stop_styles), ('cancel', V.cancel_styles)):
            for style in styles:
                with self.subTest(operation=operation, style=style), self.scene(receiver, source) as scene:
                    for index, us in enumerate(samples):
                        scene.advance_to(us)
                        if us == ENTRY_US:
                            scene.command({'op': operation, 'id': 1, 'style': style, 'tailMs': TAIL_US // 1000})
                        counts, frame = timeline[index]
                        self.assertEqual(observe(scene)['counts'], counts, us)
                        self.assertEqual(scene.render().bytes, frame, us)

    def test_aggregate_release_from_a_drain_stopped_source_lives(self):
        """AGGREGATE-REENTRAINMENT: a stopped original emitter can release aggregate matter."""
        receiver = {'op': 'floor', 'enabled': True, 'height': 0, 'reentrainWindSpeed': 0, 'maxIndividual': 2,
                    'maxTiles': 4, 'overflow': 'merge-to-field', 'cellSize': 100}
        with self.scene(receiver, emitter(MATRIX_EFFECT, **PHASE_SETUPS['settled'])) as scene:
            scene.advance_to(ENTRY_US)
            scene.command({'op': 'stop', 'id': 1, 'style': self.V.cancel_excluded})
            tile = scene.info()['aggregateMaterials'][0]
            aggregated = observe(scene)['counts'][2]
            self.assertGreaterEqual(tile['count'], 2)
            scene.command({'op': 'aggregate-reemit', 'tileIndex': tile['tileIndex'], 'count': 2, 'velocity': [0, 2, 0]})
            scene.advance_to(ENTRY_US + TAIL_US)
            observed = observe(scene)
            self.assertEqual(observed['counts'][0], 2)
            self.assertEqual(observed['counts'][2], aggregated - 2)
            self.assertEqual(observed['emitter'][0], 'draining')

    def test_destructive_endings_cannot_return_to_drain_or_resume(self):
        """EMITTER-CANCEL: endings finish by the deadline; only reauthoring restarts emission."""
        V = self.V
        drain = V.cancel_excluded
        algorithm = {name: a for name, _, a, _ in V.particle_effects}[MATRIX_EFFECT]
        for entry in ('stop', 'cancel', 'natural'):
            for style in V.cancel_styles:
                with self.subTest(entry=entry, style=style):
                    authored = emitter(MATRIX_EFFECT, rate=8, runningTimeMs=600 if entry == 'natural' else 0,
                                       lifetimeMinMs=5000, lifetimeMaxMs=5000, **({'endStyle': style} if entry == 'natural' else {}))
                    authored.pop('count')
                    with self.scene(authored) as scene:
                        origin = 600000 if entry == 'natural' else ENTRY_US
                        scene.advance_to(origin)
                        if entry != 'natural':
                            scene.command({'op': entry, 'id': 1, 'style': style, 'tailMs': TAIL_US // 1000})
                        live = scene.particles()
                        self.assertTrue(live)
                        scene.advance_to(origin + TAIL_US // 2)
                        held = scene.snapshot()
                        for command, expected in (({'op': 'stop', 'id': 1, 'style': drain}, DESTRUCTIVE_TO_DRAIN),
                                                  ({'op': 'resume', 'id': 1}, V.resume_error)):
                            with self.assertRaises(ValueError) as caught:
                                scene.command(command)
                            self.assertEqual(str(caught.exception), expected)
                            self.assertTrue(scene.snapshot() == held)
                        other = next(s for s in V.cancel_styles if s != style and V.supports(algorithm, s))
                        scene.command({'op': 'stop', 'id': 1, 'style': other, 'tailMs': TAIL_US // 1000 * 2})
                        scene.advance_to(boundary_us(first_step_at_or_after(origin + 2 * TAIL_US) - 1))
                        self.assertTrue(scene.particles(), 'A changed destructive tail must keep the first origin')
                        scene.advance_to(boundary_us(first_step_at_or_after(origin + 2 * TAIL_US)))
                        self.assertEqual(scene.particles(), [])
                        births = scene.info()['emitters'][0]['attemptedBirths']
                        scene.advance_to(origin + 3 * TAIL_US)
                        self.assertEqual(scene.info()['emitters'][0]['attemptedBirths'], births)
                        scene.command({'op': 'clear-instance', 'id': 1})
                        scene.command({**authored, 'endStyle': drain, 'startTimeUs': origin + 3 * TAIL_US})
                        scene.advance_to(origin + 4 * TAIL_US)
                        self.assertTrue(scene.particles(), 'Reauthoring must remain the explicit restart')
        doc = flat((NATIVE / 'docs/EMITTER-CANCEL.md').read_text())
        self.assertIn(DESTRUCTIVE_TO_DRAIN, doc, 'EMITTER-CANCEL must document the destructive-to-drain diagnostic')

    def test_cancel_defaults_to_the_current_ending_and_retained_tail(self):
        """EMITTER-CANCEL: omitted style uses the non-drain style or dissolve; omitted tail is kept."""
        V = self.V
        for style in V.emitter_styles:
            with self.subTest(style=style):
                authored = emitter(MATRIX_EFFECT, endStyle=style, tailMs=700, runningTimeMs=2000)
                with self.scene(authored) as cancelled, self.scene(authored) as stopped:
                    for scene in (cancelled, stopped):
                        scene.advance_to(ENTRY_US)
                    cancelled.command({'op': 'cancel', 'id': 1})
                    stopped.command({'op': 'stop', 'id': 1, 'style': V.cancel_default if style == V.cancel_excluded else style})
                    self.assertTrue(cancelled.snapshot() == stopped.snapshot())

    def test_pause_clear_and_reset_keep_their_documented_ownership_during_endings(self):
        V = self.V
        style = V.cancel_styles[0]
        cancel = {'op': 'cancel', 'id': 1, 'style': style, 'tailMs': TAIL_US // 1000}
        dead = first_step_at_or_after(ENTRY_US + TAIL_US)
        with self.scene(emitter(MATRIX_EFFECT, lifetimeMinMs=5000, lifetimeMaxMs=5000)) as scene:
            scene.advance_to(ENTRY_US)
            scene.command(cancel)
            scene.advance_to(SECOND_US)
            scene.command({'op': 'pause', 'paused': True})
            held = scene.snapshot()
            scene.advance_to(FINAL_US)
            self.assertTrue(scene.snapshot() == held, 'A paused time command advanced the tail')
            scene.command(cancel)
            self.assertTrue(scene.snapshot() == held, 'Repeated cancel while paused restarted the tail')
            scene.command({'op': 'pause', 'paused': False})
            scene.advance_to(boundary_us(dead - 1))
            self.assertTrue(scene.particles(), 'Pause wall time must not consume the tail')
            scene.advance_to(boundary_us(dead))
            self.assertEqual(scene.particles(), [])
        settled = emitter(MATRIX_EFFECT, **PHASE_SETUPS['settled'])
        with self.scene(settled) as scene:
            scene.advance_to(ENTRY_US)
            deposits = observe(scene)['deposits']
            scene.command(cancel)
            scene.command({'op': 'clear-instance', 'id': 1})
            self.assertEqual(scene.info()['emitters'], [])
            self.assertEqual(observe(scene)['deposits'], deposits, 'clear-instance must keep scene deposits')
            scene.advance_to(FINAL_US)
            self.assertEqual(observe(scene)['deposits'], deposits)
            scene.command({'op': 'reset', 'seed': SEED})
            self.assertEqual((scene.info()['emitters'], observe(scene)['deposits']), ([], ()))
        with self.scene(settled, emitter(MATRIX_EFFECT, id=2, lifetimeMinMs=5000, lifetimeMaxMs=5000)) as scene:
            scene.advance_to(ENTRY_US)
            scene.command({**cancel, 'id': 2})
            scene.command({'op': 'clear', 'scope': 'deposits'})
            self.assertEqual(observe(scene)['deposits'], ())
            live = scene.particles()
            self.assertTrue(live, 'clear deposits must keep live particles and their ending')
            scene.advance_to(boundary_us(dead))
            self.assertEqual(scene.particles(), [])
            self.assertEqual([row['phase'] for row in scene.info()['emitters']], ['terminal', 'terminal'])
        with self.scene(settled) as scene:
            scene.advance_to(ENTRY_US)
            deposits = observe(scene)['deposits']
            scene.command({'op': 'stop', 'id': 1, 'style': V.cancel_excluded})
            scene.command({'op': 'clear', 'scope': 'weather'})
            self.assertEqual(scene.info()['emitters'], [])
            self.assertEqual(observe(scene)['deposits'], deposits, 'clear weather must keep deposits')

    def test_batched_and_scheduled_endings_execute_in_the_core(self):
        """EMITTER-RESUME: the shared C core executes lifecycle commands in batches and schedules."""
        V = self.V
        style = V.cancel_styles[0]
        cancel = {'op': 'cancel', 'id': 1, 'style': style, 'tailMs': TAIL_US // 1000}
        authored = emitter(MATRIX_EFFECT, **PHASE_SETUPS['draining'])
        with self.scene(authored) as direct, self.scene(authored) as batched:
            for scene in (direct, batched):
                scene.advance_to(ENTRY_US)
            direct.command(cancel)
            batched.batch([cancel])
            self.assertTrue(direct.snapshot() == batched.snapshot(), 'A batched ending differs from direct')
        with self.scene(emitter(MATRIX_EFFECT, lifetimeMinMs=5000, lifetimeMaxMs=5000)) as scene:
            at = ENTRY_US + 1
            scene.schedule(1, at, cancel)
            executed = first_step_at_or_after(at)
            scene.advance_to(boundary_us(executed - 1))
            births = scene.info()['emitters'][0]['attemptedBirths']
            self.assertEqual(len(scene.info()['pending']), 1)
            scene.advance_to(boundary_us(executed))
            self.assertEqual(scene.info()['pending'], [])
            dead = first_step_at_or_after(boundary_us(executed) + TAIL_US)
            scene.advance_to(boundary_us(dead - 1))
            self.assertTrue(scene.particles(), 'The scheduled ending clock starts at its executed boundary')
            scene.advance_to(boundary_us(dead))
            self.assertEqual(scene.particles(), [])
            self.assertEqual(scene.info()['emitters'][0]['attemptedBirths'], births)


if __name__ == '__main__':
    unittest.main()
