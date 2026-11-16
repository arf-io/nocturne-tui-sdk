// Offline original Atelier trail fixture authoring; never native candidate output.
import {sampleAtelierText} from '../../bindings/continuity/atelier-text.js';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const effects=[['rain','text/skyfall-type'],['comet-stitch','text/comet-stitch'],['constellation','text/constellation-type'],['orbit','text/orbital-type'],['prism-weave','text/prism-weave']],times=[0,40000,80000,180000,410000,730000,1080000,1200000],rows=[];
for(const [effect,id] of effects)for(const easing of ['linear','smooth','cubic','back','bounce'])for(const phase of ['show','hide'])for(const trailLength of [0,1,8]){
 const config={durationMs:1000,delayMs:80,staggerMs:20,variation:0,distance:6,scatter:3,wind:2,cycles:1.5,hueSpread:110,seed:6137,easing,overshoot:1.2,trailLength};
 const poses=times.map(us=>sampleAtelierText('NODE',phase,us/1000,{effect,easing,overshoot:1.2,trailLength,durationMs:1000,delayMs:80,staggerMs:20,speedJitter:0,travelRows:6,spreadColumns:3,drift:2,turns:1.5,hueSpread:110,seed:6137}));
 rows.push({id,phase,easing,trailLength,config,poses});
}
const sources={};for(const p of ['bindings/continuity/atelier-text.js','bindings/continuity/observatory.js'])sources[p]=createHash('sha256').update(readFileSync(new URL('../../'+p,import.meta.url))).digest('hex');
writeFileSync(new URL('./fixtures/text-trail-reference.json',import.meta.url),JSON.stringify({origin:'Original Atelier source sampler, offline; not candidate output',sources,times,rows})+'\n');
