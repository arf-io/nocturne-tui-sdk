import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const [input,output]=process.argv.slice(2),requests=JSON.parse(readFileSync(input,'utf8'));
const wasm=readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),results=[];
assert.deepEqual(WebAssembly.Module.imports(new WebAssembly.Module(wasm)),[]);
for(const r of requests){
 const scene=await NativeScene.create(wasm,2030);
 try{for(const c of r.commands)scene.command(c);
 let k=0;
 for(const t of r.times){
  while(k<(r.actions||[]).length&&r.actions[k].timeUs<=t){const a=r.actions[k++];scene.advanceTo(a.timeUs);scene.command(a.command);}
  scene.advanceTo(t);const snap=scene.snapshot(),frame=scene.render();
  const words=Array.from(new Uint32Array(frame.bytes.buffer,frame.bytes.byteOffset,frame.bytes.byteLength/4));
  assert.deepEqual(scene.snapshot(),snap);results.push({id:r.id,timeUs:t,words});
 }
 }finally{scene.close();}
}
writeFileSync(output,JSON.stringify(results));
