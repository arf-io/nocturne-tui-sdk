"""Execute all four application guides against the actual owned C scene.

The records are deliberately local example data. These tests exercise native cells,
snapshots and intents; no provider, service or substitute scene participates.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples'))
from rc4_applications import ApplicationDemo, exportApplication

SCENARIOS = ('chat', 'form', 'graph', 'dashboard')
LABELS = {
    'chat': ('Chat | local example data', 'Conversation', 'Latest local message'),
    'form': ('Form | local example data', 'Quantity', 'Include notes', 'Submitted name'),
    'graph': ('Graph | local example data', 'Prepare bundle', 'Inspect bundle', 'Shared artifact'),
    'dashboard': ('Dashboard | local example data', 'Local samples', 'Completion', 'Recorded review'),
}
LIBRARY = os.environ.get('NOCTURNE_TEST_LIBRARY')


def screenText(frame):
    """Decode the SDK's scalar-per-cell profile, without terminal-width inference."""
    cells = frame.words()
    return '\n'.join(''.join(chr(c[0]) for c in cells[y * frame.width:(y + 1) * frame.width])
                     for y in range(frame.height))


class ApplicationGuideTests(unittest.TestCase):
    def testEveryScenarioRendersFullLabelsAndKeepsDraftWhileHeld(self):
        draft = 'Aé界e\u0301Z — retained local draft'
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario), ApplicationDemo(scenario, library=LIBRARY) as app:
                app.setDraft(draft)
                before = app.scene.snapshot()
                frame = app.scene.render()
                for label in LABELS[scenario]:
                    self.assertIn(label, screenText(frame))
                self.assertEqual(app.scene.info()['prompt']['text'], draft)
                self.assertEqual(app.scene.snapshot(), before)
                self.assertEqual(app.scene.render().bytes, frame.bytes)
                self.assertEqual(app.scene.info()['intents'], [])

    def testNativeActionRetainsIntentUntilHostCommitsAndAcknowledges(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario), ApplicationDemo(scenario, library=LIBRARY) as app:
                app.setDraft('A local submission')
                app.activateAction()
                info = app.scene.info()
                self.assertEqual(len(info['intents']), 1)
                self.assertEqual(info['values']['/example/completed'], 0)
                self.assertFalse(info['messages'][0]['acknowledged'])
                before = app.scene.snapshot()
                app.scene.render()
                self.assertEqual(app.scene.snapshot(), before)
                self.assertEqual(app.handleIntents(), 1)
                info = app.scene.info()
                self.assertEqual(info['intents'], [])
                self.assertEqual(info['values']['/example/completed'], 1)
                self.assertTrue(info['messages'][0]['acknowledged'])
                self.assertEqual(info['prompt']['text'], 'A local submission')
                once = app.scene.snapshot()
                app.activateAction()
                self.assertEqual(app.handleIntents(), 0)
                self.assertEqual(app.scene.snapshot(), once)

    def testActionCanBeActivatedFromItsActualNativeCell(self):
        with ApplicationDemo('chat', library=LIBRARY) as app:
            before = app.scene.info()['fieldCount']
            app.activateAction(pointer=True)
            intent = app.scene.info()['intents'][0]
            self.assertEqual(intent['event'], '/example/chat/commit')
            self.assertEqual(app.scene.info()['fieldCount'], before)
            self.assertEqual(app.scene.info()['values']['/example/completed'], 0)
            self.assertEqual(app.handleIntents(), 1)

    def testUnownedIntentIsRetainedForItsHost(self):
        with ApplicationDemo('chat', library=LIBRARY) as app:
            app.scene.command({'op': 'status', 'id': 2, 'area': 0, 'text': 'Other local owner',
                               'durationMs': 0, 'actions': [{'id': 1, 'label': 'Other',
                                                           'event': '/example/other'}]})
            app.scene.command({'op': 'notification-action', 'id': 2, 'actionId': 1})
            foreign = app.scene.info()['intents'][0]
            app.activateAction()
            self.assertEqual(app.handleIntents(), 1)
            self.assertEqual(app.scene.info()['intents'], [foreign])

    def testChatCommitsCompleteLocalTextWithoutClearingItsDraft(self):
        text = 'Aé界e\u0301Z\nSecond local line'
        with ApplicationDemo('chat', library=LIBRARY) as app:
            app.setDraft(text)
            app.activateAction()
            app.handleIntents()
            info = app.scene.info()
            self.assertEqual(info['prompt']['text'], text)
            self.assertIn(text, [w['text'] for w in info['widgets']])

    def testFormUsesRealBindingsAndRejectsInvalidEditsAtomically(self):
        with ApplicationDemo('form', library=LIBRARY) as app:
            app.setForm(quantity=7, includeNotes=True)
            info = app.scene.info()
            self.assertEqual(info['values']['/example/quantity'], 7)
            self.assertEqual(info['values']['/example/includeNotes'], 1)
            self.assertIn('[x] Include notes', screenText(app.scene.render()))
            for quantity, notes in ((0, True), (101, True), (1.5, True), (True, True), (2, 1)):
                before = app.scene.snapshot()
                with self.subTest(quantity=quantity, notes=notes), self.assertRaises(ValueError):
                    app.setForm(quantity=quantity, includeNotes=notes)
                self.assertEqual(app.scene.snapshot(), before)
            app.setDraft('Example name')
            app.activateAction()
            app.handleIntents()
            info = app.scene.info()
            self.assertEqual(info['values']['/example/submittedQuantity'], 7)
            self.assertEqual(info['values']['/example/submittedNotes'], 1)
            self.assertIn('Example name', [w['text'] for w in info['widgets']])

    def testFormValidationPreservesPendingActionForCorrection(self):
        with ApplicationDemo('form', library=LIBRARY) as app:
            app.setDraft('  \n ')
            app.activateAction()
            before = app.scene.snapshot()
            with self.assertRaises(ValueError):
                app.handleIntents()
            self.assertEqual(app.scene.snapshot(), before)
            app.setDraft('Corrected local name')
            self.assertEqual(app.handleIntents(), 1)
            self.assertEqual(app.scene.info()['values']['/example/completed'], 1)

    def testGraphKeepsOneSharedRecordAndFullHashAfterSelection(self):
        with ApplicationDemo('graph', library=LIBRARY) as app:
            before = app.scene.info()['nodes']
            shared = next(n for n in before if n['label'] == 'Shared artifact')
            self.assertEqual(len([n for n in before if n['id'] == shared['id']]), 1)
            self.assertEqual(shared['sha'], hashlib.sha256(b'local example artifact\n').hexdigest())
            self.assertEqual(len(shared['sha']), 64)
            self.assertIn('Two local records refer to this one artifact.', shared['detail'])
            app.activateAction()
            app.handleIntents()
            info = app.scene.info()
            self.assertEqual(info['selection'], shared['id'])
            self.assertEqual([(n['id'], n['label'], n['sha'], n['detail']) for n in info['nodes']],
                             [(n['id'], n['label'], n['sha'], n['detail']) for n in before])
            self.assertEqual(app.relationships, ((1, 3, 'produces'), (2, 3, 'reference')))

    def testDashboardUpdatesRealPlotsAndRejectsNonfiniteSamples(self):
        with ApplicationDemo('dashboard', library=LIBRARY) as app:
            before = app.scene.render().bytes
            app.updateDashboard([5, 10, 20, 35])
            info = app.scene.info()
            self.assertEqual(info['values']['/example/completion'], 35)
            self.assertNotEqual(app.scene.render().bytes, before)
            self.assertIn('Local samples: 5, 10, 20, 35', screenText(app.scene.render()))
            for samples in ([], [float('nan')], [float('inf')], [-1], [101], [True], list(range(129))):
                snapshot = app.scene.snapshot()
                with self.subTest(samples=samples), self.assertRaises(ValueError):
                    app.updateDashboard(samples)
                self.assertEqual(app.scene.snapshot(), snapshot)

    def testSnapshotRestoresDraftPendingActionAndCompletedLocalState(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario), ApplicationDemo(scenario, library=LIBRARY) as app:
                app.setDraft('Snapshot retained é界e\u0301')
                app.activateAction()
                pending = app.scene.snapshot()
                pendingCells = app.scene.render().bytes
                app.handleIntents()
                completed = app.scene.snapshot()
                completedCells = app.scene.render().bytes
                app.scene.command({'op': 'reset'})
                app.scene.restore(pending)
                self.assertEqual(app.scene.snapshot(), pending)
                self.assertEqual(app.scene.render().bytes, pendingCells)
                self.assertEqual(app.handleIntents(), 1)
                self.assertEqual(app.scene.snapshot(), completed)
                self.assertEqual(app.scene.render().bytes, completedCells)
                self.assertEqual(app.scene.info()['prompt']['text'], 'Snapshot retained é界e\u0301')

    def testExportsAreActualOwnedCellsMetadataAndRestorableSnapshots(self):
        with tempfile.TemporaryDirectory(prefix='nocturne-application-guide-') as directory:
            for scenario in SCENARIOS:
                output = Path(directory) / scenario
                report = exportApplication(output, scenario, draft='Exported local input',
                                           activate=True, library=LIBRARY)
                cells = (output / 'application.cells').read_bytes()
                snapshot = (output / 'application.snapshot').read_bytes()
                info = json.loads((output / 'application-info.json').read_text())
                self.assertEqual(len(cells), report['width'] * report['height'] * 16)
                self.assertEqual(report['frameSha256'], hashlib.sha256(cells).hexdigest())
                self.assertEqual(report['snapshotSha256'], hashlib.sha256(snapshot).hexdigest())
                self.assertTrue(report['renderPure'])
                self.assertEqual(report['dataOrigin'], 'local example data')
                self.assertEqual(info['prompt']['text'], 'Exported local input')
                self.assertEqual(info['values']['/example/completed'], 1)
                with ApplicationDemo(scenario, library=LIBRARY) as restored:
                    restored.scene.restore(snapshot)
                    self.assertEqual(restored.scene.render().bytes, cells)
                before = {p.name: p.read_bytes() for p in output.iterdir()}
                with self.assertRaises(FileExistsError):
                    exportApplication(output, scenario, library=LIBRARY)
                self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)

    def testCliExecutesRealNativeExporter(self):
        with tempfile.TemporaryDirectory(prefix='nocturne-application-cli-') as directory:
            output = Path(directory) / 'chat'
            command = [sys.executable, str(ROOT / 'examples/rc4_applications.py'), 'chat',
                       '--output', str(output), '--draft', 'Local CLI input', '--activate']
            if LIBRARY:
                command += ['--library', LIBRARY]
            run = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(report, json.loads((output / 'APPLICATION.json').read_text()))
            self.assertIn('Local CLI input', (output / 'application.txt').read_text())

    def testInvalidScenarioAndDraftCreateNoOutput(self):
        with tempfile.TemporaryDirectory(prefix='nocturne-application-invalid-') as directory:
            for index, scenario, draft in ((0, 'unknown', 'x'), (1, 'chat', 'x' * 2049),
                                            (2, 'form', '  ')):
                output = Path(directory) / str(index)
                with self.assertRaises(ValueError):
                    exportApplication(output, scenario, draft=draft, activate=True, library=LIBRARY)
                self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
