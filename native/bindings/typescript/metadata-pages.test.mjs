import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
test('legacy imports report promoted state and preserve immutable fixture bytes',async()=>{
 const fixture=gunzipSync(readFileSync(new URL('../../tests/fixtures/schema-20261031-before-trigger-formulas.snapshot.gz',import.meta.url)));
 const manifest=JSON.parse(readFileSync(new URL('../../tests/fixtures/schema-20261031-before-trigger-formulas.snapshot.json',import.meta.url),'utf8'));
 assert.equal(createHash('sha256').update(fixture).digest('hex'),manifest.snapshotSha256);
 const supplied=Uint8Array.from(fixture),scene=await NativeScene.create(wasm,42);try{
 const currentSchema=new DataView(scene.snapshot().buffer).getUint32(12,true);assert.ok(currentSchema>=0x20261068);
  scene.restore(supplied);assert.deepEqual(supplied,Uint8Array.from(fixture));
  const promoted=scene.snapshot(),contract=scene.info().contract;
  assert.equal(contract.snapshotSchema,currentSchema);assert.equal(contract.sourceSchema,currentSchema);
  assert.equal(contract.sourceSchema,new DataView(promoted.buffer,promoted.byteOffset,promoted.byteLength).getUint32(28,true));
  assert.equal(contract.snapshotCapacityBytes,promoted.length);scene.restore(promoted);
  assert.deepEqual(scene.info().contract,contract);assert.deepEqual(scene.snapshot(),promoted);
 }finally{scene.close();}
});
test('runtime discovery matches snapshot wire metadata and owns its arrays',async()=>{
 const scene=await NativeScene.create(wasm,42);try{
  const saved=scene.snapshot(),header=new DataView(saved.buffer,saved.byteOffset,saved.byteLength),contract=scene.info().contract;
  assert.equal(contract.abiVersion,header.getUint32(8,true));assert.equal(contract.snapshotSchema,header.getUint32(12,true));
  assert.equal(contract.sourceSchema,header.getUint32(28,true));assert.equal(contract.snapshotCapacityBytes,saved.length);
  assert.equal(contract.metadataProfile,'nocturne.metadata/v1');assert.equal(contract.commandProfile,'nocturne.commands/v1');
  assert.equal(contract.bindingFamilies.length,24);assert.equal(new Set(contract.bindingFamilies).size,24);
  assert.ok(contract.bindingFamilies.includes('accessibility'));assert.ok(contract.features.includes('character-cell-inspection'));
  assert.deepEqual(scene.snapshot(),saved);scene.restore(saved);assert.deepEqual(scene.info().contract,contract);
  contract.bindingFamilies.length=0;assert.equal(scene.info().contract.bindingFamilies.length,24);
 }finally{scene.close();}
});
test('window and area authored controls survive binding teardown and restoration',async()=>{
 const scene=await NativeScene.create(wasm,42);try{
  for(const family of ['window','area']){
   const properties=family==='window'?{width:2000000000,height:1000000000,position:[1,2,3],yaw:12,pitch:13,roll:14,alpha:.6,group:7,title:'NOC 日本',text:'Retained source'}:
    {x:-2147483648,y:2147483647,width:2147483647,height:2147483647,padding:2,margin:1,alpha:.7,hideEmpty:true,speedX:12,speedY:3,layout:'queue'};
   const timing=family==='window'?{durationMs:1200}:{fadeMs:500,gapMs:250};
   scene.command({op:family,id:1,...properties,...timing});
   const saved=scene.snapshot(),entry=scene.info()[family==='window'?'windows':'areas'].find(item=>item.id===1);
   for(const [field,value] of Object.entries(properties))assert.deepEqual(entry[field],value,field);
   if(family==='window'){assert.equal(entry.durationUs,1200000);assert.equal(entry.atUs,0);}
   else{assert.equal(entry.fadeUs,500000);assert.equal(entry.gapUs,250000);}
   assert.deepEqual(scene.snapshot(),saved);scene.restore(saved);
   assert.deepEqual(scene.info()[family==='window'?'windows':'areas'].find(item=>item.id===1),entry);
   scene.command({op:'define',path:`/${family}/width`,value:1234,binding:{family,id:1,field:'width'}});
   scene.command({op:'remove-value',path:`/${family}/width`});
   assert.equal(scene.info()[family==='window'?'windows':'areas'].find(item=>item.id===1).width,1234);
   assert.equal(entry.width,properties.width);
  }
 }finally{scene.close();}
});
test('widget inspection retains full series and signed geometry boundaries',async()=>{
 const scene=await NativeScene.create(wasm,42);try{
  const data=Array.from({length:128},(_,index)=>index%2?-1000000:1000000);
  scene.command({op:'widget',id:1,kind:'bars',x:-2147483648,y:2147483647,width:2147483647,height:2147483647,data});
  const saved=scene.snapshot(),widget=scene.info().widgets[0];
  assert.deepEqual(widget.data,data);assert.equal(widget.x,-2147483648);assert.equal(widget.y,2147483647);
  assert.equal(widget.width,2147483647);assert.equal(widget.height,2147483647);assert.deepEqual(scene.snapshot(),saved);
  for(const change of [{width:0},{height:2147483648},{x:-2147483649},{y:.5},{alpha:1.01},{data:Array(129).fill(0)},{data:[1000001]}]){
   assert.throws(()=>scene.command({op:'widget',id:1,...change}));assert.deepEqual(scene.snapshot(),saved);assert.deepEqual(scene.info().widgets[0],widget);
  }
  scene.command({op:'widget',id:1,data:[]});assert.deepEqual(scene.info().widgets[0].data,[]);assert.deepEqual(widget.data,data);
 }finally{scene.close();}
});
test('widget metadata exposes owned authored geometry, appearance and series',async()=>{
 const scene=await NativeScene.create(wasm,42);try{
  const properties={x:-123,y:456,width:2000000000,height:1000000000,padding:2,material:3,
   backgroundMaterial:4,alpha:.75,enabled:false,selected:true,active:true,min:-2,max:5,
   mode:3,text:'NOC 日本',value:.5,data:[1,2,4]};
  scene.command({op:'widget',id:1,kind:'donut',border:'heavy',pulseMs:250,...properties});
  const saved=scene.snapshot(),info=scene.info().widgets[0];
  for(const [key,value] of Object.entries(properties))assert.deepEqual(info[key],value,key);
  assert.equal(info.border,4);assert.equal(info.kind,9);assert.equal(info.pulseUs,250000);
  assert.deepEqual(scene.snapshot(),saved);scene.restore(saved);assert.deepEqual(scene.info().widgets[0],info);
  scene.command({op:'define',path:'/alpha',value:.6,binding:{family:'widget',id:1,field:'alpha'}});
  scene.command({op:'remove-value',path:'/alpha'});assert.equal(scene.info().widgets[0].alpha,.6);assert.equal(info.alpha,.75);
  scene.command({op:'widget',id:1,data:[9]});assert.deepEqual(info.data,[1,2,4]);assert.deepEqual(scene.info().widgets[0].data,[9]);
 }finally{scene.close();}
});
test('complete metadata preserves accepted over-capacity Unicode and snapshots',async()=>{
 const scene=await NativeScene.create(wasm,8128);try{
  assert.equal(typeof scene.infoComplete,'function');
  assert.deepEqual(scene.infoComplete(),scene.info());
  assert.deepEqual(scene.infoComplete(null),scene.info());assert.deepEqual(scene.infoComplete(16777217),scene.info());
  for(const value of [0,-1,1.5,NaN,Infinity,true,0x100000000])assert.throws(()=>scene.infoComplete(value),RangeError);
  assert.throws(()=>scene.infoComplete(1),RangeError);
  scene.command({op:'pause',paused:true});const text='🙂'.repeat(2048);
  for(let id=1;id<=24;id++)scene.command({op:'text',id,text});
  for(let id=1;id<=12;id++)scene.command({op:'window',id,title:`Retained ${id}`,text,position:[0,0,16000]});
  const largePrompt='界'.repeat(400001);scene.command({op:'draft',text:largePrompt,emitWeather:false});
  const before=scene.snapshot(),bounded=scene.info();
  const info=scene.infoComplete();assert.equal(info.prompt.text,largePrompt);assert.ok(Buffer.byteLength(JSON.stringify(info))>1048576);
  assert.ok(bounded.error==='metadata capacity exceeded'||JSON.stringify(bounded)===JSON.stringify(info));assert.equal(info.textRuns.length,24);assert.equal(info.windows.length,12);
  for(const item of [...info.textRuns,...info.windows])assert.equal(item.text,text);
  assert.deepEqual(scene.snapshot(),before);
  scene.command({op:'clear',scope:'text'});assert.equal(info.textRuns.length,24);
 }finally{scene.close();}assert.throws(()=>scene.infoComplete(),/closed/);
});

test('complete metadata accepts explicit17MiB caller limit on owned source',async()=>{
 const scene=await NativeScene.create(wasm,8128);try{
  const text='界é🙂\n'.repeat(100001);scene.command({op:'draft',text,emitWeather:false});
  const info=scene.infoComplete(17*1024*1024);assert.equal(info.prompt.text,text);assert.equal(info.prompt.caret,Array.from(text).length);
  const bytes=Buffer.byteLength(JSON.stringify(info));assert.ok(bytes>1048576);
  assert.throws(()=>scene.infoComplete(bytes-1),RangeError);
  console.log(`Actual WASM complete metadata bytes=${bytes} scalars=${Array.from(text).length}; explicit caller limit=17825792`);
 }finally{scene.close();}
});
