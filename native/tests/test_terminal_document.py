from pathlib import Path
import importlib.util,json,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
spec=importlib.util.spec_from_file_location('terminal_document',ROOT/'examples/terminal.py');terminal=importlib.util.module_from_spec(spec);spec.loader.exec_module(terminal)
class TerminalDocument(unittest.TestCase):
 def execute(self,source,saved,run):
  scene=NativeScene();close=Mock(wraps=scene.close);scene.close=close
  host=SimpleNamespace(scene=scene,run=lambda:run(scene))
  with patch.object(terminal,'Host',return_value=host),patch.object(sys.stdin,'isatty',return_value=True),patch.object(sys.stdout,'isatty',return_value=True),patch.object(sys,'argv',['terminal','--load-document',str(source),'--save-document',str(saved)]):
   try:terminal.main()
   finally:close.assert_called_once()
 def testAcceptedDocumentIsSavedAfterNormalExit(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'in';saved=Path(tmp)/'out';source.write_text(json.dumps(dict(profile='nocturne-document-v1',text='é日本',caret=2)))
   self.execute(source,saved,lambda scene:scene.command(dict(op='paste',text='X')))
   self.assertEqual(json.loads(saved.read_text()),dict(profile='nocturne-document-v1',text='éX日本',caret=3))
 def testRunFailureCannotOverwritePreviousSave(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'in';saved=Path(tmp)/'out';source.write_text(json.dumps(dict(profile='nocturne-document-v1',text='abc',caret=1)));saved.write_bytes(b'previous')
   def fail(scene):scene.command(dict(op='paste',text='X'));raise RuntimeError('host failure')
   with self.assertRaisesRegex(RuntimeError,'host failure'):self.execute(source,saved,fail)
   self.assertEqual(saved.read_bytes(),b'previous')
 def testRejectedImportNeverRunsOrSaves(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'in';saved=Path(tmp)/'out';source.write_text(json.dumps(dict(profile='future',text='',caret=0)));saved.write_bytes(b'previous');run=Mock()
   with self.assertRaises(ValueError):self.execute(source,saved,run)
   run.assert_not_called();self.assertEqual(saved.read_bytes(),b'previous')
if __name__=='__main__':unittest.main()
