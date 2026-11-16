import {readFileSync} from 'node:fs';
import {createInterface} from 'node:readline';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)));
let index=0;
for await(const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
 const {text}=JSON.parse(line);console.log(JSON.stringify({index:index++,boundaries:scene.graphemeBoundaries(text),widths1:scene.graphemeWidths(text,1),widths2:scene.graphemeWidths(text,2),layouts:[1,3,8].flatMap(columns=>[1,2].map(policy=>scene.graphemeLayout(text,columns,policy)))}));
}scene.close();
