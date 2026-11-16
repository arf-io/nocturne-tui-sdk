import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';

const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
function equalBytes(actual,expected,label){
  assert.equal(actual.byteLength,expected.byteLength,label+' length');
  assert.equal(sha256(actual),sha256(expected),label+' SHA256');
}
function crc32(bytes){let crc=0xffffffff;for(const x of bytes){crc^=x;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
function word(bytes,offset){return new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getUint32(offset,true);}
function validSnapshot(bytes,schema){
  assert.equal(word(bytes,8),1,'Snapshot ABI');
  assert.equal(word(bytes,12),schema,'Outer snapshot schema');
  assert.equal(word(bytes,28),schema,'Inner state schema');
  assert.equal(word(bytes,16),bytes.byteLength-24,'Payload length');
  assert.equal(word(bytes,20),crc32(bytes.subarray(24)),'Payload CRC32');
}
const wasm=fs.readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const a=await NativeScene.create(wasm),b=await NativeScene.create(wasm);
try{
  const text='🙂A\0אב\n'.repeat(14001);
  assert.equal(Array.from(text).length,84006);
  assert.equal(Array.from(text).filter(c=>c.codePointAt(0)===0).length,14001,'Actual embedded NULs');
  assert.equal(Array.from(text).filter(c=>c==='\n').length,14001,'Actual newlines');
  const push={op:'source-modal',action:'push',entry:{id:'same',kind:'drawer-right',title:text,body:text,atMs:0,dismissible:true},context:text};
  a.command(push);a.command({op:'source-modal',action:'edit',query:text,selected:3});
  let info=a.infoComplete().sourceModal;
  assert.equal(info.query,text);assert.equal(info.context,text);assert.equal(info.entries[0].title,text);assert.equal(info.entries[0].body,text);
  const saved=a.snapshot();b.restore(saved);equalBytes(b.snapshot(),saved,'Current long-text snapshot');
  a.command(push);a.command({op:'source-modal',action:'dismiss'});assert.equal(a.infoComplete().sourceModal.query,text);
  const before=a.snapshot();
  assert.throws(()=>a.command({op:'batch',commands:[{op:'source-modal',action:'clear'},{op:'invalid'}]}));
  equalBytes(a.snapshot(),before,'Late batch rollback');
  a.command({op:'input',text:'blocked'});assert.equal(a.infoComplete().prompt.text,'');
  const base=new URL('../../tests/fixtures/original-modal-schema93/',import.meta.url);
  const provenance=JSON.parse(fs.readFileSync(new URL('PROVENANCE.json',base)));
  const modalOffset=provenance.modalOffset;
  for(const [offset,value] of [[24+modalOffset,9],[24+modalOffset+4,0xffffffff],[24+modalOffset+48+96,0xffffffff],[before.length-4,0xd800]]){
    const bad=before.slice(),v=new DataView(bad.buffer,bad.byteOffset,bad.byteLength);
    v.setUint32(offset,value,true);v.setUint32(20,crc32(bad.subarray(24)),true);
    assert.throws(()=>a.restore(bad));equalBytes(a.snapshot(),before,'Corrupt modal rollback at '+offset);
  }
  const fixture=zlib.gunzipSync(fs.readFileSync(new URL('snapshot.gz',base)));
  const frame=zlib.gunzipSync(fs.readFileSync(new URL('frame.gz',base)));
  const fixtureHash='f98615e1f53b1dcfa7d4cf3262a84697d04e37fad64ec85fc361968ad76715ae';
  const frameHash='e9c20ab3b01cac839eee67f0a607739af8a6468572c2d89fdd9da169d80aa323';
  assert.equal(provenance.snapshotSha256,fixtureHash);assert.equal(sha256(fixture),fixtureHash);
  assert.equal(provenance.frameSha256,frameHash);assert.equal(sha256(frame),frameHash);
  assert.equal(provenance.fixedPrefixBytes,30499432);assert.equal(modalOffset,30494248);
  validSnapshot(fixture,0x20261093);
  b.restore(fixture);
  const promoted=b.snapshot(),fixed93=provenance.fixedPrefixBytes,cameraBytes=296,clockBytes=16,fixed95=fixed93+cameraBytes+clockBytes;
  validSnapshot(promoted,0x20261095);
  assert.equal(promoted.length,fixture.length+cameraBytes+clockBytes,'Published append size');
  equalBytes(promoted.subarray(0,12),fixture.subarray(0,12),'Magic and ABI retained');
  equalBytes(promoted.subarray(24,28),fixture.subarray(24,28),'State magic retained');
  equalBytes(promoted.subarray(32,24+fixed93),fixture.subarray(32,24+fixed93),'Original fixed prefix except schema');
  equalBytes(promoted.subarray(24+fixed93,24+fixed95),new Uint8Array(cameraBytes+clockBytes),'Disabled appended controls and clock');
  equalBytes(promoted.subarray(24+fixed95),fixture.subarray(24+fixed93),'Complete original document/model/modal payload');
  info=b.infoComplete();
  assert.equal(info.contract.snapshotSchema,0x20261095);assert.equal(info.sourceModal.depth,2);assert.equal(Array.from(info.sourceModal.query).length,80000);
  assert.equal(Array.from(info.prompt.text).length,provenance.documentScalars);assert.equal(info.sourceModel.triangles,provenance.sourceModelTriangles);
  assert.deepEqual(info.camera.controls,{
    enabled:false,rig:'orbit',mode:'orbit',inputTarget:'body',
    inputAxes:Object.fromEntries(['x','y','z'].map(axis=>[axis,{action:'disabled',sensitivity:0,enabled:false,invert:false}])),
    head:{position:[0,0,0],rotation:[0,0,0]},crane:{pivot:[0,0,0],boom:[0,0,0]},
    follow:{target:{kind:'point',point:[0,0,0]},offset:[0,0,0],track:false},anchor:null,
  });
  const rendered=b.render().cells;
  equalBytes(new Uint8Array(rendered.buffer,rendered.byteOffset,rendered.byteLength),frame,'Exact historical frame');
  equalBytes(b.snapshot(),promoted,'Historical rendering purity');
  a.restore(promoted);equalBytes(a.snapshot(),promoted,'Current schema roundtrip');
  assert.equal(sha256(fixture),fixtureHash,'Genuine input fixture immutable');
  a.command({op:'scene-art',scene:'copper-causeway'});
  const clock=a.infoComplete();assert.equal(clock.sceneArt.timeMs,null);assert.equal(clock.sceneArt.effective.timeMs,Math.floor(clock.clock.timeUs/1000));
}finally{a.close();b.close();}
console.log('PASS actual WASM modal long strings/NUL/newline/nesting/rollback/input ownership/genuine93 migration/exact frame/current roundtrip');
