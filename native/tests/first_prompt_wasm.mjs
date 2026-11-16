import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const wasm=readFileSync(process.argv[2]);const payload=JSON.parse(readFileSync(process.argv[3]));
// An array holds 96x40 original rows; {extent:[...]} holds rows beyond the archived 512x256 library ABI.
const oracle=Array.isArray(payload)?payload:payload.extent;
const same=(actual,expected,label)=>{if(actual.equals(expected))return;let i=0;while(i<actual.length&&actual[i]===expected[i])i++;assert.fail(`${label}: ${actual.length}/${expected.length} bytes, first difference at cell ${Math.floor(i/16)} word ${Math.floor(i%16/4)}`);};
for(const row of oracle){const s=await NativeScene.create(wasm);try{
 const width=row.width??96,height=row.height??40;
 s.command({op:'resize',width,height});s.command({op:'prompt-source',values:{layout:1,...row.values}});if(row.arrays)s.command({op:'prompt-source',...row.arrays});s.command({op:'draft',text:row.text??'Original prompt',emitWeather:false});s.advanceTo(row.timeUs);
 if(row.geometry){
  const g=s.info().prompt.firstPromptSource;assert.deepEqual([g.visibleStart,g.visibleEnd,g.column,g.row],row.geometry);assert.deepEqual(g.values.slice(0,2),[width,height]);
  // Caller-owned render memory has not grown yet: the core reports the storage diagnostic and keeps the surface.
  assert.ok(s.exports.nrRenderMemorySize(s.context)>s.exports.nrRenderMemoryCapacity(s.context));const held=s.snapshot();
  assert.equal(s.exports.nrRender(s.context),0);assert.equal(s.string(s.exports.nrError(s.context)),'Viewport render memory required');assert.deepEqual(s.snapshot(),held);assert.deepEqual(s.info().prompt.firstPromptSource,g);
 }
 const snapshot=s.snapshot(),clock=JSON.stringify(s.info().clock),frame=Buffer.from(s.render().bytes);same(frame,Buffer.from(row.expected,'base64'),`${width}x${height}`);assert.deepEqual(s.snapshot(),snapshot);assert.deepEqual(s.promptVisualLayout(),[]);
 if(row.geometry){same(Buffer.from(s.render().bytes),frame,`${width}x${height} repeat`);assert.equal(JSON.stringify(s.info().clock),clock);assert.deepEqual(s.snapshot(),snapshot);}
}finally{s.close();}}
if(!Array.isArray(payload))console.log(`PASS actual WASM ${oracle.length} original frames beyond 512x256, render purity and render-memory diagnostic`);
else{
const s=await NativeScene.create(wasm);try{
 s.command({op:'resize',width:96,height:40});s.command({op:'prompt-source'});const text='a'.repeat(66001)+'e\u0301🪶\u202aאב\u202c終';s.command({op:'draft',text,emitWeather:false});assert.equal(s.info().prompt.text,text);s.command({op:'select',anchor:66001,caret:66003,unit:'grapheme'});assert.equal(s.selectedText(),'e\u0301');const before=s.snapshot();assert.throws(()=>s.command({op:'resize',width:2097153,height:40}));assert.deepEqual(s.snapshot(),before);s.command({op:'draft',text:'later',emitWeather:false});s.restore(before);assert.equal(s.info().prompt.text,text);
}finally{s.close();}console.log('PASS actual WASM44 original frames and unbounded Unicode current document');

const migrated=await NativeScene.create(wasm);try{const currentSchema=new DataView(migrated.snapshot().buffer).getUint32(12,true);const original=gunzipSync(readFileSync(new URL('./fixtures/camera-graph-sky-schema88/snapshot.gz',import.meta.url)));const frame=gunzipSync(readFileSync(new URL('./fixtures/camera-graph-sky-schema88/frame.gz',import.meta.url)));migrated.restore(original);assert.deepEqual(Buffer.from(migrated.render().bytes),frame);assert.equal(migrated.info().prompt.firstPromptSource,null);assert.equal(new DataView(migrated.snapshot().buffer).getUint32(12,true),currentSchema);}finally{migrated.close();}console.log('PASS genuine88 snapshot full-frame migration in WASM');
}
