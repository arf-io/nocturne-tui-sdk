from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hosts/python'))
from prompt_toolkit_host import FrameworkHost
from prompt_toolkit.application.current import set_app
from prompt_toolkit.layout.screen import Screen,WritePosition
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.output import DummyOutput
class FrameworkUnicode(unittest.TestCase):
 def testFrameworkScreenKeepsWholeClusterAndNativeWidth(self):
  host=FrameworkHost(output=DummyOutput(),unicode_document=True);self.addCleanup(host.scene.close)
  host.scene.command(dict(op='draft',text='א́👩‍🔧ב',emitWeather=False));host.scene.command(dict(op='resize',width=20,height=8));before=host.scene.snapshot()
  screen=Screen()
  with set_app(host.application):host.document_window.write_to_screen(screen,MouseHandlers(),WritePosition(0,0,20,8),'',True,None)
  self.assertEqual(screen.data_buffer[1][0].char,'ב');self.assertEqual(screen.data_buffer[1][1].char,'👩‍🔧');self.assertEqual(screen.data_buffer[1][1].width,2);self.assertEqual(screen.data_buffer[1][2].char,'');self.assertEqual(screen.data_buffer[1][3].char,'א́');self.assertEqual(host.scene.snapshot(),before)
 def testFrameworkScreenPaintsNativeSelection(self):
  host=FrameworkHost(output=DummyOutput(),unicode_document=True);self.addCleanup(host.scene.close)
  host.scene.command(dict(op='draft',text='אב',emitWeather=False));host.scene.command(dict(op='select',anchor=0,caret=1))
  screen=Screen()
  with set_app(host.application):host.document_window.write_to_screen(screen,MouseHandlers(),WritePosition(0,0,20,8),'',True,None)
  self.assertIn('bg:#43637f',screen.data_buffer[1][1].style)
if __name__=='__main__':unittest.main()
