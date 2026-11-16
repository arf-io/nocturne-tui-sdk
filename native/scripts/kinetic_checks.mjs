// Historical evaluator is an offline test oracle only; SDK dispatch remains C/WASM.
import {sampleWeather} from '../../bindings/continuity/kinetic-particles.js';
export function checkKinetic(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).kinetic;
 const want=sampleWeather({id:1,x:0,y:0,atMs:0,kind:recipe.profile},us/1000,{seed:2030,shockwave:.4});
 if(!row||row.profile!==recipe.profile)throw Error('Source profile ownership');
 for(const key of ['core','radius','shockwave'])if(Math.abs(row[key]-want[key])>5e-5)throw Error('Original source core/radius/envelope');
 for(const key of ['points','segments']){
  if(row[key+'Count']!==want[key].length||row[key].length!==Math.min(16,want[key].length))throw Error('Source primitive full/sample counts');
  for(const [index,actual] of row[key].entries()){
   const r=want[key][index],expected=key==='points'?[r.x,r.y,r.opacity,r.heat,r.glyph.codePointAt(0),r.size]:[r.x1,r.y1,r.x2,r.y2,r.opacity,r.heat,r.branch];
   if(actual.some((value,k)=>Math.abs(value-expected[k])>5e-5))throw Error('Original source primitive');
  }
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runKinetic(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkKinetic(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
