// Real WASM against independent reflected IEEE bitwise reference.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
function reference(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let j=0;j<8;j++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 const corpus=Uint8Array.from({length:8192},(_,i)=>i&255),p=s.input;
 new Uint8Array(s.exports.memory.buffer,p,corpus.length).set(corpus);
 for(let offset=0;offset<16;offset++)for(const length of [...Array.from({length:130},(_,i)=>i),255,256,257,511,512,513,1023,1024,1025,4095,4096,4097])assert.equal(s.exports.nrCrc(p+offset,length)>>>0,reference(corpus.slice(offset,offset+length)));
 s.command({op:'draft',text:'CRC é中',emitWeather:false});const snap=s.snapshot();
 assert.equal(new DataView(snap.buffer,snap.byteOffset,snap.byteLength).getUint32(20,true),reference(snap.slice(24)));
 s.restore(snap);assert.deepEqual(s.snapshot(),snap);const bad=snap.slice();bad[bad.length-1]^=1;assert.throws(()=>s.restore(bad));assert.deepEqual(s.snapshot(),snap);
 console.log('PASS actual WASM CRC vectors, snapshot and atomic corruption');
}finally{s.close();}
