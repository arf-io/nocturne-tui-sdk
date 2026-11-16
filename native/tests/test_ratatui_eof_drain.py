"""Real PTY/subprocess drain regression; no mocked readiness or reads."""
import importlib.util,os,sys,subprocess,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class RatatuiEOFDrain(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('ratatui_qualification',ROOT/'native/hosts/ratatui/qualify.py');self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
    def test_actual_exit_drain_preserves_bytes_and_finishes_at_eof(self):
        import pty
        master,slave=pty.openpty()
        try:
            child=subprocess.Popen([sys.executable,'-c','import os;os.write(1,b"actual terminal bytes\\n")'],stdout=slave,stderr=slave,stdin=slave)
            self.assertEqual(child.wait(timeout=5),0)
            chunks=[];self.module.drainPending(master,chunks.append,time.monotonic()+2)
            self.assertIn(b'actual terminal bytes',b''.join(chunks))
            os.close(slave);slave=None
            self.module.drainPending(master,chunks.append,time.monotonic()+2)
        finally:
            os.close(master)
            if slave is not None:os.close(slave)
    def test_expired_deadline_rejects_readable_real_pty(self):
        import pty
        master,slave=pty.openpty()
        try:
            os.write(slave,b'pending bytes')
            with self.assertRaises(TimeoutError):self.module.drainPending(master,lambda data:None,time.monotonic()-1)
        finally:os.close(master);os.close(slave)
