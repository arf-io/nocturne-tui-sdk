"""Actual C metadata streaming: bounds, byte ownership, CRC and accepted text."""
import ctypes as C
import json
from pathlib import Path
import sys
import unittest
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

TEXT = "🙂" * 2048

def populate(scene):
    scene.command({'op': 'pause', 'paused': True})
    for i in range(1, 25):
        scene.command({'op': 'text', 'id': i, 'text': TEXT})
    for i in range(1, 13):
        scene.command({'op': 'window', 'id': i, 'title': f'Retained {i}',
                       'text': TEXT, 'position': [0, 0, 16000]})

class MetadataPages(unittest.TestCase):
    def setUp(self):
        self.s = NativeScene(seed=8128)
        self.addCleanup(self.s.close)

    def api(self):
        self.assertTrue(hasattr(self.s._lib, 'nrInfoPage'), 'current C ABI needs nrInfoPage')
        f = self.s._lib.nrInfoPage
        f.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32]
        f.restype = C.c_int
        return f

    def collect(self, page_size=65536):
        f = self.api(); out = C.create_string_buffer(page_size + 5)
        words = (C.c_uint32 * 4)(); offset = 0; chunks = []; identity = None
        while True:
            C.memset(out, 0x5a, len(out))
            status = f(self.s._context, offset, out, page_size, words, 4)
            self.assertIn(status, (0, 1))
            total, written, next_offset, checksum = words
            self.assertEqual(written, min(page_size, total-offset))
            self.assertEqual(next_offset, offset + written)
            self.assertEqual(status, int(next_offset < total))
            self.assertEqual(out.raw[written:], b'Z' * (len(out)-written))
            self.assertEqual(identity or (total, checksum), (total, checksum))
            identity = total, checksum
            chunks.append(out.raw[:written]); offset = next_offset
            if status == 0: break
            self.assertGreater(written, 0)
        data = b''.join(chunks)
        self.assertEqual(len(data), identity[0])
        self.assertEqual(zlib.crc32(data), identity[1])
        return data

    def test_large_accepted_scene_recovers_without_state_mutation(self):
        populate(self.s)
        large_prompt="界"*400001
        self.s.command({'op':'draft','text':large_prompt,'emitWeather':False})
        before = self.s.snapshot()
        bounded = self.s.info()
        raw = self.collect(); self.assertGreater(len(raw), 1048576)
        info = json.loads(raw)
        self.assertIn(bounded, ({'error': 'metadata capacity exceeded'}, info))
        self.assertEqual(info['prompt']['text'],large_prompt)
        self.assertEqual(len(info['textRuns']), 24)
        self.assertEqual(len(info['windows']), 12)
        self.assertTrue(all(t['text'] == TEXT for t in info['textRuns'] + info['windows']))
        self.assertEqual(before, self.s.snapshot())
        self.assertEqual(self.s.info(), bounded)

    def test_small_result_is_byte_identical_to_legacy_and_crosses_utf8_boundaries(self):
        self.s.command({'op': 'draft', 'text': 'A🙂BéC \" \\ \n'})
        legacy = self.s._lib.nrInfo(self.s._context)
        for page_size in (7, 4095, 65536):
            with self.subTest(page_size=page_size):
                self.assertEqual(self.collect(page_size), legacy)

    def test_probe_and_end_return_no_terminator_or_payload(self):
        f = self.api(); words = (C.c_uint32 * 6)(9, 9, 9, 9, 73, 74)
        self.assertEqual(f(self.s._context, 0, None, 0, words, 6), 1)
        total, written, next_offset, checksum = words[:4]
        self.assertGreater(total, 0); self.assertEqual((written, next_offset), (0, 0))
        out = C.create_string_buffer(b'unchanged')
        self.assertEqual(f(self.s._context, total, out, 9, words, 6), 0)
        self.assertEqual(list(words[:4]), [total, 0, total, checksum])
        self.assertEqual(list(words[4:]), [73, 74])
        self.assertEqual(out.value, b'unchanged')

    def test_rejection_leaves_outputs_and_snapshot_unchanged(self):
        f = self.api(); out = C.create_string_buffer(b'X' * 64)
        words = (C.c_uint32 * 4)(17, 18, 19, 20)
        before = self.s.snapshot()
        cases = [(None, 0, out, 64, words, 4),
                 (self.s._context, 0xffffffff, out, 64, words, 4),
                 (self.s._context, 0, out, 65537, words, 4),
                 (self.s._context, 0, None, 64, words, 4),
                 (self.s._context, 0, out, 64, None, 4),
                 (self.s._context, 0, out, 64, words, 3),
                 (self.s._context, 0, self.s._context, 64, words, 4),
                 (self.s._context, 0, out, 64, self.s._context, 4),
                 (self.s._context, 0, out, 64, C.byref(out, 4), 4),
                 (self.s._context, 0, out, 64, C.byref(words, 1), 4)]
        for args in cases:
            with self.subTest(args=str(args)):
                self.assertEqual(f(*args), -1)
                self.assertEqual(out.value, b'X' * 64)
                self.assertEqual(list(words), [17, 18, 19, 20])
                self.assertEqual(before, self.s.snapshot())

    def test_context_changes_have_distinct_consistency_checksums(self):
        f = self.api(); words = (C.c_uint32 * 4)()
        f(self.s._context, 0, None, 0, words, 4); old = tuple(words)
        self.s.command({'op': 'draft', 'text': 'one accepted new source'})
        f(self.s._context, 0, None, 0, words, 4)
        self.assertNotEqual(words[3], old[3])

    def test_python_complete_reader_owned_bounded_and_closed(self):
        self.assertTrue(callable(getattr(self.s, 'info_complete', None)))
        self.s.command({'op': 'draft', 'text': 'é🙂 exact'})
        normal = self.s.info(); self.assertEqual(self.s.info_complete(), normal)
        with self.assertRaises(ValueError): self.s.info_complete(max_bytes=1)
        self.assertEqual(self.s.info_complete(max_bytes=None),normal)
        self.assertEqual(self.s.info_complete(max_bytes=16777217),normal)
        for limit in (True, 0, -1, 1.5, 0x100000000):
            with self.assertRaises(ValueError): self.s.info_complete(max_bytes=limit)
        old = self.s.info_complete()
        self.s.command({'op': 'draft', 'text': 'changed'})
        self.assertEqual(old['prompt']['text'], 'é🙂 exact')
        populate(self.s)
        complete = self.s.info_complete()
        self.assertEqual(len(complete['windows']), 12)
        self.s.close()
        with self.assertRaises(RuntimeError): self.s.info_complete()

    def test_complete_metadata_exceeds_previous_16mib_limit(self):
        text='\x0b'*2800001
        self.s.command({'op':'draft','text':text,'emitWeather':False})
        words=(C.c_uint32*4)()
        self.assertEqual(self.api()(self.s._context,0,None,0,words,4),1)
        self.assertGreater(words[0],16777216)
        info=self.s.info_complete()
        self.assertEqual(info['prompt']['text'],text)
        self.assertEqual(info['prompt']['caret'],len(text))
        self.assertEqual(self.s.text_run_source(0,0),text)
        print(f'Actual native complete metadata bytes={words[0]} scalars={len(text)} crc32={words[3]:08x}',flush=True)

    def test_strict_plan_includes_complete_metadata_wasm_and_sanitizers(self):
        import subprocess
        run=subprocess.run([sys.executable,str(ROOT/'scripts/qualify.py'),'--list','--strict','--capture'],
                           capture_output=True,text=True,check=True)
        rows=json.loads(run.stdout);names={x['id'] for x in rows}
        self.assertTrue({'metadata-pages-typescript','metadata-pages-sanitizer-build',
                         'metadata-pages-sanitizer-run'}<=names)

    def test_page_sizes_produce_identical_complete_large_bytes(self):
        populate(self.s)
        large_prompt="界"*400001
        self.s.command({'op':'draft','text':large_prompt,'emitWeather':False})
        before = self.s.snapshot()
        expected = self.collect(65536)
        self.assertEqual(self.collect(16381), expected)
        self.assertEqual(self.collect(32767), expected)
        self.assertEqual(before, self.s.snapshot())

if __name__ == '__main__': unittest.main()
