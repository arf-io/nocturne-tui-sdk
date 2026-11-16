import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const commands=JSON.parse(readFileSync(new URL('../../examples/waterfall-scene.json',import.meta.url))).commands;
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 s.command({op:'draft',text:'NOC operator draft',emitWeather:false});s.command({op:'batch',commands});
 s.advanceTo(1000000);let q=s.infoComplete();
 assert.ok(Math.abs(q.flows[0].deliveredVolume-1)<1e-5);
 assert.ok(Math.abs(q.flowSinks[0].receivedVolume-.75)<1e-5);
 assert.ok(Math.abs(q.flowSprays[0].receivedVolume-.25)<1e-5);
 s.command({op:'set',path:'/waterfall/flux',value:0});const start=s.snapshot();
 s.advanceTo(2500000);q=s.infoComplete();const expected=s.snapshot(),frame=s.render();
 assert.equal(q.prompt.text,'NOC operator draft');assert.ok(q.flowSprays[0].impactedVolume>0);
 const basin=q.surfaceWater.find(w=>w.surfaceId===3);assert.ok(basin.retainedVolume>0);
 assert.ok(Math.abs(basin.receivedVolume-basin.retainedVolume-basin.evaporatedVolume-basin.exportedVolume-basin.transferredVolume)<1e-5);
 assert.throws(()=>s.command({op:'set',path:'/waterfall/flux',value:-1}));assert.deepEqual(s.snapshot(),expected);
 s.restore(start);for(const time of [1200000,1500000,2000000,2500000]){s.advanceTo(time);s.render();s.infoComplete();}
 assert.deepEqual(s.snapshot(),expected);assert.deepEqual(s.render(),frame);
 console.log('PASS actual WASM complete waterfall delayed allocation, basin impact, source ownership, rejection and replay');
}finally{s.close();}
