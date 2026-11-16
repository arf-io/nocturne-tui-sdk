"""Consume finite-mass drag results in an application diagnostic window.

Run with --output result.json, optionally --frame window.cells. This pure
exchange calculation does not configure a retained surface or fluid solver.
"""
import argparse,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--frame',type=Path);args=parser.parse_args()
 with NativeScene(seed=2030) as scene:
  before=scene.snapshot();a=[5,-2,1];b=[-1,3,0];row=scene.fluid_drag_exchange(2,3,4,.5,a,b)
  fraction=-math.expm1(-4*.5*(1/2+1/3));impulse=[1.2*fraction*(x-y) for x,y in zip(a,b)]
  expected=[x-j/2 for x,j in zip(a,impulse)]+[y+j/3 for y,j in zip(b,impulse)]+impulse+[.6*sum((x-y)**2 for x,y in zip(a,b))*fraction*(2-fraction)]
  if len(row)!=10 or any(abs(x-y)>1e-9 for x,y in zip(row,expected)):raise RuntimeError('Independent exchange reference differs')
  momentum=[2*x+3*y for x,y in zip(row[:3],row[3:6])]
  if any(abs(x-(2*u+3*v))>1e-9 for x,u,v in zip(momentum,a,b)):raise RuntimeError('Exchange lost momentum')
  initial_energy=sum(x*x for x in a)+1.5*sum(y*y for y in b)
  final_energy=sum(x*x for x in row[:3])+1.5*sum(y*y for y in row[3:6])
  if abs(initial_energy-final_energy-row[9])>1e-9:raise RuntimeError('Exchange energy ledger differs')
  inertias=[2,4,8];water_inertias=[3,5,7];conductances=[4,0,2]
  angular=scene.angular_drag_exchange(inertias,water_inertias,conductances,.5,a,b)
  angular_energy=0
  for axis in range(3):
   inertia= inertias[axis];water_inertia=water_inertias[axis]
   attenuation=-math.expm1(-conductances[axis]*.5*(1/inertia+1/water_inertia));reduced=inertia*water_inertia/(inertia+water_inertia)
   angular_impulse=reduced*attenuation*(a[axis]-b[axis]);angular_energy+=.5*reduced*(a[axis]-b[axis])**2*attenuation*(2-attenuation)
   if abs(angular[axis]-(a[axis]-angular_impulse/inertia))>1e-9 or abs(angular[axis+3]-(b[axis]+angular_impulse/water_inertia))>1e-9:raise RuntimeError('Independent angular reference differs')
   if abs(inertia*angular[axis]+water_inertia*angular[axis+3]-(inertia*a[axis]+water_inertia*b[axis]))>1e-9:raise RuntimeError('Angular exchange lost momentum')
  if abs(angular[9]-angular_energy)>1e-9:raise RuntimeError('Rotational energy ledger differs')
  if scene.snapshot()!=before:raise RuntimeError('Exchange query modified source')
  text=f'Body mass 2 / water mass 3\nConductance 4 / elapsed 0.5 s\nBody velocity: {row[:3]}\nWater velocity: {row[3:6]}\nWater impulse: {row[6:9]}\nDissipated energy: {row[9]:.6f}\nConserved momentum: {momentum}'
  text+=f'\nShared principal-frame angular exchange\nBody omega: {angular[:3]}\nWater omega: {angular[3:6]}\nAngular impulse: {angular[6:9]}\nRotational dissipation: {angular[9]:.6f}'
  scene.command(dict(op='window',id=1,title='Finite exchange / application diagnostics',text=text,width=56,height=24,alpha=.85))
  authored=scene.snapshot();frame=scene.render()
  if scene.snapshot()!=authored:raise RuntimeError('Rendering modified source')
  if args.frame is not None:args.frame.write_bytes(frame.bytes)
  args.output.write_text(json.dumps(dict(schema='nocturne.fluid-exchange-example.v1',result=row,angularResult=angular,angularFrame='explicit-shared-principal',momentum=momentum,initialEnergy=initial_energy,finalEnergy=final_energy,queryPure=True,renderPure=True,analyticReference='exact finite-mass and diagonal finite-inertia exchange',windowId=1),indent=2)+'\n')

if __name__=='__main__':main()
