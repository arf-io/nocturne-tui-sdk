import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {StudioDataSource,observatorySample} from './pearl_data.mjs';
const original=name=>JSON.parse(gunzipSync(readFileSync(new URL('../../tests/fixtures/pearl-data-original/'+name+'.json.gz',import.meta.url))));
test('original Studio WASM tween/data target/count at32 irregular samples',()=>{
 const source=new StudioDataSource();for(const row of original('STUDIO-ORACLE').rows){source.advanceTo(row.elapsedMs);const actual=source.snapshot();for(const key of ['motionMs','dataCount','value','fromValue','changedMs','displayValue'])assert.equal(actual[key],row[key],key+' @'+row.elapsedMs);}
});
test('original Studio slider/prompt commits and motion policy are retained',()=>{
 const source=new StudioDataSource();for(const row of original('STUDIO-ORACLE').mixedInputRows){const request=row.request;source.advanceTo(row.elapsedMs,{playing:request.playing??true});if('value'in request)source.setValue(request.value);if('prompt'in request)source.promptCommit(request.prompt);const actual=source.snapshot();for(const key of ['motionMs','dataCount','value','fromValue','changedMs','displayValue'])assert.equal(actual[key],row[key],key+' @'+row.elapsedMs);}
});
test('Studio partitions retain every stateful commit and snapshots are owned',()=>{
 const direct=new StudioDataSource(),partitioned=new StudioDataSource();direct.advanceTo(5001);for(const at of [1,46,47,94,425,1703,5001])partitioned.advanceTo(at);assert.deepEqual(partitioned.snapshot(),direct.snapshot());const saved=direct.snapshot();direct.advanceTo(5050);assert.notDeepEqual(direct.snapshot(),saved);assert.equal(saved.elapsedMs,5001);assert.throws(()=>direct.advanceTo(4999));
});
test('actual original Observatory waveform, lower reference and bus samples',()=>{
 for(const row of original('OBSERVATORY-ORACLE').rows){const actual=observatorySample(row.dataMs);assert.deepEqual(actual.waveform,row.waveform);assert.deepEqual(actual.bus.map(x=>x.value),row.bus.map(x=>x.value));const lines=row.scenes.scope.nodes.filter(n=>n.kind==='line');const reference=lines.find(n=>n.data?.length===128&&n.id!==7000);assert.ok(reference);assert.deepEqual(actual.reference.map(v=>Math.round(v*1000)),reference.data);assert.equal(actual.quality,'synthetic');}
});
