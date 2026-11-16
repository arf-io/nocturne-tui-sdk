"""Finite rotating water, constant waves and layered application diagnostics.

Emit an owned JSON report with independent geometry/height references. Optional
--frames writes native cell buffers for each screen; no bundled fonts are used.
"""
import argparse,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

def near(actual,expected,tolerance=1e-9):
 if len(actual)!=len(expected) or any(abs(a-b)>tolerance for a,b in zip(actual,expected)):raise RuntimeError('Independent rotating surface reference differs')

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--frames',type=Path);args=parser.parse_args()
 if args.frames is not None:args.frames.mkdir(parents=True,exist_ok=True)
 samples=[];omega=math.pi/2
 with NativeScene(seed=2030) as scene:
  for command in [dict(op='resize',width=100,height=40),dict(op='camera',position=[8,6,12],yaw=-33,pitch=-12,fov=67),dict(op='surface',id=1),dict(op='mesh',triangles=[dict(a=[0,0,0],b=[4,0,0],c=[0,0,4],surfaceId=1,color=0x42b9ef,alpha=.7)]),dict(op='surface-fluid',surfaceId=1,mass=3,velocity=[.25,0,0]),dict(op='surface-fluid-angular',surfaceId=1,inertia=3,omega=[0,0,omega]),dict(op='surface-waves',surfaceId=1,waves=[[.5,0,0,0,0]])]:scene.command(command)
  initial=scene.snapshot()
  for time in [0,250000,500000]:
   scene.advance_to(time);seconds=time/1e6;angle=omega*seconds;sine=math.sin(angle);cosine=math.cos(angle);offset=.25*seconds
   before=scene.snapshot();triangles=scene.surface_triangles(1);near(triangles[0][1:10],[offset-.5*sine,.5*cosine,0,offset+4*cosine-.5*sine,4*sine+.5*cosine,0,offset-.5*sine,.5*cosine,4])
   x=offset+cosine-.5*sine;height=sine+.5*cosine;sample=scene.surface_wave_sample(1,x,1)
   near(sample,[height,-sine,cosine,0,omega*(cosine-.5*sine),0])
   angular=scene.surface_fluid_angular(1);near(angular,[3,0,0,omega,0,0,3*omega,0,0,0,0,1.5*omega*omega])
   pose=scene.info()['surfaceFluidAngular'][0]['pose'];near(pose['orientation'],[0,0,math.sin(angle/2),math.cos(angle/2)],5.1e-7)
   if scene.snapshot()!=before:raise RuntimeError('Public inspection modified source')
   scene.command(dict(op='window',id=1,title='Rotating water / scene inspector',position=[2,2,0],width=46,height=16,alpha=.82,text=f'Time {seconds:.2f} s\nWorld omega Z: {omega:.6f}\nFinite inertia: 3\nTranslation X: 0.25 / s\nWave height: 0.5\nSurface alpha: 0.7\nSample height: {sample[0]:.6f}\nNormal: {sample[1:4]}\nMaterial vertical speed: {sample[4]:.6f}'))
   scene.command(dict(op='window',id=2,title='Application status',position=[8,6,-2],width=44,height=11,alpha=.65,text='Public SDK queries + retained scene\nWave, rotation and translation compose\nInspection and rendering preserve state\nStop freezes reservoir orientation'))
   authored=scene.snapshot();frame=scene.render()
   if scene.snapshot()!=authored:raise RuntimeError('Application rendering modified source')
   if args.frames is not None:(args.frames/f'rotating-surface-{time}.cells').write_bytes(frame.bytes)
   visible=sorted({row[3]&0xffff for row in frame.words() if row[3]&0xffff0000==0x50000000})
   samples.append(dict(timeUs=time,visibleWindowIds=visible,triangles=triangles,waveSample=sample,angular=angular,pose=pose,queryPure=True,renderPure=True))
  scene.command(dict(op='stop-surface-fluid',surfaceId=1));frozen=scene.info()['surfaceFluidAngular'][0]['pose'];scene.advance_to(1000000)
  if scene.info()['surfaceFluidAngular'][0]['pose']!=frozen:raise RuntimeError('Stop advanced pose')
  scene.restore(initial);scene.advance_to(500000);near(scene.surface_triangles(1)[0][1:10],samples[-1]['triangles'][0][1:10])
  args.output.write_text(json.dumps(dict(schema='nocturne.rotating-surface-example.v1',samples=samples,stopFrozen=True,replayGeometry=True,reference='independent rigid rotation and material velocity',sceneOptions=['finite-translation','finite-angular-inertia','constant-wave','mesh-alpha','layered-windows']),indent=2)+'\n')

if __name__=='__main__':main()
