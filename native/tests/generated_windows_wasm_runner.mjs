import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const [input,output]=process.argv.slice(2),request=JSON.parse(readFileSync(input,'utf8'));
const scene=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
try{
  for(const command of request.commands)scene.command(command);
  const frames=[];
  for(const item of request.actions){
    scene.command(item.command);scene.advanceTo(item.time);
    const before=scene.snapshot(),frame=scene.render();assert.deepEqual(scene.snapshot(),before);
    frames.push({words:Array.from(new Uint32Array(frame.bytes.buffer,frame.bytes.byteOffset,frame.bytes.byteLength/4)),content:scene.infoComplete().windows[0].content});
  }
  const document='x'.repeat(4095)+'Z';
  scene.command({op:'window-content',id:1,text:document});
  assert.equal(scene.textRunSource(2,1),document);
  for(const identity of ['pearl-cascade','tidal-glass','copper-causeway','red-shift','silt']){
    scene.command({op:'scene-art',scene:identity});assert.equal(scene.infoComplete().sceneArt.scene,identity);
  }
  scene.command({op:'remove-scene-art'});assert.equal(scene.infoComplete().sceneArt,null);
  writeFileSync(output,JSON.stringify(frames));
}finally{scene.close();}
