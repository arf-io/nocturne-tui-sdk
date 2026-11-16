import {sampleBurst} from './atelier_oracle.mjs';
export function checkAtelier(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).atelier;
 const command=recipe.commands.find(c=>c.op==='atelier-style'),{op,id,eventId,...options}=command;
 const want=sampleBurst({id:eventId,x:0,y:0,atMs:0,kind:recipe.profile},us/1000,options);
 if(!row||row.profile!==recipe.profile||row.elapsedUs!==us)throw Error('Atelier ownership/epoch');
 for(const key of ['points','segments','glows']){
  if(row[key+'Count']!==want[key].length||row[key].length!==Math.min(16,want[key].length))throw Error('Source primitive counts '+key);
  for(const [index,actual] of row[key].entries()){
   const r=want[key][index],expected=key==='points'?[r.x,r.y,r.glyph.codePointAt(0),r.alpha,r.heat]:key==='segments'?[r.x1,r.y1,r.x2,r.y2,r.alpha,r.heat]:[r.x,r.y,r.radius,r.alpha,r.heat,r.ring?1:0];
   if(actual.some((value,k)=>Math.abs(value-expected[k])>5e-5))throw Error('Original Atelier primitive '+key+' '+index);
  }
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runAtelier(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkAtelier(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
