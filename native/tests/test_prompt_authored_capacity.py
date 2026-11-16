"""Authored maxChars is a working document bound, not metadata."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bindings/python"))
from nocturne_native import NativeScene

class PromptAuthoredCapacity(unittest.TestCase):
    def scene(self, limit=4):
        s=NativeScene(2030); self.addCleanup(s.close)
        s.command({"op":"prompt","presentation":"framed","maxChars":limit})
        return s
    def rejected_unchanged(self,s,command):
        before=s.snapshot()
        with self.assertRaises((ValueError,RuntimeError)): s.command(command)
        self.assertEqual(s.snapshot(),before)
    def test_draft_input_paste_reject_overflow_atomically(self):
        for op in ("draft","input","paste"):
            with self.subTest(op=op):
                s=self.scene()
                self.rejected_unchanged(s,{"op":op,"text":"ABCDE"})
                s.command({"op":op,"text":"ABCD"})
                self.assertEqual(s.info()["prompt"]["text"],"ABCD")
    def test_selection_replacement_and_unicode_scalar_limit(self):
        s=self.scene()
        s.command({"op":"draft","text":"A😀BC","emitWeather":False})
        s.command({"op":"select","anchor":1,"caret":3})
        s.command({"op":"input","text":"🌧Z"})
        self.assertEqual(s.info()["prompt"]["text"],"A🌧ZC")
        self.rejected_unchanged(s,{"op":"input","text":"Q"})
    def test_shrink_rejects_current_document_and_source_history_survives(self):
        s=self.scene(8)
        s.command({"op":"draft","text":"12345678","emitWeather":False})
        self.rejected_unchanged(s,{"op":"prompt","maxChars":4})
        s.command({"op":"draft","text":"1234","emitWeather":False})
        s.command({"op":"prompt","maxChars":4})
        s.command({"op":"key","key":"z","ctrl":True})
        self.assertEqual(s.info()["prompt"]["text"],"12345678")
        self.rejected_unchanged(s,{"op":"input","text":"Q"})
    def test_newline_and_vim_paste_obey_limit(self):
        s=self.scene()
        s.command({"op":"draft","text":"ABCD","emitWeather":False})
        self.rejected_unchanged(s,{"op":"key","key":"Enter","shift":True})

if __name__=="__main__": unittest.main()
