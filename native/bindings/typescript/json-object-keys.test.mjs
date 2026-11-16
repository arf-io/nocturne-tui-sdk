import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const raw=text=>{const bytes=new TextEncoder().encode(text);new Uint8Array(s.exports.memory.buffer,s.input,bytes.length).set(bytes);return s.exports.nrCommand(s.context,s.input,bytes.length);};
try{
 s.command({op:'define',path:'/object',type:'json',value:null});let identity=0;
 for(const key of ['k'.repeat(2000),'日'.repeat(500),'nul\0key','😀'.repeat(200)]){
  const value={[key]:++identity};s.command({op:'set',path:'/object',value});assert.deepEqual(s.info().values['/object'],value);
  const saved=s.snapshot();s.restore(saved);assert.deepEqual(s.snapshot(),saved);
  s.command({op:'emit-intent',event:'/host/object',payload:value});
  s.command({op:'set',path:'/object',intentId:identity,expression:{intentPath:''}});s.command({op:'ack-intent',id:identity});assert.deepEqual(s.info().values['/object'],value);
 }
 for(const [left,right] of [['x'.repeat(2000),'x'.repeat(2000)],['日'.repeat(200),'\\u65e5'.repeat(200)],['a\\u0000b','a\\u0000b'],['abc','a\\u0062c']]){
  const saved=s.snapshot();assert.equal(raw('{"op":"set","path":"/object","value":{"'+left+'":1,"'+right+'":2}}'),-1);assert.deepEqual(s.snapshot(),saved);
 }
 const rule={id:'state',states:{['s'.repeat(128)]:{enabled:false}}};s.command({op:'character-rule',rule});assert.deepEqual(s.info().characterRules,[rule]);
 const object={['k'.repeat(1000)]:1,['nul\0key']:2,wanted:7};
 s.command({op:'set',path:'/object',value:object});s.command({op:'define',path:'/out',value:0});
 s.command({op:'set',path:'/out',expression:{path:'/object',pointer:'/wanted'}});assert.equal(s.info().values['/out'],7);
 s.command({op:'emit-intent',event:'/host/object',payload:object});
 s.command({op:'set',path:'/out',intentId:++identity,expression:{intentPath:'/wanted'}});assert.equal(s.info().values['/out'],7);
 const equalValue={['日'.repeat(500)]:3,['nul\0key']:4,tail:[1,2]};
 s.command({op:'set',path:'/object',value:equalValue});s.command({op:'define',path:'/equal',value:false});
 s.command({op:'set',path:'/equal',expression:{equal:[{path:'/object'},{literal:Object.fromEntries(Object.entries(equalValue).reverse())}]}});
 assert.equal(s.info().values['/equal'],true);const pure=s.snapshot();s.render();assert.deepEqual(s.snapshot(),pure);
 console.log(JSON.stringify({runtime:'actual WASM',longUnicodeKeys:true,nulDataKeys:true,decodedDuplicateRejection:true,stateName128:true,replay:true}));
}finally{s.close();}
