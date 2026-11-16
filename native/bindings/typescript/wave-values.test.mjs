import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const initial=[[1,.2,.3,2,.4],[.5,.1,.2,1,.3]],members=['amplitude','kx','kz','omega','phase'];
for(let index=0;index<2;index++)for(const [member,name] of members.entries()){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle]){
   scene.command({op:'surface',id:1});
   scene.command({op:'mesh',triangles:[{a:[-10,0,-10],b:[10,0,-10],c:[0,0,10],surfaceId:1}]});
   scene.command({op:'surface-waves',surfaceId:1,waves:initial});scene.advanceTo(250000);
  }
  const expected=initial.map(row=>[...row]);expected[index][member]=.75;
  s.command({op:'define',path:'/wave',value:.75,binding:{family:'surface-wave',id:1,field:`waves.${index}.${name}`}});
  oracle.command({op:'surface-waves',surfaceId:1,waves:expected});
  s.command({op:'remove-value',path:'/wave'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);oracle.advanceTo(1000000);
  const finish=s.snapshot();assert.deepEqual(finish,oracle.snapshot());s.render();assert.deepEqual(s.snapshot(),finish);
  s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'surface',id:1});s.command({op:'surface-waves',surfaceId:1,waves:initial});
 s.command({op:'define',path:'/wave',value:1,binding:{family:'surface-wave',id:1,field:'waves.1.amplitude'}});
 s.command({op:'surface-waves',surfaceId:1,waves:[initial[0]]});
 let before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/wave',value:.5}));assert.deepEqual(s.snapshot(),before);
 assert.equal(s.info().valueDescriptors['/wave'].binding.field,'waves.1.amplitude');
 s.command({op:'bind',path:'/wave',binding:{family:'surface-wave',id:1,field:'waves.0.amplitude'}});
 s.command({op:'surface-waves',surfaceId:1,waves:[[128,0,0,0,0],[128,0,0,0,0]]});
 for(const [field,value] of [['waves.0.amplitude',129],['waves.2.phase',1],['waves.00.phase',1],['waves.-1.phase',1],['waves.0.unknown',1]]){
  before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value,binding:{family:'surface-wave',id:1,field}}));assert.deepEqual(s.snapshot(),before);
 }
 console.log(JSON.stringify({runtime:'actual WASM',coefficientOracles:10,removedIndex:true,explicitRebinding:true,aggregateBounds:true,atomicRejection:true,purity:true,replay:true}));
}finally{s.close();}
