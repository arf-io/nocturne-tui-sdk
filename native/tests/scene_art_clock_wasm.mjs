import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),wasm=readFileSync(resolve(root,'dist/nocturne_native.wasm'));
const hash=b=>createHash('sha256').update(b).digest('hex');
assert.ok(process.argv[2],'Independent original-sample reference directory is required');
const reference=resolve(process.argv[2]),contract=JSON.parse(readFileSync(resolve(reference,'contract.json')));
function equalBytes(a,b,label){assert.equal(a.length,b.length,label+' length');assert.equal(hash(a),hash(b),label+' SHA');}
const isolate=[{op:'environment',presentation:'canvas',stars:0,background:1053726,sampling:'braille',style:'solid'},{op:'prompt',active:false},{op:'floor',enabled:false,visible:false}];
const world=['width','height','scene','cameraX','cameraY','cameraZ','yaw','pitch','roll','fov','projection','span','flow','travel','seed','redshift','discTilt','detail','waterAlpha','background','ink','accent','secondary','sampling'];
const scales=[1,1,1,256,256,256,256,256,256,256,1,256,1000,256,1,1000,256,1,1000,1,1,1,1,1];
const fields=['waveHeight','wavelength','windAngle','crossSwell','choppiness','foam','waveSpeed','joinRiver'],detailScales=[256,256,256,1000,1000,1000,1000,1];
const names=['pearl-cascade','copper-causeway','red-shift','tidal-glass','silt'];
function visual(b){const out=Buffer.alloc(b.length/16*12);for(let i=0,j=0;i<b.length;i+=16,j+=12)out.set(b.subarray(i,i+12),j);return out;}
const e=resolve(root,'evidence/original-scenic-restoration-20261013'),manifest=JSON.parse(readFileSync(resolve(e,'ORIGINAL-WORLD-FRAMES.json')));
for(const f of manifest.frames){const s=await NativeScene.create(wasm,2030);try{
 for(const c of isolate)s.command(c);s.command({...isolate[0],background:f.worldQ[19],sampling:f.worldQ[23]?'braille':'half'});
 const controls=Object.fromEntries(world.slice(3).map((k,i)=>[k,f.worldQ[i+3]/scales[i+3]]));const detail=Object.fromEntries(fields.map((k,i)=>[k,f.detailQ[i]/detailScales[i]]));
 s.command({op:'scene-art',scene:names[f.worldQ[2]],width:f.width,height:f.height,controls,detail,timeMs:f.timeMs});s.advanceTo(12345678);
 const before=s.snapshot(),a=s.render(),expected=readFileSync(resolve(e,f.cellsFile));assert.equal(hash(expected),f.cellsSha256);const corrected=readFileSync(resolve(reference,f.cellsFile));assert.equal(hash(corrected),contract.expected[f.id]);equalBytes(visual(a.bytes),visual(corrected),f.id+' full visual with corrected braille encoding');assert.ok([...a.cells].every((v,i)=>i%4!==3||v===0));equalBytes(s.snapshot(),before,'render purity');equalBytes(s.render().bytes,a.bytes,'repeat');assert.equal(s.infoComplete().sceneArt.effective.timeMs,f.timeMs);
}finally{s.close();}}
const s=await NativeScene.create(wasm,2030),r=await NativeScene.create(wasm,2030);
try{
 for(const c of isolate){s.command(c);r.command(c);}for(const q of [s,r])q.command({op:'scene-art',scene:'pearl-cascade',width:80,height:32});
 s.command({op:'scene-art',timeMs:2000});r.advanceTo(2000000);equalBytes(s.render().bytes,r.render().bytes,'explicit source clock');s.advanceTo(9000123);s.command({op:'scene-art',controls:{waterAlpha:.94}});assert.equal(s.infoComplete().sceneArt.timeMs,2000);s.command({op:'scene-art',timeMs:null});r.advanceTo(9000123);assert.equal(s.infoComplete().sceneArt.timeMs,null);assert.equal(s.infoComplete().sceneArt.effective.timeMs,9000);equalBytes(s.render().bytes,r.render().bytes,'global clock');
 for(const t of [0,1,4294967296,9007199254740991]){s.command({op:'scene-art',timeMs:t});assert.equal(s.infoComplete().sceneArt.timeMs,t);s.render();}
 let saved=s.snapshot();for(const bad of [-1,.25,9007199254740992,'2',true,[],{}]){assert.throws(()=>s.command({op:'scene-art',timeMs:bad}));equalBytes(s.snapshot(),saved,'invalid atomic');}
 assert.throws(()=>s.command({op:'batch',commands:[{op:'scene-art',timeMs:8},{op:'scene-art',timeMs:-1}]}));equalBytes(s.snapshot(),saved,'late batch atomic');
 for(const command of [{op:'remove-scene-art'},{op:'clear',scope:'scene-art'},{op:'reset'}]){s.command(command);assert.equal(s.infoComplete().sceneArt,null);s.command({op:'scene-art',scene:'silt'});assert.equal(s.infoComplete().sceneArt.timeMs,null);s.command({op:'scene-art',timeMs:10});}
 const fix=resolve(root,'tests/fixtures/original-scenic-schema94'),proof=JSON.parse(readFileSync(resolve(fix,'PROVENANCE.json'))),old=gunzipSync(readFileSync(resolve(fix,'snapshot.gz'))),frame=gunzipSync(readFileSync(resolve(fix,'frame.gz')));
 assert.equal(hash(old),proof.snapshotSha256);assert.equal(hash(frame),proof.frameSha256);s.restore(old);const info=s.infoComplete();assert.equal(info.sceneArt.timeMs,null);assert.equal([...info.prompt.text].length,70005);assert.equal([...info.sourceModal.query].length,80000);assert.equal(info.sourceModel.triangles,4608);assert.equal(info.camera.controls.rig,'spacecraft');const currentFrame=readFileSync(resolve(reference,'genuine94-current.cells'));assert.equal(hash(currentFrame),contract.genuine94CurrentSha256);equalBytes(s.render().bytes,currentFrame,'genuine94 current native/WASM whole frame');
 saved=s.snapshot();assert.equal(new DataView(saved.buffer,saved.byteOffset,saved.byteLength).getUint32(12,true),contract.schema);assert.equal(s.infoComplete().contract.snapshotSchema,contract.schema);assert.equal(saved.length,old.length+contract.fixed-30499728);equalBytes(saved.subarray(32,24+30499728),old.subarray(32,24+30499728),'genuine94 fixed prefix');assert.ok(saved.subarray(24+30499728,24+contract.fixed).every(x=>x===0));equalBytes(saved.subarray(24+contract.fixed),old.subarray(24+30499728),'genuine94 dynamic suffix');r.restore(saved);equalBytes(r.snapshot(),saved,'current exact roundtrip');equalBytes(r.render().bytes,currentFrame,'current complete frame');
 const halfProof=JSON.parse(readFileSync(resolve(fix,'HALF-PROVENANCE.json'))),half=gunzipSync(readFileSync(resolve(fix,'half-frame.gz')));
 assert.equal(halfProof.genuine94SnapshotSha256,hash(old));assert.equal(halfProof.genuine94BrailleFrameSha256,hash(frame));assert.equal(halfProof.originalBrailleFrameVerifiedBeforeCommand,true);assert.equal(hash(half),halfProof.frameSha256);assert.deepEqual(halfProof.commandsAfterRestore,[{op:'scene-art',controls:{sampling:0}}]);s.command(halfProof.commandsAfterRestore[0]);equalBytes(s.render().bytes,half,'genuine94 complete unchanged half frame');
 console.log(JSON.stringify({passed:true,schema:contract.schema,originalFrames:manifest.frames.length,genuine94:true}));
}finally{s.close();r.close();}
