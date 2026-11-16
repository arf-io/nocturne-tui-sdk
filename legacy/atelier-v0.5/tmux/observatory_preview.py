#!/usr/bin/env python3
"""Start a separate tmux server with a Nocturne theme; never source ~/.tmux.conf."""
import argparse,os,shlex,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',choices=['smart-dark','copper','neon-dreams','opal','winter','millennial-gray'],default='smart-dark');p.add_argument('--scene',default='warp');p.add_argument('--fps',type=int,default=60);p.add_argument('--print-command',action='store_true');a=p.parse_args()
 if not 1<=a.fps<=120:p.error('fps must be 1..120')
 command=shlex.join(['node',str(ROOT/'examples/observatory_terminal.mjs'),'--scene',a.scene,'--palette',a.profile,'--fps',str(a.fps)])
 argv=['tmux','-L',f'nocturne-observatory-{os.getpid()}','-f',str(ROOT/'tmux/observatory-profiles'/f'{a.profile}.conf'),'new-session','-s','Observatory',command]
 if a.print_command:print(shlex.join(argv));return
 if not shutil.which('tmux'):p.error('tmux is unavailable; run the Node host directly')
 raise SystemExit(subprocess.call(argv))
if __name__=='__main__':main()
