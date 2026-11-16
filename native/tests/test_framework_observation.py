"""Actual PTY harness negative test; this fixture is not a framework qualification."""
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class FrameworkObservation(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('prompt_toolkit'),'prompt_toolkit unavailable')
    def testControllingTerminalAndUnrestoredRawModeAreObserved(self):
        specification=importlib.util.spec_from_file_location('framework_observation',ROOT/'scripts/check_framework.py')
        module=importlib.util.module_from_spec(specification);specification.loader.exec_module(module)
        script='''import os,tty
fd=os.open('/dev/tty',os.O_RDWR);os.close(fd)
tty.setraw(0)
os.write(1,b'CONTROLLING_TTY_OBSERVED\\x1b[?1049hNOCTURNE')
data=b''
while b'\\x11' not in data:
 chunk=os.read(0,4096)
 if not chunk:break
 data+=chunk;os.write(1,chunk)
os.write(1,b'\\x1b[?1049l')
'''
        realPopen=subprocess.Popen
        def brokenChild(argv,**kwargs):
            return realPopen([sys.executable,'-c',script],**kwargs)
        with tempfile.TemporaryDirectory() as temporary:
            module.ROOT=Path(temporary);(module.ROOT/'evidence').mkdir()
            with patch.object(module.subprocess,'Popen',side_effect=brokenChild):
                self.assertEqual(module.main(),2)
            report=json.loads((module.ROOT/'evidence/framework.json').read_text())
            check=next(c for c in report['checks'] if c['name']=='terminal attributes restored')
            self.assertEqual(check['status'],'FAIL','unrestored raw mode cannot pass')
            self.assertFalse(report['passed'])
            self.assertIn(b'CONTROLLING_TTY_OBSERVED',(module.ROOT/'evidence/framework-output.bin').read_bytes())
if __name__=='__main__':unittest.main()
