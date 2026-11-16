#!/usr/bin/env python3
"""Measure actual core CRC and snapshot; zlib is an independent correctness oracle."""
import argparse,ctypes,json,sys,time,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--output',required=True);p.add_argument('--iterations',type=int,default=20);args=p.parse_args()
if args.iterations<1:p.error('iterations must be positive')
s=NativeScene(2030,library=args.library)
try:
    snapshot=s.snapshot();data=snapshot[24:];buffer=ctypes.create_string_buffer(data)
    crc=s._lib.nrCrc;crc.argtypes=[ctypes.c_void_p,ctypes.c_uint32];crc.restype=ctypes.c_uint32
    expected=zlib.crc32(data);timings={}
    for name,operation in [('crc',lambda:crc(buffer,len(data))),('snapshot',s.snapshot)]:
        operation();samples=[]
        for _ in range(args.iterations):
            start=time.perf_counter();actual=operation();samples.append(time.perf_counter()-start)
            if name=='crc':assert actual==expected
            else:assert actual==snapshot
        timings[name]={'samplesSeconds':samples,'meanSeconds':sum(samples)/len(samples)}
    result={'library':str(Path(args.library).resolve()),'payloadBytes':len(data),'crc32':expected,'iterations':args.iterations,'timings':timings}
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:s.close()
