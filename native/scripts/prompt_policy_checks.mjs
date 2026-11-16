export function checkPromptPolicy(scene,recipe){
 const info=scene.infoComplete(),p=info.prompt;
 if(p.layout!==recipe.layout||p.direction!==(recipe.direction||'ltr')||p.ambiguousWidth!==recipe.ambiguousWidth||info.accessibility.screenReader!==recipe.screenReader)throw Error('Prompt policy metadata');
 if(p.text!=='AéX🙂Z'||p.caret!==4)throw Error('Logical scalar editing');
 const rows=scene.promptVisualLayout();
 if(Boolean(rows.length)!==(recipe.layout!=='scalar'))throw Error('Visual cluster policy');
}
export function runPromptPolicy(scene,recipe,equalBytes){
 const frames=[];
 for(const [i,action] of recipe.actions.entries()){
  scene.advanceTo(action.timeUs);scene.command(action.command);
  const p=scene.infoComplete().prompt;
  if(p.caret!==[4,3,4][i]||p.text!==['Aé🙂Z','Aé🙂Z','AéX🙂Z'][i])throw Error('Independent logical source offsets');
  const pure=scene.snapshot();frames.push(scene.render().bytes);scene.promptVisualLayout();
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');
 }
 scene.advanceTo(1000000);checkPromptPolicy(scene,recipe);
 const pure=scene.snapshot();frames.push(scene.render().bytes);
 if(!equalBytes(pure,scene.snapshot()))throw Error('Final render mutation');
 return {frames};
}
