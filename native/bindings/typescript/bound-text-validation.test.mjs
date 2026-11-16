import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const cases=[['widget','text',{op:'widget',id:1,kind:'button'}],
 ['window','title',{op:'window',id:1}],['window','text',{op:'window',id:1}],
 ['text','text',{op:'text',id:1,text:'old'}],['node','label',{op:'node',id:1,label:'old'}],
 ['node','detail',{op:'node',id:1,label:'old'}],['indicator','sequence',{op:'indicator',id:1}]];
for(const [family,field,base] of cases){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  s.command(base);s.command({op:'define',path:'/text',value:'old',binding:{family,id:1,field}});
  for(const control of ['\u0000','\u0001','\u001b','\u001f'])for(const command of [
   {op:family,id:1,[field]:'before'+control+'after'},{op:'set',path:'/text',value:'before'+control+'after'}]){
   const before=s.snapshot();assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),before);
  }
  // Compare clean scenes so source glyph identities and inactive tails share history.
  const value='日本\té\n👩‍🔧';oracle.command(base);
  oracle.command({op:family,id:1,[field]:'old'});
  s.command({op:'set',path:'/text',value});s.command({op:'remove-value',path:'/text'});
  oracle.command({op:family,id:1,[field]:value});assert.deepEqual(s.snapshot(),oracle.snapshot());
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);
try{
 const value='\u0000\u0001\u001b';s.command({op:'define',path:'/data',value});assert.equal(s.info().values['/data'],value);
 const saved=s.snapshot();s.restore(saved);assert.deepEqual(s.snapshot(),saved);
 console.log(JSON.stringify({runtime:'actual WASM',textTargets:cases.length,publicValidationParity:true,atomicRejection:true,unicode:true,dataStrings:true}));
}finally{s.close();}
