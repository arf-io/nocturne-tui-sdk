export function checkEndPolicy(scene,recipe,time,cohort){
 const particles=scene.particles();
 const expected=time<750000||recipe.style==='drain'?32:0;
 if(time>0&&particles.length!==expected)throw Error('Ending deadline/cohort '+time);
 if(time===375000){
  if(JSON.stringify(particles.map(p=>p[0]))!==JSON.stringify(cohort.map(p=>p[0])))throw Error('Particle identities');
  if(recipe.style==='quench'&&JSON.stringify(particles.map(p=>p.slice(6,9)))!==JSON.stringify(cohort.map(p=>p.slice(6,9))))throw Error('Quench momentum');
 }
 if(scene.infoComplete().prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runEndPolicy(scene,recipe,equalBytes){
 const frames=[];let cohort;
 for(const time of recipe.sampleTimesUs){
  scene.advanceTo(time);
  if(time===250000){cohort=scene.particles();if(cohort.length!==32)throw Error('Authored cohort');scene.command(recipe.endCommand);
   if(JSON.stringify(scene.particles())!==JSON.stringify(cohort))throw Error('Immediate ending changed cohort');}
  if(time===375000){const before=scene.snapshot();scene.command(recipe.endCommand);
   if(!equalBytes(before,scene.snapshot()))throw Error('Repeated ending changed deadline/source');}
  checkEndPolicy(scene,recipe,time,cohort);const pure=scene.snapshot();frames.push(scene.render().bytes);scene.infoComplete();
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query purity');
 }
 return {frames,cohort};
}
