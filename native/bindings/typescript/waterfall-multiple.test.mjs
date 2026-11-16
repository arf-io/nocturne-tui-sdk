import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const commands=JSON.parse(readFileSync(new URL('../../examples/waterfall-scene.json',import.meta.url))).commands;
const second=structuredClone(commands);
for(const c of second){
 if(c.op==='surface')c.id+=3;
 if(c.surfaceId!==undefined)c.surfaceId+=3;
 if(c.flowId!==undefined)c.flowId=2;
 if(c.emitterId!==undefined)c.emitterId=2;
 if(c.op==='flow')c.id=2;
 if(c.op==='waterfall'){c.channelSurfaceId+=3;c.sheetSurfaceId+=3;}
 if(c.op==='ribbon')for(const p of c.points)p[0]+=10;
 if(c.op==='mesh')for(const t of c.triangles){t.surfaceId+=3;for(const p of [t.a,t.b,t.c])p[0]+=10;}
 if(c.op==='emitter'){c.id=2;c.position[0]+=10;c.colliders.surfaces=c.colliders.surfaces.map(id=>id+3);}
 if(c.op==='define'){c.path='/other-waterfall/flux';c.binding.id=2;}
}
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 s.command({op:'batch',commands});const original=s.surfaceTriangles(1);s.command({op:'batch',commands:second});
 assert.deepEqual(s.surfaceTriangles(1),original);s.command({op:'set',path:'/waterfall/flux',value:0});s.advanceTo(1000000);
 const flows=s.infoComplete().flows;assert.equal(flows.find(f=>f.id===1).injectedVolume,0);assert.equal(flows.find(f=>f.id===2).injectedVolume,2);
 const before=s.snapshot();assert.throws(()=>s.command({op:'waterfall',channelSurfaceId:1,sheetSurfaceId:2,flowId:1,channelStage:'channel',sheetStage:'sheet',referenceFlux:2,drop:3}));assert.deepEqual(s.snapshot(),before);
 console.log('PASS actual WASM independent waterfall assemblies preserve owned geometry/control and reject owned reassembly');
}finally{s.close();}
