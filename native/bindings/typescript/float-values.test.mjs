import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const fields={mass:2000,radius:2,fluidDensity:800,gravity:10,drag:3,visible:0,color:0xabcdef,surfaceId:2,
 'position.x':2,'position.y':2,'position.z':2,'velocity.x':1,'velocity.y':1,'velocity.z':1};
for(const [field,value] of Object.entries(fields)){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle]){
   for(const command of [{op:'surface',id:1},{op:'surface',id:2},
    {op:'mesh',triangles:[{a:[-10,0,-10],b:[10,0,-10],c:[0,0,10],surfaceId:1}]},
    {op:'float-body',id:1,surfaceId:1,position:[0,0,0],velocity:[1,0,0]}])scene.command(command);
   scene.advanceTo(250000);
  }
  const current=oracle.floatBody(1),edit={op:'float-body',id:1};
  if(field.includes('.')){
   const [name,axis]=field.split('.');edit[name]=Array.from(current.slice(name==='position'?0:3,name==='position'?3:6));edit[name]['xyz'.indexOf(axis)]=value;
  }else edit[field]=field==='visible'?Boolean(value):value;
  s.command({op:'define',path:'/control',value,binding:{family:'float-body',id:1,field}});
  oracle.command(edit);s.command({op:'remove-value',path:'/control'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);oracle.advanceTo(1000000);const finish=s.snapshot();assert.deepEqual(finish,oracle.snapshot());
  s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
console.log(JSON.stringify({runtime:'actual WASM',movingBodyPublicOracles:Object.keys(fields).length,purity:true,replay:true}));
