export function checkWindowPolicy(scene,recipe,us){
 const info=scene.infoComplete(),w=info.windows.find(w=>w.id===1),action=recipe.windowAction;
 const text=Array.from({length:90},(_,i)=>'Document row '+i).join('\n');
 if(!w||w.text!==text||info.prompt.text!=='Window policy draft')throw Error('Retained source');
 const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 if(action==='summon'&&!eq(w.position,[0,0,2]))throw Error('Summon pose');
 if(action==='visit'&&!eq(info.camera.position,[4,2,37]))throw Error('Visit camera');
 if(['roll-up','roll-down'].includes(action)&&us>=750000&&w.visible!==(action==='roll-up'?0:1))throw Error('Roll target');
 if(['page-next','page-prev'].includes(action)&&(!w.reader||w.scrollRow!==(action==='page-next'?36:0)))throw Error('Reader page');
}
export function runWindowPolicy(scene,recipe,equalBytes){
 scene.advanceTo(250000);scene.command(recipe.actions[0].command);const frames=[];
 for(const us of [250000,750000,1000000]){
  scene.advanceTo(us);const pure=scene.snapshot();frames.push(scene.render().bytes);checkWindowPolicy(scene,recipe,us);
  if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');
 }
 return {frames};
}
