import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
try {
 for(const scene of [s,oracle]){scene.command({op:'flow',id:1,flux:2,stages:[{name:'fall',delayUs:100000,tailUs:500000}]});scene.advanceTo(250000);}
 s.command({op:'define',path:'/flux',value:4,binding:{family:'flow',id:1,field:'flux'}});
 oracle.command({op:'flow-rate',id:1,flux:4});
 for(const [time,value] of [[500000,0],[750000,3],[750000,5],[1000000,5]]){
  s.advanceTo(time);oracle.advanceTo(time);
  s.command({op:'set',path:'/flux',value});oracle.command({op:'flow-rate',id:1,flux:value});
  assert.deepEqual(s.info().flows,oracle.info().flows);
 }
 assert.deepEqual(s.info().valueDescriptors['/flux'].binding,{family:'flow',id:1,field:'flux'});
 const start=s.snapshot();s.advanceTo(2000000);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);
 s.restore(start);s.advanceTo(2000000);assert.deepEqual(s.snapshot(),finish);
 oracle.advanceTo(2000000);s.command({op:'remove-value',path:'/flux'});assert.deepEqual(s.snapshot(),oracle.snapshot());
 const before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value:2,binding:{family:'flow',id:99,field:'flux'}}));assert.deepEqual(s.snapshot(),before);
 const eventFlow=await NativeScene.create(wasm);
 try{
  eventFlow.command({op:'flow',id:1,flux:2,stages:[{name:'fall'}]});
  eventFlow.command({op:'define',path:'/flux',value:2,binding:{family:'flow',id:1,field:'flux'}});
  eventFlow.command({op:'trigger',id:1,target:'/flux',event:'/host/flow',whenExpression:true,expression:{intentPath:'/flux'}});
  eventFlow.command({op:'emit-intent',event:'/host/flow',payload:{flux:5}});
  assert.equal(eventFlow.info().values['/flux'],5);assert.equal(eventFlow.info().intents.length,1);
 }finally{eventFlow.close();}
 console.log(JSON.stringify({runtime:'actual WASM',publicRateOracle:true,historyPreserved:true,renderPure:true,replay:true,atomicRejection:true}));
}finally{s.close();oracle.close();}
