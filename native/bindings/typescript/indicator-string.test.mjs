import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
try{
 for(const scene of [s,oracle]){scene.command({op:'indicator',id:1,x:12,y:8,sequence:'|/-',stepMs:120});scene.advanceTo(250000);}
 s.command({op:'define',path:'/wait',value:'◐◓◑◒',binding:{family:'indicator',id:1,field:'sequence'}});
 oracle.command({op:'indicator',id:1,sequence:'◐◓◑◒'});s.command({op:'remove-value',path:'/wait'});assert.deepEqual(s.snapshot(),oracle.snapshot());
 const start=s.snapshot();
 for(const time of [500000,1000000,2000000]){s.advanceTo(time);oracle.advanceTo(time);assert.deepEqual(s.snapshot(),oracle.snapshot());assert.deepEqual(s.render().bytes,oracle.render().bytes);}
 const finish=s.snapshot();s.restore(start);s.advanceTo(2000000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'define',path:'/wait',value:'x'.repeat(128),binding:{family:'indicator',id:1,field:'sequence'}});
 for(const value of ['', 'x'.repeat(129),true,'\u0001']){
  const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/wait',value}));assert.deepEqual(s.snapshot(),before);
 }
 console.log(JSON.stringify({runtime:'actual WASM',publicSequenceOracle:true,unicode:true,bounds:true,purity:true,replay:true}));
}finally{s.close();oracle.close();}
