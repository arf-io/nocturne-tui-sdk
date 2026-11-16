export function checkFloorCollider(scene,recipe,time=null){
 const info=scene.infoComplete(),mask=info.emitters[0].colliders;
 if(mask.floor!==recipe.floor||mask.surfaces.length!==0)throw Error('Explicit floor mask');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
 if(time!==null&&time>=8333){
  const particles=scene.particles();
  if(info.particles.deposited!==(recipe.floor?32:0)||particles.length!==(recipe.floor?0:32))throw Error('Actual floor collision outcome');
  if(!recipe.floor&&particles.some(p=>p[4]>=0))throw Error('Excluded floor crossing');
 }
}
