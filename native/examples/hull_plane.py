"""Consume owned oriented-hull queries and present their result in a window.

This displaced-volume example uses vertical lift; it is not a pressure solver.
Run with --output report.json and optionally --frame window.cells.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--frame',type=Path);args=parser.parse_args()
 vertices=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
 faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]]
 with NativeScene(seed=2030) as scene:
  before=scene.snapshot();point=[0,0,0];normal=[-1,1,0]
  immersion=scene.hull_immersion_plane(vertices,faces,point,normal)
  wrench=scene.hull_buoyancy_plane(vertices,faces,point,normal,density=1000,gravity=10,mass=4000,center_of_mass=[0,0,0])
  expected=[8,4,1/3,-1/3,0,0,0,0,0,0,40000/3]
  if any(abs(a-b)>1e-8 for a,b in zip(wrench,expected)) or any(abs(a-b)>1e-8 for a,b in zip(immersion,expected[:5])):raise RuntimeError('Independent diagonal-box reference differs')
  if scene.snapshot()!=before:raise RuntimeError('Hull queries modified scene')
  text=f'Total volume: {immersion[0]:.3f}\nDisplaced: {immersion[1]:.3f}\nCentroid: {immersion[2:]}\nNet force: {wrench[5:8]}\nTorque: {wrench[8:11]}\nModel: vertical displaced-volume lift'
  scene.command(dict(op='window',id=1,title='Oriented hull / application diagnostics',text=text,width=48,height=18,alpha=.85))
  authored=scene.snapshot();frame=scene.render()
  if scene.snapshot()!=authored:raise RuntimeError('Diagnostic rendering modified scene')
  if args.frame is not None:args.frame.write_bytes(frame.bytes)
  args.output.write_text(json.dumps(dict(schema='nocturne.hull-plane-example.v1',point=point,normal=normal,immersion=immersion,wrench=wrench,queryPure=True,renderPure=True,analyticReference='unit box cut by y <= x',windowId=1),indent=2)+'\n')

if __name__=='__main__':main()
