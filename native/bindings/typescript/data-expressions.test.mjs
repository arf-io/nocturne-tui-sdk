import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),42);
try{
 for(const [path,value] of [['/name','NOC'],['/ready',true],['/flag',false],['/out',''],['/seconds',2]])s.command({op:'define',path,value});
 s.command({op:'set',path:'/out',expression:{concat:[{path:'/name'},{literal:' 日本 "quoted"'}]}});assert.equal(s.info().values['/out'],'NOC 日本 "quoted"');
 for(const [expression,expected] of [
  [{and:[{path:'/ready'},{not:{path:'/flag'}}]},true],
  [{or:[false,false]},false],
  [{equal:[{literal:{a:[true,null,1],b:'日'}},{literal:{b:'日',a:[true,null,1]}}]},true],
  [{equal:[true,1]},false],
  [{equal:[{convert:{value:{path:'/seconds'},from:'seconds',to:'milliseconds'}},2000]},true],
 ]){s.command({op:'set',path:'/flag',expression});assert.equal(s.info().values['/flag'],expected);}
 s.command({op:'set',path:'/out',expression:{if:{condition:{path:'/ready'},then:'Ready',else:{intentPath:'/missing'}}}});assert.equal(s.info().values['/out'],'Ready');
 s.command({op:'define',path:'/numeric',value:0});s.command({op:'set',path:'/numeric',expression:{if:{condition:true,then:{convert:{value:2,from:'seconds',to:'milliseconds'}},else:{divide:[1,0]}}}});assert.equal(s.info().values['/numeric'],2000);
 s.command({op:'trigger',id:1,target:'/out',event:'/host/task',debounceMs:500,
  whenExpression:{and:[{path:'/ready'},{equal:[{intentPath:'/task/status'},'ready']}]},
  expression:{concat:['Task: ',{intentPath:'/task/title'}]}});
 s.command({op:'emit-intent',event:'/host/task',payload:{task:{status:'ready',title:'NOC 日本'}}});
 const start=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/ready'}));assert.deepEqual(s.snapshot(),start);
 s.advanceTo(500000);const finish=s.snapshot();assert.equal(s.info().values['/out'],'Task: NOC 日本');assert.equal(s.info().triggers[0].lastIntent,1);
 s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'widget',id:1,kind:'button',text:'NOC',alpha:.2});
 s.command({op:'state-register',id:1,path:'/app/button',role:'control',target:{family:'widget',id:1}});
 s.command({op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{path:'/out'},'Task: NOC 日本']},style:{alpha:.8}});
 assert.equal(s.info().registeredStates[0].effective.alpha,.8);s.command({op:'set',path:'/out',value:'manual'});assert.equal(s.info().registeredStates[0].effective.alpha,.2);
 s.command({op:'remove-style-rule',id:1});s.command({op:'remove-trigger',id:1});
 for(const command of [{op:'set',path:'/flag',expression:{and:[true,1]}},{op:'set',path:'/out',expression:{concat:['text',true]}}]){
  const before=s.snapshot();assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),before);
 }
 console.log(JSON.stringify({runtime:'actual WASM',typedOperators:6,semanticJsonEquality:true,numericUnitsComposition:true,retainedTypedActions:true,typedStyleGuard:true,lifetimeProtection:true,atomicFaults:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
