from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class PromptModifiers(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def testModifiedVimKeysCannotConsumeOrEditTheDraft(self):
  self.s.command(dict(op='prompt',mode='vim-inline'));self.s.command(dict(op='draft',text='abc\ndef',caret=4,emitWeather=False));self.s.command(dict(op='key',key='Escape'))
  for modifier in ['ctrl','alt','meta']:
   for key in ['i','I','A','o','O','h','j','k','l','u','x','X','s','D','C','0','^','$']:
    before=self.s.snapshot()
    with self.assertRaises(ValueError,msg=(modifier,key)):self.s.command(dict(op='key',key=key,**{modifier:True}))
    self.assertEqual(self.s.snapshot(),before,(modifier,key))
 def testMixedModifiersCannotInvokeControlShortcuts(self):
  self.s.command(dict(op='draft',text='abcdef',caret=3,emitWeather=False))
  for modifier in ['alt','meta']:
   for key in ['a','e','z']:
    before=self.s.snapshot()
    with self.assertRaises(ValueError):self.s.command(dict(op='key',key=key,ctrl=True,**{modifier:True}))
    self.assertEqual(self.s.snapshot(),before)
 def testControlShortcutsAndShiftedVimCommandsRemainAvailable(self):
  self.s.command(dict(op='draft',text='abc',caret=1,emitWeather=False))
  self.s.command(dict(op='key',key='a',ctrl=True));self.assertEqual(self.s.info()['prompt']['caret'],0)
  self.s.command(dict(op='key',key='e',ctrl=True));self.assertEqual(self.s.info()['prompt']['caret'],3)
  self.s.command(dict(op='prompt',mode='vim-inline'));self.s.command(dict(op='key',key='Escape'))
  self.s.command(dict(op='key',key='O',shift=True));self.assertEqual(self.s.info()['prompt']['text'],'\nabc')
if __name__=='__main__':unittest.main()
