"""Parse legacy and Observatory profiles against an isolated actual tmux server. CI-only here."""
from pathlib import Path
import subprocess,os,json,sys
ROOT=Path(__file__).resolve().parents[1];name=f'nocturne-ci-{os.getpid()}';prefix=['tmux','-L',name]
def call(args):return subprocess.run(prefix+args,capture_output=True,text=True,check=True,timeout=5).stdout
try:
    call(['-f','/dev/null','new-session','-d','-s','check','sleep 60'])
    profiles=sorted((ROOT/'tmux/profiles').glob('*.conf'))+sorted((ROOT/'tmux/observatory-profiles').glob('*.conf'))
    for path in profiles:call(['source-file',str(path)])
    rendered=subprocess.check_output([sys.executable,str(ROOT/'tmux/status.py'),'--palette','smart-dark','--title','inert #(not-a-command)'],text=True)
    call(['set-option','-t','check','status-left',rendered.strip()]);assert '#[fg=#' in call(['show-options','-qv','-t','check','status-left'])
    print(json.dumps({'status':'PASS','profiles':len(profiles),'styleOutputAccepted':True,'version':subprocess.check_output(['tmux','-V'],text=True).strip()}))
finally:subprocess.run(prefix+['kill-server'],capture_output=True)
