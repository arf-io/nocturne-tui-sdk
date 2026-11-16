#!/usr/bin/env python3
"""Build and export a shared-field ocean through the public Python/C SDK.

Usage: python3 native/examples/shared_ocean.py --output /new/path/ocean
Build native first. Output includes owned frames, source commands, snapshots,
metadata and deterministic replay evidence. No terminal or service is required.
"""
from pathlib import Path
import argparse,hashlib,json,math,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

def build_scene(scene):
    """Assemble ordinary reusable SDK components; return their authoring commands."""
    commands=[]
    def send(**command):commands.append(command);scene.command(command)
    send(op='resize',width=100,height=40)
    send(op='environment',background=0x081322,stars=0,sampling='braille')
    send(op='camera',position=[0,10,20],pitch=-27,span=24,orthographic=True)
    send(op='prompt',active=False,alpha=0)
    send(op='floor',enabled=False,visible=False)
    send(op='surface',id=1,restitution=.15,friction=.15,settleSpeed=0,wetnessGain=.002)
    triangles=[]
    for z in range(8):
        for x in range(8):
            a=[-8+x*2,0,-8+z*2];b=[a[0]+2,0,a[2]];c=[a[0],0,a[2]+2];d=[b[0],0,c[2]]
            triangles += [dict(a=a,b=c,c=b,surfaceId=1,color=0x176786),dict(a=b,b=c,c=d,surfaceId=1,color=0x176786)]
    send(op='mesh',sampling='braille',triangles=triangles)
    send(op='surface-waves',surfaceId=1,waves=[[.18,.45,.15,1.3,0],[.09,-.2,.6,.8,1],[.04,.8,-.35,2.1,.4]])
    send(op='surface-foam',surfaceId=1,sourceRate=.6,curvatureThreshold=.01,decay=.5,impactGain=.08,color=0xe2f2ef)
    send(op='ribbon',points=[[-9,1,-9],[9,1,-9],[9,1,9],[-9,1,9]],width=1,closed=True,color=0x79716a,append=True)
    send(op='model-import',schema='nocturne.model/v1',units='meters',coordinates='right-handed-y-up',vertices=[[-2,0,9],[-2,2,9],[2,0,9],[2,2,9]],materials=[dict(color=0x9a8c73)],triangles=[dict(indices=[0,1,2],material=0),dict(indices=[2,1,3],material=0)],append=True)
    for ident,x,z,radius,color in [(1,-3,-2,.55,0xf5b642),(2,2,-1,.45,0xeb7255),(3,0,3,.65,0xb2c66b)]:
        send(op='float-body',id=ident,surfaceId=1,position=[x,0,z],radius=radius,mass=1000*2*math.pi*radius**3/3,drag=3,color=color)
    send(op='emitter',id=1,effect='weather/rain-threads',shape='box',count=80,runningTimeMs=4000,position=[0,.7,0],extent=[12,0,12],velocity=[0,-8,0],spread=[0,0,0],gravity=[0,-9.81,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],sizeMin=.04,sizeMax=.06,lifetimeMinMs=1000,lifetimeMaxMs=1000,deposit=False,collision=True,colliders=dict(surfaces=[1]),sampling='braille')
    send(op='node',id=1,label='SHARED OCEAN',kind='sample',position=[-6,2,0],color=0x83c8e5)
    send(op='path-travel',id=1,target=dict(family='node',id=1),points=[[-6,2,-6],[6,2,-6],[6,2,6],[-6,2,6]],closed=True,mode='loop',speed=3)
    return commands

def export_ocean(output,library=None):
    output.mkdir(parents=True,exist_ok=False)
    receipt={'scene':'shared-ocean','abi':1,'captures':[],'renderPure':True,'replayExact':False}
    with NativeScene(2030,library=library) as scene:
        commands=build_scene(scene)
        (output/'scene.ndjson').write_text(''.join(json.dumps(c,separators=(',',':'))+'\n' for c in commands))
        checkpoint=None
        for tick in [0,500000,1000000,2000000,4000000]:
            scene.advance_to(tick);snapshot=scene.snapshot();frame=scene.render();info=scene.info()
            if scene.snapshot()!=snapshot:raise RuntimeError('render mutated native state')
            stem=f'{tick:08d}'
            (output/(stem+'.cells')).write_bytes(frame.bytes)
            (output/(stem+'.snapshot')).write_bytes(snapshot)
            (output/(stem+'.json')).write_text(json.dumps(info,indent=2)+'\n')
            cells=list(struct.iter_unpack('<IIII',frame.bytes))
            text='\n'.join(''.join(chr(cells[y*frame.width+x][0] or 32) for x in range(frame.width)) for y in range(frame.height))+'\n'
            (output/(stem+'.txt')).write_text(text)
            foam=scene.surface_foam(1)
            residual=sum(r[2]-r[1]-r[3]-r[4] for r in foam)
            if abs(residual)>1e-8:raise RuntimeError('foam intensity accounting diverged')
            receipt['captures'].append(dict(timeUs=tick,width=frame.width,height=frame.height,frameSha256=hashlib.sha256(frame.bytes).hexdigest(),snapshotSha256=hashlib.sha256(snapshot).hexdigest(),impacts=info['surfaces'][0]['impacts'],foamBalanceResidual=residual,foamStored=sum(r[1] for r in foam),foamGenerated=sum(r[2] for r in foam),foamDecayed=sum(r[3] for r in foam),foamSaturated=sum(r[4] for r in foam),floatingBodies=info['floatBodies']))
            if tick==1000000:checkpoint=snapshot
        final=scene.snapshot();scene.restore(checkpoint);scene.advance_to(4000000)
        if scene.snapshot()!=final:raise RuntimeError('native replay diverged')
        receipt['replayExact']=True;receipt['snapshotSchema']=hex(int.from_bytes(final[12:16],'little'))
    sources=sorted((ROOT/'src').glob('*.c'))+[ROOT/'src/internal.h',ROOT/'include/nocturne_native.h',ROOT/'bindings/python/nocturne_native.py',Path(__file__).resolve()]
    receipt['sourceSha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (output/'OCEAN.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--library',type=Path);args=parser.parse_args()
    report=export_ocean(args.output,args.library)
    print(json.dumps({k:report[k] for k in ['scene','renderPure','replayExact','snapshotSchema']},indent=2))
