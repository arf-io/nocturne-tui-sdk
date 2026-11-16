export function checkDraftWeather(scene,recipe,index){
 const info=scene.infoComplete(),texts=['Aé\nB','Aé\nB','AB','A🙂B'],carets=[4,4,1,2],counts=[2,2,2,3];
 if(info.prompt.text!==texts[index]||info.prompt.caret!==carets[index]||info.fieldCount!==(recipe.emitWeather?counts[index]:0))throw Error('Independent draft scalar emission/source');
}
export function runDraftWeather(scene,recipe,equalBytes){
 const frames=[];for(const [index,action] of recipe.actions.entries()){
  scene.advanceTo(action.timeUs);scene.command(action.command);const pure=scene.snapshot();checkDraftWeather(scene,recipe,index);
  frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');
 }
 return {frames};
}
