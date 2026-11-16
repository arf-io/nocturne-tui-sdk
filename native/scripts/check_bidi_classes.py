#!/usr/bin/env python3
"""Execute every pinned BidiTest class sequence and requested paragraph mode."""
import argparse,ctypes as C,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
SCALARS=dict(zip('L R AL EN AN ES ET CS NSM BN B S WS ON LRE LRO RLE RLO PDF LRI RLI FSI PDI'.split(),[65,0x5d0,0x627,49,0x661,43,36,44,0x300,0xad,10,9,32,33,0x202a,0x202d,0x202b,0x202e,0x202c,0x2066,0x2067,0x2068,0x2069]))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();source=ROOT/'unicode/17.0.0/BidiTest.txt';raw=source.read_bytes()
 pinned=next(r['sha256'] for r in json.loads((source.parent/'SOURCES.json').read_text())['sources'] if r['name']==source.name)
 if hashlib.sha256(raw).hexdigest()!=pinned:raise SystemExit('Bidi class source hash mismatch')
 total=sequences=0;failures=[];levels=order=None
 with NativeScene() as scene:
  fn=scene._lib.nrBidiVisual;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
  for lineNumber,line in enumerate(raw.decode().splitlines(),1):
   line=line.split('#')[0].strip()
   if not line:continue
   if line.startswith('@Levels:'):levels=[None if x=='x' else int(x) for x in line.split(':')[1].split()];continue
   if line.startswith('@Reorder:'):order=[int(x) for x in line.split(':')[1].split()];continue
   if line.startswith('@'):raise ValueError('Unknown directive')
   text,mask=line.split(';');scalars=[SCALARS[name] for name in text.split()];bits=int(mask,16);sequences+=1
   if levels is None or order is None or len(levels)!=len(scalars):raise ValueError('Invalid fixture')
   values=(C.c_uint32*max(1,len(scalars)))(*scalars);out=(C.c_uint32*(max(1,len(scalars))*4))()
   for bit,direction in [(1,2),(2,0),(4,1)]:
    if not bits&bit:continue
    total+=1;n=fn(values,len(scalars),direction,out,len(scalars));actualOrder=[out[i*4] for i in range(max(0,n))];actualLevels=[None]*len(scalars)
    for i in range(max(0,n)):actualLevels[out[i*4]]=out[i*4+2]
    if n<0 or actualLevels!=levels or actualOrder!=order:failures.append(dict(line=lineNumber,input=text,direction=direction,expectedLevels=levels,actualLevels=actualLevels,expectedOrder=order,actualOrder=actualOrder))
 nativeHash=hashlib.sha256(Path(scene._lib._name).read_bytes()).hexdigest()
 sourceFiles={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/bidi.c',ROOT/'src/unicode_bidi.inc',ROOT/'include/nocturne_native.h']}
 report=dict(nativeLibrarySha256=nativeHash,sourceFiles=sourceFiles,schema='nr-bidi-class-conformance-v1',unicodeVersion='17.0.0',sourceSha256=pinned,sequences=sequences,total=total,mismatches=len(failures),passed=bool(total) and not failures,failures=failures[:20])
 if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='failures'}));print(json.dumps(failures[:3],indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
