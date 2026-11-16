export function checkPresentationPolicy(scene,recipe,phase,beforeFrame,equalBytes){
 const info=scene.infoComplete();
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
 if(recipe.kind==='replay'&&phase==='action'){
  const widget=info.widgets.find(w=>w.id===1);
  if(widget.plot.revealAtUs!==(recipe.policy?500000:0))throw Error('Reveal epoch');
  const same=equalBytes(beforeFrame,scene.render().bytes);
  if(same===recipe.policy)throw Error('Reveal geometry restart/preserve');
 }
 if(recipe.kind==='border'&&phase==='final'){
  scene.render();const glyph=scene.inspectCharacterCell(2,1).glyph;
  const corners={rounded:0x256d,square:0x250c,double:0x2554,heavy:0x250f};
  if(recipe.policy==='none'?Object.values(corners).includes(glyph):glyph!==corners[recipe.policy])throw Error('Visible corner glyph');
  const window=info.windows.find(w=>w.id===1);
  if(window.title!=='Border policy'||window.text!=='Retained border document')throw Error('Window document ownership');
 }
}
