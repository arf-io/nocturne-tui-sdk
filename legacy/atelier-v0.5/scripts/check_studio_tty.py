"""PTY test: input/data during pause, mouse selection, modes restored on exit."""
import os,pty,subprocess,fcntl,termios,struct,time,select,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/studio';OUT.mkdir(exist_ok=True)
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,100,0,0));initial=termios.tcgetattr(slave);readfd,writefd=os.pipe();path=OUT/'tty-metrics.json'
proc=subprocess.Popen([sys.executable,str(ROOT/'examples/studio_terminal.py'),'--scene','controls','--data-fd',str(readfd),'--metrics',str(path)],stdin=slave,stdout=slave,stderr=slave,pass_fds=(readfd,));os.close(readfd);output=bytearray()
def drain(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if select.select([master],[],[],.02)[0]:
   try:output.extend(os.read(master,65536))
   except OSError:break
try:
 deadline=time.monotonic()+6
 while b'\x1b[?2004h' not in output and time.monotonic()<deadline:drain(.04)
 assert b'\x1b[?2004h' in output,'terminal did not signal readiness'
 drain(.12);os.write(master,b'\x10');drain(.12) # Ctrl+P pause
 os.write(master,b'hello');drain(.10);os.write(writefd,b'{"type":"value","value":830}\n');drain(.10)
 os.write(master,b'\x1b[<0;7;11M');drain(.10);os.write(master,b'\x1b');drain(.10);os.write(master,b'\x11');drain(.1)
 proc.wait(timeout=4);assert proc.returncode==0,output[-2000:]
 metrics=json.loads(path.read_text());assert metrics['text']=='hello',metrics;assert metrics['value']==830,metrics;assert metrics['dataCommits']>=6,metrics;assert not metrics['playing'],metrics
 assert termios.tcgetattr(slave)==initial,'termios not restored';assert b'\x1b[?1049l' in output,'alternate screen not exited';assert b'\x1b[?1006l' in output,'mouse mode not disabled';assert b'Traceback' not in output
 report=dict(status='PASS',receivedBytes=len(output),dataWhilePaused=True,mouseSequenceAccepted=True,termiosRestored=True,metrics=metrics);(OUT/'tty-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:
 if proc.poll() is None:proc.kill();proc.wait()
 for fd in (master,slave,writefd):os.close(fd)
