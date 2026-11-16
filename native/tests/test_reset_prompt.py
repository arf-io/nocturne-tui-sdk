from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class ResetPrompt(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def testExplicitResetPreservesEditorAndUndo(self):
  self.s.command(dict(op='prompt',mode='vim-full'));self.s.command(dict(op='draft',text='é日本',caret=2,emitWeather=False));self.s.command(dict(op='key',key='i'));self.s.command(dict(op='paste',text='X'));self.s.command(dict(op='key',key='Escape'));before=self.s.info()['prompt']
  self.s.command(dict(op='reset',seed=99,preservePrompt=True));self.assertEqual(self.s.info()['prompt'],before)
  self.s.command(dict(op='key',key='u'));p=self.s.info()['prompt'];self.assertEqual((p['text'],p['caret'],p['mode'],p['vimMode']),('é日本',2,3,'normal'))
 def testWrappedUndoRingSurvivesRepeatedReset(self):
  for i in range(105):self.s.command(dict(op='paste',text=chr(65+i)))
  for seed in [99,101,2030]:self.s.command(dict(op='reset',seed=seed,preservePrompt=True))
  for count in range(104,4,-1):
   self.s.command(dict(op='key',key='z',ctrl=True));p=self.s.info()['prompt'];self.assertEqual(p['text'],''.join(chr(65+i) for i in range(count)));self.assertEqual(p['caret'],count)
  before=self.s.snapshot();self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.snapshot(),before)
 def testModalOwnershipSurvivesResetAndRelease(self):
  self.s.command(dict(op='draft',text='accepted',caret=3,emitWeather=False));self.s.command(dict(op='key',key='F1'));self.s.command(dict(op='reset',preservePrompt=True))
  self.assertEqual(self.s.info()['inputOwner'],'modal');before=self.s.snapshot();self.s.command(dict(op='paste',text='blocked'));self.assertEqual(self.s.snapshot(),before)
  self.s.command(dict(op='key',key='Escape'));self.s.command(dict(op='paste',text='X'));self.assertEqual(self.s.info()['prompt']['text'],'accXepted')
 def testDefaultResetStillClearsDocument(self):
  self.s.command(dict(op='draft',text='X'));self.s.command(dict(op='reset'));self.assertEqual(self.s.info()['prompt']['text'],'')
 def testInvalidPreservationFlagIsAtomic(self):
  self.s.command(dict(op='draft',text='X'));before=self.s.snapshot()
  with self.assertRaises(Exception):self.s.command(dict(op='reset',seed=99,preservePrompt=1))
  self.assertEqual(self.s.snapshot(),before)
if __name__=='__main__':unittest.main()
