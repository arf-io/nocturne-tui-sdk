import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const smooth=p=>p*p*(3-2*p);
const empty=s.snapshot();
try{for(const rings of [1,3,16]){s.restore(empty);s.command({op:'field',x:10,y:5,width:1,speed:8,strength:.7,lifeMs:4000,material:0,rings});
for(const t of [0,250000,1000000,2000000]){s.advanceTo(t);const b=s.snapshot();for(const x of [10,10.25,12,14,18]){const age=t/1e6,d=2*Math.abs(x-10),expected=Math.max(...Array.from({length:rings},(_,k)=>smooth(Math.max(0,1-Math.abs(d-16*age+8*k)/2))/(1+.42*k)))*smooth(1-age/4)*.7;assert.ok(Math.abs(s.fieldSample(1,x,5)[0]-expected)<2e-6);}s.render();assert.deepEqual(b,s.snapshot());}}
for(const rings of [0,17,1.5,true]){const b=s.snapshot();assert.throws(()=>s.command({op:'field',rings}));assert.deepEqual(b,s.snapshot());}console.log('PASS actual WASM compact soft-front independent oracle, purity and rejection');}finally{s.close();}
