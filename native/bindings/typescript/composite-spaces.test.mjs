import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 const before=scene.snapshot(),q=65535n;
 let checks=0;
 for(const [baseAlpha,sourceAlpha] of [[0,0],[0,65535],[65535,0],[65535,65535],[12345,45678],[32768,32768]]){
  const b=BigInt(baseAlpha),a=BigInt(sourceAlpha);
  // Exact coverage numerators with denominator q squared; no float oracle.
  const coverage=[(a+b)*q-a*b,0n,a*q,b*q,(a+b)*q-a*b,a*b,a*b,
   a*(q-b),b*(q-a),b*q,a*q,(a+b)*q-2n*a*b,(a+b)*q];
  for(const [operation,numerator] of coverage.entries()){
   const bounded=numerator>q*q?q*q:numerator;
   const expected=Number((2n*bounded+q)/(2n*q));
   for(let space=0;space<4;space++){
    for(let blend=0;blend<28;blend++){
     if(blend===26)continue; // Dissolve explicitly changes source coverage.
     assert.equal(scene.compositeInSpace(0x204060,0xe08010,space,baseAlpha,sourceAlpha,blend,operation).alpha,expected,`${baseAlpha}:${sourceAlpha}:${operation}:${space}:${blend}`);checks++;
    }
   }
  }
 }
 assert.deepEqual(scene.snapshot(),before);
 console.log(JSON.stringify({runtime:'actual WASM',exactCoverageOracles:checks,operators:13,spaces:4,coveragePreservingBlends:27,purity:true}));
}finally{scene.close();}
