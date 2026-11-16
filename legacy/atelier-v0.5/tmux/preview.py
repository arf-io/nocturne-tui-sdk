#!/usr/bin/env python3
"""Launch a separate tmux server with an explicit Nocturne profile.

Does not source ~/.tmux.conf or overwrite AFD's running server. Ctrl+Q exits
Nocturne. The pane is an interactive art/demo app, not a shell prompt executor.
"""
import argparse,os,shlex,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',default='smart-dark',choices=[x.stem for x in (ROOT/'tmux/profiles').glob('*.conf')]);p.add_argument('--scene',default='starwrite');p.add_argument('--print-command',action='store_true');a=p.parse_args()
    argv=['tmux','-L',f'nocturne-preview-{os.getpid()}','-f',str(ROOT/'tmux/profiles'/f'{a.profile}.conf'),'new-session','-s','Nocturne',shlex.join([sys.executable,str(ROOT/'examples/studio_terminal.py'),'--scene',a.scene,'--palette',a.profile])]
    if a.print_command:print(shlex.join(argv));return
    if not shutil.which('tmux'):p.error('tmux is not installed; run the terminal demo directly or install tmux first')
    raise SystemExit(subprocess.call(argv))
if __name__=='__main__':main()
