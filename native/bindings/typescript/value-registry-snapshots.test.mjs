import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
function crc32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let k=0;k<8;k++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
for(const value of [2,true,'NOC',{id:'noc-1'}]){
 const s=await NativeScene.create(wasm);
 try{
  s.command({op:'define',path:'/first-identity',value:1});s.command({op:'define',path:'/second-identity',value});
  const good=s.snapshot(),damaged=Uint8Array.from(good);
  const offset=Buffer.from(good).indexOf(Buffer.from('/second-identity\0'));
  assert.ok(offset>=24);damaged.fill(0,offset,offset+128);damaged.set(new TextEncoder().encode('/first-identity'),offset);
  new DataView(damaged.buffer).setUint32(20,crc32(damaged.subarray(24)),true);
  assert.throws(()=>s.restore(damaged));assert.deepEqual(s.snapshot(),good);
 }finally{s.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'define',path:'/source',value:3});s.command({op:'define',path:'/out',value:0});
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'set',path:'/out',expression:{path:'/source'}},{op:'set',path:'/source',value:4}]}});
 const saved=s.snapshot();s.restore(saved);assert.deepEqual(s.snapshot(),saved);
 assert.throws(()=>s.command({op:'remove-value',path:'/source'}));assert.deepEqual(s.snapshot(),saved);
 s.advanceTo(500000);assert.deepEqual(s.info().values,{'/source':4,'/out':3});
 console.log(JSON.stringify({runtime:'actual WASM',duplicatePathsRejected:true,typedRegistry:true,pendingBatchRestore:true,ownership:true,orderedExecution:true}));
}finally{s.close();}
