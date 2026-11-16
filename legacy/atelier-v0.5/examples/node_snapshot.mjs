/** Complete Node example: node examples/node_snapshot.mjs > frame.ansi */
import fs from 'node:fs';
import {NocturneEngine,toAnsi} from '../dist/typescript/nocturne.js';
const schema=JSON.parse(fs.readFileSync(new URL('../schema.json',import.meta.url),'utf8'));
const bytes=fs.readFileSync(new URL('../dist/nocturne.wasm',import.meta.url));
const engine=await NocturneEngine.create(bytes,schema);
const config=engine.defaults({width:80,height:24,layout:1,effect:3,stars:1});
const frame=engine.render(config,6000,'hello from TypeScript / Node');
process.stdout.write(toAnsi(frame)+'\n');
