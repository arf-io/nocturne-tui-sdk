import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
function setup(temperature=300,target=true){
 s.command({op:'reset'});s.command({op:'surface',id:1});
 s.command({op:'mesh',triangles:[{a:[0,0,0],b:[1,0,0],c:[0,0,1],surfaceId:1},{a:[2,0,0],b:[3,0,0],c:[2,0,1],surfaceId:1}]});
 s.command({op:'surface-water',surfaceId:1,capacity:10,evaporationUs:0});s.command({op:'surface-water-add',triangleIndex:0,volume:4});
 s.command({op:'surface-thermal',triangleIndex:0,temperature,capacity:100});
 if(target)s.command({op:'surface-thermal',triangleIndex:1,temperature:100,capacity:200});
}
const command={op:'surface-water-transfer',fromTriangle:0,toTriangle:1,volume:2,heatCapacityPerVolume:10};
try{
 setup();const before=s.snapshot();s.command(command);const after=s.snapshot();
 const a=s.thermalSample(0),b=s.thermalSample(1);assert.equal(a[0],240);assert.equal(b[0],130);assert.equal(a[6],6000);assert.equal(b[5],6000);assert.equal(a[1]+b[1],50000);
 assert.deepEqual(s.info().surfaceWater[0].cells.map(row=>row.retainedVolume),[2,2]);s.render();assert.deepEqual(s.snapshot(),after);s.restore(before);s.command(command);assert.deepEqual(s.snapshot(),after);
 setup();const legacy={...command};delete legacy.heatCapacityPerVolume;s.command(legacy);assert.equal(s.thermalSample(0)[0],300);assert.equal(s.thermalSample(1)[0],100);
 setup();for(const cp of [0,-1,1e9+1,1000,'ten',null]){const saved=s.snapshot();assert.throws(()=>s.command({...command,heatCapacityPerVolume:cp}));assert.deepEqual(s.snapshot(),saved);}
 setup(300,false);const saved=s.snapshot();assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),saved);
 setup();s.command({op:'surface-thermal-power',triangleIndex:0,power:100});s.advanceTo(1000000);s.command(command);
 assert.ok(Math.abs(s.thermalSample(0)[0]-240.8)<1e-6);assert.ok(Math.abs(s.thermalSample(1)[0]-130.1)<1e-6);assert.ok(Math.abs(s.thermalSample(0)[3]-100)<1e-6);
 const wetSaved=s.snapshot();assert.throws(()=>s.command({...command,volume:3}));assert.deepEqual(s.snapshot(),wetSaved);
 setup(300,false);s.command({op:'surface-thermal',triangleIndex:1,temperature:9999,capacity:1});const hotSaved=s.snapshot();assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),hotSaved);
 setup(0);s.command(command);assert.equal(s.thermalSample(1)[0],100);
 console.log('Actual WASM water-carried heat conservation, compatibility, rejection, purity and replay passed');
}finally{s.close();}
