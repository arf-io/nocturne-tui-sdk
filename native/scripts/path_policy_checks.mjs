export function expectedPathPolicy(recipe,us){
 const length=recipe.closed?12:7;let d=8*us/1e6;
 if(recipe.travelMode==='clamp')d=Math.min(length,d);
 else if(recipe.travelMode==='loop')d%=length;
 else {d%=2*length;if(d>length)d=2*length-d;}
 if(d<3)return [d,0,0];if(d<=7)return [3,d-3,0];
 return [3*(1-(d-7)/5),4*(1-(d-7)/5),0];
}
export function checkPathPolicy(scene,recipe,us){
 const info=scene.infoComplete(),actor=info.pathActors.find(a=>a.id===1),want=expectedPathPolicy(recipe,us);
 if(!actor||actor.family!==recipe.targetFamily||actor.position.some((v,i)=>Math.abs(v-want[i])>1e-6))throw Error('Independent path target position');
 if(recipe.targetFamily==='window'&&JSON.stringify(info.windows.find(w=>w.id===1).position)!==JSON.stringify(actor.position))throw Error('Window target pose');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runPathPolicy(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkPathPolicy(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
