import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 for(const c of [{op:'widget',id:1,kind:'text',text:'Owned source',alpha:.2},{op:'state-register',id:21,path:'/view',role:'control',target:{family:'widget',id:1}},
  {op:'define',path:'/ready',value:false},{op:'define',path:'/level',value:0},{op:'trigger',id:1,target:'/ready',event:'/host/ready',whenExpression:true,expression:{intentPath:'/ready'}},
  {op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{path:'/ready'},style:{alpha:.8}}])s.command(c);
 const start=s.snapshot();
 const run=()=>{for(const [ready,alpha] of [[true,.8],[false,.2]]){s.command({op:'emit-intent',event:'/host/ready',payload:{ready}});
  assert.equal(s.infoComplete().registeredStates[0].effective.alpha,alpha);const before=s.snapshot();s.render();s.infoComplete();assert.deepEqual(s.snapshot(),before);}};
 run();const final=s.snapshot(),frame=s.render();s.restore(start);run();assert.deepEqual(s.snapshot(),final);assert.deepEqual(s.render(),frame);
 for(const whenExpression of [{equal:[{intentField:'value'},1]},{if:{condition:false,then:{intentPath:'/ready'},else:true}},{equal:[{object:{x:{intentField:'id'}}},{literal:{x:1}}]}]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'style-rule',id:2,selector:{family:'widget',id:1},whenExpression,style:{alpha:.6}}),/Invalid typed appearance guard/);assert.deepEqual(s.snapshot(),before);
 }
 const payload={intentField:'id',intentPath:'/ready'};
 s.command({op:'style-rule',id:2,selector:{family:'widget',id:1},whenExpression:{equal:[{literal:payload},{literal:payload}]},style:{alpha:.6}});
 s.advanceTo(1);assert.equal(s.infoComplete().registeredStates[0].effective.alpha,.6);
 for(const when of [{intentValue:{comparison:'above',value:0}},{not:{intentValue:{comparison:'above',value:0}}}]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'style-rule',id:2,selector:{family:'widget',id:1},when,style:{alpha:.6}}),/State invariant rejected/);assert.deepEqual(s.snapshot(),before);
 }
 for(const [when,alpha] of [[{path:'/level',comparison:'above',value:0},.2],[{not:{path:'/level',comparison:'above',value:0}},.6]]){
  s.command({op:'style-rule',id:2,selector:{family:'widget',id:1},when,style:{alpha:.6}});s.advanceTo(s.infoComplete().clock.timeUs+1);assert.equal(s.infoComplete().registeredStates[0].effective.alpha,alpha);
 }
}finally{s.close();}
console.log('PASS actual WASM appearance event routing/rejection, opaque literal data, legacy numeric conditions, purity and replay');
