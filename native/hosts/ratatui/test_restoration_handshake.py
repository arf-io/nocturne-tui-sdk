"""Actual compiled host and real terminal cleanup; no mocks."""
import importlib.util,json,os,pty,tempfile,termios,time,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('qualification',Path(__file__).with_name('qualify.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
class RestorationHandshake(unittest.TestCase):
    def test_actual_host_restores_before_session_exit(self):
        binary=Path(os.environ['NOCTURNE_RATATUI_TEST_BINARY'])
        with tempfile.TemporaryDirectory() as temporary:
            r=q.runPty('restoration-handshake',binary,Path(temporary),dict(os.environ,TERM='xterm-256color'),10,None)
            self.assertEqual(r['status'],'PASS',r.get('reason'));self.assertTrue(r['terminalAttributesRestoredByChild']);self.assertTrue(r['restorationObservedBeforeExit']);self.assertEqual(r['exitCode'],0)
    def test_failed_actual_child_retains_terminal_receipt(self):
        binary=Path(os.environ['NOCTURNE_RATATUI_TEST_BINARY'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            r=q.runPty('failed-child',binary,root,dict(os.environ,TERM='xterm-256color'),5,None,failure='invalid')
            self.assertEqual(r['status'],'FAIL');self.assertEqual(json.loads((root/'failed-child.json').read_text())['status'],'FAIL')
    def test_revoked_terminal_cleanup_returns_error(self):
        master,slave=pty.openpty();before=termios.tcgetattr(slave);os.close(slave)
        try:self.assertIsInstance(q.restoreParentTerminal(slave,before),str)
        finally:os.close(master)
if __name__=='__main__':unittest.main()
