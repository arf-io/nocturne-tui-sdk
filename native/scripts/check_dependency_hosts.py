#!/usr/bin/env python3
"""Execute real Terminal Kit/Bubble Tea PTY cases against already built SDK hosts.

Every case owns a controlling PTY, requires observed raw entry, and records actual
exit plus complete termios/protocol restoration before parent cleanup. No source
writes, downloads, fake frameworks or background acceptance. Linux/POSIX only.
"""
from __future__ import annotations
import argparse,json,math,os,signal,sys
from pathlib import Path
from dependency_pty import PtyProbe,writeJson,digest,timestamp
ROOT=Path(__file__).resolve().parents[2]

def exerciseInput(p):
 for raw,text,caret in [(b'abc','abc',3),(b'\x1b[D','abc',2),('é'.encode(),'abéc',3),(b'\x1b[F','abéc',4),
                        (b'\x1b[200~ "\\Z\x1b[201~','abéc "\\Z',8),(b'\x7f','abéc "\\',7)]:
  p.send(raw);p.wait(lambda:p.info().get('prompt',{}).get('text')==text and p.info()['prompt']['caret']==caret,'native edit/paste/caret '+repr(text))
  assert p.info()['clock']['timeUs']==0,'held input advanced time'
 p.wait(lambda:p.visible('abéc'),'actual terminal displays typed Unicode')
 p.resize(100,30)
 p.wait(lambda:any(r.get('width')==100 and r.get('height')==30 for r in p.records()),'PTY resize reaches native frame')
 p.wait(lambda:p.visible('NOCTURNE HOST QUALIFICATION'),'actual native title repainted after resize')
 assert p.info()['clock']['timeUs']==0,'resize advanced held simulation'

def exercisePointer(p):
 def state():
  rows=p.info().get('registeredStates',[]);return rows[0].get('states',{}) if rows else {}
 for data,key,val in [(b'\x1b[<35;10;11M','hover',True),(b'\x1b[<0;10;11M','pressed',True),(b'\x1b[<0;10;11m','pressed',False),(b'\x1b[O','hover',False)]:
  p.send(data);p.wait(lambda:state().get(key) is val,f'native {key}={val}')
 assert state().get('selected') is True,'native click did not select'
 # Releasing outside the widget and native camera drag must stay distinct.
 before=p.info()['camera'];p.send(b'\x1b[<0;50;17M\x1b[<32;55;17M\x1b[<0;55;17m')
 p.wait(lambda:p.info().get('camera')!=before,'actual left-drag changes native camera')
 before=p.info()['camera'];p.send(b'\x1b[<2;50;17M\x1b[<34;55;17M\x1b[<2;55;17m')
 p.wait(lambda:p.info().get('camera')!=before,'actual right-drag pans native camera')
 assert p.info()['clock']['timeUs']==0,'pointer advanced held time'
 assert p.info()['fieldCount']==0,'pointer generated text weather'

def runCase(host,scenario,argv,cwd,env,out,timeout):
 env=dict(env,NOCTURNE_TEST_SCENARIO=scenario,NOCTURNE_TEST_FIXTURE=str(ROOT/'native/tests/fixtures/dependency-hosts.ndjson'))
 try:p=PtyProbe(argv,cwd,env,out,host+'-'+scenario,timeout)
 except OSError:
  return json.loads((out/(host+'-'+scenario+'.json')).read_text())
 try:
  if scenario=='setup':
   p.wait(lambda:p.raw() and any(r['event']=='setup-raw' for r in p.records()),'observed raw partial startup before injected failure')
   p.send(b'\x11');p.finish(1)
   assert b'intentional partial-startup' in p.output,'wrong startup failure'
  else:
   p.waitReady('NOCTURNE HOST QUALIFICATION' if not scenario.startswith('cli-') else 'NOCTURNE')
   if not scenario.startswith('cli-'):
    p.wait(lambda:bool(p.info()),'native state observation')
    assert all(p.screen.modes.get(n) is True for n in (1003,1006,1004,2004)),'required input reporting absent'
   if scenario=='input':exerciseInput(p)
   elif scenario=='pointer':exercisePointer(p)
   elif scenario=='normal':p.wait(lambda:p.info()['clock']['timeUs']>0,'normal host clock advances native simulation')
   if scenario=='paste-reject':
    p.send(b'retained');p.wait(lambda:p.info().get('prompt',{}).get('text')=='retained','precondition before invalid pasted control')
    p.send(b'\x1b[200~\x11\x1b[201~');p.finish(1)
    assert b'State invariant rejected' in p.output,'paste must reach native rejection, not a successful quit shortcut'
    assert p.info()['prompt']['text']=='retained','invalid paste modified accepted input'
   elif scenario in ('error','exception','rejection','panic'):
    p.send(b'\x11' if host=='bubbletea' else b'\x14');p.finish(1)
    if scenario=='error':assert b'Unknown or not-yet-implemented' in p.output,'missing native error output'
    else:assert b'intentional qualification' in p.output,'missing injected failure output'
   else:p.send(b'\x03' if scenario in ('ctrlc','cli-ctrlc') else b'\x11');p.finish(0)
  if not scenario.startswith('cli-'):assert p.records()[-1]['event']=='exit','missing final native observation'
 except BaseException as e:
  p.result.update(status='TIMEOUT' if isinstance(e,TimeoutError) else 'INTERRUPTED' if isinstance(e,KeyboardInterrupt) else 'FAIL',accepted=False,reason=repr(e))
  if isinstance(e,KeyboardInterrupt):raise
 finally:p.close()
 print(p.name,p.result['status'],'exit',p.result.get('exitCode'),p.result.get('reason',''),flush=True)
 return p.result

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--host',choices=['terminal-kit','bubbletea','both'],default='both');ap.add_argument('--bubbletea-bin',type=Path);ap.add_argument('--bubbletea-fixture',type=Path)
 ap.add_argument('--evidence-dir',type=Path,required=True);ap.add_argument('--timeout',type=float,default=20)
 args=ap.parse_args();out=args.evidence_dir.resolve()
 if out.exists() or out.is_relative_to(ROOT):ap.error('new external evidence directory required')
 if args.host in ('bubbletea','both') and (not args.bubbletea_bin or not args.bubbletea_fixture):ap.error('Bubble Tea binaries required')
 if not math.isfinite(args.timeout) or args.timeout<=0:ap.error('positive finite timeout required')
 if not sys.platform.startswith('linux'):ap.error('these PTY checks require Linux; other platforms are not qualified')
 out.mkdir(parents=True);rows=[];report={'schema':'nocturne.dependency-hosts.pty.v1','status':'RUNNING','startedAt':timestamp(),'cases':rows,'fullRC4Qualified':False}
 path=out/'QUALIFICATION.json';writeJson(path,report)
 def interrupted(signum,frame):raise KeyboardInterrupt(f'signal {signum}')
 old=signal.signal(signal.SIGTERM,interrupted)
 try:
  for host in ['terminal-kit','bubbletea'] if args.host=='both' else [args.host]:
   cli=['node',str(ROOT/'native/hosts/terminal-kit/host.mjs')] if host=='terminal-kit' else [str(args.bubbletea_bin.resolve())]
   fixture=['node',str(ROOT/'native/hosts/terminal-kit/qualification.mjs')] if host=='terminal-kit' else [str(args.bubbletea_fixture.resolve())]
   for scenario in ['cli-ctrlq','cli-ctrlc','normal','input','pointer','ctrlc','paste-reject','error',*(['exception','rejection'] if host=='terminal-kit' else ['panic']),'setup']:
    row=runCase(host,scenario,cli if scenario.startswith('cli-') else fixture,ROOT,os.environ.copy(),out,args.timeout);rows.append(row);writeJson(path,report)
  states={r['status'] for r in rows}
  report['status']=next((s for s in ('TIMEOUT','BLOCKED','FAIL') if s in states),'PASS')
 except BaseException as error:
  report.update(status='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAIL',reason=repr(error))
 finally:
  signal.signal(signal.SIGTERM,old);report['finishedAt']=timestamp();writeJson(path,report)
 return {'PASS':0,'FAIL':2,'BLOCKED':3,'TIMEOUT':4,'INTERRUPTED':130}[report['status']]
if __name__=='__main__':raise SystemExit(main())
