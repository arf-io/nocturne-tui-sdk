#!/usr/bin/env python3
"""Opt-in tmux status-left renderer. Prefer AFD's existing scheduler when present.

Default: emit one styled frame to stdout. --animate explicitly mutates status-left
on one session and restores its previous local state on clean exit, unless another
writer changed it. Never writes pane contents or invokes a shell.
"""
from pathlib import Path
import argparse,subprocess,sys,time,signal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'integrations'))
from afd_bridge import renderStatus,PALETTES

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--palette',default='smart-dark',choices=list(PALETTES));p.add_argument('--width',type=int,default=40);p.add_argument('--time-ms',type=int,default=3000);p.add_argument('--title',default='NOCTURNE / AFD');p.add_argument('--animate',action='store_true');p.add_argument('--session');p.add_argument('--socket');p.add_argument('--fps',type=int,default=10);a=p.parse_args()
    if not 1<=a.fps<=30:p.error('fps 1..30')
    if not a.animate:print(renderStatus(a.time_ms,a.palette,a.width,a.title));return
    if not a.session:p.error('--animate requires an explicit --session target; do not co-run with an AFD status writer')
    prefix=['tmux']+(['-L',a.socket] if a.socket else [])
    def call(args):return subprocess.run(prefix+args,check=True,capture_output=True,text=True,timeout=3).stdout.rstrip('\n')
    listed=call(['show-options','-q','-t',a.session,'status-left']);hadLocal=bool(listed)
    original=call(['show-options','-qv','-t',a.session,'status-left']);last=None;running=True
    def stop(*_):
        nonlocal running
        running=False
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,stop)
    epoch=time.monotonic();deadline=epoch
    try:
        while running:
            last=renderStatus(int((time.monotonic()-epoch)*1000),a.palette,a.width,a.title)
            call(['set-option','-t',a.session,'status-left',last])
            # An option change schedules a status redraw; no pane escape writes.
            deadline+=1/a.fps;now=time.monotonic()
            if deadline<now:deadline=now
            time.sleep(max(0,deadline-now))
    finally:
        try:
            current=call(['show-options','-qv','-t',a.session,'status-left'])
            if current==last:
                if hadLocal:call(['set-option','-t',a.session,'status-left',original])
                else:call(['set-option','-u','-t',a.session,'status-left'])
        except (subprocess.SubprocessError,OSError):pass
if __name__=='__main__':main()
