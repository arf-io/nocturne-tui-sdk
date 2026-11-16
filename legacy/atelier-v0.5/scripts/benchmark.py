"""Measure this runtime's render/encoding costs. Not end-to-end display latency."""
from pathlib import Path
import json
import platform
import statistics
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne import Surface
from terminal import AnsiWriter
rows=[]
for preset in json.loads((ROOT/'presets.json').read_text()):
    surface=Surface(width=84,height=28,**preset['values'])
    if 'palette' in preset:surface.setPalette(preset['palette'])
    if 'starPalette' in preset:surface.setStarPalette(preset['starPalette'])
    writer=AnsiWriter();times=[];encoding=[];bytesOut=[]
    for i in range(65):
        start=time.perf_counter_ns()
        frame=surface.render(6000+i*1000//30,text='live terminal material')
        mid=time.perf_counter_ns()
        encoded=writer.encode(frame)
        end=time.perf_counter_ns()
        if i>=5:
            times.append((mid-start)/1e6);encoding.append((end-mid)/1e6);bytesOut.append(len(encoded.encode()))
    rows.append({'preset':preset['id'],'medianRenderMs':round(statistics.median(times),3),'medianDiffEncodingMs':round(statistics.median(encoding),3),'medianBytesPerMotionFrame':round(statistics.median(bytesOut))})
report={'platform':platform.platform(),'python':platform.python_version(),'dimensions':[84,28],'measuredFramesPerPreset':60,'includesPythonBindingAllocation':True,'includesActualTerminalWrites':False,'results':rows}
(ROOT/'dist/benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
