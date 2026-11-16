import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const commands=JSON.parse(readFileSync(new URL('../../examples/garden-scene.json',import.meta.url))).commands;
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 s.command({op:'draft',text:'NOC garden draft',emitWeather:false});s.command({op:'batch',commands});
 s.advanceTo(1000000);const start=s.snapshot();s.advanceTo(3000000);const expected=s.snapshot(),frame=s.render(),q=s.infoComplete();
 assert.equal(q.prompt.text,'NOC garden draft');const surface=q.surfaces.find(row=>row.id===1);
 assert.ok(surface.impacts>0);assert.ok(surface.wetness>0);assert.ok(q.deposits.some(row=>row.surfaceId===1));
 q.surfaces.length=0;assert.ok(s.infoComplete().surfaces.length>0);assert.deepEqual(s.snapshot(),expected);
 assert.throws(()=>s.command({op:'set',path:'/garden/heat',value:-1}));assert.deepEqual(s.snapshot(),expected);
 s.restore(start);for(const time of [1500000,2000000,2500000,3000000]){s.advanceTo(time);s.render();s.infoComplete();}
 assert.deepEqual(s.snapshot(),expected);assert.deepEqual(s.render(),frame);
 console.log('PASS actual WASM garden accumulation, wet response, retained source, rejection, ownership and replay');
}finally{s.close();}
