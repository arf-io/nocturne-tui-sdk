"""Real native prompt consumer oracles; no substitute scene or Unicode resolver."""
import ctypes as C
import struct
import unittest
import zlib
from nocturne_native import NativeScene


class BidiPromptPresentation(unittest.TestCase):
    def scene(self, text='אב', mode='grow', width=16, direction='auto'):
        s = NativeScene()
        self.addCleanup(s.close)
        s.command({'op':'resize', 'width':width, 'height':22})
        s.command({'op':'prompt', 'layout':'bidi', 'direction':direction,
                   'mode':mode, 'minRows':2, 'maxRows':4})
        s.command({'op':'draft', 'text':text, 'emitWeather':False})
        return s

    def test_positive_independent_hebrew_order_and_real_native_projection(self):
        s = self.scene()
        before = s.snapshot()
        rows = s.prompt_visual_layout()
        self.assertEqual([r[:5] for r in rows],
                         [[1,2,0,0,1], [0,1,1,0,1]])
        self.assertEqual([r[8:] for r in rows], [[1,ord('ב')], [1,ord('א')]])
        f = s.render()
        for r in rows:
            x,y = map(int,r[5:7])
            self.assertEqual(f.words()[y*f.width+x][0], int(r[9]))
            self.assertEqual(s.inspect_character_cell(x,y)['index'], int(r[0]))
        self.assertEqual(s.text_run_source(0,0), 'אב')
        self.assertEqual(s.snapshot(), before)
        self.assertEqual([r[:8] for r in rows], s.prompt_layout())

    def test_positive_odd_level_pointer_edges_are_logical_source_boundaries(self):
        s = self.scene()
        x,y = map(int,s.prompt_visual_layout()[0][5:7])
        for at,expected in [(x,2), (x+1,1), (x+2,0)]:
            for phase in ['down','up']:
                s.command({'op':'pointer','phase':phase,'x':at,'y':y})
            self.assertEqual(s.info()['prompt']['caret'], expected)

    def test_positive_combining_cluster_keeps_original_scalar_ownership(self):
        s = self.scene('א\u0301ב')
        rows = s.prompt_visual_layout()
        self.assertEqual([r[:5] for r in rows], [[2,3,0,0,1],[0,2,1,0,1]])
        x,y = map(int, rows[1][5:7])
        for at in [x,x+1]:
            for phase in ['down','up']:
                s.command({'op':'pointer','phase':phase,'x':at,'y':y})
            self.assertIn(s.info()['prompt']['caret'], [0,2])
        self.assertEqual(s.text_run_source(0,0), 'א\u0301ב')

    def test_positive_mirroring_does_not_change_source_or_selection(self):
        s = self.scene('(אב)', direction='rtl')
        rows = s.prompt_visual_layout()
        self.assertEqual([r[0] for r in rows], [3,2,1,0])
        self.assertEqual([r[9] for r in rows], list(map(ord,'(בא)')))
        s.command({'op':'select','anchor':0,'caret':4})
        self.assertEqual(s.selected_text(), '(אב)')
        self.assertEqual(s.text_run_source(0,0), '(אב)')

    def test_positive_all_modes_and_forced_direction_use_existing_engine(self):
        for mode in ['marquee','grow','vim-inline','vim-full']:
            for direction,code in [('ltr',0),('rtl',1),('auto',2)]:
                with self.subTest(mode=mode,direction=direction):
                    s = self.scene('Aאב B界', mode=mode, direction=direction)
                    rows = s.prompt_visual_layout()
                    expected = s.bidi_layout('Aאב B界', 12, direction=code)
                    self.assertEqual([r[:5] for r in rows], [r[:5] for r in expected])
                    self.assertEqual([r[8:] for r in rows], [r[5:] for r in expected])
                    self.assertTrue(all(r[7] == 1 for r in rows))

    def test_positive_wrapped_mixed_lines_keep_paragraph_resolution(self):
        text = 'אAב B界\nגDד'
        s = self.scene(text, width=9)
        expected = s.bidi_layout(text, 5, direction=2)
        rows = s.prompt_visual_layout()
        self.assertEqual([r[:5] for r in rows], [r[:5] for r in expected])
        self.assertEqual([r[8:] for r in rows], [r[5:] for r in expected])
        self.assertEqual(s.text_run_source(0,0), text)

    def test_positive_removed_controls_never_paint_or_capture(self):
        s = self.scene('A\u202bאב\u202cB')
        rows = s.prompt_visual_layout()
        self.assertFalse(any(r[0] in [1,4] for r in rows))
        for r in rows:
            if r[7] and r[4]:
                x,y = map(int,r[5:7])
                for phase in ['down','up']:
                    s.command({'op':'pointer','phase':phase,'x':x,'y':y})
                self.assertIn(s.info()['prompt']['caret'],
                              {int(v) for row in rows for v in row[:2]})

    def test_positive_owned_rows_and_inactive_visibility_are_pure(self):
        s = self.scene()
        rows = s.prompt_visual_layout()
        rows[0][0] = 900
        self.assertEqual(s.prompt_visual_layout()[0][0], 1)
        s.command({'op':'prompt','active':False})
        before = s.snapshot()
        self.assertTrue(all(r[7] == 0 for r in s.prompt_visual_layout()))
        self.assertEqual(s.snapshot(), before)

    def test_positive_vertical_navigation_uses_visual_column(self):
        s = self.scene('אב\nגד')
        s.command({'op':'select','anchor':2,'caret':2})
        s.command({'op':'key','key':'ArrowDown'})
        self.assertEqual(s.info()['prompt']['caret'],5)
        s.command({'op':'key','key':'ArrowUp'})
        self.assertEqual(s.info()['prompt']['caret'],2)

    def test_regression_authentic_schema50_keeps_logical_output(self):
        with NativeScene() as s:
            s.command({'op':'prompt','layout':'grapheme'})
            s.command({'op':'draft','text':'אב','emitWeather':False})
            expected=s.render();old=bytearray(s.snapshot()[:24+13497392])
            struct.pack_into('<I',old,12,0x20261050)
            struct.pack_into('<I',old,16,13497392)
            struct.pack_into('<I',old,28,0x20261050)
            struct.pack_into('<I',old,20,zlib.crc32(old[24:]))
            s.restore(old)
            self.assertEqual(s.render(),expected)
            self.assertEqual([r[0] for r in s.prompt_visual_layout()],[0,1])

    def test_negative_old_queued_bidi_options_and_partitioned_replay(self):
        with NativeScene() as s:
            s.command({'op':'schedule','id':1,'atUs':500000,
                       'command':{'op':'batch','commands':[
                           {'op':'prompt','layout':'bidi','direction':'rtl'}]}})
            before=s.snapshot();old=bytearray(before[:24+13497392])
            struct.pack_into('<I',old,12,0x20261050)
            struct.pack_into('<I',old,16,13497392)
            struct.pack_into('<I',old,28,0x20261050)
            struct.pack_into('<I',old,20,zlib.crc32(old[24:]))
            with self.assertRaises(ValueError):s.restore(old)
            self.assertEqual(s.snapshot(),before)
            s.advance_to(1000000);done=s.snapshot();s.restore(before)
            for t in [250000,500000,750000,1000000]:s.advance_to(t)
            self.assertEqual(s.snapshot(),done)

    def test_negative_options_are_atomic_and_not_silently_ignored(self):
        s = self.scene()
        before = s.snapshot()
        for patch in [{'direction':'bad'}, {'direction':True},
                      {'layout':'scalar','direction':'rtl'},
                      {'layout':'grapheme','direction':'auto'}]:
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):
                    s.command({'op':'prompt',**patch})
                self.assertEqual(s.snapshot(), before)

    def test_negative_real_C_probe_alignment_capacity_alias_canaries(self):
        s = self.scene()
        fn = s._lib.nrPromptVisualLayout
        fn.argtypes = [C.c_void_p,C.c_void_p,C.c_uint32]
        fn.restype = C.c_int
        self.assertEqual(fn(s._context,None,0),2)
        out = (C.c_double*30)(*([91]*30))
        before = s.snapshot()
        for ptr,cap in [(out,1),(C.c_void_p(C.addressof(out)+1),2),
                        (s._context,2)]:
            self.assertEqual(fn(s._context,ptr,cap),-1)
        self.assertEqual(list(out),[91]*30)
        self.assertEqual(fn(s._context,out,2),2)
        self.assertEqual(list(out)[20:],[91]*10)
        self.assertEqual(s.snapshot(),before)

    def test_regression_scalar_and_logical_grapheme_defaults_remain(self):
        with NativeScene() as s:
            s.command({'op':'draft','text':'אב','emitWeather':False})
            self.assertEqual(s.prompt_visual_layout(),[])
            s.command({'op':'prompt','layout':'grapheme'})
            rows = s.prompt_visual_layout()
            self.assertEqual([r[0] for r in rows],[0,1])
            self.assertEqual([r[8] for r in rows],[0,0])
            self.assertEqual([r[:8] for r in rows],s.prompt_layout())

    def test_negative_schema50_rejects_bidi_policy_with_valid_crc(self):
        s = self.scene()
        before = s.snapshot()
        old = bytearray(before[:24+13497392])
        struct.pack_into('<I',old,12,0x20261050)
        struct.pack_into('<I',old,16,13497392)
        struct.pack_into('<I',old,28,0x20261050)
        struct.pack_into('<I',old,20,zlib.crc32(old[24:]))
        with self.assertRaises(ValueError):
            s.restore(old)
        self.assertEqual(s.snapshot(),before)
