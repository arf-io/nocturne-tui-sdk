import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
try {
 for(const [text,cols,x,y,want] of [['é中',8,1,0,2],['👩‍🔧A',8,1,0,3],['A\r\n',8,0,1,3],['',1,0,0,0]])assert.equal(s.graphemeHit(text,cols,x,y),want);
 for(const args of [['A',0,0,0],['A',1,-1,0],['\ud800',1,0,0],['A',1,0,2**32]])assert.throws(()=>s.graphemeHit(...args));
 console.log('PASS: actual WASM grapheme hit binding');
}finally{s.close();}
