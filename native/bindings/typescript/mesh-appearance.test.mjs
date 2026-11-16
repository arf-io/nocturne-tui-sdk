import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const triangles=[{a:[-10,0,-10],b:[10,0,-10],c:[0,0,10],surfaceId:1,color:0x123456,alpha:.6},
 {a:[10,0,-10],b:[20,0,-10],c:[10,0,10],surfaceId:1,color:0x654321,alpha:.3}];
for(const [family,id,field,value,edit] of [
 ['mesh',0,'alpha',.2,{alpha:.2}],['mesh',0,'color',0xabcdef,{color:0xabcdef}],
 ['mesh',0,'sampling',2,{sampling:'braille'}],
 ['triangle',1,'alpha',.2,{triangleIndex:1,alpha:.2}],['triangle',1,'color',0xabcdef,{triangleIndex:1,color:0xabcdef}],
]){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle]){
   for(const command of [{op:'surface',id:1},{op:'mesh',triangles},
    {op:'surface-waves',surfaceId:1,waves:[[1,1,0,0,0]]},{op:'surface-foam',surfaceId:1,curvatureThreshold:0}])scene.command(command);
   scene.advanceTo(250000);
  }
  const ledger=s.surfaceFoam(1);
  s.command({op:'define',path:'/appearance',value,binding:{family,id,field}});
  assert.deepEqual(s.surfaceFoam(1),ledger);oracle.command({op:'mesh-style',...edit});
  s.command({op:'remove-value',path:'/appearance'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  const start=s.snapshot();s.advanceTo(1000000);const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);
  s.restore(start);s.advanceTo(1000000);assert.deepEqual(s.snapshot(),finish);
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'surface',id:1});s.command({op:'mesh',triangles});
 for(const edit of [{alpha:2},{triangleIndex:2,alpha:.5},{triangleIndex:0,sampling:'braille'},{color:.5},{},{alpha:.5,color:-1}]){
  const before=s.snapshot();assert.throws(()=>s.command({op:'mesh-style',...edit}));assert.deepEqual(s.snapshot(),before);
 }
 s.command({op:'define',path:'/triangle',value:.5,binding:{family:'triangle',id:1,field:'alpha'}});
 s.command({op:'mesh',triangles:[triangles[0]]});const before=s.snapshot();
 assert.throws(()=>s.command({op:'set',path:'/triangle',value:.8}));assert.deepEqual(s.snapshot(),before);
 s.command({op:'bind',path:'/triangle',binding:{family:'triangle',id:0,field:'alpha'}});
 console.log(JSON.stringify({runtime:'actual WASM',appearanceOracles:5,ledgerPreserved:true,removedIndex:true,atomicRejection:true,purity:true,replay:true}));
}finally{s.close();}
