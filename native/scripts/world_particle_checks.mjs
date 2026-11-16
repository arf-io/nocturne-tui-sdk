// Original evaluator is an offline test oracle; SDK dispatch remains native C/WASM.
import {sampleWorldEvent} from '../../bindings/continuity/black-hole-space.js';
export function checkWorldParticle(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).worldSource;
 const control=recipe.commands.find(c=>c.op==='world-style');
 const sourceRipple=recipe.profile==='ripples'&&(control.paint??'source')==='source';
 const want=sourceRipple?[]:sampleWorldEvent({kind:recipe.profile,seed:control.seed,scale:control.scale,lifeMs:control.lifeMs,atMs:0,position:{x:0,y:0,z:0}},us/1000,control.count,control.gravity);
 if(!row||row.profile!==recipe.profile||row.elapsedUs!==us)throw Error('World ownership/epoch');
 if(row.paint!==(control.paint??'source'))throw Error('World paint ownership');
 if(sourceRipple){
  // Actual archived WorldRenderer dispatches ripples to the Studio integer
  // tile, not sampleWorldEvent's precipitation fallthrough. Full original
  // pixel/oblique-plane parity is asserted by WorldOriginalIntegration.
  const emitter=recipe.commands.find(command=>command.op==='emitter'&&command.id===1),plane=row.ripplePlane;
  const expected={eventId:1,speed:2048,width:384,opacity:600,rings:4,cellAspect:2000,unitsPerCell:control.scale??1};
  if(!plane||Object.entries(expected).some(([key,value])=>plane[key]!==value))throw Error('Original world ripple plane controls');
  const orientation=emitter.birthOrientation??[0,0,0];
  if(plane.birthOrientation.length!==3||plane.birthOrientation.some((value,index)=>Math.abs(value-orientation[index])>5e-5))throw Error('Original world ripple immutable plane');
  if(row.projectedSegmentsCount!==0||row.projectedSegments.length!==0)throw Error('World ripple fabricated particle projection');
 }

 const points=want.map(r=>[r.x,r.y,r.z,r.glyph,r.opacity,r.hue]);
 const segments=want.filter(r=>r.previous).map(r=>[r.previous.x,r.previous.y,r.previous.z,r.x,r.y,r.z,r.opacity,r.hue]);
 for(const [key,expected] of [['points',points],['segments',segments]]){
  if(row[key+'Count']!==expected.length||row[key].length!==Math.min(16,expected.length))throw Error('World primitive counts '+key);
  for(const [index,actual] of row[key].entries())if(actual.length!==expected[index].length||actual.some((value,k)=>Math.abs(value-expected[index][k])>5e-5))throw Error('Original world primitive '+key+' '+index);
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runWorldParticle(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkWorldParticle(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
