export function checkStatusPolicy(scene,recipe,us){
 const info=scene.infoComplete(),m=info.messages.find(m=>m.id===1);
 if(!m||m.important!==false||m.state!==(us<1000000?'active':'expired')||m.text!=='ABCDEFGHIJKLMNOPQRSTUVWXYZabcd\nABCDEFGHIJKLMNOPQRSTUVWXYZabcd')throw Error('Retained message expiry/source');
 if(us===500000){
  const index=['horizontal','horizontal-fade'].includes(recipe.statusMode)?2:['vertical','vertical-fade'].includes(recipe.statusMode)?20:0;
  scene.render();const cell=scene.inspectCharacterCell(8,8);
  if(cell.index!==index||cell.glyph!==m.text.codePointAt(index))throw Error('Independent visible scroll index');
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runStatusPolicy(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();frames.push(scene.render().bytes);checkStatusPolicy(scene,recipe,us);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Query/render mutation');}
 return {frames};
}
