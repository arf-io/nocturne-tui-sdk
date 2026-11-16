import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 for(const command of [{op:'define',path:'/source',value:1e12,readonly:true},{op:'define',path:'/out',value:0},
  {op:'set',path:'/out',expression:{negate:{path:'/source'}}}])scene.command(command);
 assert.equal(scene.infoComplete().values['/out'],-1e12);
 scene.command({op:'environment',background:0});scene.command({op:'set',path:'/out',value:0xffffff});
 scene.command({op:'bind',path:'/out',binding:{family:'environment',id:0,field:'background'}});
 scene.command({op:'bind',path:'/out',binding:null});assert.equal(scene.infoComplete().valueDescriptors['/out'].binding,null);
 const before=scene.snapshot();assert.equal(new DataView(before.buffer).getUint32(12,true),scene.infoComplete().contract.snapshotSchema);assert.equal(before.length,scene.infoComplete().contract.snapshotCapacityBytes);
 for(const command of [{op:'set',path:'/out',value:1e12+1},{op:'set',path:'/source',value:0},
  {op:'bind',path:'/out',binding:{family:'accessibility',id:0,field:'screenReader'}}]){
  assert.throws(()=>scene.command(command));assert.deepEqual(scene.snapshot(),before);
 }
 scene.render();scene.infoComplete();assert.deepEqual(scene.snapshot(),before);scene.command({op:'set',path:'/out',value:1});scene.restore(before);assert.deepEqual(scene.snapshot(),before);
}finally{scene.close();}
console.log('PASS actual WASM wide numeric storage, expression/read-only, colour detach, range rollback and schema56 replay');
