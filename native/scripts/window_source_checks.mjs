// Geometry expectations are frozen preserved-source samples, never candidate output.
export function checkWindowSource(scene,recipe,us){
 const info=scene.infoComplete(),window=info.windows.find(w=>w.id===1);
 if(!window||!window.sourceGeometry||window.text!=='Retained content\nSource geometry animation')throw Error('Source window ownership');
 for(const sample of recipe.geometrySamples){const actual=scene.windowSample(1,sample.u,sample.v,sample.p),expected=sample.expected;
  for(let k=0;k<4;k++)if(Math.abs(actual[k]/(k===3?1e6:65536)-expected[k])>.0012)throw Error('Original window geometry '+sample.p+' '+sample.u+' '+k);}
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runWindowSource(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkWindowSource(scene,recipe,us);frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}return {frames};
}
