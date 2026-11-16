export function observatoryRandom(seed,index){
 let v=(seed^Math.imul(index+1,0x9e3779b9))>>>0;v=Math.imul(v^(v>>>16),0x7feb352d)>>>0;v=Math.imul(v^(v>>>15),0x846ca68b)>>>0;
 return ((v^(v>>>16))>>>0)/4294967296;
}
export function observatoryExpected(kind,index,t){
 const r=observatoryRandom(73,index),r2=observatoryRandom(7992,index);let x,y,glyph;
 if(kind==='rain'){x=(r-.5)*20;y=-r2*14+t*12;glyph=index%2?0x2571:0x2502;}
 else if(kind==='snow'){x=(r-.5)*24+Math.sin(2*t+r2*2*Math.PI)*2;y=-12-r2*8+t*12*.4;glyph=[0xb7,0x2219,0x22c5][index%3];}
 else if(kind==='embers'){x=(r-.5)*t*8;y=-t*12*(.2+r2*.4);glyph=0x2219;}
 else{x=Math.cos(r*2*Math.PI)*t*12*r2;y=Math.sin(r*2*Math.PI)*t*12*r2/2+2*t*t;glyph=0xb7;}
 return [index,x,y,glyph,.5*Math.max(0,1-t/2.4)**2*(.5+.5*r)];
}
export function checkObservatory(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).observatory;
 if(!row||row.profile!==recipe.profile||row.count!==28||row.samples.length!==(us<2400000?16:0))throw Error('Source profile count/lifetime');
 for(const [index,sample] of row.samples.entries()){
  const want=observatoryExpected(recipe.profile,index,us/1e6);
  if(sample.some((v,i)=>Math.abs(v-want[i])>2e-5))throw Error('Independent source equation/glyph/opacity');
 }
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runObservatory(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkObservatory(scene,recipe,us);frames.push(scene.render().bytes);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}
 return {frames};
}
