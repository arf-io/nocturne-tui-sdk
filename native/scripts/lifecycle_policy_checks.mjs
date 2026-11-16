export function checkLifecyclePolicy(scene,recipe,original){
 const info=scene.infoComplete(),reset=recipe.policy.startsWith('reset');
 if(info.prompt.text!==(recipe.policy==='reset-discard'?'':'Retained lifecycle draft')||info.prompt.caret!==(recipe.policy==='reset-discard'?0:7))throw Error('Reset prompt preservation');
 const clearGraph=reset||recipe.policy==='clear-graph',clearText=reset||recipe.policy==='clear-text';
 if(info.nodes.length!==(clearGraph?0:2)||info.graph.edges.length!==(clearGraph?0:1))throw Error('Selective graph retention');
 if(JSON.stringify(info.textRuns)!==JSON.stringify(clearText?[]:original.textRuns))throw Error('Selective text retention');
 const authored=rows=>rows.map(w=>[w.id,w.title,w.text,w.width,w.height]);
 if(JSON.stringify(authored(info.windows))!==JSON.stringify(reset?[]:authored(original.windows)))throw Error('Unrelated window retention');
}
export function runLifecyclePolicy(scene,recipe,equalBytes){
 const original=scene.infoComplete();
 if(original.nodes.length!==2||!original.textRuns.some(t=>t.id===1))throw Error('Initial resources');
 scene.advanceTo(250000);scene.command(recipe.actions[0].command);
 checkLifecyclePolicy(scene,recipe,original);const frames=[];
 for(const us of [250000,750000]){
  scene.advanceTo(us);const pure=scene.snapshot();frames.push(scene.render().bytes);scene.infoComplete();
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');
 }
 return {frames,original};
}
