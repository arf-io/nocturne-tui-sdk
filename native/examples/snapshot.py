#!/usr/bin/env python3
"""Write an owned native frame and metadata; does not own a terminal."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
with NativeScene(seed=2030) as scene:
    scene.command({'op':'emitter','id':1,'effect':'weather/autumn-drift','count':40})
    scene.advance_to(900000)
    frame=scene.render()
    Path('preview.cells').write_bytes(frame.bytes)
    print(json.dumps(scene.info(),indent=2))
