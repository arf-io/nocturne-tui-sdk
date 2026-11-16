#!/usr/bin/env python3
"""Run every pinned Unicode 17 BidiCharacterTest case through actual native C."""
import argparse,ctypes as C,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
 source=ROOT/'unicode/17.0.0/BidiCharacterTest.txt';raw=source.read_bytes()
 pinned=next(r['sha256'] for r in json.loads((source.parent/'SOURCES.json').read_text())['sources'] if r['name']==source.name)
 if hashlib.sha256(raw).hexdigest()!=pinned:raise SystemExit('Bidi character source hash mismatch')
 total=0;failures=[]
 with NativeScene() as scene:
  fn=scene._lib.nrBidiVisual;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
  for lineNumber,line in enumerate(raw.decode().splitlines(),1):
   fields=[p.strip() for p in line.split('#')[0].split(';')]
   if len(fields)!=5:continue
   scalars=[int(c,16) for c in fields[0].split()];direction=int(fields[1]);expectedLevels=[None if x=='x' else int(x) for x in fields[3].split()];expectedOrder=[int(x) for x in fields[4].split()]
   values=(C.c_uint32*max(1,len(scalars)))(*scalars);out=(C.c_uint32*(max(1,len(scalars))*4))();n=fn(values,len(scalars),direction,out,len(scalars));total+=1
   order=[out[i*4] for i in range(max(0,n))];levels=[None]*len(scalars)
   for i in range(max(0,n)):levels[out[i*4]]=out[i*4+2]
   if n<0 or order!=expectedOrder or levels!=expectedLevels:
    failures.append(dict(line=lineNumber,input=fields[0],direction=direction,expectedLevels=expectedLevels,actualLevels=levels,expectedOrder=expectedOrder,actualOrder=order))
 nativeHash=hashlib.sha256(Path(scene._lib._name).read_bytes()).hexdigest()
 sourceFiles={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/bidi.c',ROOT/'src/unicode_bidi.inc',ROOT/'include/nocturne_native.h']}
 report=dict(nativeLibrarySha256=nativeHash,sourceFiles=sourceFiles,schema='nr-bidi-character-conformance-v1',unicodeVersion='17.0.0',sourceSha256=pinned,total=total,mismatches=len(failures),passed=bool(total) and not failures,failures=failures[:20])
 if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='failures'}));print(json.dumps(failures[:3],indent=2))
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
