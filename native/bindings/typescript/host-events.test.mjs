import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 const payloads=[null,true,false,42,.5,'Unicode é / 日本',[1,false,'a'],{task:{id:'noc-1',ready:true},items:[1,2]}];
 for(const payload of payloads)s.command({op:'emit-intent',event:'/host/task',payload});
 assert.deepEqual(s.info().intents.map(i=>i.payload),payloads);assert.ok(s.info().intents.every(i=>i.origin==='host'&&i.messageId===0&&i.actionId===0));
 const snapshot=s.snapshot();s.render();assert.deepEqual(s.snapshot(),snapshot);s.restore(snapshot);assert.deepEqual(s.info().intents.map(i=>i.payload),payloads);
 s.command({op:'ack-intent',id:1});assert.equal(s.info().intents.length,7);
 const before=s.snapshot();assert.throws(()=>s.command({op:'emit-intent',event:'/bad//path',payload:{ready:true}}));assert.deepEqual(s.snapshot(),before);
 s.command({op:'define',path:'/go',value:1});s.command({op:'define',path:'/out',value:0});
 s.command({op:'trigger',id:1,source:'/go',target:'/out',event:'/host/approved',expression:{multiply:[{intentField:'value'},2]}});
 s.command({op:'emit-intent',event:'/host/approved',value:7,payload:{task:'noc-1'}});assert.equal(s.info().values['/out'],14);assert.equal(s.info().intents.at(-1).payload.task,'noc-1');
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'emit-intent',event:'/host/scheduled',payload:{ready:true}}});
 const start=s.snapshot();s.advanceTo(1000000);const finish=s.snapshot();assert.equal(s.info().intents.at(-1).atUs,500000);
 s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 console.log(JSON.stringify({runtime:'actual WASM',payloadTypes:payloads.length,explicitAcknowledgement:true,numericEventTrigger:true,atomicRejection:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
