#!/usr/bin/env python3
"""Four complete headless consumers of the actual Nocturne C core.

All domain records are local example data. No provider, service, network request,
terminal, or wall clock is needed. Build the native library before running:

    python3 native/examples/rc4_applications.py chat --output /new/chat --activate

The host explicitly handles a notification intent, commits a local native-state
edit, and acknowledges that intent in one batch. A native snapshot therefore
contains the local result, retained draft, and action-consumption state together.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

SCENARIOS = ('chat', 'form', 'graph', 'dashboard')
DEFAULT_DRAFTS = {
    'chat': 'A message composed locally; the draft remains editable.',
    'form': 'Local example name',
    'graph': 'A retained note about the shared local artifact.',
    'dashboard': 'A retained note about these local sample values.',
}
ACTION_LABELS = {
    'chat': 'Keep local message',
    'form': 'Submit local form',
    'graph': 'Inspect shared artifact',
    'dashboard': 'Record local review',
}
RESULT_LABELS = {
    'chat': 'Latest local message',
    'form': 'Submitted name',
    'graph': 'Local selection',
    'dashboard': 'Recorded review',
}
RESULT_ID = 103
MESSAGE_ID = 1
ACTION_ID = 1


class ApplicationDemo:
    """Own one real native scene and the small synchronous example host policy.

    Args: scenario is chat/form/graph/dashboard; library optionally selects a built
    C library. Returns an owned context manager exposing ``scene: NativeScene``.
    Raises ValueError for invalid local data/native commands, OSError if loading
    the native library fails, and RuntimeError after the scene is closed.
    Example: with ApplicationDemo('chat') as app: app.activateAction(); app.handleIntents()

    Public methods serialize native calls through NativeScene, but this example's
    read/compute/batch host cycle assumes one host event loop. It is not a generic
    multi-threaded or external-service exactly-once transaction coordinator.
    """

    def __init__(self, scenario: str, library: str | Path | None = None):
        if scenario not in SCENARIOS:
            raise ValueError('scenario must be chat, form, graph, or dashboard')
        self.scenario = scenario
        self.event = f'/example/{scenario}/commit'
        self.relationships = ()
        self.scene = NativeScene(seed=2030, library=library)
        try:
            width = 160 if scenario == 'graph' else 120
            self.scene.batch([
                {'op': 'resize', 'width': width, 'height': 48},
                {'op': 'environment', 'stars': 0, 'background': 0x0B121B,
                 'style': 'solid', 'sampling': 'cell'},
                {'op': 'accessibility', 'reducedMotion': True, 'screenReader': False},
                {'op': 'prompt', 'mode': 'grow', 'minRows': 3, 'maxRows': 5,
                 'border': 'rounded', 'padding': 0, 'active': True},
                self._text(100, 2, 1, f'{scenario.title()} | local example data', width - 4),
                self._text(101, 2, 3, 'Actual native cells | Retained draft | Explicit host acknowledgement', width - 4),
                self._text(102, 2, 28, RESULT_LABELS[scenario], width - 4),
                self._text(RESULT_ID, 2, 30, 'No local action committed yet.', width - 4),
                {'op': 'define', 'path': '/example/completed', 'value': 0},
                {'op': 'area', 'id': 1, 'x': 2, 'y': 34, 'width': width - 4,
                 'height': 6, 'padding': 0, 'border': 'rounded', 'layout': 'direct',
                 'gapMs': 0, 'alpha': 0.8},
                {'op': 'status', 'id': MESSAGE_ID, 'area': 1,
                 'text': 'Local action: the host commits it only after handling its retained intent.',
                 'durationMs': 0, 'mode': 'pop', 'important': True,
                 'actions': [{'id': ACTION_ID, 'label': ACTION_LABELS[scenario],
                              'event': self.event, 'value': 1, 'dismiss': False}]},
            ])
            if scenario == 'chat':
                self.scene.batch([
                    self._text(10, 2, 7, 'Conversation'),
                    self._text(11, 2, 9, 'Local notebook: this example retains one latest local message.'),
                    self._text(12, 2, 11, 'Compose in the native draft, activate the action, then let the host handle it.'),
                    self._text(13, 2, 13, 'No remote participant or generated reply is part of this local conversation.'),
                ])
            elif scenario == 'form':
                self.scene.batch([
                    self._text(10, 2, 7, 'Name: edit the retained native draft below'),
                    self._text(11, 2, 10, 'Quantity'),
                    {'op': 'widget', 'id': 20, 'kind': 'progress', 'x': 2, 'y': 12,
                     'width': 50, 'height': 3, 'min': 0, 'max': 100, 'value': 1,
                     'sampling': 'half'},
                    {'op': 'widget', 'id': 21, 'kind': 'checkbox', 'x': 2, 'y': 17,
                     'width': 40, 'height': 1, 'text': 'Include notes', 'selected': False},
                    self._text(22, 2, 20, 'Quantity: 1'),
                    {'op': 'define', 'path': '/example/quantity', 'value': 1,
                     'binding': {'family': 'widget', 'id': 20, 'field': 'value'}},
                    {'op': 'define', 'path': '/example/includeNotes', 'value': 0,
                     'binding': {'family': 'widget', 'id': 21, 'field': 'selected'}},
                    {'op': 'define', 'path': '/example/submittedQuantity', 'value': 0},
                    {'op': 'define', 'path': '/example/submittedNotes', 'value': 0},
                ])
            elif scenario == 'graph':
                artifactHash = hashlib.sha256(b'local example artifact\n').hexdigest()
                self.relationships = ((1, 3, 'produces'), (2, 3, 'reference'))
                self.scene.batch([
                    {'op': 'layout', 'dimensions': 2},
                    {'op': 'camera', 'position': [0, 6, 145], 'yaw': 0, 'pitch': 0, 'fov': 64},
                    {'op': 'node', 'id': 1, 'label': 'Prepare bundle', 'kind': 'local record',
                     'detail': 'A local preparation record.', 'position': [-34, 24, 0],
                     'pinned': True, 'maxColumns': 28, 'showKind': False, 'showDetail': False},
                    {'op': 'node', 'id': 2, 'label': 'Inspect bundle', 'kind': 'local record',
                     'detail': 'An independent local inspection record.', 'position': [34, 24, 0],
                     'pinned': True, 'maxColumns': 28, 'showKind': False, 'showDetail': False},
                    {'op': 'node', 'id': 3, 'label': 'Shared artifact', 'kind': 'local artifact',
                     'detail': 'Two local records refer to this one artifact.', 'sha': artifactHash,
                     'position': [0, -18, 0], 'pinned': True, 'maxColumns': 28,
                     'shaPrefix': 12, 'showKind': False, 'showDetail': False},
                    *[{'op': 'edge', 'from': start, 'to': end, 'kind': kind}
                      for start, end, kind in self.relationships],
                ])
            else:
                self.scene.batch([
                    self._text(10, 2, 7, 'Local samples'),
                    self._text(11, 66, 7, 'Completion', 48),
                    {'op': 'widget', 'id': 20, 'kind': 'bars', 'x': 2, 'y': 10,
                     'width': 54, 'height': 12, 'min': 0, 'max': 100,
                     'data': [15, 25, 40, 55, 70], 'sampling': 'braille'},
                    {'op': 'widget', 'id': 21, 'kind': 'donut', 'x': 68, 'y': 10,
                     'width': 28, 'height': 12, 'min': 0, 'max': 100, 'value': 70,
                     'sampling': 'braille', 'innerRadius': 0.6},
                    {'op': 'define', 'path': '/example/completion', 'value': 70,
                     'binding': {'family': 'widget', 'id': 21, 'field': 'value'}},
                    self._text(22, 2, 24, 'Local samples: 15, 25, 40, 55, 70'),
                ])
            self.setDraft(DEFAULT_DRAFTS[scenario])
            self.scene.advance_to(900000)
            self.scene.command({'op': 'pause', 'paused': True})
        except BaseException:
            self.scene.close()
            raise

    @staticmethod
    def _text(identity: int, x: int, y: int, text: str, width: int = 116) -> dict:
        """Return a real native text-widget transaction with scalar-cell framing."""
        return {'op': 'widget', 'id': identity, 'kind': 'text', 'x': x, 'y': y,
                'width': width, 'height': 1, 'text': text, 'alpha': 0}

    def setDraft(self, text: str) -> None:
        """Replace the native draft immediately, without decorative input weather.

        Text is a Unicode string of at most 2048 scalars. Native validation rejects
        an invalid draft atomically. The example never clears it after an action.
        """
        if not isinstance(text, str):
            raise ValueError('draft must be a Unicode string')
        self.scene.command({'op': 'draft', 'text': text, 'emitWeather': False})

    def setForm(self, *, quantity: int, includeNotes: bool) -> None:
        """Validate and atomically edit the local form's numeric/boolean bindings.

        Quantity is an integer in [1,100], includeNotes is bool. Raises ValueError
        before mutation on a wrong scenario or invalid field; returns None.
        """
        if self.scenario != 'form':
            raise ValueError('setForm belongs to the form scenario')
        if type(quantity) is not int or not 1 <= quantity <= 100 or type(includeNotes) is not bool:
            raise ValueError('quantity must be an integer 1..100 and includeNotes must be bool')
        self.scene.batch([
            {'op': 'set', 'path': '/example/quantity', 'value': quantity},
            {'op': 'set', 'path': '/example/includeNotes', 'value': int(includeNotes)},
            {'op': 'widget', 'id': 22, 'text': f'Quantity: {quantity}'},
        ])

    def updateDashboard(self, samples: list[int | float]) -> None:
        """Commit 1..16 local finite samples in [0,100] to real plot widgets.

        The final sample supplies completion. The native widget data capacity is
        larger. Full numeric text is retained in metadata even if a supplied
        decimal representation exceeds the default row. Invalid data/scenario
        raises ValueError without changing the native snapshot.
        """
        if self.scenario != 'dashboard':
            raise ValueError('updateDashboard belongs to the dashboard scenario')
        if (not isinstance(samples, list) or not 1 <= len(samples) <= 16 or
                any(type(x) not in (int, float) or not 0 <= x <= 100 or not math.isfinite(x) for x in samples)):
            raise ValueError('samples must contain 1..16 finite numbers in 0..100')
        self.scene.batch([
            {'op': 'widget', 'id': 20, 'data': samples},
            {'op': 'set', 'path': '/example/completion', 'value': samples[-1]},
            {'op': 'widget', 'id': 22, 'text': 'Local samples: ' + ', '.join(f'{x:g}' for x in samples)},
        ])

    def activateAction(self, *, pointer: bool = False) -> None:
        """Activate the native notification, leaving its intent for the host.

        The optional pointer path finds the action's actual current native cell
        and submits down/up events. It raises RuntimeError if that action is not
        visible. Calling this method never commits the example's local result.
        """
        if not pointer:
            self.scene.command({'op': 'notification-action', 'id': MESSAGE_ID, 'actionId': ACTION_ID})
            return
        frame = self.scene.render()
        # Notification hit IDs encode message identity and zero-based action slot.
        hitId = 0x63000000 | (MESSAGE_ID << 2)
        positions = [i for i, cell in enumerate(frame.words()) if cell[3] == hitId]
        if not positions:
            raise RuntimeError('the local notification action has no visible native hit cell')
        index = positions[len(positions) // 2]
        for phase in ('down', 'up'):
            self.scene.command({'op': 'pointer', 'phase': phase,
                                'x': index % frame.width, 'y': index // frame.width})

    def handleIntents(self) -> int:
        """Handle only this example's current message/action/version; return count.

        Commit the native local result and explicit ack-intent/ack-status in one
        native batch. Form validation failure raises ValueError and preserves the
        pending intent for correction. Unowned/stale intents remain queued. A real
        external operation would require a host-owned durable idempotency policy.
        """
        handled = 0
        for intent in self.scene.info()['intents']:
            info = self.scene.info()
            message = next((m for m in info['messages'] if m['id'] == MESSAGE_ID), None)
            if (not message or intent['event'] != self.event or intent['messageId'] != MESSAGE_ID or
                    intent['actionId'] != ACTION_ID or intent['messageSequence'] != message['sequence']):
                continue
            text = info['prompt']['text']
            values = info['values']
            edits = []
            if self.scenario == 'form':
                if not text.strip():
                    raise ValueError('the local form requires a nonblank name; correct the retained draft and retry')
                edits.extend([
                    {'op': 'set', 'path': '/example/submittedQuantity', 'value': values['/example/quantity']},
                    {'op': 'set', 'path': '/example/submittedNotes', 'value': values['/example/includeNotes']},
                ])
            elif self.scenario == 'graph':
                edits.append({'op': 'select', 'id': 3, 'durationMs': 0})
                text = 'Selected Shared artifact; its full hash and detail remain native metadata.'
            elif self.scenario == 'dashboard':
                text = f'Local review recorded at completion {values["/example/completion"]:g}%. Draft retained.'
            edits.extend([
                {'op': 'widget', 'id': RESULT_ID, 'text': text},
                {'op': 'set', 'path': '/example/completed', 'value': values['/example/completed'] + 1},
                {'op': 'ack-intent', 'id': intent['id']},
                {'op': 'ack-status', 'id': MESSAGE_ID},
            ])
            self.scene.batch(edits)
            handled += 1
        return handled

    def close(self) -> None:
        """Release the owned native context; idempotent."""
        self.scene.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def exportApplication(output: Path, scenario: str, *, draft: str | None = None,
                      activate: bool = False, library: str | Path | None = None) -> dict:
    """Execute a complete guide and publish owned local artifacts to a new directory.

    Args: new output path, scenario, optional draft/native library, and whether to
    activate and explicitly handle the example action. Returns the JSON manifest.
    Invalid native/local input raises ValueError before an output is created. An
    existing output raises FileExistsError. Filesystem errors propagate; an owned
    staging directory is removed on failure. The caller owns its output parent;
    concurrent writers to the same destination are outside this example's scope.
    """
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    with ApplicationDemo(scenario, library=library) as app:
        if draft is not None:
            app.setDraft(draft)
        if activate:
            app.activateAction()
            app.handleIntents()
        snapshot = app.scene.snapshot()
        frame = app.scene.render()
        info = app.scene.info()
        if app.scene.snapshot() != snapshot:
            raise RuntimeError('render or info mutated authoritative application state')
        cells = frame.words()
        text = '\n'.join(''.join(chr(cell[0]) for cell in cells[y * frame.width:(y + 1) * frame.width])
                         for y in range(frame.height)) + '\n'
        report = {
            'scenario': scenario, 'dataOrigin': 'local example data', 'runtime': 'Python -> native C ABI',
            'width': frame.width, 'height': frame.height, 'renderPure': True,
            'frameSha256': hashlib.sha256(frame.bytes).hexdigest(),
            'snapshotSha256': hashlib.sha256(snapshot).hexdigest(),
            'hostHandledActions': info['values']['/example/completed'],
            'pendingIntentIds': [i['id'] for i in info['intents']],
            'graphRelationships': app.relationships,
        }
        # JSON arrays give the returned manifest the same shape as the on-disk one.
        report = json.loads(json.dumps(report))
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='nocturne-local-example-', dir=output.parent))
        try:
            (staging / 'application.cells').write_bytes(frame.bytes)
            (staging / 'application.snapshot').write_bytes(snapshot)
            (staging / 'application-info.json').write_text(json.dumps(info, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            (staging / 'application.txt').write_text(text, encoding='utf-8')
            (staging / 'APPLICATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            if output.exists():
                raise FileExistsError(output)
            staging.rename(output)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return report


def main() -> None:
    """Run the selected local example and print its actual export manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', choices=SCENARIOS)
    parser.add_argument('--output', type=Path, required=True, help='new output directory')
    parser.add_argument('--draft', help='replace the retained local draft')
    parser.add_argument('--activate', action='store_true', help='activate and explicitly handle one local action')
    parser.add_argument('--library', type=Path, help='optional built native C library')
    args = parser.parse_args()
    print(json.dumps(exportApplication(args.output, args.scenario, draft=args.draft,
                                       activate=args.activate, library=args.library), indent=2))


if __name__ == '__main__':
    main()
