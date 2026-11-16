import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const points=[{position:[0,0,0],parent:-1},{position:[3,0,0],parent:0},{position:[3,4,0],parent:1},{position:[3,0,12],parent:1}];
try{
 s.command({op:'electrical-arc',id:7,points,speed:10,holdMs:200,fadeMs:300,jitter:0,flicker:0,alpha:.8});
 const start=s.snapshot();s.advanceTo(700000);const expected=s.snapshot(),frame=s.render();
 assert.deepEqual(s.infoComplete().electricalArcs[0].segments,[[0,0,0,3,0,0,1],[3,0,0,3,4,0,2],[3,0,0,3,0,4,3]]);
 const q=s.infoComplete();q.electricalArcs[0].points[0].position[0]=999;assert.deepEqual(s.infoComplete().electricalArcs[0].points,points);s.render();assert.deepEqual(s.snapshot(),expected);
 for(const patch of [{speed:0},{repeatMs:1999},{points:[points[0],{position:[1,0,0],parent:1}]}]){
  assert.throws(()=>s.command({op:'electrical-arc',id:8,points,speed:10,holdMs:200,fadeMs:300,...patch}));assert.deepEqual(s.snapshot(),expected);
 }
 s.command({op:'remove-electrical-arc',id:7});assert.notDeepEqual(s.render().bytes,frame.bytes);
 s.restore(start);for(const t of [100000,300000,500000,700000]){s.advanceTo(t);s.render();}
 assert.deepEqual(s.snapshot(),expected);assert.deepEqual(s.render(),frame);
 s.advanceTo(1850000);assert.equal(s.infoComplete().electricalArcs[0].phase,'fade');assert.ok(Math.abs(s.infoComplete().electricalArcs[0].opacity-.4)<1e-9);
 s.advanceTo(2000000);assert.equal(s.infoComplete().electricalArcs[0].phase,'finished');assert.deepEqual(s.infoComplete().electricalArcs[0].segments,[]);
 console.log('PASS actual WASM connected electrical geometry, lifecycle, ownership, purity, atomic rejection and replay');
}finally{s.close();}
