#!/usr/bin/env python3
"""Exercise the actual Bubble Tea Unicode profile in a controlling PTY."""
import argparse,hashlib,json,tempfile
from pathlib import Path
from check_document_host import run
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--host',choices=['bubbletea','ratatui'],default='bubbletea');p.add_argument('--binary',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 with tempfile.TemporaryDirectory() as folder:
  info=Path(folder)/'info.json';text='א́👩‍🔧ב'
  result,raw=run([a.binary,'--unicode-document','--paused','--document-text='+text,'--info-on-exit='+str(info)],True,b'\x1b[<0;1;2M\x1b[<0;1;2mX\x11')
  result['sourceExact']=json.loads(info.read_text())['prompt']['text']==text+'X'
  result['wholeClustersPresented']=all(s.encode() in raw for s in ['א́','👩‍🔧'])
  result['passed']=result['exitCode']==0 and all(result[k] for k in ['terminalRestored','alternateScreenReleased','sourceExact','wholeClustersPresented'])
  result['host']=a.host
  sources=[ROOT/'hosts/bubbletea/main.go',ROOT/'hosts/bubbletea/unicode_document.go',ROOT/'bindings/go/nocturne.go'] if a.host=='bubbletea' else [ROOT/'hosts/ratatui/src/lib.rs',ROOT/'hosts/ratatui/examples/unicode_document.rs',ROOT/'bindings/rust/src/lib.rs']
  result['binarySha256']=hashlib.sha256(Path(a.binary).read_bytes()).hexdigest()
  cases=[]
  recipes=[('shift-navigation',b'\x1b[H\x1b[1;2C\x1b[1;2C\x1b[1;2CX\x11'),('drag-selection',b'\x1b[<0;1;2M\x1b[<32;4;2M\x1b[<0;4;2mX\x11')]
  if a.host=='ratatui':recipes.append(('modal-roundtrip',b'\x1bOPZ\x1b[C\x1bOP\x1b[H\x1b[1;2C\x1b[1;2C\x1b[1;2CX\x11'))
  for name,payload in recipes:
   case,terminal=run([a.binary,'--unicode-document','--paused','--document-text=ABC','--info-on-exit='+str(info)],True,payload)
   case['sourceExact']=json.loads(info.read_text())['prompt']['text']=='X'
   case['passed']=case['exitCode']==0 and case['terminalRestored'] and case['alternateScreenReleased'] and case['sourceExact']
   case['name']=name;cases.append(case);(a.output/(name+'.bin')).write_bytes(terminal)
  result['interactions']=cases;result['passed']=result['passed'] and all(c['passed'] for c in cases)
  result['sourceFiles']={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources+[ROOT/'src/bidi.c']}
  (a.output/'terminal.bin').write_bytes(raw);(a.output/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
