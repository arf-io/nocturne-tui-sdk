export function checkPointerCancel(scene,recipe,index){
 const info=scene.infoComplete(),state=info.registeredStates.find(r=>r.id===1);
 const pressed=index===0||(recipe.workflow==='recover'&&index===2);
 if(!state||state.states.pressed!==pressed||state.authored.alpha!==.2||state.effective.alpha!==(pressed?.8:.2))throw Error('Actual pressed appearance');
 if(recipe.actions[index].command.phase==='cancel'&&state.states.hover)throw Error('Cancelled hover');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runPointerCancel(scene,recipe,equalBytes){
 const frames=[];
 for(const [index,action] of recipe.actions.entries()){
  scene.advanceTo(action.timeUs);scene.render();scene.command(action.command);checkPointerCancel(scene,recipe,index);
  const pure=scene.snapshot();frames.push(scene.render().bytes);scene.infoComplete();
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');
 }
 scene.advanceTo(1000000);frames.push(scene.render().bytes);
 return {frames};
}
