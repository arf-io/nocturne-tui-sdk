import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm);
try{
 const fields=[['position.x',12,'position',[12,6,30]],['position.y',9,'position',[0,9,30]],['position.z',25,'position',[0,6,25]],['yaw',20,'yaw',20],['pitch',-15,'pitch',-15],['roll',30,'roll',30],['near',.5,'near',.5],['far',150,'far',150],['fov',50,'fov',50],['span',30,'span',30],['orthographic',1,'orthographic',true]];
 for(const [field,value,key,expected] of fields){s.command({op:'reset'});s.command({op:'camera',position:[0,6,30],yaw:0,pitch:0,roll:0,near:.1,far:200,fov:70,span:40,orthographic:false});s.command({op:'define',path:'/control',value,binding:{family:'camera',field}});assert.deepEqual(s.info().camera[key],expected);const saved=s.snapshot();s.render();assert.deepEqual(s.snapshot(),saved);s.command({op:'set',path:'/control',value});s.restore(saved);assert.deepEqual(s.snapshot(),saved);}
 s.command({op:'reset'});s.command({op:'widget',id:1,kind:'donut',data:[2,3,5]});s.command({op:'define',path:'/radius',value:.55,binding:{family:'widget',id:1,field:'innerRadius'}});s.command({op:'set',path:'/radius',value:.7});assert.equal(s.info().widgets[0].plot.innerRadius,.7);
 const saved=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/radius',value:1}));assert.deepEqual(s.snapshot(),saved);
 s.command({op:'flight',steps:[{kind:'cruise',durationMs:2000,speed:5}]});s.advanceTo(1000000);const pose=s.info().camera.position;s.command({op:'define',path:'/yaw',value:30,binding:{family:'camera',field:'yaw'}});assert.deepEqual(s.info().camera.position,pose);assert.equal(s.info().camera.flightActive,false);
 console.log(JSON.stringify({runtime:'actual WASM',cameraFields:fields.length,widgetGeometry:true,atomicRejection:true,flightCapture:true,renderPure:true,snapshotReplay:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
