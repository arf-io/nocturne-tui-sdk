import assert from 'node:assert/strict';
import fs from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const wasm=fs.readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url));
const scene=await NativeScene.create(wasm,2030);let text='';
scene.command({op:'prompt',presentation:'framed'});
for(const n of [35001,35003,70007]){const part='🌧'.repeat(n);scene.command({op:'input',text:part});text+=part;assert.equal(scene.textRunSource(0,0),text);}
const n=Array.from(text).length;scene.command({op:'select',anchor:0,caret:n});assert.equal(scene.selectedText(),text);assert.equal(scene.textRunClusters(0,0).length,n);assert.equal(scene.textRunLayout(0,0,80).length,n);
const saved=scene.snapshot();scene.render();assert.deepEqual(scene.snapshot(),saved);
const restored=await NativeScene.create(wasm,99);restored.restore(saved);assert.equal(restored.textRunSource(0,0),text);assert.deepEqual(restored.snapshot(),saved);restored.close();
assert.throws(()=>scene.command({op:'select',anchor:0,caret:-1}));assert.deepEqual(scene.snapshot(),saved);
scene.command({op:'draft',text:'🌧'.repeat(270001),emitWeather:false});assert.equal(Array.from(scene.textRunSource(0,0)).length,270001);scene.close();
const bidi=await NativeScene.create(wasm,7);bidi.command({op:'prompt',layout:'bidi',direction:'rtl',mode:'grow'});bidi.command({op:'draft',text:'אב\n'.repeat(25001),emitWeather:false});const rows=bidi.promptVisualLayout();assert.equal(rows.length,75003);assert.deepEqual(rows.slice(0,3).map(r=>r[0]),[2,1,0]);assert.deepEqual(rows.slice(-3).map(r=>r[0]),[75002,75001,75000]);const before=bidi.snapshot();bidi.render();assert.deepEqual(bidi.snapshot(),before);bidi.close();
console.log('PASS large public WASM bidi:75,003scalars,25,001wholeRTLparagraphs,exactgeometry,renderpurity');
console.log('PASS growing WASM prompt: repeated65k crossings,140011selected/cluster/layoutscalars,270001scalar command>1MiB,render purity,variable snapshot fresh-context restore,invalid atomicity');
