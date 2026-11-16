from pathlib import Path
import json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'hosts/python'),str(ROOT/'bindings/python')]
from document_store import save_document,load_document,PROFILE
from nocturne_native import NativeScene
class DocumentStore(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'draft.json'
 def testRoundTripPreservesExactUnicodeAndCaretWithoutSaveMutation(self):
  text='é👩\u200d🔧\n日本語'
  self.s.command(dict(op='draft',text=text,caret=2,emitWeather=False));before=self.s.snapshot();save_document(self.s,self.path);self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='draft',text='other',emitWeather=False));before=self.s.info();load_document(self.s,self.path);after=self.s.info()
  self.assertEqual(after['prompt']['text'],text);self.assertEqual(after['prompt']['caret'],2);self.assertEqual(after['fieldCount'],before['fieldCount']);self.assertEqual(after['clock'],before['clock'])
 def testRequiredSeparatorsRoundTripWithoutNormalization(self):
  for separator in ['\r','\r\n','\x0b','\x0c','\u0085','\u2028','\u2029']:
   with self.subTest(separator=repr(separator)):
    text='before'+separator+'after';caret=len('before'+separator)
    self.s.command(dict(op='draft',text=text,caret=caret,emitWeather=False))
    before=self.s.snapshot();save_document(self.s,self.path)
    self.assertEqual(self.s.snapshot(),before)
    self.assertEqual(json.loads(self.path.read_text())['text'],text)
    self.s.command(dict(op='draft',text='replacement',emitWeather=False))
    load_document(self.s,self.path)
    self.assertEqual((self.s.info()['prompt']['text'],self.s.info()['prompt']['caret']),(text,caret))
 def testFailedReplacePreservesPreviousFileAndScene(self):
  self.path.write_bytes(b'old');before=self.s.snapshot()
  with patch('document_store.os.replace',side_effect=OSError('injected storage failure')):
   with self.assertRaises(OSError):save_document(self.s,self.path)
  self.assertEqual(self.path.read_bytes(),b'old');self.assertEqual(self.s.snapshot(),before);self.assertEqual(list(self.path.parent.iterdir()),[self.path])
 def testLargeImportsPreserveExactSourceAndExplicitLimits(self):
  for text in ['x'*2049,('界e\u0301🙂\n'*14001),('界🙂e\u0301\n'*100001)]:
   with self.subTest(scalars=len(text)):
    value=dict(profile=PROFILE,text=text,caret=len(text)-1);self.path.write_text(json.dumps(value));load_document(self.s,self.path)
    if len(text)>100000:self.assertGreater(len(text.encode('utf-8')),1024*1024)
    self.assertEqual(self.s.text_run_source(0,0),text);self.assertEqual(self.s.info_complete()['prompt']['caret'],len(text)-1)
    before=self.s.snapshot();save_document(self.s,self.path);self.assertEqual(self.s.snapshot(),before);self.assertEqual(json.loads(self.path.read_text()),value)
    self.s.command(dict(op='draft',text='replacement',emitWeather=False));clock=self.s.info_complete()['clock'];load_document(self.s,self.path);self.assertEqual(self.s.text_run_source(0,0),text);self.assertEqual(self.s.info_complete()['clock'],clock)
  self.s.command(dict(op='draft',text='',emitWeather=False));self.s.command(dict(op='prompt',presentation='framed',maxChars=2048));before=self.s.snapshot()
  self.path.write_text(json.dumps(dict(profile=PROFILE,text='x'*2049,caret=0)))
  with self.assertRaises(ValueError):load_document(self.s,self.path)
  self.assertEqual(self.s.snapshot(),before)
 def testInvalidUtf8FilePreservesScene(self):
  self.path.write_bytes(b'\xff\xfe');before=self.s.snapshot()
  with self.assertRaises(UnicodeDecodeError):load_document(self.s,self.path)
  self.assertEqual(self.s.snapshot(),before)
 def testRejectedImportsAreAtomic(self):
  for value in [dict(profile=PROFILE,text='abc',caret=True),dict(profile=PROFILE,text='abc',caret=4),dict(profile='future',text='',caret=0),dict(profile=PROFILE,text='\x00',caret=0)]:
   self.path.write_text(json.dumps(value));before=self.s.snapshot()
   with self.assertRaises(ValueError):load_document(self.s,self.path)
   self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
