import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm);
try {
 s.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});assert.equal(s.thermalSample(0),null);
 s.command({op:'surface-thermal',triangleIndex:0,temperature:293,capacity:2,power:4});s.advanceTo(500000);
 const saved=s.snapshot(),row=s.thermalSample(0),expected=[294,588,586,2,0,0,0,2,4,293];
 expected.forEach((v,i)=>assert.ok(Math.abs(row[i]-v)<1e-6));row[0]=999;assert.equal(s.thermalSample(0)[0],294);assert.deepEqual(s.snapshot(),saved);
 assert.throws(()=>s.thermalSample(1));assert.throws(()=>s.thermalSample(-1));assert.throws(()=>s.thermalSample(true));
 const out=s.checkpoint;new Float64Array(s.exports.memory.buffer,out,10).fill(777);
 assert.equal(s.exports.nrThermalSample(s.context,0,out,9),-1);assert.deepEqual(Array.from(new Float64Array(s.exports.memory.buffer,out,10)),Array(10).fill(777));
 assert.equal(s.exports.nrThermalSample(s.context,0,s.context,10),-1);assert.deepEqual(s.snapshot(),saved);
 s.command({op:'mesh',triangles:[]});assert.throws(()=>s.thermalSample(0));
} finally {s.close();}
console.log('PASS thermal sample ownership, analytic energy, raw output guards and lifetime');
const settings=await NativeScene.create(wasm);
try {
 settings.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});
 settings.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2,power:4});settings.advanceTo(500000);
 const before=settings.thermalSample(0);settings.command({op:'surface-thermal-settings',triangleIndex:0,ambientTemperature:300,conductance:4,power:0});
 assert.deepEqual(settings.thermalSample(0).slice(0,8),before.slice(0,8));const saved=settings.snapshot();settings.advanceTo(1000000);
 assert.ok(Math.abs(settings.thermalSample(0)[0]-(300+101*Math.exp(-1)))<1e-5);const finish=settings.snapshot();settings.restore(saved);
 for(const t of [600000,700000,800000,900000,1000000])settings.advanceTo(t);assert.deepEqual(settings.snapshot(),finish);
 for(const command of [{op:'surface-thermal-settings',triangleIndex:0},{op:'surface-thermal-settings',triangleIndex:0,conductance:-1},{op:'surface-thermal-settings',triangleIndex:0,power:0,temperature:500}]){assert.throws(()=>settings.command(command));assert.deepEqual(settings.snapshot(),finish);}
} finally {settings.close();}
const queued=await NativeScene.create(wasm);
try {
 queued.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});queued.command({op:'surface-thermal',triangleIndex:0,temperature:293,capacity:2});
 queued.command({op:'schedule',id:1,atUs:500000,command:{op:'surface-thermal-settings',triangleIndex:0,power:4}});queued.command({op:'mesh',triangles:[]});
 const blocked=queued.snapshot();queued.restore(blocked);assert.throws(()=>queued.advanceTo(500000));assert.deepEqual(queued.snapshot(),blocked);
 queued.restore(blocked);queued.command({op:'cancel-schedule',id:1});queued.advanceTo(500000);
} finally {queued.close();}
const bound=await NativeScene.create(wasm),direct=await NativeScene.create(wasm);
try {
 for(const scene of [bound,direct]){scene.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});scene.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2,ambientTemperature:300,conductance:2,power:4});}
 for(const [field,value] of [['power',4],['ambientTemperature',300],['conductance',2]])bound.command({op:'define',path:'/'+field,value,binding:{family:'triangle',id:0,field:'thermal.'+field}});
 for(const scene of [bound,direct])scene.advanceTo(500000);
 for(const [field,value] of [['power',0],['ambientTemperature',250],['conductance',4]]){bound.command({op:'set',path:'/'+field,value});direct.command({op:'surface-thermal-settings',triangleIndex:0,[field]:value});}
 for(const scene of [bound,direct])scene.advanceTo(1000000);
 const a=bound.thermalSample(0),b=direct.thermalSample(0);a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<1e-6));const before=bound.snapshot();
 assert.throws(()=>bound.command({op:'set',path:'/conductance',value:-1}));assert.deepEqual(bound.snapshot(),before);
 bound.command({op:'schedule',id:1,atUs:1500000,command:{op:'set',path:'/power',value:8}});bound.command({op:'mesh',triangles:[]});const blocked=bound.snapshot();bound.restore(blocked);
 assert.throws(()=>bound.advanceTo(1500000));assert.deepEqual(bound.snapshot(),blocked);bound.restore(blocked);bound.command({op:'cancel-schedule',id:1});bound.command({op:'bind',path:'/power',binding:null});bound.command({op:'set',path:'/power',value:8});bound.advanceTo(1500000);
} finally {bound.close();direct.close();}
const migration=await NativeScene.create(wasm);
try {
 migration.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});migration.command({op:'surface-thermal',triangleIndex:0,temperature:293,capacity:2});
 migration.command({op:'define',path:'/power',value:4,binding:{family:'triangle',id:0,field:'thermal.power'}});const before=migration.snapshot(),old=before.slice(0,24+12508512),view=new DataView(old.buffer,old.byteOffset,old.byteLength);
 view.setUint32(12,0x20261034,true);view.setUint32(16,12508512,true);view.setUint32(28,0x20261034,true);let crc=0xffffffff;
 for(const byte of old.subarray(24)){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}view.setUint32(20,(crc^0xffffffff)>>>0,true);
 assert.throws(()=>migration.restore(old));assert.deepEqual(migration.snapshot(),before);
} finally {migration.close();}
const discovery=await NativeScene.create(wasm);
try {
 const before=discovery.snapshot(),contract=discovery.info().contract;
 for(const feature of ['thermal-cell-inspection','thermal-response-settings','thermal-value-bindings','shortcut-negotiation'])assert.ok(contract.features.includes(feature));
 assert.deepEqual(contract.queryContracts.nrThermalSample,{capacityUnit:'double',rowWords:10,alignmentBytes:8,ownedBindings:true,pure:true,absentReturn:0,presentReturn:1,invalidReturn:-1,contextOverlapAllowed:false,fields:['temperature','energy','initialEnergy','appliedEnergy','environmentEnergy','importedEnergy','transferredEnergy','capacity','power','ambientTemperature']});
 assert.deepEqual(discovery.snapshot(),before);
} finally {discovery.close();}
const network=await NativeScene.create(wasm);
try {
 const triangle={a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]};network.command({op:'mesh',triangles:[triangle,triangle]});
 network.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2,power:4});network.command({op:'surface-thermal',triangleIndex:1,temperature:300,capacity:4});network.command({op:'surface-thermal-link',id:1,fromTriangle:0,toTriangle:1,conductance:3});
 const start=network.snapshot();let expected=[400,300],previous=0;
 for(let step=1;step<=120;step++){
  const now=Math.floor(step*1000000/120),elapsed=(now-previous)/1e6;previous=now;
  const a=expected[0]+(step<=60?4:0)*elapsed/2,b=expected[1],k=3/120,d=8+6*k;
  expected=[(2*a*(4+k)+4*k*b)/d,(4*b*(2+k)+2*k*a)/d];
  if(step===60){network.advanceTo(500000);const before=network.thermalSample(0);network.command({op:'surface-thermal-settings',triangleIndex:0,power:0});assert.deepEqual(network.thermalSample(0).slice(0,8),before.slice(0,8));}
 }
 network.advanceTo(1000000);const rows=[network.thermalSample(0),network.thermalSample(1)];rows.forEach((r,i)=>{assert.ok(Math.abs(r[0]-expected[i])<1e-5);assert.ok(Math.abs(r[1]-(r[2]+r[3]+r[4]+r[5]-r[6]))<1e-5);});assert.ok(Math.abs(rows[0][1]+rows[1][1]-2002)<1e-5);
 const finish=network.snapshot();network.restore(start);for(const time of [123456,250000,500000])network.advanceTo(time);network.command({op:'surface-thermal-settings',triangleIndex:0,power:0});for(const time of [666666,750000,1000000])network.advanceTo(time);assert.deepEqual(network.snapshot(),finish);
} finally {network.close();}
const partitioned=await NativeScene.create(wasm);
try {
 partitioned.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});partitioned.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2,ambientTemperature:300,conductance:2,power:4});
 for(const [field,value] of [['power',4],['ambientTemperature',300],['conductance',2]])partitioned.command({op:'define',path:'/'+field,value,binding:{family:'triangle',id:0,field:'thermal.'+field}});
 const start=partitioned.snapshot();partitioned.advanceTo(1000000);const finish=partitioned.snapshot();partitioned.restore(start);
 for(const time of [123456,250001,500123,750456,1000000])partitioned.advanceTo(time);assert.deepEqual(partitioned.snapshot(),finish);
} finally {partitioned.close();}
