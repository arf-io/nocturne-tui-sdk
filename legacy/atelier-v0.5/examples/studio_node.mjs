/** Node.js snapshot host. No packages other than compiled SDK/WASM are needed. */
import fs from 'node:fs';
import {StudioEngine} from '../dist/typescript/studio.js';
import {toAnsi} from '../dist/typescript/nocturne.js';
const schema=JSON.parse(fs.readFileSync(new URL('../studio.schema.json',import.meta.url)));
const engine=await StudioEngine.create(new Uint8Array(fs.readFileSync(new URL('../dist/nocturne.wasm',import.meta.url))),schema);
const config=engine.defaults({width:80,height:24,pattern:3,focusMode:1,focusY:12*256});
const frame=engine.render(config,2500,[{kind:'progress',x:5,y:12,width:65,height:2,value:670,colorAnimation:2}],[{x:20,y:12,atMs:1700}]);
process.stdout.write(toAnsi(frame)+'\n');
