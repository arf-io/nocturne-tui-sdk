import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));const s=await NativeScene.create(wasm);
try{
 for(const [path,value] of [['/go',0],['/out',0],['/a',6],['/b',2]])s.command({op:'define',path,value});
 for(const [expression,expected] of [[{add:[{path:'/a'},{path:'/b'}]},8],[{subtract:[{path:'/a'},{path:'/b'}]},4],[{multiply:[{path:'/a'},{path:'/b'}]},12],[{divide:[{path:'/a'},{path:'/b'}]},3],[{min:[{path:'/a'},{path:'/b'}]},2],[{max:[{path:'/a'},{path:'/b'}]},6],[{negate:{path:'/a'}},-6],[{abs:-6},6],[{clamp:{value:{path:'/a'},min:0,max:4}},4]]){
  s.command({op:'set',path:'/go',value:0});s.command({op:'trigger',id:1,source:'/go',target:'/out',threshold:0,expression});s.command({op:'set',path:'/go',value:1});assert.equal(s.info().values['/out'],expected);
 }
 s.command({op:'trigger',id:1,source:'/go',target:'/out',expression:{path:'/a'},debounceMs:500});let saved=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/a'}));assert.deepEqual(s.snapshot(),saved);
 s.command({op:'set',path:'/go',value:0});s.command({op:'set',path:'/go',value:1});s.command({op:'set',path:'/a',value:8});saved=s.snapshot();s.advanceTo(500000);assert.equal(s.info().values['/out'],8);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(saved);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 const legacy=gunzipSync(readFileSync(new URL('../../tests/fixtures/schema-20261031-before-trigger-formulas.snapshot.gz',import.meta.url)));
 // Exact historical trigger bits, independently read from the immutable fixture.
 assert.equal(legacy.readBigUInt64LE(4203864),0x3fe6666666666667n);
 s.restore(legacy);s.command({op:'set',path:'/go',value:1});assert.equal(s.info().values['/out'],legacy.readDoubleLE(4203864));
 console.log(JSON.stringify({runtime:'actual WASM',operators:9,compiledLifetimeProtection:true,debounceReadsCurrentValues:true,renderPure:true,snapshotReplay:true,previousSchemaMigration:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
