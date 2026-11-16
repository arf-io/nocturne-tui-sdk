import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
try {
 const e=s.exports;
 for(const [scalar,type] of [[65,0],[0x5d0,1],[0x627,2],[0x590,1],[0x7b2,2],[0x2066,19],[0x2067,20],[0x2068,21],[0x2069,22]])assert.equal(e.nrBidiClass(scalar),type);
 assert.equal(e.nrBidiMirror(60),62);assert.equal(e.nrBidiMirror(65),65);assert.equal(e.nrBidiClass(0xd800),-1);
 for(const [text,expected] of [['123 עברית',1],['123 English',0],['\u2067עברית\u2069English',0],['\u2066English\u2069עברית',1]]){
  const scalars=Array.from(text,c=>c.codePointAt(0));new Uint32Array(e.memory.buffer,s.input,scalars.length).set(scalars);
  assert.equal(e.nrBidiParagraphLevel(s.input,scalars.length,0),expected);
 }
 assert.equal(e.nrBidiBracket(40,s.checkpoint,2),1);assert.deepEqual(Array.from(new Uint32Array(e.memory.buffer,s.checkpoint,2)),[41,1]);
 for(const [text,direction,expected] of [
  ['A\u202bB\u202cC',0,[[0,0,0,0],[16,16,0,1],[0,0,1,0],[18,18,1,1],[0,0,0,0]]],
  ['\u202eA1\u202cB',0,[[17,17,0,1],[0,1,1,0],[3,1,1,0],[18,18,1,1],[0,0,0,0]]],
  ['\u2068א\u2069A',0,[[21,21,0,0],[1,1,1,0],[22,22,0,0],[0,0,0,0]]]
 ]) {
  const values=Array.from(text,c=>c.codePointAt(0));new Uint32Array(e.memory.buffer,s.input,values.length).set(values);
  assert.equal(e.nrBidiExplicit(s.input,values.length,direction,s.checkpoint,2048),values.length);
  const result=new Uint32Array(e.memory.buffer,s.checkpoint,values.length*4);
  assert.deepEqual(Array.from({length:values.length},(_,i)=>Array.from(result.subarray(i*4,i*4+4))),expected);
 }
 const overflow='\u2067'.repeat(130)+'A'+'\u2069'.repeat(130)+'B';
 const values=Array.from(overflow,c=>c.codePointAt(0));new Uint32Array(e.memory.buffer,s.input,values.length).set(values);
 assert.equal(e.nrBidiExplicit(s.input,values.length,0,s.checkpoint,2048),values.length);
 const explicit=new Uint32Array(e.memory.buffer,s.checkpoint,values.length*4);
 assert.equal(explicit[130*4+2],125);assert.equal(explicit[(values.length-1)*4+2],0);
 for(const [text,expected] of [['ا́1',[1,1,4]],['א1+2',[1,3,3,3]],['ا\u2066A\u20691',[1,19,0,22,4]],['A\u2067ا\u20691',[0,20,1,22,0]]]) {
  const data=Array.from(text,c=>c.codePointAt(0));new Uint32Array(e.memory.buffer,s.input,data.length).set(data);
  assert.equal(e.nrBidiWeak(s.input,data.length,0,s.checkpoint,2048),data.length);
  const rows=new Uint32Array(e.memory.buffer,s.checkpoint,data.length*7);
  assert.deepEqual(Array.from({length:data.length},(_,i)=>rows[i*7+1]),expected);
 }
 for(const [text,direction,expected] of [['A(א)B',0,[0,0,1,0,0]],['א(א)A',0,[1,1,1,1,0]],['א(A)',1,[1,1,2,1]],['א 12 א',0,[1,1,2,2,1,1]],['A\u2067א(א)\u2069B',0,[0,0,1,1,1,1,0,0]]]) {
  const data=Array.from(text,c=>c.codePointAt(0));new Uint32Array(e.memory.buffer,s.input,data.length).set(data);
  assert.equal(e.nrBidiLevels(s.input,data.length,direction,s.checkpoint,2048),data.length);
  const rows=new Uint32Array(e.memory.buffer,s.checkpoint,data.length*7);
  assert.deepEqual(Array.from({length:data.length},(_,i)=>rows[i*7+2]),expected);
 }
 for(const [text,direction,expected] of [['א12ב',0,[3,1,2,0]],['A\u202bא \u202c',0,[0,2,3]],['(א)',1,[2,1,0]]]) {
  const data=Array.from(text,c=>c.codePointAt(0));new Uint32Array(e.memory.buffer,s.input,data.length).set(data);
  const n=e.nrBidiVisual(s.input,data.length,direction,s.checkpoint,2048);
  const rows=new Uint32Array(e.memory.buffer,s.checkpoint,n*4);
  assert.deepEqual(Array.from({length:n},(_,i)=>rows[i*4]),expected);
 }
 console.log('PASS: actual WASM Unicode 17 bidi properties, paragraph direction and explicit levels and weak, bracket, neutral and implicit resolution');
}finally{s.close();}
