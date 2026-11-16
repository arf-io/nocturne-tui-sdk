export function checkSourceOptions(scene,recipe,us){
 const info=scene.infoComplete();
 if(recipe.switch==='reducedMotion'){
  const row=info.emitters.find(e=>e.id===1).atelier;
  for(const key of ['points','segments','glows'])if(row[key+'Count']!==0||row[key].length!==0)throw Error('Reduced motion primitives');
 }else{
  const row=info.windows.find(w=>w.id===1);if(row.sourceGeometry!==false)throw Error('Explicit native window geometry');
  for(const p of [0,.25,.5,1]){
   const row=scene.windowSample(1,.2,.3,p),want=[-9*65536,4*65536,0,p*1e6,1];
   if(row.some((v,i)=>v!==want[i]))throw Error('Independent native fade geometry');
  }
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runSourceOptions(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkSourceOptions(scene,recipe,us);frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}return {frames};
}
