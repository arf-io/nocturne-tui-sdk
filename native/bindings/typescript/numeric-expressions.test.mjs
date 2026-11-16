import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));const s=await NativeScene.create(wasm);
try{
 for(const [path,value] of [['/out',0],['/scale',2],['/offset',3]])s.command({op:'define',path,value});
 const formulas=[[{add:[1,2,3]},6],[{subtract:[10,3]},7],[{multiply:[2,3,4]},24],[{divide:[7,2]},3.5],[{min:[7,2,5]},2],[{max:[7,2,5]},7],[{negate:3},-3],[{abs:-3},3],[{clamp:{value:8,min:2,max:5}},5]];
 for(const [expression,expected] of formulas){s.command({op:'set',path:'/out',expression});assert.equal(s.info().values['/out'],expected);}
 s.command({op:'status',id:7,area:0,text:'Action',durationMs:0,actions:[{id:3,label:'Confirm',event:'/task/approved',value:7}]});s.command({op:'notification-action',id:7,actionId:3});const intents=s.info().intents;
 s.command({op:'set',path:'/out',intentId:1,expression:{subtract:[{multiply:[2,{intentField:'value'}]},{path:'/offset'}]}});assert.equal(s.info().values['/out'],11);assert.deepEqual(s.info().intents,intents);
 for(const expression of [{divide:[1,0]},{multiply:[1e12,2]},{path:'/missing'},{intentField:'value'}]){const saved=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/out',expression}));assert.deepEqual(s.snapshot(),saved);}
 s.command({op:'schedule',id:1,atUs:1000000,command:{op:'set',path:'/out',expression:{multiply:[{path:'/scale'},4]}}});s.command({op:'set',path:'/scale',value:3});const start=s.snapshot();s.advanceTo(1000000);assert.equal(s.info().values['/out'],12);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 console.log(JSON.stringify({runtime:'actual WASM',operators:formulas.length,exactIntent:true,nonConsuming:true,atomicRejection:true,executionTimeValues:true,renderPure:true,snapshotReplay:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
