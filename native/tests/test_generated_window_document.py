import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"bindings/python"))

from nocturne_native import NativeScene


class GeneratedWindowDocument(unittest.TestCase):
    def test_full_empty_and_missing_source_reads(self):
        with NativeScene(2030) as scene:
            scene.command({'op': 'window', 'id': 1, 'title': 'Window', 'text': 'initial'})
            text = 'x' * 4095 + 'Z'
            scene.command({'op': 'window-content', 'id': 1, 'text': text})
            self.assertEqual(len(text), 4096)
            self.assertEqual(scene.text_run_source(2, 1), text)
            scene.command({'op': 'window-content', 'id': 1, 'text': ''})
            self.assertEqual(scene.text_run_source(2, 1), '')
            with self.assertRaises(ValueError):
                scene.text_run_source(2, 65535)


if __name__ == '__main__':
    unittest.main()
