import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const bytes=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),names=['silk-tide','satin-rings','opal-fronts','interference-tide'];
for(let profile=0;profile<4;profile++){const s=await NativeScene.create(bytes);try{s.command({op:'field',optics:'source',effect:'surface-field/'+names[profile],x:10,y:5,width:1,speed:8,strength:.7,lifeMs:4000,seed:0});
for(const t of [0,250000,1000000,2250000]){s.advanceTo(t);const before=s.snapshot(),age=t/1e6,radius=16*age,fade=1-age/4;
for(const [x,y] of [[10,5],[10.25,5],[12,5],[14,5],[18,5],[22,5],[10,8]]){const d=Math.hypot(2*(x-10),4*(y-5));let expected;
if(profile===0){let peak=0;for(let k=0;k<2;k++){const r=radius-8*k;if(r<0)continue;const p=Math.max(0,1-Math.abs(d-r)/2);peak=Math.max(peak,p*p*(3-2*p)/(1+.42*k));}expected=peak*fade*fade*(3-2*fade)*.7;}
else if(profile===1)expected=(Math.abs(d-radius)<=6?Math.exp(-(((d-radius)/2)**2)):0)*fade**2*.65*.7;
else if(profile===2){const hit=Array.from({length:96},(_,j)=>j).some(j=>Math.floor(2*x+.5)===Math.floor(20+radius*Math.cos(j*Math.PI/48)+.5)&&Math.floor(4*y+.5)===Math.floor(20+radius*Math.sin(j*Math.PI/48)+.5));expected=hit?fade**1.5*.7:0;}
else expected=Math.max(0,1-Math.abs(d-radius)/2)*fade**1.8*.35*.7;
assert.ok(Math.abs(s.fieldSample(1,x,y)[0]-expected)<2e-6,`${names[profile]} ${t} ${x} ${y}`);}s.render();assert.deepEqual(before,s.snapshot());}
const b=s.snapshot();assert.throws(()=>s.command({op:'field',optics:'unknown'}));assert.deepEqual(b,s.snapshot());}finally{s.close();}}
console.log('PASS actual WASM four independent source-optics equations/geometry, purity and atomic rejection');
