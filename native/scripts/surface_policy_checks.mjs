export function checkSurfacePolicy(scene,recipe,us){
 const info=scene.infoComplete(),surface=info.surfaces.find(s=>s.id===1),merged=recipe.overflow==='merge-to-field';
 if(!surface||surface.renderVisible!==recipe.renderVisible||surface.collisionEnabled!==true)throw Error('Independent visibility/collision policy');
 if(us>=8333&&(surface.individualDeposits!==1||surface.aggregateDeposits!==(merged?31:0)||surface.rejectedDeposits!==(merged?0:31)))throw Error('Independent deposit accounting');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runSurfacePolicy(scene,recipe,equalBytes){
 const initial=scene.snapshot(),frame=scene.render().bytes;
 scene.command({op:'surface',id:1,renderVisible:!recipe.renderVisible});
 const changed=scene.render().bytes;scene.restore(initial);
 if(equalBytes(frame,changed))throw Error('Visibility has no frame effect');
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkSurfacePolicy(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
