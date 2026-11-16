"""Run the real terminal demo in a pseudo-tty; check input, pause, exit, restoration."""
from pathlib import Path
import fcntl
import json
import os
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import time
ROOT=Path(__file__).resolve().parents[1]
master,slave=pty.openpty()
fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,160,0,0))
before=termios.tcgetattr(slave)
process=subprocess.Popen([sys.executable,str(ROOT/'examples/terminal_demo.py'),'--preset','quiet-machinery'],stdin=slave,stdout=slave,stderr=subprocess.PIPE,cwd=ROOT)
allOutput=bytearray()
def drain(seconds):
    end=time.monotonic()+seconds
    result=bytearray()
    while time.monotonic()<end:
        ready,_,_=select.select([master],[],[],max(0,end-time.monotonic()))
        if ready:
            try:result.extend(os.read(master,262144))
            except OSError:break
    allOutput.extend(result)
    return bytes(result)
try:
    deadline=time.monotonic()+8
    while b'\x1b[?1049h' not in allOutput and time.monotonic()<deadline:
        drain(.1)
        if process.poll() is not None:raise RuntimeError(process.stderr.read().decode())
    assert b'\x1b[?1049h' in allOutput, ('Terminal did not start',bytes(allOutput))
    os.write(master,b'\x10')
    paused=drain(.15)
    if process.poll() is not None: raise RuntimeError(process.stderr.read().decode())
    sampleBefore=re.findall(rb'motion (\d+)',paused)[-1]
    os.write(master,b'\x0cinstant data while paused')
    edited=drain(.15)
    sampleAfter=re.findall(rb'motion (\d+)',edited)[-1]
    assert sampleBefore==sampleAfter,(sampleBefore,sampleAfter)
    visible=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',edited)
    assert b'instant data while paused' in visible,visible[-2000:]
    os.write(master,b'\x11')
    drain(.15)
    process.wait(timeout=2)
    assert process.returncode==0,process.stderr.read().decode()
    assert b'\x1b[?1049h' in allOutput and b'\x1b[?1049l' in allOutput
    assert termios.tcgetattr(slave)==before
    results={'passed':True,'checks':['interactive pseudo-tty','pause preserves motion sample','typing draws while paused','Ctrl+Q exits with flow control disabled','alternate-screen cleanup','tty attributes restored']}
    (ROOT/'dist/tty-test-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
finally:
    if process.poll() is None:process.kill();process.wait()
    os.close(master);os.close(slave)
