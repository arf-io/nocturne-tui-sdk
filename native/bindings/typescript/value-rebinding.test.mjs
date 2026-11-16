import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 for(const id of [1,2])s.command({op:'widget',id,kind:'progress',value:0});
 s.command({op:'define',path:'/control',value:.5,binding:{family:'widget',id:1,field:'value'}});
 s.command({op:'bind',path:'/control',binding:{family:'widget',id:2,field:'value'}});
 s.command({op:'set',path:'/control',value:.8});assert.deepEqual(s.info().widgets.map(w=>w.value),[.5,.8]);
 const before=s.snapshot();assert.throws(()=>s.command({op:'bind',path:'/control',binding:{family:'widget',id:99,field:'value'}}));assert.deepEqual(s.snapshot(),before);
 s.command({op:'bind',path:'/control',binding:null});s.command({op:'set',path:'/control',value:.2});assert.deepEqual(s.info().widgets.map(w=>w.value),[.5,.8]);
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'bind',path:'/control',binding:{family:'widget',id:2,field:'value'}}});
 const start=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/control'}));assert.deepEqual(s.snapshot(),start);
 s.advanceTo(1000000);assert.equal(s.info().widgets[1].value,.2);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);
 s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'field',x:10,y:10,lifeMs:100});s.command({op:'define',path:'/field',value:2,binding:{family:'field',id:1,field:'width'}});
 s.advanceTo(1200000);s.command({op:'field',x:10,y:10,lifeMs:1000});const expired=s.snapshot();
 assert.throws(()=>s.command({op:'set',path:'/field',value:3}));assert.deepEqual(s.snapshot(),expired);
 s.command({op:'bind',path:'/field',binding:{family:'field',id:2,field:'width'}});assert.equal(s.info().fields[0].width,2);
 console.log(JSON.stringify({runtime:'actual WASM',replacement:true,detach:true,atomicRejection:true,pendingOwnership:true,fieldExpiry:true,renderPure:true,replay:true}));
}finally{s.close();}
