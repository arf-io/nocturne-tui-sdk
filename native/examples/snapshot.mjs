import {readFile,writeFile} from 'node:fs/promises';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const scene=await NativeScene.create(await readFile(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
scene.command({op:'emitter',id:1,effect:'weather/autumn-drift',count:40});
scene.advanceTo(900000);
await writeFile('preview.cells',scene.render().bytes);
console.log(JSON.stringify(scene.info(),null,2));
