export function fieldPolicyIntensity(recipe,us,x,y){
 const age=us/1e6,distance=Math.hypot(2*(x-10),4*(y-5)),radius=recipe.continuous?0:4*age,fade=recipe.continuous?1:1-age,band=6;
 if(recipe.optics==='source'){
  let peak=0;for(let index=0;index<2;index++){const r=radius-4*band*index;if(r<0)continue;
   const p=Math.max(0,1-Math.abs(distance-r)/band);peak=Math.max(peak,(3*p*p-2*p**3)/(1+.42*index));}
  return peak*(3*fade*fade-2*fade**3)*.7;
 }
 const d=distance-radius;if(Math.abs(d)>5*band)return 0;
 const angle=((distance-4*age)/(band+.01)*100-age*90)*Math.PI/180;
 return (.2+.8*(1+Math.cos(angle))/2)*.7*fade/(1+(d/band)**2);
}
export function checkFieldPolicy(scene,recipe,us){
 for(const [x,y] of [[10,5],[12,6],[80,30]]){
  const row=scene.fieldSample(1,x,y);
  if(!recipe.continuous&&us>=1000000){if(row!==null)throw Error('Impulse expiry');continue;}
  if(!row||Math.abs(row[0]-fieldPolicyIntensity(recipe,us,x,y))>2e-6||row[2]!==10||row[3]!==5)throw Error('Independent field sample');
 }
 if(scene.infoComplete().prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runFieldPolicy(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkFieldPolicy(scene,recipe,us);
  frames.push(scene.render().bytes);scene.infoComplete();if(!equalBytes(pure,scene.snapshot()))throw Error('Query/render mutation');}
 return {frames};
}
