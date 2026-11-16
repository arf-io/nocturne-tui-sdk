import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
function crc(bytes){let value=0xffffffff;for(const byte of bytes){value^=byte;for(let i=0;i<8;i++)value=(value>>>1)^((value&1)?0xedb88320:0);}return (value^0xffffffff)>>>0;}
// Current PromptWire stores 131 used-length scalar arrays; its final uint32
// table has eight-byte struct alignment. nrSnapshotSize excludes used scalars.
// Arrays128/129 are the active prompt source/identities (prompt_storage.c).
function promptIdentityOffset(scene,snapshot){
 const view=new DataView(snapshot.buffer,snapshot.byteOffset,snapshot.byteLength),wireBytes=scene.exports.nrPromptWireSize(),footer=scene.exports.nrSnapshotSize()-wireBytes,arrayCount=131;
 const lengthsAt=footer+wireBytes-Math.ceil(arrayCount*4/8)*8,lengths=Array.from({length:arrayCount},(_,i)=>view.getUint32(lengthsAt+i*4,true));
 assert.equal(footer+wireBytes+lengths.reduce((sum,n)=>sum+n*4,0),snapshot.byteLength,'complete current dynamic payload');
 const source=Array.from(scene.textRunSource(0,0),c=>c.codePointAt(0)),clusters=scene.textRunClusters(0,0),identityAt=footer+wireBytes+lengths.slice(0,129).reduce((sum,n)=>sum+n*4,0);
 assert.equal(lengths[0],source.length);assert.equal(lengths[128],source.length);assert.equal(lengths[129],source.length);
 assert.equal(view.getUint32(lengthsAt-12,true),source.length,'active identity header count');assert.equal(view.getUint32(lengthsAt-8,true),clusters[0][3],'active identity generation');
 assert.deepEqual(Array.from({length:source.length},(_,i)=>view.getUint32(identityAt-source.length*4+i*4,true)),source,'active retained source');
 const identities=new Array(source.length);for(const [identity,begin,end] of clusters)identities.fill(identity,begin,end);
 assert.deepEqual(Array.from({length:source.length},(_,i)=>view.getUint32(identityAt+i*4,true)),identities,'active identities match public clusters');
 return {source:identityAt-source.length*4,identity:identityAt,generation:lengthsAt-8};
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'draft',text:'A e\u0301 Z',emitWeather:false});const old=s.textRunClusters(0,0);assert.deepEqual(old.map(r=>r.slice(1,3)),[[0,1],[1,2],[2,4],[4,5],[5,6]]);
 s.command({op:'draft',text:'A X e\u0301 Z',emitWeather:false});const current=s.textRunClusters(0,0);assert.equal(current[0][0],old[0][0]);assert.equal(current.at(-1)[0],old.at(-1)[0]);assert.equal(current.at(-3)[0],old.at(-3)[0]);assert.ok(!old.some(r=>r[0]===current[2][0]));
 s.command({op:'draft',text:'A X e\u0300 Z',emitWeather:false});assert.notEqual(s.textRunClusters(0,0).at(-3)[0],current.at(-3)[0]);
 s.command({op:'window',id:1,title:'T 👩\u200d🚀',text:'Body e\u0301'});const body=s.textRunClusters(2,1),title=s.textRunClusters(3,1);
 s.command({op:'window',id:1,width:40,height:20});assert.deepEqual(s.textRunClusters(2,1),body);assert.deepEqual(s.textRunClusters(3,1),title);
 s.command({op:'define',path:'/body',value:'Body e\u0301!',binding:{family:'window',id:1,field:'text'}});assert.deepEqual(s.textRunClusters(2,1).slice(0,-1),body);assert.deepEqual(s.textRunClusters(3,1),title);
 const before=s.snapshot();body[0][0]=99;s.render();s.textRunClusters(2,1);assert.deepEqual(s.snapshot(),before);assert.throws(()=>s.textRunClusters(2,999));
 const out=new Uint32Array(s.exports.memory.buffer,s.checkpoint,4);out.fill(123);assert.equal(s.exports.nrTextRunClusters(s.context,0,0,s.checkpoint,0),-1);assert.deepEqual(Array.from(out),[123,123,123,123]);
 s.command({op:'reset'});s.command({op:'draft',text:'A',emitWeather:false});for(const [id,atUs,text] of [[1,250000,'AB'],[2,500000,'AC'],[3,750000,'A']])s.command({op:'schedule',id,atUs,command:{op:'draft',text,emitWeather:false}});
 const start=s.snapshot();s.advanceTo(1000000);const finish=s.snapshot();s.restore(start);for(const time of [250000,500000,750000,1000000])s.advanceTo(time);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'reset'});s.command({op:'draft',text:'e\u0301 👩\u200d🚀',emitWeather:false});const oldSchema=s.snapshot().slice(0,24+12508512),view=new DataView(oldSchema.buffer,oldSchema.byteOffset,oldSchema.byteLength);view.setUint32(12,0x20261034,true);view.setUint32(16,12508512,true);view.setUint32(28,0x20261034,true);view.setUint32(20,crc(oldSchema.subarray(24)),true);
 s.restore(oldSchema);const migrated=s.snapshot(),ids=s.textRunClusters(0,0);s.restore(oldSchema);assert.deepEqual(s.snapshot(),migrated);assert.deepEqual(s.textRunClusters(0,0),ids);assert.equal(s.textRunSource(0,0),'e\u0301 👩\u200d🚀');
 const activeIdentity=promptIdentityOffset(s,migrated);s.restore(migrated);assert.deepEqual(s.snapshot(),migrated);assert.deepEqual(s.textRunClusters(0,0),ids);
 for(const [offset,value] of [[activeIdentity.source,'z'.codePointAt(0)],[activeIdentity.identity+4,ids[1][0]],[activeIdentity.generation,0],[activeIdentity.identity,0]]){
  const bad=migrated.slice(),badView=new DataView(bad.buffer,bad.byteOffset,bad.byteLength);badView.setUint32(offset,value,true);badView.setUint32(20,crc(bad.subarray(24)),true);
  assert.throws(()=>s.restore(bad));assert.deepEqual(s.snapshot(),migrated);assert.deepEqual(s.textRunClusters(0,0),ids);assert.equal(s.textRunSource(0,0),'e\u0301 👩\u200d🚀');
 }
 s.command({op:'text',id:1,text:'e\u0301x'});for(const [i,row] of s.textRunClusters(1,1).entries()){assert.equal(row[0],s.textClusterSample(1,i)[0]>>>0);assert.equal(row[3],0);}
 s.command({op:'reset'});s.command({op:'draft',text:'A',emitWeather:false});s.command({op:'schedule',id:1,atUs:500000,command:{op:'draft',text:'AB',emitWeather:false}});
 let exhausted=s.snapshot(),exhaustedView=new DataView(exhausted.buffer,exhausted.byteOffset,exhausted.byteLength);exhaustedView.setUint32(24+12508512,0xffffffff,true);exhaustedView.setUint32(20,crc(exhausted.subarray(24)),true);s.restore(exhausted);
 let blocked=s.snapshot(),retained=s.textRunClusters(0,0);assert.throws(()=>s.advanceTo(500000));assert.deepEqual(s.snapshot(),blocked);assert.deepEqual(s.textRunClusters(0,0),retained);s.restore(blocked);assert.deepEqual(s.snapshot(),blocked);
 s.command({op:'cancel-schedule',id:1});s.advanceTo(500000);assert.equal(s.textRunSource(0,0),'A');assert.deepEqual(s.textRunClusters(0,0),retained);
 s.command({op:'reset'});s.command({op:'schedule',id:1,atUs:500000,command:{op:'window',id:1,title:'New',text:'Body'}});exhausted=s.snapshot();exhaustedView=new DataView(exhausted.buffer,exhausted.byteOffset,exhausted.byteLength);exhaustedView.setUint32(24+12508512+4,0xffffffff,true);exhaustedView.setUint32(20,crc(exhausted.subarray(24)),true);s.restore(exhausted);
 blocked=s.snapshot();assert.throws(()=>s.advanceTo(500000));assert.deepEqual(s.snapshot(),blocked);s.restore(blocked);assert.deepEqual(s.snapshot(),blocked);s.command({op:'cancel-schedule',id:1});s.advanceTo(500000);assert.throws(()=>s.textRunClusters(2,1));

 for(const counter of [12508512,12508516]){
  s.command({op:'reset'});s.command({op:'draft',text:'éx',emitWeather:false});const data=s.snapshot(),view=new DataView(data.buffer,data.byteOffset,data.byteLength);view.setUint32(24+counter,0xffffffff,true);view.setUint32(20,crc(data.subarray(24)),true);s.restore(data);
  const before=s.snapshot(),ids=s.textRunClusters(0,0);s.render();assert.equal(s.textRunSource(0,0),'éx');assert.deepEqual(s.textRunClusters(0,0),ids);assert.deepEqual(s.snapshot(),before);s.restore(before);assert.deepEqual(s.snapshot(),before);
 }
 s.command({op:'reset'});const longText='A'+'é中👩‍🚀'.repeat(11000);s.command({op:'draft',text:longText,emitWeather:false});const longIds=s.textRunClusters(0,0),longBefore=s.snapshot(),longCapacity=s.exports.nrPromptMemoryCapacity(s.context),queued={op:'schedule',id:1,atUs:500000,command:{op:'input',text:'X'}},raw=new TextEncoder().encode(JSON.stringify(queued));
 s.ensureInput(raw.length);new Uint8Array(s.exports.memory.buffer,s.input,raw.length).set(raw);assert.ok(s.exports.nrCommand(s.context,s.input,raw.length)<0);assert.equal(s.string(s.exports.nrError(s.context)),'Prompt storage required');assert.ok(s.exports.nrPromptMemorySize(s.context)>longCapacity);assert.deepEqual(s.snapshot(),longBefore);
 s.command(queued);assert.ok(s.exports.nrPromptMemoryCapacity(s.context)>longCapacity);const normal=s.snapshot();assert.throws(()=>s.command({op:'schedule',id:2,atUs:600000,command:{op:'input',text:123}}),/Scheduled command fails validation against current state/);assert.deepEqual(s.snapshot(),normal);assert.deepEqual(s.textRunClusters(0,0),longIds);
 s.advanceTo(500000);assert.equal(s.textRunSource(0,0),longText+'X');s.command({op:'key',key:'z',ctrl:true});assert.equal(s.textRunSource(0,0),longText);assert.deepEqual(s.textRunClusters(0,0),longIds);s.command({op:'key',key:'r',ctrl:true});assert.equal(s.textRunSource(0,0),longText+'X');s.command({op:'key',key:'z',ctrl:true});assert.equal(s.textRunSource(0,0),longText);assert.deepEqual(s.textRunClusters(0,0),longIds);s.restore(normal);
 const longExhausted=normal.slice(),longView=new DataView(longExhausted.buffer,longExhausted.byteOffset,longExhausted.byteLength);longView.setUint32(24+12508512,0xffffffff,true);longView.setUint32(20,crc(longExhausted.subarray(24)),true);s.restore(longExhausted);const longBlocked=s.snapshot();s.render();assert.equal(s.textRunSource(0,0),longText);assert.deepEqual(s.textRunClusters(0,0),longIds);assert.deepEqual(s.snapshot(),longBlocked);
 assert.throws(()=>s.advanceTo(500000));assert.deepEqual(s.snapshot(),longBlocked);assert.deepEqual(s.textRunClusters(0,0),longIds);s.restore(longBlocked);assert.deepEqual(s.snapshot(),longBlocked);s.command({op:'cancel-schedule',id:1});s.advanceTo(500000);assert.equal(s.textRunSource(0,0),longText);assert.deepEqual(s.textRunClusters(0,0),longIds);
}finally{s.close();}
console.log(JSON.stringify({runtime:'actual WASM',concern:'retained source cluster IDs',unicode:true,windowBindings:true,queuedPartitionReplay:true,migration:true,corruptionRejection:true,purity:true}));
