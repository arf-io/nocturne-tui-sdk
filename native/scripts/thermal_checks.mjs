// Preserved evaluator is an offline test oracle; SDK dispatch is always C/WASM.
import {sampleThermal} from '../../bindings/continuity/effect-catalog.js';
export function checkThermal(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).thermalSource;
 const control=recipe.commands.find(c=>c.op==='thermal-style');
 const want=sampleThermal(recipe.profile,control.seed,us/1000,control.lifeMs);
 if(!row||row.profile!==recipe.profile||row.elapsedUs!==us)throw Error('Thermal ownership/epoch');
 for(const key of ['points','segments']){
  if(row[key+'Count']!==want[key].length||row[key].length!==Math.min(16,want[key].length))throw Error('Thermal primitive counts '+key);
  for(const [index,actual] of row[key].entries()){
   const r=want[key][index],expected=key==='points'?[r.x,r.y,r.z,r.glyph.codePointAt(0),r.opacity,r.hue]:[r.a.x,r.a.y,r.a.z,r.b.x,r.b.y,r.b.z,r.opacity,r.hue];
   if(actual.length!==expected.length||actual.some((value,k)=>Math.abs(value-expected[k])>5e-5))throw Error('Original thermal primitive '+key+' '+index);
  }
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runThermal(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkThermal(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
