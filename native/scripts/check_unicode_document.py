#!/usr/bin/env python3
"""Actual controlling-PTY Unicode document presentation, pointer and save check."""
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
from check_document_host import run
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--host',choices=['standalone','prompt-toolkit'],default='standalone');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
 host_path=ROOT/('examples/terminal.py' if args.host=='standalone' else 'hosts/python/prompt_toolkit_host.py')
 hold_flag='--paused' if args.host=='standalone' else '--reduced-motion'
 with tempfile.TemporaryDirectory() as directory:
  folder=Path(directory);source=folder/'in.json';saved=folder/'out.json';info=folder/'info.json';text='א́👩‍🔧ב'
  source.write_text(json.dumps(dict(profile='nocturne-document-v1',text=text,caret=0),ensure_ascii=False))
  result,raw=run([sys.executable,str(host_path),'--unicode-document',hold_flag,'--fps','1','--load-document',str(source),'--save-document',str(saved),'--info-on-exit',str(info)],True,b'\x1b[<0;1;2M\x1b[<0;1;2mX\x11')
  (args.output/'terminal.bin').write_bytes(raw);document=json.loads(saved.read_text());native=json.loads(info.read_text())
  result['documentExact']=document==dict(profile='nocturne-document-v1',text=text+'X',caret=len(text)+1)
  result['nativeDocumentExact']=native['prompt']['text']==document['text'] and native['prompt']['caret']==document['caret']
  result['unicodeBytesPresented']='א́'.encode() in raw and '👩‍🔧'.encode() in raw
  result['passed']=result['exitCode']==0 and all(result[k] for k in ['terminalRestored','alternateScreenReleased','documentExact','nativeDocumentExact','unicodeBytesPresented'])
  text='L00\n'*40
  source.write_text(json.dumps(dict(profile='nocturne-document-v1',text=text,caret=0)))
  navigation,raw=run([sys.executable,str(host_path),'--unicode-document',hold_flag,'--fps','1','--load-document',str(source),'--save-document',str(saved),'--info-on-exit',str(info)],True,b'\x1b[<65;1;2M\x1b[<0;1;2M\x1b[<0;1;2mX\x11')
  (args.output/'scroll-terminal.bin').write_bytes(raw)
  navigation['documentExact']=json.loads(saved.read_text())==dict(profile='nocturne-document-v1',text=text[:12]+'X'+text[12:],caret=13)
  navigation['passed']=navigation['exitCode']==0 and navigation['terminalRestored'] and navigation['alternateScreenReleased'] and navigation['documentExact']
  result['navigation']=navigation;result['passed']=result['passed'] and navigation['passed']
  result['host']=args.host
  result['sourceFiles']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [host_path,ROOT/'hosts/python/unicode_document_view.py',ROOT/'bindings/python/nocturne_native.py',ROOT/'src/bidi.c']}
  (args.output/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
