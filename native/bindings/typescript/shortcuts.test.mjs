import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 const before=s.snapshot();const candidates=[[10,113,2],[10,115,2],[20,113,2],[30,120,8]],host=[[113,2,0],[115,2,0],[120,8,1]];
 const rows=s.negotiateShortcuts([10,20,30],candidates,host);assert.deepEqual(rows,[[10,115,2,1],[20,113,2,1],[30,0,0,0]]);rows[0][0]=99;assert.deepEqual(s.snapshot(),before);
 assert.deepEqual(s.negotiateShortcuts([1],[[1,66,0],[1,65,0]],[[65,0,0],[66,0,0]]),[[1,66,0,1]]);
 for(let mask=0;mask<512;mask++){
  const cs=[];for(let a=0;a<3;a++)for(let k=0;k<3;k++)if(mask&(1<<(a*3+k)))cs.push([a+1,k+65,0]);
  let best=0;for(let a=-1;a<3;a++)for(let b=-1;b<3;b++)for(let c=-1;c<3;c++){
   const choice=[a,b,c],used=choice.filter(k=>k>=0);if(new Set(used).size!==used.length)continue;
   if(choice.every((k,i)=>k<0||(mask&(1<<(i*3+k)))))best=Math.max(best,used.length);
  }
  const rs=s.negotiateShortcuts([1,2,3],cs,[[65,0,0],[66,0,0],[67,0,0]]);assert.equal(rs.reduce((n,r)=>n+r[3],0),best);
 }
 assert.deepEqual(s.negotiateShortcuts([],[],[]),[]);
 for(const args of [[[1,1],[],[]],[[0],[],[]],[[1],[[2,65,0]],[]],[[1],[],[[65,16,0]]],[[1],[],[[65,0,2]]],[[1],[],[[65,0,0],[65,0,1]]]])assert.throws(()=>s.negotiateShortcuts(...args));
 // Raw C ABI short output and misalignment leave the sentinel unchanged.
 new Uint32Array(s.exports.memory.buffer,s.input,7).set([1,1,65,0,65,0,0]);new Uint32Array(s.exports.memory.buffer,s.checkpoint,4).fill(99);
 assert.equal(s.exports.nrNegotiateShortcuts(s.input,1,s.input+4,1,s.input+16,1,s.checkpoint,0),-1);
 assert.deepEqual(Array.from(new Uint32Array(s.exports.memory.buffer,s.checkpoint,4)),[99,99,99,99]);
 assert.equal(s.exports.nrNegotiateShortcuts(s.input,1,s.input+4,1,s.input+16,1,s.checkpoint+1,1),-1);
 new Uint32Array(s.exports.memory.buffer,s.input,7).set([1,1,65,2,65,2,0]);
 assert.equal(s.exports.nrNegotiateShortcuts(s.input,1,s.input+4,1,s.input+16,1,s.input,1),1);
 assert.deepEqual(Array.from(new Uint32Array(s.exports.memory.buffer,s.input,4)),[1,65,2,1]);
 assert.deepEqual(s.snapshot(),before);
} finally {s.close();}
console.log('Shortcut capability matching: exhaustive cardinality, reservations, preference, purity and invalid buffers');
