import sys,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1].parent
sys.path[:0]=[str(ROOT/"native/bindings/python"),str(ROOT/"native/hosts/python")]
from nocturne_native import NativeScene
from atelier_application import atelier_prompt_command
from unicode_document_view import UnicodeDocumentView
class DocumentCapacity(unittest.TestCase):
 def scene(self):
  s=NativeScene();self.addCleanup(s.close);return s
 def test_factory_default_and_zero_and_authored_limit(self):
  for options in [None,{"maxChars":0}]:
   s=self.scene();s.command(atelier_prompt_command(options=options));s.command({"op":"draft","text":"x"*65537,"emitWeather":False});self.assertEqual(len(s.text_run_source(0,0)),65537)
  s=self.scene();s.command(atelier_prompt_command(options={"maxChars":70000}));s.command({"op":"draft","text":"x"*70000,"emitWeather":False});before=s.snapshot()
  with self.assertRaises(ValueError):s.command({"op":"input","text":"x"})
  self.assertEqual(before,s.snapshot())
 def test_small_mapping_matches_original_native_helpers(self):
  s=self.scene()
  for text in ["", "AאבB", "א́👩‍🔧ב\tA\nב", "\r\nZ", "A\u2067אב\u2069B"]:
   for columns in [1,7,31]:
    for direction in [0,1,2]:
     self.assertEqual(s.document_layout(text,columns,direction),s.bidi_layout(text,columns,direction))
     boundaries=s.document_boundaries(text);self.assertEqual(boundaries,s.grapheme_boundaries(text))
     for offset in boundaries:
      for affinity in [0,1]:self.assertEqual(s.document_caret(text,columns,offset,affinity,direction),s.bidi_caret(text,columns,offset,affinity,direction))
     for x,y in [(0,0),(3,0),(0,3),(31,7)]:self.assertEqual(s.document_hit(text,columns,x,y,direction),s.bidi_hit(text,columns,x,y,direction))
 def test_long_paragraph_and_multiparagraph_native_view(self):
  s=self.scene();view=UnicodeDocumentView()
  for text in ["אב"*2501, ("Aא́👩‍🔧ב\tZ\n"*7001)]:
   s.command({"op":"draft","text":text,"caret":len(text),"emitWeather":False});before=s.snapshot();rows=s.document_layout(text,79);self.assertGreater(len(rows),2048);self.assertEqual(max(row[1] for row in rows),len(text));self.assertEqual(s.document_boundaries(text)[-1],len(text));self.assertIsNotNone(view.paint(s,79,20));self.assertEqual(before,s.snapshot());self.assertEqual(s.text_run_source(0,0),text)
   self.assertTrue(view.move(s,"PageUp",True));self.assertGreaterEqual(s.info_complete()["prompt"]["anchor"],0);view.paint(s,79,20);self.assertTrue(view.move(s,"PageUp"));view.paint(s,79,20);self.assertTrue(view.scroll_by(s,3));view.pointer(s,"down",2,2,False);view.pointer(s,"move",5,2,False);view.pointer(s,"up",5,2,False);self.assertEqual(s.text_run_source(0,0),text)
 def test_hidden_boundaries_match_original_native_semantics(self):
  s=self.scene();self.assertEqual(s.document_boundaries("a\u202a\u202cb"),[0,1,2,3,4])
  for method in [s.document_caret,s.bidi_caret]:
   with self.assertRaises(ValueError):method("a\u202a\u202cb",8,2)
 def test_default_factory_keeps_original_short_document_frames(self):
  for mode in ["marquee","grow","vim-inline","vim-full"]:
   old,new=self.scene(),self.scene()
   for scene,max_chars in [(old,65536),(new,0)]:
    scene.command({"op":"resize","width":100,"height":40});scene.command(atelier_prompt_command(mode,{"maxChars":max_chars}));scene.command({"op":"draft","text":"Type original light א́👩‍🔧.","caret":0,"emitWeather":False})
   self.assertEqual(old.render().bytes,new.render().bytes,mode)
 def test_native_workspace_rejections_are_atomic(self):
  import ctypes as C
  s=self.scene();s.document_layout("abc",8);fn=s._lib.nrDocumentBidiClusterLayout;source=(C.c_uint32*3)(97,98,99);out=(C.c_uint32*21)(*([0x12345678]*21));scratch=(C.c_uint32*160)();expected=list(out)
  self.assertLess(fn(source,3,1,8,2,out,3,scratch,159),0);self.assertEqual(list(out),expected)
  self.assertLess(fn(source,3,1,8,2,out,2,scratch,160),0);self.assertEqual(list(out),expected)
  scratch_before=list(scratch);self.assertLess(fn(source,3,1,8,2,scratch,3,scratch,160),0);self.assertEqual(list(scratch),scratch_before)
  self.assertLess(fn(source,0x80000000,1,8,2,out,3,scratch,160),0);self.assertEqual(list(out),expected)
 def test_invalid_unicode_and_policy_are_pure(self):
  s=self.scene();before=s.snapshot()
  for text,columns in [("x\ud800",8),("valid",0)]:
   with self.assertRaises((ValueError,UnicodeError)):s.document_layout(text,columns)
  with self.assertRaises(ValueError):s.document_caret("é",8,1)
  self.assertEqual(s.snapshot(),before)
if __name__=="__main__":unittest.main(verbosity=2)
