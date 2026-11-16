#!/usr/bin/env python3
"""Measure current C rendering only, separately from terminal output and font rasterization."""
from pathlib import Path
import sys,json,time,statistics,platform
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
rows=[]
for recipe in json.loads((ROOT/'recipes.json').read_text()):
 with NativeScene()as s:
  s.command({'op':'resize','width':160,'height':48})
  for command in recipe['commands']:s.command(command)
  s.advance_to(900000)
  for _ in range(3):s.render()
  samples=[]
  for i in range(40):
   s.advance_to(900000+i*16667);t=time.perf_counter_ns();s.render();samples.append((time.perf_counter_ns()-t)/1e6)
  samples.sort();rows.append({'scene':recipe['id'],'medianMs':round(statistics.median(samples),3),'p95Ms':round(samples[int(len(samples)*.95)-1],3),'maxMs':round(max(samples),3)})
result={'scope':'Warm native render plus copied frame only, 160x48, 40 samples per scene. Not physical 60 FPS or end-to-end input latency.','platform':platform.platform(),'scenes':rows}
(ROOT/'evidence/benchmark.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
