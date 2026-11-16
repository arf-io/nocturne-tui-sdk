// Frozen original source samples are the oracle, never candidate-generated values.
export function checkTextTrails(scene,recipe,us){
 const index=recipe.sampleTimesUs.indexOf(us);if(index<0)throw Error('Unspecified source time');
 const info=scene.infoComplete(),run=info.textRuns.find(r=>r.id===1),expected=[];
 if(!run||info.prompt.text!==recipe.expectedPrompt)throw Error('Retained text/draft ownership');
 const near=(a,b)=>{if(Math.abs(a-b)>.0012)throw Error(`Source trail mismatch ${a} != ${b}`);};
 for(const [glyphIndex,pose] of recipe.expectedPoses[index].entries()){
  for(const [ordinal,trail] of pose.trail.entries()){
   const row=scene.textTrailSample(1,glyphIndex,ordinal),main=scene.textSample(1,glyphIndex);
   if(row[0]!==main[2]||row[1]!==pose.glyph.codePointAt(0)||row[2]!==ordinal+1)throw Error('Trail identity/glyph/ordinal');
   near(row[3]/65536,trail.x+10);near(row[4]/65536,trail.y+10);near(row[5]/1e6,trail.opacity);near(row[6]/1000,pose.hueDelta);
   expected.push([glyphIndex,ordinal+1,row[1],trail.x+10,trail.y+10,trail.opacity,pose.hueDelta,row[0]]);
   row[0]=0;if(scene.textTrailSample(1,glyphIndex,ordinal)[0]!==main[2])throw Error('Borrowed trail output');
  }
  let rejected=false;try{scene.textTrailSample(1,glyphIndex,pose.trail.length);}catch{rejected=true;}
  if(!rejected)throw Error('Missing trail accepted');
 }
 if(run.trailCount!==expected.length||run.trailSampleLimit!==16||run.trails.length!==Math.min(16,expected.length))throw Error('Full count/bounded metadata');
 for(const [i,row] of run.trails.entries())for(let j=0;j<8;j++)near(row[j],expected[i][j]);
 for(const args of [[0,0,0],[1,-1,0],[1,0,-1],[true,0,0],[1,0,.5]]){
  let rejected=false;try{scene.textTrailSample(...args);}catch{rejected=true;}if(!rejected)throw Error('Invalid trail input accepted');
 }
}
export function runTextTrails(scene,recipe,equalBytes){
 const frames=[];for(const us of recipe.sampleTimesUs){scene.advanceTo(us);const pure=scene.snapshot();checkTextTrails(scene,recipe,us);frames.push(scene.render().bytes);if(!equalBytes(pure,scene.snapshot()))throw Error('Render/query mutation');}return {frames};
}
