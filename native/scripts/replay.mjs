import { readFileSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { createHash } from 'node:crypto';
import { NativeScene } from '../bindings/typescript/native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
const hash=b=>createHash('sha256').update(b).digest('hex');
let index=0;
for await(const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
 const command=JSON.parse(line);while(scene.command(command)===1){}
 const frame=scene.render(),state=scene.snapshot();
 console.log(JSON.stringify({index:index++,frame:hash(frame.bytes),state:hash(state),metadata:scene.info(),motions:scene.particleMotions()}));
}
