"""Harness tests are not framework qualification; use the real host gate for that."""
import importlib.util,sys,unittest,tempfile,os
from unittest.mock import patch
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from dependency_pty import PtyProbe,TerminalScreen
class ScreenTests(unittest.TestCase):
 def test_incremental_unicode_and_cursor(self):
  s=TerminalScreen(12,4)
  for b in 'é\x1b[2;3HX'.encode():s.feed(bytes([b]))
  self.assertEqual(s.lines()[0][0],'é');self.assertEqual(s.lines()[1][2],'X')
 def test_mode_state_requires_last_restoration(self):
  s=TerminalScreen(12,4);s.feed(b'\x1b[?1049h\x1b[?25l\x1b[?1049l\x1b[?25h\x1b[?1049h')
  self.assertTrue(s.modes[1049]);self.assertTrue(s.modes[25])
 def test_unknown_control_rejects(self):
  with self.assertRaises(ValueError):TerminalScreen(12,4).feed(b'\x1b[123z')
 def test_reset_erase_and_query(self):
  s=TerminalScreen(12,4);s.feed(b'abcd\r\x1b[2KX\x1b]11;?\x07\x1b[6n')
  self.assertEqual(s.lines()[0].rstrip(),'X')
class ProcessTests(unittest.TestCase):
 def test_empty_read_marks_terminal_eof_instead_of_spinning(self):
  p=object.__new__(PtyProbe);p.master=-1;p.output=bytearray();p.eof=False
  p.screen=TerminalScreen(12,4)
  with patch('select.select',return_value=([-1],[],[])),patch('os.read',return_value=b''):
   p.drain()
  self.assertTrue(p.eof)
 def test_exited_child_raw_mode_remains_observable_without_parent_restoration(self):
  with tempfile.TemporaryDirectory() as td:
   p=PtyProbe([sys.executable,'-c','import tty;tty.setraw(0)'],Path(td),os.environ.copy(),Path(td),'unrestored',3)
   try:
    p.child.wait(timeout=3)
    self.assertTrue(p.raw())
   finally:p.close()
   self.assertFalse(p.result['terminalAttributesRestoredByChild'])
   self.assertFalse(p.result['accepted'])
 def test_early_exit_is_not_raw_terminal_acceptance(self):
  with tempfile.TemporaryDirectory() as td:
   p=PtyProbe([sys.executable,'-c','pass'],Path(td),os.environ.copy(),Path(td),'early',3)
   try:
    with self.assertRaises(AssertionError):p.waitReady()
   finally:p.close()
   self.assertFalse(p.result['accepted']);self.assertFalse(p.result['rawModeObserved'])
 def test_lifetime_timeout_not_pass(self):
  with tempfile.TemporaryDirectory() as td:
   p=PtyProbe([sys.executable,'-c','import time;time.sleep(20)'],Path(td),os.environ.copy(),Path(td),'timeout',0.1)
   try:
    with self.assertRaises(TimeoutError):p.waitReady()
   finally:p.close()
   self.assertTrue(p.result['parentForcedCleanup']);self.assertFalse(p.result['accepted'])

class LaunchFailureTests(unittest.TestCase):
 def test_missing_executable_is_terminal_blocked_receipt_without_fd_leak(self):
  import json
  with tempfile.TemporaryDirectory() as td:
   fdDirectory='/proc/self/fd' if Path('/proc/self/fd').is_dir() else '/dev/fd'
   before=set(os.listdir(fdDirectory))
   with self.assertRaises(FileNotFoundError):
    PtyProbe([str(Path(td)/'missing-binary')],Path(td),os.environ.copy(),Path(td),'missing',2)
   self.assertEqual(set(os.listdir(fdDirectory)),before)
   r=json.loads((Path(td)/'missing.json').read_text())
   self.assertEqual(r['status'],'BLOCKED');self.assertIsNone(r['exitCode']);self.assertFalse(r['accepted'])
 def test_invalid_bubbletea_cli_never_leaves_running_directory(self):
  import subprocess
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'not-created'
   result=subprocess.run([sys.executable,str(SCRIPTS/'check_dependency_hosts.py'),'--host','bubbletea','--evidence-dir',str(out)],capture_output=True,timeout=5)
   self.assertNotEqual(result.returncode,0);self.assertFalse(out.exists())

if __name__=='__main__':unittest.main(verbosity=2)
