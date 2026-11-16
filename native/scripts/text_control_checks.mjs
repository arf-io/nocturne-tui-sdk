// Frozen original JS source boundary values, not native candidate output.
export function checkTextControls(scene,recipe,us){
 const index=recipe.sampleTimesUs.indexOf(us);if(index<0)throw Error('Unspecified source time');
 const info=scene.infoComplete(),run=info.textRuns.find(r=>r.id===1);
 if(!run||run.text!=='NODE'||info.prompt.text!==recipe.expectedPrompt)throw Error('Text/draft ownership');
 for(const [i,pose] of recipe.expectedPoses[index].entries()){
  const actual=scene.textSample(1,i);
  if(actual[0]!==pose.glyph.codePointAt(0))throw Error('Original source glyph');
  const wanted=[pose.x+10,pose.y+10,pose.alpha??pose.opacity,pose.hue??pose.hueDelta];
  const measured=[actual[3]/65536,actual[4]/65536,actual[5]/1e6,actual[6]/1000];
  for(let j=0;j<4;j++)if(Math.abs(measured[j]-wanted[j])>.0012)throw Error(`Source control pose ${i}/${j}: ${measured[j]} != ${wanted[j]}`);
 }
}
export function runTextControls(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkTextControls(scene,recipe,us);frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}return {frames};
}
