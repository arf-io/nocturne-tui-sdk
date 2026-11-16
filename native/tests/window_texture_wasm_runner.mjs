import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';

const [inputPath,outputPath]=process.argv.slice(2);
const {commands,changes}=JSON.parse(readFileSync(inputPath,'utf8'));
const scene=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
try{
  for(const command of commands)scene.command(command);
  const schema=new DataView(scene.snapshot().buffer).getUint32(12,true);assert.ok(schema>=0x20261068,'window texture writer contract required');
  assert.equal(scene.infoComplete().contract.snapshotSchema,schema);
  const frames=[];
  for(const command of changes){
    if(command)scene.command(command);
    const before=scene.snapshot(),frame=scene.render();
    assert.deepEqual(scene.snapshot(),before,'render is pure');
    frames.push({words:Array.from(new Uint32Array(frame.bytes.buffer,frame.bytes.byteOffset,frame.bytes.byteLength/4)),
      texture:scene.infoComplete().windows.find(w=>w.id===1).texture});
  }
  writeFileSync(outputPath,JSON.stringify({frames}));
}finally{scene.close();}
