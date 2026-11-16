import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
s.command({op:'flow',id:1,flux:2,stages:[{name:'channel',delayUs:500000},{name:'basin',tailUs:500000}]});
s.advanceTo(1000000);
const f=s.info().flows[0];assert.equal(f.flux,2);assert.equal(f.stages[0].flux,2);assert.ok(Math.abs(f.outletFlux-2*(1-Math.exp(-1)))<1e-5);assert.ok(Math.abs(f.deliveredVolume-Math.exp(-1))<1e-5);assert.ok(Math.abs(f.injectedVolume-f.deliveredVolume-f.storedVolume)<1e-5);
const saved=s.snapshot();s.render();assert.deepEqual(s.snapshot(),saved);
s.command({op:'flow-rate',id:1,flux:0});s.advanceTo(2000000);const expected=s.snapshot();s.restore(saved);s.command({op:'flow-rate',id:1,flux:0});s.advanceTo(1234567);s.advanceTo(2000000);assert.deepEqual(s.snapshot(),expected);
s.command({op:'surface',id:1});s.command({op:'mesh',triangles:[{a:[-4,-2,0],b:[4,-2,0],c:[0,4,0],surfaceId:1,color:0xffffff,alpha:1}]});
s.command({op:'flow-surface',surfaceId:1,flowId:1,stage:'channel',referenceFlux:2});const bound=s.snapshot();const dry=s.render();assert.deepEqual(s.snapshot(),bound);s.command({op:'remove-flow-surface',surfaceId:1});assert.notDeepEqual(s.render(),dry);s.restore(bound);s.command({op:'mesh',triangles:[]});assert.deepEqual(s.render(),dry);
s.close();console.log('PASS native WASM retained flow transport');
const wet=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url))),dryScene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
for(const scene of [wet,dryScene]){
 scene.command({op:'surface',id:1});scene.command({op:'mesh',triangles:[{a:[-4,-2,0],b:[4,-2,0],c:[0,4,0],surfaceId:1,color:0xffffff,alpha:1}]});
 scene.command({op:'flow',id:1,flux:2,stages:[{name:'basin'}]});
}
wet.command({op:'flow-sink',flowId:1,surfaceId:1,fraction:.5,capacity:1,evaporationUs:500000});wet.advanceTo(1000000);dryScene.advanceTo(1000000);
const sink=wet.info().flowSinks[0];assert.equal(sink.receivedVolume,1);assert.ok(Math.abs(sink.retainedVolume-.5*(1-Math.exp(-2)))<1e-5);assert.ok(Math.abs(sink.receivedVolume-sink.retainedVolume-sink.evaporatedVolume)<1e-5);
const held=wet.snapshot();assert.notDeepEqual(wet.render(),dryScene.render());assert.deepEqual(wet.snapshot(),held);wet.close();dryScene.close();console.log('PASS native WASM accounted basin wetness');
const spray=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
spray.command({op:'emitter',id:1,effect:'weather/rain-threads',count:0,lifetimeMinMs:10000,lifetimeMaxMs:10000});spray.command({op:'flow',id:1,flux:2,stages:[{name:'spray',delayUs:250000}]});spray.command({op:'flow-spray',flowId:1,emitterId:1,fraction:.5,particleVolume:.1});spray.advanceTo(1000000);assert.equal(spray.info().particles.born,7);assert.equal(spray.info().flowSprays[0].pendingVolume,.05);const checkpoint=spray.snapshot();spray.render();assert.deepEqual(spray.snapshot(),checkpoint);spray.command({op:'flow-rate',id:1,flux:0});spray.advanceTo(1500000);const drained=spray.snapshot();spray.restore(checkpoint);spray.command({op:'flow-rate',id:1,flux:0});spray.advanceTo(1500000);assert.deepEqual(spray.snapshot(),drained);spray.close();console.log('PASS native WASM allocated flow spray');
const short=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
short.command({op:'emitter',id:1,effect:'weather/rain-threads',count:0,collision:false,lifetimeMinMs:100,lifetimeMaxMs:100});short.command({op:'flow',id:1,flux:2,stages:[{name:'spray'}]});short.command({op:'flow-spray',flowId:1,emitterId:1,fraction:.5,particleVolume:.1});short.advanceTo(1000000);const life=short.info().flowSprays[0];assert.ok(life.expiredVolume>0);assert.ok(Math.abs(life.emittedVolume-life.liveVolume-life.expiredVolume-life.impactedVolume-life.exportedVolume-life.legacyUnresolvedVolume)<1e-6);const lifeSaved=short.snapshot();short.render();assert.deepEqual(lifeSaved,short.snapshot());short.close();console.log('PASS native WASM spray particle volume ownership');
