import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const commands=JSON.parse(readFileSync(new URL('../../examples/road-scene.json',import.meta.url))).commands;
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 s.command({op:'draft',text:'NOC travel draft',emitWeather:false});s.command({op:'batch',commands});
 s.advanceTo(1000000);assert.deepEqual(s.infoComplete().camera.position,[0,1.7,-2]);const start=s.snapshot();
 s.advanceTo(3000000);const expected=s.snapshot(),frame=s.render();assert.equal(s.infoComplete().prompt.text,'NOC travel draft');
 s.restore(start);for(const t of [1500000,2000000,2500000,3000000]){s.advanceTo(t);s.render();s.infoComplete();}
 assert.deepEqual(s.snapshot(),expected);assert.deepEqual(s.render(),frame);
 s.command({op:'remove-path-travel',id:1});const position=s.infoComplete().camera.position;s.advanceTo(4000000);assert.deepEqual(s.infoComplete().camera.position,position);
 const saved=s.snapshot(),bad=commands.map(c=>structuredClone(c));bad.find(c=>c.op==='ribbon').width=0;
 assert.throws(()=>s.command({op:'batch',commands:bad}));assert.deepEqual(s.snapshot(),saved);
 console.log('PASS actual WASM road travel, retained draft, atomic rejection, query/render purity, freeze and replay');
}finally{s.close();}
