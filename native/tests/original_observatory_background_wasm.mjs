import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const [input,output]=process.argv.slice(2),{rows,layout}=JSON.parse(readFileSync(input,'utf8'));
const wasm=readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url));
assert.deepEqual(WebAssembly.Module.imports(new WebAssembly.Module(wasm)),[]);
function crc32(bytes){let value=0xffffffff;for(const byte of bytes){value^=byte;for(let i=0;i<8;i++)value=(value>>>1)^((value&1)?0xedb88320:0);}return (value^0xffffffff)>>>0;}
function constructed90(bytes){
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 assert.equal(view.getUint32(12,true),layout.schema);assert.equal(view.getUint32(28,true),layout.schema);
 assert.equal(view.getUint32(16,true),bytes.length-24);assert.equal(view.getUint32(20,true),crc32(bytes.subarray(24)));
 assert.ok(bytes.subarray(24+layout.prior,24+layout.current).every(x=>x===0),'Cannot discard active appended state');
 const old=new Uint8Array(bytes.length-(layout.current-layout.prior));old.set(bytes.subarray(0,24+layout.prior));old.set(bytes.subarray(24+layout.current),24+layout.prior);
 const header=new DataView(old.buffer);header.setUint32(12,0x20261090,true);header.setUint32(28,0x20261090,true);header.setUint32(16,old.length-24,true);header.setUint32(20,crc32(old.subarray(24)),true);return old;
}
function unchanged(s,operation){const before=s.snapshot(),frame=s.render().bytes;assert.throws(operation);assert.deepEqual(s.snapshot(),before);assert.deepEqual(s.render().bytes,frame);}
const results=[],checks=[];
for(const row of rows){
 const s=await NativeScene.create(wasm,2030);
 try{
  for(const c of row.commands)s.command(c);
  for(const a of row.actions){s.advanceTo(Math.round(a.atMs*1000));s.command({op:'window-application',...a.patch});}
  s.advanceTo(Math.round(row.atMs*1000));let snapshot=s.snapshot();const surface=Array.from(s.render().cells);assert.deepEqual(s.snapshot(),snapshot);
  for(const c of row.nodes)s.command(c);snapshot=s.snapshot();const composed=Array.from(s.render().cells);assert.deepEqual(s.snapshot(),snapshot);
  s.advanceTo(Math.round(row.atMs*1000)+1000);s.restore(snapshot);assert.deepEqual(s.snapshot(),snapshot);assert.deepEqual(Array.from(s.render().cells),composed);
  results.push({id:row.id,surface,composed});
  if(row===rows[0]){
   unchanged(s,()=>s.restore(constructed90(s.snapshot())));checks.push('constructed90-new-scene-atomic-rejection');
   s.command({op:'window-application',scene:'windows'});const expected=s.render().bytes;s.restore(constructed90(s.snapshot()));assert.deepEqual(s.render().bytes,expected);checks.push('constructed90-old-windows-accepted');
   s.command({op:'remove-window-application'});s.command({op:'window-application',scene:'observatory',paletteWindowId:1});
   const info=s.infoComplete().windowApplication;assert.deepEqual([info.scene,info.weatherIntensity,info.novaStrength,info.weatherLifeMs,info.weatherSpeed],['observatory',.38,.28,2400,12]);checks.push('original-defaults');
   for(const life of [200,8000])for(const speed of [1,50]){s.command({op:'window-application',weatherLifeMs:life,weatherSpeed:speed});const q=s.infoComplete().windowApplication;assert.deepEqual([q.weatherLifeMs,q.weatherSpeed],[life,speed]);}
   checks.push('original-domain-boundaries');
   for(const patch of [{weatherSpeed:0},{weatherSpeed:50.01},{weatherLifeMs:199},{weatherLifeMs:8001},{weatherSpeed:12,particles:{launchSpeed:13}},{weatherLifeMs:2400,particles:{lifeMs:2401}},... [null,true,[],{},'12'].map(weatherSpeed=>({weatherSpeed}))])unchanged(s,()=>s.command({op:'window-application',...patch}));
   unchanged(s,()=>s.command({op:'batch',commands:[{op:'window-application',weatherSpeed:50},{op:'window-application',weatherLifeMs:199}]}));checks.push('invalid-domain-type-alias-and-late-batch-atomicity');
   const raw=new TextEncoder().encode('{"op":"window-application","weatherSpeed":1e999}');const before=s.snapshot(),frame=s.render().bytes;s.ensureInput(raw.length);new Uint8Array(s.exports.memory.buffer,s.input,raw.length).set(raw);assert.ok(s.exports.nrCommand(s.context,s.input,raw.length)<0);assert.deepEqual(s.snapshot(),before);assert.deepEqual(s.render().bytes,frame);checks.push('raw-nonfinite-atomic-rejection');
   s.command({op:'window-application',weatherSpeed:50,weatherLifeMs:8000,particles:{launchSpeed:50,lifeMs:8000}});s.command({op:'window-application',gradientPhase:.3});const q=s.infoComplete().windowApplication;assert.deepEqual([q.weatherSpeed,q.weatherLifeMs],[50,8000]);checks.push('equal-aliases-and-partial-update-preservation');
  }
 }finally{s.close();}
}
writeFileSync(output,JSON.stringify({rows:results,checks}));
