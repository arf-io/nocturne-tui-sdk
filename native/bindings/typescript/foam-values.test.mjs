import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const fields={enabled:0,sourceRate:3,curvatureThreshold:.2,decay:2,impactGain:.2,color:0xabcdef};
for(const [field,value] of Object.entries(fields)){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle]){
   for(const command of [{op:'surface',id:1},{op:'mesh',triangles:[{a:[-10,0,-10],b:[10,0,-10],c:[0,0,10],surfaceId:1}]},
    {op:'surface-waves',surfaceId:1,waves:[[1,1,0,0,0]]},{op:'surface-foam',surfaceId:1,sourceRate:2,curvatureThreshold:0}])scene.command(command);
   scene.advanceTo(250000);
  }
  const ledger=s.surfaceFoam(1);
  s.command({op:'define',path:'/foam',value,binding:{family:'surface-foam',id:1,field}});
  assert.deepEqual(s.surfaceFoam(1),ledger);
  oracle.command({op:'surface-foam',surfaceId:1,[field]:field==='enabled'?Boolean(value):value});
  s.command({op:'remove-value',path:'/foam'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);oracle.advanceTo(1000000);const finish=s.snapshot();assert.deepEqual(finish,oracle.snapshot());
  s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
console.log(JSON.stringify({runtime:'actual WASM',publicOracles:6,ledgerPreserved:true,purity:true,replay:true}));
