import assert from 'node:assert/strict';
import fs from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const scene=await NativeScene.create(fs.readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030),result=[];
for(const c of JSON.parse(fs.readFileSync(process.argv[2],'utf8'))){
 scene.command({op:'reset',seed:2030});for(const command of c.baseCommands)scene.command(command);
 scene.command({op:'emitter',id:1,effect:c.effect,position:[0,0,0],count:0,alpha:1,runningTimeMs:0});scene.command({op:'corona-style',id:1,...c.options});scene.advanceTo(c.timeMs*1000);
 const before=scene.snapshot();result.push(Array.from(scene.render().cells));assert.deepEqual(scene.snapshot(),before);
}scene.close();process.stdout.write(JSON.stringify(result));
