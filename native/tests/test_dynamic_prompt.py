"""Real caller-owned prompt growth through the Python/native public ABI."""
import ctypes as C,sys,unittest,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class DynamicPrompt(unittest.TestCase):
 def test_repeated_growth_unicode_selection_history_snapshot(self):
  with NativeScene() as scene:
   scene.command({'op':'prompt','presentation':'framed','mode':'grow'})
   for size in (65537,131089,262177):
    text=('A\n界e\u0301🙂'*(size//6+1))[:size]
    scene.command({'op':'draft','text':text,'emitWeather':False})
    self.assertEqual(scene.text_run_source(0,0),text)
    scene.command({'op':'select','anchor':size-12,'caret':size})
    self.assertEqual(scene.selected_text(),text[-12:])
    saved=scene.snapshot();scene.render();self.assertEqual(scene.snapshot(),saved)
    with NativeScene() as restored:
     restored.restore(saved);self.assertEqual(restored.text_run_source(0,0),text);self.assertEqual(restored.snapshot(),saved)
    before=scene.snapshot()
    with self.assertRaises(ValueError):scene.command({'op':'draft','text':text,'unexpected':1})
    self.assertEqual(scene.snapshot(),before)
 def test_authored_limit_optional_and_atomic(self):
  with NativeScene() as scene:
   scene.command({'op':'prompt','presentation':'framed','maxChars':70000})
   scene.command({'op':'draft','text':'A'*70000,'emitWeather':False});saved=scene.snapshot()
   with self.assertRaises(ValueError):scene.command({'op':'input','text':'B'})
   self.assertEqual(scene.snapshot(),saved)
   scene.command({'op':'prompt','maxChars':0});scene.command({'op':'input','text':'B'})
   self.assertEqual(len(scene.text_run_source(0,0)),70001)
 def test_storage_failure_history_registers_and_checkpoint(self):
  import json
  with NativeScene() as scene:
   saved=scene.snapshot();raw=json.dumps({'op':'draft','text':'A'*70001,'emitWeather':False}).encode()
   self.assertLess(scene._lib.nrCommand(scene._context,raw,len(raw)),0)
   self.assertEqual(scene._lib.nrError(scene._context),b'Prompt storage required');self.assertEqual(scene.snapshot(),saved)
   required=scene._lib.nrPromptMemorySize(scene._context)
   self.assertLess(scene._lib.nrSetPromptMemory(scene._context,None,required),0)
   self.assertLess(scene._lib.nrSetPromptMemory(scene._context,scene._context,required),0)
   self.assertEqual(scene.snapshot(),saved)
   scene.command({'op':'prompt','presentation':'framed','mode':'vim-inline'})
   text='Z'*70001;scene.command({'op':'draft','text':text,'caret':0,'emitWeather':False})
   def keys(*values):
    for key in values:scene.command({'op':'key','key':key})
   keys('Escape','"','a','y','y')
   scene.command({'op':'draft','text':'tail','caret':0,'emitWeather':False});keys('Escape','"','a','P')
   self.assertEqual(scene.text_run_source(0,0),text+'\n'+'tail');keys('u');self.assertEqual(scene.text_run_source(0,0),'tail')
   scene.command({'op':'draft','text':text,'caret':0,'emitWeather':False});keys('Escape',':','w','Enter')
   saved=scene.snapshot()
   with NativeScene() as other:
    other.restore(saved);self.assertEqual(other.snapshot(),saved);self.assertEqual(other.text_run_source(0,0),text)
 def test_compact_grapheme_query_beyond_old_capacity(self):
  with NativeScene() as scene:
   text='e\u0301界\t\n'*15001;scene.command({'op':'prompt','layout':'grapheme','mode':'grow'})
   scene.command({'op':'draft','text':text,'emitWeather':False});self.assertEqual(scene.text_run_source(0,0),text)
   self.assertEqual(len(scene.text_run_clusters(0,0)),60004);self.assertEqual(len(scene.prompt_layout()),60004)
   saved=scene.snapshot();scene.render();self.assertEqual(scene.snapshot(),saved)
 def test_large_bidi_public_geometry_and_capacity_independent_snapshot(self):
  with NativeScene() as scene:
   text='אב\n'*25001;scene.command({'op':'prompt','layout':'bidi','direction':'rtl','mode':'grow'})
   scene.command({'op':'draft','text':text,'emitWeather':False});rows=scene.prompt_visual_layout()
   self.assertEqual(len(rows),len(text));self.assertEqual([int(r[0]) for r in rows[:3]],[2,1,0])
   self.assertEqual([int(r[0]) for r in rows[-3:]],[75002,75001,75000])
   self.assertEqual(scene.text_run_source(0,0),text);saved=scene.snapshot();scene.render();self.assertEqual(scene.snapshot(),saved)
   capacity=scene._lib.nrPromptMemoryCapacity(scene._context);arena=C.create_string_buffer(capacity*2+8);pointer=(C.addressof(arena)+7)&~7
   self.assertEqual(scene._lib.nrSetPromptMemory(scene._context,pointer,capacity*2),0);self.assertEqual(scene.snapshot(),saved)
   self.assertLess(scene._lib.nrSetPromptMemory(scene._context,pointer,capacity*2),0)
   self.assertLess(scene._lib.nrLoad(scene._context,pointer,len(saved)),0);self.assertEqual(scene.snapshot(),saved)
if __name__=='__main__':unittest.main()
