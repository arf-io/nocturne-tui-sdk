"""RC4-026 executable acceptance matrix: StatusArea and Notification behaviour.

Expectations are derived from the contract text, never from current output:
native/docs/NOTIFICATIONS.md, STATUS-WORKFLOWS.md, STATUS-WORKFLOWS-20261011.md,
NODE-STATUS-GALLERY.md, the status sections of API.md, CONDITIONS.md and
TRIGGER-EXPRESSIONS.md (retained-event watermarks), AREA-GEOMETRY.md and the
area/status/pause field reference in docs/current/Commands.md. Every test quotes
the sentence it enforces. The retained regression module test_notifications.py is
unchanged; the sentences it already pins are listed in ALREADY_PINNED and are not
duplicated here. tests/status_notifications_wasm.mjs runs the same cases through
the import-free WASM build of the same C core.
"""
from pathlib import Path
import hashlib, importlib.util, json, os, struct, subprocess, sys, unittest, zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

ACTION_FAMILY = 0x63
SAFE_INTEGER = 9007199254740991
ALREADY_PINNED = {
    'At 64 pending intentions, activation rejects before consuming the action': 'testQueueFullDoesNotConsumeActionOrMessage',
    'An action activates once per message version ... idempotent, including after its intention was acknowledged': 'testActionIsIdempotentUntilMessageExplicitlyReplaced',
    'A missing acknowledgement is idempotent': 'testAckMissingIntentIsIdempotent',
    'Modal ownership wins': 'testModalBlocksNotificationActions',
    'clicking an action never falls through to camera/weather input (active action)': 'testActionButtonUsesCurrentHitMap',
    'Fixed `durationMs` and derived duration are mutually exclusive': 'testStaticDurationAndDynamicDurationAreExclusive',
    'Important records cannot coalesce': 'testImportantAndCoalescingRejected',
    'Coalescing requires nonempty key (key omitted)': 'testCoalescingRequiresKey',
    'At most four unique actions (duplicate identities)': 'testDuplicateActionIdsRejected',
    'A notification action is data, never a callback': 'testUnknownActionPropertyRejected',
    'Zero-alpha actions have no pointer hit': 'testZeroMaterialAlphaRemovesInkAndActionHits',
    'Status material alpha and blend now affect notification ink': 'testStatusMaterialBlendIsApplied',
}

def hit_id(message, slot=0):
    return (ACTION_FAMILY << 24) | (message << 2) | slot

def cells(frame, predicate):
    return [(i % frame.width, i // frame.width) for i, w in enumerate(frame.words()) if predicate(w)]

def glyphs(frame, glyph):
    return cells(frame, lambda w: w[0] == ord(glyph))

def inked(frame, glyph):
    """Cells showing the glyph with foreground distinct from its background."""
    return cells(frame, lambda w: w[0] == ord(glyph) and w[1] != w[2])

def word(frame, x, y):
    return frame.words()[y * frame.width + x]

def baseline(seed=18):
    scene = NativeScene(seed)
    scene.command({'op': 'environment', 'stars': 0})
    scene.command({'op': 'prompt', 'active': False})
    return scene


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.s = baseline(); self.addCleanup(self.s.close)
    def fresh(self, seed=18):
        scene = baseline(seed); self.addCleanup(scene.close); return scene
    def cmd(self, op, **fields):
        return self.s.command({'op': op, **fields})
    def area(self, ident=1, scene=None, **fields):
        options = dict(id=ident, x=2, y=3, width=30, height=6, border='none', padding=0,
                       alpha=0, layout='ordered', gapMs=0)
        options.update(fields); (scene or self.s).command({'op': 'area', **options})
    def status(self, ident=None, scene=None, **fields):
        options = dict(area=1, text='Notice', durationMs=0)
        if ident is not None: options['id'] = ident
        if 'dwellPerCharacterMs' in fields: options.pop('durationMs')
        options.update(fields); return (scene or self.s).command({'op': 'status', **options})
    def action(self, ident=1, **fields):
        return {'id': ident, 'label': 'Go', 'event': '/task/go', **fields}
    def info(self, scene=None):
        return (scene or self.s).info_complete()
    def messages(self, scene=None):
        return self.info(scene)['messages']
    def record(self, ident, scene=None):
        return next(m for m in self.messages(scene) if m['id'] == ident)
    def states(self, scene=None):
        return {m['id']: m['state'] for m in self.messages(scene)}
    def intents(self, scene=None):
        return self.info(scene)['intents']
    def rejects(self, command, scene=None):
        scene = scene or self.s; before = scene.snapshot()
        with self.assertRaises(ValueError, msg=command): scene.command(command)
        self.assertEqual(scene.snapshot(), before, command)
    def activate(self, message, action=1, scene=None):
        (scene or self.s).command({'op': 'notification-action', 'id': message, 'actionId': action})


class OwnershipAndScope(Acceptance):
    def test_record_is_retained_after_expiry_and_dismissal_until_purge(self):
        """NOTIFICATIONS.md: "A status message is a retained source record."
        API.md: "Expired/dismissed records remain recoverable until `purge-status`"."""
        self.area()
        self.status(1, text='Expires Ω', durationMs=1000)
        self.status(2, text='Dismissed Ψ')
        self.s.advance_to(1_000_000); self.cmd('dismiss', id=2)
        self.assertEqual((self.record(1)['state'], self.record(1)['text']), ('expired', 'Expires Ω'))
        self.assertEqual((self.record(2)['state'], self.record(2)['text']), ('dismissed', 'Dismissed Ψ'))
        frame = self.s.render()
        self.assertEqual(glyphs(frame, 'Ω') + glyphs(frame, 'Ψ'), [])
        self.cmd('purge-status', id=1)
        self.assertEqual([m['id'] for m in self.messages()], [2])

    def test_area_owns_clipping_and_complete_text_is_recoverable(self):
        """NOTIFICATIONS.md: "Its area owns layout and clipping."
        AREA-GEOMETRY.md: "Parent offsets add; each ancestor and owner rectangle intersects the viewport." """
        self.area(1, x=5, y=6, width=8, height=3)
        self.area(2, parent=1, x=4, y=1, width=10, height=4)
        self.area(3, x=40, y=6, width=8, height=3)
        self.status(2, area=2, text='Ψ' * 40)
        self.status(3, area=3, text='Ω' * 40)
        frame = self.s.render()
        own = glyphs(frame, 'Ω')
        self.assertEqual(len(own), 24)
        self.assertTrue(all(40 <= x < 48 and 6 <= y < 9 for x, y in own), own)
        nested = glyphs(frame, 'Ψ')
        self.assertEqual(sorted(nested), [(x, y) for x in range(9, 13) for y in range(7, 9)])
        self.assertEqual(self.s.area_geometry(2), [9, 7, 10, 4, 9, 7, 4, 2, 9, 7, 10, 4])
        self.assertEqual(self.record(2)['text'], 'Ψ' * 40)
        self.assertEqual(self.record(3)['text'], 'Ω' * 40)

    def test_activation_is_one_ordered_intention_that_rendering_never_consumes(self):
        """NOTIFICATIONS.md: "Activation creates one ordered intention that the host may
        inspect, handle, and acknowledge. Rendering never consumes it." """
        self.area()
        self.status(1, actions=[self.action()])
        self.activate(1)
        intents, snapshot = self.intents(), self.s.snapshot()
        self.assertEqual(len(intents), 1)
        for _ in range(3):
            self.s.render(); self.s.info(); self.s.info_complete(); self.s.inspect_character_cell(3, 3)
        self.assertEqual(self.intents(), intents)
        self.assertEqual(self.s.snapshot(), snapshot)

    def test_content_overflow_reports_reader_and_keeps_complete_source(self):
        """NOTIFICATIONS.md: "An area must be large enough for its content/action panels;
        overflow reports `contentNeedsReader` and full action metadata remains available."
        Resolved there as: "Each render counts every active record whose unscrolled text extends
        past its area's content box ... Marquee motion does not enlarge the box." """
        long = 'Too long for the area to show'
        inspect = [self.action(label='Inspect')]
        def needs(texts, mode='static', height=2, width=12, border='none', actions=()):
            with baseline() as scene:
                self.area(1, scene=scene, width=width, height=height, border=border)
                for ident, text in enumerate(texts, 1):
                    self.status(ident, scene=scene, text=text, mode=mode, actions=list(actions))
                scene.render(); info = self.info(scene)
            self.assertEqual([m['text'] for m in sorted(info['messages'], key=lambda m: m['id'])], list(texts))
            for record in info['messages']:
                self.assertEqual([(a['id'], a['label'], a['event']) for a in record['actions']],
                                 [(a['id'], a['label'], a['event']) for a in actions])
            return info['render']['contentNeedsReader']
        with self.subTest('content and action panel fit'):
            self.assertEqual(needs(['Fits'], height=4, actions=inspect), 0)
        with self.subTest('action panel below the box'):
            self.assertGreaterEqual(needs(['Fits'], height=2, actions=inspect), 1)
        for mode in ('static', 'pop', 'fade', 'horizontal', 'vertical', 'horizontal-fade', 'vertical-fade'):
            with self.subTest('text larger than the content box', mode=mode):
                self.assertGreaterEqual(needs([long + '\n' + long], mode=mode), 1)
        with self.subTest('ordered record stacked below the box'):
            self.assertGreaterEqual(needs(['first', 'second'], height=1), 1)
        with self.subTest('area without a content box'):
            self.assertGreaterEqual(needs(['x'], width=2, border='square'), 1)

    def test_consumed_action_stays_visible_inactive_and_owns_its_press(self):
        """NOTIFICATIONS.md: "clicking an action never falls through to camera/weather input.
        Consumed actions remain visible but inactive." and "Repeated activation of an
        already-consumed action is idempotent" (a native pointer hit activates it)."""
        self.area(1, x=4, y=4, width=40, height=8, layout='queue')
        self.status(1, text='Build needs review', actions=[self.action(label='Review', event='/build/review')])
        frame = self.s.render()
        button = cells(frame, lambda w: w[3] == hit_id(1))
        letters = set(map(ord, 'Review'))
        label = [(x, y) for x, y in button if word(frame, x, y)[0] in letters]
        self.assertEqual(len(label), len('Review'))
        self.activate(1)
        self.assertTrue(self.record(1)['actions'][0]['activated'])
        consumed = self.s.render()
        self.assertEqual([word(consumed, x, y)[0] for x, y in label], [word(frame, x, y)[0] for x, y in label])
        before = self.info()
        x, y = label[len(label) // 2]
        self.cmd('pointer', phase='down', x=x, y=y)
        self.cmd('pointer', phase='move', x=x + 6, y=y + 1)
        self.cmd('pointer', phase='up', x=x + 6, y=y + 1)
        after = self.info()
        self.assertEqual(after['intents'], before['intents'])
        self.assertEqual(after['messages'], before['messages'])
        self.assertEqual(after['camera'], before['camera'])
        self.assertEqual(after['fieldCount'], before['fieldCount'])
        self.cmd('ack-intent', id=1)
        for phase in ('down', 'up'): self.cmd('pointer', phase=phase, x=x, y=y)
        self.assertEqual(self.intents(), [])


class MessageAuthoring(Acceptance):
    def test_key_is_at_most_63_utf8_bytes(self):
        """NOTIFICATIONS.md: "key | Optional UTF-8 grouping key, at most 63 bytes." """
        self.area()
        for ident, key in ((1, 'a' * 63), (2, 'é' * 31 + 'a')):
            self.status(ident, key=key); self.assertEqual(self.record(ident)['key'], key)
        for key in ('a' * 64, 'é' * 32):
            self.rejects({'op': 'status', 'id': 3, 'area': 1, 'text': 'k', 'durationMs': 0, 'key': key})

    def test_key_is_scoped_to_its_area(self):
        """NOTIFICATIONS.md: "key | ... Scoped to the area." """
        self.area(1); self.area(2, y=12)
        for area in (1, 2, 1):
            self.status(area=area, text='Build', key='build', coalesce='count')
        self.assertEqual(sorted((m['area'], m['occurrences']) for m in self.messages()), [(1, 2), (2, 1)])

    def test_coalesce_choices_default_none_and_nonempty_key(self):
        """NOTIFICATIONS.md: "coalesce | `none`, `count`, `replace-queued`. Default none.
        Requires nonempty key." """
        self.area()
        self.rejects({'op': 'status', 'area': 1, 'text': 'x', 'key': 'k', 'coalesce': 'merge'})
        self.rejects({'op': 'status', 'area': 1, 'text': 'x', 'key': '', 'coalesce': 'count'})
        self.status(text='same', key='k'); self.status(text='same', key='k')
        self.status(text='same', key='k', coalesce='none')
        self.assertEqual([m['occurrences'] for m in self.messages()], [1, 1, 1])

    def test_at_most_four_actions(self):
        """NOTIFICATIONS.md: "actions | At most four unique actions per message" """
        self.area()
        self.status(1, actions=[self.action(i, label=f'A{i}') for i in range(1, 5)])
        self.assertEqual([a['id'] for a in self.record(1)['actions']], [1, 2, 3, 4])
        self.rejects({'op': 'status', 'id': 2, 'area': 1, 'text': 'x',
                      'actions': [self.action(i, label=f'A{i}') for i in range(1, 6)]})

    def test_dwell_per_character_is_an_integer_from_0_to_60000(self):
        """NOTIFICATIONS.md: "dwellPerCharacterMs | Integer milliseconds per retained scalar, 0..60000." """
        self.area()
        self.status(1, text='x', dwellPerCharacterMs=60000)
        self.status(2, text='x', dwellPerCharacterMs=0)
        self.assertEqual((self.record(1)['durationUs'], self.record(2)['durationUs']), (60_000_000, 1_000_000))
        for value in (60001, -1, 1.5, '5'):
            self.rejects({'op': 'status', 'id': 3, 'area': 1, 'text': 'x', 'dwellPerCharacterMs': value})

    def test_derived_duration_is_clamped_with_documented_defaults_and_bounds(self):
        """NOTIFICATIONS.md: "minDurationMs / maxDurationMs | Derived-duration bounds, defaults
        1000 and 60000; 0..86400000." and "The derived duration is
        clamp(scalarCount * dwellPerCharacterMs, minDurationMs, maxDurationMs)." """
        self.area()
        self.status(1, text='abcde', dwellPerCharacterMs=10)
        self.status(2, text='x' * 30, dwellPerCharacterMs=100)
        self.status(3, text='x' * 1000, dwellPerCharacterMs=100)
        self.status(4, text='x', dwellPerCharacterMs=1, minDurationMs=0, maxDurationMs=86400000)
        self.assertEqual([self.record(i)['durationUs'] for i in range(1, 5)],
                         [1_000_000, 3_000_000, 60_000_000, 1_000])
        base = {'op': 'status', 'id': 5, 'area': 1, 'text': 'x', 'dwellPerCharacterMs': 1}
        for patch in ({'maxDurationMs': 86400001}, {'minDurationMs': 86400001}, {'minDurationMs': -1},
                      {'minDurationMs': 2000, 'maxDurationMs': 1000}, {'minDurationMs': 1.5}):
            self.rejects({**base, **patch})
        self.rejects({'op': 'status', 'id': 5, 'area': 1, 'text': 'x', 'minDurationMs': 10})

    def test_derived_duration_counts_scalars_not_bytes(self):
        """NOTIFICATIONS.md: "dwellPerCharacterMs | Integer milliseconds per retained scalar" """
        self.area()
        text = 'Aé界éZ'  # six scalars, ten UTF-8 bytes
        self.status(1, text=text, dwellPerCharacterMs=100, minDurationMs=0, maxDurationMs=10000)
        self.assertEqual(self.record(1)['durationUs'], 600_000)

    def test_fixed_duration_default_and_zero_without_automatic_expiry(self):
        """Commands.md status: "durationMs ... Fixed dwell; default 6000 ms; zero prevents
        automatic expiry". NOTIFICATIONS.md: "Duration zero means no automatic expiry." """
        self.area()
        self.cmd('status', id=1, area=1, text='default')
        self.status(2, text='forever', durationMs=0)
        self.assertEqual(self.record(1)['durationUs'], 6_000_000)
        self.s.advance_to(5_999_999); self.assertEqual(self.states(), {1: 'active', 2: 'active'})
        self.s.advance_to(6_000_000); self.assertEqual(self.states(), {1: 'expired', 2: 'active'})
        self.s.advance_to(30_000_000); self.assertEqual(self.states()[2], 'active')

    def test_blank_message_is_a_record_that_occupies_its_minimum_dwell(self):
        """NOTIFICATIONS.md: "A blank message is still a record and still gets its configured
        minimum dwell." API.md: "An intentional empty message still occupies its dwell time." """
        self.area(layout='queue')
        self.status(1, text='', dwellPerCharacterMs=50)
        self.status(2, text='Next', durationMs=1000)
        self.assertEqual(self.record(1)['durationUs'], 1_000_000)
        self.s.advance_to(999_999); self.assertEqual(self.states(), {1: 'active', 2: 'queued'})
        self.s.advance_to(1_000_000); self.assertEqual(self.states(), {1: 'expired', 2: 'active'})
        self.assertEqual(self.record(2)['startUs'], 1_000_000)

    def test_priority_is_nonpreemptive_and_equal_priority_uses_accepted_order(self):
        """NOTIFICATIONS.md: "priority chooses the next message, never interrupts the active one."
        API.md: "A queue activates the highest-priority ready item when idle; it does not preempt
        an active message. Equal priority uses accepted order." """
        self.area(layout='queue')
        for ident, priority in ((1, 0), (2, 0), (3, 50), (4, 50)):
            self.status(ident, text=f'm{ident}', durationMs=1000, priority=priority)
        self.s.advance_to(999_999); self.assertEqual(self.states(), {1: 'active', 2: 'queued', 3: 'queued', 4: 'queued'})
        self.s.advance_to(1_500_000); self.assertEqual(self.states()[3], 'active')
        self.status(5, text='urgent', durationMs=1000, priority=100)
        self.assertEqual((self.states()[3], self.states()[5]), ('active', 'queued'))
        self.s.advance_to(2_000_000); self.assertEqual(self.states()[5], 'active')
        self.s.advance_to(3_000_000); self.assertEqual(self.states()[4], 'active')
        self.s.advance_to(4_000_000); self.assertEqual(self.states()[2], 'active')
        self.assertEqual([self.record(i)['startUs'] for i in (1, 3, 5, 4, 2)],
                         [0, 1_000_000, 2_000_000, 3_000_000, 4_000_000])

    def test_duration_begins_at_activation_and_gap_separates_messages(self):
        """API.md: "Duration begins at activation, not enqueue." and "`gapMs` applies between messages." """
        self.area(layout='queue', gapMs=250)
        self.status(1, text='first', durationMs=1000)
        self.status(2, text='second', durationMs=500)
        self.s.advance_to(1_249_999); self.assertEqual(self.states(), {1: 'expired', 2: 'queued'})
        self.s.advance_to(1_250_000); self.assertEqual(self.states()[2], 'active')
        second = self.record(2)
        self.assertEqual((second['readyUs'], second['startUs'], second['durationUs']), (0, 1_250_000, 500_000))
        self.s.advance_to(1_749_999); self.assertEqual(self.states()[2], 'active')
        self.s.advance_to(1_750_000); self.assertEqual(self.states()[2], 'expired')

    def test_authored_deferred_start_is_preserved(self):
        """Commands.md status: "startTimeUs ... Exact integer native timestamp, 0–86400000000;
        defaults to current time". NODE-STATUS-GALLERY.md: "preserve an authored deferred start" """
        self.area()
        self.status(1, text='later', startTimeUs=500_000, durationMs=1000)
        self.assertEqual((self.record(1)['state'], self.record(1)['readyUs']), ('queued', 500_000))
        self.s.advance_to(499_999); self.assertEqual(self.states()[1], 'queued')
        self.s.advance_to(500_000); self.assertEqual((self.states()[1], self.record(1)['startUs']), ('active', 500_000))
        self.status(2, text='now', durationMs=0)
        self.assertEqual((self.record(2)['readyUs'], self.record(2)['startUs']), (500_000, 500_000))
        self.s.advance_to(1_499_999); self.assertEqual(self.states()[1], 'active')
        self.s.advance_to(1_500_000); self.assertEqual(self.states()[1], 'expired')
        for start in (1.5, 86_400_000_001, -1):
            self.rejects({'op': 'status', 'id': 3, 'area': 1, 'text': 'x', 'startTimeUs': start})

    def test_count_merges_only_identical_live_records(self):
        """NOTIFICATIONS.md: "`count` merges identical live content and action configuration
        under the same key. It increments occurrences without resetting start or duration.
        Different content or policy rejects atomically." """
        self.area()
        base = dict(text='Compile', key='k', coalesce='count', durationMs=1000, actions=[self.action()])
        self.status(1, **base)
        self.s.advance_to(300_000); self.status(**base)
        first = self.record(1)
        self.assertEqual((first['occurrences'], first['startUs'], first['durationUs']), (2, 0, 1_000_000))
        command = {'op': 'status', 'area': 1, **base}
        for patch in ({'actions': [self.action(label='Other')]}, {'priority': 5}, {'mode': 'pop'},
                      {'durationMs': 2000}):
            self.rejects({**command, **patch})
        self.status(2, text='Compile', key='q')
        self.rejects({**command, 'key': 'q'})
        self.s.advance_to(1_000_000); self.status(**base)
        self.assertEqual(sorted((m['id'], m['state'], m['occurrences']) for m in self.messages()),
                         [(1, 'expired', 2), (2, 'active', 1), (3, 'active', 1)])

    def test_replace_queued_replaces_only_an_undisplayed_record(self):
        """NOTIFICATIONS.md: "`replace-queued` replaces only an undisplayed queued record,
        retaining its identity and sequence; active content remains unchanged." """
        self.area(layout='queue')
        policy = dict(key='progress', coalesce='replace-queued', durationMs=1000)
        self.status(text='10%', **policy)
        self.status(text='20%', **policy)
        queued = self.record(2)
        self.assertEqual((self.record(1)['state'], queued['state']), ('active', 'queued'))
        self.status(text='30%', **policy)
        replaced = self.record(2)
        self.assertEqual((replaced['text'], replaced['sequence'], replaced['replacements']), ('30%', queued['sequence'], 1))
        self.assertEqual((self.record(1)['text'], self.record(1)['replacements']), ('10%', 0))
        self.assertEqual(len(self.messages()), 2)
        self.s.advance_to(1_000_000)
        self.assertEqual((self.record(2)['state'], self.record(2)['text']), ('active', '30%'))

    def test_replacement_is_a_new_version_with_fresh_action_state(self):
        """NOTIFICATIONS.md: "A replacement is a deliberate new version and resets its action
        activation state." """
        self.area()
        self.status(7, text='v1', actions=[self.action()])
        self.activate(7)
        first = self.record(7)
        self.status(7, text='v2', actions=[self.action()])
        second = self.record(7)
        self.assertFalse(second['actions'][0]['activated'])
        self.assertGreater(second['sequence'], first['sequence'])
        self.activate(7)
        self.assertEqual([(q['messageId'], q['messageSequence']) for q in self.intents()],
                         [(7, first['sequence']), (7, second['sequence'])])

    def test_automatic_ids_are_monotonic(self):
        """NOTIFICATIONS.md: "Automatic ids are monotonic and separate from weather identities" """
        self.area()
        self.status(text='a'); self.status(3, text='explicit'); self.status(text='b'); self.status(text='c')
        self.assertEqual([m['id'] for m in sorted(self.messages(), key=lambda m: m['sequence'])], [1, 3, 2, 4])
        self.cmd('dismiss', id=4); self.cmd('purge-status', id=4)
        self.status(text='d')
        self.assertIn(5, [m['id'] for m in self.messages()])
        self.assertNotIn(4, [m['id'] for m in self.messages()])

    def test_explicit_id_cannot_replace_an_unacknowledged_important_record(self):
        """NOTIFICATIONS.md: "explicit ids must not replace an unacknowledged important record."
        and "important | ... When true, replacing/purging/clearing requires `ack-status`." """
        self.area()
        self.status(9, text='Warning', important=True)
        replacement = {'op': 'status', 'id': 9, 'area': 1, 'text': 'Overwrite', 'durationMs': 0}
        self.rejects(replacement)
        self.cmd('dismiss', id=9); self.rejects(replacement)
        self.cmd('ack-status', id=9); self.cmd(**replacement)
        self.assertEqual(self.record(9)['text'], 'Overwrite')

    def test_history_capacity_is_explicit_and_never_evicts(self):
        """NOTIFICATIONS.md: "Finite history capacity is explicit; an exhausted history rejects
        new records until the application intentionally frees slots. No current status API
        silently discards a warning." API.md: "the 48-record bound does not silently evict
        important data." """
        self.area()
        self.status(1, text='Warning', important=True)
        self.status(2, text='tick', key='t', coalesce='count')
        for ident in range(3, 49): self.status(ident, text=f'm{ident}')
        self.rejects({'op': 'status', 'id': 49, 'area': 1, 'text': 'overflow', 'durationMs': 0})
        self.rejects({'op': 'status', 'area': 1, 'text': 'overflow', 'durationMs': 0})
        self.status(text='tick', key='t', coalesce='count')
        self.assertEqual(self.record(2)['occurrences'], 2)
        self.cmd('dismiss', id=3); self.cmd('purge-status', id=3)
        self.status(49, text='accepted after an explicit purge')
        self.assertEqual(len(self.messages()), 48)
        warning = self.record(1)
        self.assertEqual((warning['text'], warning['important'], warning['acknowledged']), ('Warning', True, False))


class ActionsAndIntentions(Acceptance):
    def test_action_identity_is_an_integer_from_1_to_65535(self):
        """NOTIFICATIONS.md: "Each action: id integer 1..65535" """
        self.area()
        self.status(1, actions=[self.action(1), self.action(65535, label='Last')])
        self.assertEqual([a['id'] for a in self.record(1)['actions']], [1, 65535])
        for ident in (0, 65536, 1.5, '1'):
            self.rejects({'op': 'status', 'id': 2, 'area': 1, 'text': 'x', 'actions': [self.action(ident)]})

    def test_action_label_is_one_to_64_scalars(self):
        """NOTIFICATIONS.md: "label 1..64 supported scalars" """
        self.area()
        for ident, label in ((1, '界' * 64), (2, 'é' * 32)):
            self.status(ident, actions=[self.action(label=label)])
            self.assertEqual(self.record(ident)['actions'][0]['label'], label)
        for label in ('界' * 65, ''):
            self.rejects({'op': 'status', 'id': 3, 'area': 1, 'text': 'x', 'actions': [self.action(label=label)]})

    def test_action_event_is_a_canonical_path_up_to_127_bytes(self):
        """NOTIFICATIONS.md: "event canonical path up to 127 bytes" and "Event segments accept
        ASCII alphanumeric, `_`, `-`, and `.`; empty, dot/dot-dot, trailing separator and
        whitespace segments reject." """
        self.area()
        accepted = ['/' + 'a' * 126, '/a_b-c.d/E9', '/x/.hidden', '/v1.2/run']
        for ident, event in enumerate(accepted, 1):
            self.status(ident, actions=[self.action(event=event)])
            self.assertEqual(self.record(ident)['actions'][0]['event'], event)
        for event in ('/' + 'a' * 127, '/', '', 'a/b', '/a//b', '/a/', '/a/.', '/a/./b', '/a/..',
                      '/a/../b', '/a b', '/a\tb', '/é'):
            self.rejects({'op': 'status', 'id': 9, 'area': 1, 'text': 'x', 'actions': [self.action(event=event)]})

    def test_action_value_and_dismiss_defaults_and_bounds(self):
        """NOTIFICATIONS.md: "value finite number -1000000..1000000 (default 0); dismiss boolean
        (default false)." """
        self.area()
        self.status(1, actions=[self.action(1), self.action(2, label='Hi', value=1000000),
                                self.action(3, label='Lo', value=-1000000, dismiss=True)])
        self.assertEqual([(a['value'], a['dismiss']) for a in self.record(1)['actions']],
                         [(0, False), (1000000, False), (-1000000, True)])
        for patch in ({'value': 1000000.5}, {'value': -1000001}, {'dismiss': 'yes'}, {'dismiss': 1}):
            self.rejects({'op': 'status', 'id': 2, 'area': 1, 'text': 'x', 'actions': [self.action(**patch)]})
        before = self.s.snapshot()
        with self.assertRaises(ValueError):
            self.s.command_raw(b'{"op":"status","id":2,"area":1,"text":"x","actions":'
                               b'[{"id":1,"label":"A","event":"/a","value":NaN}]}')
        self.assertEqual(self.s.snapshot(), before)

    def test_intention_record_has_the_documented_shape(self):
        """NOTIFICATIONS.md: "The result appears in `info().intents`:
        {"id":1,"messageId":40,"actionId":1,"messageSequence":1,"event":"/build/inspect","value":40,"atUs":0}" """
        self.area(2)
        self.cmd('status', id=40, area=2, text='Build requires review', important=True, mode='pop',
                 durationMs=0, actions=[{'id': 1, 'label': 'Inspect', 'event': '/build/inspect', 'value': 40}])
        self.cmd('notification-action', id=40, actionId=1)
        self.assertEqual(self.intents(), [{'id': 1, 'messageId': 40, 'actionId': 1, 'messageSequence': 1,
                                           'event': '/build/inspect', 'value': 40, 'atUs': 0}])
        self.s.advance_to(250_000)
        self.status(41, area=2, actions=[self.action()]); self.activate(41)
        self.assertEqual(self.intents()[-1]['atUs'], 250_000)

    def test_intention_ids_are_monotonic_and_returned_in_id_order(self):
        """NOTIFICATIONS.md: "IDs are monotonic up to the JavaScript safe integer limit. Results are
        returned in id order." """
        self.area()
        for ident in (1, 2, 3):
            self.status(ident, actions=[self.action()]); self.activate(ident)
        self.cmd('ack-intent', id=1)
        self.status(4, actions=[self.action()]); self.activate(4)
        self.assertEqual([q['id'] for q in self.intents()], [2, 3, 4])
        self.cmd('ack-intent', id=4)
        self.status(5, actions=[self.action()]); self.activate(5)
        self.assertEqual([q['id'] for q in self.intents()], [2, 3, 5])

    def test_intention_ids_stop_at_the_javascript_safe_integer_limit(self):
        """NOTIFICATIONS.md: "IDs are monotonic up to the JavaScript safe integer limit."
        A CRC-correct snapshot places the retained counter just below the limit."""
        self.area()
        self.status(1, actions=[self.action(i, label=f'A{i}') for i in range(1, 5)])
        def u64(value): return struct.pack('<Q', value)
        steps = [lambda: None,
                 lambda: (self.activate(1, 1), self.cmd('ack-intent', id=1)),
                 lambda: (self.activate(1, 2), self.cmd('ack-intent', id=2)),
                 lambda: self.cmd('define', path='/unrelated', value=5),
                 lambda: self.activate(1, 3)]
        offsets = None
        for step, value in zip(steps, (1, 2, 3, 3, 4)):
            step(); data = self.s.snapshot()
            if offsets is None:
                offsets, at = [], data.find(u64(value), 24)
                while at >= 0: offsets.append(at); at = data.find(u64(value), at + 1)
            else:
                offsets = [at for at in offsets if data[at:at + 8] == u64(value)]
        self.assertEqual(len(offsets), 1, 'the retained intention counter must be unambiguous')
        patched = bytearray(data); patched[offsets[0]:offsets[0] + 8] = u64(SAFE_INTEGER)
        struct.pack_into('<I', patched, 20, zlib.crc32(patched[24:]))
        scene = self.fresh(); scene.restore(bytes(patched))
        self.activate(1, 4, scene=scene)
        self.assertEqual([q['id'] for q in self.intents(scene)], [3, SAFE_INTEGER])
        self.status(2, scene=scene, actions=[self.action()])
        self.rejects({'op': 'notification-action', 'id': 2, 'actionId': 1}, scene=scene)
        scene.command({'op': 'ack-intent', 'id': SAFE_INTEGER})
        self.rejects({'op': 'notification-action', 'id': 2, 'actionId': 1}, scene=scene)
        self.assertFalse(self.record(2, scene)['actions'][0]['activated'])

    def test_inactive_or_missing_actions_reject_atomically(self):
        """NOTIFICATIONS.md: "Inactive/missing actions reject." """
        self.area(1, layout='queue')
        self.status(1, durationMs=1000, actions=[self.action()])
        self.status(2, actions=[self.action()])
        self.status(3, area=0, durationMs=500, actions=[self.action()])
        self.status(4, area=0, actions=[self.action()]); self.cmd('dismiss', id=4)
        self.s.advance_to(500_000)
        self.assertEqual(self.states(), {1: 'active', 2: 'queued', 3: 'expired', 4: 'dismissed'})
        for message, action in ((99, 1), (1, 9), (2, 1), (3, 1), (4, 1)):
            self.rejects({'op': 'notification-action', 'id': message, 'actionId': action})
        self.assertEqual(self.intents(), [])

    def test_ack_intent_removes_only_that_intention(self):
        """NOTIFICATIONS.md: "The host's `{ "op":"ack-intent", "id":1 }` removes that intention
        only. A missing acknowledgement is idempotent." """
        self.area()
        for ident in (1, 2, 3):
            self.status(ident, actions=[self.action(event=f'/task/{ident}')]); self.activate(ident)
        before = self.intents()
        self.cmd('ack-intent', id=2)
        self.assertEqual(self.intents(), [before[0], before[2]])
        snapshot = self.s.snapshot(); self.cmd('ack-intent', id=2)
        self.assertEqual(self.s.snapshot(), snapshot)

    def test_intentions_survive_expiry_rendering_input_snapshots_and_reset_clears_them(self):
        """NOTIFICATIONS.md: "Intention records survive message expiry/dismissal/purge/status
        clearing, normal rendering, input and snapshots. Reset explicitly creates a new scene and
        clears them." """
        self.cmd('prompt', active=True)
        self.area()
        self.status(1, durationMs=1000, actions=[self.action()]); self.activate(1)
        retained = self.intents()
        self.s.advance_to(1_000_000); self.assertEqual(self.states()[1], 'expired')
        self.s.render(); self.s.render()
        self.cmd('input', text='typed while pending')
        self.assertEqual(self.info()['prompt']['text'], 'typed while pending')
        self.assertEqual(self.intents(), retained)
        restored = self.fresh(99); restored.restore(self.s.snapshot())
        self.assertEqual(self.intents(restored), retained)
        self.cmd('reset')
        self.assertEqual((self.messages(), self.intents()), ([], []))

    def test_ack_status_neither_purges_nor_acknowledges_intentions(self):
        """NOTIFICATIONS.md: "`ack-status` acknowledges an important source record; it neither
        purges content nor acknowledges its action intentions." STATUS-WORKFLOWS.md: the
        workflow "rejects acknowledgment of a missing record." """
        self.area()
        self.status(1, text='Important', important=True, actions=[self.action()]); self.activate(1)
        intents = self.intents()
        self.cmd('ack-status', id=1)
        record = self.record(1)
        self.assertEqual((record['acknowledged'], record['state'], record['text']), (True, 'active', 'Important'))
        self.assertEqual(self.intents(), intents)
        self.rejects({'op': 'ack-status', 'id': 77})

    def test_dismiss_removes_presentation_and_keeps_the_record(self):
        """NOTIFICATIONS.md: "`dismiss` removes the presentation." """
        self.area(1); self.area(2, y=12, layout='queue')
        self.status(1, text='ΩΩΩ')
        self.assertTrue(glyphs(self.s.render(), 'Ω'))
        self.cmd('dismiss', id=1)
        self.assertEqual(glyphs(self.s.render(), 'Ω'), [])
        self.assertEqual((self.record(1)['state'], self.record(1)['text']), ('dismissed', 'ΩΩΩ'))
        self.status(2, area=2, text='first', durationMs=1000)
        self.status(3, area=2, text='ΨΨΨ', durationMs=1000)
        self.cmd('dismiss', id=3); self.s.advance_to(2_000_000)
        self.assertEqual(self.states()[3], 'dismissed')
        self.assertEqual(glyphs(self.s.render(), 'Ψ'), [])

    def test_dismiss_action_is_separate_from_acknowledgement_and_purge(self):
        """NODE-STATUS-GALLERY.md: "Four action workflows separate dismiss policy from explicit
        intent acknowledgement and purge." STATUS-WORKFLOWS.md: "message removal never
        acknowledges them." """
        self.area(layout='queue', gapMs=250)
        self.status(1, text='Close me', actions=[self.action(label='Close', event='/close', dismiss=True)])
        self.status(2, text='next')
        self.s.advance_to(100_000); self.activate(1)
        self.assertEqual(self.states(), {1: 'dismissed', 2: 'queued'})
        self.assertEqual([q['event'] for q in self.intents()], ['/close'])
        self.s.advance_to(349_999); self.assertEqual(self.states()[2], 'queued')
        self.s.advance_to(350_000); self.assertEqual((self.states()[2], self.record(2)['startUs']), ('active', 350_000))
        self.cmd('purge-status', id=1); self.cmd('clear', scope='status')
        self.assertEqual([q['event'] for q in self.intents()], ['/close'])
        self.cmd('ack-intent', id=1); self.assertEqual(self.intents(), [])

    def test_clear_status_cannot_erase_an_unacknowledged_important_record(self):
        """NOTIFICATIONS.md: "`purge-status` and `clear status` cannot erase an unacknowledged
        important record." """
        self.area()
        self.status(1, text='Important', important=True); self.status(2, text='Normal')
        self.rejects({'op': 'clear', 'scope': 'status'})
        self.cmd('ack-status', id=1); self.cmd('clear', scope='status')
        self.assertEqual(self.messages(), [])

    def test_purge_rejects_live_records(self):
        """STATUS-WORKFLOWS.md: "The important workflow rejects live purge" and API.md:
        "Expired/dismissed records remain recoverable until `purge-status`" """
        self.area(layout='queue')
        self.status(1, durationMs=1000); self.status(2, durationMs=1000)
        for ident in (1, 2): self.rejects({'op': 'purge-status', 'id': ident})
        self.s.advance_to(1_000_000); self.cmd('purge-status', id=1)
        self.cmd('dismiss', id=2); self.cmd('purge-status', id=2)
        self.assertEqual(self.messages(), [])


class SimulationClock(Acceptance):
    def test_rendering_and_reads_never_expire_or_activate_records(self):
        """NOTIFICATIONS.md: "Rendering never consumes it." API.md: "Duration begins at
        activation, not enqueue." Expiry and activation follow the simulation clock only."""
        self.area(layout='queue')
        self.status(1, text='first', durationMs=1000, actions=[self.action()])
        self.status(2, text='second', durationMs=1000)
        self.s.advance_to(999_999)
        snapshot = self.s.snapshot()
        for _ in range(3):
            self.s.render(); self.s.info(); self.s.info_complete(); self.s.inspect_character_cell(2, 3)
        self.assertEqual(self.s.snapshot(), snapshot)
        self.assertEqual(self.states(), {1: 'active', 2: 'queued'})
        self.s.advance_to(1_000_000)
        self.assertEqual(self.states(), {1: 'expired', 2: 'active'})

    def test_paused_clock_holds_expiry(self):
        """Commands.md pause: "`true` stops clock advancement". NOTIFICATIONS.md: "Duration zero
        means no automatic expiry" - any other duration elapses on the simulation clock."""
        self.area()
        self.status(1, durationMs=1000)
        self.cmd('pause', paused=True); self.s.advance_to(5_000_000)
        self.assertEqual((self.info()['clock']['timeUs'], self.states()[1]), (0, 'active'))
        self.cmd('pause', paused=False); self.s.advance_to(1_000_000)
        self.assertEqual(self.states()[1], 'expired')

    def test_scheduled_activation_sees_expiry_at_its_boundary(self):
        """API.md: "A command is structurally and semantically checked when accepted and checked
        again at execution against the then-current state. It runs at the first simulation
        boundary at or after atUs." NOTIFICATIONS.md: "Inactive/missing actions reject." """
        command = {'op': 'notification-action', 'id': 1, 'actionId': 1}
        for chunks in ([1_000_000], [996_000, 1_000_000], [500_000, 999_999, 1_000_000]):
            with self.subTest(chunks=chunks):
                scene = self.fresh()
                self.status(1, scene=scene, area=0, durationMs=1000, actions=[self.action()])
                scene.schedule(9, 1_000_000, command)
                with self.assertRaises(ValueError):
                    for time in chunks: scene.advance_to(time)
                self.assertEqual(self.intents(scene), [])
        immediate = self.fresh()
        self.status(1, scene=immediate, area=0, durationMs=1000, actions=[self.action()])
        immediate.advance_to(1_000_000)
        self.rejects(command, scene=immediate)

    def test_scheduled_status_outcome_does_not_depend_on_advance_chunking(self):
        """ARCHITECTURE.md §5: "Presentation may sample at 30, 60, or another frequency without
        changing simulation results." API.md: scheduled commands are "checked again at execution
        against the then-current state". NOTIFICATIONS.md: "`count` merges identical live content" """
        record = {'op': 'status', 'area': 0, 'text': 'tick', 'key': 'k', 'coalesce': 'count', 'durationMs': 995}
        def run(chunks):
            scene = self.fresh(); scene.command({**record, 'id': 1}); scene.schedule(9, 1_000_000, record)
            for time in chunks: scene.advance_to(time)
            return scene
        runs = {'single': run([2_000_000]), 'chunked': run([996_000, 2_000_000]),
                '60 Hz': run(list(range(16_667, 2_000_000, 16_667)) + [2_000_000])}
        expected = [(1, 'expired', 1, 0), (2, 'expired', 1, 1_000_000)]
        for name, scene in runs.items():
            with self.subTest(run=name):
                self.assertEqual(sorted((m['id'], m['state'], m['occurrences'], m['startUs'])
                                        for m in self.messages(scene)), expected)
                self.assertEqual(scene.snapshot(), runs['single'].snapshot())


class Presentation(Acceptance):
    def test_pop_is_full_ink_at_first_sample_and_gone_at_expiry(self):
        """NOTIFICATIONS.md: "`pop` is full opacity at its first visible sample and disappears at expiry." """
        self.area(fadeMs=1000)
        self.status(1, text='ΣΣ', mode='pop', durationMs=4000)
        self.status(2, text='ΩΩ', mode='fade', durationMs=4000)
        first = self.s.render()
        pop = inked(first, 'Σ'); self.assertEqual(len(pop), 2)
        self.s.advance_to(2_000_000); full = self.s.render()
        self.assertEqual(word(first, *pop[0])[1], word(full, *inked(full, 'Ω')[0])[1])
        self.s.advance_to(3_999_999); self.assertEqual(len(inked(self.s.render(), 'Σ')), 2)
        self.s.advance_to(4_000_000); self.assertEqual(glyphs(self.s.render(), 'Σ'), [])

    def test_fade_modes_retain_configured_easing(self):
        """NOTIFICATIONS.md: "`fade`, `horizontal-fade`, and `vertical-fade` retain configured easing." """
        self.area(1, fadeMs=1000, speedX=0, speedY=0)
        self.area(2, y=12, fadeMs=250, speedX=0, speedY=0)
        self.status(1, text='ΩΩ', mode='fade', durationMs=4000)
        self.status(2, text='ΨΨ', mode='horizontal-fade', durationMs=4000)
        self.status(3, text='ΦΦ', mode='vertical-fade', durationMs=4000)
        self.status(4, area=2, text='ΣΣ', mode='fade', durationMs=4000)
        self.status(5, text='ΘΘ', mode='pop', durationMs=4000)
        def colour(frame, glyph):
            found = glyphs(frame, glyph); return word(frame, *found[0])[1] if found else None
        start = self.s.render()
        for glyph in 'ΩΨΦΣ': self.assertEqual(inked(start, glyph), [], glyph)
        full = colour(start, 'Θ')
        self.s.advance_to(250_000); early = self.s.render()
        self.assertNotIn(colour(early, 'Ω'), (None, full))
        self.s.advance_to(500_000); middle = self.s.render()
        self.assertEqual(colour(middle, 'Σ'), full)
        self.assertNotIn(colour(middle, 'Ω'), (None, full))
        self.s.advance_to(2_000_000); held = self.s.render()
        for glyph in 'ΩΨΦΣ': self.assertEqual(colour(held, glyph), full, glyph)
        self.s.advance_to(3_750_000)
        self.assertNotIn(colour(self.s.render(), 'Ω'), (None, full))
        self.s.advance_to(4_000_000)
        self.assertEqual(glyphs(self.s.render(), 'Ω'), [])

    def test_action_button_is_drawn_only_where_it_fits_completely(self):
        """NOTIFICATIONS.md: "Buttons use the current native hit map and are drawn only where the
        complete button fits." """
        self.area(1, height=2)
        self.status(1, text='Short', actions=[self.action(label='Inspect')])
        frame = self.s.render()
        self.assertEqual(cells(frame, lambda w: w[3] >> 24 == ACTION_FAMILY), [])
        self.assertGreaterEqual(self.info()['render']['contentNeedsReader'], 1)
        self.area(1, height=4)
        frame = self.s.render()
        button = cells(frame, lambda w: w[3] == hit_id(1))
        xs, ys = [x for x, _ in button], [y for _, y in button]
        rectangle = [(x, y) for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)]
        self.assertEqual(sorted(button, key=lambda p: (p[1], p[0])), rectangle)
        self.assertTrue(2 <= min(xs) and max(xs) < 32 and 3 <= min(ys) and max(ys) < 7)
        rows = [''.join(chr(word(frame, x, y)[0]) for x in range(min(xs), max(xs) + 1)) for y in range(min(ys), max(ys) + 1)]
        self.assertTrue(any('Inspect' in row for row in rows), rows)

    def test_ordered_layout_arranges_records_without_overlap(self):
        """ARCHITECTURE.md §13 / Commands.md area: "ordered, queue or direct notification
        arrangement"; StatusArea "covers ordered/direct layout". """
        self.area()
        self.status(1, text='ΩΩ'); self.status(2, text='ΨΨ')
        frame = self.s.render()
        first, second = glyphs(frame, 'Ω'), glyphs(frame, 'Ψ')
        self.assertEqual(len(first), 2); self.assertEqual(len(second), 2)
        self.assertLess(max(y for _, y in first), min(y for _, y in second))

    def test_direct_layout_places_records_at_area_relative_coordinates(self):
        """Commands.md status: "x ... Area-relative layout placement", "y ... Area-relative layout
        placement". AREA-GEOMETRY.md: "Content uses authored padding plus one cell of chrome for
        any non-none border" """
        self.area(1, x=10, y=5, layout='direct')
        self.area(2, x=50, y=5, height=8, layout='direct', border='rounded', padding=1)
        self.status(1, area=1, text='ΩΨ', x=4, y=2)
        self.status(2, area=2, text='ΦΣ', x=4, y=2)
        frame = self.s.render()
        self.assertEqual((glyphs(frame, 'Ω'), glyphs(frame, 'Ψ')), ([(14, 7)], [(15, 7)]))
        self.assertEqual((glyphs(frame, 'Φ'), glyphs(frame, 'Σ')), ([(56, 9)], [(57, 9)]))

    def test_queue_layout_presents_one_record_at_a_time(self):
        """API.md: "A queue activates the highest-priority ready item when idle; it does not
        preempt an active message." """
        self.area(layout='queue')
        self.status(1, text='ΩΩ', durationMs=1000); self.status(2, text='ΨΨ', durationMs=1000)
        frame = self.s.render()
        self.assertEqual((len(glyphs(frame, 'Ω')), len(glyphs(frame, 'Ψ'))), (2, 0))
        self.s.advance_to(1_000_000); frame = self.s.render()
        self.assertEqual((len(glyphs(frame, 'Ω')), len(glyphs(frame, 'Ψ'))), (0, 2))

    def test_empty_area_disappears_only_with_hide_empty_and_keeps_ownership(self):
        """Commands.md area: "hideEmpty ... controls empty-area presentation rather than deleting
        ownership." ARCHITECTURE.md §13: StatusArea covers "empty-area disappearance". """
        corner = ord('┌')
        self.area(1, x=2, y=3, width=12, height=4, border='square', hideEmpty=True)
        self.area(2, x=20, y=3, width=12, height=4, border='square')
        frame = self.s.render()
        self.assertNotEqual(word(frame, 2, 3)[0], corner)
        self.assertEqual(word(frame, 20, 3)[0], corner)
        self.assertEqual(self.s.area_geometry(1)[:4], [2, 3, 12, 4])
        self.status(1, text='now visible')
        self.assertEqual(word(self.s.render(), 2, 3)[0], corner)

    def test_local_text_remains_immediate(self):
        """NOTIFICATIONS.md: "Local text always remains immediate." """
        self.cmd('prompt', active=True)
        self.area(layout='queue')
        self.status(1, actions=[self.action()]); self.status(2, actions=[self.action()]); self.activate(1)
        messages, intents = self.messages(), self.intents()
        self.cmd('input', text='abc')
        self.assertEqual(self.info()['prompt']['text'], 'abc')
        self.assertEqual((self.messages(), self.intents()), (messages, intents))


class Persistence(Acceptance):
    def test_snapshot_round_trip_retains_queue_counters_consumption_and_intentions(self):
        """NOTIFICATIONS.md: "Snapshots retain message counters, action consumption and pending
        intentions." """
        self.area(layout='queue', gapMs=100)
        self.status(text='first', durationMs=1000, actions=[self.action(1), self.action(2, label='Two')])
        self.status(text='second', durationMs=1000, priority=5)
        self.status(text='third', durationMs=1000, key='k', coalesce='replace-queued')
        self.status(text='third v2', durationMs=1000, key='k', coalesce='replace-queued')
        self.status(10, area=0, text='important', important=True)
        for _ in range(2): self.status(area=0, text='tele', key='t', coalesce='count', durationMs=5000)
        self.activate(1, 1)
        snapshot = self.s.snapshot()
        restored = self.fresh(99); restored.restore(snapshot)
        self.assertEqual(restored.snapshot(), snapshot)
        for key in ('messages', 'intents', 'areas'):
            self.assertEqual(self.info(restored)[key], self.info()[key], key)
        for scene in (self.s, restored):
            self.status(scene=scene, area=0, text='after restore')
            self.activate(1, 1, scene=scene); self.activate(1, 2, scene=scene)
            scene.advance_to(2_500_000)
        self.assertEqual(restored.snapshot(), self.s.snapshot())
        self.assertEqual(self.record(5, restored)['text'], 'after restore')
        self.assertEqual([(q['id'], q['actionId']) for q in self.intents(restored)], [(1, 1), (2, 2)])
        self.assertEqual({i: self.states(restored)[i] for i in (1, 2, 3)}, {1: 'expired', 2: 'expired', 3: 'active'})
        self.assertEqual((self.record(3, restored)['text'], self.record(3, restored)['startUs']), ('third v2', 2_200_000))
        self.assertEqual(self.record(4, restored)['occurrences'], 2)

    def test_unrecognized_snapshot_length_rejects_atomically(self):
        """NOTIFICATIONS.md: "Other schema/length pairs reject." """
        self.area(); self.status(1, actions=[self.action()]); self.activate(1)
        snapshot = self.s.snapshot()
        truncated = bytearray(snapshot[:-1])
        struct.pack_into('<I', truncated, 16, len(truncated) - 24)
        struct.pack_into('<I', truncated, 20, zlib.crc32(truncated[24:]))
        with self.assertRaises(ValueError): self.s.restore(bytes(truncated))
        self.assertEqual(self.s.snapshot(), snapshot)


class RetainedEventWatermarks(Acceptance):
    def setUp(self):
        super().setUp()
        self.cmd('define', path='/enabled', value=1); self.cmd('define', path='/out', value=0)
    def rule(self, scene=None, **fields):
        options = {'op': 'trigger', 'id': 1, 'event': '/task/approved', 'target': '/out',
                   'when': {'path': '/enabled', 'comparison': 'equal', 'value': 1},
                   'action': 'increment', 'value': 1}
        options.update(fields); (scene or self.s).command(options)
    def approve(self, ident, event='/task/approved', scene=None):
        self.status(ident, scene=scene, area=0, actions=[self.action(event=event)])
        self.activate(ident, scene=scene)
    def out(self, scene=None):
        return self.info(scene)['values']['/out']
    def trigger(self, scene=None):
        return self.info(scene)['triggers'][0]

    def test_same_event_edit_keeps_watermark_and_restarts_debounce(self):
        """CONDITIONS.md: "Editing the same rule ID and event path restarts condition/debounce
        state but retains its accepted-intent watermark and fire counter: previously accepted
        intentions do not replay." """
        self.rule(debounceMs=100)
        self.approve(1)
        self.s.advance_to(100_000)
        self.assertEqual((self.out(), self.trigger()['lastIntent'], self.trigger()['fireCount']), (1, 1, 1))
        self.approve(2)
        self.s.advance_to(150_000); self.rule(debounceMs=100, value=10)
        self.assertEqual((self.trigger()['lastIntent'], self.trigger()['fireCount']), (1, 1))
        self.s.advance_to(200_000); self.assertEqual(self.out(), 1)
        self.s.advance_to(300_000)
        self.assertEqual((self.out(), self.trigger()['lastIntent'], self.trigger()['fireCount']), (11, 2, 2))
        self.s.advance_to(600_000); self.assertEqual(self.out(), 11)

    def test_watermark_survives_message_removal_and_snapshot_restore(self):
        """CONDITIONS.md: "Pending and accepted intent IDs, condition-node count, truth, counters,
        and timing are inspectable under `info().triggers`. Snapshots preserve them."
        STATUS-WORKFLOWS.md: "message removal never acknowledges them." """
        self.rule(); self.approve(1)
        self.assertEqual(self.out(), 1)
        self.rule(value=5)
        self.cmd('dismiss', id=1); self.cmd('purge-status', id=1); self.cmd('clear', scope='status')
        self.assertEqual([q['id'] for q in self.intents()], [1])
        restored = self.fresh(99); restored.restore(self.s.snapshot())
        restored.command({'op': 'set', 'path': '/enabled', 'value': 0})
        restored.command({'op': 'set', 'path': '/enabled', 'value': 1})
        self.assertEqual((self.out(restored), self.trigger(restored)['lastIntent']), (1, 1))
        self.approve(2, scene=restored)
        self.assertEqual((self.out(restored), self.trigger(restored)['lastIntent'],
                          self.trigger(restored)['fireCount']), (6, 2, 2))

    def test_event_path_change_is_new_subscription_and_recreation_is_fresh(self):
        """CONDITIONS.md: "Changing the event path is a new subscription and considers retained
        matching intentions on that path." TRIGGER-EXPRESSIONS.md: "removing and recreating a
        subscription creates a fresh subscriber." """
        self.approve(1, '/a'); self.approve(2, '/b')
        def evaluate(): self.cmd('set', path='/enabled', value=1)
        self.rule(event='/a'); evaluate()
        self.assertEqual((self.out(), self.trigger()['lastIntent']), (1, 1))
        self.rule(event='/b'); evaluate()
        self.assertEqual((self.out(), self.trigger()['lastIntent'], self.trigger()['fireCount']), (2, 2, 1))
        self.rule(event='/a'); evaluate()
        self.assertEqual((self.out(), self.trigger()['lastIntent']), (3, 1))
        self.cmd('remove-trigger', id=1); self.rule(event='/a'); evaluate()
        self.assertEqual((self.out(), self.trigger()['lastIntent'], self.trigger()['fireCount']), (4, 1, 1))

    def test_rejected_rule_edit_preserves_watermark(self):
        """GOAL-NOCTURNE-1.0.0.md: "Inputs commit atomically; rejected transactions preserve
        authoritative state." CONDITIONS.md: "previously accepted intentions do not replay." """
        self.rule(); self.approve(1)
        self.rejects({'op': 'trigger', 'id': 1, 'event': '/task/approved', 'target': '/missing',
                      'when': {'path': '/enabled', 'comparison': 'equal', 'value': 1}})
        self.assertEqual((self.out(), self.trigger()['lastIntent']), (1, 1))
        self.approve(2)
        self.assertEqual((self.out(), self.trigger()['lastIntent'], self.trigger()['fireCount']), (2, 2, 2))

    def test_rendering_and_reads_never_advance_the_watermark(self):
        """CONDITIONS.md: "Inspection, rendering and reads do not consume or acknowledge it." and
        "No render, info query, scroll gesture, or unrelated typed character consumes an intention." """
        self.cmd('set', path='/enabled', value=0)
        self.rule(); self.approve(1)
        snapshot = self.s.snapshot()
        for _ in range(3): self.s.render(); self.s.info(); self.s.info_complete()
        self.assertEqual(self.s.snapshot(), snapshot)
        self.assertEqual((self.trigger()['lastIntent'], self.trigger()['intentCandidate']['id']), (0, 1))
        self.cmd('set', path='/enabled', value=1)
        self.assertEqual((self.out(), self.trigger()['lastIntent']), (1, 1))


class InfoReadback(Acceptance):
    def test_new_area_readback_reports_documented_defaults(self):
        """Commands.md area defaults: alpha 0.4, border rounded, fadeMs 500, gapMs 300, height 4,
        hideEmpty false, layout ordered, margin 0, material 2, padding 1, parent 0, speedX 8,
        speedY 1, width 80, x 0, y 0; "Integer 1..65535; identifies one of the 16 area slots." """
        self.cmd('area', id=3)
        area = next(a for a in self.info()['areas'] if a['id'] == 3)
        expected = {'alpha': 0.4, 'border': 1, 'fadeUs': 500_000, 'gapUs': 300_000, 'height': 4,
                    'hideEmpty': False, 'layout': 'ordered', 'margin': 0, 'material': 2, 'padding': 1,
                    'parent': 0, 'speedX': 8, 'speedY': 1, 'width': 80, 'x': 0, 'y': 0}
        self.assertEqual({k: area[k] for k in expected}, expected)  # border 1 is `rounded` in none/rounded/...
        for ident in range(4, 19): self.cmd('area', id=ident)
        self.assertEqual(len(self.info()['areas']), 16)
        self.rejects({'op': 'area', 'id': 19})

    def test_message_readback_exposes_lifecycle_and_policy_fields(self):
        """STATUS-WORKFLOWS.md: "Each host action checks exact message/intention membership,
        authored record fields". NOTIFICATIONS.md: "important | Default false." """
        self.area(layout='queue')
        self.status(1, text='first', durationMs=1000, actions=[self.action()])
        self.status(2, text='second', durationMs=1000, key='k', priority=7)
        record = self.record(2)
        required = {'id', 'text', 'state', 'area', 'priority', 'readyUs', 'startUs', 'durationUs', 'sequence',
                    'key', 'occurrences', 'replacements', 'important', 'acknowledged', 'actions'}
        self.assertLessEqual(required, set(record))
        self.assertEqual({k: record[k] for k in ('text', 'state', 'area', 'priority', 'key', 'occurrences',
                                                 'replacements', 'important', 'acknowledged', 'actions')},
                         {'text': 'second', 'state': 'queued', 'area': 1, 'priority': 7, 'key': 'k',
                          'occurrences': 1, 'replacements': 0, 'important': False, 'acknowledged': False,
                          'actions': []})
        self.assertLessEqual({'id', 'label', 'event', 'value', 'dismiss', 'activated'}, set(self.record(1)['actions'][0]))
        observed = [self.record(1)['state']]
        self.s.advance_to(1_000_000); observed.append(self.record(1)['state'])
        self.cmd('dismiss', id=2); observed.append(self.record(2)['state'])
        self.assertEqual(observed, ['active', 'expired', 'dismissed'])

    def test_retained_regressions_still_pin_their_sentences(self):
        """AGENTS.md: "Retain earlier tests and reference data." The sentences in ALREADY_PINNED
        are enforced by native/tests/test_notifications.py, which this matrix relies on."""
        spec = importlib.util.spec_from_file_location('retained_notifications', ROOT / 'tests/test_notifications.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for sentence, name in ALREADY_PINNED.items():
            self.assertTrue(hasattr(module.NotificationTests, name), (sentence, name))


class WasmMirror(unittest.TestCase):
    CASES = ['documented-intent-shape', 'consumed-action-owns-press', 'content-overflow-reported',
             'scheduled-activation-boundary', 'scheduled-status-chunk-invariance', 'nonpreemptive-priority-queue',
             'history-capacity', 'same-event-watermark-debounce', 'snapshot-round-trip', 'render-and-read-purity',
             'intent-order-and-ack', 'count-coalescing-live-only', 'replace-queued-identity', 'important-guard']

    def test_import_free_wasm_repeats_the_cases_and_matches_native_bytes(self):
        """CURRENT-API-1.0.0.md: "Python, Go and Rust call this core directly; TypeScript runs the
        same core through import-free WASM." The mirror repeats this module's assertions; its
        recorded script must give the same snapshot, frame and metadata through the C ABI."""
        result = subprocess.run([os.environ.get('NODE', 'node'), str(ROOT / 'tests/status_notifications_wasm.mjs')],
                                capture_output=True, text=True, timeout=900)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-4000:])
        report = json.loads(result.stdout)
        self.assertEqual((report['passed'], report['imports'], report['cases']), (True, 0, self.CASES))
        parity, frame = report['parity'], None
        with baseline() as scene:
            for step in parity['script']:
                if 'command' in step: scene.command(step['command'])
                elif step.get('render'): frame = scene.render()
                else: scene.advance_to(step['advanceTo'])
            info = scene.info_complete()
            self.assertEqual(hashlib.sha256(scene.snapshot()).hexdigest(), parity['snapshotSha256'])
        self.assertEqual(hashlib.sha256(frame.bytes).hexdigest(), parity['frameSha256'])
        self.assertEqual(info['render']['contentNeedsReader'], parity['contentNeedsReader'])
        self.assertEqual((info['messages'], info['intents']), (parity['messages'], parity['intents']))


if __name__ == '__main__':
    unittest.main()
