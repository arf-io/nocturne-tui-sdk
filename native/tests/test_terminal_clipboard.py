from pathlib import Path
import codecs,importlib.util,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
spec=importlib.util.spec_from_file_location('clipboard_terminal',ROOT/'examples/terminal.py');terminal=importlib.util.module_from_spec(spec);spec.loader.exec_module(terminal)
class TerminalClipboard(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.host=terminal.Host.__new__(terminal.Host);self.host.scene=self.s;self.host.buffer=bytearray();self.host.pasting=False;self.host.paint=lambda:None;self.host.decoder=codecs.getincrementaldecoder('utf-8')('strict');self.host.clipboard=''
 def testSplitShiftSequenceCreatesNativeSelection(self):
  self.s.command(dict(op='draft',text='AB',caret=0,emitWeather=False));self.host.input(b'\x1b[1;');self.host.input(b'2C');p=self.s.info()['prompt'];self.assertEqual((p['anchor'],p['caret']),(0,1))
 def testCopyCutPasteUnicodeRange(self):
  self.s.command(dict(op='draft',text='Aé日本Z',emitWeather=False));self.s.command(dict(op='select',anchor=1,caret=5));self.host.input(b'\x1bw\x17\x19');self.assertEqual(self.host.clipboard,'é日本');self.assertEqual(self.s.info()['prompt']['text'],'Aé日本Z')
 def testModalCannotReadOrEditClipboard(self):
  self.s.command(dict(op='draft',text='secret'));self.s.command(dict(op='select',anchor=0,caret=6));self.s.command(dict(op='key',key='F1'));self.host.clipboard='previous';before=self.s.snapshot();self.host.input(b'\x1bw\x17\x19');self.assertEqual(self.host.clipboard,'previous');self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
