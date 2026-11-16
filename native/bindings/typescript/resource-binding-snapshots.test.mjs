import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';

const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
function crc32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
function checksum(bytes){new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).setUint32(20,crc32(bytes.subarray(24)),true);return bytes;}
const scene=await NativeScene.create(wasm);
try{
 scene.command({op:'define',path:'/shape-fixture',value:1});
 const good=scene.snapshot(),base=Buffer.from(good).indexOf(Buffer.from('/shape-fixture\0'))-16;
 assert.ok(base>=24,'fixture must identify an authored value record');
 const malformed=[
  [1,9999,'alpha'],[1,0,'channels.q'],[1,0,'alpha.missing'],[1,0,'channels.r.rate.extra'],
  [2,0,'alpha'],[2,1,'missing'],[2,1,'position.w'],[2,1,'position.x.extra'],
  [3,1,'data.00'],[3,1,'data.128'],[15,1,'missing'],[16,0,'friction'],
  [3,0,'alpha'],[3,1,'missing'],[4,0,'missing'],[5,0,'alpha'],[5,1,'missing'],
  [6,0,'x'],[6,1,'missing'],[7,0,'alpha'],[7,1,'missing'],[8,1,'alpha'],[8,0,'missing'],
  [9,0,'active'],[9,1,'unknown'],[10,0,'color'],[10,1,'missing'],[11,0,'cursor'],[11,1,'missing'],
  [12,1,'alpha'],[12,0,'missing'],[13,1,'background'],[13,0,'missing'],[14,0,'x'],[14,1,'missing'],
  [17,1,'waves.00.phase'],[17,1,'waves.32.phase'],[18,0,'mass'],
  [19,0,'decay'],[20,1,'alpha'],[21,0,'sampling'],[21,65535,'alpha'],[22,0,'alpha'],
  [23,1,'reducedMotion'],[23,0,'unknown'],[24,0,'reducedMotion'],
 ];
 const frame=scene.render().bytes;
 for(const [family,id,field] of malformed){
  const damaged=Uint8Array.from(good),view=new DataView(damaged.buffer);
  view.setInt32(base+8,family,true);view.setInt32(base+12,id,true);
  damaged.fill(0,base+144,base+176);damaged.set(new TextEncoder().encode(field),base+144);
  assert.throws(()=>scene.restore(checksum(damaged)),`${family}:${id}:${field}`);
  assert.deepEqual(scene.snapshot(),good,'failed import must preserve authored state');
  assert.deepEqual(scene.render().bytes,frame,'failed import must preserve the rendered scene');
 }
 scene.command({op:'reset'});
 scene.command({op:'define',path:'/legacy-shape',value:1});
 const legacySource=scene.snapshot(),legacyBase=Buffer.from(legacySource).indexOf(Buffer.from('/legacy-shape\0'))-16;
 assert.ok(legacyBase>=24);
 const legacyCases=[
  [1,7,'alpha','material'],[2,12345,'windX','emitter'],[3,12345,'alpha','widget'],[4,0,'yaw','camera'],
  [5,12345,'alpha','window'],[6,12345,'material','text'],[7,12345,'alpha','area'],[8,0,'alpha','floor'],[9,12345,'active','state'],
 ];
 function legacyBinding(family,id,field){
  const source=Uint8Array.from(legacySource.subarray(0,24+5266400)),view=new DataView(source.buffer);
  view.setInt32(legacyBase+8,family,true);view.setInt32(legacyBase+12,id,true);
  source.fill(0,legacyBase+144,legacyBase+176);source.set(new TextEncoder().encode(field),legacyBase+144);
  view.setUint32(28,0x20261031,true);view.setUint32(12,0x20261031,true);view.setUint32(16,5266400,true);
  return checksum(source);
 }
 for(const [family,id,field,name] of legacyCases){
  const source=legacyBinding(family,id,field),original=Uint8Array.from(source);scene.restore(source);
  assert.deepEqual(source,original);assert.deepEqual(scene.info().valueDescriptors['/legacy-shape'].binding,{family:name,id,field});
  const promoted=scene.snapshot();scene.restore(promoted);assert.deepEqual(scene.snapshot(),promoted);
 }
 const promoted=scene.snapshot();
 for(const [family,id,field] of [[1,0,'alpha.rate'],[2,1,'gravity.y'],[3,1,'border'],[5,1,'group'],[6,1,'width'],[7,1,'layout'],[8,0,'height']]){
  assert.throws(()=>scene.restore(legacyBinding(family,id,field)));assert.deepEqual(scene.snapshot(),promoted);
 }
 scene.command({op:'reset'});
 scene.command({op:'define',path:'/dormant',value:1});
 const empty=scene.snapshot(),emptyBase=Buffer.from(empty).indexOf(Buffer.from('/dormant\0'))-16;
 assert.ok(emptyBase>=24);
 for(const [family,id,field] of [[1,7,'alpha'],[1,7,'channels.r.rate'],[2,12345,'wind.y'],[2,12345,'birthOrientation.z']]){
  const source=Uint8Array.from(empty),view=new DataView(source.buffer);
  view.setInt32(emptyBase+8,family,true);view.setInt32(emptyBase+12,id,true);
  source.fill(0,emptyBase+144,emptyBase+176);source.set(new TextEncoder().encode(field),emptyBase+144);
  scene.restore(checksum(source));assert.deepEqual(scene.snapshot(),source);
  assert.throws(()=>scene.command({op:'set',path:'/dormant',value:2}));assert.deepEqual(scene.snapshot(),source);
 }
 scene.command({op:'reset'});
 scene.command({op:'define',path:'/flag',value:0,binding:{family:'accessibility',field:'reducedMotion'}});
 const flag=scene.snapshot(),flagBase=Buffer.from(flag).indexOf(Buffer.from('/flag\0'))-16;
 assert.ok(flagBase>=24);
 for(const value of [-1,.5,2]){
  const damaged=Uint8Array.from(flag);new DataView(damaged.buffer).setFloat64(flagBase+176,value,true);
  assert.throws(()=>scene.restore(checksum(damaged)));assert.deepEqual(scene.snapshot(),flag);
 }
 scene.command({op:'reset'});
 scene.command({op:'surface',id:1});
 scene.command({op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0]]});
 scene.command({op:'define',path:'/wave',value:1,binding:{family:'surface-wave',id:1,field:'waves.0.amplitude'}});
 scene.command({op:'surface-waves',surfaceId:1,waves:[]});
 const dormant=scene.snapshot();scene.restore(dormant);assert.deepEqual(scene.snapshot(),dormant);
 assert.deepEqual(scene.info().valueDescriptors['/wave'].binding,{family:'surface-wave',id:1,field:'waves.0.amplitude'});
 assert.throws(()=>scene.command({op:'set',path:'/wave',value:2}));assert.deepEqual(scene.snapshot(),dormant);
 scene.command({op:'bind',path:'/wave',binding:null});scene.command({op:'set',path:'/wave',value:2});
 assert.equal(scene.info().values['/wave'],2);
 scene.command({op:'reset'});
 scene.command({op:'flow',id:1,flux:2,stages:[{name:'fall'}]});
 scene.command({op:'define',path:'/flux',value:2,binding:{family:'flow',id:1,field:'flux'}});
 const current=scene.snapshot(),old=Uint8Array.from(current.subarray(0,24+5266400)),view=new DataView(old.buffer);
 view.setUint32(28,0x20261031,true);view.setUint32(12,0x20261031,true);view.setUint32(16,5266400,true);
 assert.throws(()=>scene.restore(checksum(old)),'schema 31 cannot introduce a later binding family');
 assert.deepEqual(scene.snapshot(),current);
 for(const [field,accepted] of [['alpha',true],['alpha.rate',false]]){
  scene.command({op:'reset'});
  scene.command({op:'schedule',id:1,atUs:500000,command:{op:'define',path:'/alpha',value:.5,binding:{family:'material',id:0,field}}});
  const scheduled=scene.snapshot(),legacy=Uint8Array.from(scheduled.subarray(0,24+5266400)),header=new DataView(legacy.buffer);
  header.setUint32(28,0x20261031,true);header.setUint32(12,0x20261031,true);header.setUint32(16,5266400,true);checksum(legacy);
  if(!accepted){assert.throws(()=>scene.restore(legacy));assert.deepEqual(scene.snapshot(),scheduled);continue;}
  const input=Uint8Array.from(legacy);scene.restore(legacy);assert.deepEqual(legacy,input);const promotedSchedule=scene.snapshot();
  scene.advanceTo(500000);assert.equal(scene.info().values['/alpha'],.5);
  assert.deepEqual(scene.info().valueDescriptors['/alpha'].binding,{family:'material',id:0,field:'alpha'});
  const finish=scene.snapshot(),painted=scene.render().bytes;scene.restore(promotedSchedule);scene.advanceTo(500000);
  assert.deepEqual(scene.snapshot(),finish);assert.deepEqual(scene.render().bytes,painted);
 }
 console.log(JSON.stringify({runtime:'actual WASM',malformedBindingOracles:malformed.length,failedImportAtomic:true,dormantOwnership:true,explicitDetach:true,schema31RejectsFutureBindings:true}));
}finally{scene.close();}
