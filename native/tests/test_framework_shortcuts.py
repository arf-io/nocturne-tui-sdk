"""Actual Prompt Toolkit routing harnesses queued for the combined text gate."""
from pathlib import Path
import sys,unittest,asyncio
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hosts/python'))
from prompt_toolkit_host import FrameworkHost
from shortcut_profile import ShortcutProfile,FUNCTION,parse_reservations
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.clipboard import InMemoryClipboard
class FrameworkShortcuts(unittest.TestCase):
 def test_registered_fallback_clipboard_and_quit_delivery(self):
  with create_pipe_input() as source:
   host=FrameworkHost(input=source,output=DummyOutput(),reserved_shortcuts=parse_reservations(['Ctrl+q','Alt+w','Ctrl+w','Ctrl+y']))
   try:
    self.assertIn('Quit: Alt+q',host.shortcut_profile.hints);self.assertIn('Copy: Alt+c',host.shortcut_profile.hints)
    host.scene.command(dict(op='draft',text='Aé日本Z',caret=5,emitWeather=False));host.scene.command(dict(op='select',anchor=1,caret=5))
    async def execute():
     task=asyncio.create_task(host.application.run_async())
     try:
      await asyncio.sleep(.05);source.send_bytes(b'\x1bc\x1bx\x1bv\x1bq');await asyncio.wait_for(task,3)
     finally:
      if not task.done():task.cancel()
    asyncio.run(execute());self.assertEqual(host.application.clipboard.get_data().text,'é日本');self.assertEqual(host.scene.info()['prompt']['text'],'Aé日本Z')
   finally:host.scene.close()
 def test_unassigned_actions_have_no_registered_shortcut(self):
  with create_pipe_input() as source:
   host=FrameworkHost(input=source,output=DummyOutput(),reserved_shortcuts=parse_reservations(['Ctrl+q','Alt+q','F2','F3']))
   try:
    self.assertIn('Quit: unassigned',host.shortcut_profile.hints);self.assertIn('Hold: unassigned',host.shortcut_profile.hints)
    self.assertNotIn(1,[a for a,_ in host.shortcut_profile.bindings]);self.assertNotIn(2,[a for a,_ in host.shortcut_profile.bindings])
    from prompt_toolkit.keys import Keys
    self.assertFalse(any(b.keys==(Keys.ControlQ,) for b in host.application.key_bindings.bindings))
    self.assertFalse(any(b.keys==(Keys.F2,) for b in host.application.key_bindings.bindings))
    self.assertTrue(host.application.key_bindings.get_bindings_for_keys((Keys.ControlC,)))
   finally:host.scene.close()
 def test_remapped_help_reader_hold_and_scene_keep_source(self):
  with create_pipe_input() as source:
   host=FrameworkHost(input=source,output=DummyOutput(),reserved_shortcuts=parse_reservations(['F1','F2','F4','F6']))
   try:
    self.assertEqual(host.shortcut_profile.action_for(FUNCTION+7,0),7);self.assertEqual(host.shortcut_profile.action_for(FUNCTION+8,0),8)
    app=SimpleNamespace(clipboard=InMemoryClipboard(),invalidate=lambda:None);event=SimpleNamespace(app=app)
    host.scene.command(dict(op='draft',text='retained é',emitWeather=False));host.shortcut_action(2,event);self.assertTrue(host.held)
    host.shortcut_action(3,event);self.assertEqual(host.scene.info()['prompt']['text'],'retained é')
    host.shortcut_action(7,event);self.assertNotEqual(host.scene.info()['inputOwner'],'prompt')
    host.shortcut_action(4,event);self.assertEqual(app.clipboard.get_data().text,'')
    host.scene.command(dict(op='key',key='Escape'));host.shortcut_action(8,event);self.assertEqual(host.scene.info()['prompt']['text'],'retained é')
   finally:host.scene.close()
 def test_invalid_reservations_reject_explicitly(self):
  with self.assertRaises(ValueError):parse_reservations(['Ctrl+imaginary'])
