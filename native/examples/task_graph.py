#!/usr/bin/env python3
"""Execute the standalone task/work graph with the direct Python/C binding.

Usage: python3 native/examples/task_graph.py --output /new/path/graph --dimensions 3
Build native first. Output is synthetic owned cells, metadata and a state snapshot;
this headless exporter does not own a terminal, clock, provider or display server.
"""
from pathlib import Path
import argparse, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene


def exportGraph(output: Path, dimensions: int = 3, library: Path | None = None) -> dict:
    """Execute canonical NDJSON commands and export a fixed-time native frame.

    Args: new output directory, dimensions 2 or 3, optional built C library path.
    Returns the frame/hash receipt. Raises ValueError on invalid dimensions, native
    command rejection, or an existing destination; filesystem errors propagate.
    """
    if dimensions not in (2,3):raise ValueError('dimensions must be 2 or 3')
    output.mkdir(parents=True,exist_ok=False)
    with NativeScene(2030,library=library) as scene:
        for line in (ROOT/'examples/task_graph.ndjson').read_text().splitlines():
            if line:scene.command(json.loads(line))
        if dimensions!=3:
            scene.command({'op':'camera','profile':'default','position':[0,8,162],'yaw':0,'pitch':0,'roll':0,'fov':64,'orthographic':False})
            scene.command({'op':'layout','mode':'layered','dimensions':dimensions,'spacing':30})
        scene.advance_to(900000)
        snapshot=scene.snapshot();frame=scene.render();info=scene.info()
        if scene.snapshot()!=snapshot:raise RuntimeError('render mutated authoritative graph state')
        (output/'graph.cells').write_bytes(frame.bytes)
        (output/'graph.snapshot').write_bytes(snapshot)
        (output/'graph-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
        report={'dimensions':dimensions,'width':frame.width,'height':frame.height,
                'frameSha256':hashlib.sha256(frame.bytes).hexdigest(),
                'nodeIds':[n['id'] for n in info['nodes']],'renderPure':True,'timeUs':900000}
        (output/'GRAPH.json').write_text(json.dumps(report,indent=2)+'\n')
        return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--dimensions',type=int,choices=(2,3),default=3)
    parser.add_argument('--library',type=Path)
    args=parser.parse_args()
    print(json.dumps(exportGraph(args.output,args.dimensions,args.library),indent=2))
