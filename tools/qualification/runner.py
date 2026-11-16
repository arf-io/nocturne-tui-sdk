#!/usr/bin/env python3
"""Nocturne RC3 qualification: provision, freeze, execute, capture, inspect, package.

Every declared animation tick is saved. A finite, versioned scenario plan is not
an exhaustive proof of all continuous parameter combinations. Missing languages,
frameworks, changed inputs, timeouts and pending human review remain visible.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, platform, re, shlex, shutil, signal, subprocess, sys, time, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
LANGUAGES=['typescript','python','go','rust']
EXCLUDED={'.git','node_modules','target','.venv','.nocturne-tools','__pycache__','.pytest_cache','dist','evidence','qualification-results'}

def tickTimes(frames:int,fps:int):
    if not isinstance(frames,int)or not isinstance(fps,int)or frames<0 or fps<1 or fps>240:raise ValueError('Invalid tick plan')
    return [i*1000//fps for i in range(frames)]

def safeRelative(value):
    if not isinstance(value,str)or not value or '\\'in value or ':'in value or '\x00'in value:return False
    if any(x in ('','.','..') for x in value.split('/')):return False
    p=PurePosixPath(value)
    return not p.is_absolute() and all(x not in ('','..','.')for x in p.parts)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def fingerprint(root):
    records={}
    for directory,dirs,names in os.walk(root):
        dirs[:]=sorted(x for x in dirs if x not in EXCLUDED)
        for name in sorted(names):
            p=Path(directory)/name;r=p.relative_to(root)
            if p.is_symlink():records[str(r)]={'symlink':os.readlink(p)};continue
            if name.endswith(('.pyc','.so','.dylib','.dll','.html','.mp4','.png','.zip','.bundle')):continue
            # Generated old receipts are not application inputs.
            if name in ('SHA256SUMS.txt','SOURCE-CONTENTS.md','BUILD-IDENTITY.json'):continue
            records[str(r)]=digest(p)
    return {'sha256':hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'files':records}

def runStep(name,argv,cwd,out,timeout=600,env=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    result={'id':name,'argv':list(map(str,argv)),'cwd':str(cwd),'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'required':True}
    exe=argv[0];environment=env or os.environ.copy()
    if not Path(cwd).is_dir() or not shutil.which(str(exe),path=environment.get('PATH')):
        result.update(status='BLOCKED',reason='Missing executable or working directory',exitCode=None,seconds=0)
    else:
        log=out/(name+'.log');result['log']=log.name
        # File logging avoids pipe backpressure. A monitor kills a runaway producer
        # at 32 MiB, preserving a bounded complete diagnostic prefix.
        try:
            with log.open('wb')as f:
                p=subprocess.Popen(list(map(str,argv)),cwd=cwd,stdout=f,stderr=subprocess.STDOUT,env=environment,start_new_session=(os.name=='posix'))
                status=None
                while p.poll() is None:
                    if time.monotonic()-start>timeout:status='TIMEOUT';break
                    if log.stat().st_size>32*1024*1024:status='FAIL';result['reason']='Log capacity exceeded';break
                    time.sleep(.05)
                if status:
                    if os.name=='posix':os.killpg(p.pid,signal.SIGTERM)
                    else:p.terminate()
                    try:p.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        if os.name=='posix':os.killpg(p.pid,signal.SIGKILL)
                        else:p.kill()
                        p.wait(timeout=5)
                result.update(status=status or ('PASS'if p.returncode==0 else 'FAIL'),exitCode=p.returncode,seconds=round(time.monotonic()-start,3))
        except (OSError,subprocess.SubprocessError)as error:result.update(status='BLOCKED',exitCode=None,reason=str(error),seconds=round(time.monotonic()-start,3))
    (out/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(f"{result['status']:8} {name} ({result['seconds']} s)",flush=True);return result

def qualifies(results,complete):return bool(complete and results and all(r['status']=='PASS' for r in results))

def environment(root):
    paths=[root/'.venv/bin',root/'.nocturne-tools/node/bin',root/'.nocturne-tools/go/bin',root/'node_modules/.bin',Path.home()/'.cargo/bin',Path('/opt/homebrew/opt/llvm/bin'),Path('/opt/homebrew/opt/lld/bin')]
    e=os.environ.copy();e['PATH']=os.pathsep.join(map(str,paths))+os.pathsep+e.get('PATH','');e['GOTOOLCHAIN']='local';e['PYTHONUNBUFFERED']='1'
    if (root/'.nocturne-tools/bootstrap/LOCKS.json').exists():e['RUSTUP_TOOLCHAIN']='stable'
    return e

def createPlan(root,profile,seconds,fps,width,height):
    catalog=json.loads((root/'chromatic.catalog.json').read_text())
    ids=[x['id']for x in catalog]
    if profile=='smoke':ids=[x for x in ['scene:warp','scene:dag','scene:windows','chroma:hazard-opera']if x in ids]
    cases=[]
    for index,id in enumerate(ids):
        cases.append({'name':f'{index:03d}-'+re.sub('[^a-zA-Z0-9._-]','-',id),'id':id,'frames':max(2,round(seconds*fps)),'commands':[]})
    # Additional scripted interaction: new text while motion is held, then continue.
    if profile=='full':
        cases.append({'name':'input-held-alpha','id':'scene:warp','frames':61,'commands':[{'frame':0,'op':'prompt-config','payload':{'alpha':0}},{'frame':1,'op':'demo-key','payload':{'key':'p','ctrl':True}},{'frame':2,'op':'demo-input','payload':{'text':'IMMEDIATE INPUT'}},{'frame':30,'op':'demo-key','payload':{'key':'p','ctrl':True}}]})
    return {'schema':'nocturne.capture-plan.v1','profile':profile,'scope':'all recovered catalogue entries for the declared finite duration plus explicit regression timelines; not all possible infinite animations','fps':fps,'width':width,'height':height,'cellWidth':10,'cellHeight':20,'languages':LANGUAGES,'cases':cases,'expectedFrames':sum(c['frames']for c in cases),'noFrameSkipping':True,'output':'PNG + 16-byte cells every declared tick per executed language; per-case MP4'}

def writeReplay(plan,path):
    lines=[]
    for case in plan['cases']:
        commands=[('-', 'session-reset',{}),('-','demo-resize',{'width':plan['width'],'height':plan['height']}),('-','demo-open',{'id':case['id']})]
        for i,t in enumerate(tickTimes(case['frames'],plan['fps'])):
            for event in case['commands']:
                if event['frame']==i:commands.append(('-',event['op'],event['payload']))
            commands.append((case['name']+f'/frame-{i:06d}','demo-time',{'timeMs':t}))
        lines.extend('\t'.join((name,op,json.dumps(p,separators=(',',':'))))for name,op,p in commands)
    path.write_text('\n'.join(lines)+'\n')

def archiveEvidence(root,destination):
    entries=[]
    for p in sorted(root.rglob('*')):
        if p.is_file()and not p.is_symlink()and p.name!='EVIDENCE-MANIFEST.json':entries.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':digest(p)})
    (root/'EVIDENCE-MANIFEST.json').write_text(json.dumps({'schema':'nocturne.evidence-manifest.v1','files':entries},indent=2))
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True)as z:
        for p in sorted(root.rglob('*')):
            if p.is_file()and not p.is_symlink():z.write(p,p.relative_to(root))
    verifyEvidence(destination)

def verifyEvidence(path):
    with zipfile.ZipFile(path)as z:
        names=z.namelist()
        if any((i.external_attr>>16)&0o170000==0o120000 for i in z.infolist()):raise ValueError('Symlink member rejected')
        if len(names)!=len(set(names))or any(not safeRelative(x)for x in names):raise ValueError('Unsafe/duplicate archive name')
        m=json.loads(z.read('EVIDENCE-MANIFEST.json'));expected={x['path']:x for x in m['files']}
        if len(expected)!=len(m['files']):raise ValueError('Duplicate manifest path')
        if set(names)!=set(expected)|{'EVIDENCE-MANIFEST.json'}:raise ValueError('Manifest membership mismatch')
        for name,item in expected.items():
            data=z.read(name)
            if len(data)!=item['bytes']or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Integrity mismatch '+name)
    return len(names)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['smoke','full'],default='full');parser.add_argument('--no-install',action='store_true')
    parser.add_argument('--yes',action='store_true');parser.add_argument('--list',action='store_true');parser.add_argument('--output',type=Path)
    parser.add_argument('--seconds',type=float,default=6);parser.add_argument('--fps',type=int,default=60);parser.add_argument('--width',type=int,default=160);parser.add_argument('--height',type=int,default=52)
    parser.add_argument('--budget-gib',type=float,default=200);parser.add_argument('--timeout',type=int,default=7200);parser.add_argument('--no-video',action='store_true');parser.add_argument('--verify',type=Path)
    args=parser.parse_args()
    if args.verify:print('Verified',verifyEvidence(args.verify),'members');return 0
    if not .05<=args.seconds<=120 or not 1<=args.fps<=120 or not 36<=args.width<=240 or not 18<=args.height<=100:parser.error('Invalid sampling/geometry')
    plan=createPlan(ROOT,args.profile,args.seconds,args.fps,args.width,args.height)
    rawBytes=plan['expectedFrames']*len(LANGUAGES)*args.width*args.height*16
    estimate=rawBytes*4 # cells, surfaces, PNGs and videos, workload-dependent
    plan['storageEstimateBytes']=estimate
    if args.list:print(json.dumps(plan,indent=2));return 0
    if estimate>args.budget_gib*1024**3:parser.error('Plan exceeds budget; explicitly increase --budget-gib or use --profile smoke. No frames will be silently skipped.')
    if args.profile=='full'and not args.yes:
        if not sys.stdin.isatty():parser.error('Full capture requires --yes after inspecting --list')
        if input(f"Capture {plan['expectedFrames']*4:,} PNG/cell frames (estimated {estimate/1024**3:.1f} GiB), install dependencies unless --no-install? [y/N] ").lower()!='y':return 2
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=(args.output or ROOT.parent/('nocturne-evidence-'+stamp)).resolve()
    if out.exists()and any(out.iterdir()):parser.error('Output must be new/empty')
    if out==ROOT or ROOT in out.parents:parser.error('Evidence must live outside SDK to keep source fingerprint meaningful')
    out.mkdir(parents=True,exist_ok=True);logs=out/'logs';logs.mkdir();env=environment(ROOT);results=[];before=None
    (out/'CAPTURE-PLAN.json').write_text(json.dumps(plan,indent=2));writeReplay(plan,out/'replay.tsv')
    (out/'PLATFORM.json').write_text(json.dumps({'system':platform.system(),'release':platform.release(),'architecture':platform.machine(),'python':sys.version,'physicalDisplayTested':False},indent=2))
    def step(name,argv,cwd=ROOT,timeout=args.timeout):
        r=runStep(name,argv,cwd,logs,timeout,env);results.append(r);(out/'PROGRESS.json').write_text(json.dumps(results,indent=2));return r
    try:
        if shutil.disk_usage(out).free < estimate:
            results.append({'id':'storage-preflight','status':'BLOCKED','required':True,'reason':'Not enough free disk for the declared capture; no frames silently skipped','estimatedBytes':estimate})
            raise RuntimeError('Storage preflight blocked capture')
        if not args.no_install:step('bootstrap',['sh','tools/bootstrap.sh','--yes'])
        env=environment(ROOT)
        if args.no_install:env.update(GOPROXY='off',CARGO_NET_OFFLINE='true')
        for name,cmd in [('node',['node','--version']),('python',['python3','--version']),('go',['go','version']),('rust',['rustc','--version']),('cargo',['cargo','--version']),('ffmpeg',['ffmpeg','-version'])]:step('version-'+name,cmd,timeout=30)
        for name in ('RESULT.json','LOCKS.json','python-lock.log'):
            installed=ROOT/'.nocturne-tools/bootstrap'/name
            if installed.exists():
                (out/'provisioning').mkdir(exist_ok=True);shutil.copyfile(installed,out/'provisioning'/name)
        before=fingerprint(ROOT);(out/'SOURCE-BEFORE.json').write_text(json.dumps(before,indent=2))
        identity={'actualGit':None,'packagedIdentity':None}
        if (ROOT/'BUILD-IDENTITY.json').exists():identity['packagedIdentity']=json.loads((ROOT/'BUILD-IDENTITY.json').read_text())
        if (ROOT/'.git').exists() and shutil.which('git',path=env.get('PATH')):
            identity['actualGit']={}
            for label,command in [('head',['rev-parse','HEAD']),('tree',['rev-parse','HEAD^{tree}']),('status',['status','--porcelain'])]:
                got=subprocess.run(['git',*command],cwd=ROOT,capture_output=True,text=True,timeout=15,env=env)
                identity['actualGit'][label]={'exitCode':got.returncode,'value':got.stdout.strip()}
        (out/'SOURCE-IDENTITY.json').write_text(json.dumps(identity,indent=2))
        step('build-native-wasm',['sh','scripts/build.sh','--wasm'],timeout=180)
        step('build-current-gallery',['python3','scripts/build_rc3.py'],timeout=60)
        step('contracts',['node','--test',*[str(x.relative_to(ROOT)) for x in sorted((ROOT/'tests/rc3').glob('*.mjs'))]],timeout=180)
        step('runner-tests',['python3','-m','unittest','discover','-s','tests/rc3','-p','test_*.py'],timeout=90)
        if args.profile=='full':
            step('historical',['sh','scripts/check_workbench.sh'])
            step('native-rust',['cargo','test','--locked','--all-targets'],ROOT/'bindings/rust')
            step('rust-docs',['cargo','doc','--locked','--no-deps'],ROOT/'bindings/rust')
            step('optional-terminal-emulator',['env','REQUIRE_PTY=1','node','tests/observatory/pty_headless.mjs'])
            step('tmux-profile-validation',['python3','scripts/check_tmux.py'],timeout=120)
        # Dependency locks are generated only during explicit provisioning, never here.
        step('typescript-framework-build',['npm','run','build'],ROOT/'apps/typescript')
        step('go-framework-build',['go','build','-mod=readonly','-o','../../dist/rc3-bubbletea','.'],ROOT/'apps/go')
        step('rust-framework-build',['cargo','build','--locked'],ROOT/'apps/rust')
        for language,cmd,cwd in [
          ('typescript',['node','examples/rc3_replay.mjs'],ROOT),
          ('python',['python3','examples/rc3_replay.py'],ROOT),
          ('go',['go','run','-mod=readonly','./cmd/rc3-replay'],ROOT/'bindings/go'),
          ('rust',['cargo','run','--locked','--example','rc3_replay','--'],ROOT/'bindings/rust')]:
            target=out/'frames'/language;target.mkdir(parents=True,exist_ok=True)
            argv=cmd+[str(out/'replay.tsv'),str(target)]
            if language in ('rust','go'):argv.append(str(ROOT/'examples/chromatic_bridge.mjs'))
            step('canonical-'+language,argv,cwd)
        for language,cmd,cwd in [
          ('python',['python3','apps/python/nocturne_app.py'],ROOT),
          ('typescript',['node','dist/main.js'],ROOT/'apps/typescript'),
          ('go',[str(ROOT/'dist/rc3-bubbletea')],ROOT),
          ('rust',[str(ROOT/'apps/rust/target/debug/nocturne-rc3-ratatui')],ROOT)]:
            step('surface-'+language,cmd+['--surface-replay',str(out/'frames'/language),str(out/'surfaces'/language)],cwd)
            step('pty-'+language,['python3','tools/qualification/framework_pty.py','--language',language,'--output',str(out/'frameworks'/language)],timeout=90)
        step('browser',['python3','tools/qualification/browser.py','--output',str(out/'browser')],timeout=300)
        step('browser-tick-capture',['python3','tools/qualification/browser_ticks.py',str(out)]+(['--no-video']if args.no_video else[]))
        step('visual-inspection',['python3','tools/qualification/visual.py',str(out)]+(['--no-video']if args.no_video else[]))
    except BaseException as error:
        results.append({'id':'runner-exception','status':'FAIL','reason':str(error),'required':True})
    finally:
        after=fingerprint(ROOT);(out/'SOURCE-AFTER.json').write_text(json.dumps(after,indent=2))
        changed=before is None or before['sha256']!=after['sha256']
        results.append({'id':'frozen-inputs','status':'FAIL' if changed else 'PASS','required':True})
        complete=args.profile=='full'and not args.no_video
        report={'schema':'nocturne.qualification.v1','sourceSHA256':after['sha256'],'profile':args.profile,'automatedQualificationPassed':qualifies(results,complete),'qualificationPassed':False,'humanVisualReview':'PENDING; automated heuristics cannot judge all compositing/art failures','completeProfile':complete,'steps':results,'remotePublication':'NOT PERFORMED','evidenceScope':'Every tick in CAPTURE-PLAN, not every possible infinite animation/configuration. Framework offscreen surfaces and PTY interaction are separately labelled.'}
        (out/'RESULT.json').write_text(json.dumps(report,indent=2));bundle=out.with_suffix('.zip');archiveEvidence(out,bundle)
        print('Evidence directory:',out,'\nReturn bundle:',bundle,'\nFull human-qualified release: false',flush=True)
    return 0 if report['automatedQualificationPassed'] else 2
if __name__=='__main__':raise SystemExit(main())
