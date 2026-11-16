import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const fields={collisionEnabled:0,renderVisible:0,maxIndividual:100,maxTiles:100,overflow:0,
 restitution:.4,friction:.2,settleSpeed:3,reentrainWindSpeed:5,retentionMs:4000,fadeMs:1000,
 wetnessGain:.2,evaporation:.2,heatGain:.2,cooling:.2,thermalEvaporation:.2,wetnessDarkening:.2,
 heatColor:0xabcdef,heatTintStrength:.2};
for(const [field,value] of Object.entries(fields)){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle])scene.command({op:'surface',id:1});
  const publicValue=['collisionEnabled','renderVisible'].includes(field)?Boolean(value):field==='overflow'?['reject-new','merge-to-field'][value]:value;
  s.command({op:'define',path:'/control',value,binding:{family:'surface',id:1,field}});
  assert.deepEqual(s.info().valueDescriptors['/control'].binding,{family:'surface',id:1,field});
  oracle.command({op:'surface',id:1,[field]:publicValue});s.command({op:'remove-value',path:'/control'});
  assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);oracle.advanceTo(1000000);
  const finish=s.snapshot();assert.deepEqual(finish,oracle.snapshot());s.render();assert.deepEqual(s.snapshot(),finish);
  s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'surface',id:1});
 s.command({op:'define',path:'/visible',value:false,binding:{family:'surface',id:1,field:'renderVisible'}});
 for(const [field,value] of [['maxTiles',0],['friction',2],['wetness',1],['fadeMs',.0005],['collisionEnabled',.5]]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value,binding:{family:'surface',id:1,field}}));assert.deepEqual(s.snapshot(),before);
 }
 console.log(JSON.stringify({runtime:'actual WASM',publicSettingOracles:Object.keys(fields).length,booleanBinding:true,atomicRejection:true,purity:true,replay:true}));
}finally{s.close();}
