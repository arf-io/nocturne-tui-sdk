// Expectations are frozen offline original-source samples, never candidate output.
export function checkTextSeed(scene,recipe,us){
 const index=recipe.sampleTimesUs.indexOf(us);if(index<0)throw Error('Unspecified source time');
 const info=scene.infoComplete(),run=info.textRuns.find(r=>r.id===1),command=recipe.commands.find(c=>c.op==='text'&&c.id===1);
 if(!run||run.seed!==command.seed||run.text!=='NODE'||run.alphabet!==command.alphabet||run.alphabetCount!==Array.from(command.alphabet).length)throw Error('Owned full source alphabet');
 for(let i=0;i<4;i++)if(scene.textSample(1,i)[0]!==recipe.expectedGlyphs[index][i])throw Error('Original extended alphabet glyph '+i);
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
export function runTextSeed(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkTextSeed(scene,recipe,us);frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}return {frames};
}
