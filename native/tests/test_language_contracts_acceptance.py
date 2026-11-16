"""RC4-028 acceptance matrix: registered selectors, appearance bindings, guards,
value maps and the historical character-selector path grammar.

Each test enforces one documented rule and quotes the sentence it derives from.
Expectations come from native/docs/SELECTORS.md, CONDITIONS.md,
CHARACTER-SELECTORS.md, DATA-EXPRESSIONS.md, VALUE-BINDINGS.md and
docs/rc4-contracts7/TDD.md, never from current output. Everything runs against
the real C core through the Python C-ABI binding: no mocks, no renderer shims.
Hostile restored indices need State byte offsets and are enforced by the
companion C program native/tests/language_contracts_acceptance.c.

Run from the repository root:
    python3 -m unittest native.tests.test_language_contracts_acceptance -v
or from native/ through the qualification discovery (`unittest discover -s tests`).
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene  # noqa: E402

WIDGET_HIT = 0x30000000
NODE_HIT = 0x10000000
WINDOW_FAMILIES = (0x20, 0x50, 0x60, 0x61, 0x62, 0x64)
PROMPT_HIT = 0x40000000
FAMILY_PROPERTIES = {
    # SELECTORS.md "Family-specific properties" table.
    'widget': {'material', 'backgroundMaterial', 'alpha', 'sampling'},
    'window': {'material', 'alpha'},
    'emitter': {'material', 'alpha', 'sampling', 'surfaceAlpha', 'veinContrast'},
    'text': {'material'},
    'area': {'material', 'alpha'},
    'indicator': {'material'},
    'node': {'color'},
    'floor': {'alpha', 'sampling'},
    'mesh': {'alpha', 'sampling', 'color'},
    'prompt': {'alpha'},
}
SAMPLE_VALUE = {'material': 2, 'backgroundMaterial': 2, 'alpha': .5, 'sampling': 'cell',
                'surfaceAlpha': .5, 'veinContrast': .5, 'color': 0x123456}


def leaf(path='/heat', comparison='above', **bounds):
    return {'path': path, 'comparison': comparison, **(bounds or {'value': 50})}


class LanguageContractsAcceptance(unittest.TestCase):
    """One test per documented rule; see each docstring for the cited sentence."""

    def setUp(self):
        self.s = self.scene()

    def tearDown(self):
        self.s.close()

    # ----------------------------------------------------------------- helpers
    def scene(self, seed=2030):
        s = NativeScene(seed)
        s.command({'op': 'environment', 'stars': 0, 'style': 'solid'})
        for ident, x, text in [(1, 5, 'Select me'), (2, 38, 'Neighbour')]:
            s.command({'op': 'widget', 'id': ident, 'kind': 'button', 'x': x, 'y': 5, 'width': 25,
                       'height': 3, 'text': text, 'border': 'rounded', 'material': 1, 'alpha': .2})
        return s

    def cmd(self, op, scene=None, **fields):
        return (scene or self.s).command({'op': op, **fields})

    def register(self, ident=1, path='/lab/one', role='control', family='widget', target=None,
                 scene=None, **fields):
        return self.cmd('state-register', scene, id=ident, path=path, role=role,
                        target={'family': family, 'id': ident if target is None else target}, **fields)

    def rule(self, ident=1, selector=None, style=None, scene=None, **fields):
        return self.cmd('style-rule', scene, id=ident, selector=selector or {'family': 'widget'},
                        style=style or {'material': 2}, **fields)

    def entry(self, ident=1, scene=None):
        return next(x for x in (scene or self.s).info()['registeredStates'] if x['id'] == ident)

    def effective(self, key, ident=1, scene=None):
        return self.entry(ident, scene)['effective'][key]

    def guard(self, ident=1, scene=None):
        return next(r for r in (scene or self.s).info()['styleRules'] if r['id'] == ident)['guard']

    def rejects(self, command, scene=None):
        """Rejection is a ValueError diagnostic and leaves scene bytes identical."""
        scene = scene or self.s
        before = scene.snapshot()
        with self.assertRaises(ValueError, msg=command) as caught:
            scene.command(command)
        self.assertTrue(str(caught.exception), 'a rejection must carry a diagnostic')
        self.assertEqual(before, scene.snapshot(), command)
        return str(caught.exception)

    def assertMicro(self, actual, expected):
        """Metadata numbers are serialized at one-millionth resolution."""
        self.assertLessEqual(abs(actual - expected), 5.000001e-7, (actual, expected))

    def owned(self, frame, hit):
        return [w for w in frame.words() if w[3] == hit]

    def cell_for(self, frame, predicate):
        width = frame.width
        for index, word in enumerate(frame.words()):
            if predicate(word[3]):
                return index % width, index // width
        self.fail('no rendered cell satisfies the hit predicate')

    # ------------------------------------------------- registration grammar
    def test_registration_paths_are_canonical_absolute_ascii_at_most_127_bytes(self):
        """SELECTORS.md: "Paths are canonical absolute ASCII paths, at most 127 bytes, with the
        same segment validation as notification event paths: no empty, `.` or `..` segments.\""""
        for path in ['/a', '/app/actions/inspect', '/a.b/c-d_e', '/' + 'a' * 126]:
            self.register(5, path, target=1)
            self.assertEqual(self.entry(5)['path'], path)
            self.cmd('state-unregister', id=5)
        for path in ['', 'app', '/', '/app/', '//app', '/app//x', '/./x', '/x/.', '/x/../y', '/x/..',
                     '/' + 'a' * 127, '/café', '/a b', '/a\\b']:
            with self.subTest(path=path):
                self.rejects({'op': 'state-register', 'id': 5, 'path': path, 'role': 'control',
                              'target': {'family': 'widget', 'id': 1}})

    def test_roles_are_nonempty_ascii_word_characters_at_most_47_bytes(self):
        """SELECTORS.md: "Roles are nonempty ASCII letters/digits/underscore/hyphen, at most 47
        bytes.\""""
        for role in ['a', 'Review-control_9', 'r' * 47]:
            self.register(5, '/role/ok', role, target=1)
            self.assertEqual(self.entry(5)['role'], role)
            self.cmd('state-unregister', id=5)
        for role in ['', 'r' * 48, 'has space', 'dot.ted', 'slash/ed', 'été']:
            with self.subTest(role=role):
                self.rejects({'op': 'state-register', 'id': 5, 'path': '/role/bad', 'role': role,
                              'target': {'family': 'widget', 'id': 1}})
                self.rejects({'op': 'style-rule', 'id': 5, 'selector': {'family': 'widget', 'role': role},
                              'style': {'material': 2}})

    def test_registration_and_rule_ids_are_integers_1_to_65535(self):
        """SELECTORS.md: "Registration and rule IDs are integers 1..65535.\""""
        self.register(65535, '/ids/max', target=1)
        self.rule(65535)
        for ident in [0, 65536, -1, 1.5, True, '1', None]:
            with self.subTest(id=ident):
                self.rejects({'op': 'state-register', 'id': ident, 'path': '/ids/bad', 'role': 'r',
                              'target': {'family': 'widget', 'id': 2}})
                self.rejects({'op': 'style-rule', 'id': ident, 'selector': {'family': 'widget'},
                              'style': {'material': 2}})

    def test_singleton_targets_use_zero_and_others_use_their_public_identity(self):
        """SELECTORS.md: "Targets use their existing public identity; floor, mesh and prompt are
        scene singletons whose target ID must be zero.\""""
        for ident, family in [(10, 'floor'), (11, 'mesh'), (12, 'prompt')]:
            self.register(ident, '/singleton/' + family, family=family, target=0)
            self.assertTrue(self.entry(ident)['exists'])
            self.rejects({'op': 'state-register', 'id': 20, 'path': '/singleton/bad', 'role': 'r',
                          'target': {'family': family, 'id': 1}})
        self.rejects({'op': 'state-register', 'id': 20, 'path': '/widget/zero', 'role': 'r',
                      'target': {'family': 'widget', 'id': 0}})

    def test_one_unique_path_and_target_pair_and_the_target_must_exist(self):
        """SELECTORS.md: "Every registration has one unique path and one unique `(family,
        targetId)` pair. The target must exist on registration.\""""
        self.register(1, '/unique/one', target=1)
        self.rejects({'op': 'state-register', 'id': 2, 'path': '/unique/one', 'role': 'r',
                      'target': {'family': 'widget', 'id': 2}})
        self.rejects({'op': 'state-register', 'id': 2, 'path': '/unique/two', 'role': 'r',
                      'target': {'family': 'widget', 'id': 1}})
        self.rejects({'op': 'state-register', 'id': 2, 'path': '/unique/two', 'role': 'r',
                      'target': {'family': 'widget', 'id': 999}})
        self.rejects({'op': 'state-register', 'id': 2, 'path': '/unique/two', 'role': 'r',
                      'target': {'family': 'window', 'id': 1}})

    def test_capacities_are_64_registrations_and_32_rules(self):
        """SELECTORS.md: "At most 64 registrations and 32 rules exist in a scene." and "Unknown
        fields, duplicates, bad references and exhausted capacities reject the whole transaction.\""""
        ident = 1
        for family, count in [('text', 24), ('area', 16), ('indicator', 24)]:
            for target in range(1, count + 1):
                extra = {'text': 'x'} if family == 'text' else {'sequence': 'ab'} if family == 'indicator' else {}
                self.cmd(family, id=target, **extra)
                self.register(ident, '/capacity/%s/%d' % (family, target), family=family, target=target)
                ident += 1
        self.rejects({'op': 'state-register', 'id': 65, 'path': '/capacity/floor', 'role': 'r',
                      'target': {'family': 'floor', 'id': 0}})
        for rule in range(1, 33):
            self.rule(rule, {'family': 'text'}, {'material': 2})
        self.rejects({'op': 'style-rule', 'id': 33, 'selector': {'family': 'text'}, 'style': {'material': 2}})
        self.cmd('state-unregister', id=1)
        self.cmd('remove-style-rule', id=1)
        self.register(65, '/capacity/floor', family='floor', target=0)
        self.rule(33, {'family': 'floor'}, {'alpha': .5})

    def test_update_preserves_target_and_path_and_reregistration_revalidates(self):
        """SELECTORS.md: "Updating a registration preserves its target and path. Reissuing
        `state-register` for the same registry ID may replace those fields subject to the same
        validation.\""""
        self.register(21, '/app/actions/inspect', target=1)
        self.register(22, '/app/other', target=2)
        self.cmd('state-update', id=21, role='review-control', active=False)
        entry = self.entry(21)
        self.assertEqual((entry['path'], entry['family'], entry['targetId'], entry['role']),
                         ('/app/actions/inspect', 'widget', 1, 'review-control'))
        self.assertFalse(entry['states']['active'])
        for patch in [{'path': '/moved'}, {'target': {'family': 'widget', 'id': 2}}]:
            self.rejects({'op': 'state-update', 'id': 21, **patch})
        self.rejects({'op': 'state-update', 'id': 99, 'role': 'missing'})
        self.rejects({'op': 'state-register', 'id': 21, 'path': '/app/other', 'role': 'r',
                      'target': {'family': 'widget', 'id': 1}})
        self.cmd('state-unregister', id=22)
        self.register(21, '/app/moved', target=2)
        self.assertEqual((self.entry(21)['path'], self.entry(21)['targetId']), ('/app/moved', 2))
        self.register(23, '/app/actions/inspect', target=1)

    def test_unregistering_removes_only_the_registration(self):
        """SELECTORS.md: "Unregistering removes only the registration, not the component or its
        content.\""""
        self.register()
        before = self.owned(self.s.render(), WIDGET_HIT | 1)
        self.rule()
        self.assertNotEqual(before, self.owned(self.s.render(), WIDGET_HIT | 1))
        self.cmd('state-unregister', id=1)
        self.assertEqual(self.s.info()['registeredStates'], [])
        self.assertEqual([w['text'] for w in self.s.info()['widgets'] if w['id'] == 1], ['Select me'])
        self.assertEqual(before, self.owned(self.s.render(), WIDGET_HIT | 1))
        self.rejects({'op': 'state-unregister', 'id': 1})

    def test_removed_component_leaves_dormant_registration_reactivated_by_public_id(self):
        """SELECTORS.md: "Removing a component leaves a dormant registration. Recreating that
        public target ID reactivates the registration; this is explicitly **ID-based**\""""
        self.cmd('emitter', id=4, effect='weather/autumn-drift', count=2)
        self.register(9, '/scene/leaves', family='emitter', target=4)
        self.rule(1, {'family': 'emitter'}, {'alpha': .5})
        self.cmd('clear-instance', id=4)
        entry = self.entry(9)
        self.assertFalse(entry['exists'])
        self.assertEqual(entry['effective'], {})
        self.cmd('emitter', id=4, effect='weather/autumn-drift', count=2)
        self.assertTrue(self.entry(9)['exists'])
        self.assertEqual(self.effective('alpha', 9), .5)

    # --------------------------------------------------------- selector grammar
    def test_selector_id_is_the_target_identity_not_the_registry_id(self):
        """SELECTORS.md: "`selector.id`, when supplied, refers to the **target** ID, not the
        registry ID.\""""
        self.register(21, '/app/actions/inspect', target=1)
        self.rule(1, {'family': 'widget', 'id': 21}, {'material': 3})
        self.assertEqual(self.effective('material', 21), 1)
        self.rule(1, {'family': 'widget', 'id': 1}, {'material': 3})
        self.assertEqual(self.effective('material', 21), 3)

    def test_family_is_required_and_optional_filters_are_anded(self):
        """SELECTORS.md: "`family` is required. Optional `id`, `role`, `path` or `pathPrefix`, and
        state flags are ANDed.\""""
        self.register(1, '/and/one', 'control', target=1)
        self.register(2, '/and/two', 'control', target=2)
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'role': 'control'}, 'style': {'material': 2}})
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'Widget'}, 'style': {'material': 2}})
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget', 'unknown': 1},
                      'style': {'material': 2}})
        self.rule(1, {'family': 'widget', 'role': 'control', 'pathPrefix': '/and', 'id': 2,
                      'states': {'selected': False}}, {'material': 3})
        self.assertEqual((self.effective('material', 1), self.effective('material', 2)), (1, 3))
        self.cmd('widget', id=2, selected=True)
        self.assertEqual(self.effective('material', 2), 1)
        self.rule(1, {'family': 'window', 'pathPrefix': '/and'}, {'material': 3})
        self.assertEqual((self.effective('material', 1), self.effective('material', 2)), (1, 1))

    def test_exact_path_matches_exactly(self):
        """SELECTORS.md: "`path` matches exactly.\""""
        self.register(1, '/lab/a', target=1)
        self.register(2, '/lab/a/b', target=2)
        self.rule(1, {'family': 'widget', 'path': '/lab/a'}, {'alpha': .9})
        self.assertEqual((self.effective('alpha', 1), self.effective('alpha', 2)), (.9, .2))
        self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': 'widget', 'path': '/'},
                      'style': {'alpha': .9}})

    def test_path_prefix_matches_complete_segments_and_root_matches_all(self):
        """SELECTORS.md: "`pathPrefix` matches a complete path segment: `/app` matches `/app` and
        `/app/actions`, but not `/apple`. Prefix `/` matches all registered paths.\""""
        self.cmd('widget', id=3, kind='button', x=5, y=12, width=20, height=3, text='Third', material=1, alpha=.2)
        self.register(1, '/app', target=1)
        self.register(2, '/app/actions', target=2)
        self.register(3, '/apple', target=3)
        self.rule(1, {'family': 'widget', 'pathPrefix': '/app'}, {'material': 3})
        self.assertEqual([self.effective('material', i) for i in (1, 2, 3)], [3, 3, 1])
        self.rule(1, {'family': 'widget', 'pathPrefix': '/'}, {'material': 3})
        self.assertEqual([self.effective('material', i) for i in (1, 2, 3)], [3, 3, 3])
        for prefix in ['/app/', '//', 'app', '/app//actions', '/./app']:
            self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': 'widget', 'pathPrefix': prefix},
                          'style': {'material': 2}})

    def test_exact_path_and_prefix_cannot_coexist(self):
        """SELECTORS.md: "Exact path and pathPrefix cannot coexist in the same selector.\""""
        self.register(1, '/lab/a', target=1)
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget', 'path': '/lab/a',
                      'pathPrefix': '/lab'}, 'style': {'material': 2}})

    def test_unregistered_components_are_never_affected(self):
        """SELECTORS.md: "Unregistered components are never affected.\""""
        self.register(1, '/lab/one', target=1)
        neighbour = self.owned(self.s.render(), WIDGET_HIT | 2)
        self.rule(1, {'family': 'widget', 'pathPrefix': '/'}, {'material': 3, 'alpha': .9})
        self.rule(2, {'family': 'widget'}, {'backgroundMaterial': 2})
        self.assertEqual(neighbour, self.owned(self.s.render(), WIDGET_HIT | 2))

    def test_state_flags_are_booleans_and_false_requires_absence(self):
        """SELECTORS.md: "`states` accepts only boolean `active`, `selected`, `hover`, `pressed`,
        `disabled`. An omitted flag imposes no condition. A false flag explicitly requires
        absence.\""""
        self.register()
        for states in [{'focused': True}, {'hover': 'yes'}, {'hover': 1}, {'selected': None}]:
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget', 'states': states},
                          'style': {'material': 2}})
        self.rule(1, {'family': 'widget', 'states': {'hover': False}}, {'material': 3})
        self.rule(2, {'family': 'widget', 'states': {}}, {'alpha': .9})
        self.assertEqual((self.effective('material'), self.effective('alpha')), (3, .9))
        self.cmd('pointer', phase='move', x=8, y=6)
        self.assertTrue(self.entry()['states']['hover'])
        self.assertEqual((self.effective('material'), self.effective('alpha')), (1, .9))

    def test_active_state_sources_and_inactive_registration_suppression(self):
        """SELECTORS.md: "active | Widget active flag; running/nonstopping emitter; prompt active
        flag; otherwise existing target. Registration inactivity suppresses every rule for that
        target." and "A widget's own `active` flag defaults to false, so a widget registration
        reports `active` only after that widget sets it\""""
        self.register(1, '/active/widget', target=1)
        self.cmd('emitter', id=6, effect='weather/autumn-drift', count=4)
        self.register(6, '/active/emitter', family='emitter', target=6)
        self.cmd('area', id=7)
        self.register(7, '/active/area', family='area', target=7)
        self.register(8, '/active/prompt', family='prompt', target=0)
        widget_flag = next(w['active'] for w in self.s.info()['widgets'] if w['id'] == 1)
        self.assertIs(widget_flag, False)
        self.assertIs(self.entry(1)['states']['active'], False)
        self.assertTrue(all(self.entry(i)['states']['active'] for i in (6, 7, 8)))
        self.cmd('widget', id=1, active=True)
        self.assertTrue(self.entry(1)['states']['active'])
        self.cmd('widget', id=1, active=False)
        self.assertFalse(self.entry(1)['states']['active'])
        self.cmd('stop', id=6)
        self.assertFalse(self.entry(6)['states']['active'])
        self.rule(1, {'family': 'area', 'states': {'active': False}}, {'material': 3})
        self.rule(2, {'family': 'area'}, {'alpha': .9})
        self.assertEqual((self.effective('material', 7), self.effective('alpha', 7)),
                         (self.entry(7)['authored']['material'], .9))
        self.cmd('state-update', id=7, active=False)
        self.assertFalse(self.entry(7)['states']['active'])
        self.assertEqual(self.entry(7)['effective'], self.entry(7)['authored'],
                         'an inactive registration suppresses every rule, including active:false')

    def test_selected_state_sources_and_other_families_return_false(self):
        """SELECTORS.md: "selected | Actual widget selection, selected window, selected graph node,
        or active prompt. Other families return false.\""""
        self.register(1, '/selected/widget', target=1)
        self.cmd('window', id=3, title='Three', text='body', durationMs=0)
        self.cmd('window', id=4, title='Four', text='body', durationMs=0)
        self.register(3, '/selected/window3', family='window', target=3)
        self.register(4, '/selected/window4', family='window', target=4)
        self.cmd('node', id=5, label='Node')
        self.register(5, '/selected/node', family='node', target=5)
        self.register(6, '/selected/prompt', family='prompt', target=0)
        self.cmd('area', id=7)
        self.register(7, '/selected/area', family='area', target=7)
        self.register(8, '/selected/floor', family='floor', target=0)
        selected = lambda i: self.entry(i)['states']['selected']
        self.assertEqual([selected(i) for i in (1, 3, 4, 5, 7, 8)], [False, False, True, False, False, False])
        self.assertEqual(selected(6), self.entry(6)['states']['active'])
        self.cmd('widget', id=1, selected=True)
        self.cmd('window', id=3)
        self.cmd('select', id=5)
        self.assertEqual([selected(i) for i in (1, 3, 4, 5)], [True, True, False, True])

    def test_hover_is_the_latest_rendered_hit_owner_for_addressable_families(self):
        """SELECTORS.md: "hover | Latest pointer hit owner, using the same native rendered cells as
        interaction. Widgets, windows/chrome/docks, nodes and prompt are addressable.\""""
        self.register(1, '/hover/widget', target=1)
        self.cmd('node', id=3, label='Node')
        self.register(3, '/hover/node', family='node', target=3)
        self.cmd('window', id=4, title='Window', text='body text', durationMs=0)
        self.register(4, '/hover/window', family='window', target=4)
        self.register(5, '/hover/prompt', family='prompt', target=0)
        self.cmd('input', text='draft')
        frame = self.s.render()
        targets = {1: lambda hit: hit == WIDGET_HIT | 1, 3: lambda hit: hit == NODE_HIT | 3,
                   4: lambda hit: (hit >> 24) in WINDOW_FAMILIES and (hit & 0xffff) == 4,
                   5: lambda hit: (hit & 0xff000000) == PROMPT_HIT}
        for ident, predicate in targets.items():
            x, y = self.cell_for(frame, predicate)
            self.cmd('pointer', phase='move', x=x, y=y)
            hovered = [i for i in targets if self.entry(i)['states']['hover']]
            self.assertEqual(hovered, [ident], (x, y))
        chrome = self.cell_for(frame, lambda hit: (hit >> 24) in (0x50, 0x60, 0x61, 0x62) and (hit & 0xffff) == 4)
        self.cmd('pointer', phase='move', x=chrome[0], y=chrome[1])
        self.assertTrue(self.entry(4)['states']['hover'])
        self.cmd('pointer', phase='cancel', x=-1, y=-1)
        self.assertFalse(any(self.entry(i)['states']['hover'] for i in targets))

    def test_pressed_is_retained_until_up_or_cancel_independent_of_camera_capture(self):
        """SELECTORS.md: "pressed | Native pointer-down owner, retained until up/cancel,
        independent of camera capture.\""""
        self.register()
        self.rule(1, {'family': 'widget', 'states': {'pressed': True}}, {'material': 3})
        self.cmd('pointer', phase='down', x=8, y=6)
        self.cmd('pointer', phase='move', x=70, y=30)
        entry = self.entry()
        self.assertEqual((entry['states']['pressed'], entry['states']['hover'], entry['effective']['material']),
                         (True, False, 3))
        self.cmd('pointer', phase='up', x=70, y=30)
        self.assertFalse(self.entry()['states']['pressed'])
        self.cmd('pointer', phase='down', x=8, y=6)
        self.cmd('pointer', phase='cancel', x=-1, y=-1)
        self.assertFalse(self.entry()['states']['pressed'])
        self.cmd('pointer', phase='down', x=70, y=30)
        self.assertFalse(self.entry()['states']['pressed'], 'a camera drag owns no registered target')
        self.cmd('pointer', phase='up', x=70, y=30)

    def test_disabled_is_the_inverted_widget_enabled_flag_only(self):
        """SELECTORS.md: "disabled | The widget's enabled flag inverted. Other families return
        false.\""""
        self.register(1, '/disabled/widget', target=1)
        self.cmd('area', id=7)
        self.register(7, '/disabled/area', family='area', target=7)
        self.register(8, '/disabled/prompt', family='prompt', target=0)
        self.assertEqual([self.entry(i)['states']['disabled'] for i in (1, 7, 8)], [False, False, False])
        self.cmd('widget', id=1, enabled=False)
        self.assertTrue(self.entry(1)['states']['disabled'])
        self.cmd('widget', id=1, enabled=True)
        self.assertFalse(self.entry(1)['states']['disabled'])

    def test_passive_pointer_movement_is_an_input_transaction_not_a_render_side_effect(self):
        """SELECTORS.md: "Passive pointer movement is an input transaction, not a render side
        effect." TDD.md: "Passive mouse movement updates hover; up/cancel clears press.\""""
        self.register()
        self.rule(1, {'family': 'widget', 'states': {'hover': True}}, {'material': 3})
        camera = self.s.info()['camera']
        before = self.s.snapshot()
        for _ in range(3):
            self.s.render()
        self.assertEqual(before, self.s.snapshot())
        self.cmd('pointer', phase='move', x=8, y=6)
        self.assertNotEqual(before, self.s.snapshot())
        self.assertEqual((self.entry()['states']['hover'], self.effective('material')), (True, 3))
        self.assertEqual(camera, self.s.info()['camera'])

    # --------------------------------------------------- family applicability
    def test_every_supported_family_property_is_accepted(self):
        """SELECTORS.md "Family-specific properties" table (widget: material, backgroundMaterial,
        alpha, sampling; ... prompt: alpha)."""
        self.make_family_targets()
        expected = {'cell': 0}
        for family, properties in FAMILY_PROPERTIES.items():
            for prop in sorted(properties):
                with self.subTest(family=family, property=prop):
                    self.rule(1, {'family': family}, {prop: SAMPLE_VALUE[prop]})
                    value = self.entry(self.family_ids[family])['effective'][prop]
                    self.assertEqual(value, expected.get(SAMPLE_VALUE[prop], SAMPLE_VALUE[prop]))

    def test_every_inapplicable_family_property_rejects_instead_of_a_silent_no_op(self):
        """SELECTORS.md: "A rule requires at least one property. Inapplicable properties reject"
        and TDD.md: "Explicit family selection rejects inapplicable properties instead of accepting
        no-op settings.\""""
        self.make_family_targets()
        everything = set(SAMPLE_VALUE)
        for family, properties in FAMILY_PROPERTIES.items():
            for prop in sorted(everything - properties):
                with self.subTest(family=family, property=prop):
                    self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': family},
                                  'style': {prop: SAMPLE_VALUE[prop]}})
                    self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': family}, 'enabled': False,
                                  'style': {prop: SAMPLE_VALUE[prop]}})
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': family}, 'style': {}})
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': family}})

    def make_family_targets(self):
        self.cmd('window', id=3, title='W', text='body', durationMs=0)
        self.cmd('emitter', id=4, effect='weather/autumn-drift', count=2)
        self.cmd('text', id=5, text='Retained', effect='text/instant-ink')
        self.cmd('area', id=6)
        self.cmd('indicator', id=7, sequence='abcd')
        self.cmd('node', id=8, label='Node')
        self.cmd('mesh', triangles=[{'a': [-1, 1, 0], 'b': [1, 1, 0], 'c': [0, 2, 0]}])
        self.family_ids = {'widget': 1, 'window': 3, 'emitter': 4, 'text': 5, 'area': 6, 'indicator': 7,
                           'node': 8, 'floor': 10, 'mesh': 11, 'prompt': 12}
        for family, ident in self.family_ids.items():
            self.register(ident, '/family/' + family, family=family,
                          target=0 if family in ('floor', 'mesh', 'prompt') else (1 if family == 'widget' else ident))

    def test_leaf_only_properties_reject_on_a_matching_non_leaf_emitter(self):
        """SELECTORS.md: "emitter | material, alpha, sampling; leaf-only surfaceAlpha and
        veinContrast" and "Inapplicable properties reject, including leaf-only fields on a matching
        non-leaf emitter.\""""
        self.cmd('emitter', id=1, effect='weather/silver-squall', count=1)
        self.cmd('emitter', id=2, effect='weather/autumn-drift', count=1)
        self.register(1, '/weather/rain', 'rain', family='emitter', target=1)
        self.register(2, '/weather/leaves', 'leaf', family='emitter', target=2)
        for prop in ['surfaceAlpha', 'veinContrast']:
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'emitter'}, 'style': {prop: .5}})
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'emitter', 'id': 1},
                          'style': {prop: .5}})
            self.rule(1, {'family': 'emitter', 'role': 'leaf'}, {prop: .5})
            self.assertEqual(self.effective(prop, 2), .5)
        self.rule(2, {'family': 'emitter'}, {'material': 3, 'alpha': .5, 'sampling': 'half'})

    def test_applicability_is_checked_for_disabled_rules_false_guards_and_future_registrations(self):
        """SELECTORS.md: "Applicability is checked even for a disabled rule or currently false
        guard, so enabling a rule cannot reveal a silent no-op. Future registrations are subject to
        the same check.\""""
        self.cmd('define', path='/heat', value=0)
        self.cmd('emitter', id=1, effect='weather/silver-squall', count=1)
        self.register(1, '/weather/rain', 'leaf', family='emitter', target=1)
        selector = {'family': 'emitter', 'role': 'leaf'}
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': selector, 'enabled': False,
                      'style': {'veinContrast': 1}})
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': selector, 'when': leaf(value=50),
                      'style': {'veinContrast': 1}})
        self.cmd('state-unregister', id=1)
        self.rule(1, selector, {'veinContrast': 1}, enabled=False)
        self.rule(2, selector, {'surfaceAlpha': .5}, when=leaf(value=50))
        self.rejects({'op': 'state-register', 'id': 1, 'path': '/weather/rain', 'role': 'leaf',
                      'target': {'family': 'emitter', 'id': 1}})
        self.cmd('emitter', id=2, effect='weather/autumn-drift', count=1)
        self.register(2, '/weather/leaves', 'leaf', family='emitter', target=2)
        self.cmd('clear-instance', id=2)
        self.rejects({'op': 'emitter', 'id': 2, 'effect': 'weather/silver-squall', 'count': 1})
        self.cmd('emitter', id=2, effect='weather/autumn-drift', count=1)
        self.register(3, '/weather/rain-two', 'rain', family='emitter', target=1)
        self.rejects({'op': 'state-update', 'id': 3, 'role': 'leaf'})

    def test_material_identifiers_are_existing_integers_with_widget_background_fallback(self):
        """SELECTORS.md: "Material identifiers are existing integers 0..15. Widget backgroundMaterial
        also accepts -1 for the existing fallback." and "Material references must exist when
        used.\""""
        self.register()
        for value in [0, 1, 2.0]:
            self.rule(1, {'family': 'widget'}, {'material': value})
            self.assertEqual(self.effective('material'), value)
        self.rule(1, {'family': 'widget'}, {'backgroundMaterial': -1})
        self.assertEqual(self.effective('backgroundMaterial'), -1)
        for style in [{'material': -1}, {'material': 16}, {'material': 15}, {'material': '2'},
                      {'material': True}, {'backgroundMaterial': -2}, {'backgroundMaterial': 16}]:
            with self.subTest(style=style):
                self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': style})
        self.cmd('area', id=5)
        self.register(5, '/area', family='area', target=5)
        self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': 'area'}, 'style': {'material': -1}})

    def test_color_is_an_integer_0_to_ffffff(self):
        """SELECTORS.md: "`color` is an integer 0..0xffffff.\""""
        self.cmd('node', id=3, label='Node')
        self.register(3, '/color/node', family='node', target=3)
        for value in [0, 0xffffff, 0x123456]:
            self.rule(1, {'family': 'node'}, {'color': value})
            self.assertEqual(self.effective('color', 3), value)
        for value in [-1, 0x1000000, 1.5, '0x123456', True]:
            with self.subTest(color=value):
                self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'node'}, 'style': {'color': value}})

    def test_sampling_is_a_named_policy_and_only_widgets_inherit(self):
        """SELECTORS.md: "`sampling` is `cell`, `half`, `braille` or `hybrid`; only widgets
        additionally accept `inherit`." and "Sampling metadata is numeric: -1 inherit, 0 cell, 1
        half, 2 braille, 3 hybrid.\""""
        self.register()
        self.register(10, '/sampling/floor', family='floor', target=0)
        for name, number in [('inherit', -1), ('cell', 0), ('half', 1), ('braille', 2), ('hybrid', 3)]:
            self.rule(1, {'family': 'widget'}, {'sampling': name})
            self.assertEqual(self.effective('sampling'), number)
        for name in ['cell', 'half', 'braille', 'hybrid']:
            self.rule(2, {'family': 'floor'}, {'sampling': name})
        for value in ['auto', 'Braille', 0, 2, None]:
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': {'sampling': value}})
        self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': 'floor'}, 'style': {'sampling': 'inherit'}})

    def test_rule_override_renders_exactly_like_the_same_authored_property(self):
        """SELECTORS.md: "Alpha retains each component's original meaning." and TDD.md: "Rules
        override only presentation" / "Presentation is resolved into context-owned scratch\""""
        window = [{'op': 'window', 'id': 3, 'title': 'Window', 'text': 'body text here', 'material': 1,
                   'alpha': .3, 'durationMs': 0}, {'op': 'time', 'timeUs': 2000000}]
        floor = [{'op': 'camera', 'position': [0, 18, 35], 'pitch': -25, 'yaw': 0},
                 {'op': 'floor', 'visible': True, 'alpha': .3, 'sampling': 'braille'}]
        triangles = [{'a': [-3, 0, 0], 'b': [-1, 0, 0], 'c': [-2, 2, 0], 'color': 0xff0000, 'alpha': 1},
                     {'a': [1, 0, 0], 'b': [3, 0, 0], 'c': [2, 2, 0], 'color': 0x0000ff, 'alpha': .5}]
        recolored = [dict(t, color=0x00ff00) for t in triangles]
        faded = [dict(t, alpha=.25) for t in triangles]
        widget = [{'op': 'widget', 'id': 9, 'kind': 'button', 'x': 5, 'y': 12, 'width': 25, 'height': 3,
                   'text': 'Equivalent', 'material': 1, 'alpha': .2}]
        plot = [{'op': 'widget', 'id': 9, 'kind': 'pie', 'x': 2, 'y': 12, 'width': 30, 'height': 12,
                 'data': [3, 1], 'sampling': 'braille', 'material': 1}]
        cases = [
            ('widget', 9, widget, {'material': 3}, {'op': 'widget', 'id': 9, 'material': 3}),
            ('widget', 9, widget, {'alpha': .9}, {'op': 'widget', 'id': 9, 'alpha': .9}),
            ('widget', 9, widget, {'backgroundMaterial': 2}, {'op': 'widget', 'id': 9, 'backgroundMaterial': 2}),
            ('widget', 9, plot, {'sampling': 'half'}, {'op': 'widget', 'id': 9, 'sampling': 'half'}),
            ('window', 3, window, {'material': 2}, {'op': 'window', 'id': 3, 'material': 2}),
            ('window', 3, window, {'alpha': .8}, {'op': 'window', 'id': 3, 'alpha': .8}),
            ('text', 3, [{'op': 'text', 'id': 3, 'text': 'Retained', 'effect': 'text/instant-ink', 'material': 1}],
             {'material': 2}, {'op': 'text', 'id': 3, 'material': 2}),
            ('area', 3, [{'op': 'area', 'id': 3, 'material': 1, 'alpha': .3}], {'alpha': .8},
             {'op': 'area', 'id': 3, 'alpha': .8}),
            ('indicator', 3, [{'op': 'indicator', 'id': 3, 'sequence': 'abcd', 'material': 1}], {'material': 2},
             {'op': 'indicator', 'id': 3, 'material': 2}),
            ('node', 3, [{'op': 'node', 'id': 3, 'label': 'Retained'}], {'color': 0x123456},
             {'op': 'node', 'id': 3, 'color': 0x123456}),
            ('floor', 0, floor, {'alpha': .8}, {'op': 'floor', 'alpha': .8}),
            ('floor', 0, floor, {'sampling': 'cell'}, {'op': 'floor', 'sampling': 'cell'}),
            ('mesh', 0, [{'op': 'mesh', 'triangles': triangles}], {'sampling': 'cell'}, {'op': 'mesh', 'sampling': 'cell'}),
            ('mesh', 0, [{'op': 'mesh', 'triangles': triangles}], {'color': 0x00ff00},
             {'op': 'mesh', 'triangles': recolored}),
            ('mesh', 0, [{'op': 'mesh', 'triangles': triangles}], {'alpha': .25}, {'op': 'mesh', 'triangles': faded}),
            ('prompt', 0, [{'op': 'input', 'text': 'draft'}], {'alpha': .4}, {'op': 'prompt', 'alpha': .4}),
        ]
        for family, target, setup, style, authored in cases:
            with self.subTest(family=family, style=style):
                ruled, edited = self.scene(7), self.scene(7)
                try:
                    for scene in (ruled, edited):
                        for command in setup:
                            scene.command(command)
                        self.register(30, '/equivalent/' + family, family=family, target=target, scene=scene)
                    base = ruled.render().bytes
                    self.rule(1, {'family': family}, style, scene=ruled)
                    edited.command(authored)
                    self.assertNotEqual(base, ruled.render().bytes, 'the override must be visible')
                    self.assertEqual(edited.render().bytes, ruled.render().bytes)
                finally:
                    ruled.close()
                    edited.close()

    def test_mesh_sampling_override_does_not_flatten_distinct_triangles(self):
        """SELECTORS.md: "Mesh alpha/color overrides apply to its triangles; an unrelated sampling
        override does not flatten distinct authored triangle colors or opacities. Mesh metadata's
        unoverridden alpha/color represent the first triangle for inspection only.\""""
        self.cmd('mesh', triangles=[{'a': [-3, 0, 0], 'b': [-1, 0, 0], 'c': [-2, 2, 0], 'color': 0xff0000, 'alpha': 1},
                                    {'a': [1, 0, 0], 'b': [3, 0, 0], 'c': [2, 2, 0], 'color': 0x0000ff, 'alpha': .5}])
        self.register(11, '/mesh', family='mesh', target=0)
        authored = self.entry(11)['authored']
        self.assertEqual((authored['color'], authored['alpha']), (0xff0000, 1))
        self.rule(1, {'family': 'mesh'}, {'sampling': 'cell'})
        self.assertEqual(self.entry(11)['effective'], dict(authored, sampling=0))
        styled = self.s.render().bytes
        distinct, flattened = self.scene(), self.scene()
        try:
            for scene, second in [(distinct, (0x0000ff, .5)), (flattened, (0xff0000, 1))]:
                scene.command({'op': 'mesh', 'sampling': 'cell', 'triangles': [
                    {'a': [-3, 0, 0], 'b': [-1, 0, 0], 'c': [-2, 2, 0], 'color': 0xff0000, 'alpha': 1},
                    {'a': [1, 0, 0], 'b': [3, 0, 0], 'c': [2, 2, 0], 'color': second[0], 'alpha': second[1]}]})
                self.register(11, '/mesh', family='mesh', target=0, scene=scene)
            self.assertEqual(distinct.render().bytes, styled)
            self.assertNotEqual(flattened.render().bytes, styled)
        finally:
            distinct.close()
            flattened.close()

    def test_opacity_never_selects_a_different_glyph_family(self):
        """SELECTORS.md: "Neither opacity nor brightness silently selects a different glyph
        family." and AGENTS.md: "Local glyph policies are independent.\""""
        self.cmd('widget', id=9, kind='pie', x=2, y=10, width=30, height=12, data=[3, 1], sampling='braille',
                 material=1, alpha=.2)
        self.register(9, '/plot', target=9)
        glyphs = [w[0] for w in self.owned(self.s.render(), WIDGET_HIT | 9)]
        self.assertTrue(any(0x2800 < g <= 0x28ff for g in glyphs))
        for alpha in [0, .05, 1]:
            self.rule(1, {'family': 'widget', 'id': 9}, {'alpha': alpha})
            self.assertEqual(glyphs, [w[0] for w in self.owned(self.s.render(), WIDGET_HIT | 9)], alpha)

    # ---------------------------------------------------- priority and slots
    def test_priority_is_an_integer_in_the_signed_16_bit_range(self):
        """SELECTORS.md: "Priority is an integer -32768..32767.\""""
        self.register()
        for priority in [-32768, 0, 32767]:
            self.rule(1, priority=priority)
        for priority in [-32769, 32768, 1.5, '1', True, None]:
            self.rejects({'op': 'style-rule', 'id': 1, 'priority': priority, 'selector': {'family': 'widget'},
                          'style': {'material': 2}})

    def test_higher_priority_wins_for_each_property_independently(self):
        """SELECTORS.md: "For each property independently, higher priority wins\""""
        self.register()
        self.rule(50, style={'material': 2}, priority=10)
        self.rule(2, style={'material': 3, 'alpha': .5}, priority=0)
        self.rule(3, style={'alpha': .9}, priority=-32768)
        self.assertEqual((self.effective('material'), self.effective('alpha')), (2, .5))
        self.rule(3, style={'alpha': .9}, priority=1)
        self.assertEqual((self.effective('material'), self.effective('alpha')), (2, .9))
        self.rule(4, style={'material': 0}, priority=-32768)
        self.assertEqual(self.effective('material'), 2)

    def test_equal_priority_uses_later_occupied_slot_edits_keep_slots_and_removal_frees_first_slot(self):
        """SELECTORS.md: "equal priority uses later occupied registration **slot**. Editing a rule
        preserves its slot. Removing a rule frees its slot; newly added rules use the first free
        slot. This deterministic ordering is not CSS specificity or a wall-clock creation-order
        rule.\""""
        self.register()
        for ident, alpha in [(10, .3), (11, .4), (12, .5)]:
            self.rule(ident, style={'alpha': alpha})
        self.assertEqual(self.effective('alpha'), .5)
        self.cmd('remove-style-rule', id=10)
        self.rule(13, style={'alpha': .6})
        self.assertEqual(self.effective('alpha'), .5, 'the newest rule reuses slot 0 and loses')
        self.assertEqual([r['id'] for r in self.s.info()['styleRules']], [13, 11, 12])
        self.rule(11, style={'alpha': .7})
        self.assertEqual(self.effective('alpha'), .5, 'an edit keeps slot 1 below slot 2')
        self.cmd('remove-style-rule', id=12)
        self.assertEqual(self.effective('alpha'), .7, 'slot 1 now beats slot 0')
        self.rejects({'op': 'remove-style-rule', 'id': 12})

    # ----------------------------------------------------------- restoration
    def test_removing_disabling_or_unmatching_exposes_the_latest_authored_style(self):
        """SELECTORS.md: "Resolution starts from the **current authored properties** on every call.
        ... Removing, disabling or ceasing to match a rule exposes the latest authored style,
        including edits performed while overridden.\""""
        self.register(1, '/restore/one', 'control', target=1)
        self.rule(1, {'family': 'widget', 'role': 'control'}, {'material': 2, 'alpha': .8})
        self.cmd('widget', id=1, material=3, alpha=.4)
        self.assertEqual(self.entry()['authored']['material'], 3)
        self.assertEqual((self.effective('material'), self.effective('alpha')), (2, .8))
        self.rule(1, {'family': 'widget', 'role': 'control'}, {'material': 2, 'alpha': .8}, enabled=False)
        self.assertEqual((self.effective('material'), self.effective('alpha')), (3, .4))
        self.rule(1, {'family': 'widget', 'role': 'control'}, {'material': 2, 'alpha': .8})
        self.cmd('widget', id=1, material=0, alpha=.6)
        self.cmd('state-update', id=1, role='elsewhere')
        self.assertEqual((self.effective('material'), self.effective('alpha')), (0, .6))
        self.cmd('state-update', id=1, role='control')
        self.cmd('widget', id=1, material=1, alpha=.1)
        self.cmd('remove-style-rule', id=1)
        self.assertEqual((self.effective('material'), self.effective('alpha')), (1, .1))
        reference = self.scene(2030)
        try:
            reference.command({'op': 'widget', 'id': 1, 'material': 1, 'alpha': .1})
            self.register(1, '/restore/one', 'control', target=1, scene=reference)
            self.assertEqual(reference.render().bytes, self.s.render().bytes)
        finally:
            reference.close()

    def test_rules_do_not_reset_reveals_change_documents_or_restart_widget_timestamps(self):
        """SELECTORS.md: "Rules do not respawn particles, reset reveals, retarget movement, change
        documents, or restyle already deposited leaf identities." and "Changing a widget value
        updates its change timestamp only when the value differs; styling alone does not restart
        its reveal.\""""
        self.cmd('widget', id=9, kind='pie', x=2, y=10, width=30, height=12, data=[3, 1], revealMs=1000, material=1)
        self.cmd('window', id=3, title='Doc', text='retained document', durationMs=0)
        self.register(9, '/plot', target=9)
        self.register(3, '/doc', family='window', target=3)
        self.s.advance_to(300000)
        widget = lambda: next(w for w in self.s.info()['widgets'] if w['id'] == 9)
        before = (widget()['plot']['revealAtUs'], widget()['changedUs'],
                  [w['text'] for w in self.s.info()['windows'] if w['id'] == 3])
        self.rule(1, {'family': 'widget', 'id': 9}, {'alpha': .9, 'material': 3, 'sampling': 'braille'})
        self.rule(2, {'family': 'window'}, {'material': 2, 'alpha': .5})
        self.s.render()
        self.assertEqual(before, (widget()['plot']['revealAtUs'], widget()['changedUs'],
                                  [w['text'] for w in self.s.info()['windows'] if w['id'] == 3]))
        changed = lambda: next(w for w in self.s.info()['widgets'] if w['id'] == 1)['changedUs']
        self.cmd('widget', id=1, value=.25)
        self.assertEqual(changed(), 300000)
        self.s.advance_to(400000)
        self.cmd('widget', id=1, value=.25)
        self.assertEqual(changed(), 300000, 'an unchanged value keeps its timestamp')
        self.cmd('widget', id=1, value=.5)
        self.assertEqual(changed(), 400000)

    # ------------------------------------------------------------------ maps
    def test_map_is_exactly_the_documented_clamped_affine_formula(self):
        """SELECTORS.md: "The map is exactly `outputMin + (outputMax-outputMin) *
        clamp((value-inputMin) / (inputMax-inputMin), 0, 1)`.\""""
        self.register()
        self.cmd('define', path='/load', value=0)

        def expected(value, a, b, lo, hi):
            return lo + (hi - lo) * min(max((value - a) / (b - a), 0), 1)
        for bounds in [(0, 100, .1, .9), (-50, 30, 1, 0), (-1000000, 1000000, 0, 1), (3, 7, .25, .25)]:
            a, b, lo, hi = bounds
            self.rule(1, style={'alpha': {'path': '/load', 'inputMin': a, 'inputMax': b,
                                          'outputMin': lo, 'outputMax': hi}})
            for value in [a - 1e5, a, a + (b - a) / 3, (a + b) / 2, b, b + 1e5, -1e12, 1e12]:
                with self.subTest(bounds=bounds, value=value):
                    self.cmd('set', path='/load', value=value)
                    self.assertMicro(self.effective('alpha'), expected(value, a, b, lo, hi))
                    self.assertEqual(self.entry()['authored']['alpha'], .2)

    def test_map_input_endpoints_are_finite_bounded_and_strictly_increasing(self):
        """SELECTORS.md: "Input endpoints must be finite, within ±1,000,000 and strictly
        increasing.\""""
        self.register()
        self.cmd('define', path='/x', value=1)
        self.rule(1, style={'alpha': {'path': '/x', 'inputMin': -1000000, 'inputMax': 1000000,
                                      'outputMin': 0, 'outputMax': 1}})
        for a, b in [(1, 1), (2, 1), (-1000001, 0), (0, 1000001), (-2e6, -1.5e6), ('0', 1), (None, 1), (False, 1)]:
            with self.subTest(inputMin=a, inputMax=b):
                self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': 'widget'},
                              'style': {'alpha': {'path': '/x', 'inputMin': a, 'inputMax': b,
                                                  'outputMin': 0, 'outputMax': 1}}})
        for raw in [b'-1e999', b'1e999']:
            before = self.s.snapshot()
            with self.assertRaises(ValueError, msg=raw):
                self.s.command_raw(b'{"op":"style-rule","id":2,"selector":{"family":"widget"},"style":{"alpha":'
                                   b'{"path":"/x","inputMin":' + raw + b',"inputMax":1,"outputMin":0,"outputMax":1}}}')
            self.assertEqual(before, self.s.snapshot())

    def test_map_output_endpoints_lie_in_the_unit_interval_and_may_descend(self):
        """SELECTORS.md: "Output endpoints must be in [0,1]; descending output is valid.\""""
        self.register()
        self.cmd('define', path='/x', value=25)
        self.rule(1, style={'alpha': {'path': '/x', 'inputMin': 0, 'inputMax': 100, 'outputMin': 1, 'outputMax': 0}})
        self.assertEqual(self.effective('alpha'), .75)
        for lo, hi in [(-.1, 1), (0, 1.1), (2, 0), (0, -1e-9)]:
            with self.subTest(outputMin=lo, outputMax=hi):
                self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': 'widget'},
                              'style': {'alpha': {'path': '/x', 'inputMin': 0, 'inputMax': 1,
                                                  'outputMin': lo, 'outputMax': hi}}})

    def test_map_references_an_already_defined_numeric_value_with_exact_fields(self):
        """SELECTORS.md: "The path must already be defined." and TDD.md: "Maps reference registered
        values and explicitly clamp a finite input interval to a bounded output interval.\""""
        self.register()
        self.cmd('define', path='/x', value=1)
        self.cmd('define', path='/flag', value=True)
        good = {'path': '/x', 'inputMin': 0, 'inputMax': 1, 'outputMin': 0, 'outputMax': 1}
        for broken in [dict(good, path='/missing'), dict(good, path='/flag'), dict(good, path='x'),
                       {k: v for k, v in good.items() if k != 'outputMax'},
                       {k: v for k, v in good.items() if k != 'path'},
                       dict(good, clamp=True), dict(good, path=['/x'])]:
            with self.subTest(map=broken):
                self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': {'alpha': broken}})
        self.rule(1, style={'alpha': good})

    def test_only_alpha_surface_alpha_and_vein_contrast_accept_maps(self):
        """SELECTORS.md: "Alpha, surfaceAlpha and veinContrast accept maps; discrete material
        identifiers, sampling policies and packed colors do not.\""""
        self.cmd('define', path='/x', value=1)
        self.cmd('emitter', id=4, effect='weather/autumn-drift', count=1)
        self.register(4, '/leaves', 'leaf', family='emitter', target=4)
        self.cmd('node', id=5, label='Node')
        self.register(5, '/node', family='node', target=5)
        self.register()
        mapping = {'path': '/x', 'inputMin': 0, 'inputMax': 2, 'outputMin': 0, 'outputMax': 1}
        for prop in ['alpha', 'surfaceAlpha', 'veinContrast']:
            self.rule(1, {'family': 'emitter'}, {prop: mapping})
            self.assertEqual(self.effective(prop, 4), .5)
        for family, prop in [('widget', 'material'), ('widget', 'backgroundMaterial'), ('widget', 'sampling'),
                             ('emitter', 'material'), ('emitter', 'sampling'), ('node', 'color')]:
            with self.subTest(family=family, property=prop):
                self.rejects({'op': 'style-rule', 'id': 2, 'selector': {'family': family}, 'style': {prop: mapping}})

    def test_constant_material_sampling_and_color_ids_are_not_rounded_value_maps(self):
        """TDD.md: "Constant material/sampling IDs are not rounded value maps." with SELECTORS.md
        "Material identifiers are existing integers" and "`color` is an integer\""""
        self.register()
        self.cmd('node', id=5, label='Node')
        self.register(5, '/node', family='node', target=5)
        for family, style in [('widget', {'material': 1.5}), ('widget', {'material': 2.0000001}),
                              ('widget', {'backgroundMaterial': -0.5}), ('widget', {'backgroundMaterial': 1.25}),
                              ('widget', {'sampling': 1}), ('widget', {'sampling': 2.0}), ('node', {'color': 255.5})]:
            with self.subTest(style=style):
                self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': family}, 'style': style})
        self.rule(1, style={'material': 2.0})
        self.assertEqual(self.effective('material'), 2)

    def test_mapped_and_guarded_values_stay_protected_while_a_rule_references_them(self):
        """DATA-EXPRESSIONS.md: "Current/disabled rules and queued guards/actions protect every
        referenced value" and VALUE-BINDINGS.md: "consumer refusal\""""
        self.register()
        self.cmd('define', path='/map', value=1)
        self.cmd('define', path='/guard', value=1)
        self.rule(1, style={'alpha': {'path': '/map', 'inputMin': 0, 'inputMax': 1, 'outputMin': 0, 'outputMax': 1}},
                  enabled=False)
        self.rule(2, style={'material': 2}, when=leaf('/guard', 'equal', value=1))
        self.rejects({'op': 'remove-value', 'path': '/map'})
        self.rejects({'op': 'remove-value', 'path': '/guard'})
        self.cmd('remove-style-rule', id=1)
        self.cmd('remove-style-rule', id=2)
        self.cmd('remove-value', path='/map')
        self.cmd('remove-value', path='/guard')

    # ---------------------------------------------------------------- guards
    def test_guard_trees_are_bounded_to_31_nodes_and_depth_8(self):
        """CONDITIONS.md: "Trees have at most 31 nodes and depth 8, counting the root as depth 1."
        and SELECTORS.md: "with 31 nodes and depth 8.\""""
        self.register()
        self.cmd('define', path='/heat', value=60)
        deep = leaf()
        for _ in range(7):
            deep = {'not': deep}
        self.rule(1, when=deep)
        self.rule(2, when={'any': [leaf() for _ in range(30)]})
        self.assertEqual([r['conditionNodes'] for r in self.s.info()['styleRules']], [8, 31])
        self.rejects({'op': 'style-rule', 'id': 3, 'selector': {'family': 'widget'}, 'style': {'material': 2},
                      'when': {'not': deep}})
        self.rejects({'op': 'style-rule', 'id': 3, 'selector': {'family': 'widget'}, 'style': {'material': 2},
                      'when': {'any': [leaf() for _ in range(31)]}})

    def test_guard_tree_syntax_errors_reject_atomically(self):
        """CONDITIONS.md: "ALL/ANY require at least one child; NOT accepts one object. ... Unknown
        fields, missing paths, mixed scalar/tree syntax, nonfinite numbers, oversized trees and
        reversed ranges reject atomically.\""""
        self.register()
        self.cmd('define', path='/heat', value=60)
        self.rule(1, when=leaf())
        for tree in [{'all': []}, {'any': []}, {'not': []}, {'not': [leaf()]}, {'all': leaf()},
                     leaf('/missing'), dict(leaf(), unknown=1), {'all': [leaf()], 'any': [leaf()]},
                     {'all': [leaf()], 'path': '/heat'}, leaf(comparison='between', min=4, max=2),
                     leaf(comparison='between', value=3), leaf(comparison='above', min=1, max=2),
                     leaf(comparison='equal', value=2, hysteresis=1), leaf(comparison='not-equal', value=2, hysteresis=.5),
                     leaf(value=1000001), leaf(value=50, hysteresis=1000001), leaf(value=50, hysteresis=-1),
                     leaf(comparison='greater'), {'path': '/heat', 'value': 1}, [leaf()], 'true', True]:
            with self.subTest(tree=tree):
                self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': {'material': 2},
                              'when': tree})

    def test_style_guards_are_current_truth_without_trigger_timing_or_actions(self):
        """SELECTORS.md: "Style guards represent current truth, not trigger edge/debounce/cooldown
        actions." and TDD.md: "Rules override only presentation" / "No expression interpreter,
        event bus or second time source is added.\""""
        self.register()
        self.cmd('define', path='/heat', value=60)
        self.cmd('define', path='/out', value=0)
        for extra in [{'edge': 'rising'}, {'debounceMs': 10}, {'cooldownMs': 10}, {'event': '/review/inspect'},
                      {'target': '/out'}, {'action': 'increment'}, {'value': 1}, {'source': '/heat'},
                      {'expression': 1}]:
            with self.subTest(field=extra):
                self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': {'material': 2},
                              'when': leaf(), **extra})

    def test_style_guards_cannot_read_an_event_payload(self):
        """DATA-EXPRESSIONS.md: "it cannot directly reference an event because appearance has no
        event subscription." and CONDITIONS.md: "A selector without an event gate is ambiguous and
        rejects.\""""
        self.register()
        self.cmd('define', path='/heat', value=60)
        for tree in [{'intentValue': {'comparison': 'at-least', 'value': 1}},
                     {'all': [leaf(), {'intentValue': {'comparison': 'equal', 'value': 7}}]}]:
            self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': {'material': 2},
                          'when': tree})
        self.rejects({'op': 'style-rule', 'id': 1, 'selector': {'family': 'widget'}, 'style': {'material': 2},
                      'whenExpression': {'equal': [{'intentPath': '/value'}, 7]}})
        self.cmd('define', path='/out', value=0)
        self.cmd('trigger', id=1, event='/review', when={'intentValue': {'comparison': 'at-least', 'value': 1}},
                 target='/out', action='increment', value=1)
        self.cmd('trigger', id=2, event='/review', whenExpression={'equal': [{'intentPath': '/value'}, 7]},
                 target='/out', action='increment', value=1)
        self.assertEqual([t['id'] for t in self.s.info()['triggers']], [1, 2], 'the leaves are valid with an event gate')

    def test_hysteresis_expands_each_comparison_release_interval_once_true(self):
        """CONDITIONS.md: "Once a registered-value leaf is true, its release interval expands by
        hysteresis: above/at-least lower their release threshold; below/at-most raise it; between
        expands both ends.\""""
        self.register()
        self.cmd('define', path='/x', value=0)
        sequences = {
            'above': ({'value': 50}, [(51, True), (46, True), (45, False), (49, False), (51, True)]),
            'at-least': ({'value': 50}, [(50, True), (45, True), (44.9, False), (49.9, False)]),
            'below': ({'value': 50}, [(49, True), (54, True), (55, False), (51, False)]),
            'at-most': ({'value': 50}, [(50, True), (55, True), (55.1, False), (50.1, False)]),
            'between': ({'min': 20, 'max': 40}, [(30, True), (15, True), (14.9, False), (18, False),
                                                 (30, True), (45, True), (45.1, False), (41, False)]),
        }
        for comparison, (bounds, steps) in sequences.items():
            with self.subTest(comparison=comparison):
                self.cmd('set', path='/x', value=-500 if comparison in ('above', 'at-least', 'between') else 500)
                self.rule(1, when=leaf('/x', comparison, hysteresis=5, **bounds))
                self.assertFalse(self.guard())
                for value, truth in steps:
                    self.cmd('set', path='/x', value=value)
                    self.assertEqual((value, self.guard()), (value, truth))
                    self.assertEqual(self.effective('material'), 2 if truth else 1)

    def test_reissuing_a_style_rule_restarts_its_hysteresis_released(self):
        """SELECTORS.md: "Reissuing a `style-rule` with the same ID recompiles its guard: per-leaf
        hysteresis restarts released and that command re-evaluates it, as a trigger edit restarts its
        condition state." and "Editing a rule preserves its slot.\""""
        self.register()
        self.cmd('define', path='/heat', value=20)
        self.rule(7, style={'alpha': .3})
        self.rule(1, when=leaf(value=50, hysteresis=5))
        self.cmd('set', path='/heat', value=51)
        self.cmd('set', path='/heat', value=47)
        self.assertEqual((self.guard(1), self.effective('material')), (True, 2))
        self.rule(1, when=leaf(value=50, hysteresis=5), priority=1)
        self.assertEqual((self.guard(1), self.effective('material')), (False, 1))
        self.assertEqual([r['id'] for r in self.s.info()['styleRules']], [7, 1])
        self.cmd('set', path='/heat', value=51)
        self.cmd('set', path='/heat', value=47)
        self.assertEqual((self.guard(1), self.effective('material')), (True, 2))

    def test_every_leaf_updates_its_own_state_without_short_circuit(self):
        """CONDITIONS.md: "Every leaf updates its own state, even in a branch whose result would be
        short-circuited by a conventional boolean expression. That prevents stale hysteresis on
        later use.\""""
        self.register()
        for path, value in [('/a', 1), ('/b', 0), ('/heat', 20)]:
            self.cmd('define', path=path, value=value)
        self.rule(1, when={'any': [leaf('/a', 'equal', value=1), leaf(value=50, hysteresis=5)]})
        self.rule(2, style={'alpha': .9}, when={'all': [leaf('/b', 'equal', value=1), leaf(value=50, hysteresis=5)]})
        self.cmd('set', path='/heat', value=51)
        self.assertEqual((self.guard(1), self.guard(2)), (True, False))
        self.s.batch([{'op': 'set', 'path': '/heat', 'value': 47}, {'op': 'set', 'path': '/a', 'value': 0},
                      {'op': 'set', 'path': '/b', 'value': 1}])
        self.assertEqual((self.guard(1), self.guard(2)), (True, True),
                         'the hysteresis leaves latched at 51 although their branch was decided elsewhere')

    def test_guard_truth_changes_only_through_commands_and_simulation_ticks(self):
        """SELECTORS.md: "Commands and simulation ticks update guard truth. ... Render and metadata
        reads never evaluate hysteresis or fire a trigger." TDD.md: "Only commands and simulation
        ticks update guard state. Rendering and info are pure.\""""
        self.register()
        self.cmd('define', path='/heat', value=20)
        self.cmd('define', path='/go', value=0)
        self.rule(1, when=leaf(value=50, hysteresis=5))
        self.cmd('set', path='/heat', value=51)
        self.cmd('set', path='/heat', value=47)
        latched = self.s.snapshot()
        for _ in range(4):
            self.s.render()
            self.s.info()
            self.s.info_complete()
            self.s.inspect_character_cell(8, 6)
        self.assertEqual(latched, self.s.snapshot())
        self.assertTrue(self.guard())
        self.cmd('input', text='unrelated typing')
        self.assertTrue(self.guard(), 'an unrelated command re-evaluates with the same values')
        self.cmd('trigger', id=1, when=leaf('/go', 'equal', value=1), target='/heat', action='set', value=10,
                 debounceMs=100)
        self.cmd('set', path='/go', value=1)
        self.assertEqual((self.s.info()['values']['/heat'], self.guard()), (47, True))
        self.s.advance_to(150000)
        self.assertEqual((self.s.info()['values']['/heat'], self.guard(), self.effective('material')), (10, False, 1))

    def test_a_batch_evaluates_guards_against_its_final_values_only(self):
        """SELECTORS.md: "A batch uses its final values." and CONDITIONS.md: "It never fires on an
        intermediate combination.\""""
        self.register()
        self.cmd('define', path='/heat', value=20)
        self.rule(1, when=leaf(value=50, hysteresis=5))
        self.s.batch([{'op': 'set', 'path': '/heat', 'value': 60}, {'op': 'set', 'path': '/heat', 'value': 48}])
        self.assertFalse(self.guard(), 'a transient 60 must not latch the leaf')
        self.cmd('set', path='/heat', value=60)
        self.s.batch([{'op': 'set', 'path': '/heat', 'value': 40}, {'op': 'set', 'path': '/heat', 'value': 47}])
        self.assertTrue(self.guard(), 'a transient 40 must not release the latched leaf')

    def test_trigger_evaluation_is_one_bounded_pre_write_pass_even_for_self_reference_and_cycles(self):
        """CONDITIONS.md: "Every evaluation reads one pre-write snapshot of all values. Rules apply
        their constant set/increment actions in stable registration-slot order. No recursive
        same-pass cascade occurs. A rule reading another rule's output sees that change at the next
        explicit evaluation.\""""
        for path in ['/self', '/x', '/y', '/z']:
            self.cmd('define', path=path, value=0)
        self.cmd('trigger', id=1, when=leaf('/self', 'at-least', value=1), target='/self', action='increment',
                 value=1, edge='level')
        self.cmd('trigger', id=2, when=leaf('/x', 'at-least', value=1), target='/y', action='increment', value=1,
                 edge='level')
        self.cmd('trigger', id=3, when=leaf('/y', 'at-least', value=1), target='/x', action='increment', value=1,
                 edge='level')
        self.cmd('set', path='/self', value=1)
        self.cmd('set', path='/x', value=1)
        values = self.s.info()['values']
        self.assertEqual((values['/self'], values['/x'], values['/y']), (3, 1, 1))
        for step in range(1, 4):
            self.cmd('set', path='/z', value=step)
            values = self.s.info()['values']
            self.assertEqual((values['/self'], values['/x'], values['/y']), (3 + step, 1 + step, 1 + step))
        self.s.render()
        self.s.info()
        self.assertEqual(self.s.info()['values']['/self'], 6, 'rendering and info never evaluate rules')

    def test_triggers_on_one_target_apply_in_stable_registration_slot_order(self):
        """CONDITIONS.md: "Rules apply their constant set/increment actions in stable
        registration-slot order.\""""
        for path in ['/go', '/out']:
            self.cmd('define', path=path, value=0)
        self.cmd('trigger', id=9, when=leaf('/go', 'equal', value=1), target='/out', action='set', value=5)
        self.cmd('trigger', id=1, when=leaf('/go', 'equal', value=1), target='/out', action='increment', value=1)
        self.cmd('set', path='/go', value=1)
        self.assertEqual(self.s.info()['values']['/out'], 6)
        self.cmd('set', path='/go', value=0)
        self.cmd('trigger', id=9, when=leaf('/go', 'equal', value=1), target='/out', action='set', value=7)
        self.cmd('set', path='/go', value=1)
        self.assertEqual(self.s.info()['values']['/out'], 8, 'an edited rule keeps its earlier slot')

    def test_retained_events_drive_mapped_appearance_without_acknowledgement_or_replay(self):
        """SELECTORS.md: "Retained notification intentions can drive a bound or mapped value through
        an existing event-gated trigger. Neither styles nor rendering acknowledge that queue." and
        CONDITIONS.md: "Editing the same rule ID and event path restarts condition/debounce state but
        retains its accepted-intent watermark and fire counter\""""
        self.register()
        self.cmd('define', path='/approved', value=0)
        self.cmd('define', path='/enabled', value=1)
        self.rule(1, style={'alpha': {'path': '/approved', 'inputMin': 0, 'inputMax': 4, 'outputMin': .2,
                                      'outputMax': 1}})
        self.cmd('trigger', id=1, when=leaf('/enabled', 'equal', value=1), event='/approve', target='/approved',
                 action='increment', value=1)
        self.cmd('status', id=1, text='Inspect', durationMs=0, actions=[{'id': 1, 'label': 'Inspect', 'event': '/approve'}])
        self.cmd('notification-action', id=1, actionId=1)
        self.assertMicro(self.effective('alpha'), .4)
        for _ in range(3):
            self.s.render()
            self.s.info()
        self.assertEqual(len(self.s.info()['intents']), 1)
        self.cmd('trigger', id=1, when=leaf('/enabled', 'at-least', value=1), event='/approve', target='/approved',
                 action='increment', value=1)
        self.cmd('set', path='/enabled', value=2)
        self.assertEqual(self.s.info()['values']['/approved'], 1, 'a same-event edit must not replay')
        self.assertEqual(self.s.info()['triggers'][0]['lastIntent'], 1)
        self.assertMicro(self.effective('alpha'), .4)

    # ------------------------------------------------------------------ purity
    def purity_scene(self):
        s = self.s
        self.cmd('emitter', id=1, effect='weather/autumn-drift', count=6, runningTimeMs=0)
        self.register(1, '/weather/settled', 'leaf', family='emitter', target=1)
        s.advance_to(20000000)
        self.cmd('emitter', id=2, effect='weather/autumn-drift', count=8, runningTimeMs=0)
        self.register(2, '/weather/airborne', 'leaf', family='emitter', target=2)
        s.advance_to(20500000)
        self.cmd('define', path='/approved', value=0)
        self.cmd('trigger', id=1, source='/approved', comparison='above', threshold=-1, event='/approve',
                 target='/approved', value=1)
        self.cmd('status', id=1, text='Approve', durationMs=0, actions=[{'id': 1, 'label': 'Ok', 'event': '/approve'}])
        self.cmd('notification-action', id=1, actionId=1)
        self.cmd('input', text='draft bytes stay')
        self.assertTrue(s.info()['deposits'] and s.particles(), 'scene needs deposits and airborne leaves')

    def observed(self):
        info = self.s.info()
        return {'snapshot': self.s.snapshot(), 'particles': self.s.particles(), 'deposits': info['deposits'],
                'triggers': [(t['id'], t['lastIntent'], t['fireCount']) for t in info['triggers']],
                'intents': info['intents'], 'prompt': info['prompt']['text'], 'values': info['values']}

    def test_sampling_appearance_changes_no_physics_deposit_birth_draft_or_watermark(self):
        """TDD.md: "Presentation is resolved into context-owned scratch, never into authoritative
        State. Physics, deposited styles, birth identities, draft bytes and rule/event watermarks
        must not change as a consequence of sampling appearance.\""""
        self.purity_scene()
        trigger = self.s.info()['triggers'][0]
        self.assertEqual((trigger['lastIntent'], trigger['fireCount']), (1, 1), 'a real accepted-intent watermark')
        authored = [self.entry(i)['authored'] for i in (1, 2)]
        emitters = self.s.info()['emitters']
        self.rule(1, {'family': 'emitter'}, {'material': 3, 'sampling': 'braille', 'alpha': .5,
                                             'surfaceAlpha': .9, 'veinContrast': 1})
        before = self.observed()
        for _ in range(6):
            self.s.render()
            self.s.info()
            self.s.info_complete()
        self.assertEqual(before, self.observed())
        self.assertEqual(authored, [self.entry(i)['authored'] for i in (1, 2)])
        self.assertEqual(emitters, self.s.info()['emitters'])
        self.assertTrue(all(self.entry(i)['effective'] != self.entry(i)['authored'] for i in (1, 2)))

    def test_appearance_rules_do_not_alter_simulation_evolution(self):
        """SELECTORS.md: "Rules do not respawn particles, reset reveals, retarget movement, change
        documents, or restyle already deposited leaf identities." and TDD.md: "Physics, deposited
        styles, birth identities ... must not change as a consequence of sampling appearance.\""""
        self.purity_scene()
        baseline = self.s.snapshot()
        self.rule(1, {'family': 'emitter'}, {'material': 3, 'sampling': 'half', 'surfaceAlpha': .9,
                                             'veinContrast': 1})
        for time in range(20600000, 23000001, 400000):
            self.s.advance_to(time)
            self.s.render()
        self.cmd('remove-style-rule', id=1)
        styled = self.s.snapshot()
        reference = NativeScene(2030)
        try:
            reference.restore(baseline)
            for time in range(20600000, 23000001, 400000):
                reference.advance_to(time)
            self.assertEqual(reference.particles(), self.s.particles())
            self.assertEqual(reference.info()['deposits'], self.s.info()['deposits'])
            self.assertEqual(reference.snapshot(), styled)
        finally:
            reference.close()

    def test_deposited_leaves_keep_the_style_captured_at_deposition(self):
        """SELECTORS.md: "Rules do not ... restyle already deposited leaf identities." and API.md:
        "Render is pure and deposited identities are not restyled.\""""
        self.cmd('emitter', id=1, effect='weather/autumn-drift', count=6, runningTimeMs=0)
        self.register(1, '/weather/settled', 'leaf', family='emitter', target=1)
        self.s.advance_to(20000000)
        self.assertEqual(self.s.particles(), [])
        self.assertTrue(self.s.info()['deposits'])
        frame = self.s.render().bytes
        bare = self.scene()
        try:
            bare.advance_to(20000000)
            self.assertNotEqual(bare.render().bytes, frame, 'the settled deposits must be visible')
        finally:
            bare.close()
        self.rule(1, {'family': 'emitter'}, {'material': 3, 'sampling': 'braille', 'alpha': .2,
                                             'surfaceAlpha': .9, 'veinContrast': 1})
        self.assertEqual(frame, self.s.render().bytes)

    # ------------------------------------------------------------------ replay
    def test_snapshot_replay_restores_registry_rules_interaction_and_latched_guards(self):
        """TDD.md: "trajectories, render purity, snapshot replay and hostile restored indices" and
        SELECTORS.md: "`info().registeredStates` exposes path, role, family, targetId, existence,
        state flags, authored and effective properties. `styleRules` exposes ID, priority, enabled,
        guard truth and condition-node count.\""""
        self.register(1, '/replay/one', target=1)
        self.register(2, '/replay/two', 'other', target=2)
        self.cmd('define', path='/heat', value=20)
        self.cmd('define', path='/load', value=30)
        self.rule(1, {'family': 'widget', 'states': {'hover': True}}, {'material': 3}, priority=5)
        self.rule(2, {'family': 'widget', 'role': 'other'}, {'alpha': {'path': '/load', 'inputMin': 0,
                                                                         'inputMax': 100, 'outputMin': 0,
                                                                         'outputMax': 1}})
        self.rule(3, {'family': 'widget', 'pathPrefix': '/replay'}, {'backgroundMaterial': 2},
                  when=leaf(value=50, hysteresis=5))
        self.cmd('set', path='/heat', value=55)
        self.cmd('set', path='/heat', value=47)
        self.cmd('pointer', phase='down', x=8, y=6)
        saved, frame, info = self.s.snapshot(), self.s.render().bytes, self.s.info()
        self.cmd('remove-style-rule', id=3)
        self.cmd('state-unregister', id=2)
        restored = NativeScene(99)
        try:
            restored.restore(saved)
            restored_info = restored.info()
            for key in ['registeredStates', 'styleRules', 'values']:
                self.assertEqual(info[key], restored_info[key], key)
            self.assertEqual(frame, restored.render().bytes)
            self.assertEqual(saved, restored.snapshot())
            self.s.restore(saved)
            for scene in (self.s, restored):
                scene.command({'op': 'set', 'path': '/heat', 'value': 46})
                scene.command({'op': 'pointer', 'phase': 'up', 'x': 8, 'y': 6})
                scene.advance_to(500000)
            self.assertEqual(self.s.snapshot(), restored.snapshot())
            self.assertTrue(self.guard(3, restored))
        finally:
            restored.close()

    # --------------------------------------------------------- value bindings
    def test_boolean_bindings_accept_exactly_numeric_zero_or_one(self):
        """SELECTORS.md: "Boolean bindings accept exactly numeric 0 or 1." and "Invalid bindings
        reject atomically\""""
        self.register(21, '/bind/state', target=1)
        for field, family, ident in [('selected', 'widget', 1), ('enabled', 'widget', 1), ('active', 'widget', 1),
                                     ('active', 'state', 21)]:
            path = '/bind/%s/%s' % (family, field)
            self.cmd('define', path=path, value=1, binding={'family': family, 'id': ident, 'field': field})
            self.cmd('set', path=path, value=0)
            self.cmd('set', path=path, value=1)
            for value in [.5, 2, -1, 1e-9]:
                with self.subTest(field=field, value=value):
                    self.rejects({'op': 'set', 'path': path, 'value': value})

    def test_material_bindings_require_existing_integer_ids_and_alpha_is_bounded(self):
        """SELECTORS.md: "Material bindings require existing integer IDs. Alpha is bounded to
        [0,1].\""""
        self.cmd('define', path='/m', value=1, binding={'family': 'widget', 'id': 1, 'field': 'material'})
        self.cmd('define', path='/bg', value=-1, binding={'family': 'widget', 'id': 1, 'field': 'backgroundMaterial'})
        self.cmd('define', path='/a', value=.5, binding={'family': 'widget', 'id': 1, 'field': 'alpha'})
        for path, value in [('/m', 1.5), ('/m', -1), ('/m', 15), ('/m', 16), ('/bg', -2), ('/bg', .5),
                            ('/a', -.01), ('/a', 1.01)]:
            with self.subTest(path=path, value=value):
                self.rejects({'op': 'set', 'path': path, 'value': value})
        self.cmd('set', path='/m', value=2.0)
        self.cmd('set', path='/a', value=1)
        widget = next(w for w in self.s.info()['widgets'] if w['id'] == 1)
        self.assertEqual((widget['material'], widget['backgroundMaterial'], widget['alpha']), (2, -1, 1))

    def test_invalid_bindings_reject_atomically_in_trigger_actions_and_batches(self):
        """SELECTORS.md: "Invalid bindings reject atomically, including in trigger actions and
        batches.\""""
        self.cmd('define', path='/a', value=.5, binding={'family': 'widget', 'id': 1, 'field': 'alpha'})
        self.cmd('define', path='/go', value=0)
        self.cmd('trigger', id=1, when=leaf('/go', 'equal', value=1), target='/a', action='set', value=2)
        self.rejects({'op': 'set', 'path': '/go', 'value': 1})
        self.rejects({'op': 'batch', 'commands': [{'op': 'input', 'text': 'atomic'},
                                                  {'op': 'set', 'path': '/a', 'value': 3}]})
        self.assertEqual(self.s.info()['prompt']['text'], '')

    def test_state_binding_id_names_the_registry_entry_and_floor_binding_uses_zero(self):
        """SELECTORS.md: "floor | alpha; binding ID must be zero" and "state | active; binding ID
        identifies the registry entry\""""
        self.register(21, '/bind/registry', target=1)
        self.rule(1)
        self.rejects({'op': 'define', 'path': '/wrong', 'value': 0, 'binding': {'family': 'state', 'id': 1,
                                                                                 'field': 'active'}})
        self.cmd('define', path='/active', value=0, binding={'family': 'state', 'id': 21, 'field': 'active'})
        self.assertEqual((self.entry(21)['states']['active'], self.effective('material', 21)), (False, 1))
        self.cmd('set', path='/active', value=1)
        self.assertEqual(self.effective('material', 21), 2)
        self.rejects({'op': 'define', 'path': '/floor/bad', 'value': .5, 'binding': {'family': 'floor', 'id': 1,
                                                                                      'field': 'alpha'}})
        self.cmd('define', path='/floor/alpha', value=.5, binding={'family': 'floor', 'id': 0, 'field': 'alpha'})
        self.rejects({'op': 'set', 'path': '/floor/alpha', 'value': 1.5})

    # ---------------------------------------------------- character selectors
    def test_character_selector_paths_follow_the_historical_value_path_grammar(self):
        """CHARACTER-SELECTORS.md: "The reference is `bindings/chromatic/chromatic-style.js`,
        specifically validateSelector and matching." validateSelector applies valuePath to a
        nonempty `path` or `pathPrefix`: an absolute path without `//`, empty segments, a `~` not
        followed by `0`/`1`, or `__proto__`/`prototype`/`constructor` segments; an empty string is
        skipped and imposes no filter. Native strings fit 128 UTF-8 bytes (127 payload bytes)."""
        def rule(field, value, ident='paths'):
            return {'op': 'character-rule', 'rule': {'id': ident, 'selector': {field: value}, 'foreground': 2}}
        for field in ['path', 'pathPrefix']:
            for value in ['/app', '/app/styled', '/a~0b', '/a~1b/c', '/screen/background', '/a b', '/café',
                          '/' + 'a' * 126, '']:
                with self.subTest(field=field, accepted=value):
                    self.s.command(rule(field, value))
            for value in ['/', '/app/', '//app', '/app//x', '/__proto__', '/app/prototype', '/x/constructor',
                          '/a~2', '/a~', '/~', 'app', '/' + 'a' * 127]:
                with self.subTest(field=field, rejected=value):
                    self.rejects(rule(field, value, 'rejected'))
        self.assertEqual([r['id'] for r in self.s.info()['characterRules']], ['paths'])

    def test_character_selector_empty_path_imposes_no_filter(self):
        """CHARACTER-SELECTORS.md (historical `matching`): `if (s.path && s.path !== path)` and
        `if (s.pathPrefix && ...)`: an empty path or prefix string imposes no path filter, so the
        selected treatment matches exactly like an omitted path."""
        self.register(1, '/app/styled', 'user-text', target=1)
        outputs = []
        for selector in [{'role': 'user-text'}, {'role': 'user-text', 'path': ''},
                         {'role': 'user-text', 'pathPrefix': ''}]:
            self.cmd('character-rule', rule={'id': 'treatment', 'selector': selector,
                                             'foregroundEffects': [{'type': 'invert'}], 'protectLocalInk': False})
            outputs.append(self.s.render().bytes)
        self.cmd('remove-character-rule', id='treatment')
        untreated = self.s.render().bytes
        self.assertNotEqual(outputs[0], untreated)
        self.assertEqual(outputs, [outputs[0]] * 3)


if __name__ == '__main__':
    unittest.main()
