#!/usr/bin/env python3
"""Exercise the shipped prompt_toolkit host in an actual PTY, not a mock UI."""
from pathlib import Path
import fcntl,json,os,platform,pty,re,selectors,struct,subprocess,sys,termios,time
ROOT=Path(__file__).resolve().parents[1]
def main():
    try:import prompt_toolkit
    except ImportError:
        print('BLOCKED: prompt_toolkit is not installed');return 2
    master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',30,96,0,0))
    terminal=master if sys.platform=='darwin' else slave
    before=termios.tcgetattr(terminal);out=bytearray();selector=selectors.DefaultSelector();selector.register(master,selectors.EVENT_READ)
    report=ROOT/'evidence/framework-state.json';checks=[]
    if report.exists():report.unlink()
    def control():os.setsid();fcntl.ioctl(slave,termios.TIOCSCTTY,0)
    child=subprocess.Popen([sys.executable,str(ROOT/'hosts/python/prompt_toolkit_host.py'),'--scene','autumn','--fps','1','--info-on-exit',str(report)],stdin=slave,stdout=slave,stderr=slave,cwd=ROOT,preexec_fn=control,env={**os.environ,'TERM':'xterm-256color'})
    def drain(seconds):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            if selector.select(max(0,min(.02,until-time.monotonic()))):
                try:out.extend(os.read(master,65536))
                except OSError:break
    def check(name,condition):checks.append({'name':name,'status':'PASS' if condition else 'FAIL'})
    try:
        deadline=time.monotonic()+8
        while b'NOCTURNE' not in out and child.poll() is None and time.monotonic()<deadline:drain(.03)
        check('framework entered alternate screen',b'\x1b[?1049h' in out and b'NOCTURNE' in out)
        os.write(master,b'\x1bOQ');drain(.15) # F2: hold decoration, not input.
        marker=len(out);os.write(master,b'FIRST');drain(.35)
        visible=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',out[marker:])
        check('native input rendered before 1 FPS deadline',b'FIRST' in visible)
        os.write(master,b'\x01X\x05Z');drain(.2)
        os.write(master,b'\x1b[200~ PASTED\x1b[201~');drain(.2)
        os.write(master,b'\x11');deadline=time.monotonic()+6
        while child.poll() is None and time.monotonic()<deadline:drain(.05)
        check('clean framework exit',child.poll()==0)
        if child.poll() is None:child.kill();child.wait()
        drain(.05)
        after=termios.tcgetattr(terminal)
        check('terminal attributes restored',after==before)
        check('alternate screen released',b'\x1b[?1049l' in out)
        metadata=json.loads(report.read_text()) if report.exists() else {}
        check('native caret and bracketed paste retain exact text',metadata.get('prompt',{}).get('text')=='XFIRSTZ PASTED')
    finally:
        if child.poll() is None:child.kill();child.wait()
        selector.close();os.close(master);os.close(slave)
    def attributes(value):return value[:6]+[[v.hex() if isinstance(v,bytes) else v for v in value[6]]]
    result={'schema':'nocturne.framework.execution.v1','framework':'prompt_toolkit','version':prompt_toolkit.__version__,'scope':'Actual controlling PTY, native C renderer and prompt_toolkit input/output/event loop; not qualification of other frameworks or physical devices.','platform':platform.platform(),'architecture':platform.machine(),'terminalObservationSource':'master' if terminal==master else 'slave','terminalBefore':attributes(before),'terminalAfter':attributes(after),'checks':checks,'passed':all(x['status']=='PASS' for x in checks),'capturedBytes':len(out)}
    (ROOT/'evidence/framework-output.bin').write_bytes(out);(ROOT/'evidence/framework.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
