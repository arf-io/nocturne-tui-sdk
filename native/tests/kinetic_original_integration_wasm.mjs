import assert from 'node:assert/strict';
import fs from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const bytes=fs.readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url));
const scene=await NativeScene.create(bytes,2030),result=[];
for(const request of JSON.parse(fs.readFileSync(process.argv[2],'utf8'))){
 scene.command({op:'reset',seed:2030});
 for(const command of request.baseCommands)scene.command(command);
 scene.command({op:'emitter',id:1,effect:request.effect,position:[0,0,0],count:0,alpha:1,runningTimeMs:0});
 scene.command({op:'kinetic-style',id:1,...request.options});
 scene.advanceTo(request.timeMs*1000);const before=scene.snapshot();result.push(Array.from(scene.render().cells));assert.deepEqual(scene.snapshot(),before);
}
scene.close();process.stdout.write(JSON.stringify(result));
