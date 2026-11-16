export function checkCorona(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).corona;
 const envelope=us<2400000?(1-us/2400000)**2:0,glyph=us<200000?0x2219:us<430000?0x2726:us<650000?0x2727:0;
 if(!row||row.coreGlyph!==glyph||row.elapsedUs!==us||Math.abs(row.radius-12*us/1e6)>1e-6||Math.abs(row.envelope-envelope)>1e-6)throw Error('Independent corona temporal equations');
 for(const [distance,value] of row.radialSamples)if(Math.abs(value-Math.exp(-(((distance-row.radius)/1.7)**2))*.28*envelope*.65)>2e-6)throw Error('Independent Gaussian sample');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runCorona(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkCorona(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
