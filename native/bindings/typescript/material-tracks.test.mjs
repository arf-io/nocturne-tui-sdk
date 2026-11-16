import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const fields={initial:.4,rate:.2,min:.1,max:.9,step:.2,periodMs:1200,boundary:2,easing:4,seed:4294967295};
for(const base of ['alpha','index','channels.h'])for(const [member,value] of Object.entries(fields)){
 const s=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
 try{
  for(const scene of [s,oracle])scene.command({op:'material',id:2,space:'hsl'});
  s.command({op:'define',path:'/control',value,binding:{family:'material',id:2,field:`${base}.${member}`}});
  const authored=member==='boundary'?['clamp','loop','reverse','random','smooth-random'][value]:member==='easing'?['linear','ease-in','ease-out','smooth','smoother','sine','step'][value]:value;
  const edit={[member]:authored};oracle.command({op:'material',id:2,...(base.startsWith('channels.')?{channels:{[base.at(-1)]:edit}}:{[base]:edit})});
  s.command({op:'remove-value',path:'/control'});assert.deepEqual(s.snapshot(),oracle.snapshot());
  s.advanceTo(1000000);oracle.advanceTo(1000000);assert.deepEqual(s.render().bytes,oracle.render().bytes);
 }finally{s.close();oracle.close();}
}
console.log(JSON.stringify({runtime:'actual WASM',independentPublicTrackOracles:27,fullUnsignedSeed:true}));
