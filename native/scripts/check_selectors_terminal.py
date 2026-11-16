#!/usr/bin/env python3
"""Qualify passive mouse movement in the real POSIX native host using a PTY.

Runs the supplied selector-studio scene, sends SGR pointer input, and checks the
host's final native metadata and terminal cleanup. Writes a receipt and raw output.
No subprocess is counted as successful before it exits. Example: python3 native/scripts/check_selectors_terminal.py
"""
from pathlib import Path
import fcntl, json, os, pty, re, selectors, struct, subprocess, sys, termios, time
ROOT=Path(__file__).resolve().parents[1]

def main():
    master,slave=pty.openpty()
    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',48,160,0,0))
    terminal=master if sys.platform=='darwin' else slave;before=termios.tcgetattr(terminal);output=bytearray();checks=[]
    selector=selectors.DefaultSelector();selector.register(master,selectors.EVENT_READ)
    report=ROOT/'evidence/selector-terminal-state.json'
    if report.exists():report.unlink()
    def control():os.setsid();fcntl.ioctl(slave,termios.TIOCSCTTY,0)
    proc=subprocess.Popen([sys.executable,str(ROOT/'examples/terminal.py'),'--scene','selector-studio','--fps','1','--paused','--info-on-exit',str(report)],stdin=slave,stdout=slave,stderr=slave,cwd=ROOT,preexec_fn=control)
    def drainUntil(predicate,seconds):
        deadline=time.monotonic()+seconds
        while not predicate() and time.monotonic()<deadline:
            if selector.select(min(.05,max(0,deadline-time.monotonic()))):
                try:output.extend(os.read(master,65536))
                except OSError:break
        return predicate()
    def check(name,condition):
        checks.append({'name':name,'status':'PASS' if condition else 'FAIL'})
        print(checks[-1]['status'],name,flush=True)
    try:
        def hasTitle():return b'SELECTOR STUDIO' in re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',output)
        ready=drainUntil(lambda:hasTitle() or proc.poll() is not None,10)
        check('selector-studio starts in an actual terminal',ready and hasTitle() and proc.poll() is None)
        check('host requests all-motion SGR mouse reporting',b'\x1b[?1003h'in output and b'\x1b[?1006h'in output)
        # One continuous ordered input stream is parsed and committed by the host.
        os.write(master,b'\x1b[<35;16;14M\x1b[<0;16;14M\x1b[<0;16;14m\x1b[<35;66;14M\x11')
        exited=drainUntil(lambda:proc.poll() is not None,10)
        check('native host exits successfully',exited and proc.returncode==0)
        if not exited:proc.kill();proc.wait()
        # Drain remaining final output after exit without assuming a read boundary.
        while selector.select(0):
            try:
                chunk=os.read(master,65536)
                if not chunk:break
                output.extend(chunk)
            except OSError:break
        check('terminal attributes are restored',termios.tcgetattr(terminal)==before)
        check('all-motion reporting and alternate screen are released',all(code in output for code in [b'\x1b[?1003l',b'\x1b[?1006l',b'\x1b[?1049l',b'\x1b[?25h']))
        info=json.loads(report.read_text())if report.exists()else{}
        registered={r['id']:r for r in info.get('registeredStates',[])}
        check('first button selected by real SGR down/up',registered.get(1,{}).get('states',{}).get('selected') is True)
        check('passive move transfers hover to second button',registered.get(2,{}).get('states',{}).get('hover') is True and registered.get(1,{}).get('states',{}).get('hover') is False)
        check('no press remains after release',all(not r['states']['pressed'] for r in registered.values()) and bool(registered))
        check('native hover appearance reaches selected material',registered.get(2,{}).get('effective',{}).get('material')==2)
        check('all pointer input preserves held time and causes no weather',info.get('clock',{}).get('timeUs')==0 and info.get('fieldCount')==0)
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        selector.close();os.close(master);os.close(slave)
    result={'scope':'Real controlling PTY with actual direct C/ctypes host and SGR all-motion events; no physical terminal claim.','checks':checks,'passed':all(c['status']=='PASS' for c in checks),'capturedBytes':len(output)}
    (ROOT/'evidence/selector-terminal-output.bin').write_bytes(output)
    (ROOT/'evidence/selector-terminal.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
