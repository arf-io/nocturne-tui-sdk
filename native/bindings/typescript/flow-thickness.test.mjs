import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);
function setup(s,tailUs=0,delayUs=0){for(const command of [{op:'floor',enabled:false},{op:'surface',id:1,restitution:1,friction:0,settleSpeed:0},{op:'ribbon',points:[[0,0,-2],[0,0,0]],width:2,surfaceId:1},{op:'flow',id:1,flux:2,stages:[{name:'channel',tailUs,delayUs}]},{op:'flow-surface',surfaceId:1,flowId:1,stage:'channel',referenceFlux:2},{op:'flow-thickness',surfaceId:1,width:2,speed:2,maxDepth:1,direction:[0,1,0]}])s.command(command);}
function volume(rows){let total=0;for(const r of rows){const a=r.slice(1,4),b=r.slice(4,7),c=r.slice(7,10);for(let k=0;k<3;k++)total+=a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3])/6;}return Math.abs(total);}
const s=await NativeScene.create(wasm);
try{
 setup(s);near(s.flowThickness(1)[1],.5);near(s.flowThickness(1)[2],1);const rows=s.surfaceTriangles(1);assert.equal(rows.length,12);near(volume(rows),2);
 const before=s.snapshot();rows[0][1]=99;s.surfaceTriangles(1);s.render();s.info();assert.deepEqual(s.snapshot(),before);
 for(const command of [{op:'mesh',triangles:[]},{op:'remove-flow-surface',surfaceId:1},{op:'flow-rate',id:1,flux:5},{op:'surface-waves',surfaceId:1,waves:[[1,1,0,0,0]]}]){assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),before);}
 s.command({op:'emitter',id:1,effect:'weather/autumn-drift',count:1,runningTimeMs:0,shape:'point',position:[0,1,-1],velocity:[0,-240,0],extent:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,flutterHz:0,flutterAmount:0,tumble:[0,0,0],deposit:false,collision:true,lifetimeMinMs:10000,lifetimeMaxMs:10000,sizeMin:.1,sizeMax:.1,colliders:{surfaces:[1]}});
 s.advanceTo(8333);const p=s.particles()[0];assert.ok(Math.abs(p[7]/65536-240)<2/65536);assert.ok(Math.abs(p[4]/65536-2.001)<2/65536);
 s.command({op:'remove-flow-thickness',surfaceId:1});assert.equal(s.flowThickness(1),null);assert.equal(s.surfaceTriangles(1).length,2);
 s.command({op:'reset'});setup(s,1000000,250000);near(s.flowThickness(1)[1],0);assert.deepEqual(s.surfaceTriangles(1),[]);s.advanceTo(1250000);near(s.flowThickness(1)[1],.5*(1-Math.exp(-1)));
 s.command({op:'flow-rate',id:1,flux:0});const saved=s.snapshot();s.advanceTo(2500000);near(s.flowThickness(1)[1],.5*(Math.exp(-1)-Math.exp(-2.25)));const finish=s.snapshot();s.restore(saved);s.advanceTo(2500000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'reset'});setup(s,10000);s.command({op:'emitter',id:1,effect:'weather/autumn-drift',count:1,runningTimeMs:0,shape:'point',position:[0,.1,-1],velocity:[0,0,0],extent:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,flutterHz:0,flutterAmount:0,tumble:[0,0,0],deposit:false,collision:true,lifetimeMinMs:10000,lifetimeMaxMs:10000,sizeMin:.1,sizeMax:.1,colliders:{surfaces:[1]}});
 s.advanceTo(8333);const depth=.5*(1-Math.exp(-.8333)),moving=s.particles()[0];assert.ok(Math.abs(moving[7]/65536-2*120*depth)<3/65536);assert.ok(Math.abs(moving[4]/65536-(2*depth-.099))<3/65536);
 const out=new Float64Array(s.exports.memory.buffer,s.checkpoint,12);out.fill(123);assert.equal(s.exports.nrSurfaceTriangles(s.context,1,s.checkpoint,1),-1);assert.equal(s.exports.nrFlowThickness(s.context,1,s.checkpoint,5),-1);assert.deepEqual(Array.from(out),Array(12).fill(123));
 s.command({op:'reset'});s.command({op:'surface',id:1});s.command({op:'ribbon',points:[[0,0,-2],[0,0,0]],width:2,surfaceId:1});
 s.command({op:'flow',id:1,flux:2,stages:[{name:'first',delayUs:250000,tailUs:1000000},{name:'second',delayUs:125000,tailUs:1000000},{name:'third'}]});
 s.command({op:'flow-surface',surfaceId:1,flowId:1,stage:'third',referenceFlux:2});s.command({op:'flow-thickness',surfaceId:1,width:2,speed:2,maxDepth:1});
 const erlang=t=>t<=0?0:1-Math.exp(-t)*(1+t);
 for(const time of [0,375000,500000,1375000]){
  s.advanceTo(time);const sample=s.flowThickness(1),expected=2*erlang(time/1e6-.375);near(sample[0],expected);assert.equal(s.info().flows[0].stages[2].flux,Number(sample[0].toFixed(6)));
  const geometry=s.surfaceTriangles(1);if(sample[1]>0)near(Math.max(...geometry.flatMap(r=>[r[2],r[5],r[8]])),expected/4);else assert.deepEqual(geometry,[]);
 }
 s.command({op:'flow-rate',id:1,flux:0});const serialSaved=s.snapshot();s.advanceTo(2750000);near(s.flowThickness(1)[0],2*(erlang(2.375)-erlang(1)));assert.equal(s.info().flows[0].stages[2].flux,Number(s.flowThickness(1)[0].toFixed(6)));
 const serialFinish=s.snapshot();s.render();s.flowThickness(1);s.surfaceTriangles(1);assert.deepEqual(s.snapshot(),serialFinish);s.restore(serialSaved);s.advanceTo(2750000);assert.deepEqual(s.snapshot(),serialFinish);
 s.command({op:'reset'});setup(s);const meshIds=s.surfaceTriangles(1).map(r=>r[0]),ledger=s.info().flows,foamLedger=s.surfaceFoamTransport(1);
 s.command({op:'flow-thickness-settings',surfaceId:1,width:4,speed:1});assert.deepEqual(s.flowThickness(1),[2,.5,2,4,1,1]);assert.deepEqual(s.surfaceTriangles(1).map(r=>r[0]),meshIds);assert.deepEqual(s.info().flows,ledger);assert.deepEqual(s.surfaceFoamTransport(1),foamLedger);
 s.command({op:'flow-thickness-settings',surfaceId:1,speed:2});near(s.flowThickness(1)[1],.25);const hydraulic=s.snapshot();
 for(const command of [{op:'flow-thickness-settings',surfaceId:1},{op:'flow-thickness-settings',surfaceId:1,width:.1},{op:'flow-thickness-settings',surfaceId:1,speed:0},{op:'flow-thickness-settings',surfaceId:1,width:4,direction:[0,1,0]}]){assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),hydraulic);}
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'flow-thickness-settings',surfaceId:1,width:4}});s.command({op:'remove-flow-thickness',surfaceId:1});const missing=s.snapshot();s.restore(missing);assert.throws(()=>s.advanceTo(500000));assert.deepEqual(s.snapshot(),missing);s.restore(missing);s.command({op:'cancel-schedule',id:1});s.advanceTo(500000);
 s.command({op:'reset'});setup(s);for(const [field,value] of [['width',4],['speed',1]])s.command({op:'define',path:'/'+field,value,binding:{family:'surface',id:1,field:'thickness.'+field}});
 assert.deepEqual(s.flowThickness(1),[2,.5,2,4,1,1]);s.command({op:'set',path:'/speed',value:2});near(s.flowThickness(1)[1],.25);const bound=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/width',value:.1}));assert.deepEqual(s.snapshot(),bound);
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/width',value:8}});s.command({op:'remove-flow-thickness',surfaceId:1});const dormant=s.snapshot();s.restore(dormant);assert.throws(()=>s.advanceTo(500000));assert.deepEqual(s.snapshot(),dormant);s.restore(dormant);s.command({op:'cancel-schedule',id:1});s.command({op:'bind',path:'/width',binding:null});s.command({op:'set',path:'/width',value:8});s.advanceTo(500000);
}finally{s.close();}
console.log(JSON.stringify({runtime:'actual WASM',concern:'flow-dependent closed geometry',volumeOracle:true,depthOracle:true,collisionTopFace:true,tailReplay:true,purity:true}));
const lifetime=await NativeScene.create(wasm);
try {
 for(const command of [{op:'surface',id:1},{op:'ribbon',points:[[0,0,-2],[0,0,0]],width:2,surfaceId:1},{op:'flow',id:1,flux:2,stages:[{name:'channel'}]},{op:'flow-surface',surfaceId:1,flowId:1,stage:'channel',referenceFlux:2},{op:'surface-water',surfaceId:1,capacity:1,evaporationUs:1000000},{op:'surface-water-add',triangleIndex:0,volume:.5},{op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2,power:4},{op:'surface-thermal',triangleIndex:1,temperature:300,capacity:2},{op:'surface-thermal-link',id:1,fromTriangle:0,toTriangle:1,conductance:3}])lifetime.command(command);
 lifetime.advanceTo(500000);const water=lifetime.waterSample(0),thermal=[lifetime.thermalSample(0),lifetime.thermalSample(1)],start=lifetime.snapshot();
 const compile={op:'flow-thickness',surfaceId:1,width:2,speed:2,maxDepth:1},retire={op:'remove-flow-thickness',surfaceId:1};lifetime.command(compile);assert.deepEqual(lifetime.waterSample(0),water);assert.deepEqual([lifetime.thermalSample(0),lifetime.thermalSample(1)],thermal);assert.equal(lifetime.info().thermalLinks.length,1);
 lifetime.command(retire);const info=lifetime.info();assert.ok(Math.abs(info.surfaceWater[0].exportedVolume-.5*Math.exp(-.5))<1e-6);assert.ok(Math.abs(info.surfaceThermal.exportedEnergy-1402)<1e-5);assert.equal(info.thermalLinks,undefined);assert.equal(lifetime.thermalSample(0),null);assert.deepEqual(lifetime.waterSample(0).slice(1,7),[0,0,0,0,0,0]);const finish=lifetime.snapshot();lifetime.restore(start);lifetime.command(compile);lifetime.command(retire);assert.deepEqual(lifetime.snapshot(),finish);
} finally {lifetime.close();}
