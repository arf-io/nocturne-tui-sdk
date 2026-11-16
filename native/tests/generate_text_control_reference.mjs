// Offline preserved source control-boundary oracle; never candidate output.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {sampleText} from '../../bindings/continuity/kinetic-text.js';
import {sampleAtelierText} from '../../bindings/continuity/atelier-text.js';
const ledger=JSON.parse(readFileSync(new URL('../port-ledger.json',import.meta.url))),rows=[],times=[0,137000,333000,730000,12000000,30000000];
for(const entry of ledger.entries.filter(e=>e.nativeContract==='TextTransition')){
 const family=entry.oldId.includes('/atelier/')?'atelier':'kinetic',effect=entry.oldId.split('/').at(-1);
 for(const phase of ['show','hide'])for(const boundary of ['low','high']){
  if(family==='kinetic'&&phase==='show'&&['fall','ash'].includes(effect))continue;
  const high=boundary==='high',config={durationMs:high?(family==='atelier'?10000:12000):0,staggerMs:high?(family==='atelier'?500:1000):0,jitterMs:high&&family==='kinetic'?4000:0,batchSize:high?(family==='atelier'?64:128):1,distance:high?(family==='atelier'?80:100):0,scatter:high?(family==='atelier'?80:120):0,variation:high?(family==='atelier'?.95:.9):0,wind:high?(family==='atelier'?30:20):(family==='atelier'?-30:-20),overshoot:high?(family==='atelier'?3:2):0,cycles:high?(family==='atelier'?8:20):0,scrambleHz:high?(family==='atelier'?60:120):1,hueSpread:high?(family==='atelier'?360:180):(family==='atelier'?0:-180),seed:high?4294967295:0,delayMs:high&&family==='atelier'?5000:0,easing:'smooth',trailLength:0,alphabet:' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/!?'};
  const options=family==='atelier'?{effect,durationMs:config.durationMs,delayMs:config.delayMs,staggerMs:config.staggerMs,batchSize:config.batchSize,seed:config.seed,travelRows:config.distance,spreadColumns:config.scatter,drift:config.wind,speedJitter:config.variation,cycleHz:config.scrambleHz,easing:config.easing,trailLength:0,overshoot:config.overshoot,turns:config.cycles,hueSpread:config.hueSpread,alphabet:config.alphabet}:{effect,phase:phase==='show'?'reveal':'hide',durationMs:config.durationMs,staggerMs:config.staggerMs,jitterMs:config.jitterMs,batchSize:config.batchSize,distanceRows:config.distance,scatterCols:config.scatter,speedVariation:config.variation,scrambleHz:config.scrambleHz,alphabet:config.alphabet,cycles:config.cycles,wind:config.wind,overshoot:config.overshoot,seed:config.seed,easing:config.easing,hueSpread:config.hueSpread,originX:0,originY:0,width:120};
  rows.push({id:entry.newId,family,effect,phase,boundary,config,poses:times.map(us=>family==='atelier'?sampleAtelierText('NODE',phase,us/1000,options):sampleText('NODE',us/1000,options))});
 }
}
const sources={};for(const p of ['bindings/continuity/kinetic-text.js','bindings/continuity/atelier-text.js','bindings/continuity/observatory.js'])sources[p]=createHash('sha256').update(readFileSync(new URL('../../'+p,import.meta.url))).digest('hex');
writeFileSync(new URL('./fixtures/text-control-reference.json',import.meta.url),JSON.stringify({origin:'Offline original source low/high controls',times,sources,rows})+'\n');
