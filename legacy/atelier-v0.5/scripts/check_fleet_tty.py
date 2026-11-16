#!/usr/bin/env python3
"""Test Pearl Fleet in a POSIX pseudo-terminal with real NDJSON descriptors.
No actual agents, terminal multiplexer, network requests, or shell mutations.
"""
import errno,fcntl,json,os,pty,select,struct,subprocess,termios,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
master,slave=pty.openpty();before=termios.tcgetattr(slave)
fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
sourceRead,sourceWrite=os.pipe();commandRead,commandWrite=os.pipe()
proc=subprocess.Popen(['node','examples/fleet_terminal.mjs','--agent','atlas','--columns','120','--rows','40','--data-fd',str(sourceRead),'--commands-fd',str(commandWrite)],cwd=ROOT,stdin=slave,stdout=slave,stderr=slave,pass_fds=(sourceRead,commandWrite),env={**os.environ,'TERM':'xterm-256color','COLORTERM':'truecolor'})
checks=[];captured=bytearray();commands=bytearray()
def drain(seconds=.25):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  readable,_,_=select.select([master,commandRead],[],[],min(.04,max(0,end-time.monotonic())))
  for fd in readable:
   try:data=os.read(fd,65536)
   except OSError as e:
    if e.errno==errno.EIO:continue
    raise
   (captured if fd==master else commands).extend(data)
def check(name,value):
 assert value,name+'\n'+captured[-1800:].decode(errors='replace')
 checks.append(name)
def event(seq,kind,payload,agent='atlas'):
 os.write(sourceWrite,(json.dumps({'version':1,'seq':seq,'agentId':agent,'type':kind,'atMs':seq*100,'payload':payload})+'\n').encode());drain()
try:
 drain(.6);check('raw terminal and mouse modes enabled',b'\x1b[?1006h' in captured and not(termios.tcgetattr(slave)[3]&termios.ICANON))
 os.write(master,b'\x10');drain(.2)
 event(1,'telemetry',{'tokenRate':67,'latencyMs':123,'contextPermille':420,'queue':3,'tools':8,'progressPermille':670})
 event(2,'message.start',{'messageId':'pipe','role':'agent','text':'PIPE_MESSAGE_OK'})
 check('external data visible during paused decoration',b'PIPE_MESSAGE_OK' in captured)
 os.write(master,b'hello-from-pty\r');drain(.35)
 out=[json.loads(x) for x in commands.splitlines()];check('outbound note uses an explicit command descriptor',len(out)==1 and out[0]['text']=='hello-from-pty' and out[0]['agentId']=='atlas')
 # Screen row 5 is the agent tab strip. It remains pointer-accessible while paused.
 os.write(master,b'\x1b[<0;21;5M\x1b[<0;21;5m');drain(.2)
 os.write(master,b'prism-mouse-note\r');drain(.25)
 out=[json.loads(x) for x in commands.splitlines()];check('native SGR mouse selects agent workspace',len(out)==2 and out[-1]['agentId']=='prism')
 event(3,'message.delta',{'messageId':'missing','text':'must reject'})
 check('invalid message event does not terminate the host',proc.poll() is None)
 event(3,'status',{'status':'running'})
 check('host continues after validation error',proc.poll() is None)
 os.write(master,b'\x11');drain(.4);proc.wait(timeout=3)
 check('Ctrl+Q exits successfully',proc.returncode==0)
 check('TTY flags restored',termios.tcgetattr(slave)==before)
 check('mouse, cursor and alternate screen restored',b'\x1b[?1006l' in captured and b'\x1b[?25h' in captured and b'\x1b[?1049l' in captured)
finally:
 if proc.poll() is None:proc.kill();proc.wait()
 for fd in (master,slave,sourceRead,sourceWrite,commandRead,commandWrite):os.close(fd)
report={'suite':'Pearl Fleet POSIX PTY','status':'PASS','count':len(checks),'checks':checks,'bytesObserved':len(captured),'outboundCommands':len(out),'realAgentConnections':0}
(ROOT/'dist/fleet/tty-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
