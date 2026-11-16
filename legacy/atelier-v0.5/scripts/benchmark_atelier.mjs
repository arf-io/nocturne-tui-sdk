#!/usr/bin/env node
/** Measure model+cell rendering separately from terminal transport. No claim
 * of physical FPS. Fixed seeds/timestamps, explicit repeated warm-up frames. */
import fs from 'node:fs';import {performance} from 'node:perf_hooks';
import {StudioEngine} from '../dist/typescript/studio.js';
import {AtelierModel,AtelierRenderer,ATELIER_SCENES} from '../dist/typescript/atelier.js';
import {CellWriter} from '../examples/observatory_writer.mjs';
import {PassThrough} from 'node:stream';
const engine=await StudioEngine.create(fs.readFileSync('dist/nocturne.wasm'),JSON.parse(fs.readFileSync('studio.schema.json'))),r=new AtelierRenderer(engine),out=[];
for(const scene of ATELIER_SCENES.slice(0,6)){
 const m=new AtelierModel();m.setScene(scene.id);if(scene.id==='weather')m.emit(65,22,'*','nova');
 for(let i=0;i<12;i++){m.setTime(i*17);r.render(m);}
 const costs=[],encodes=[],bytes=[];const stream=new PassThrough();stream.resume();const writer=new CellWriter(stream);
 for(let i=0;i<80;i++){m.setTime(250+i*1000/60);const t=performance.now(),f=r.render(m).frame;costs.push(performance.now()-t);const tt=performance.now(),encoded=writer.encode(f);encodes.push(performance.now()-tt);if(i)bytes.push(Buffer.byteLength(encoded));}
 const summary=a=>{const v=[...a].sort((a,b)=>a-b);return {median:v[Math.floor(v.length*.5)],p95:v[Math.floor(v.length*.95)],max:v.at(-1)};};
 writer.dispose();out.push({scene:scene.id,cells:[m.width,m.height],renderMs:summary(costs),encodeMs:summary(encodes),bytesPerFrame:summary(bytes),estimatedBytesPerSecond60:Math.round(bytes.reduce((a,b)=>a+b,0)/bytes.length*60)});
}
fs.writeFileSync('dist/atelier/performance.json',JSON.stringify({note:'Linux sandbox / Node 22 / WASM. Excludes stdout transport, terminal emulation and physical display.',results:out},null,2)+'\n');console.log(JSON.stringify(out,null,2));
