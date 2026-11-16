import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
function crc32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'character-region',region:{id:'fragment',path:'/app/fragment',cells:[0],indices:[9]}});
 s.command({op:'character-rule',rule:{id:'invert',selector:{path:'/app/fragment'},foregroundEffects:[{type:'invert'}]}});
 const good=s.snapshot(),frame=s.render().bytes;
 for(const command of [
  '{"op":"character-rule","rule":{"id":"first","id":"second"}}',
  '{"op":"character-rule","rule":{"id":"x\\u0000hidden"}}',
  '{"op":"character-region","region":{"id":"x","path":"/app/x\\u0000hidden"}}',
 ]){
  const bytes=new TextEncoder().encode(command);new Uint8Array(s.exports.memory.buffer,s.input,bytes.length).set(bytes);
  assert.equal(s.exports.nrCommand(s.context,s.input,bytes.length),-1);assert.deepEqual(s.snapshot(),good);
 }
 for(const base of [24+7771360,24+8296672])for(const fault of ['used','length','terminator','tail','unused','duplicate','json']){
  const damaged=new Uint8Array(good),view=new DataView(damaged.buffer);const length=view.getInt32(base+4,true);
  if(fault==='used')view.setInt32(base,2,true);
  else if(fault==='length')view.setInt32(base+4,4096,true);
  else if(fault==='terminator')damaged[base+8+length]=1;
  else if(fault==='tail')damaged[base+9+length]=1;
  else if(fault==='unused')damaged[base+4104+8]=1;
  else if(fault==='duplicate')damaged.set(good.subarray(base,base+4104),base+4104);
  else damaged[base+8]=91;
  view.setUint32(20,crc32(damaged.subarray(24)),true);
  assert.throws(()=>s.restore(damaged),`${base}:${fault}`);assert.deepEqual(s.snapshot(),good);assert.deepEqual(s.render().bytes,frame);
 }
 const fixture=gunzipSync(readFileSync(new URL('../../tests/fixtures/schema-20261031-before-trigger-formulas.snapshot.gz',import.meta.url)));
 s.restore(fixture);assert.deepEqual(s.info().characterRules,[]);assert.deepEqual(s.info().characterRegions,[]);
 const promoted=s.snapshot();s.render();assert.deepEqual(s.snapshot(),promoted);
 console.log(JSON.stringify({runtime:'actual WASM',hostileSourceOracles:14,schema31Promotion:true,cachePreservedOnFailure:true,purity:true}));
}finally{s.close();}
