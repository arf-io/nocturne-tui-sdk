import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const directory=process.argv[2],read=name=>fs.readFileSync(path.join(directory,name)),write=(name,bytes)=>fs.writeFileSync(path.join(directory,name),bytes);
const requests=JSON.parse(read('requests.json')),bytes=fs.readFileSync(process.argv[3]),scene=await NativeScene.create(bytes,2030),results=[];
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function subset(want,got,at=''){if(want!==null&&typeof want==='object'&&!Array.isArray(want)){for(const[k,v]of Object.entries(want)){assert.ok(Object.hasOwn(got,k),at+'/'+k);subset(v,got[k],at+'/'+k);}}else if(Array.isArray(want)){assert.equal(got.length,want.length,at);want.forEach((v,i)=>subset(v,got[i],at+'/'+i));}else assert.deepEqual(got,want,at);}
function grow(c){scene.command({op:'prompt',presentation:'framed',mode:'grow',active:true,maxChars:0});scene.command({op:'draft',text:c.text,emitWeather:false});let count=Array.from(c.text).length;scene.command({op:'select',anchor:count-12,caret:count});}
for(const c of requests){
 let name=c.schema;grow(c);scene.restore(read(name+'.old'));subset(c.readback,scene.infoComplete());assert.equal(scene.textRunSource(0,0),c.source);assert.equal(scene.selectedText(),c.selection);
 let saved=Buffer.from(scene.snapshot()),frame=Buffer.from(scene.render().bytes);assert.deepEqual(frame,read(name+'.frame'),name+' original artwork');assert.deepEqual(Buffer.from(scene.snapshot()),saved,name+' render purity');assert.deepEqual(saved,read(name+'.native'),name+' migrated cross-backend snapshot');assert.ok(saved.readUInt32LE(12)>=0x20261085,'combined schema85 required');
 scene.restore(saved);assert.deepEqual(Buffer.from(scene.render().bytes),frame,name+' replay');grow(c);assert.equal(scene.textRunSource(0,0),c.text);assert.equal(scene.selectedText(),c.selectionText);
 let grown=Buffer.from(scene.snapshot()),grownFrame=Buffer.from(scene.render().bytes);assert.deepEqual(grown,read(name+'.grown-native'),name+' grown prompt snapshot');assert.deepEqual(grownFrame,read(name+'.grown-frame'),name+' grown prompt artwork');assert.deepEqual(Buffer.from(scene.snapshot()),grown,name+' grown render purity');write(name+'.grown-wasm',grown);
 results.push({sourceSchema:name,targetSchema:'0x'+saved.readUInt32LE(12).toString(16),originalSnapshotSha256:hash(read(name+'.old')),frameSha256:hash(frame),migratedSnapshotSha256:hash(saved),grownSnapshotSha256:hash(grown),grownFrameSha256:hash(grownFrame),promptScalars:Array.from(c.text).length,status:'PASS'});
}scene.close();console.log(JSON.stringify({status:'PASS',cases:results}));
