import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),42);
try{
 for(const command of [{op:'define',path:'/out',type:'json',value:{}},{op:'define',path:'/title',value:'NOC 日本'},{op:'define',path:'/ready',value:true}])s.command(command);
 s.command({op:'set',path:'/out',expression:{object:{title:{path:'/title'},'日本/a~b':{array:[{path:'/ready'},null,{literal:{nested:[1,2]}}]},empty:{object:{}}}}});
 assert.deepEqual(s.info().values['/out'],{title:'NOC 日本','日本/a~b':[true,null,{nested:[1,2]}],empty:{}});
 s.command({op:'set',path:'/out',expression:{array:[]}});assert.deepEqual(s.info().values['/out'],[]);
 s.command({op:'define',path:'/go',value:1});
 s.command({op:'trigger',id:1,source:'/go',target:'/out',event:'/host/task',debounceMs:500,expression:{object:{task:{intentPath:'/task'},ready:{equal:[{intentPath:'/status'},'ready']}}}});
 s.command({op:'emit-intent',event:'/host/task',payload:{task:{id:'noc-1',items:[true,null]},status:'ready'}});
 const start=s.snapshot();s.advanceTo(500000);const finish=s.snapshot();assert.deepEqual(s.info().values['/out'],{task:{id:'noc-1',items:[true,null]},ready:true});
 s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'ack-intent',id:1});assert.equal(s.info().values['/out'].task.id,'noc-1');
 s.command({op:'define',path:'/long',value:'x'.repeat(3000)});
 for(const expression of [{array:[{path:'/long'},{path:'/long'}]},{object:{task:{path:'/missing'}}},{array:Array.from({length:17},(_,i)=>i)}]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/out',expression}));assert.deepEqual(s.snapshot(),before);
 }
 let deep=1;for(let i=0;i<7;i++)deep=[deep];s.command({op:'define',path:'/deep',type:'json',value:deep});
 const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/out',expression:{array:[{path:'/deep'}]}}));assert.deepEqual(s.snapshot(),before);
 console.log(JSON.stringify({runtime:'actual WASM',constructedContainers:true,unicodeKeys:true,retainedAction:true,ownedCopy:true,atomicCapacityFaults:true,depthLimit:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
