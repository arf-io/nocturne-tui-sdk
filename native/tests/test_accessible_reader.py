"""Read the real C cell plane at finite viewport bounds; no synthetic adapters."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene


class AccessibleReaderTests(unittest.TestCase):
    def setUp(self):
        self.scene = NativeScene(2030)
        self.addCleanup(self.scene.close)
        self.scene.command({'op': 'environment', 'stars': 0, 'style': 'solid'})
        self.scene.command({'op': 'pause', 'paused': True})

    def command(self, operation, **fields):
        return self.scene.command({'op': operation, **fields})

    def window(self, identifier=1):
        return next(w for w in self.scene.info()['windows'] if w['id'] == identifier)

    def readerText(self, identifier=1):
        frame = self.scene.render()
        words = frame.words()
        owner = 0x20000000 | identifier
        return '\n'.join(''.join(chr(g) if ident == owner else ' '
                                 for g, _, _, ident in words[y * frame.width:(y + 1) * frame.width])
                         for y in range(frame.height))

    def test_reader_remains_visible_in_all_prompt_modes_and_small_viewports(self):
        self.command('window', id=1, title='Critical', text='Approval required',
                     padding=8, position=[0, 0, 16000], alpha=0)
        self.command('draft', text='P' * 400, emitWeather=False)
        for width, height in [(20, 10), (40, 16), (80, 24)]:
            self.command('resize', width=width, height=height)
            for mode in ['marquee', 'grow', 'vim-inline', 'vim-full']:
                with self.subTest(width=width, height=height, mode=mode):
                    self.command('prompt', mode=mode, minRows=60, maxRows=60)
                    self.command('window-action', id=1, action='read')
                    before = self.scene.snapshot()
                    text = self.readerText()
                    self.assertIn('Critical', text)
                    self.assertIn('Approval', text)
                    self.assertNotIn('PPP', text)
                    self.assertEqual(self.scene.snapshot(), before)
                    self.assertEqual(self.window()['text'], 'Approval required')

    def test_f6_reaches_all_twelve_closed_and_offscreen_windows(self):
        self.command('resize', width=20, height=10)
        self.command('prompt', mode='vim-full')
        for identifier in range(1, 13):
            self.command('window', id=identifier, title=f'Window {identifier:02}',
                         text=f'Body {identifier:02}', position=[0, 0, 16000])
            self.command('window-action', id=identifier, action='close', durationMs=0)
        for identifier in range(1, 13):
            self.command('key', key='F6')
            self.assertIn(f'Body {identifier:02}', self.readerText(identifier))
        self.assertEqual(len(self.scene.info()['windows']), 12)

    def test_reader_paging_precedes_background_graph_selection(self):
        self.command('resize', width=40, height=16)
        self.command('node', id=1, label='Background selection', detail='graph row\n' * 40)
        self.command('select', id=1)
        self.command('window', id=1, title='Document', text='document row\n' * 90)
        self.command('window-action', id=1, action='read')
        self.command('key', key='PageDown')
        self.assertGreater(self.window()['scrollRow'], 0)
        self.assertEqual(self.scene.info()['inspectorScroll'], 0)
        self.assertEqual(self.scene.info()['selection'], 1)

    def test_tiny_reader_page_and_scroll_bounds_include_the_title(self):
        self.command('resize', width=20, height=10)
        self.command('window', id=1, title='Title\n' * 16, text='Row\n' * 30)
        self.command('window-action', id=1, action='read')
        self.command('window-action', id=1, action='page-next')
        self.assertGreater(self.window()['scrollRow'], 0)
        self.command('window-action', id=1, action='scroll', rows=2048)
        # 17 title rows, one separator, 31 body rows; six visible content rows.
        self.assertEqual(self.window()['scrollRow'], 43)
        self.assertIn('Row', self.readerText())
        self.command('key', key='PageUp')
        self.assertEqual(self.window()['scrollRow'], 37)
        self.command('window-action', id=1, action='scroll', rows=-2048)
        self.assertEqual(self.window()['scrollRow'], 0)
        self.assertIn('Title', self.readerText())

    def test_escape_exits_reader_before_changing_prompt_or_graph(self):
        self.command('node', id=1, label='Still selected')
        self.command('select', id=1)
        self.command('draft', text='keep source', emitWeather=False)
        self.command('prompt', mode='vim-full')
        self.command('window', id=1, title='Reader', text='retained document')
        self.command('window-action', id=1, action='read')
        self.command('key', key='Escape')
        self.assertFalse(self.window()['reader'])
        self.assertEqual(self.scene.info()['prompt']['text'], 'keep source')
        self.assertEqual(self.scene.info()['selection'], 1)
        self.command('key', key='F6')
        self.assertIn('retained document', self.readerText())

    def test_reader_pointer_wheel_and_drag_cannot_move_hidden_geometry(self):
        self.command('resize', width=20, height=10)
        self.command('prompt', mode='vim-full')
        self.command('window', id=1, title='Reader', text='row\n' * 60)
        self.command('window-action', id=1, action='read')
        self.scene.render()
        before = self.scene.info()
        self.command('wheel', delta=-1, x=3, y=4)
        self.assertEqual(self.window()['scrollRow'], 3)
        self.assertEqual(self.scene.info()['camera'], before['camera'])
        self.command('pointer', phase='down', x=3, y=4)
        self.command('pointer', phase='move', x=10, y=6)
        self.command('pointer', phase='up', x=10, y=6)
        self.assertEqual(self.window()['position'], before['windows'][0]['position'])
        self.assertEqual(self.scene.info()['prompt']['caret'], before['prompt']['caret'])

    def test_modal_retains_precedence_and_complete_source(self):
        self.command('window', id=1, title='Reader', text='held')
        self.command('window-action', id=1, action='read')
        self.command('key', key='F1')
        before = self.scene.snapshot()
        for key in ['F6', 'PageUp', 'PageDown']:
            self.command('key', key=key)
        self.assertEqual(self.scene.snapshot(), before)
        self.command('key', key='Escape')
        self.assertTrue(self.window()['reader'])
        self.assertIn('held', self.readerText())

    def test_reader_keyboard_focus_does_not_edit_the_obscured_prompt(self):
        self.command('resize', width=20, height=10)
        self.command('draft', text='accepted prompt', emitWeather=False)
        self.command('window', id=1, title='Reader', text='row\n' * 50)
        self.command('window-action', id=1, action='read')
        prompt = self.scene.info()['prompt']
        for key in ['A', 'Enter', 'Backspace', 'Delete']:
            self.command('key', key=key)
        self.command('key', key='z', ctrl=True)
        self.assertEqual(self.scene.info()['prompt'], prompt)
        self.command('key', key='ArrowDown')
        self.assertEqual(self.window()['scrollRow'], 1)
        self.command('key', key='End')
        self.assertGreater(self.window()['scrollRow'], 1)
        self.command('key', key='Home')
        self.assertEqual(self.window()['scrollRow'], 0)
        self.assertEqual(self.scene.info()['prompt'], prompt)

    def test_minimum_viewport_help_keeps_exit_and_recovery_keys_readable(self):
        self.command('resize', width=20, height=10)
        self.command('key', key='F1')
        before = self.scene.snapshot()
        frame = self.scene.render()
        words = frame.words()
        text = '\n'.join(''.join(chr(g) if ident == 0x7fffffff else ' '
                                 for g, _, _, ident in words[y * frame.width:(y + 1) * frame.width])
                         for y in range(frame.height))
        for key in ['Esc', 'F6', 'PgUp']:
            self.assertIn(key, text)
        self.assertEqual(self.scene.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
