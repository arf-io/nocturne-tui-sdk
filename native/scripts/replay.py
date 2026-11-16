#!/usr/bin/env python3
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
s=NativeScene(seed=2030)
for index,line in enumerate(sys.stdin):
    while s.command_raw(line.encode())==1:pass
    f=s.render();state=s.snapshot()
    print(json.dumps({'index':index,'frame':hashlib.sha256(f.bytes).hexdigest(),'state':hashlib.sha256(state).hexdigest(),'metadata':s.info(),'motions':s.particle_motions()},separators=(',',':')))
