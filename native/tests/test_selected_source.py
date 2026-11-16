from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class SelectedSource(unittest.TestCase):
 def testOwnedUnicodeRangeAndOwnership(self):
  with NativeScene() as s:
   self.assertIsNone(s.selected_text());s.command(dict(op='draft',text='Aé日本Z',emitWeather=False));s.command(dict(op='select',anchor=5,caret=1));before=s.snapshot();self.assertEqual(s.selected_text(),'é日本');self.assertEqual(s.snapshot(),before)
   s.command(dict(op='key',key='F1'));self.assertIsNone(s.selected_text());s.command(dict(op='key',key='Escape'));self.assertEqual(s.selected_text(),'é日本')
if __name__=='__main__':unittest.main()
