import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} != ${b}`);
try {
 scene.command({op:'surface',id:1});const triangle={a:[-2,0,-2],b:[2,0,-2],c:[0,0,2],surfaceId:1};scene.command({op:'mesh',triangles:[triangle,triangle]});scene.command({op:'surface-water',surfaceId:1,capacity:1,evaporationUs:1000000});
 scene.command({op:'surface-water-add',triangleIndex:0,volume:.5});scene.advanceTo(500000);scene.command({op:'surface-water-add',triangleIndex:0,volume:.25});const saved=scene.snapshot();scene.advanceTo(1000000);
 const water=scene.info().surfaceWater[0],expected=.5*Math.exp(-1)+.25*Math.exp(-.5);near(water.receivedVolume,.75);near(water.retainedVolume,expected);near(water.receivedVolume,water.retainedVolume+water.evaporatedVolume+water.exportedVolume);assert.equal(water.cells[1].retainedVolume,0);
 const finish=scene.snapshot();scene.restore(saved);scene.advanceTo(1000000);assert.deepEqual(scene.snapshot(),finish);
 for(const command of [{op:'surface-water-add',triangleIndex:0,volume:0},{op:'surface-water-add',triangleIndex:2,volume:.1},{op:'surface-water-add',triangleIndex:0,volume:.1,wetness:1}]){assert.throws(()=>scene.command(command));assert.deepEqual(scene.snapshot(),finish);}
 scene.command({op:'schedule',id:1,atUs:1500000,command:{op:'surface-water-add',triangleIndex:0,volume:.1}});scene.command({op:'mesh',triangles:[]});near(scene.info().surfaceWater[0].exportedVolume,expected);
 const blocked=scene.snapshot();scene.restore(blocked);assert.throws(()=>scene.advanceTo(1500000));assert.deepEqual(scene.snapshot(),blocked);scene.restore(blocked);scene.command({op:'cancel-schedule',id:1});scene.advanceTo(1500000);
} finally {scene.close();}
console.log('PASS authored water input analytic evaporation, balance, purity, lifetime and queued recovery');
const settings=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 settings.command({op:'surface',id:1});const triangle={a:[-2,0,-2],b:[2,0,-2],c:[0,0,2],surfaceId:1};settings.command({op:'mesh',triangles:[triangle,triangle]});settings.command({op:'surface-water',surfaceId:1,capacity:1,evaporationUs:1000000});
 settings.command({op:'surface-water-add',triangleIndex:0,volume:.5});settings.command({op:'surface-water-add',triangleIndex:1,volume:.25});settings.advanceTo(500000);
 const before=settings.info().surfaceWater[0];settings.command({op:'surface-water-settings',surfaceId:1,capacity:2,evaporationUs:2000000});const after=settings.info().surfaceWater[0];
 for(const field of ['receivedVolume','retainedVolume','evaporatedVolume','exportedVolume','importedVolume','transferredVolume'])near(after[field],before[field]);near(after.cells[0].wetness,before.cells[0].wetness/2);
 const saved=settings.snapshot();settings.advanceTo(1000000);near(settings.info().surfaceWater[0].retainedVolume,.75*Math.exp(-.75));const finish=settings.snapshot();settings.restore(saved);settings.advanceTo(1000000);assert.deepEqual(settings.snapshot(),finish);
 for(const command of [{op:'surface-water-settings',surfaceId:1},{op:'surface-water-settings',surfaceId:1,capacity:0},{op:'surface-water-settings',surfaceId:1,evaporationUs:500},{op:'surface-water-settings',surfaceId:1,evaporationUs:1000.5},{op:'surface-water-settings',surfaceId:2,capacity:2}]){assert.throws(()=>settings.command(command));assert.deepEqual(settings.snapshot(),finish);}
 const retained=settings.info().surfaceWater[0].retainedVolume;settings.command({op:'surface-water-settings',surfaceId:1,evaporationUs:0});settings.advanceTo(2000000);near(settings.info().surfaceWater[0].retainedVolume,retained);
} finally {settings.close();}
const bindings=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 bindings.command({op:'surface',id:1});bindings.command({op:'mesh',triangles:[{a:[-2,0,-2],b:[2,0,-2],c:[0,0,2],surfaceId:1}]});bindings.command({op:'surface-water',surfaceId:1,capacity:1,evaporationUs:1000000});bindings.command({op:'surface-water-add',triangleIndex:0,volume:.5});
 for(const [field,value] of [['capacity',1],['evaporationUs',1000000]])bindings.command({op:'define',path:'/'+field,value,binding:{family:'surface',id:1,field:'water.'+field}});
 bindings.advanceTo(500000);bindings.command({op:'set',path:'/capacity',value:2});bindings.command({op:'set',path:'/evaporationUs',value:2000000});const start=bindings.snapshot();bindings.advanceTo(1000000);const finish=bindings.snapshot();near(bindings.info().surfaceWater[0].retainedVolume,.5*Math.exp(-.75));bindings.restore(start);
 for(const time of [600123,700234,800345,900456,1000000])bindings.advanceTo(time);assert.deepEqual(bindings.snapshot(),finish);
 for(const [path,value] of [['/capacity',0],['/evaporationUs',500],['/evaporationUs',1000.5]]){assert.throws(()=>bindings.command({op:'set',path,value}));assert.deepEqual(bindings.snapshot(),finish);}
} finally {bindings.close();}
const oldSchema=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 oldSchema.command({op:'surface',id:1});oldSchema.command({op:'surface-water',surfaceId:1,capacity:1});oldSchema.command({op:'define',path:'/capacity',value:1,binding:{family:'surface',id:1,field:'water.capacity'}});
 const before=oldSchema.snapshot(),old=before.slice(0,24+12508512),view=new DataView(old.buffer,old.byteOffset,old.byteLength);view.setUint32(12,0x20261034,true);view.setUint32(16,12508512,true);view.setUint32(28,0x20261034,true);
 let crc=0xffffffff;for(const byte of old.subarray(24)){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}view.setUint32(20,(crc^0xffffffff)>>>0,true);
 assert.throws(()=>oldSchema.restore(old));assert.deepEqual(oldSchema.snapshot(),before);
} finally {oldSchema.close();}
const sample=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 sample.command({op:'surface',id:1});const triangle={a:[-2,0,-2],b:[2,0,-2],c:[0,0,2],surfaceId:1};sample.command({op:'mesh',triangles:[triangle,triangle]});assert.equal(sample.waterSample(0),null);sample.command({op:'surface-water',surfaceId:1,capacity:1});assert.deepEqual(sample.waterSample(0),[1,0,0,0,0,0,0,1]);
 sample.command({op:'surface-water-add',triangleIndex:0,volume:.5});sample.command({op:'surface-water-transfer',fromTriangle:0,toTriangle:1,volume:.2});const before=sample.snapshot(),rows=[sample.waterSample(0),sample.waterSample(1)];
 const expected=[[1,.5,.3,.3,0,.2,0,1],[1,0,.2,.2,.2,0,0,1]];rows.forEach((row,i)=>{row.forEach((v,k)=>near(v,expected[i][k]));near(row[1]+row[4],row[2]+row[5]+row[6]);});rows[0][2]=999;near(sample.waterSample(0)[2],.3);assert.deepEqual(sample.snapshot(),before);
 const out=sample.checkpoint;new Float64Array(sample.exports.memory.buffer,out,8).fill(777);assert.equal(sample.exports.nrWaterSample(sample.context,0,out,7),-1);assert.deepEqual(Array.from(new Float64Array(sample.exports.memory.buffer,out,8)),Array(8).fill(777));assert.equal(sample.exports.nrWaterSample(sample.context,0,sample.context,8),-1);assert.deepEqual(sample.snapshot(),before);
} finally {sample.close();}
const waterDiscovery=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 const before=waterDiscovery.snapshot(),contract=waterDiscovery.info().contract;
 for(const feature of ['water-cell-inspection','water-volume-authoring','water-response-settings','water-value-bindings'])assert.ok(contract.features.includes(feature));
 assert.deepEqual(contract.queryContracts.nrWaterSample,{capacityUnit:'double',rowWords:8,alignmentBytes:8,ownedBindings:true,pure:true,absentReturn:0,presentReturn:1,invalidReturn:-1,contextOverlapAllowed:false,fields:['surfaceId','receivedVolume','retainedVolume','wetness','importedVolume','transferredVolume','evaporatedVolume','capacity']});assert.deepEqual(waterDiscovery.snapshot(),before);
} finally {waterDiscovery.close();}
