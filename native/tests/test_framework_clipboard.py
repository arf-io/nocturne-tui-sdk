from pathlib import Path
import sys,unittest,asyncio
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hosts/python'))
from prompt_toolkit_host import FrameworkHost
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.clipboard import InMemoryClipboard
class FrameworkClipboard(unittest.TestCase):
 def testRegisteredKeysCopyCutPasteSelectedNativeText(self):
  with create_pipe_input() as source:
   host=FrameworkHost(input=source,output=DummyOutput())
   try:
    host.scene.command(dict(op='draft',text='Aé日本Z',caret=5,emitWeather=False));host.scene.command(dict(op='select',anchor=1,caret=5))
    async def execute():
     task=asyncio.create_task(host.application.run_async());await asyncio.sleep(.05);source.send_bytes(b'\x1bw\x17\x19\x11');await task
    asyncio.run(execute());self.assertEqual(host.application.clipboard.get_data().text,'é日本');self.assertEqual(host.scene.info()['prompt']['text'],'Aé日本Z')
   finally:host.scene.close()
 def testModalCannotReadOrCutPromptThroughClipboard(self):
  with create_pipe_input() as source:
   host=FrameworkHost(input=source,output=DummyOutput())
   try:
    host.scene.command(dict(op='draft',text='secret'));host.scene.command(dict(op='select',anchor=0,caret=6));host.scene.command(dict(op='key',key='F1'));before=host.scene.snapshot();clipboard=InMemoryClipboard();clipboard.set_text('previous')
    host.clipboard_action('copy',clipboard);host.clipboard_action('cut',clipboard);host.clipboard_action('paste',clipboard)
    self.assertEqual(clipboard.get_data().text,'previous');self.assertEqual(host.scene.snapshot(),before)
   finally:host.scene.close()
if __name__=='__main__':unittest.main()
