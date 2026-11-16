import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {NativeScene} from './native_scene.mjs';
const fix=new URL('../../tests/fixtures/source-model/',import.meta.url), data=fs.readFileSync(new URL('model-records.bin',fix));
const wasm=fs.readFileSync(process.env.NOCTURNE_MODEL_WASM||new URL('../../dist/nocturne_native.wasm',import.meta.url));
const a=await NativeScene.create(wasm,2030), b=await NativeScene.create(wasm,2030);
assert.equal(typeof a.setModelRecords,'function');a.setModelRecords(data);assert.deepEqual(a.modelRecords(),new Uint8Array(data));
const oracle=JSON.parse(fs.readFileSync(new URL('ORACLE.json',fix),'utf8'));
oracle.frames.push(...JSON.parse(fs.readFileSync(new URL('DEPTH-ORACLE.json',fix),'utf8')).frames);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const originalBytes=fs.readFileSync(new URL('world.wasm',fix));
assert.equal(sha(originalBytes),oracle.wasmSha256);
const originalModule=new WebAssembly.Module(originalBytes);
assert.deepEqual(WebAssembly.Module.imports(originalModule),[]);
const original=new WebAssembly.Instance(originalModule).exports;
const maxCells=Math.max(...oracle.frames.map(row=>row.config[0]*row.config[1]));
const colorsPtr=original.memory.buffer.byteLength,depthPtr=colorsPtr+maxCells*8*4;
original.memory.grow(Math.ceil(maxCells*8*8/65536));
function originalModelExpected(row,archived,records){
 const q=row.config,count=q[0]*q[1],background=q[19];
 assert.equal(sha(archived),row.sha256,'Immutable model frame SHA: '+row.id);
 assert.equal(records.length%40,0);
 new Int32Array(original.memory.buffer,original.nsWorldConfigPtr(),24).set(q);
 new Uint8Array(original.memory.buffer,original.nsWorldMeshPtr(),records.length).set(records);
 const written=original.nsWorldRenderMesh(original.nsWorldConfigPtr(),0n,original.nsWorldMeshPtr(),records.length/40,
   original.nsFramePtr(),count,colorsPtr,depthPtr,count*8);
 assert.equal(written,count,'Original renderer rejected '+row.id);
 const untouched=Buffer.from(original.memory.buffer,original.nsFramePtr(),count*16);
 assert.ok(untouched.equals(archived),'Original source/immutable frame differs: '+row.id);
 if(!q[23])return Buffer.from(archived);
 // The original renderer supplies geometry/color samples. RC2 intentionally
 // replaces its full-occupancy solid/half-block fallback with eight dots.
 const pixels=new Uint32Array(original.memory.buffer,colorsPtr,count*8),out=Buffer.alloc(count*16),dots=[1,8,2,16,4,32,64,128];
 for(let y=0;y<q[1];y++)for(let x=0;x<q[0];x++){
  let mask=0,n=0,r=0,g=0,b=0;
  for(let k=0;k<8;k++){const color=pixels[(y*4+Math.floor(k/2))*(q[0]*2)+x*2+k%2];
   if(color!==background){mask|=dots[k];n++;r+=(color>>>16)&255;g+=(color>>>8)&255;b+=color&255;}}
  const at=(y*q[0]+x)*16,fg=n?(Math.floor(r/n)<<16)|(Math.floor(g/n)<<8)|Math.floor(b/n):background;
  out.writeUInt32LE(mask?0x2800+mask:32,at);out.writeUInt32LE(fg,at+4);
  out.writeUInt32LE(background,at+8);out.writeUInt32LE(n?1:0,at+12);
 }
 return out;
}
const negativeRow=oracle.frames.find(row=>row.config[23]),archived=fs.readFileSync(new URL(negativeRow.id,fix));
const altered=Buffer.from(archived);altered[4]^=1;
assert.throws(()=>originalModelExpected({...negativeRow,sha256:sha(altered)},altered,data),/Original source\/immutable frame differs/);
const alteredRecords=Buffer.from(data);for(let at=36;at<alteredRecords.length;at+=40)alteredRecords.writeUInt32LE(0x00ff00,at);
assert.throws(()=>originalModelExpected(negativeRow,archived,alteredRecords),/Original source\/immutable frame differs/);

let frames=0;
for(const row of oracle.frames){const records=fs.readFileSync(new URL(row.recordsFile||'model-records.bin',fix));a.setModelRecords(records);const q=row.config;
 a.command({op:'environment',presentation:'canvas',stars:0,background:q[19],sampling:q[23]?'braille':'half',style:'solid'});a.command({op:'prompt',active:false});a.command({op:'floor',enabled:false,visible:false});
 a.command({op:'model-view',width:q[0],height:q[1],controls:{cameraX:q[3]/256,cameraY:q[4]/256,cameraZ:q[5]/256,yaw:q[6]/256,pitch:q[7]/256,roll:q[8]/256,fov:q[9]/256,projection:q[10],span:q[11]/256,background:q[19],sampling:q[23]}});
 const before=a.snapshot(),actual=a.render().bytes,expected=originalModelExpected(row,fs.readFileSync(new URL(row.id,fix)),records);for(let i=12;i<expected.length;i+=16)expected.writeUInt32LE(0,i);
 assert.ok(Buffer.from(actual).equals(expected),`${row.id}: actual ${actual.length}B ${sha(actual)}, expected ${expected.length}B ${sha(expected)}`);assert.deepEqual(a.snapshot(),before);frames++;
 if(process.env.NOCTURNE_MODEL_CAPTURE_DIR){fs.mkdirSync(process.env.NOCTURNE_MODEL_CAPTURE_DIR+'/wasm',{recursive:true});fs.writeFileSync(process.env.NOCTURNE_MODEL_CAPTURE_DIR+'/wasm/'+row.id,actual);}
}
a.setModelRecords(data);a.command({op:'input',text:'A🙂אב\n'.repeat(14001)});const snap=a.snapshot();b.restore(snap);assert.deepEqual(b.snapshot(),snap);assert.deepEqual(b.modelRecords(),new Uint8Array(data));assert.deepEqual(b.render().bytes,a.render().bytes);
const bad=Buffer.from(data);bad.writeUInt32LE(0x1000000,36);assert.throws(()=>a.setModelRecords(bad));assert.deepEqual(a.snapshot(),snap);assert.throws(()=>a.setModelRecords(new Uint8Array(39)));
a.setModelRecords(new Uint8Array());assert.equal(a.modelRecords().length,0);assert.deepEqual(b.modelRecords(),new Uint8Array(data));a.close();b.close();assert.throws(()=>a.modelRecords());
const oldFix=new URL('../../tests/fixtures/first-prompt-schema89/',import.meta.url),migrated=await NativeScene.create(wasm);try{const original=gunzipSync(fs.readFileSync(new URL('snapshot.gz',oldFix)));assert.equal(original.readUInt32LE(12),0x20261089);migrated.restore(original);assert.deepEqual(Buffer.from(migrated.render().bytes),gunzipSync(fs.readFileSync(new URL('frame.gz',oldFix))));assert.equal(migrated.modelRecords().length,0);assert.equal(new DataView(migrated.snapshot().buffer).getUint32(12,true),migrated.info().contract.snapshotSchema);}finally{migrated.close();}
const ownFix=new URL('../../tests/fixtures/original-model-schema90/',import.meta.url),roundtrip=await NativeScene.create(wasm);try{const original=gunzipSync(fs.readFileSync(new URL('snapshot.gz',ownFix)));roundtrip.restore(original);const promoted=Buffer.from(roundtrip.snapshot());assert.equal(promoted.readUInt32LE(12),roundtrip.info().contract.snapshotSchema);assert.deepEqual(promoted.subarray(32,24+30489392),original.subarray(32,24+30489392));assert.deepEqual(promoted.subarray(24+30489392+promoted.length-original.length),original.subarray(24+30489392));roundtrip.restore(promoted);assert.deepEqual(Buffer.from(roundtrip.snapshot()),promoted);assert.deepEqual(Buffer.from(roundtrip.render().bytes),gunzipSync(fs.readFileSync(new URL('frame.gz',ownFix))));assert.deepEqual(roundtrip.modelRecords(),new Uint8Array(data));}finally{roundtrip.close();}
console.log(JSON.stringify({status:'PASS',originalFrames:frames,encoding:'original samples / RC2 braille / exact half',referenceNegativeControls:2,triangles:4608,longPromptScalars:70005,snapshotAtomic:true}));
