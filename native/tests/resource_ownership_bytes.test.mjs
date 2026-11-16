import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
import {equalBytes,projectOwnership,heldAutomaticExpected} from '../scripts/resource_ownership_checks.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)));
try{
 const original=scene.snapshot();assert.equal(equalBytes(original,scene.snapshot()),true);
 scene.command({op:'draft',text:'Actual source mutation',emitWeather:false});assert.equal(equalBytes(original,scene.snapshot()),false);
 for(const offset of [0,1,2,3,4,Math.floor(original.length/2),original.length-1]){
  const changed=original.slice();changed[offset]^=1;assert.equal(equalBytes(original,changed),false,'changed byte '+offset);
 }
 for(const length of [0,1,2,3,4,5,7,8]){
  const left=original.subarray(1,1+length),right=original.slice(1,1+length);assert.equal(equalBytes(left,right),true);
  if(length){right[length-1]^=1;assert.equal(equalBytes(left,right),false);}
 }
 assert.equal(equalBytes(original,original.subarray(1)),false);
 assert.throws(()=>equalBytes([],original),TypeError);
 scene.restore(original);scene.command({op:'define',path:'/ownership/control',value:7});const authored=scene.snapshot();
 assert.equal(equalBytes(projectOwnership(scene),original),true);assert.equal(equalBytes(scene.snapshot(),authored),true);
 const held=heldAutomaticExpected(scene);assert.equal(equalBytes(scene.snapshot(),authored),true);
 scene.command({op:'pause',paused:true});assert.equal(equalBytes(scene.snapshot(),held),true);assert.equal(equalBytes(held,authored),false);
}finally{scene.close();}
console.log('PASS real WASM snapshot identity, every-byte mismatch, alignment/tails and source-preserving projection');
