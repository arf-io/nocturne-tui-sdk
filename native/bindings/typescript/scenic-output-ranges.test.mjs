import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 for(const cmd of [{op:'surface',id:1},{op:'ribbon',points:[[0,0,-2],[0,0,0]],width:2,surfaceId:1},{op:'flow',id:1,flux:2,stages:[{name:'channel'}]},{op:'flow-surface',surfaceId:1,flowId:1,stage:'channel',referenceFlux:2},{op:'flow-thickness',surfaceId:1,width:2,speed:2,maxDepth:1},{op:'float-body',id:1,surfaceId:1,position:[0,0,0],radius:1,mass:1000}])s.command(cmd);
 const before=s.snapshot(),contextBefore=new Uint8Array(s.exports.memory.buffer,s.context,s.exports.nrContextSize()).slice();
 for(const [name,capacity,wave] of [['nrFlowThickness',6,false],['nrSurfaceTriangles',12,false],['nrSurfaceFoam',12,false],['nrSurfaceFoamTransport',12,false],['nrFloatBody',12,false],['nrSurfaceWaveSample',6,true]]){
  for(const out of [s.context,0xfffffff8]){
   const args=[s.context,1,...(wave?[0,0]:[]),out,capacity];assert.equal(s.exports[name](...args),-1,name);
   assert.deepEqual(new Uint8Array(s.exports.memory.buffer,s.context,contextBefore.length),contextBefore,name);assert.deepEqual(s.snapshot(),before,name);
  }
 }
 assert.equal(s.surfaceTriangles(1).length,12);assert.equal(s.surfaceFoam(1).length,12);assert.equal(s.surfaceFoamTransport(1).length,12);assert.equal(s.flowThickness(1)[1],.5);
}finally{s.close()}
console.log('Scenic output ranges: context alias, pointer overflow, atomic rejection and valid owned queries');
