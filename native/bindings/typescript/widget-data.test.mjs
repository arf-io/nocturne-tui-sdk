import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
for(const data of [[1,2,3],[],[-1000000,0,1000000]]){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle]){scene.command({op:'widget',id:1,kind:'bars',data:[5,6,7,8],revealMs:2000});scene.advanceTo(250000);}
  s.command({op:'define',path:'/series',type:'json',value:data,binding:{family:'widget',id:1,field:'data'}});
  oracle.command({op:'widget',id:1,data});s.command({op:'remove-value',path:'/series'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);oracle.advanceTo(1000000);const finish=s.snapshot();assert.deepEqual(finish,oracle.snapshot());assert.deepEqual(s.render().bytes,oracle.render().bytes);
  s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'widget',id:1,kind:'bars',data:[]});s.command({op:'define',path:'/series',type:'json',value:[],binding:{family:'widget',id:1,field:'data'}});
 s.command({op:'emit-intent',event:'/host/series',payload:{series:[2,4,6]}});
 s.command({op:'set',path:'/series',intentId:1,expression:{intentPath:'/series'}});s.command({op:'ack-intent',id:1});assert.deepEqual(s.info().values['/series'],[2,4,6]);
 for(const data of [[true],[null],['3'],{},[1000001]]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/series',value:data}));assert.deepEqual(s.snapshot(),before);
 }
 const saved=s.snapshot();s.restore(saved);assert.deepEqual(s.snapshot(),saved);
 console.log(JSON.stringify({runtime:'actual WASM',publicDataOracles:3,ownedPayload:true,strictNumericElements:true,atomicRejection:true,purity:true,replay:true,restore:true}));
}finally{s.close();}
