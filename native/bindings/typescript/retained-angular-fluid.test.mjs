import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
try{
 scene.command({op:'surface',id:1});assert.equal(scene.surfaceFluidAngular(1),null);
 scene.command({op:'mesh',triangles:[{a:[-20,0,-20],b:[20,0,-20],c:[20,0,20],surfaceId:1},{a:[-20,0,-20],b:[20,0,20],c:[-20,0,20],surfaceId:1}]});
 scene.command({op:'surface-fluid',surfaceId:1,mass:3});scene.command({op:'surface-fluid-angular',surfaceId:1,inertia:3});
 const owned=scene.surfaceFluidAngular(1);assert.deepEqual(owned,[3,0,0,0,0,0,0,0,0,0,0,0]);owned[0]=999;assert.equal(scene.surfaceFluidAngular(1)[0],3);
 const vertices=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]];
 scene.command({op:'float-body',id:1,surfaceId:1,mass:2,gravity:0,drag:2,position:[0,-2,0]});scene.command({op:'float-hull',id:1,vertices,faces,inertia:[2,2,2],angularVelocity:[0,1,0]});
 const start=scene.snapshot();scene.advanceTo(8334);const body=scene.floatHull(1),water=scene.surfaceFluidAngular(1),f=-Math.expm1(-4/120*(1/2+1/3));
 near(body[5],1-.6*f);near(water[2],.4*f);near(water[8],1.2*f);near(water[10],.6*f*(2-f));near(2*body[5]+3*water[2],2);near(body[5]**2+1.5*water[2]**2+water[10],1);
 const metadata=scene.info().surfaceFluidAngular[0];assert.equal(metadata.active,true);assert.equal(metadata.history.exports,0);assert.ok(Math.abs(metadata.omega[1]-water[2])<=5.1e-7);assert.equal(scene.info().contract.queryContracts.nrSurfaceFluidAngular.rowWords,12);
 const before=scene.snapshot();scene.render();assert.deepEqual(scene.snapshot(),before);
 scene.restore(start);scene.advanceTo(250000);const finish=scene.snapshot();scene.restore(start);for(const time of [13000,51000,119000,187000,250000])scene.advanceTo(time);assert.deepEqual(scene.snapshot(),finish);
 const record=scene.surfaceFluidAngular(1);scene.command({op:'stop-surface-fluid',surfaceId:1});scene.advanceTo(500000);assert.deepEqual(scene.surfaceFluidAngular(1),record);
 scene.command({op:'surface',id:2});scene.command({op:'surface-fluid',surfaceId:2,mass:4});scene.command({op:'schedule',id:1,atUs:1000000,command:{op:'surface-fluid-angular',surfaceId:2,inertia:3}});scene.command({op:'surface-fluid-angular',surfaceId:2,inertia:4});const blocked=scene.snapshot();scene.restore(blocked);assert.throws(()=>scene.advanceTo(1000000));assert.deepEqual(scene.snapshot(),blocked);scene.command({op:'cancel-schedule',id:1});scene.advanceTo(1000000);assert.equal(scene.surfaceFluidAngular(2)[0],4);
}finally{scene.close();}
const posed=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 for(const command of [{op:'surface',id:1},{op:'mesh',triangles:[{a:[10,20,30],b:[14,20,30],c:[10,20,34],surfaceId:1}]},{op:'surface-fluid',surfaceId:1,mass:3},{op:'surface-fluid-angular',surfaceId:1,inertia:3,pivot:[10,20,30],orientation:[0,0,Math.sin(Math.PI/8),Math.cos(Math.PI/8)],omega:[0,0,Math.PI/2]}])posed.command(command);
 const start=posed.snapshot(),triangles=posed.surfaceTriangles(1);near(triangles[0][4],10+4*Math.SQRT1_2);near(triangles[0][5],20+4*Math.SQRT1_2);
 const sample=posed.surfaceWaveSample(1,11,31);near(sample[0],21);near(sample[1],-Math.SQRT1_2);near(sample[2],Math.SQRT1_2);near(sample[4],Math.PI/2);
 triangles[0][4]=999;near(posed.surfaceTriangles(1)[0][4],10+4*Math.SQRT1_2);
 const metadata=posed.info().surfaceFluidAngular[0];assert.deepEqual(metadata.pose.pivot,[10,20,30]);metadata.pose.pivot[0]=999;assert.deepEqual(posed.info().surfaceFluidAngular[0].pose.pivot,[10,20,30]);assert.deepEqual(posed.snapshot(),start);
 posed.advanceTo(250000);const finish=posed.snapshot();posed.restore(start);for(const time of [13000,119000,250000])posed.advanceTo(time);assert.deepEqual(posed.snapshot(),finish);
 const before=posed.snapshot();posed.render();assert.deepEqual(posed.snapshot(),before);
 posed.command({op:'stop-surface-fluid',surfaceId:1});const frozen=posed.info().surfaceFluidAngular[0].pose;posed.advanceTo(500000);assert.deepEqual(posed.info().surfaceFluidAngular[0].pose,frozen);
}finally{posed.close();}
console.log('PASS retained angular reciprocal exchange, ownership and replay');
