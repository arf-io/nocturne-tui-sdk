import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const waveQuotaRecovery=await NativeScene.create(wasm,42);
try{
 waveQuotaRecovery.command({op:'surface',id:1});waveQuotaRecovery.command({op:'surface-waves',surfaceId:1,waves:[[100,0,0,0,0],[1,0,0,0,0]]});
 waveQuotaRecovery.command({op:'define',path:'/amplitude',value:1,binding:{family:'surface-wave',id:1,field:'waves.1.amplitude'}});
 waveQuotaRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/amplitude',value:2}});
 waveQuotaRecovery.command({op:'surface-waves',surfaceId:1,waves:[[256,0,0,0,0],[0,0,0,0,0]]});const blocked=waveQuotaRecovery.snapshot();waveQuotaRecovery.restore(blocked);assert.deepEqual(waveQuotaRecovery.snapshot(),blocked);
 assert.throws(()=>waveQuotaRecovery.advanceTo(500000));assert.deepEqual(waveQuotaRecovery.snapshot(),blocked);
 waveQuotaRecovery.command({op:'surface-waves',surfaceId:1,waves:[[100,0,0,0,0],[0,0,0,0,0]]});const repaired=waveQuotaRecovery.snapshot();waveQuotaRecovery.advanceTo(500000);assert.equal(waveQuotaRecovery.info().values['/amplitude'],2);
 const finish=waveQuotaRecovery.snapshot();waveQuotaRecovery.restore(repaired);waveQuotaRecovery.advanceTo(500000);assert.deepEqual(waveQuotaRecovery.snapshot(),finish);
}finally{waveQuotaRecovery.close();}
const dormantTriangle={a:[0,0,0],b:[1,0,0],c:[0,1,0]},dormantArt={op:'cell-art',id:1,width:1,height:1,cells:[[65,0xffffff,0]]};
const dormantCases=[];
for(const [field,value] of Object.entries({mass:2000,radius:2,fluidDensity:800,gravity:10,drag:3,visible:0,color:0xabcdef,surfaceId:2,'position.x':2,'position.y':2,'position.z':2,'velocity.x':1,'velocity.y':1,'velocity.z':1}))dormantCases.push(['float-body',1,field,value,[{op:'surface',id:1},{op:'surface',id:2},{op:'float-body',id:1,surfaceId:1}],{op:'remove-float-body',id:1},{op:'float-body',id:1,surfaceId:1}]);
for(const [field,value] of [['x',2147483647],['y',-2147483648],['alpha',.5],['layer',1]])dormantCases.push(['cell-art',1,field,value,[dormantArt],{op:'remove-cell-art',id:1},dormantArt]);
for(const [field,value] of [['alpha',.5],['color',0xabcdef]])dormantCases.push(['triangle',1,field,value,[{op:'mesh',triangles:[dormantTriangle,dormantTriangle]}],{op:'mesh',triangles:[dormantTriangle]},{op:'mesh',triangles:[dormantTriangle,dormantTriangle]}]);
for(const member of ['amplitude','kx','kz','omega','phase'])dormantCases.push(['surface-wave',1,`waves.1.${member}`,.5,[{op:'surface',id:1},{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0],[1,0,0,0,0]]}],{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0]]},{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0],[1,0,0,0,0]]}]);
const dormantInvalidCases=[
 ['float-body','mass',1,0,[{op:'surface',id:1},{op:'float-body',id:1,surfaceId:1}],{op:'remove-float-body',id:1}],
 ['float-body','radius',64,99,[{op:'surface',id:1},{op:'float-body',id:1,surfaceId:1}],{op:'remove-float-body',id:1}],
 ['float-body','visible',0,9,[{op:'surface',id:1},{op:'float-body',id:1,surfaceId:1}],{op:'remove-float-body',id:1}],
 ['cell-art','alpha',.5,9.5,[dormantArt],{op:'remove-cell-art',id:1}],
 ['cell-art','layer',1,9,[dormantArt],{op:'remove-cell-art',id:1}],
 ['triangle','alpha',.5,9.5,[{op:'mesh',triangles:[dormantTriangle,dormantTriangle]}],{op:'mesh',triangles:[dormantTriangle]}],
 ['triangle','color',999999,-99999,[{op:'mesh',triangles:[dormantTriangle,dormantTriangle]}],{op:'mesh',triangles:[dormantTriangle]}],
 ['surface-wave','waves.1.amplitude',128,999,[{op:'surface',id:1},{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0],[1,0,0,0,0]]}],{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0]]}],
 ['surface-wave','waves.1.phase',1000000,9999999,[{op:'surface',id:1},{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0],[1,0,0,0,0]]}],{op:'surface-waves',surfaceId:1,waves:[[1,0,0,0,0]]}]
];
for(const [family,field,value,badValue,setup,remove] of dormantInvalidCases){
 const source=await NativeScene.create(wasm,42);
 try{
  for(const command of setup)source.command(command);
  source.command({op:'define',path:'/control',value,binding:{family,id:1,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value}});source.command(remove);
  const blocked=source.snapshot();source.restore(blocked);const damaged=Buffer.from(blocked),original=Buffer.from(`"value":${JSON.stringify(value)}`),replacement=Buffer.from(`"value":${JSON.stringify(badValue)}`);
  assert.equal(original.length,replacement.length);const offset=damaged.indexOf(original);assert.ok(offset>=0);replacement.copy(damaged,offset);
  let crc=0xffffffff;for(const byte of damaged.subarray(24)){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}damaged.writeUInt32LE((crc^0xffffffff)>>>0,20);
  assert.throws(()=>source.restore(damaged));assert.deepEqual(source.snapshot(),blocked);
 }finally{source.close();}
}
for(const [family,capacity,field,value] of [['float-body',64,'mass',7],['cell-art',4,'alpha',.5]]){
 const source=await NativeScene.create(wasm,42);
 try{
  source.command({op:'surface',id:1});const base=family==='float-body'?{op:'float-body',id:65535,surfaceId:1,gravity:0}:{op:'cell-art',id:65535,width:1,height:1,cells:[[65,0xffffff,0]]};
  source.command(base);source.command({op:'define',path:'/control',value,binding:{family,id:65535,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value}});source.command({op:`remove-${family}`,id:65535});
  for(let id=1;id<=capacity;id++)source.command({...base,id});
  const blocked=source.snapshot();source.restore(blocked);assert.deepEqual(source.snapshot(),blocked);
  assert.throws(()=>source.advanceTo(500000));assert.deepEqual(source.snapshot(),blocked);
  source.command({op:'cancel-schedule',id:1});source.advanceTo(500000);assert.equal(source.info().values['/control'],value);
 }finally{source.close();}
}
for(const [family,id,field,value,setup,remove,repair] of dormantCases){
 const source=await NativeScene.create(wasm,42),recovered=await NativeScene.create(wasm,99);
 try{
  for(const command of setup)source.command(command);
  source.command({op:'define',path:'/control',value,binding:{family,id,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value}});
  source.command(remove);const blocked=source.snapshot();recovered.restore(blocked);assert.deepEqual(recovered.snapshot(),blocked);
  assert.throws(()=>recovered.advanceTo(500000));assert.deepEqual(recovered.snapshot(),blocked);
  recovered.command(repair);const start=recovered.snapshot();recovered.advanceTo(500000);const finish=recovered.snapshot();assert.equal(recovered.info().values['/control'],value);
  recovered.restore(start);recovered.advanceTo(500000);assert.deepEqual(recovered.snapshot(),finish);
  source.restore(blocked);source.command({op:'cancel-schedule',id:1});source.advanceTo(500000);
 }finally{source.close();recovered.close();}
}
const dormantBooleanBody=await NativeScene.create(wasm,42);
try{
 dormantBooleanBody.command({op:'surface',id:1});dormantBooleanBody.command({op:'float-body',id:1,surfaceId:1});
 dormantBooleanBody.command({op:'define',path:'/visible',value:false,binding:{family:'float-body',id:1,field:'visible'}});
 dormantBooleanBody.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/visible',value:true}});
 dormantBooleanBody.command({op:'remove-float-body',id:1});const blocked=dormantBooleanBody.snapshot();dormantBooleanBody.restore(blocked);assert.deepEqual(dormantBooleanBody.snapshot(),blocked);
 assert.throws(()=>dormantBooleanBody.advanceTo(500000));assert.deepEqual(dormantBooleanBody.snapshot(),blocked);
 dormantBooleanBody.command({op:'float-body',id:1,surfaceId:1});dormantBooleanBody.advanceTo(500000);assert.equal(dormantBooleanBody.info().values['/visible'],true);
}finally{dormantBooleanBody.close();}
for(const [field,initial,target,other,blockedValue,repairedValue] of [['sizeMin',.5,2,'sizeMax',1,3],['farFadeDistance',0,10,'farDistance',5,200],['lifetimeMinMs',1000,3000,'lifetimeMaxMs',2000,4000]]){
 const source=await NativeScene.create(wasm,42);
 try{
  source.command({op:'emitter',id:1,count:100,runningTimeMs:2000,sizeMin:.5,sizeMax:3,nearDistance:1,farDistance:200,farFadeDistance:0,lifetimeMinMs:1000,lifetimeMaxMs:4000});
  source.command({op:'define',path:'/control',value:initial,binding:{family:'emitter',id:1,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value:target}});
  source.command({op:'define',path:'/counterpart',value:blockedValue,binding:{family:'emitter',id:1,field:other}});
  const blocked=source.snapshot();source.restore(blocked);assert.deepEqual(source.snapshot(),blocked);assert.throws(()=>source.advanceTo(500000));assert.deepEqual(source.snapshot(),blocked);
  source.command({op:'set',path:'/counterpart',value:repairedValue});const repaired=source.snapshot();source.advanceTo(500000);const finish=source.snapshot();assert.equal(source.info().values['/control'],target);
  source.restore(repaired);source.advanceTo(500000);assert.deepEqual(source.snapshot(),finish);
 }finally{source.close();}
}
for(const [field,initial,target,other,blockedValue,repairedValue] of [['deposit',false,true,'collision',false,true],['collision',true,false,'deposit',true,false]]){
 const source=await NativeScene.create(wasm,42);
 try{
  source.command({op:'emitter',id:1,count:0,collision:true,deposit:false});source.command({op:'define',path:'/control',value:initial,binding:{family:'emitter',id:1,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value:target}});
  source.command({op:'define',path:'/counterpart',value:blockedValue,binding:{family:'emitter',id:1,field:other}});
  const blocked=source.snapshot();source.restore(blocked);assert.deepEqual(source.snapshot(),blocked);assert.throws(()=>source.advanceTo(500000));assert.deepEqual(source.snapshot(),blocked);
  source.command({op:'set',path:'/counterpart',value:repairedValue});const repaired=source.snapshot();source.advanceTo(500000);const finish=source.snapshot();assert.equal(source.info().values['/control'],target);
  source.restore(repaired);source.advanceTo(500000);assert.deepEqual(source.snapshot(),finish);
 }finally{source.close();}
}
const pathOwnedRecovery=await NativeScene.create(wasm,42);
try{
 pathOwnedRecovery.command({op:'emitter',id:1,position:[0,6,0]});pathOwnedRecovery.command({op:'define',path:'/x',value:0,binding:{family:'emitter',id:1,field:'position.x'}});
 pathOwnedRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/x',value:7}});
 pathOwnedRecovery.command({op:'path-travel',id:1,target:{family:'emitter',id:1},points:[[0,6,0],[10,6,0]],speed:1});
 const blocked=pathOwnedRecovery.snapshot();pathOwnedRecovery.restore(blocked);assert.deepEqual(pathOwnedRecovery.snapshot(),blocked);assert.throws(()=>pathOwnedRecovery.advanceTo(500000));assert.deepEqual(pathOwnedRecovery.snapshot(),blocked);
 pathOwnedRecovery.command({op:'remove-path-travel',id:1});const repaired=pathOwnedRecovery.snapshot();pathOwnedRecovery.advanceTo(500000);const finish=pathOwnedRecovery.snapshot();assert.equal(pathOwnedRecovery.info().values['/x'],7);
 pathOwnedRecovery.restore(repaired);pathOwnedRecovery.advanceTo(500000);assert.deepEqual(pathOwnedRecovery.snapshot(),finish);
}finally{pathOwnedRecovery.close();}
const laterSprayRecovery=await NativeScene.create(wasm,42);
try{
 laterSprayRecovery.command({op:'emitter',id:1,count:0});laterSprayRecovery.command({op:'define',path:'/count',value:0,binding:{family:'emitter',id:1,field:'count'}});
 laterSprayRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/count',value:7}});
 laterSprayRecovery.command({op:'flow',id:1,flux:0,stages:[{name:'fall'}]});laterSprayRecovery.command({op:'flow-spray',flowId:1,emitterId:1,fraction:1,particleVolume:.1});
 const blocked=laterSprayRecovery.snapshot(),sprays=laterSprayRecovery.info().flowSprays;laterSprayRecovery.restore(blocked);assert.deepEqual(laterSprayRecovery.snapshot(),blocked);
 assert.throws(()=>laterSprayRecovery.advanceTo(500000));assert.deepEqual(laterSprayRecovery.snapshot(),blocked);
 laterSprayRecovery.command({op:'cancel-schedule',id:1});laterSprayRecovery.advanceTo(500000);assert.deepEqual(laterSprayRecovery.info().flowSprays,sprays);assert.equal(laterSprayRecovery.info().values['/count'],0);
}finally{laterSprayRecovery.close();}
const birthHistoryRecovery=await NativeScene.create(wasm,42);
try{
 birthHistoryRecovery.command({op:'emitter',id:1,count:100,runningTimeMs:2000});birthHistoryRecovery.command({op:'define',path:'/count',value:100,binding:{family:'emitter',id:1,field:'count'}});
 birthHistoryRecovery.command({op:'schedule',id:1,atUs:1000000,command:{op:'set',path:'/count',value:1}});birthHistoryRecovery.advanceTo(500000);
 const blocked=birthHistoryRecovery.snapshot(),particles=birthHistoryRecovery.particles();birthHistoryRecovery.restore(blocked);assert.deepEqual(birthHistoryRecovery.snapshot(),blocked);assert.deepEqual(birthHistoryRecovery.particles(),particles);
 assert.throws(()=>birthHistoryRecovery.advanceTo(1000000));assert.deepEqual(birthHistoryRecovery.snapshot(),blocked);
 birthHistoryRecovery.command({op:'define',path:'/cycles',value:100,binding:{family:'emitter',id:1,field:'cycles'}});const repaired=birthHistoryRecovery.snapshot();birthHistoryRecovery.advanceTo(1000000);const finish=birthHistoryRecovery.snapshot();assert.equal(birthHistoryRecovery.info().values['/count'],1);
 birthHistoryRecovery.restore(repaired);birthHistoryRecovery.advanceTo(1000000);assert.deepEqual(birthHistoryRecovery.snapshot(),finish);
}finally{birthHistoryRecovery.close();}
const emitterRecoveryFields={alpha:.6,surfaceAlpha:.6,veinContrast:.6,backTint:.6,twoSided:0,heat:2,drag:1,lift:2,flutterHz:3,flutterAmount:1,sizeMin:.8,sizeMax:2,radius:2,windScale:3,windPeriodSeconds:2,curl:.3,nearDistance:2,farDistance:100,farFadeDistance:10,material:3,sampling:2,deposit:0,collision:1,topology:1,count:120,rate:3,cycles:2,gapMs:100,runningTimeMs:3000,lifetimeMinMs:1500,lifetimeMaxMs:5000,tailMs:1000,trailMs:100,birthFadeMs:200,deathFadeMs:300,coreMs:200};
for(const [vector,value] of [['position',2],['extent',2],['velocity',2],['spread',2],['gravity',-2],['wind',2],['windVariation',2],['tumble',20],['shapeWeights',.5],['birthOrientation',20],['initialOrientation',20],['angularVelocity',20]])for(const axis of 'xyz')emitterRecoveryFields[`${vector}.${axis}`]=value;
const emitterRecoveryBase={op:'emitter',id:1,effect:'weather/autumn-drift',count:100,runningTimeMs:2000,lifetimeMinMs:1000,lifetimeMaxMs:4000,sizeMin:.5,sizeMax:3,nearDistance:1,farDistance:200,farFadeDistance:0,position:[0,6,0],extent:[2,2,2],velocity:[0,0,0],spread:[0,0,0],gravity:[0,-4,0],wind:[0,0,0],windVariation:[0,0,0],tumble:[0,0,0],birthOrientation:[0,0,0],initialOrientation:[0,0,0],angularVelocity:[0,0,0],shapeWeights:[.5,.5,.5],collision:true,deposit:false};
for(const [field,value] of Object.entries(emitterRecoveryFields)){
 const source=await NativeScene.create(wasm,42),recovered=await NativeScene.create(wasm,99);
 try{
  source.command(emitterRecoveryBase);source.command({op:'define',path:'/control',value,binding:{family:'emitter',id:1,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value}});
  source.command({op:'clear',scope:'weather'});const blocked=source.snapshot();
  recovered.restore(blocked);assert.deepEqual(recovered.snapshot(),blocked);assert.throws(()=>recovered.advanceTo(500000));assert.deepEqual(recovered.snapshot(),blocked);
  recovered.command(emitterRecoveryBase);const repaired=recovered.snapshot();recovered.advanceTo(500000);const finish=recovered.snapshot();assert.equal(recovered.info().values['/control'],value);
  recovered.restore(repaired);recovered.advanceTo(500000);assert.deepEqual(recovered.snapshot(),finish);
  source.restore(blocked);source.command({op:'cancel-schedule',id:1});source.advanceTo(500000);assert.deepEqual(source.info().emitters,[]);
 }finally{source.close();recovered.close();}
}
for(const [field,value,badValue] of [['alpha',.6,9.6],['sampling',2,9],['twoSided',0,9],['deposit',0,9],['collision',1,9],['topology',1,9],['count',120,-20]]){
 const source=await NativeScene.create(wasm,42);
 try{
  source.command(emitterRecoveryBase);source.command({op:'define',path:'/control',value,binding:{family:'emitter',id:1,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/control',value}});
  source.command({op:'clear',scope:'weather'});const blocked=source.snapshot();source.restore(blocked);
  const damaged=Buffer.from(blocked),literal=Buffer.from(`"value":${JSON.stringify(value)}`),replacement=Buffer.from(`"value":${JSON.stringify(badValue)}`);
  assert.equal(literal.length,replacement.length);const offset=damaged.indexOf(literal);assert.ok(offset>=0);replacement.copy(damaged,offset);
  let crc=0xffffffff;for(const byte of damaged.subarray(24)){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}damaged.writeUInt32LE((crc^0xffffffff)>>>0,20);
  assert.throws(()=>source.restore(damaged));assert.deepEqual(source.snapshot(),blocked);
 }finally{source.close();}
}
const sprayRegistryRecovery=await NativeScene.create(wasm,42);
try{
 sprayRegistryRecovery.command({op:'emitter',id:65535,count:1});
 sprayRegistryRecovery.command({op:'define',path:'/count',value:1,binding:{family:'emitter',id:65535,field:'count'}});
 sprayRegistryRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/count',value:7}});
 sprayRegistryRecovery.command({op:'clear',scope:'weather'});sprayRegistryRecovery.command({op:'flow',id:1,flux:0,stages:[{name:'fall'}]});
 for(let id=1;id<=16;id++){
  sprayRegistryRecovery.command({op:'emitter',id,count:0});
  sprayRegistryRecovery.command({op:'flow-spray',flowId:1,emitterId:id,fraction:.0625,particleVolume:.1});
 }
 const blocked=sprayRegistryRecovery.snapshot(),sprays=sprayRegistryRecovery.info().flowSprays;sprayRegistryRecovery.restore(blocked);
 assert.deepEqual(sprayRegistryRecovery.snapshot(),blocked);assert.deepEqual(sprayRegistryRecovery.info().flowSprays,sprays);
 assert.throws(()=>sprayRegistryRecovery.advanceTo(500000));assert.deepEqual(sprayRegistryRecovery.snapshot(),blocked);
 sprayRegistryRecovery.command({op:'cancel-schedule',id:1});sprayRegistryRecovery.advanceTo(500000);
 assert.deepEqual(sprayRegistryRecovery.info().flowSprays,sprays);assert.equal(sprayRegistryRecovery.info().values['/count'],1);
}finally{sprayRegistryRecovery.close();}
const fullEmitterRecovery=await NativeScene.create(wasm,42);
try{
 const base={op:'emitter',id:65535,count:1,runningTimeMs:0,wind:[0,0,0]};fullEmitterRecovery.command(base);
 fullEmitterRecovery.command({op:'define',path:'/wind',value:0,binding:{family:'emitter',id:65535,field:'wind.x'}});
 fullEmitterRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/wind',value:7}});
 fullEmitterRecovery.command({op:'clear',scope:'weather'});
 for(let id=1;id<=16;id++)fullEmitterRecovery.command({op:'emitter',id,count:0,birthOrientation:[10,20,30],initialOrientation:[40,50,60],angularVelocity:[1,2,3],colliders:{floor:true,surfaces:[]}});
 const blocked=fullEmitterRecovery.snapshot(),emitters=fullEmitterRecovery.info().emitters;fullEmitterRecovery.restore(blocked);
 assert.deepEqual(fullEmitterRecovery.snapshot(),blocked);assert.deepEqual(fullEmitterRecovery.info().emitters,emitters);
 assert.throws(()=>fullEmitterRecovery.advanceTo(500000));assert.deepEqual(fullEmitterRecovery.snapshot(),blocked);
 fullEmitterRecovery.command({op:'clear',scope:'weather'});fullEmitterRecovery.command(base);fullEmitterRecovery.advanceTo(500000);assert.equal(fullEmitterRecovery.info().values['/wind'],7);
}finally{fullEmitterRecovery.close();}
const acknowledgedRecovery=await NativeScene.create(wasm,42);
try{
 acknowledgedRecovery.command({op:'define',path:'/out',value:0});
 acknowledgedRecovery.command({op:'emit-intent',event:'/host/data',payload:{amount:6}});
 acknowledgedRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/out',intentId:1,expression:{intentPath:'/amount'}}});
 acknowledgedRecovery.command({op:'ack-intent',id:1});const blocked=acknowledgedRecovery.snapshot();
 acknowledgedRecovery.restore(blocked);assert.deepEqual(acknowledgedRecovery.snapshot(),blocked);
 assert.throws(()=>acknowledgedRecovery.advanceTo(500000));assert.deepEqual(acknowledgedRecovery.snapshot(),blocked);
 acknowledgedRecovery.command({op:'cancel-schedule',id:1});
 acknowledgedRecovery.command({op:'emit-intent',event:'/host/data',payload:{amount:9}});
 acknowledgedRecovery.command({op:'schedule',id:2,atUs:500000,command:{op:'set',path:'/out',intentId:2,expression:{intentPath:'/amount'}}});
 const repaired=acknowledgedRecovery.snapshot();acknowledgedRecovery.advanceTo(500000);const finish=acknowledgedRecovery.snapshot();
 assert.equal(acknowledgedRecovery.info().values['/out'],9);
 acknowledgedRecovery.restore(repaired);acknowledgedRecovery.advanceTo(500000);assert.deepEqual(acknowledgedRecovery.snapshot(),finish);
}finally{acknowledgedRecovery.close();}
for(const typed of [false,true]){
 const source=await NativeScene.create(wasm,42),recovered=await NativeScene.create(wasm,99);
 try{
  source.command({op:'define',path:'/source',value:typed?{amount:2}:2});source.command({op:'define',path:'/out',value:0});
  const expression=typed?{path:'/source',pointer:'/amount'}:{divide:[4,{path:'/source'}]};
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/out',expression}});
  source.command({op:'set',path:'/source',value:typed?{}:0});const blocked=source.snapshot();
  recovered.restore(blocked);assert.deepEqual(recovered.snapshot(),blocked);
  assert.throws(()=>recovered.advanceTo(500000));assert.deepEqual(recovered.snapshot(),blocked);
  recovered.command({op:'set',path:'/source',value:typed?{amount:7}:1});const repaired=recovered.snapshot();
  recovered.advanceTo(500000);assert.equal(recovered.info().values['/out'],typed?7:4);const finish=recovered.snapshot();
  recovered.restore(repaired);recovered.advanceTo(500000);assert.deepEqual(recovered.snapshot(),finish);
  source.restore(blocked);source.command({op:'cancel-schedule',id:1});source.advanceTo(500000);assert.equal(source.info().values['/out'],0);
 }finally{source.close();recovered.close();}
}
const dependentGuard={if:{condition:{equal:[{path:'/go'},1]},then:{equal:[{divide:[1,{path:'/den'}]},1]},else:false}};
for(const consumer of ['numeric-action','typed-guard','style-guard']){
 const source=await NativeScene.create(wasm,42),recovered=await NativeScene.create(wasm,99);
 try{
  for(const [path,value] of [['/go',0],['/out',0],['/den',1]])source.command({op:'define',path,value});
  if(consumer==='numeric-action')source.command({op:'trigger',id:1,source:'/go',target:'/out',expression:{divide:[1,{path:'/den'}]}});
  else if(consumer==='typed-guard')source.command({op:'trigger',id:1,target:'/out',whenExpression:dependentGuard,expression:7});
  else{
   source.command({op:'widget',id:1,kind:'button',text:'Guarded'});
   source.command({op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:dependentGuard,style:{alpha:.8}});
  }
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/go',value:1}});
  source.command({op:'set',path:'/den',value:0});const blocked=source.snapshot();
  recovered.restore(blocked);assert.deepEqual(recovered.snapshot(),blocked);
  assert.throws(()=>recovered.advanceTo(500000));assert.deepEqual(recovered.snapshot(),blocked);
  recovered.command({op:'set',path:'/den',value:1});const repaired=recovered.snapshot();
  recovered.advanceTo(500000);const finish=recovered.snapshot();assert.equal(recovered.info().values['/go'],1);
  assert.equal(recovered.info().values['/out'],consumer==='numeric-action'?1:consumer==='typed-guard'?7:0);
  recovered.restore(repaired);recovered.advanceTo(500000);assert.deepEqual(recovered.snapshot(),finish);
  source.restore(blocked);source.command({op:'cancel-schedule',id:1});source.advanceTo(500000);
  assert.equal(source.info().values['/go'],0);assert.equal(source.info().values['/den'],0);
 }finally{source.close();recovered.close();}
}
for(const [field,initial,target] of [['minColumns',100,120],['maxColumns',8,10],['padding',8,7]]){
 const source=await NativeScene.create(wasm,42),recovered=await NativeScene.create(wasm,99);
 try{
  const config={op:'node',id:65535,label:'Original',minColumns:field==='minColumns'?100:field==='maxColumns'?8:22,maxColumns:field==='minColumns'?200:field==='maxColumns'?8:44,padding:field==='padding'?8:0};
  source.command(config);source.command({op:'define',path:'/size',value:initial,binding:{family:'node',id:65535,field}});
  source.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/size',value:target}});
  source.command({op:'clear',scope:'graph'});const blocked=source.snapshot();
  recovered.restore(blocked);assert.deepEqual(recovered.snapshot(),blocked);
  assert.throws(()=>recovered.advanceTo(500000));assert.deepEqual(recovered.snapshot(),blocked);
  recovered.command(config);recovered.advanceTo(500000);assert.equal(recovered.info().values['/size'],target);
  source.restore(blocked);source.command({op:'cancel-schedule',id:1});source.advanceTo(500000);
  assert.deepEqual(source.info().nodes,[]);assert.equal(source.info().values['/size'],initial);
 }finally{source.close();recovered.close();}
}
const graphRecovery=await NativeScene.create(wasm);
try{
 graphRecovery.command({op:'node',id:1,label:'Original',position:[0,0,0],pinned:true});
 graphRecovery.command({op:'define',path:'/x',value:0,binding:{family:'node',id:1,field:'position.x'}});
 graphRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/x',value:40}});
 graphRecovery.command({op:'clear',scope:'graph'});const blocked=graphRecovery.snapshot();graphRecovery.restore(blocked);
 assert.deepEqual(graphRecovery.snapshot(),blocked);assert.deepEqual(graphRecovery.info().nodes,[]);
 assert.throws(()=>graphRecovery.advanceTo(500000));assert.deepEqual(graphRecovery.snapshot(),blocked);
 graphRecovery.command({op:'node',id:1,label:'Repair',position:[0,0,0],pinned:true});graphRecovery.advanceTo(500000);
 assert.equal(graphRecovery.info().values['/x'],40);assert.equal(graphRecovery.info().nodes[0].position[0],40);
 graphRecovery.restore(blocked);graphRecovery.command({op:'cancel-schedule',id:1});graphRecovery.advanceTo(500000);
 assert.deepEqual(graphRecovery.info().nodes,[]);assert.equal(graphRecovery.info().values['/x'],0);
}finally{graphRecovery.close();}
const mixedTextRecovery=await NativeScene.create(wasm);
try{
 mixedTextRecovery.command({op:'text',id:65535,text:'Target',width:20});
 mixedTextRecovery.command({op:'define',path:'/width',value:20,binding:{family:'text',id:65535,field:'width'}});
 mixedTextRecovery.command({op:'define',path:'/out',value:0});
 mixedTextRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'set',path:'/out',value:3},{op:'set',path:'/width',value:30}]}});
 mixedTextRecovery.command({op:'clear',scope:'text'});const blocked=mixedTextRecovery.snapshot();mixedTextRecovery.restore(blocked);
 assert.deepEqual(mixedTextRecovery.snapshot(),blocked);assert.deepEqual(mixedTextRecovery.info().textRuns,[]);
 assert.throws(()=>mixedTextRecovery.advanceTo(500000));assert.deepEqual(mixedTextRecovery.snapshot(),blocked);
 assert.deepEqual(mixedTextRecovery.info().values,{'/width':20,'/out':0});
 mixedTextRecovery.command({op:'text',id:65535,text:'Repair',width:20});mixedTextRecovery.advanceTo(500000);
 assert.deepEqual(mixedTextRecovery.info().values,{'/width':30,'/out':3});const final=mixedTextRecovery.snapshot();mixedTextRecovery.restore(final);assert.deepEqual(mixedTextRecovery.snapshot(),final);
}finally{mixedTextRecovery.close();}
const fullTextRecovery=await NativeScene.create(wasm);
try{
 fullTextRecovery.command({op:'text',id:1,text:'Original',width:20});
 fullTextRecovery.command({op:'define',path:'/width',value:20,binding:{family:'text',id:1,field:'width'}});
 fullTextRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/width',value:30}});
 fullTextRecovery.command({op:'clear',scope:'text'});for(let id=2;id<=25;id++)fullTextRecovery.command({op:'text',id,text:`Foreign 日本 ${id}`});
 const texts=fullTextRecovery.info().textRuns,blocked=fullTextRecovery.snapshot();fullTextRecovery.restore(blocked);
 assert.deepEqual(fullTextRecovery.snapshot(),blocked);assert.deepEqual(fullTextRecovery.info().textRuns,texts);
 assert.throws(()=>fullTextRecovery.advanceTo(500000));assert.deepEqual(fullTextRecovery.snapshot(),blocked);
 fullTextRecovery.command({op:'clear',scope:'text'});fullTextRecovery.command({op:'text',id:1,text:'Repair',width:20});fullTextRecovery.advanceTo(500000);assert.equal(fullTextRecovery.info().values['/width'],30);
 fullTextRecovery.restore(blocked);fullTextRecovery.command({op:'cancel-schedule',id:1});fullTextRecovery.advanceTo(500000);
 assert.deepEqual(fullTextRecovery.info().textRuns,texts);assert.equal(fullTextRecovery.info().values['/width'],20);
}finally{fullTextRecovery.close();}
const clearedText=await NativeScene.create(wasm);
try{
 clearedText.command({op:'text',id:1,text:'Retained target',width:20});
 clearedText.command({op:'define',path:'/width',value:20,binding:{family:'text',id:1,field:'width'}});
 clearedText.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/width',value:30}});
 clearedText.command({op:'clear',scope:'text'});const blocked=clearedText.snapshot();
 const damaged=Uint8Array.from(blocked),offset=Buffer.from(blocked).indexOf(Buffer.from('"value":30'));
 assert.ok(offset>=0);damaged.set(new TextEncoder().encode('"value":-1'),offset);
 assert.throws(()=>clearedText.restore(pendingChecksum(damaged)));assert.deepEqual(clearedText.snapshot(),blocked);clearedText.restore(blocked);
 assert.deepEqual(clearedText.snapshot(),blocked);assert.deepEqual(clearedText.info().textRuns,[]);
 assert.throws(()=>clearedText.advanceTo(500000));assert.deepEqual(clearedText.snapshot(),blocked);
 clearedText.command({op:'text',id:1,text:'Recreated target',width:20});clearedText.advanceTo(500000);assert.equal(clearedText.info().values['/width'],30);
 clearedText.restore(blocked);clearedText.command({op:'cancel-schedule',id:1});clearedText.advanceTo(500000);
 assert.deepEqual(clearedText.info().textRuns,[]);assert.equal(clearedText.info().values['/width'],20);
}finally{clearedText.close();}
const mixedDormant=await NativeScene.create(wasm);
try{
 mixedDormant.command({op:'widget',id:1,kind:'donut',value:.5});
 mixedDormant.command({op:'define',path:'/radius',value:.5,binding:{family:'widget',id:1,field:'innerRadius'}});
 mixedDormant.command({op:'define',path:'/out',value:0});
 mixedDormant.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'set',path:'/out',value:3},{op:'set',path:'/radius',value:.7}]}});
 mixedDormant.command({op:'widget',id:1,kind:'button'});const blocked=mixedDormant.snapshot();mixedDormant.restore(blocked);
 assert.deepEqual(mixedDormant.snapshot(),blocked);assert.throws(()=>mixedDormant.advanceTo(500000));
 assert.deepEqual(mixedDormant.snapshot(),blocked);assert.deepEqual(mixedDormant.info().values,{'/radius':.5,'/out':0});
 mixedDormant.command({op:'widget',id:1,kind:'donut'});mixedDormant.advanceTo(500000);assert.deepEqual(mixedDormant.info().values,{'/radius':.7,'/out':3});
}finally{mixedDormant.close();}
const dormantWrite=await NativeScene.create(wasm);
try{
 dormantWrite.command({op:'widget',id:1,kind:'donut',value:.5});
 dormantWrite.command({op:'define',path:'/radius',value:.5,binding:{family:'widget',id:1,field:'innerRadius'}});
 dormantWrite.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/radius',value:.7}});
 dormantWrite.command({op:'widget',id:1,kind:'button'});const blocked=dormantWrite.snapshot();
 const damaged=Uint8Array.from(blocked),offset=Buffer.from(blocked).indexOf(Buffer.from('"value":0.7'));
 assert.ok(offset>=0);damaged.set(new TextEncoder().encode('"value":1.7'),offset);
 assert.throws(()=>dormantWrite.restore(pendingChecksum(damaged)));assert.deepEqual(dormantWrite.snapshot(),blocked);
 dormantWrite.restore(blocked);assert.deepEqual(dormantWrite.snapshot(),blocked);assert.throws(()=>dormantWrite.advanceTo(500000));
 assert.deepEqual(dormantWrite.snapshot(),blocked);assert.equal(dormantWrite.info().values['/radius'],.5);
 dormantWrite.command({op:'widget',id:1,kind:'donut'});dormantWrite.advanceTo(500000);
 assert.equal(dormantWrite.info().values['/radius'],.7);assert.equal(dormantWrite.info().widgets[0].plot.innerRadius,.7);
 dormantWrite.restore(blocked);dormantWrite.command({op:'cancel-schedule',id:1});dormantWrite.advanceTo(500000);
 assert.equal(dormantWrite.info().values['/radius'],.5);
}finally{dormantWrite.close();}
const ownerRecovery=await NativeScene.create(wasm);
try{
 for(const [path,value] of [['/source',7],['/out',0],['/other',2],['/other-out',0]])ownerRecovery.command({op:'define',path,value});
 ownerRecovery.command({op:'widget',id:1,kind:'progress',value:.5});
 ownerRecovery.command({op:'schedule',id:10,atUs:500000,command:{op:'batch',commands:[{op:'remove-value',path:'/source'},{op:'define',path:'/source',type:'string',value:'Replacement'}]}});
 for(const [id,path,target] of [[2,'/source','/out'],[3,'/other','/other-out']]){
  ownerRecovery.command({op:'trigger',id,source:path,target,threshold:10,value:1});
  ownerRecovery.command({op:'style-rule',id,enabled:false,selector:{family:'widget'},style:{alpha:{path,inputMin:0,inputMax:10,outputMin:0,outputMax:1}}});
 }
 ownerRecovery.command({op:'schedule',id:11,atUs:1000000,command:{op:'set',path:'/out',expression:{path:'/source'}}});
 const blocked=ownerRecovery.snapshot();ownerRecovery.restore(blocked);assert.deepEqual(ownerRecovery.snapshot(),blocked);
 assert.deepEqual(ownerRecovery.info().triggers.map(item=>item.id),[2,3]);assert.deepEqual(ownerRecovery.info().styleRules.map(item=>item.id),[2,3]);assert.equal(ownerRecovery.info().pending.length,2);
 assert.throws(()=>ownerRecovery.advanceTo(500000));assert.deepEqual(ownerRecovery.snapshot(),blocked);
 ownerRecovery.command({op:'remove-trigger',id:2});ownerRecovery.command({op:'remove-style-rule',id:2});ownerRecovery.command({op:'cancel-schedule',id:11});ownerRecovery.advanceTo(500000);
 assert.equal(ownerRecovery.info().values['/source'],'Replacement');assert.deepEqual(ownerRecovery.info().triggers.map(item=>item.id),[3]);assert.deepEqual(ownerRecovery.info().styleRules.map(item=>item.id),[3]);
 const before=ownerRecovery.snapshot();assert.throws(()=>ownerRecovery.command({op:'remove-value',path:'/other'}));assert.deepEqual(ownerRecovery.snapshot(),before);
}finally{ownerRecovery.close();}
const replacementRecovery=await NativeScene.create(wasm);
try{
 replacementRecovery.command({op:'define',path:'/source',value:7});replacementRecovery.command({op:'define',path:'/out',value:0});
 replacementRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[
  {op:'remove-value',path:'/source'},{op:'define',path:'/source',type:'string',value:'Replacement'}]}});
 replacementRecovery.command({op:'trigger',id:2,source:'/source',target:'/out',threshold:10,value:1});
 const blocked=replacementRecovery.snapshot();replacementRecovery.restore(blocked);assert.deepEqual(replacementRecovery.snapshot(),blocked);
 assert.deepEqual(replacementRecovery.info().triggers.map(item=>item.id),[2]);assert.throws(()=>replacementRecovery.advanceTo(500000));
 assert.deepEqual(replacementRecovery.snapshot(),blocked);replacementRecovery.command({op:'remove-trigger',id:2});
 replacementRecovery.advanceTo(500000);assert.deepEqual(replacementRecovery.info().values,{'/source':'Replacement','/out':0});
 const final=replacementRecovery.snapshot();replacementRecovery.restore(final);assert.deepEqual(replacementRecovery.snapshot(),final);
}finally{replacementRecovery.close();}
const mixedRecovery=await NativeScene.create(wasm);
try{
 mixedRecovery.command({op:'define',path:'/source',value:7});mixedRecovery.command({op:'define',path:'/out',value:0});
 mixedRecovery.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'set',path:'/out',value:3},{op:'remove-value',path:'/source'}]}});
 mixedRecovery.command({op:'trigger',id:2,source:'/source',target:'/out',threshold:10,value:1});
 const blocked=mixedRecovery.snapshot();mixedRecovery.restore(blocked);assert.deepEqual(mixedRecovery.snapshot(),blocked);
 assert.throws(()=>mixedRecovery.advanceTo(500000));assert.deepEqual(mixedRecovery.snapshot(),blocked);
 assert.deepEqual(mixedRecovery.info().values,{'/source':7,'/out':0});
 mixedRecovery.command({op:'remove-trigger',id:2});mixedRecovery.advanceTo(500000);assert.deepEqual(mixedRecovery.info().values,{'/out':3});
}finally{mixedRecovery.close();}
for(const batch of [false,true]){
 const missingStyle=await NativeScene.create(wasm);
 try{
  missingStyle.command({op:'define',path:'/retained',value:7});
  missingStyle.command({op:'style-rule',id:1,selector:{family:'widget'},style:{alpha:.5}});
  const removal={op:'remove-style-rule',id:1};
  missingStyle.command({op:'schedule',id:1,atUs:500000,command:batch?{op:'batch',commands:[{op:'remove-value',path:'/retained'},removal]}:removal});
  missingStyle.command(removal);const saved=missingStyle.snapshot();missingStyle.restore(saved);assert.deepEqual(missingStyle.snapshot(),saved);
  assert.throws(()=>missingStyle.advanceTo(500000));assert.deepEqual(missingStyle.snapshot(),saved);
  assert.deepEqual(missingStyle.info().values,{'/retained':7});
  missingStyle.command({op:'cancel-schedule',id:1});missingStyle.advanceTo(500000);
  assert.deepEqual(missingStyle.info().pending,[]);assert.deepEqual(missingStyle.info().values,{'/retained':7});
 }finally{missingStyle.close();}
}
function pendingChecksum(bytes){let crc=0xffffffff;for(const byte of bytes.subarray(24)){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}new DataView(bytes.buffer).setUint32(20,(crc^0xffffffff)>>>0,true);return bytes;}
const shapeScene=await NativeScene.create(wasm);
try{
 shapeScene.command({op:'define',path:'/source',value:7});shapeScene.command({op:'define',path:'/out',value:0});
 shapeScene.command({op:'trigger',id:2,source:'/source',target:'/out',threshold:10,value:1});
 const template={op:'batch',commands:[{op:'remove-trigger',id:1}]};
 shapeScene.command({op:'schedule',id:1,atUs:500000,command:template});const saved=shapeScene.snapshot();
 const offset=Buffer.from(saved).indexOf(Buffer.from(JSON.stringify(template)));assert.ok(offset>=32);
 const malformed=[...[0,-1,65536,.5,true,'1',null].map(id=>({op:'remove-trigger',id})),
  {op:'remove-trigger'},{op:'remove-trigger',id:1,extra:0},{op:'remove-style-rule',id:1.5},
  {op:'remove-value',path:'relative'},{op:'remove-value',path:null},{op:'remove-value',path:'/source',extra:0},
  {op:'batch',commands:null},{op:'batch',commands:[null]},{op:'batch',commands:[{op:'batch',commands:[]}]},
  {op:'batch',commands:Array.from({length:65},()=>({op:'remove-trigger',id:1}))},
  ...[{op:'set',path:'/out',value:'bad'},{op:'unknown'},{op:'set',path:'/out',expression:{unknown:1}},
   {op:'set',path:'/out',value:3,extra:0}].map(child=>({op:'batch',commands:[{op:'remove-value',path:'/source'},child]}))];
 for(const command of malformed){
  const payload=new TextEncoder().encode(JSON.stringify(command));assert.ok(payload.length<4096);
  const damaged=Uint8Array.from(saved);damaged.fill(0,offset,offset+4096);damaged.set(payload,offset);
  new DataView(damaged.buffer).setInt32(offset-24,payload.length,true);
  assert.throws(()=>shapeScene.restore(pendingChecksum(damaged)),JSON.stringify(command));assert.deepEqual(shapeScene.snapshot(),saved);
 }
}finally{shapeScene.close();}
const blockedBatch=await NativeScene.create(wasm);
try{
 blockedBatch.command({op:'define',path:'/source',value:7});blockedBatch.command({op:'define',path:'/out',value:0});
 const trigger={op:'trigger',id:1,source:'/source',target:'/out',threshold:10,value:1};blockedBatch.command(trigger);
 blockedBatch.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'remove-trigger',id:1},{op:'remove-value',path:'/source'}]}});
 blockedBatch.command({...trigger,id:2});const blocked=blockedBatch.snapshot();blockedBatch.restore(blocked);
 assert.deepEqual(blockedBatch.snapshot(),blocked);assert.throws(()=>blockedBatch.advanceTo(500000));
 assert.deepEqual(blockedBatch.snapshot(),blocked);assert.deepEqual(blockedBatch.info().triggers.map(item=>item.id),[1,2]);
 blockedBatch.command({op:'remove-trigger',id:2});blockedBatch.advanceTo(500000);
 assert.deepEqual(blockedBatch.info().values,{'/out':0});assert.deepEqual(blockedBatch.info().triggers,[]);
}finally{blockedBatch.close();}
const blockedScene=await NativeScene.create(wasm),recoveredScene=await NativeScene.create(wasm);
try{
 blockedScene.command({op:'define',path:'/source',value:7});blockedScene.command({op:'define',path:'/out',value:0});
 blockedScene.command({op:'schedule',id:1,atUs:500000,command:{op:'remove-value',path:'/source'}});
 blockedScene.command({op:'trigger',id:1,source:'/source',target:'/out',threshold:10,value:1});
 const blocked=blockedScene.snapshot();assert.throws(()=>blockedScene.advanceTo(500000));assert.deepEqual(blockedScene.snapshot(),blocked);
 recoveredScene.restore(blocked);assert.deepEqual(recoveredScene.snapshot(),blocked);
 assert.throws(()=>recoveredScene.advanceTo(500000));assert.deepEqual(recoveredScene.snapshot(),blocked);
 recoveredScene.command({op:'remove-trigger',id:1});recoveredScene.advanceTo(500000);
 assert.deepEqual(recoveredScene.info().values,{'/out':0});
 blockedScene.restore(blocked);blockedScene.command({op:'cancel-schedule',id:1});blockedScene.advanceTo(500000);
 assert.deepEqual(blockedScene.info().values,{'/source':7,'/out':0});
}finally{blockedScene.close();recoveredScene.close();}
const component=await NativeScene.create(wasm);
try{
 const binding={family:'widget',id:1,field:'value'};
 component.command({op:'widget',id:1,kind:'progress',x:2,y:2,width:20,height:3,value:0});
 component.command({op:'define',path:'/level',value:.8,binding});
 component.command({op:'define',path:'/out',value:0});
 component.command({op:'trigger',id:1,source:'/level',target:'/out',threshold:.9,value:1});
 component.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/level',value:.6}});
 component.command({op:'schedule',id:2,atUs:1000000,command:{op:'batch',commands:[{op:'remove-trigger',id:1},{op:'remove-value',path:'/level'}]}});
 const start=component.snapshot();component.advanceTo(1000000);const finish=component.snapshot();
 assert.equal(component.info().widgets[0].value,.6);assert.deepEqual(component.info().values,{'/out':0});
 assert.deepEqual(component.info().triggers,[]);assert.deepEqual(component.info().pending,[]);
 component.restore(start);component.advanceTo(500000);component.advanceTo(1000000);assert.deepEqual(component.snapshot(),finish);
 component.command({op:'define',path:'/replacement',value:.3,binding});assert.equal(component.info().widgets[0].value,.3);
 component.command({op:'remove-value',path:'/replacement'});assert.equal(component.info().widgets[0].value,.3);
}finally{component.close();}
for(const batch of [true,false]){
 const teardown=await NativeScene.create(wasm);
 try{
  teardown.command({op:'define',path:'/source',value:7});teardown.command({op:'define',path:'/out',value:0});
  const trigger={op:'trigger',id:1,source:'/source',target:'/out',threshold:10,value:1};
  if(batch)teardown.command(trigger);
  teardown.command({op:'schedule',id:1,atUs:500000,command:batch?{op:'batch',commands:[{op:'remove-trigger',id:1},{op:'remove-value',path:'/source'}]}:{op:'remove-value',path:'/source'}});
  if(!batch){
   teardown.command(trigger);const before=teardown.snapshot();assert.throws(()=>teardown.advanceTo(500000));assert.deepEqual(teardown.snapshot(),before);
   teardown.command({op:'remove-trigger',id:1});const retained=teardown.snapshot();
   assert.throws(()=>teardown.command({op:'remove-value',path:'/source'}));assert.deepEqual(teardown.snapshot(),retained);
  }
  const start=teardown.snapshot();teardown.restore(start);teardown.advanceTo(500000);
  assert.deepEqual(teardown.info().values,{'/out':0});const finish=teardown.snapshot();
  teardown.restore(start);teardown.advanceTo(500000);assert.deepEqual(teardown.snapshot(),finish);
 }finally{teardown.close();}
}
for(const writeTime of [500000,1000000]){
 const ordered=await NativeScene.create(wasm);
 try{
  ordered.command({op:'define',path:'/owned',value:7});
  ordered.command({op:'schedule',id:1,atUs:writeTime,command:{op:'set',path:'/owned',value:9}});
  ordered.command({op:'schedule',id:2,atUs:1000000,command:{op:'remove-value',path:'/owned'}});
  const start=ordered.snapshot();ordered.restore(start);assert.deepEqual(ordered.snapshot(),start);
  ordered.advanceTo(1000000);assert.ok(!Object.hasOwn(ordered.info().values,'/owned'));const finish=ordered.snapshot();
  ordered.restore(start);ordered.advanceTo(writeTime);ordered.advanceTo(1000000);assert.deepEqual(ordered.snapshot(),finish);
 }finally{ordered.close();}
}
const removal=await NativeScene.create(wasm);
try{
 removal.command({op:'define',path:'/owned',value:7});
 removal.command({op:'schedule',id:1,atUs:500000,command:{op:'remove-value',path:'/owned'}});
 const start=removal.snapshot();assert.throws(()=>removal.command({op:'remove-value',path:'/owned'}));
 assert.deepEqual(removal.snapshot(),start);removal.restore(start);assert.deepEqual(removal.snapshot(),start);
 removal.advanceTo(500000);assert.ok(!Object.hasOwn(removal.info().values,'/owned'));const finish=removal.snapshot();
 removal.restore(start);removal.advanceTo(500000);assert.deepEqual(removal.snapshot(),finish);
 removal.command({op:'define',path:'/owned',value:9});removal.command({op:'remove-value',path:'/owned'});
}finally{removal.close();}
for(const [expression,expected] of [[{literal:{path:'/source'}},{path:'/source'}],
 [{object:{path:'/source'}},{path:'/source'}],[{array:['path','/source']},['path','/source']]]){
 const s=await NativeScene.create(wasm);
 try{
  s.command({op:'define',path:'/source',value:7});s.command({op:'define',path:'/out',type:'json',value:null});
  s.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/out',expression}});
  s.command({op:'remove-value',path:'/source'});s.advanceTo(500000);assert.deepEqual(s.info().values['/out'],expected);
 }finally{s.close();}
}
for(const expression of [{object:{path:{path:'/source'}}},{if:{condition:true,then:{literal:{}},else:{path:'/source'}}}]){
 const s=await NativeScene.create(wasm);
 try{
  s.command({op:'define',path:'/source',type:'json',value:{id:'owned'}});s.command({op:'define',path:'/out',type:'json',value:null});
  s.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/out',expression}});
  const before=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/source'}));assert.deepEqual(s.snapshot(),before);
  s.command({op:'cancel-schedule',id:1});s.command({op:'remove-value',path:'/source'});
 }finally{s.close();}
}
console.log(JSON.stringify({runtime:'actual WASM',literalDataDoesNotOwn:true,constructedKeysDoNotOwn:true,actualReferencesProtected:true,unselectedBranchesProtected:true,cancellationReleases:true}));
