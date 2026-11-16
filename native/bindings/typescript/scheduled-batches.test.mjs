import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm);
try{
 s.command({op:'define',path:'/task',type:'json',value:null});
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[
  {op:'emit-intent',event:'/host/task',payload:{id:'noc-1'}},
  {op:'set',path:'/task',intentId:1,expression:{intentPath:''}},
  {op:'ack-intent',id:1},
 ]}});
 const start=s.snapshot();s.advanceTo(500000);assert.deepEqual(s.info().values['/task'],{id:'noc-1'});assert.deepEqual(s.info().intents,[]);
 const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'define',path:'/source',value:3});s.command({op:'define',path:'/out',value:0});
 s.command({op:'schedule',id:2,atUs:1000000,command:{op:'batch',commands:[{op:'set',path:'/out',expression:{path:'/source'}}]}});
 const protectedState=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/source'}));assert.deepEqual(s.snapshot(),protectedState);
 s.command({op:'cancel-schedule',id:2});s.command({op:'remove-value',path:'/source'});
 for(const child of [{op:'time',timeUs:500000},{op:'batch',commands:[]},{op:'set',path:'/missing',value:1}]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'schedule',id:3,atUs:1000000,command:{op:'batch',commands:[{op:'set',path:'/out',value:2},child]}}));assert.deepEqual(s.snapshot(),before);
 }
 console.log(JSON.stringify({runtime:'actual WASM',orderedCopyAck:true,replay:true,purity:true,referenceOwnership:true,invalidChildRollback:true}));
}finally{s.close();}
