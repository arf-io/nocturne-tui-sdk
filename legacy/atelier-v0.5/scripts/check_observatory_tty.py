#!/usr/bin/env python3
"""Exercise Observatory with a real POSIX TTY, but no hardware or providers."""
import errno,fcntl,json,os,pty,re,select,struct,subprocess,termios,time,signal
signal.alarm(15)
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
master,slave=pty.openpty();before=termios.tcgetattr(slave)
fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
r,w=os.pipe();checks=[];captured=bytearray()
proc=subprocess.Popen(['node','examples/observatory_terminal.mjs','--read-mode','--fps','1','--scene','chat','--sensor-fd',str(r)],cwd=ROOT,stdin=slave,stdout=slave,stderr=slave,pass_fds=(r,),env={**os.environ,'TERM':'xterm-256color','COLORTERM':'truecolor'})
def drain(seconds=.2):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  ready,_,_=select.select([master],[],[],min(.015,max(0,end-time.monotonic())))
  if ready:
   try:captured.extend(os.read(master,65536))
   except OSError as e:
    if e.errno!=errno.EIO:raise

def text(data):return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',bytes(data).decode(errors='replace'))
def check(name,value):
 assert value,name+'\n'+text(captured[-1800:]);checks.append(name)
def send(row):os.write(w,(json.dumps(row)+'\n').encode());drain(.12)
try:
 drain(.6);check('raw mode, alternate screen and SGR mouse enabled',not(termios.tcgetattr(slave)[3]&termios.ICANON) and b'\x1b[?1006h' in captured)
 start=len(captured);os.write(master,b'Z');drain(.14)
 check('first typed character appears while motion is held at a 1 FPS ceiling','Z' in text(captured[start:]))
 check('typing does not require a motion deadline',proc.poll() is None)
 os.write(master,b'ebra\r');drain(.2);check('submitted local note appears without external execution','Zebra' in text(captured))
 send({'source':'fixture.temperature','value':41,'seq':1,'atMs':0,'unit':'C','quality':'external'});check('inherited scalar input remains responsive',proc.poll() is None)
 send({'type':'waveform','source':'fixture.audio','seq':1,'atMs':0,'samples':[0,.2,-.3,.7,-.2,0],'quality':'external'});check('waveform input accepted during held motion',proc.poll() is None)
 send({'source':'fixture.temperature','value':None,'seq':2,'atMs':0});check('invalid sensor record is visibly rejected','INPUT:' in text(captured))
 send({'source':'fixture.temperature','value':42,'seq':2,'atMs':0,'unit':'C'});check('valid later sample survives invalid predecessor',proc.poll() is None)
 # Click empty space: mouse bytes must not become draft text.
 start=len(captured);os.write(master,b'\x1b[<0;117;35M\x1b[<0;117;35m');drain(.12);check('SGR mouse is demultiplexed from text','[<0;117;35' not in text(captured[start:]))
 fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',28,90,0,0));proc.send_signal(__import__('signal').SIGWINCH);drain(.12);check('resize does not terminate the host',proc.poll() is None)
 os.write(master,b'\x11');drain(.25);proc.wait(timeout=3);check('Ctrl+Q exits successfully',proc.returncode==0)
 check('terminal attributes restored',termios.tcgetattr(slave)==before)
 check('cursor, mouse and alternate screen restored',all(x in captured for x in [b'\x1b[?1006l',b'\x1b[?25h',b'\x1b[?1049l']))
finally:
 if proc.poll() is None:proc.kill();proc.wait()
 for fd in (master,slave,r,w):os.close(fd)
report={'status':'PASS','count':len(checks),'checks':checks,'bytesObserved':len(captured),'hardwareTested':False};(ROOT/'dist/observatory/tty-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
