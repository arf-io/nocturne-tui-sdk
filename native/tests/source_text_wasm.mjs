import fs from 'node:fs';import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const wasm=fs.readFileSync(process.argv[2]),requests=JSON.parse(fs.readFileSync(process.argv[3],'utf8')),out=[];
let scene=null,group='';
for(const c of requests){const key=c.name.split('-').slice(0,-1).join('-');
 if(key!==group){if(scene)scene.close();scene=await NativeScene.create(wasm,2030);group=key;for(const cmd of c.commands)scene.command(cmd);}
 scene.advanceTo(c.timeMs*1000);const frame=scene.render();const raw=new Uint32Array(frame.bytes.buffer,frame.bytes.byteOffset,frame.bytes.length/4);
 out.push({cells:Array.from(raw),poses:Array.from(c.text,(_,i)=>scene.textSample(1,i))});
}
if(scene)scene.close();process.stdout.write(JSON.stringify(out));
