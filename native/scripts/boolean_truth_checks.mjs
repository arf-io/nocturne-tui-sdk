export function checkBooleanTruth(scene,recipe){
 const info=scene.infoComplete();
 if(info.values['/truth/out']!==recipe.expectedOut||info.values['/truth/probe']!==recipe.expectedProbe)throw Error('Strict Boolean result');
 const widget=info.widgets.find(w=>w.id===1),state=info.registeredStates.find(r=>r.id===21);
 if(widget.selected!==recipe.expectedOut||widget.alpha!==.2||state.effective.alpha!==recipe.expectedAlpha)throw Error('Authored/effective ownership');
 if(recipe.consumer==='trigger-guard'){
  if(info.triggers[0].lastIntent!==(recipe.truth?1:0)||info.intents.length!==1||info.intents[0].payload!==false)throw Error('Event guard/ownership');
 }
 scene.render();if(scene.inspectCharacterCell(9,12).glyph!==(recipe.expectedOut?120:32))throw Error('Visible Boolean glyph');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runBooleanTruth(scene,recipe,equalBytes){
 for(const action of recipe.actions){scene.advanceTo(action.timeUs);scene.command(action.command);}
 checkBooleanTruth(scene,recipe);const frames=[];
 for(const us of [250000,750000]){scene.advanceTo(us);const pure=scene.snapshot();frames.push(scene.render().bytes);scene.infoComplete();
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query purity');}
 return {frames};
}
