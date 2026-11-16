import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const smooth=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
try{
 s.command({op:'emitter',id:1,effect:'weather/ejecta-shell',seed:73,count:8,runningTimeMs:0,radius:2,position:[0,0,0],velocity:[0,0,0],lifetimeMinMs:5000,lifetimeMaxMs:5000});
 const start=s.snapshot();s.advanceTo(750000);const before=s.snapshot(),frame=s.render(),q=s.info().emitters[0].novaOptics;
 for(const row of q.samples){const age=row[4]/1e6,lat=1-2*(row[3]+.5)/row[2],angle=row[3]*2.399963229728653+row[1]*.0001,clump=.3+.7*Math.sin(2*angle+9*lat+row[1])**2;assert.ok(Math.abs(row[5]-clump)<1e-5);assert.ok(Math.abs(row[6]-smooth(age/.12)*smooth((1-age/5)*2)*clump)<1e-5);}
 q.samples[0][6]=999;s.render();assert.deepEqual(s.snapshot(),before);assert.notEqual(s.info().emitters[0].novaOptics.samples[0][6],999);
 s.restore(start);for(const t of [100000,250000,500000,750000]){s.advanceTo(t);s.render();}assert.deepEqual(s.snapshot(),before);assert.deepEqual(s.render(),frame);
 s.advanceTo(5100000);assert.deepEqual(s.info().emitters[0].novaOptics.samples,[]);
 console.log('PASS actual WASM captured world nova source optics, ownership, purity, replay and cleanup');
}finally{s.close();}
