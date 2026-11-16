"""Graph selection and prompt selection retain distinct public payloads."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class SelectionDispatch(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def test_graph_selection_is_not_shadowed_by_prompt_selection(self):
  self.s.command(dict(op='node',id=7,label='Node seven'));self.s.command(dict(op='draft',text='AéZ',emitWeather=False));before=self.s.info()['prompt']['text']
  self.s.command(dict(op='select',id=7,durationMs=0));self.assertEqual(self.s.info()['selection'],7);self.assertEqual(self.s.info()['prompt']['text'],before)
  self.s.command(dict(op='select',anchor=1,caret=3,unit='grapheme'));self.assertEqual(self.s.selected_text(),'é');self.assertEqual(self.s.info()['selection'],7)
 def test_mixed_or_wrong_selection_payload_rejects_atomically(self):
  self.s.command(dict(op='draft',text='AéZ',emitWeather=False))
  for command in [dict(op='select',id=7,anchor=1),dict(op='select',id=999),dict(op='select',anchor=2,caret=3,unit='grapheme')]:
   before=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command(command)
   self.assertEqual(before,self.s.snapshot())
if __name__=='__main__':unittest.main()
