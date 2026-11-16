import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const oldBytes=readFileSync(new URL('../../evidence/firework-stages-20261011/prior-schema52.wasm',import.meta.url));
const current=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
for(const topology of [0,1,2,3]){
 const prior=await NativeScene.create(oldBytes),now=await NativeScene.create(current);
 try{
  const command={op:'emitter',id:1,effect:'weather/chrysanthemum',seed:73,count:64,runningTimeMs:0,shape:'point',position:[0,0,0],velocity:[0,0,0],extent:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,flutterAmount:0,collision:false,deposit:false,radius:4,topology,coreMs:200,lifetimeMinMs:2000,lifetimeMaxMs:2000};
  prior.command(command);now.command(command);
  for(const time of [8333,250000,750000,1750000]){prior.advanceTo(time);now.advanceTo(time);assert.deepEqual(now.particles(),prior.particles(),`topology${topology}/time${time}`);}
  const oldSnapshot=prior.snapshot(),currentSnapshot=now.snapshot();
  const prefix=currentSnapshot.slice(24,oldSnapshot.length);
  new DataView(prefix.buffer,prefix.byteOffset,prefix.byteLength).setUint32(4,0x20261052,true);
  assert.deepEqual(prefix,oldSnapshot.slice(24),'Exact legacy payload including private seeds, with only schema word normalized');
 }finally{prior.close();now.close();}
}
console.log('PASS actual prior/current WASM: four existing topology populations at four clocks, exact particle rows plus legacy payload/private seeds retained with schema normalization');
