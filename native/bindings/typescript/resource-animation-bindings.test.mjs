import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const emitter={op:'emitter',id:1,effect:'weather/chrysanthemum',seed:73,count:8,runningTimeMs:0,lifetimeMinMs:2000,lifetimeMaxMs:2000};
const arc={op:'electrical-arc',id:7,points:[{position:[0,0,0],parent:-1},{position:[3,0,0],parent:0}],speed:10,holdMs:200,fadeMs:300,jitter:0,flicker:0};
let comparisons=0;
for(const [family,ident,fields] of [['emitter',1,{glitterHz:30,glitterDepth:.2,coreAlpha:.3,residualMs:350.125,residualAlpha:.4}],['electrical-arc',7,{speed:20,jitter:.5,alpha:.4,flicker:.2,delayMs:50.125,holdMs:150.125,fadeMs:250.125,repeatMs:3000.125}]]){
 for(const [field,value] of Object.entries(fields)){
  const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
  try{
   s.command(family==='emitter'?emitter:arc);oracle.command(family==='emitter'?emitter:{...arc,[field]:value});
   if(family==='emitter'){s.advanceTo(250000);oracle.advanceTo(250000);oracle.command({op:'burst-style',id:1,[field]:value});}
   const particles=s.particles();s.command({op:'define',path:'/control',value,binding:{family,id:ident,field}});
   assert.equal(s.infoComplete().valueDescriptors['/control'].binding.family,family);
   assert.deepEqual(s.particles(),particles);s.command({op:'remove-value',path:'/control'});
   assert.deepEqual(s.snapshot(),oracle.snapshot());
   for(const clock of [500000,1000000,2000000]){s.advanceTo(clock);oracle.advanceTo(clock);assert.deepEqual(s.snapshot(),oracle.snapshot());assert.deepEqual(s.render(),oracle.render());comparisons++;}
   const saved=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value:-1,binding:{family,id:ident,field}}));assert.deepEqual(s.snapshot(),saved);
  }finally{s.close();oracle.close();}
 }
}
console.log(`PASS actual WASM resource animation bindings: 13 fields, ${comparisons} timed comparisons, atomic rejection`);
const styled=await NativeScene.create(wasm);
try{
 styled.command(arc);styled.command({op:'state-register',id:21,path:'/alarms/circuit',role:'alarm',target:{family:'electrical-arc',id:7}});
 styled.advanceTo(200000);const authored=styled.infoComplete().electricalArcs,frame=styled.render();
 styled.command({op:'style-rule',id:1,selector:{family:'electrical-arc',role:'alarm'},style:{alpha:0}});
 const saved=styled.snapshot(),entry=styled.infoComplete().registeredStates.find(q=>q.id===21);
 assert.equal(entry.authored.alpha,.8);assert.equal(entry.effective.alpha,0);
 assert.notDeepEqual(styled.render(),frame);assert.deepEqual(styled.snapshot(),saved);
 assert.deepEqual(styled.infoComplete().electricalArcs,authored);
 styled.command({op:'remove-style-rule',id:1});assert.deepEqual(styled.render(),frame);
 styled.command({op:'remove-electrical-arc',id:7});assert.equal(styled.infoComplete().registeredStates[0].exists,false);
 styled.command(arc);assert.equal(styled.infoComplete().registeredStates[0].exists,true);
 console.log('PASS actual WASM reversible circuit selectors and retained identity');
}finally{styled.close();}
const discovered=await NativeScene.create(wasm);
try{
 const saved=discovered.snapshot(),contract=discovered.infoComplete().contract;
 assert.equal(contract.snapshotSchema,new DataView(saved.buffer,saved.byteOffset,saved.byteLength).getUint32(12,true));assert.equal(contract.snapshotCapacityBytes,saved.length);
 assert.ok(contract.bindingFamilies.includes('electrical-arc'));
 for(const feature of ['resource-animation-bindings','electrical-selectors'])assert.ok(contract.features.includes(feature));
 contract.features.length=0;contract.bindingFamilies.length=0;
 assert.ok(discovered.infoComplete().contract.bindingFamilies.includes('electrical-arc'));
 assert.deepEqual(discovered.snapshot(),saved);
 console.log('PASS actual WASM resource contract discovery ownership and purity');
}finally{discovered.close();}
