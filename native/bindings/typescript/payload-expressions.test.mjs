import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 s.command({op:'define',path:'/out',value:0});
 s.command({op:'emit-intent',event:'/host/task',payload:{task:{done:7,total:10},items:[3,8],'a/b':4,'~key':5,'日本':6,'':9,flag:true,text:'7',nil:null}});
 for(const [intentPath,expected] of [['/task/done',7],['/items/0',3],['/items/1',8],['/a~1b',4],['/~0key',5],['/日本',6],['/',9]]){
  s.command({op:'set',path:'/out',intentId:1,expression:{intentPath}});assert.equal(s.info().values['/out'],expected);
 }
 s.command({op:'set',path:'/out',intentId:1,expression:{divide:[{intentPath:'/task/done'},{intentPath:'/task/total'}]}});assert.equal(s.info().values['/out'],.7);
 for(const intentPath of ['relative','/bad~2key','/missing','/items/01','/items/-','/items/2','/flag','/text','/nil','']){
  const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/out',intentId:1,expression:{intentPath}}));assert.deepEqual(s.snapshot(),before);
 }
 s.command({op:'emit-intent',event:'/host/root',payload:12});
 s.command({op:'set',path:'/out',intentId:2,expression:{intentPath:''}});assert.equal(s.info().values['/out'],12);
 // Retire the pointer-study event before establishing the debounce subscription.
 // Otherwise its unacknowledged id 1 correctly owns the first pending action.
 s.command({op:'ack-intent',id:1});
 s.command({op:'define',path:'/go',value:1});
 s.command({op:'trigger',id:1,source:'/go',target:'/out',event:'/host/task',debounceMs:500,expression:{divide:[{intentPath:'/task/done'},{intentPath:'/task/total'}]}});
 s.command({op:'emit-intent',event:'/host/other',payload:{task:{done:99,total:100}}});
 s.command({op:'emit-intent',event:'/host/task',payload:{task:{done:3,total:4}}});
 const start=s.snapshot();s.advanceTo(500000);const finish=s.snapshot();assert.equal(s.info().values['/out'],.75);assert.equal(s.info().triggers[0].lastIntent,4);
 s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'ack-intent',id:4});const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/out',intentId:4,expression:{intentPath:'/task/done'}}));assert.deepEqual(s.snapshot(),before);
 console.log(JSON.stringify({runtime:'actual WASM',pointerCases:8,strictNumericLeaves:true,matchedEvent:true,atomicFaults:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
