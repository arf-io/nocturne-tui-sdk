import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
try {
 assert.deepEqual(s.bidiLayout('א́ב',8),[[2,3,0,0,1,1,0x5d1],[0,2,1,0,1,1,0x5d0]]);assert.throws(()=>s.bidiLayout('A',0));
 assert.equal(s.bidiHit('א́ב',8,0,0),3);assert.deepEqual(s.bidiCaret('AאבB',8,1,0),[1,0,0]);assert.deepEqual(s.bidiCaret('AאבB',8,1,1),[3,0,1]);assert.throws(()=>s.bidiCaret('א́ב',8,1));
 const saved=s.snapshot();const rows=s.bidiVisual('א12ב');assert.deepEqual(rows,[[3,1,1,0x5d1],[1,3,2,49],[2,3,2,50],[0,1,1,0x5d0]]);
 rows[0][0]=99;assert.equal(s.bidiVisual('א12ב')[0][0],3);assert.deepEqual(s.snapshot(),saved);
 for(const args of [['A',3],['A',true],['\ud800',0],['A'.repeat(2049),0]])assert.throws(()=>s.bidiVisual(...args));assert.deepEqual(s.bidiVisual(''),[]);
 console.log('PASS: owned WASM bidi binding, source mapping, validation and purity');
}finally{s.close();}
