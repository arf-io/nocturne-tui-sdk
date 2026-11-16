import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const cases=[
 ['widget','border',3,'double'],['widget','sampling',2,'braille'],['widget','revealMs',1200,1200],
 ['window','border',3,'double'],['window','shape',2,'ellipse'],['window','group',2,2],
 ['area','border',3,'double'],['area','layout',1,'queue'],
];
for(const [family,field,value,authored] of cases){
 const scene=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  const base={op:family,id:1,...(family==='widget'?{kind:'progress'}:{})};
  for(const s of [scene,oracle]){s.command(base);s.advanceTo(250000);}
  scene.command({op:'define',path:'/control',value,binding:{family,id:1,field}});
  oracle.command({op:family,id:1,[field]:authored});scene.command({op:'remove-value',path:'/control'});
  assert.deepEqual(scene.snapshot(),oracle.snapshot());
  scene.advanceTo(1000000);oracle.advanceTo(1000000);assert.deepEqual(scene.render().bytes,oracle.render().bytes);
 }finally{scene.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 s.command({op:'area',id:1});s.command({op:'area',id:2,parent:1});
 for(const value of [1,2,99]){const before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value,binding:{family:'area',id:1,field:'parent'}}));assert.deepEqual(s.snapshot(),before);}
 s.command({op:'define',path:'/parent',value:1,binding:{family:'area',id:2,field:'parent'}});
 s.command({op:'widget',id:1,kind:'button'});s.command({op:'window',id:1});
 for(const [family,field,value] of [['widget','sampling',2],['widget','revealMs',1200],['window','shape',11]]){const before=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value,binding:{family,id:1,field}}));assert.deepEqual(s.snapshot(),before);}
 console.log(JSON.stringify({runtime:'actual WASM',publicEditOracles:cases.length,areaHierarchyAtomicRejection:true,plotApplicability:true,polygonApplicability:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
