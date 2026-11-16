import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 s.command({op:'emitter',id:1,effect:'weather/chrysanthemum',seed:73,count:1,runningTimeMs:0,shape:'point',position:[0,0,0],velocity:[0,0,0],extent:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,flutterAmount:0,collision:false,deposit:false,coreMs:200,lifetimeMinMs:2000,lifetimeMaxMs:2000});
 s.advanceTo(8333);const birth=s.info().clock.step,start=s.snapshot(),frame=s.render();
 s.advanceTo(100000);let q=s.infoComplete().emitters[0].burstStages,row=q.samples[0];const age=(s.info().clock.step-birth)/120;
 assert.ok(Math.abs(row[3]-Math.sqrt(1-age/.2))<1e-5);assert.ok(Math.abs(row[5]-Math.exp(-age/.18))<1e-5);
 const before=s.snapshot(),particles=s.particles();s.command({op:'burst-style',id:1,glitterDepth:0,coreAlpha:0,residualAlpha:0});
 row=s.info().emitters[0].burstStages.samples[0];assert.equal(row[3],0);assert.ok(Math.abs(row[4]-(1-age/2)**1.5)<1e-5);assert.equal(row[5],0);assert.deepEqual(s.particles(),particles);
 q=s.infoComplete();q.emitters[0].burstStages.samples[0][3]=999;assert.notEqual(s.infoComplete().emitters[0].burstStages.samples[0][3],999);
 const guarded=s.snapshot();assert.throws(()=>s.command({op:'burst-style',id:1,glitterHz:61}));assert.deepEqual(s.snapshot(),guarded);
 s.restore(start);assert.deepEqual(s.render(),frame);s.advanceTo(100000);assert.deepEqual(s.snapshot(),before);
 console.log('PASS actual WASM source-derived firework stages, live controls, ownership, atomicity and replay');
}finally{s.close();}
