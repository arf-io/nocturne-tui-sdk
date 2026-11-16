#!/usr/bin/env python3
"""Render an exported Fleet scene with the native Python binding, or print its hash.
Usage: python3 examples/fleet_scene.py scene.json [--hash]
"""
from pathlib import Path
import argparse,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from fleet_scene import renderFleetScene
from terminal import AnsiWriter
p=argparse.ArgumentParser(description=__doc__);p.add_argument('scene',type=Path);p.add_argument('--hash',action='store_true');a=p.parse_args()
if a.scene.stat().st_size>4*1024*1024:p.error('Scene limit: 4 MiB')
f=renderFleetScene(json.loads(a.scene.read_text()))
if a.hash:print(hashlib.sha256(f.tobytes()).hexdigest())
else:print(AnsiWriter().encode(f)+'\x1b[0m',end='',flush=True)
