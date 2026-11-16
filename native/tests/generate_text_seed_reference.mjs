// Offline original-source fixture authoring; never invokes native candidate.
import {writeFileSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {sampleText} from '../../bindings/continuity/kinetic-text.js';
import {sampleAtelierText} from '../../bindings/continuity/atelier-text.js';
const rows=[],times=[0,41000,137000,333000,677000,999000,1000000];
for(const seed of [2147483647,2147483648,4294967295]){
 const size=256;
 const alphabet=Array.from({length:size},(_,i)=>String.fromCodePoint(0x400+i)).join('');
 for(const [family,effect,id] of [['kinetic','scramble','text/cipher-resolve'],['kinetic','flipboard','text/station-board'],['atelier','scramble','text/static-resolve'],['atelier','flipboard','text/departure-board']])for(const phase of ['show','hide']){
  const config={durationMs:1000,staggerMs:0,jitterMs:0,variation:0,seed,scrambleHz:24,easing:'linear',alphabet,trailLength:0};
  const poses=times.map(us=>family==='kinetic'?sampleText('NODE',us/1000,{effect,phase:phase==='show'?'reveal':'hide',durationMs:1000,staggerMs:0,jitterMs:0,speedVariation:0,seed,scrambleHz:24,easing:'linear',alphabet}):sampleAtelierText('NODE',phase,us/1000,{effect,durationMs:1000,staggerMs:0,speedJitter:0,seed,cycleHz:24,easing:'linear',alphabet,trailLength:0}));
  rows.push({family,id,phase,size,seed,config,poses:poses.map(ps=>ps.map(p=>p.glyph.codePointAt(0)))});
 }
}
const sources={};for(const p of ['bindings/continuity/kinetic-text.js','bindings/continuity/atelier-text.js','bindings/continuity/observatory.js'])sources[p]=createHash('sha256').update(readFileSync(new URL('../../'+p,import.meta.url))).digest('hex');
writeFileSync(new URL('./fixtures/text-seed-reference.json',import.meta.url),JSON.stringify({origin:'Preserved original JS samplers, offline; not native candidate output',times,sources,rows},null,2)+'\n');
