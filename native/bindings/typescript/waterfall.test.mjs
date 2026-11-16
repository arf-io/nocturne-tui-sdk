import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm),r=await NativeScene.create(wasm);
for(const x of [s,r]){
 for(const id of [1,2])x.command({op:'surface',id});
 x.command({op:'ribbon',points:[[0,3,-2],[0,3,0]],width:2,surfaceId:1,color:0x809caa});
 x.command({op:'flow',id:1,flux:2,stages:[{name:'channel',delayUs:250000},{name:'sheet',delayUs:250000}]});
}
s.command({op:'waterfall',channelSurfaceId:1,sheetSurfaceId:2,flowId:1,channelStage:'channel',sheetStage:'sheet',referenceFlux:2,drop:3});
r.command({op:'mesh',append:true,triangles:[{a:[1,3,0],b:[-1,3,0],c:[1,0,0],surfaceId:2,color:0x809caa,alpha:1},{a:[-1,3,0],b:[-1,0,0],c:[1,0,0],surfaceId:2,color:0x809caa,alpha:1}]});
for(const [surfaceId,stage] of [[1,'channel'],[2,'sheet']])r.command({op:'flow-surface',surfaceId,stage,flowId:1,referenceFlux:2});
assert.deepEqual(s.snapshot(),r.snapshot());s.advanceTo(750000);r.advanceTo(750000);assert.deepEqual(s.render(),r.render());const saved=s.snapshot();s.render();assert.deepEqual(saved,s.snapshot());s.close();r.close();console.log('PASS native WASM shared-lip waterfall assembly');
