import assert from 'node:assert/strict';
import {RestorationModel} from '../../../bindings/continuity/restoration-model.js';
import {ScenicOriginalClock,SCENIC_PRESETS} from './scenic_original.mjs';
const mappings=[['pearl-cascade','waterfall'],['copper-causeway','tarmac'],['tidal-glass','ocean'],['silt','dunes']];
for(const [name,id] of mappings){
 const model=new RestorationModel();model.setScene(id);const clock=new ScenicOriginalClock(name);
 for(const [at,patch] of [[0,{}],[425,{}],[1700,{landscapeSpeed:37,waterFlow:1.6}],[1901,{}],[2301,{waterFlow:0}],[3000,{}],[3501,{waterFlow:.35,landscapeSpeed:0}],[4600,{}],[5000,{landscapeSpeed:160,waterFlow:2}],[9999,{}]]){
  model.setTime(at);model.configureBH(patch);clock.configure(at,patch);
  const x=clock.sample(at);assert.equal(x.timeMs,name==='pearl-cascade'?Math.max(0,Math.round(model.waterfallPhase.at(model.motionMs)*1000)):model.motionMs);assert.equal(x.controls.travel,model.surfaceDistance.at(model.motionMs)%12000);assert.equal(x.controls.flow,name==='pearl-cascade'?(model.bh.waterFlow===0?0:1):1);
 }
 const copy=ScenicOriginalClock.fromSnapshot(clock.snapshot());assert.deepEqual(copy.sample(10000),clock.sample(10000));
 for(const patch of [{waterFlow:-1},{waterFlow:2.01},{landscapeSpeed:-1},{landscapeSpeed:161},{unknown:1},{waterFlow:NaN}]){const before=clock.snapshot();assert.throws(()=>clock.configure(10000,patch));assert.deepEqual(clock.snapshot(),before);}
}
assert.equal(SCENIC_PRESETS.moonlight.waveHeight,1.8);assert.equal(SCENIC_PRESETS['winter-swell'].waveSpeed,1.25);
console.log('PASS original four-scene piecewise clocks, source domain atomicity and checkpoint roundtrip');
