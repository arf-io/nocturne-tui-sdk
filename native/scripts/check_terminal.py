#!/usr/bin/env python3
"""Real PTY qualification of the shipped direct-Python/C terminal host."""
from pathlib import Path
import os,pty,fcntl,struct,termios,subprocess,selectors,time,json,sys,re
ROOT=Path(__file__).resolve().parents[1]
def main():
 master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',30,96,0,0));terminal=master if sys.platform=='darwin' else slave;before=termios.tcgetattr(terminal);out=bytearray();sel=selectors.DefaultSelector();sel.register(master,selectors.EVENT_READ)
 report=ROOT/'evidence/terminal-state.json';checks=[]
 def control():os.setsid();fcntl.ioctl(slave,termios.TIOCSCTTY,0)
 proc=subprocess.Popen([sys.executable,str(ROOT/'examples/terminal.py'),'--scene','flight','--fps','1','--paused','--info-on-exit',str(report)],stdin=slave,stdout=slave,stderr=slave,cwd=ROOT,preexec_fn=control)
 def drain(seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if sel.select(max(0,min(.02,end-time.monotonic()))):
    try:out.extend(os.read(master,65536))
    except OSError:break
 def check(name,condition):checks.append({'name':name,'status':'PASS'if condition else'FAIL'})
 try:
  readyDeadline=time.monotonic()+8
  while b'NOCTURNE'not in out and time.monotonic()<readyDeadline and proc.poll()is None:drain(.03)
  drain(.08);check('actual host started in alternate screen',b'\x1b[?1049h'in out and b'NOCTURNE'in out)
  marker=len(out);start=time.monotonic();os.write(master,b'FIRST');drain(.25);elapsed=time.monotonic()-start
  check('input visibly rendered before 1 FPS deadline',b'FIRST'in re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',out[marker:]) and elapsed<.8)
  os.write(master,b'\x01X\x05Z');drain(.2)
  os.write(master,b'\x1b[<0;50;12M\x1b[<32;65;15M\x1b[<0;65;15m');drain(.2)
  fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,100,0,0));drain(.2)
  os.write(master,b'\x11')
  deadline=time.monotonic()+5
  while proc.poll()is None and time.monotonic()<deadline:drain(.05)
  check('clean exit',proc.poll()==0)
  if proc.poll()is None:proc.kill();proc.wait()
  drain(.05);check('terminal attributes restored',termios.tcgetattr(terminal)==before)
  check('cursor and mouse released',b'\x1b[?1006l'in out and b'\x1b[?25h'in out and b'\x1b[?1049l'in out)
  info=json.loads(report.read_text())if report.exists()else{}
  check('Ctrl-A and Ctrl-E modify true endpoints',info.get('prompt',{}).get('text')=='XFIRSTZ')
  check('resize reaches native render',info.get('hostViewport')==[100,32])
  check('held simulation unchanged',info.get('clock',{}).get('timeUs')==0)
  check('camera moves without keynav or click weather',info.get('camera',{}).get('yaw')!=-24 and info.get('fieldCount')==7)
 finally:
  if proc.poll()is None:proc.kill();proc.wait()
  sel.close();os.close(master);os.close(slave)
 result={'scope':'Actual direct ctypes/C host in a controlling PTY; no physical terminal claim.','checks':checks,'passed':all(c['status']=='PASS'for c in checks),'capturedBytes':len(out)}
 (ROOT/'evidence/terminal-output.bin').write_bytes(out);(ROOT/'evidence/terminal.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed']else 2
if __name__=='__main__':raise SystemExit(main())
