import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
for(const index of [0,63,127]){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  const initial=Array.from({length:128},(_,i)=>i),expected=[...initial];expected[index]=-17;
  for(const scene of [s,oracle]){scene.command({op:'widget',id:1,kind:'line',data:initial,revealMs:2000});scene.advanceTo(250000);}
  s.command({op:'define',path:'/entry',value:-17,binding:{family:'widget',id:1,field:`data.${index}`}});
  oracle.command({op:'widget',id:1,data:expected});s.command({op:'remove-value',path:'/entry'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);oracle.advanceTo(1000000);const finish=s.snapshot();assert.deepEqual(finish,oracle.snapshot());assert.deepEqual(s.render().bytes,oracle.render().bytes);
  s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'widget',id:1,kind:'bars',data:[1,2]});
 for(const field of ['data.2','data.128','data.00','data.-1','data.1.extra','data.']){
  const before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value:3,binding:{family:'widget',id:1,field}}));assert.deepEqual(s.snapshot(),before);
 }
 s.command({op:'define',path:'/entry',value:3,binding:{family:'widget',id:1,field:'data.1'}});
 s.command({op:'widget',id:1,data:[1]});const saved=s.snapshot();s.restore(saved);
 assert.throws(()=>s.command({op:'set',path:'/entry',value:4}));assert.deepEqual(s.snapshot(),saved);
 s.command({op:'bind',path:'/entry',binding:{family:'widget',id:1,field:'data.0'}});
 console.log(JSON.stringify({runtime:'actual WASM',fullDataCapacity:true,publicEditOracles:3,removedSlot:true,explicitRebinding:true,atomicRejection:true,purity:true,replay:true}));
}finally{s.close();}
