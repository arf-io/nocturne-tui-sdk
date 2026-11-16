import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
function author(s,mesh,count,fade){
 s.command({op:'environment',stars:0,style:'solid'});
 const policy={maxIndividual:0,maxTiles:4,overflow:'merge-to-field',reentrainWindSpeed:0,retentionMs:1000,fadeMs:fade};
 s.command({op:'floor',enabled:!mesh,visible:false,...(!mesh?policy:{})});
 if(mesh){s.command({op:'surface',id:1,renderVisible:false,...policy});s.command({op:'mesh',triangles:[{a:[0,-10,-10],b:[0,10,-10],c:[0,0,10],surfaceId:1}]});}
 s.command(mesh?{op:'camera',position:[30,0,0],yaw:-90,pitch:0}:{op:'camera',position:[0,15,15],yaw:0,pitch:-45});
 s.command({op:'emitter',id:1,effect:'weather/snowglobe',count,runningTimeMs:0,shape:'point',position:mesh?[1,0,0]:[0,1,0],velocity:mesh?[-240,0,0]:[0,-240,0],extent:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,flutterHz:0,flutterAmount:0,tumble:[0,0,0],deposit:true,collision:true,lifetimeMinMs:10000,lifetimeMaxMs:10000,sizeMin:.1,sizeMax:.1,...(mesh?{colliders:{surfaces:[1]}}:{})});
 s.advanceTo(8333);assert.equal(s.infoComplete().particles.aggregated,count);
}
for(const mesh of [false,true]){
 const s=await NativeScene.create(wasm),reference=await NativeScene.create(wasm);
 try{
  author(s,mesh,8,500);author(reference,mesh,4,0);const start=s.snapshot();
  s.advanceTo(758333);reference.advanceTo(758333);const expected=s.snapshot(),frame=s.render();
  assert.deepEqual(frame,reference.render());assert.deepEqual(s.snapshot(),expected);
  assert.equal(s.infoComplete().particles.aggregated,8);
  s.command({op:'clear',scope:'deposits'});assert.notDeepEqual(s.render().bytes,frame.bytes,'Coverage must be visible');
  s.restore(start);for(const t of [108333,508333,758333]){s.advanceTo(t);s.render();s.infoComplete();}
  assert.deepEqual(s.snapshot(),expected);assert.deepEqual(s.render(),frame);
  assert.throws(()=>s.command({op:mesh?'surface':'floor',...(mesh?{id:1}:{}),retentionMs:100,fadeMs:101}));assert.deepEqual(s.snapshot(),expected);
  s.advanceTo(1008333);assert.equal(s.infoComplete().particles.aggregated,0);
 }finally{s.close();reference.close();}
}
console.log('PASS actual WASM floor/mesh fade, independent half-count oracle, purity, replay, rejection and expiry');
