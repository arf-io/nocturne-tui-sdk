#!/usr/bin/env python3
"""A real POSIX pseudo-terminal; no shell commands or live provider connections."""
import errno,fcntl,json,os,pty,re,select,signal,struct,subprocess,termios,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];signal.alarm(20)
master,slave=pty.openpty();before=termios.tcgetattr(slave)
fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
proc=subprocess.Popen(['node','examples/atelier_terminal.mjs','--scene','warp','--read-mode','--fps','1','--no-demo'],cwd=ROOT,stdin=slave,stdout=slave,stderr=slave,env={**os.environ,'TERM':'xterm-256color','COLORTERM':'truecolor'})
captured=bytearray();checks=[]
def drain(seconds=.15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if select.select([master],[],[],min(.015,max(0,end-time.monotonic())))[0]:
   try:captured.extend(os.read(master,65536))
   except OSError as e:
    if e.errno!=errno.EIO:raise

def text(data):return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',bytes(data).decode(errors='replace'))
def check(name,condition):
 assert condition,name+'\n'+text(captured[-2000:]);checks.append(name);print('PASS',name,flush=True)
def send(data,seconds=.16):os.write(master,data);drain(seconds)
try:
 drain(.6);check('raw mode and SGR drag tracking enabled',not(termios.tcgetattr(slave)[3]&termios.ICANON) and b'\x1b[?1002h' in captured)
 check('terminal starts with named camera shortcut and Hyperlane', 'CTRL+G' in text(captured) and 'OBLIQUE HYPERLANE' in text(captured))
 start=len(captured);send(b'Z',.13);check('first local glyph appears before a 1 FPS animation tick','Z' in text(captured[start:]))
 send(b'ebra');check('additional local text does not unpause animation',proc.poll() is None)
 start=len(captured);send(b'\x1b[1;3C');check('Alt-right camera event repaints while held',len(captured)>start and '[1;3C' not in text(captured[start:]))
 send(b'\x07');check('Ctrl+G exposes named in-terminal camera/action buttons','CAMERA / ACTION CONSOLE' in text(captured))
 # Three columns, 62 cells wide, anchored at x=56: BRAKE at local column 1 / row 4.
 start=len(captured);send(b'\x1b[<0;79;16M\x1b[<0;79;16m');check('actual SGR mouse button brakes velocity','BRAKE' in text(captured[start:]))
 send(b'\x1b');check('Escape dismisses console',proc.poll() is None)
 start=len(captured);send(b'\x0e');check('next scene opens automatic graph','Automatic 2D / 3D' in text(captured[start:]) or 'NODE INSPECTOR' in text(captured[start:]))
 send(b'\x0c');check('layout command remains responsive while motion held',proc.poll() is None)
 start=len(captured);send(b'\x1b[<0;45;22M\x1b[<32;49;24M\x1b[<0;49;24m');check('drag mouse packets never become typed text','[<32;' not in text(captured[start:]))
 fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,80,0,0));proc.send_signal(signal.SIGWINCH);drain(.16);check('viewport resize survives',proc.poll() is None)
 send(b'\x11',.3);proc.wait(timeout=3);check('Ctrl+Q clean exit',proc.returncode==0)
 check('termios restored exactly',termios.tcgetattr(slave)==before)
 check('mouse cursor wrap and alternate screen restored',all(s in captured for s in [b'\x1b[?1006l',b'\x1b[?1002l',b'\x1b[?25h',b'\x1b[?7h',b'\x1b[?1049l']))
finally:
 if proc.poll() is None:proc.terminate();proc.wait(timeout=3)
 for fd in [master,slave]:os.close(fd)
report={'status':'PASS','checks':checks,'count':len(checks),'bytesObserved':len(captured),'terminal':'POSIX PTY, not live tmux','providers':0};(ROOT/'dist/atelier/tty-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
