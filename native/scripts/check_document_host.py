#!/usr/bin/env python3
"""Real controlling-PTY CLI document import/export and failure qualification."""
from pathlib import Path
import argparse,fcntl,json,os,platform,pty,selectors,struct,subprocess,sys,tempfile,termios,time
ROOT=Path(__file__).resolve().parents[1]
def run(argv,interactive,payload=b'\x01X\x05Z\x11'):
 master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',30,96,0,0))
 terminal=master if sys.platform=='darwin' else slave;before=termios.tcgetattr(terminal);capture=bytearray()
 selector=selectors.DefaultSelector();selector.register(master,selectors.EVENT_READ)
 def control():os.setsid();fcntl.ioctl(slave,termios.TIOCSCTTY,0)
 child=subprocess.Popen(argv,stdin=slave,stdout=slave,stderr=slave,preexec_fn=control,env={**os.environ,'TERM':'xterm-256color'})
 def drain():
  if selector.select(.03):
   try:capture.extend(os.read(master,65536))
   except OSError:pass
 try:
  deadline=time.monotonic()+10
  if interactive:
   while b'NOCTURNE' not in capture and child.poll() is None and time.monotonic()<deadline:drain()
   if b'NOCTURNE' not in capture:raise RuntimeError('Host did not enter its UI')
   os.write(master,payload)
  while child.poll() is None and time.monotonic()<deadline:drain()
  if child.poll() is None:raise TimeoutError('Host CLI deadline')
  drain();after=termios.tcgetattr(terminal)
  return {'exitCode':child.returncode,'terminalRestored':after==before,'alternateScreenReleased':b'\x1b[?1049l' in capture,'capturedBytes':len(capture)},bytes(capture)
 finally:
  if child.poll() is None:child.kill();child.wait()
  selector.close();os.close(master);os.close(slave)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--host',choices=['prompt-toolkit','standalone'],default='prompt-toolkit');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
 import prompt_toolkit
 text='é👩\u200d🔧\n日本語'
 with tempfile.TemporaryDirectory() as tmp:
  tmp=Path(tmp);source=tmp/'in.json';saved=tmp/'out.json';info=tmp/'info.json'
  source.write_text(json.dumps(dict(profile='nocturne-document-v1',text=text,caret=2),ensure_ascii=False))
  hostPath=ROOT/('hosts/python/prompt_toolkit_host.py' if args.host=='prompt-toolkit' else 'examples/terminal.py')
  argv=[sys.executable,str(hostPath),'--fps','1','--load-document',str(source),'--save-document',str(saved),'--info-on-exit',str(info)]
  good,raw=run(argv,True);args.output.joinpath('roundtrip-pty.bin').write_bytes(raw)
  document=json.loads(saved.read_text());metadata=json.loads(info.read_text())
  good['documentExact']=document==dict(profile='nocturne-document-v1',text='X'+text+'Z',caret=len(text)+2)
  good['nativeDocumentExact']=metadata['prompt']['text']==document['text'] and metadata['prompt']['caret']==document['caret']
  args.output.joinpath('saved-document.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
  recipes=json.loads((ROOT/'recipes.json').read_text());initial=next(i for i,r in enumerate(recipes) if r['id']=='autumn');expectedScene=recipes[(initial+1)%len(recipes)]['id']
  switch=b'\x1bOQ' if args.host=='standalone' else b'\x1bOS'
  changed,raw=run(argv,True,switch+b'X\x05Z\x11');args.output.joinpath('scene-switch-pty.bin').write_bytes(raw)
  switched=json.loads(saved.read_text());changed['documentExact']=switched==dict(profile='nocturne-document-v1',text=text[:2]+'X'+text[2:]+'Z',caret=len(text)+2)
  switchedInfo=json.loads(info.read_text());changed['nativeDocumentExact']=switchedInfo['prompt']['text']==switched['text'] and switchedInfo['prompt']['caret']==switched['caret']
  changed['sceneChanged']=switchedInfo.get('hostScene')==expectedScene
  undo,raw=run(argv,True,b'X'+switch+b'\x1a\x11');args.output.joinpath('scene-undo-pty.bin').write_bytes(raw)
  undo['documentExact']=json.loads(saved.read_text())==dict(profile='nocturne-document-v1',text=text,caret=2)
  undoInfo=json.loads(info.read_text());undo['sceneChanged']=undoInfo.get('hostScene')==expectedScene
  undo['nativeDocumentExact']=undoInfo['prompt']['text']==text and undoInfo['prompt']['caret']==2
  source.write_text(json.dumps(dict(profile='nocturne-document-v1',text='',caret=0)))
  empty,raw=run(argv,True,switch+b'\x11');args.output.joinpath('empty-scene-switch-pty.bin').write_bytes(raw)
  empty['sceneChanged']=json.loads(info.read_text()).get('hostScene')==expectedScene
  empty['documentExact']=json.loads(saved.read_text())==dict(profile='nocturne-document-v1',text='',caret=0)
  source.write_text(json.dumps(dict(profile='future',text='',caret=0)));saved.write_bytes(b'previous document')
  bad,raw=run(argv,False);args.output.joinpath('rejected-pty.bin').write_bytes(raw);bad['previousSavePreserved']=saved.read_bytes()==b'previous document'
 report={'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'platform':platform.platform(),'host':args.host,'frameworkVersion':prompt_toolkit.__version__ if args.host=='prompt-toolkit' else None,'scope':'Actual Python CLI document roundtrip and rejected-import cleanup in controlling PTYs','roundtrip':good,'sceneSwitch':changed,'emptySceneSwitch':empty,'sceneUndo':undo,'rejectedImport':bad}
 report['passed']=all(x['exitCode']==0 and x['terminalRestored'] and x['alternateScreenReleased'] and x['documentExact'] and x['sceneChanged'] for x in [changed,empty,undo]) and changed['nativeDocumentExact'] and undo['nativeDocumentExact'] and good['exitCode']==0 and good['terminalRestored'] and good['alternateScreenReleased'] and good['documentExact'] and good['nativeDocumentExact'] and bad['exitCode']!=0 and bad['terminalRestored'] and bad['previousSavePreserved']
 args.output.joinpath('RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
