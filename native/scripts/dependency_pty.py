#!/usr/bin/env python3
"""Bounded real-PTY observation for dependency-backed SDK hosts.

This is not a terminal implementation or a substitute framework. It decodes only
observed terminal output needed by these fixtures and rejects unknown controls.
All termios comparisons happen before isolated parent rescue. No sleeps imply PASS.
"""
from __future__ import annotations
import codecs,datetime,hashlib,json,math,os,re,signal,subprocess,sys,time
from pathlib import Path
MAX_BYTES=32*1024*1024
ENV_KEYS=('PATH','TERM','LANG','COLORTERM','GOFLAGS','GOPROXY','GOSUMDB','GOMODCACHE','GOCACHE','GOTOOLCHAIN','LD_LIBRARY_PATH','CGO_LDFLAGS','CARGO_NET_OFFLINE')
def digest(path:Path)->str:
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def writeJson(path:Path,value:dict)->None:
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)
def timestamp()->str:return datetime.datetime.now(datetime.timezone.utc).isoformat()

class TerminalScreen:
 """Observe single-cell text/cursor and last DEC mode values from bounded VT output."""
 def __init__(self,width:int,height:int):
  self.decoder=codecs.getincrementaldecoder('utf-8')('replace');self.pending='';self.modes={};self.entered=set();self.queries=[];self.resize(width,height)
 def resize(self,width:int,height:int)->None:
  if not (1<=width<=1000 and 1<=height<=1000):raise ValueError('screen bound')
  self.width=width;self.height=height;self.x=self.y=0;self.cells=[[' ']*width for _ in range(height)]
 def lines(self)->list[str]:return [''.join(r) for r in self.cells]
 def feed(self,data:bytes)->None:
  self.pending+=self.decoder.decode(data)
  while self.pending:
   if self.pending.startswith('\x1b['):
    m=re.match(r'\x1b\[([0-?]*)([ -/]*)([@-~])',self.pending)
    if not m:
     if len(self.pending)>1024:raise ValueError('unterminated CSI')
     return
    args,inter,final=m.groups();self.pending=self.pending[m.end():]
    if args.startswith('?') and final in 'hl':
     for code in args[1:].split(';'):
      key=int(code);on=final=='h';self.modes[key]=on
      if on:self.entered.add(key)
      if key==1049 and on:self.resize(self.width,self.height)
     continue
    if final in 'nct' and (args.startswith('>') or not inter):self.queries.append(args+final);continue
    if final=='q' and inter==' ':continue # cursor style
    if inter:raise ValueError('unknown CSI intermediate '+inter+final)
    vs=[int(v) if v else 0 for v in args.split(';')];a=vs[0] if vs else 0;n=a or 1
    if final in 'Hf':self.y=min(self.height-1,max(0,n-1));self.x=min(self.width-1,max(0,(vs[1] if len(vs)>1 and vs[1] else 1)-1))
    elif final=='A':self.y=max(0,self.y-n)
    elif final in 'Be':self.y=min(self.height-1,self.y+n)
    elif final in 'Ca':self.x=min(self.width-1,self.x+n)
    elif final=='D':self.x=max(0,self.x-n)
    elif final=='G':self.x=min(self.width-1,n-1)
    elif final=='d':self.y=min(self.height-1,n-1)
    elif final=='J' and a in (0,1,2,3):
     if a in (2,3):self.cells=[[' ']*self.width for _ in range(self.height)]
     elif a==0:
      for y in range(self.y,self.height):
       start=self.x if y==self.y else 0;self.cells[y][start:]=[' ']*(self.width-start)
     else:
      for y in range(self.y+1):
       end=self.x+1 if y==self.y else self.width;self.cells[y][:end]=[' ']*end
    elif final=='K' and a in (0,1,2):
     start,end=(self.x,self.width) if a==0 else ((0,self.x+1) if a==1 else (0,self.width));self.cells[self.y][start:end]=[' ']*(end-start)
    elif final=='m':pass
    elif final in 'hl' and a==4:pass
    else:raise ValueError('unsupported CSI '+args+final)
    continue
   if self.pending.startswith('\x1b]'):
    m=re.search(r'\x07|\x1b\\',self.pending[2:])
    if not m:
     if len(self.pending)>4096:raise ValueError('unterminated OSC')
     return
    end=2+m.end();self.queries.append(self.pending[:end]);self.pending=self.pending[end:];continue
   if self.pending.startswith(('\x1b(','\x1b)')):
    if len(self.pending)<3:return
    if self.pending[2] not in 'B0':raise ValueError('unknown charset')
    self.pending=self.pending[3:];continue
   if self.pending.startswith(('\x1b=','\x1b>')):self.pending=self.pending[2:];continue
   if self.pending=='\x1b':return
   ch,self.pending=self.pending[0],self.pending[1:]
   if ch=='\x1b':raise ValueError('unsupported escape')
   if ch=='\r':self.x=0
   elif ch=='\n':self.y=min(self.height-1,self.y+1)
   elif ch=='\b':self.x=max(0,self.x-1)
   elif ch=='\t':self.x=min(self.width-1,(self.x//8+1)*8)
   elif ch=='\x07':pass
   elif ord(ch)<32:raise ValueError('unsupported control '+repr(ch))
   else:
    if self.x>=self.width:self.x=0;self.y=min(self.height-1,self.y+1)
    self.cells[self.y][self.x]=ch;self.x+=1

class PtyProbe:
 """Own one controlling Linux/POSIX PTY child and its exact terminal observations.

 Inputs: actual executable argv/cwd/env, new evidence paths, finite deadline.
 Call waitReady(), exercise input and then finish(expectedCode). Always close().
 close() records any necessary forced cleanup and cannot turn a failure into PASS.
 """
 def __init__(self,argv:list[str],cwd:Path,env:dict[str,str],out:Path,name:str,timeout:float=15):
  import fcntl,pty,struct,termios
  if not math.isfinite(timeout) or timeout<=0:raise ValueError('deadline')
  if not re.fullmatch(r'[A-Za-z0-9_-]+',name):raise ValueError('name')
  self.out=out;self.name=name;self.receipt=out/(name+'.json');self.trace=out/(name+'.trace.jsonl')
  if self.receipt.exists() or self.trace.exists():raise FileExistsError(self.receipt)
  out.mkdir(parents=True,exist_ok=True);self.master,self.slave=pty.openpty()
  # Darwin invalidates slave-side termios ioctls when the controlling session
  # exits. The master still exposes the real terminal attributes, including an
  # un-restored raw mode. Observe that device, never substitute saved attributes.
  self.terminalFd=self.master if sys.platform=='darwin' else self.slave
  fcntl.ioctl(self.slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0));self.before=termios.tcgetattr(self.terminalFd)
  self.started=time.monotonic();self.deadline=self.started+timeout;self.output=bytearray();self.screen=TerminalScreen(80,24);self.closed=False;self.eof=False
  env=dict(env,TERM='xterm-256color',LANG='C.UTF-8',COLORTERM='truecolor',NOCTURNE_TEST_TRACE=str(self.trace))
  self.result={'id':name,'argv':argv,'cwd':str(cwd),'timeoutSeconds':timeout,'startedAt':timestamp(),'status':'RUNNING','accepted':False,'checks':[],'rawModeObserved':False,'parentForcedCleanup':False,'environment':{k:env[k] for k in ENV_KEYS if k in env}}
  writeJson(self.receipt,self.result)
  def control():os.setsid();fcntl.ioctl(self.slave,termios.TIOCSCTTY,0)
  try:
   self.child=subprocess.Popen(argv,cwd=cwd,env=env,stdin=self.slave,stdout=self.slave,stderr=self.slave,preexec_fn=control,close_fds=True)
  except BaseException as error:
   # No child accepted the terminal. Close both allocated descriptors and leave
   # a terminal receipt instead of an orphan RUNNING claim.
   os.close(self.master);os.close(self.slave);self.closed=True
   self.result.update(status='BLOCKED' if isinstance(error,OSError) else 'INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAIL',
                      exitCode=None,reason=repr(error),finishedAt=timestamp(),seconds=round(time.monotonic()-self.started,6))
   writeJson(self.receipt,self.result);raise
  self.result['pid']=self.child.pid;writeJson(self.receipt,self.result)
 def drain(self,wait:float=0)->None:
  import select
  if self.eof:return
  if select.select([self.master],[],[],wait)[0]:
   try:data=os.read(self.master,65536)
   except OSError as e:
    if e.errno==5:self.eof=True;return
    raise
   if not data:self.eof=True;return
   self.output.extend(data)
   if len(self.output)>MAX_BYTES:raise AssertionError('transcript bound exceeded')
   self.screen.feed(data)
 def raw(self)->bool:
  import termios
  a=termios.tcgetattr(self.terminalFd)
  result=not(a[3]&(termios.ICANON|termios.ECHO|termios.ISIG)) and not(a[0]&termios.IXON)
  if result:self.result['rawModeObserved']=True
  return result
 def wait(self,predicate,message:str)->None:
  while not predicate():
   if time.monotonic()>=self.deadline:raise TimeoutError(message)
   self.drain(min(.03,max(0,self.deadline-time.monotonic())))
   if self.child.poll() is not None:
    self.drain()
    if not predicate():raise AssertionError(f'{message}; child exited {self.child.returncode}')
  self.result['checks'].append(message)
 def waitReady(self,title:str='NOCTURNE')->None:
  self.wait(lambda:self.raw() and self.screen.modes.get(1049) is True and self.screen.modes.get(25) is False and self.visible(title),'raw/alternate-screen/hidden-cursor and actual native frame')
 def send(self,data:bytes)->None:
  import select
  remaining=memoryview(data)
  while remaining:
   if time.monotonic()>=self.deadline:raise TimeoutError('input write')
   if select.select([],[self.master],[],.03)[1]:remaining=remaining[os.write(self.master,remaining):]
 def resize(self,width:int,height:int)->None:
  import fcntl,struct,termios
  self.screen.resize(width,height);fcntl.ioctl(self.slave,termios.TIOCSWINSZ,struct.pack('HHHH',height,width,0,0));os.kill(self.child.pid,signal.SIGWINCH)
 def visible(self,text:str)->bool:return text in '\n'.join(self.screen.lines())
 def records(self)->list[dict]:
  if not self.trace.exists():return []
  raw=self.trace.read_bytes()
  if len(raw)>MAX_BYTES:raise AssertionError('trace bound')
  return [json.loads(s) for s in raw.split(b'\n')[:-1] if s]
 def info(self)->dict:
  rows=self.records();return rows[-1].get('info',{}) if rows else {}
 def finish(self,code:int=0)->None:
  import select,termios
  self.result['expectedExitCode']=code
  self.wait(lambda:self.child.poll() is not None,'actual child exit');self.child.wait()
  while not self.eof and select.select([self.master],[],[],0)[0]:
   if time.monotonic()>=self.deadline:raise TimeoutError('terminal drain after child exit')
   self.drain()
  after=termios.tcgetattr(self.terminalFd);self.result['terminalAttributesRestoredByChild']=after==self.before
  assert self.result['rawModeObserved'],'no actual raw entry'
  assert after==self.before,'exact termios not restored by child'
  assert self.child.returncode==code,f'expected exit {code}, got {self.child.returncode}'
  assert self.screen.modes.get(1049) is False,'alternate screen not restored'
  assert self.screen.modes.get(25) is True,'cursor not restored'
  for mode in (1000,1002,1003,1004,1006,2004):
   if mode in self.screen.entered:assert self.screen.modes.get(mode) is False,f'input mode {mode} not restored'
  self.result.update(status='PASS',accepted=True,expectedExitCode=code,finalInfo=self.info())
  self.result['checks'].append('exact termios, alternate screen, cursor and enabled input modes restored by child')
 def close(self)->None:
  import termios
  if self.closed:return
  self.closed=True
  if self.child.poll() is None:
   self.result['parentForcedCleanup']=True
   try:os.killpg(self.child.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   self.child.wait()
  self.result['exitCode']=self.child.returncode
  self.result.setdefault('terminalAttributesRestoredByChild',termios.tcgetattr(self.terminalFd)==self.before)
  if not self.result['accepted'] and self.result['status']=='RUNNING':self.result['status']='FAIL'
  self.result['finalModes']=self.screen.modes;self.result['enabledModes']=sorted(self.screen.entered)
  # Rescue only our isolated PTY after taking the acceptance measurements.
  termios.tcsetattr(self.terminalFd,termios.TCSANOW,self.before);os.close(self.master);os.close(self.slave)
  path=self.out/(self.name+'.terminal.bin');path.write_bytes(self.output)
  self.result.update(finishedAt=timestamp(),seconds=round(time.monotonic()-self.started,6),transcript=path.name,transcriptSha256=digest(path),trace=self.trace.name if self.trace.exists() else None,traceSha256=digest(self.trace) if self.trace.exists() else None)
  writeJson(self.receipt,self.result)
