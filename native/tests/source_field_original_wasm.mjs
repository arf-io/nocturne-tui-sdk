import fs from 'node:fs';import assert from 'node:assert/strict';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const scene=await NativeScene.create(fs.readFileSync(process.argv[2]),2030),out=[];
for(const r of JSON.parse(fs.readFileSync(process.argv[3],'utf8'))){scene.command({op:'reset',seed:2030});for(const c of r.commands)scene.command(c);scene.advanceTo(r.timeMs*1000);const before=scene.snapshot();out.push(Array.from(scene.render().cells));assert.deepEqual(scene.snapshot(),before);}
scene.close();process.stdout.write(JSON.stringify(out));
