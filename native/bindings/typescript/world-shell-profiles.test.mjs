import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const bytes=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
for(const [effect,clumpy] of [['weather/ejecta-shell',true],['weather/pressure-shell',false]]){
 const s=await NativeScene.create(bytes);
 try{
  s.command({op:'emitter',id:1,effect,seed:73,count:32,runningTimeMs:0,position:[0,0,0],velocity:[0,0,0],radius:2,wind:[0,0,0],windVariation:[0,0,0],collision:false,deposit:false,lifetimeMinMs:5000,lifetimeMaxMs:5000});
  const start=s.snapshot();s.advanceTo(750000);const expected=s.snapshot(),age=s.info().clock.step/120;
  const rows=s.particles();rows.forEach((row,i)=>{const y=1-2*(i+.5)/32,angle=i*2.399963229728653+73*.0001,ring=Math.sqrt(1-y*y),r=2*(1+age*4.2)*(clumpy?1+.13*Math.sin(angle*3+y*8+73):1),want=[Math.cos(angle)*ring*r,y*r,Math.sin(angle)*ring*r];for(let k=0;k<3;k++)assert.ok(Math.abs(row[3+k]/65536-want[k])<.0015);});
  const q=s.info().emitters[0].worldShellProfile;q.shape='caller';s.render();assert.deepEqual(s.snapshot(),expected);assert.equal(s.info().emitters[0].worldShellProfile.active,true);
  s.restore(start);for(const t of [100000,250000,500000,750000])s.advanceTo(t);assert.deepEqual(s.snapshot(),expected);
 }finally{s.close();}
}
console.log('PASS actual WASM independent clumpy/uniform shell geometry, owned profile metadata, purity and replay');
