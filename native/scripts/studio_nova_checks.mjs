// Independent integer oracle from retained Studio C equations; no legacy dispatch.
function smooth(p){p=Math.max(0,Math.min(1000,p));return Math.floor(p*p*(3000-2*p)/1000000);}
function mix(a,b,p){let out=0;for(const shift of [0,8,16]){const aa=(a>>>shift)&255,bb=(b>>>shift)&255;out|=(aa+Math.trunc((bb-aa)*p/1000))<<shift;}return out>>>0;}
function paletteColor(phase,colors){if(colors.length===1)return colors[0];const p=((phase%1024)+1024)%1024*colors.length,index=Math.floor(p/1024),f=smooth(Math.floor((p%1024)*1000/1024));return mix(colors[index],colors[(index+1)%colors.length],f);}
export function checkStudioNova(scene,recipe,us){
 const info=scene.infoComplete(),row=info.emitters.find(e=>e.id===1).studioNova,c=recipe.commands.find(c=>c.op==='studio-style'),age=Math.floor(us/1000),glyphs=Array.from(c.glyphs);
 if(!row||row.elapsedUs!==us)throw Error('Studio ownership/epoch');
 let envelope=0,index=0,glyph=0;if(age<c.novaDurationMs){const phase=Math.floor(age*1000/c.novaDurationMs);envelope=smooth(phase<240?Math.floor(phase*1000/240):Math.floor((1000-phase)*1000/760));index=Math.floor(envelope*(glyphs.length-1)/1000);glyph=glyphs[index].codePointAt(0);}
 if(row.envelope!==envelope||row.glyphIndex!==index||row.glyph!==glyph||row.coreColor!==c.starPalette[c.seed%c.starPalette.length])throw Error('Integer source core');
 if(row.radialSamples.length!==16)throw Error('Integer radial sample capacity');
 for(const [i,actual] of row.radialSamples.entries()){
  const distance=i*256,radius=Math.floor(age*c.rippleSpeed/1000),fade=smooth(1000-Math.floor(age*1000/c.novaDurationMs));let peak=0;
  if(age<c.novaDurationMs)for(let k=0;k<c.rippleRings;k++){
   const r=radius-k*c.rippleWidth*4;if(r<0)continue;const delta=Math.abs(distance-r);
   if(delta<c.rippleWidth){let a=smooth(1000-Math.floor(delta*1000/c.rippleWidth));a=Math.floor(a*fade/1000);a=Math.floor(a*c.strength/1000);a=Math.floor(a*c.rippleOpacity/1000);a=Math.floor(a*1000/(1000+k*420));peak=Math.max(peak,a);}
  }
  const color=paletteColor(c.seed%1024+Math.floor(distance*1024/c.waveScale),c.palette);
  if(actual[0]!==distance||actual[1]!==peak||actual[2]!==color)throw Error('Integer source radial samples '+i);
 }
 for(const key of ['seed','novaDurationMs','rippleSpeed','rippleWidth','rippleOpacity','rippleRings','cellAspect','strength','waveScale','glyphs'])if(row.controls[key]!==c[key])throw Error('Studio control '+key);
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runStudioNova(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkStudioNova(scene,recipe,us);frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}return {frames};
}
