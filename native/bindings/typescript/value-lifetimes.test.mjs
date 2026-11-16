import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));const s=await NativeScene.create(wasm);
try{
 for(const path of ['/source','/target'])s.command({op:'define',path,value:0});
 s.command({op:'trigger',id:1,source:'/source',target:'/target'});
 const saved=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/source'}));assert.deepEqual(s.snapshot(),saved);
 s.command({op:'remove-trigger',id:1});s.command({op:'remove-value',path:'/source'});s.command({op:'define',path:'/replacement',value:99});assert.deepEqual(s.info().triggers,[]);assert.equal(s.info().values['/target'],0);
 s.command({op:'schedule',id:1,atUs:1000000,command:{op:'set',path:'/target',expression:{path:'/replacement'}}});const pending=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/replacement'}));assert.deepEqual(s.snapshot(),pending);s.command({op:'cancel-schedule',id:1});s.command({op:'remove-value',path:'/replacement'});
 s.command({op:'schedule',id:2,atUs:1000000,command:{op:'remove-value',path:'/target'}});const start=s.snapshot();s.advanceTo(1000000);assert.deepEqual(s.info().values,{});const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 for(let i=0;i<128;i++){s.command({op:'define',path:'/temporary',value:i});s.command({op:'remove-value',path:'/temporary'});}
 assert.deepEqual(s.info().values,{});
 console.log(JSON.stringify({runtime:'actual WASM',dependencyRejection:true,atomicRejection:true,slotReuse:true,churnCycles:128,pendingProtection:true,renderPure:true,snapshotReplay:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
