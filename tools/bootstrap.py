#!/usr/bin/env python3
"""Provision explicitly pinned framework packages; write actual installation evidence.
No release test silently invokes this. Successful downloads are reported only after
commands finish, and installed versions/lock digests are retained for qualification.
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, shutil, subprocess, sys, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if sys.version_info < (3, 11):raise SystemExit('tools/requirements-qualification.txt needs Python 3.11 or later (Markdown 3.11.x); found '+platform.python_version())
STATE=ROOT/'.nocturne-tools/bootstrap';STATE.mkdir(parents=True,exist_ok=True)
RESULTS=[]
def run(name,argv,env=None,cwd=ROOT):
    print('+ '+' '.join(map(str,argv)),flush=True)
    with (STATE/(name+'.log')).open('w')as log:r=subprocess.run(list(map(str,argv)),cwd=cwd,stdout=log,stderr=subprocess.STDOUT,env=env)
    RESULTS.append({'step':name,'argv':list(map(str,argv)),'exitCode':r.returncode})
    (STATE/'RESULT.json').write_text(json.dumps(RESULTS,indent=2))
    if r.returncode:raise RuntimeError(f'{name} failed ({r.returncode}); see {STATE/name}.log. Repositories/packages vary by OS; no success inferred.')

def main():
    spec=importlib.util.spec_from_file_location('installer',ROOT/'scripts/install_workbench.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    info={}
    if Path('/etc/os-release').exists():
        for line in Path('/etc/os-release').read_text().splitlines():
            if '='in line:k,v=line.split('=',1);info[k]=v.strip('"')
    env=old.baseEnv();env['RUSTUP_TOOLCHAIN']='stable';plan=old.buildPlan(platform.system(),platform.machine(),info,['node'])
    old.installNode(plan,env)
    if plan['manager']!='apk':
        if not shutil.which('rustup',path=env['PATH']):
            path=STATE/'rustup-init.sh'
            with urllib.request.urlopen('https://sh.rustup.rs',timeout=60)as r:path.write_bytes(r.read())
            (STATE/'rustup-init.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'\n')
            run('rustup',['sh',path,'-y','--no-modify-path','--profile','minimal','--default-toolchain','stable'],env)
        run('rust-toolchain',['rustup','toolchain','install','stable','--profile','minimal'],env)
    # Distro Go may be older than the SDK's minimum. Install a verified official
    # archive locally when needed; never replace a system Go tree.
    try:
        raw=subprocess.check_output(['go','env','GOVERSION'],env=env,text=True).strip().removeprefix('go')
        goReady=tuple(map(int,raw.split('.')[:2])) >= (1,23)
    except Exception:goReady=False
    if not goReady:
        with urllib.request.urlopen('https://go.dev/dl/?mode=json',timeout=60)as r:releases=json.load(r)
        arch='arm64'if platform.machine().lower()in('arm64','aarch64')else'amd64';system='darwin'if platform.system()=='Darwin'else'linux'
        item=next(f for release in releases if release.get('stable') for f in release['files']if f['os']==system and f['arch']==arch and f['kind']=='archive')
        archive=STATE/item['filename']
        with urllib.request.urlopen('https://go.dev/dl/'+item['filename'],timeout=120)as r,archive.open('wb')as w:shutil.copyfileobj(r,w)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Go download SHA256 mismatch')
        import tarfile,tempfile
        with tempfile.TemporaryDirectory(dir=ROOT/'.nocturne-tools')as temp:
            with tarfile.open(archive)as t:t.extractall(temp,filter='data')
            target=ROOT/'.nocturne-tools/go'
            if target.exists():raise RuntimeError('Existing local Go was not overwritten; inspect it')
            shutil.move(str(Path(temp)/'go'),target)
        env['PATH']=str(ROOT/'.nocturne-tools/go/bin')+os.pathsep+env['PATH']
    run('venv',[sys.executable,'-m','venv',str(ROOT/'.venv')],env)
    py=ROOT/'.venv/bin/python';env['PATH']=str(ROOT/'.venv/bin')+os.pathsep+env['PATH']
    run('python-packages',[py,'-m','pip','install','--disable-pip-version-check','-r',ROOT/'tools/requirements-qualification.txt'],env)
    run('python-lock',[py,'-m','pip','freeze','--all'],env)
    run('chromium',[py,'-m','playwright','install','chromium'],env)
    if platform.system()=='Linux' and plan['manager']=='apt-get':
        # Supported Playwright system dependency installer; explicit provisioning only.
        run('chromium-system-deps',[py,'-m','playwright','install-deps','chromium'],env)
    run('root-npm',['npm','install','--ignore-scripts','--no-audit','--no-fund'],env)
    run('typescript-framework',['npm','install','--ignore-scripts','--no-audit','--no-fund'],env,ROOT/'apps/typescript')
    run('optional-pty',['npm','install','--ignore-scripts','--no-audit','--no-fund'],env,ROOT/'integrations/pty')
    # New locks are created in the provisioning phase, never fabricated offline.
    run('go-framework-lock',['go','mod','tidy'],env,ROOT/'apps/go')
    run('go-framework-fetch',['go','mod','download'],env,ROOT/'apps/go')
    for name,d in [('native',ROOT/'bindings/rust'),('framework',ROOT/'apps/rust')]:
        cmd=['cargo'] if plan['manager']=='apk' else ['cargo','+stable']
        run('rust-'+name+'-lock',cmd+['generate-lockfile'],env,d)
        run('rust-'+name+'-fetch',cmd+['fetch','--locked'],env,d)
    locks={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'package-lock.json',ROOT/'apps/typescript/package-lock.json',ROOT/'apps/go/go.sum',ROOT/'bindings/rust/Cargo.lock',ROOT/'apps/rust/Cargo.lock')if p.exists()}
    (STATE/'LOCKS.json').write_text(json.dumps(locks,indent=2))
    print('Provisioning completed; next qualification freezes these exact files.')
if __name__=='__main__':
    try:main()
    except Exception as e:print('BOOTSTRAP BLOCKED:',e,file=sys.stderr);raise SystemExit(2)
