import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const base={op:'emitter',id:1,effect:'weather/autumn-drift',count:100,
 runningTimeMs:2000,lifetimeMinMs:1000,lifetimeMaxMs:4000,
 sizeMin:.5,sizeMax:3,position:[0,6,0],wind:[0,0,0],collision:true,deposit:false};
const node={op:'node',id:1,label:'SDK resource',position:[0,6,0],minColumns:22,maxColumns:44,padding:1};
const indicator={op:'indicator',id:1,area:0,x:12,y:6,sequence:'◐◓◑◒',stepMs:120,material:2,cursor:false};
const prompt={op:'prompt',mode:'marquee',minRows:1,maxRows:6,padding:1};
const environment={op:'environment',background:0x0b1528,stars:180,starFar:130,sampling:'hybrid',style:'solid'};
const field={op:'field',effect:'surface-field/silk-tide',x:50,y:16,width:2,speed:8,strength:.5,lifeMs:4000,material:2};
const singletons=new Set(['floor','prompt','environment']);
const bases={emitter:base,floor:{op:'floor'},node,indicator,prompt,environment,field};
const cases=[
 ['emitter','wind.x',3,{...base,wind:[3,0,0]}],
 ['emitter','sizeMax',2,{...base,sizeMax:2}],
 ['emitter','lifetimeMaxMs',5000,{...base,lifetimeMaxMs:5000}],
 ['emitter','birthFadeMs',200,{...base,birthFadeMs:200}],
 ['emitter','birthOrientation.y',20,{...base,birthOrientation:[0,20,0]}],
 ['emitter','angularVelocity.z',20,{...base,angularVelocity:[0,0,20]}],
 ['emitter','sampling',1,{...base,sampling:'half'}],
 ['floor','retentionMs',4000,{op:'floor',retentionMs:4000}],
 ['floor','restitution',.3,{op:'floor',restitution:.3}],
 ['floor','height',-3,{op:'floor',height:-3}],
 ['node','color',0xaabbcc,{...node,color:0xaabbcc}],
 ['node','position.y',8,{...node,position:[0,8,0]}],
 ['node','maxColumns',50,{...node,maxColumns:50}],
 ['node','showDetail',0,{...node,showDetail:false}],
 ['indicator','x',16,{...indicator,x:16}],
 ['indicator','stepMs',200,{...indicator,stepMs:200}],
 ['indicator','cursor',1,{...indicator,cursor:true}],
 ['prompt','mode',1,{...prompt,mode:'grow'}],
 ['prompt','maxRows',8,{...prompt,maxRows:8}],
 ['environment','background',0x123456,{...environment,background:0x123456}],
 ['environment','style',2,{...environment,style:'plasma'}],
 ['field','width',1000,{...field,width:1000}],
 ['field','x',500,{...field,x:500}],
];
for(const [family,field,value,expected] of cases){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  s.command(bases[family]);oracle.command(expected);
  s.command({op:'define',path:'/control',value,binding:{family,id:singletons.has(family)?0:1,field}});
  s.command({op:'remove-value',path:'/control'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  s.advanceTo(1000000);oracle.advanceTo(1000000);assert.deepEqual(s.snapshot(),oracle.snapshot());
  assert.deepEqual(s.render().bytes,oracle.render().bytes);
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
try{
 for(const scene of [s,oracle]){scene.command({op:'text',id:1,text:'Retained source',effect:'text/ink-dissolve',x:8,y:10,width:32});scene.advanceTo(250000);}
 s.command({op:'define',path:'/text-width',value:18,binding:{family:'text',id:1,field:'width'}});
 oracle.command({op:'text',id:1,width:18});s.command({op:'remove-value',path:'/text-width'});
 assert.deepEqual(s.snapshot(),oracle.snapshot());
 const before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value:0,binding:{family:'text',id:1,field:'width'}}));assert.deepEqual(s.snapshot(),before);
 s.command(base);s.command({op:'path-travel',id:1,target:{family:'emitter',id:1},points:[[0,6,0],[10,6,0]],speed:1});
 const owned=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/x',value:3,binding:{family:'emitter',id:1,field:'position.x'}}));assert.deepEqual(s.snapshot(),owned);
 s.command({op:'remove-path-travel',id:1});s.command({op:'define',path:'/x',value:3,binding:{family:'emitter',id:1,field:'position.x'}});
 const start=s.snapshot();s.advanceTo(1000000);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 console.log(JSON.stringify({runtime:'actual WASM',publicConfigurationOracles:cases.length,textRetarget:true,atomicRejection:true,pathOwnership:true,replay:true,renderPure:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();oracle.close();}
