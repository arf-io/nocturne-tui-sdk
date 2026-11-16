#!/usr/bin/env python3
"""Controlling-PTY transport for the optional xterm/headless skin.

This program executes ONLY the argv explicitly supplied after --, as the current
user. It is not a sandbox. Stdio is a bounded NDJSON/base64 transport; child bytes
are never logged. The parent is responsible for terminal emulation and policy.
"""
from __future__ import annotations
import argparse,base64,binascii,errno,fcntl,json,os,pty,select,signal,struct,sys,termios,time
MAX_LINE=131072
MAX_PENDING=1048576

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--columns',type=int,default=100);parser.add_argument('--rows',type=int,default=32);parser.add_argument('command',nargs=argparse.REMAINDER);a=parser.parse_args();command=a.command[1:] if a.command[:1]==['--'] else a.command
    if not command:parser.error('an explicit command after -- is required')
    if not 1<=a.columns<=1000 or not 1<=a.rows<=500:parser.error('invalid terminal dimensions')
    def emit(record):sys.stdout.buffer.write((json.dumps(record,separators=(',',':'))+'\n').encode());sys.stdout.buffer.flush()
    pid,master=pty.fork()
    if pid==0:
        fcntl.ioctl(0,termios.TIOCSWINSZ,struct.pack('HHHH',a.rows,a.columns,0,0))
        os.environ['TERM']='xterm-256color';os.environ['COLORTERM']='truecolor'
        try:os.execvpe(command[0],command,os.environ)
        except OSError as e:os.write(2,('Unable to execute child: '+str(e)+'\r\n').encode());os._exit(127)
    os.set_blocking(master,False);os.set_blocking(0,False);buffer=b'';pending=b'';eof=False;status=None;stopping=False;shutdownAt=None
    def stop(*_):
        nonlocal stopping,shutdownAt
        if not stopping:
            stopping=True;shutdownAt=time.monotonic()
            try:os.killpg(pid,signal.SIGHUP)
            except ProcessLookupError:pass
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,stop)
    try:
        while True:
            readable,writable,_=select.select(([master] if not eof else [])+([] if stopping else [0]),[master] if pending and not eof else [],[],.05)
            if master in readable:
                try:data=os.read(master,32768)
                except OSError as e:
                    if e.errno in (errno.EIO,errno.EBADF):data=b''
                    elif e.errno==errno.EAGAIN:data=None
                    else:raise
                if data:emit({'type':'output','data':base64.b64encode(data).decode()})
                elif data==b'':eof=True
            if master in writable:
                try:n=os.write(master,pending);pending=pending[n:]
                except OSError as e:
                    if e.errno not in (errno.EAGAIN,errno.EIO):raise
            if 0 in readable:
                data=os.read(0,32768)
                if not data:stop()
                buffer+=data
                if len(buffer)>MAX_LINE:emit({'type':'error','message':'input protocol line limit'});stop();buffer=b''
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1)
                    try:
                        row=json.loads(line);kind=row.get('type')
                        if kind=='input':
                            part=base64.b64decode(row['data'],validate=True)
                            if len(pending)+len(part)>MAX_PENDING:raise ValueError('bounded input queue full')
                            pending+=part
                        elif kind=='resize':
                            c,r=row['columns'],row['rows']
                            if type(c) is not int or type(r) is not int or not 1<=c<=1000 or not 1<=r<=500:raise ValueError('invalid resize')
                            fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',r,c,0,0))
                        elif kind=='signal':
                            sig={'INT':signal.SIGINT,'TERM':signal.SIGTERM,'HUP':signal.SIGHUP,'QUIT':signal.SIGQUIT}.get(row.get('name'))
                            if sig is None:raise ValueError('unsupported signal')
                            os.killpg(pid,sig)
                        elif kind=='close':stop()
                        else:raise ValueError('unknown protocol record')
                    except (ValueError,TypeError,KeyError,binascii.Error,json.JSONDecodeError) as e:emit({'type':'error','message':str(e)[:160]})
            if status is None:
                waited,result=os.waitpid(pid,os.WNOHANG)
                if waited:status=result
            if status is not None and eof:break
            if stopping and shutdownAt is not None and time.monotonic()-shutdownAt>1:
                try:os.killpg(pid,signal.SIGKILL)
                except ProcessLookupError:pass
            # If a child exits but a descendant holds the slave open, don't leak it.
            if status is not None and not stopping:stop()
    except (BrokenPipeError,KeyboardInterrupt):stop()
    finally:
        if status is None:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:_,status=os.waitpid(pid,0)
            except ChildProcessError:status=0
        os.close(master)
    code=os.waitstatus_to_exitcode(status)
    try:emit({'type':'exit','code':code if code>=0 else 128-code,'signal':-code if code<0 else None})
    except BrokenPipeError:pass
if __name__=='__main__':main()
