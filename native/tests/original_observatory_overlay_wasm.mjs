import fs from 'node:fs';import crypto from 'node:crypto';import zlib from 'node:zlib';import assert from 'node:assert/strict';import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const wasm=fs.readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url));assert.equal(WebAssembly.Module.imports(await WebAssembly.compile(wasm)).length,0);const out=[];
for(const row of JSON.parse(fs.readFileSync(process.argv[2]))){const s=await NativeScene.create(wasm);for(const c of row.commands)s.command(c);s.advanceTo(row.atUs);s.command(row.overlay);let before=s.snapshot();const underlay=Array.from(s.render().cells);assert.deepEqual(s.snapshot(),before);for(const c of row.nodes)s.command(c);before=s.snapshot();const frame=Array.from(s.render().cells);assert.deepEqual(s.snapshot(),before);out.push({id:row.id,underlay,frame});s.close();}
function exact(actual,expected,label){
 const a=Buffer.from(actual),b=Buffer.from(expected);
 assert.equal(a.length,b.length,`${label}: length`);
 assert.ok(a.equals(b),`${label}: sha256 ${crypto.createHash('sha256').update(a).digest('hex')} != ${crypto.createHash('sha256').update(b).digest('hex')}`);
}
function migrated(scene,raw,oldFixed){
 const saved=Buffer.from(scene.snapshot()),fixed=30499744,schema=0x20261095;
 assert.equal(saved.readUInt32LE(12),schema);assert.equal(saved.readUInt32LE(28),schema);
 assert.equal(scene.info().contract.snapshotSchema,schema);
 assert.equal(saved.readUInt32LE(16),saved.length-24);
 assert.equal(saved.length-raw.length,fixed-oldFixed);
 exact(saved.subarray(32,24+oldFixed),raw.subarray(32,24+oldFixed),'historical fixed prefix');
 assert.ok(saved.subarray(24+oldFixed,24+fixed).every(v=>v===0),'new appendices initialize disabled');
 exact(saved.subarray(24+fixed),raw.subarray(24+oldFixed),'complete prompt/model suffix');
 scene.restore(saved);exact(scene.snapshot(),saved,'current writer roundtrip');
 return saved;
}
for(const [epoch,folder,snapshotName,frameName,oldFixed] of [
 [91,'original-observatory-overlay','genuine91-snapshot.gz','genuine91-frame.gz',30494208],
 [92,'original-observatory-schema92','snapshot.gz','frame.gz',30494248],
]){
 const scene=await NativeScene.create(wasm),fixture=new URL(`./fixtures/${folder}/`,import.meta.url);
 const raw=zlib.gunzipSync(fs.readFileSync(new URL(snapshotName,fixture)));
 assert.equal(raw.readUInt32LE(12),epoch===91?0x20261091:0x20261092);
 scene.restore(raw);const saved=migrated(scene,raw,oldFixed);
 exact(scene.render().bytes,zlib.gunzipSync(fs.readFileSync(new URL(frameName,fixture))),`original${epoch} complete frame`);
 assert.equal(Array.from(scene.infoComplete().prompt.text).length,70005);
 const model=scene.modelRecords();assert.equal(model.length,4608*40);
 const proof=JSON.parse(fs.readFileSync(new URL(epoch===91?'GENUINE91-PROVENANCE.json':'PROVENANCE.json',fixture)));
 assert.equal(crypto.createHash('sha256').update(model).digest('hex'),proof.modelSha256);
 if(epoch===91)assert.equal(scene.info().observatoryOverlay.enabled,false);
 else assert.equal(scene.info().observatoryOverlay.kind,'dag');
 exact(scene.snapshot(),saved,'render/query purity');scene.close();
}
fs.writeFileSync(process.argv[3],JSON.stringify(out));console.log(JSON.stringify({frames:out.length,migration91:true,replay92:true}));
