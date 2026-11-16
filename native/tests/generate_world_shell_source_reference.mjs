// Offline original source expectations; never native candidate output.
import {sampleWorldEvent} from '../../bindings/continuity/black-hole-space.js';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const rows=[],times=[0,60000,120000,1000000,4999999,5000000];
for(const [profile,effect] of [['nova','weather/ejecta-shell'],['ripples','weather/pressure-shell']])for(const seed of [0,2030,4294967295])for(const count of [1,64,1200]){
 const controls={seed,count,scale:.75,lifeMs:5000,gravity:2.6};
 const samples=times.map(us=>{
  const points=sampleWorldEvent({kind:profile,seed,scale:controls.scale,lifeMs:5000,atMs:0,position:{x:0,y:0,z:0}},us/1000,count,controls.gravity);
  return {pointCount:points.length,points:points.slice(0,16).map(p=>[p.x,p.y,p.z,p.glyph,p.opacity,p.hue])};
 });rows.push({profile,effect,controls,samples});
}
const sources={};for(const p of ['bindings/continuity/black-hole-space.js','bindings/continuity/observatory.js'])sources[p]=createHash('sha256').update(readFileSync(new URL('../../'+p,import.meta.url))).digest('hex');
writeFileSync(new URL('./fixtures/world-shell-source-reference.json',import.meta.url),JSON.stringify({origin:'Offline original explicit-time source sampler',sources,times,rows})+'\n');
