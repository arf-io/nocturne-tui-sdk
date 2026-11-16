import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const base={op:'cell-art',id:1,width:2,height:1,x:4,y:8,alpha:.7,layer:'overlay',cells:[[65,0xabcdef,0x123456],[66,0x654321,0x102030]]};
for(const [field,value] of [['x',12],['y',14],['alpha',.3],['layer',0],['x',2147483647],['y',-2147483648]]){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle])scene.command(base);
  s.command({op:'define',path:'/art',value,binding:{family:'cell-art',id:1,field}});
  oracle.command({op:'cell-art',id:1,[field]:field==='layer'?['background','overlay'][value]:value});
  s.command({op:'remove-value',path:'/art'});assert.deepEqual(s.snapshot(),oracle.snapshot());assert.deepEqual(s.render().bytes,oracle.render().bytes);
  const start=s.snapshot();s.advanceTo(1000000);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
console.log(JSON.stringify({runtime:'actual WASM',publicEditOracles:6,largeCoordinates:true,sourcePreserved:true,purity:true,replay:true}));
