import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const triangles=[{a:[0,0,0],b:[1,0,0],c:[0,0,1],surfaceId:1},{a:[1,0,0],b:[1,0,1],c:[0,0,1],surfaceId:1}];
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-11,`${a} != ${b}`);
function seed(s){
 for(const command of [{op:'floor',enabled:false},{op:'surface',id:1,restitution:1,friction:0,settleSpeed:0},{op:'mesh',triangles},
 {op:'surface-foam',surfaceId:1,sourceRate:0,decay:0,impactGain:.001},
 {op:'emitter',id:1,effect:'weather/autumn-drift',count:1,runningTimeMs:0,shape:'point',position:[.2,1,.2],velocity:[0,-240,0],extent:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,flutterHz:0,flutterAmount:0,tumble:[0,0,0],deposit:false,collision:true,lifetimeMinMs:10000,lifetimeMaxMs:10000,sizeMin:1,sizeMax:1,colliders:{surfaces:[1]}}])s.command(command);
 s.advanceTo(8333);
}
function crc(bytes){let value=0xffffffff;for(const byte of bytes){value^=byte;for(let i=0;i<8;i++)value=(value>>>1)^((value&1)?0xedb88320:0);}return (value^0xffffffff)>>>0;}
function schema32(snapshot){const old=snapshot.slice(0,24+12499168),view=new DataView(old.buffer,old.byteOffset,old.byteLength);view.setUint32(12,0x20261032,true);view.setUint32(16,12499168,true);view.setUint32(28,0x20261032,true);view.setUint32(20,crc(old.subarray(24)),true);return old;}
const s=await NativeScene.create(wasm,2030),oracle=await NativeScene.create(wasm,2030);
try{
 seed(s);seed(oracle);near(s.surfaceFoamTransport(1)[0][1],.24);
 const initial=s.snapshot(),ledger=s.surfaceFoamTransport(1);
 s.command({op:'define',path:'/drift',value:1,binding:{family:'surface-foam',id:1,field:'velocity.x'}});assert.deepEqual(s.surfaceFoamTransport(1),ledger);
 s.command({op:'remove-value',path:'/drift'});oracle.command({op:'surface-foam-transport',surfaceId:1,velocity:[1,0]});assert.deepEqual(s.snapshot(),oracle.snapshot());
 const saved=s.snapshot();s.advanceTo(16666);const rows=s.surfaceFoamTransport(1),amount=.24*2/120;
 near(rows[0][1],.24-amount);near(rows[1][1],amount);near(rows[0][6],amount);near(rows[1][5],amount);
 for(const r of rows)near(r[2]+r[5],r[1]+r[3]+r[4]+r[6]);
 const finish=s.snapshot();rows[0][1]=99;s.render();s.info();s.surfaceFoamTransport(1);assert.deepEqual(s.snapshot(),finish);
 s.restore(saved);s.advanceTo(16666);assert.deepEqual(s.snapshot(),finish);
 s.restore(initial);s.command({op:'surface-foam-transport',surfaceId:1,velocity:[1000,1000]});s.advanceTo(16666);near(s.surfaceFoamTransport(1)[0][1],0);near(s.surfaceFoamTransport(1)[1][1],.24);
 s.advanceTo(25000);near(s.surfaceFoamTransport(1)[1][1],.24);s.command({op:'surface-foam-transport',surfaceId:1,velocity:[-1000,-1000]});s.advanceTo(33333);near(s.surfaceFoamTransport(1)[0][1],.24);
 s.restore(initial);const saturated=s.snapshot(),satView=new DataView(saturated.buffer,saturated.byteOffset,saturated.byteLength),cell=24+4788952+16*48+32;
 satView.setFloat64(cell,.9,true);satView.setFloat64(cell+8,.9,true);satView.setUint32(20,crc(saturated.subarray(24)),true);s.restore(saturated);
 s.command({op:'surface-foam-transport',surfaceId:1,velocity:[1000,1000]});s.advanceTo(16666);near(s.surfaceFoamTransport(1)[1][4],.14);
 s.restore(initial);s.command({op:'define',path:'/flag',value:true});s.command({op:'define',path:'/n',value:1});s.command({op:'schedule',id:1,atUs:16666,command:{op:'set',path:'/n',expression:{path:'/n'}}});
 s.restore(schema32(s.snapshot()));assert.equal(s.info().values['/flag'],true);assert.deepEqual(s.surfaceFoamTransport(1)[0].slice(5),[0,0]);s.advanceTo(16666);
 s.restore(initial);s.command({op:'schedule',id:1,atUs:16666,command:{op:'surface-foam-transport',surfaceId:1,velocity:[1,0]}});let blocked=s.snapshot();assert.throws(()=>s.restore(schema32(blocked)));assert.deepEqual(s.snapshot(),blocked);
 s.restore(initial);blocked=s.snapshot();const bad=blocked.slice(),badView=new DataView(bad.buffer,bad.byteOffset,bad.byteLength);badView.setFloat64(24+12499168+256,-1,true);badView.setUint32(20,crc(bad.subarray(24)),true);assert.throws(()=>s.restore(bad));assert.deepEqual(s.snapshot(),blocked);
 s.command({op:'surface-foam-transport',surfaceId:1,velocity:[1,0]});
 let before=s.snapshot();for(const velocity of [[1],[1,0,0],[1001,0],[true,0]]){assert.throws(()=>s.command({op:'surface-foam-transport',surfaceId:1,velocity}));assert.deepEqual(s.snapshot(),before);}
 assert.throws(()=>s.command({op:'mesh',triangles:[...triangles,{a:[1,0,0],b:[2,0,2],c:[0,0,1],surfaceId:1}]}));assert.deepEqual(s.snapshot(),before);
 assert.throws(()=>s.command({op:'mesh',triangles:[{a:[0,0,0],b:[0,1,0],c:[0,0,1],surfaceId:1}]}));assert.deepEqual(s.snapshot(),before);
 const out=new Float64Array(s.exports.memory.buffer,s.checkpoint,14);out.fill(123);assert.equal(s.exports.nrSurfaceFoamTransport(s.context,1,s.checkpoint,1),-1);assert.deepEqual(Array.from(out),Array(14).fill(123));
 s.command({op:'surface-foam',surfaceId:1,enabled:false});s.command({op:'clear-surface-foam',surfaceId:1});assert.ok(s.surfaceFoamTransport(1).every(r=>r.slice(1).every(v=>v===0)));
 s.command({op:'mesh',triangles});assert.ok(s.surfaceFoamTransport(1).every(r=>r.slice(1).every(v=>v===0)));
}finally{s.close();oracle.close();}
console.log(JSON.stringify({runtime:'actual WASM',concern:'horizontal foam inventory transport',analyticFlux:true,positivity:true,closedEdges:true,replay:true,purity:true,atomicRejection:true}));
