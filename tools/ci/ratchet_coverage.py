"""Commit upward-only coverage policy after a successful protected-branch run."""
import base64,json,math,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];path=root/'tools/ci/coverage-ratchet.json'
branch=os.environ.get('GITHUB_REF','').removeprefix('refs/heads/')
if branch not in {'main','integration'}:raise SystemExit('Ratchet requires protected branch push')
old=json.loads(path.read_text());new=json.loads(Path(sys.argv[1]).read_text())
for policy in (old,new):
 value=policy['nativeLinePercent']
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 70<=value<=100:
  raise SystemExit('Coverage policy must be a finite percentage between 70 and 100')

if new['nativeLinePercent']<=old['nativeLinePercent']:raise SystemExit(0)
token=os.environ['NOCTURNE_CI_TOKEN']
changed=subprocess.check_output(['git','diff','HEAD','--name-only','-z'],cwd=root).decode().split('\0')
if any(name and not name.startswith('native/evidence/') for name in changed):
 raise SystemExit('Ratchet requires unchanged tracked source; generated evidence may remain dirty')
path.write_text(json.dumps(new,indent=2)+'\n')
subprocess.run(['git','add','tools/ci/coverage-ratchet.json'],cwd=root,check=True)
subprocess.run(['git','-c','user.name=Nocturne CI','-c','user.email=nocturne-ci@users.noreply.github.com','commit','--only','-m','Raise native coverage ratchet','tools/ci/coverage-ratchet.json'],cwd=root,check=True)
authorization=base64.b64encode(('nocturne-ci:'+token).encode()).decode()
env=dict(os.environ,GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.extraHeader',GIT_CONFIG_VALUE_0='Authorization: Basic '+authorization)
# Ordinary push rejects a concurrent branch update; never force-push another agent.
subprocess.run(['git','push','origin',f'HEAD:refs/heads/{branch}'],cwd=root,env=env,check=True)
