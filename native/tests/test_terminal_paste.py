from pathlib import Path
import codecs,importlib.util,sys,unittest
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
spec=importlib.util.spec_from_file_location('direct_terminal',ROOT/'examples/terminal.py');terminal=importlib.util.module_from_spec(spec);spec.loader.exec_module(terminal)
class TerminalPaste(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
  self.host=terminal.Host.__new__(terminal.Host);self.host.scene=self.s;self.host.buffer=bytearray();self.host.pasting=False;self.host.paint=lambda:None;self.host.decoder=codecs.getincrementaldecoder('utf-8')('strict')
 def paste(self,text):self.host.input(b'\x1b[200~'+text+b'\x1b[201~')
 def testBlockedPastePreservesNativeState(self):
  self.s.command(dict(op='key',key='F1'));before=self.s.snapshot();self.paste(b'X');self.assertEqual(self.s.snapshot(),before)
 def testSplitFramingAndUnicodeAreOneEdit(self):
  before=self.s.info()['prompt']['revision'];self.host.input(b'\x1b[20');self.host.input(b'0~e\xcc');self.host.input(b'\x81\n\xe6\x97\xa5\x1b[20');self.host.input(b'1~')
  self.assertEqual(self.s.info()['prompt']['text'],'é\n日');self.assertEqual(self.s.info()['prompt']['revision'],before+1)
 def testLargeChunkedUnicodePasteHasNoLegacyByteLimit(self):
  text='λ🪶é\n'*25000;raw=text.encode('utf-8');before=self.s.info()['prompt']['revision']
  self.host.input(b'\x1b[200~')
  for start in range(0,len(raw),4096):self.host.input(raw[start:start+4096])
  self.host.input(b'\x1b[20');self.host.input(b'1~')
  self.assertEqual(self.s.info()['prompt']['text'],text);self.assertEqual(self.s.info()['prompt']['revision'],before+1)
 def testInvalidPasteUtf8CannotBecomeReplacementText(self):
  before=self.s.snapshot()
  with self.assertRaises(UnicodeDecodeError):self.paste(b'\xff')
  self.assertEqual(self.s.snapshot(),before)
 def testOrdinaryKeysRespectModalAndVimOwnership(self):
  self.s.command(dict(op='key',key='F1'));before=self.s.snapshot();self.host.input(b'X\n\t');self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='key',key='Escape'));self.s.command(dict(op='draft',text='AB',caret=1,emitWeather=False));self.s.command(dict(op='prompt',mode='vim-inline'));self.s.command(dict(op='key',key='Escape'))
  self.host.input(b'h');self.assertEqual(self.s.info()['prompt']['text'],'AB');self.assertEqual(self.s.info()['prompt']['caret'],0)
  self.host.input('ié'.encode());self.assertEqual(self.s.info()['prompt']['text'],'éAB')
 def testTypedEnterUsesNativeOwnership(self):
  self.host.input(b'A\nB');self.assertEqual(self.s.info()['prompt']['text'],'A\nB')
 def testInvalidTypedUtf8IsRejectedWithoutReplacement(self):
  with patch.object(terminal.Host,'load'):
   host=terminal.Host(SimpleNamespace(seed=2030,paused=True,scene='autumn'))
  self.addCleanup(host.scene.close);host.paint=lambda:None
  before=host.scene.snapshot()
  with self.assertRaises(UnicodeDecodeError):host.input(b'\xff')
  self.assertEqual(host.scene.snapshot(),before)
if __name__=='__main__':unittest.main()
