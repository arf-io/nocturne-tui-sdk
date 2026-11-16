#!/usr/bin/env python3
"""Run each real framework in a controlling PTY; save raw output and test traces.

This is an interactive integration test, not a font/display or OS screenshot test.
It verifies held-time input, catalogue/help, and normal terminal restoration.
"""
from __future__ import annotations
import argparse, fcntl, json, os, pty, select, shutil, signal, struct, subprocess, sys, termios, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--language',required=True,choices=['python','typescript','go','rust']);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    commands={'python':[sys.executable,str(ROOT/'apps/python/nocturne_app.py')],'typescript':['node',str(ROOT/'apps/typescript/dist/main.js')],'go':[str(ROOT/'dist/rc3-bubbletea'),'--root',str(ROOT)],'rust':[str(ROOT/'apps/rust/target/debug/nocturne-rc3-ratatui')]}
    command=commands[a.language]+['--page','scene:warp','--fps','1','--trace',str(out/'trace.ndjson')]
    if not shutil.which(command[0])or (a.language=='typescript'and not Path(command[1]).exists()):
        (out/'RESULT.json').write_text(json.dumps({'status':'BLOCKED','reason':'Framework application not built','command':command}));return 2
    master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',38,120,0,0));before=termios.tcgetattr(slave)
    def ownTerminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
    env={**os.environ,'TERM':'xterm-256color','COLORTERM':'truecolor','NO_COLOR':''};env.pop('NO_COLOR')
    process=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,cwd=ROOT,env=env,preexec_fn=ownTerminal,close_fds=True)
    raw=bytearray();checks=[]
    def records():
        path=out/'trace.ndjson'
        if not path.exists():return []
        result=[]
        for line in path.read_text(errors='replace').splitlines():
            try:result.append(json.loads(line))
            except json.JSONDecodeError:pass
        return result
    def waitFor(label,predicate,timeout=12):
        start=time.monotonic()
        while time.monotonic()-start<timeout:
            if select.select([master],[],[],.05)[0]:
                try:raw.extend(os.read(master,65536))
                except OSError:break
            if predicate(records()):checks.append({'id':label,'passed':True,'seconds':time.monotonic()-start});return
            if process.poll()is not None:break
        raise AssertionError(label+' not observed')
    try:
        waitFor('first actual framework frame',lambda r:bool(r))
        os.write(master,b'\x10');waitFor('decorative pause',lambda r:any((x.get('exhibition')or x.get('metadata',{}).get('exhibition',{})).get('paused')for x in r))
        os.write(master,b'RC3-INSTANT');waitFor('typing while held at 1FPS',lambda r:any('RC3-INSTANT'in x.get('text','')for x in r))
        os.write(master,b'\x1bOR');waitFor('catalogue modal',lambda r:any((x.get('exhibition')or x.get('metadata',{}).get('exhibition',{})).get('overlay')=='catalog'for x in r))
        os.write(master,b'\x1b');time.sleep(.2);os.write(master,b'\x1bOP');waitFor('help modal',lambda r:any((x.get('exhibition')or x.get('metadata',{}).get('exhibition',{})).get('overlay')=='help'for x in r))
        os.write(master,b'\x11')
        deadline=time.monotonic()+8
        while process.poll() is None and time.monotonic()<deadline:
            if select.select([master],[],[],.05)[0]:
                try:raw.extend(os.read(master,65536))
                except OSError:break
        process.wait(timeout=1)
        after=termios.tcgetattr(slave);checks.append({'id':'terminal flags restored','passed':after==before});checks.append({'id':'clean exit','passed':process.returncode==0})
        report={'status':'PASS'if all(c['passed']for c in checks)else'FAIL','framework':a.language,'checks':checks,'command':command,'scope':'actual framework PTY and semantic trace, not physical pixels'}
    except Exception as e:report={'status':'FAIL','framework':a.language,'checks':checks,'error':str(e),'command':command}
    finally:
        if process.poll()is None:os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        (out/'terminal-output.bin').write_bytes(raw);os.close(master);os.close(slave)
    (out/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return 0 if report['status']=='PASS'else 2
if __name__=='__main__':raise SystemExit(main())
