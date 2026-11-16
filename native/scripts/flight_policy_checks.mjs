export function checkFlightPolicy(scene,recipe,us){
 const info=scene.infoComplete(),camera=info.camera,t=Math.min(1,us/1e6),want=[0,0,40-4*t];
 if(camera.position.some((v,i)=>Math.abs(v-want[i])>1e-6)||camera.yaw!==0||camera.pitch!==0)throw Error('Independent cruise position');
 if(Math.abs(camera.roll-(recipe.coordinated?20*Math.sin(Math.PI*t):0))>2e-5)throw Error('Independent coordination bank');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runFlightPolicy(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkFlightPolicy(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
