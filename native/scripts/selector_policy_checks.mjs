export function checkSelectorPolicy(scene,recipe,expected,oracle,equalBytes){
 const info=scene.infoComplete(),row=info.registeredStates.find(r=>r.id===21);
 if(row.authored[recipe.property]!==recipe.baseValue||row.effective[recipe.property]!==expected)throw Error('Authored/effective property');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
 if(oracle&&!equalBytes(scene.render().bytes,oracle.render().bytes))throw Error('Independent public resource frame');
}
export function runSelectorPolicy(scene,oracle,recipe,equalBytes){
 const frames=[];
 if(oracle)oracle.command(recipe.oracleEdit);
 checkSelectorPolicy(scene,recipe,recipe.targetValue,oracle,equalBytes);
 frames.push(scene.render().bytes);
 for(const action of recipe.actions){
  scene.advanceTo(action.timeUs);if(oracle)oracle.advanceTo(action.timeUs);
  if(action.command.op==='pointer')scene.render();scene.command(action.command);
  if(oracle)for(const command of action.oracleCommands){if(command.op==='pointer')oracle.render();oracle.command(command);}
  checkSelectorPolicy(scene,recipe,action.expectedEffective,oracle,equalBytes);
  frames.push(scene.render().bytes);
  const pure=scene.snapshot();scene.render();scene.infoComplete();if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query purity');
 }
 return {frames};
}
