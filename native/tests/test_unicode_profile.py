"""Lossless scalar source/metadata invariants through the actual native ABI."""
from pathlib import Path
import sys
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


class UnicodeProfileTests(unittest.TestCase):
    def setUp(self):
        self.scene = NativeScene(2030)
        self.addCleanup(self.scene.close)
        self.scene.command({'op': 'environment', 'stars': 0, 'style': 'solid'})
        self.scene.command({'op': 'prompt', 'active': False})

    def test_scalar_cells_keep_combining_wide_emoji_and_bidi_source_order(self):
        samples = ['Ae\u0301Z', 'A界Z', 'A🙂Z', 'A👩\u200d🔧Z',
                   'A🇺🇸Z', 'אבג', 'مرحبا', 'A\u202eBC\u202cZ',
                   'A\u2067B\u2069Z', 'A\ufe0fZ', 'A\u0085Z']
        for text in samples:
            with self.subTest(text=repr(text)):
                self.scene.command({'op': 'draft', 'text': text, 'emitWeather': False})
                self.scene.command({'op': 'widget', 'id': 1, 'kind': 'text',
                                    'text': text, 'x': 2, 'y': 3, 'width': 40,
                                    'height': 1, 'padding': 0, 'border': 'none'})
                before = self.scene.snapshot()
                frame = self.scene.render()
                cells = frame.words()[3 * frame.width + 2:3 * frame.width + 2 + len(text)]
                self.assertEqual([cell[0] for cell in cells], list(map(ord, text)))
                self.assertEqual([cell[3] for cell in cells], [0x30000001] * len(text))
                self.assertEqual(self.scene.info()['prompt']['text'], text)
                self.assertEqual(self.scene.info()['widgets'][0]['text'], text)
                self.assertEqual(before, self.scene.snapshot())
                self.scene.restore(before)
                self.assertEqual(self.scene.info()['prompt']['text'], text)

    def test_illformed_unicode_and_nonlayout_c0_reject_atomically(self):
        cases = [b'"\\ud800"', b'"\\udfff"', b'"\xed\xa0\x80"',
                 b'"\xc0\xaf"', b'"\xf4\x90\x80\x80"', b'"\xe2\x82"',
                 b'"\\u0000"', b'"\\u001b"', b'"\\b"']
        self.scene.command({'op': 'draft', 'text': 'accepted e\u0301界🙂', 'emitWeather': False})
        before = self.scene.snapshot()
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.scene.command_raw(b'{"op":"draft","text":' + value + b'}')
                self.assertEqual(before, self.scene.snapshot())

    def test_document_separators_preserve_exact_source_and_restore(self):
        text='A\rB\r\nC\vD\fE\u0085F\u2028G\u2029H'
        self.scene.command({'op':'draft','text':text,'emitWeather':False})
        saved=self.scene.snapshot();self.assertEqual(self.scene.info()['prompt']['text'],text)
        self.scene.render();self.assertEqual(self.scene.snapshot(),saved)
        self.scene.restore(saved);self.assertEqual(self.scene.info()['prompt']['text'],text)

    def test_newline_and_tab_are_explicit_scalar_layout(self):
        self.scene.command({'op': 'widget', 'id': 1, 'kind': 'text', 'text': 'A\tB\nC',
                            'x': 2, 'y': 3, 'width': 8, 'height': 3, 'padding': 0, 'border': 'none'})
        frame = self.scene.render()
        cells = frame.words()
        self.assertEqual([c[0] for c in cells[3 * frame.width + 2:3 * frame.width + 5]], [65, 32, 66])
        self.assertEqual(cells[4 * frame.width + 2][0], 67)
        self.assertEqual(self.scene.info()['widgets'][0]['text'], 'A\tB\nC')

    def test_scalar_cursor_does_not_claim_grapheme_editing(self):
        self.scene.command({'op': 'draft', 'text': 'e\u0301🙂', 'caret': 2, 'emitWeather': False})
        self.scene.command({'op': 'key', 'key': 'Backspace'})
        self.assertEqual(self.scene.info()['prompt']['text'], 'e🙂')
        self.assertEqual(self.scene.info()['prompt']['caret'], 1)
        self.scene.command({'op': 'key', 'key': 'z', 'ctrl': True})
        self.assertEqual(self.scene.info()['prompt']['text'], 'e\u0301🙂')

    def test_hidden_transition_text_and_editor_focus_are_inspectable(self):
        text = 'Hidden "approval" \\ \n e\u0301 界 🙂 אבג'
        self.scene.command({'op': 'text', 'id': 7, 'text': text, 'phase': 'hide', 'local': False})
        self.scene.command({'op': 'window', 'id': 9, 'title': 'Retained', 'text': 'body'})
        self.scene.command({'op': 'prompt', 'mode': 'vim-full'})
        self.scene.command({'op': 'key', 'key': 'i'})
        before = self.scene.snapshot()
        info = self.scene.info()
        self.assertEqual(info['textProfile'], 'nr-cell-scalar-v1')
        self.assertEqual([{key:row[key] for key in ['id','text','local','phase']} for row in info['textRuns']], [{'id': 7, 'text': text, 'local': False, 'phase': 'hide'}])
        self.assertEqual(info['textRuns'][0]['seed'],2030)
        self.assertEqual(info['textRuns'][0]['trailCount'],0)
        self.assertEqual(info['textRuns'][0]['trails'],[])
        self.assertEqual(info['selectedWindow'], 9)
        self.assertEqual(info['prompt']['vimMode'], 'insert')
        self.assertEqual(before, self.scene.snapshot())

    def test_all_text_run_slots_expose_full_capacity_without_truncation(self):
        for text in ['🙂"\\\n' * 512, '🙂' * 2048, '"\\\n\t' * 512]:
            with self.subTest(first=repr(text[:4])):
                for identifier in range(1, 25):
                    self.scene.command({'op': 'text', 'id': identifier, 'text': text, 'phase': 'hide'})
                before = self.scene.snapshot()
                records = self.scene.info()['textRuns']
                self.assertEqual(len(records), 24)
                self.assertTrue(all(record['text'] == text for record in records))
                self.assertEqual(before, self.scene.snapshot())

    def test_all_64_graph_nodes_preserve_maximum_source_fields_and_escaping(self):
        label, detail = '🙂"\\\n' * 64, '🙂"\\\t' * 128
        for identifier in range(1, 65):
            self.scene.command({'op': 'node', 'id': identifier, 'label': label,
                                'detail': detail, 'kind': '"' * 47,
                                'status': '\\' * 127, 'sha': '"' * 128})
        before = self.scene.snapshot()
        records = self.scene.info()['nodes']
        self.assertEqual(len(records), 64)
        for record in records:
            self.assertEqual(record['label'], label)
            self.assertEqual(record['detail'], detail)
            self.assertEqual(record['kind'], '"' * 47)
            self.assertEqual(record['status'], '\\' * 127)
            self.assertEqual(record['sha'], '"' * 128)
        self.assertEqual(before, self.scene.snapshot())

    def test_all_48_notification_slots_page_complete_metadata_without_mutation(self):
        text, label = '🙂"\\\n' * 512, '🙂"\\\t' * 16
        for identifier in range(1, 49):
            self.scene.command({'op': 'status', 'id': identifier, 'text': text,
                                'durationMs': 0, 'actions': [
                                    {'id': action, 'label': label, 'event': '/capacity/action'}
                                    for action in range(1, 5)]})
        before = self.scene.snapshot()
        # Complete metadata must retain every source record beyond the old limit.
        info=self.scene.info();self.assertNotIn('error',info);self.assertGreater(len(json.dumps(info,ensure_ascii=False).encode()),65536)
        self.assertEqual([row['id'] for row in info['messages']],list(range(1,49)))
        for row in info['messages']:
            self.assertEqual(row['text'],text)
            self.assertEqual([(a['id'],a['label'],a['event']) for a in row['actions']],[(a,label,'/capacity/action') for a in range(1,5)])
        self.scene.render();self.assertEqual(self.scene.snapshot(),before)
        self.assertEqual(before, self.scene.snapshot())
        self.scene.restore(before)
        self.assertEqual(before, self.scene.snapshot());self.assertEqual(self.scene.info()['messages'],info['messages'])
        self.scene.command({'op': 'clear', 'scope': 'status'})
        self.assertEqual(self.scene.info()['messages'], [])

    def test_joint_metadata_pages_complete_source_without_mutation(self):
        text = '🙂' * 2048
        for identifier in range(1, 25):
            self.scene.command({'op': 'text', 'id': identifier, 'text': text})
        for identifier in range(1, 13):
            self.scene.command({'op': 'window', 'id': identifier, 'title': 'large', 'text': text})
        before = self.scene.snapshot()
        info=self.scene.info();self.assertNotIn('error',info);self.assertGreater(len(json.dumps(info,ensure_ascii=False).encode()),65536)
        self.assertEqual([row['id'] for row in info['textRuns']],list(range(1,25)))
        self.assertEqual([row['id'] for row in info['windows']],list(range(1,13)))
        for row in info['textRuns']+info['windows']:self.assertEqual(row['text'],text)
        self.scene.render();self.assertEqual(self.scene.snapshot(),before)
        self.assertEqual(before, self.scene.snapshot())
        self.scene.restore(before)
        self.assertEqual(before, self.scene.snapshot());self.assertEqual(self.scene.info(),info)


if __name__ == '__main__':
    unittest.main()
