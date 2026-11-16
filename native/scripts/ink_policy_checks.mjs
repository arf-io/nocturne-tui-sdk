export function checkInkPolicy(scene,recipe,equalBytes){
 const pure=scene.snapshot();scene.command({op:'remove-character-rule',id:'space-ink'});
 const baseline=scene.render(),expected=baseline.bytes.slice(),view=new DataView(expected.buffer,expected.byteOffset,expected.byteLength);let spaces=0;
 for(let x=2;x<6;x++){const offset=(2*baseline.width+x)*16;
  if(view.getUint32(offset,true)===32){spaces++;if(!recipe.inkOnly)view.setUint32(offset+4,view.getUint32(offset+4,true)^0xffffff,true);}}
 scene.restore(pure);
 if(!spaces||!equalBytes(expected,scene.render().bytes))throw Error('Independent complete space foreground oracle');
 if(scene.infoComplete().prompt.text!==recipe.expectedPrompt||!equalBytes(pure,scene.snapshot()))throw Error('Draft/query purity');
}
export function runInkPolicy(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);checkInkPolicy(scene,recipe,equalBytes);frames.push(scene.render().bytes);}
 return {frames};
}
