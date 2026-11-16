import assert from 'node:assert/strict';
import {parentPort,workerData,threadId} from 'node:worker_threads';
import {createHash} from 'node:crypto';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
import {decodeGalleryModel,verifyGalleryModel} from '../bindings/typescript/gallery_resources.mjs';
const scene=await NativeScene.create(workerData.wasm);
function checkLedgers(info,checks){
 const near=(a,b)=>assert.ok(Math.abs(a-b)<=1e-5,`ledger ${a} versus ${b}`);
 for(const check of checks){
  if(check.kind==='water'){
   const water=info.surfaceWater.find(w=>w.surfaceId===check.surfaceId);assert.ok(water.receivedVolume>0);
   near(water.receivedVolume+water.importedVolume,water.retainedVolume+water.evaporatedVolume+water.exportedVolume+water.transferredVolume);
   const spray=info.flowSprays[0];near(spray.receivedVolume,spray.emittedVolume+spray.pendingVolume);
   near(spray.flowReceivedVolume,water.retainedVolume+water.evaporatedVolume+water.exportedVolume+spray.liveVolume+spray.expiredVolume+spray.exportedVolume+spray.pendingVolume+spray.legacyUnresolvedVolume);
  }else if(check.kind==='thermal'){
   const cells=info.surfaceThermal.cells;assert.ok(cells.some(c=>c.importedEnergy>0));
   for(const c of cells)near(c.energy,c.initialEnergy+c.appliedEnergy+c.environmentEnergy+c.importedEnergy-c.transferredEnergy);
   near(cells.reduce((s,c)=>s+c.importedEnergy,0),cells.reduce((s,c)=>s+c.transferredEnergy,0));
  }else throw Error('Unknown ledger check');
 }
}
let samples=0;
function executeAction(scene,action,study,depth=0){
 if('hostSteps' in action){assert.ok(Array.isArray(action.hostSteps)&&action.hostSteps.length>0&&action.hostSteps.length<=32&&depth<8&&action.hostSteps.every(s=>s&&typeof s==='object'&&!Array.isArray(s)),'Invalid ordered host steps');for(const step of action.hostSteps)executeAction(scene,step,study,depth+1);}
 const expectedError=action.expectedError;
 if(expectedError!==undefined)assert.ok(typeof expectedError==='string'&&expectedError.length);
 const before=action.unchanged||expectedError?scene.snapshot():null;
 if('unchangedParticles' in action)assert.equal(typeof action.unchangedParticles,'boolean','Invalid action particle preservation');
 const particlesBefore=action.unchangedParticles?scene.particles():null;
 const targetsBefore=action.expectedNodeTargetsChanged?new Map(scene.info().nodes.map(n=>[n.id,n.targetPosition])):null;
 let failure=null;try{scene.command(action.command);}catch(e){failure=e;}
 if(expectedError){assert.ok(failure&&String(failure.message).includes(expectedError),`${study.id}: expected rejection`);}else if(failure)throw failure;
 if(before)assert.deepEqual(scene.snapshot(),before,`${study.id}: action mutation`);
 if(particlesBefore)assert.deepEqual(scene.particles(),particlesBefore,`${study.id}: action particle mutation`);
 for(const sample of action.expectedParticleSamples||[]){
  const tolerance='tolerance' in sample?sample.tolerance:0;assert.ok(Number.isInteger(sample.emitterId)&&Number.isInteger(sample.count)&&sample.count>=0&&Object.keys(sample).every(k=>['emitterId','count','position','velocity','tolerance'].includes(k))&&Number.isFinite(tolerance)&&tolerance>=0&&tolerance<=.01,'Invalid action particle sample');
  for(const key of ['position','velocity'])if(key in sample)assert.ok(Array.isArray(sample[key])&&sample[key].length===3&&sample[key].every(Number.isFinite),'Invalid action particle vector');
  const rows=scene.particles().filter(p=>p[1]===sample.emitterId);assert.equal(rows.length,sample.count,`${study.id}: action particle count`);
  for(const row of rows)for(const [key,start] of [['position',3],['velocity',6]])if(key in sample)assert.ok(sample[key].every((v,i)=>Math.abs(row[start+i]/65536-v)<=tolerance),`${study.id}: action particle ${key}`);
 }
 if(action.expectedDockWindows){const expected=action.expectedDockWindows;assert.ok(Array.isArray(expected)&&expected.every(v=>Number.isInteger(v)&&v>=1&&v<=65535)&&new Set(expected).size===expected.length,'Invalid action dock owners');const before=scene.snapshot(),frame=scene.render();const owners=new Set();for(let at=3;at<frame.cells.length;at+=4)if((frame.cells[at]&0xffff0000)===0x50000000)owners.add(frame.cells[at]&65535);assert.deepEqual([...owners].sort((a,b)=>a-b),[...expected].sort((a,b)=>a-b),`${study.id}: action dock owners`);assert.deepEqual(scene.snapshot(),before,`${study.id}: action dock query mutation`);}
 const info=scene.info();if(targetsBefore){for(const id of action.expectedNodeTargetsChanged){const node=info.nodes.find(n=>n.id===id);assert.ok(node&&targetsBefore.has(id)&&JSON.stringify(node.targetPosition)!==JSON.stringify(targetsBefore.get(id)),`${study.id}: action node target unchanged`);}}for(const [name,expected] of Object.entries(action.expectedCollections||{})){
  assert.ok(['messages','intents','registeredStates'].includes(name));assert.equal(info[name].length,expected.length,`${study.id}: action collection ${name}`);assert.equal(new Set(expected.map(r=>r.id)).size,expected.length,`${study.id}: action collection duplicate IDs`);
  const matches=(a,e,exact=false)=>e!==null&&typeof e==='object'&&!Array.isArray(e)?a!==null&&typeof a==='object'&&(!exact||Object.keys(a).length===Object.keys(e).length)&&Object.entries(e).every(([k,v])=>matches(a[k],v,exact||k==='payload')):Array.isArray(e)?Array.isArray(a)&&a.length===e.length&&e.every((v,i)=>matches(a[i],v,exact)):a===e;
  for(const row of expected)assert.ok(matches(info[name].find(r=>r.id===row.id),row),`${study.id}: action collection ${name}`);
 }for(const [key,value] of Object.entries(action.expectedPromptState||{}))assert.deepEqual(info.prompt[key],value,`${study.id}: action prompt ${key}`);
 if(action.expectedWindowState){const expected=action.expectedWindowState,actual=info.windows.find(w=>w.id===expected.id);assert.ok(actual,`${study.id}: action window`);for(const [k,v] of Object.entries(expected))assert.deepEqual(actual[k],v,`${study.id}: action window ${k}`);}
 if(action.expectedInputOwner!==undefined)assert.equal(info.inputOwner,action.expectedInputOwner,`${study.id}: action input owner`);
 if(action.expectedSelectedText!==undefined)assert.equal(scene.selectedText(),action.expectedSelectedText,`${study.id}: action selected text`);
 const matches=(a,e)=>e!==null&&typeof e==='object'&&!Array.isArray(e)?a!==null&&typeof a==='object'&&Object.entries(e).every(([k,v])=>matches(a[k],v)):Array.isArray(e)?Array.isArray(a)&&a.length===e.length&&e.every((v,i)=>matches(a[i],v)):a===e;
 if(action.expectedInfo)assert.ok(matches(info,action.expectedInfo),`${study.id}: action info`);
 if(action.expectedApproxInfo){const tolerance='approxTolerance' in action?action.approxTolerance:1e-5;assert.ok(typeof tolerance==='number'&&Number.isFinite(tolerance)&&tolerance>=0&&tolerance<=.01,'Invalid approximate action info tolerance');const near=(a,e)=>Array.isArray(e)?Array.isArray(a)&&a.length===e.length&&e.every((v,i)=>near(a[i],v)):e&&typeof e==='object'?a&&typeof a==='object'&&Object.entries(e).every(([k,v])=>near(a[k],v)):typeof e==='number'&&Number.isFinite(e)&&typeof a==='number'&&Number.isFinite(a)&&Math.abs(a-e)<=tolerance;assert.ok(near(info,action.expectedApproxInfo),`${study.id}: action approximate info`);}
 if(action.expectedCharacterCells){const before=scene.snapshot();scene.render();checkCharacterCells(scene,{id:study.id,expectedCharacterCells:action.expectedCharacterCells,sampleTimesUs:[]},undefined);assert.deepEqual(scene.snapshot(),before,`${study.id}: action cell query mutation`);}

 const queryBefore=action.expectedQueries?.length?scene.snapshot():null;
 for(const q of action.expectedQueries||[]){
  assert.ok(['flowThickness','surfaceTriangles','floatHull','surfaceFluid'].includes(q.kind)&&Number.isInteger(q.id)&&Object.keys(q).every(k=>['kind','id','equals','count','rows'].includes(k))&&['equals','count','rows'].filter(k=>k in q).length===1,'Invalid action query');
  const actual=scene[q.kind](q.id);
  if('rows' in q){assert.ok(q.kind==='surfaceTriangles'&&Array.isArray(q.rows)&&q.rows.every(r=>Array.isArray(r)&&r.length===12&&r.every(Number.isFinite)),'Invalid action query rows');assert.equal(actual.length,q.rows.length,`${study.id}: action query rows`);for(let i=0;i<actual.length;i++)assert.ok(actual[i].length===12&&actual[i].every((v,k)=>Math.abs(v-q.rows[i][k])<=1e-9),`${study.id}: action query row`);}
  else if('count' in q){assert.ok(q.kind==='surfaceTriangles'&&Number.isInteger(q.count)&&q.count>=0,'Invalid action query count');assert.equal(actual.length,q.count,`${study.id}: action query count`);}
  else if(q.equals===null)assert.equal(actual,null,`${study.id}: action query absent`);
  else {assert.ok(Array.isArray(q.equals)&&actual!==null&&actual.length===q.equals.length&&actual.every((v,i)=>Number.isFinite(v)&&Number.isFinite(q.equals[i])&&Math.abs(v-q.equals[i])<=1e-9),`${study.id}: action query row`);}
 }
 if(queryBefore)assert.deepEqual(scene.snapshot(),queryBefore,`${study.id}: action query mutation`);

}
function checkCharacterCells(scene,study,time){
 if(study.promptVisualExpected){assert.deepEqual(scene.promptVisualLayout().map(r=>[...r.slice(0,5),...r.slice(8)]),study.promptVisualExpected,`${study.id}: independent prompt visual`);assert.equal(scene.textRunSource(0,0),study.promptSourceExpected,`${study.id}: prompt visual source`);}
 if(study.promptLayoutExpected){assert.deepEqual(scene.promptLayout().map(r=>r.slice(0,5)),study.promptLayoutExpected,`${study.id}: independent prompt layout`);assert.equal(scene.textRunSource(0,0),study.promptSourceExpected,`${study.id}: prompt layout source`);}
 for(const check of study.cellArtSampleChecks||[]){
  if(check.timeUs!==time)continue;
  const art=(scene.info().cellArt||[]).find(item=>item.id===check.id);
  if(check.present===false){assert.equal(art,undefined,`${study.id}: removed cell-art retained`);continue;}
  assert.ok(art,`${study.id}: retained cell-art owner`);
  for(const field of ['x','y','alpha'])assert.equal(art[field],check[field],`${study.id}: cell-art ${field}`);
  for(const field of ['width','height','cells'])if(Object.hasOwn(check,field))assert.deepEqual(art[field],check[field],`${study.id}: cell-art source ${field}`);
 }
 for(const check of study.waterSampleChecks||[]){
  const expected=check.expected.find(item=>item.timeUs===time),water=scene.info().surfaceWater.find(item=>item.surfaceId===check.surfaceId);
  assert.ok(expected&&water,`${study.id}: missing authored water`);
  assert.ok(Math.abs(water.receivedVolume-expected.received)<1e-5&&Math.abs(water.retainedVolume-expected.retained)<1e-5,`${study.id}: authored water response`);
  assert.ok(Math.abs(water.receivedVolume+water.importedVolume-water.retainedVolume-water.evaporatedVolume-water.exportedVolume-water.transferredVolume)<1e-5,`${study.id}: water conservation`);
  assert.equal(water.cells.length,expected.wetness.length);water.cells.forEach((cell,i)=>assert.ok(Math.abs(cell.wetness-expected.wetness[i])<1e-5,`${study.id}: local wetness`));
 }
 for(const check of study.fluidSampleChecks||[]){
  const expected=check.expected.find(item=>item.timeUs===time),record=scene.surfaceFluid(check.surfaceId),body=scene.floatBody(check.bodyId);assert.ok(expected);
  for(const [label,row] of [['record',record],['body',body]]){assert.ok(row);assert.equal(row.length,expected[label].length);row.forEach((x,i)=>assert.ok(Math.abs(x-expected[label][i])<1e-5,`${study.id}: fluid ${label} word ${i}`));}
  assert.equal(scene.info().surfaceFluids.find(item=>item.surfaceId===check.surfaceId).active,expected.active);
  for(let k=0;k<3;k++)assert.ok(Math.abs(record[0]*record[1+k]-record[7+k]-record[10+k])<1e-5,`${study.id}: fluid momentum ledger`);
 }
 for(const check of study.angularFluidChecks||[]){
  const expected=check.expected.find(item=>item.timeUs===time),row=scene.surfaceFluidAngular(check.surfaceId),body=scene.floatHull(check.bodyId);
  assert.ok(expected&&row&&body);assert.equal(row.length,12);
  row.forEach((x,i)=>assert.ok(Math.abs(x-expected.record[i])<1e-9,`${study.id}: angular record ${i}`));
  body.slice(4,7).forEach((x,i)=>assert.ok(Math.abs(x-expected.bodyOmega[i])<1e-9,`${study.id}: body omega ${i}`));
  assert.ok(Math.abs(2*body[5]+row[0]*row[2]-2)<1e-9,`${study.id}: angular momentum`);
  assert.ok(Math.abs(body[5]**2+.5*row[0]*row[2]**2+row[10]-1)<1e-9,`${study.id}: angular energy`);
 }
 for(const check of study.surfacePoseChecks||[]){
  const expected=check.expected.find(item=>item.timeUs===time),triangles=scene.surfaceTriangles(check.surfaceId);
  assert.ok(expected);assert.equal(triangles.length,1);
  triangles[0].slice(1,10).forEach((x,i)=>assert.ok(Math.abs(x-expected.vertices[i])<1e-9,`${study.id}: rotated vertex ${i}`));
 }
 for(const check of study.hullSampleChecks||[]){
  const expected=check.expected.find(item=>item.timeUs===time);assert.ok(expected);
  for(const [label,row] of [['pose',scene.floatHull(check.id)],['body',scene.floatBody(check.id)]]){
   assert.ok(row);assert.equal(row.length,expected[label].length);row.forEach((x,i)=>assert.ok(Math.abs(x-expected[label][i])<1e-5,`${study.id}: hull ${label} word ${i}`));
  }
 }
 for(const expected of study.refinedFieldChecks||[]){if(expected.timeUs!==time)continue;const rows=scene.surfaceTriangles(1);let area=0,energy=0;for(const row of rows){const a=row.slice(1,4),b=row.slice(4,7),c=row.slice(7,10),u=b.map((x,k)=>x-a[k]),v=c.map((x,k)=>x-a[k]),cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];area+=Math.hypot(...cross)/2;energy+=scene.thermalSample(row[0])[1];}assert.equal(rows.length,expected.triangleCount,`${study.id}: refined field triangle count`);assert.ok(Math.abs(area-expected.totalArea)<1e-8,`${study.id}: refined field area`);assert.ok(Math.abs(energy-expected.totalThermalEnergy)<1e-5,`${study.id}: refined field energy`);}
 for(const expected of study.areaGeometryChecks||[]){assert.deepEqual(scene.areaGeometry(expected.id),expected.row,`${study.id}: independent area geometry`);}
 for(const expected of study.areaMessageChecks||[]){if(expected.timeUs!==time)continue;const message=scene.info().messages.find(m=>m.id===expected.id);assert.ok(message,`${study.id}: area message source`);for(const field of ['state','startUs','text'])assert.equal(message[field],expected[field],`${study.id}: independent area message epoch/source`);}
 for(const expected of study.colorFieldChecks||[]){if(expected.timeUs!==time)continue;const row=scene.fieldSample(expected.id,expected.x,expected.y);if(expected.present===false){assert.equal(row,null,`${study.id}: removed color field`);continue;}assert.ok(row&&Math.abs(row[0]-expected.intensity)<2e-6,`${study.id}: independent color field`);assert.deepEqual(row.slice(2),expected.center,`${study.id}: color field center`);if(expected.color!==undefined){const tolerance=expected.colorTolerance??0;assert.ok(Number.isInteger(tolerance)&&tolerance>=0&&tolerance<=2);for(const shift of [0,8,16])assert.ok(Math.abs(((row[1]>>>shift)&255)-((expected.color>>>shift)&255))<=tolerance,`${study.id}: independent color field color`);}}
 for(const expected of study.aggregateChecks||[]){if(expected.timeUs!==time)continue;const info=scene.info();assert.equal(info.aggregateReemittedCount,expected.reemittedCount,`${study.id}: aggregate count reemitted`);assert.equal(info.aggregateMaterials.reduce((n,r)=>n+r.count,0),expected.retainedCount,`${study.id}: aggregate count retained`);assert.equal(info.particles.born,expected.births,`${study.id}: aggregate count births`);}
 for(const expected of study.materialHeatChecks||[]){if(expected.timeUs!==time)continue;const ledger=scene.info().materialThermal;assert.ok(ledger,`${study.id}: missing material heat ledger`);
  for(const field of ['initialEnergy','liveEnergy','importedEnergy','transferredEnergy','exportedEnergy'])assert.ok(Math.abs(ledger[field]-expected[field])<1e-5,`${study.id}: material heat ledger ${field}`);
  assert.ok(Math.abs(ledger.initialEnergy+ledger.importedEnergy-ledger.liveEnergy-ledger.transferredEnergy-ledger.exportedEnergy)<1e-5,`${study.id}: conserved material heat ledger`);
  for(const [collection,label]of [['particles','particleCount'],['deposits','depositCount'],['aggregates','aggregateCount']])assert.equal(ledger[collection].length,expected[label],`${study.id}: material heat ledger ownership`);
 }
 for(const check of study.thermalSampleChecks||[]){
  const expected=check.expected.find(item=>item.timeUs===time),row=scene.thermalSample(check.triangleIndex);
  assert.ok(expected&&row,`${study.id}: missing thermal sample`);
  assert.ok(Math.abs(row[0]-expected.temperature)<1e-5,`${study.id}: thermal response oracle`);
  assert.ok(Math.abs(row[1]-(row[2]+row[3]+row[4]+row[5]-row[6]))<1e-5,`${study.id}: thermal energy conservation`);
  if(Object.hasOwn(expected,'evaporatedEnergy')){const cell=scene.info().surfaceThermal.cells.find(item=>item.triangleIndex===check.triangleIndex);assert.ok(cell&&Math.abs(cell.evaporatedEnergy-expected.evaporatedEnergy)<1e-5,`${study.id}: evaporation energy oracle`);}
  assert.equal(row[8],expected.power);assert.equal(row[9],expected.ambientTemperature);
 }
 const allowed=new Set(['glyph','foreground','background','id','index','role','state','path']);
 for(const expected of study.expectedCharacterCells??[]){
  assert.ok(expected&&typeof expected==='object'&&!Array.isArray(expected),`${study.id}: invalid character-cell expectation`);
  assert.ok(Object.keys(expected).every(key=>allowed.has(key)||['x','y','timeUs'].includes(key)));
  assert.ok(Object.keys(expected).some(key=>allowed.has(key)));
  assert.ok(Number.isInteger(expected.x)&&Number.isInteger(expected.y));
  if(Object.hasOwn(expected,'timeUs')){
   assert.ok(Number.isInteger(expected.timeUs)&&study.sampleTimesUs.includes(expected.timeUs),'Character-cell time must identify an authored sample');
   if(expected.timeUs!==time)continue;
  }
  const actual=scene.inspectCharacterCell(expected.x,expected.y);
  for(const [field,value] of Object.entries(expected)){
   if(['x','y','timeUs'].includes(field))continue;
   if(['role','state','path'].includes(field))assert.equal(typeof value,'string');
   else assert.ok(Number.isInteger(value));
   assert.ok(Object.hasOwn(actual,field));
   assert.equal(actual[field],value,`${study.id}: character cell (${expected.x},${expected.y}) ${field}`);
  }
 }
}
function executeStudy(study){
  const tolerance=study.expectedNumericTolerance??0;
  assert.ok(Number.isFinite(tolerance)&&tolerance>=0&&tolerance<=1e-6,'Invalid explicit expectation tolerance');
  const equal=(actual,expected)=>tolerance&&typeof actual==='number'&&typeof expected==='number'?Number.isFinite(actual)&&Math.abs(actual-expected)<=tolerance:actual===expected;
  const modelRecords=decodeGalleryModel(study);
  scene.command({op:'reset'});
  if(modelRecords!==null)scene.setModelRecords(modelRecords);
  for(const command of study.commands)scene.command(command);
  verifyGalleryModel(scene,study,modelRecords);
  const identityBefore=(study.textIdentityChecks||[]).map(check=>scene.textRunClusters(check.kind,check.id));
  const start=scene.snapshot();const actions=(study.actions||[]).slice().sort((a,b)=>a.timeUs-b.timeUs);let nextAction=0;
  for(const time of study.sampleTimesUs){while(nextAction<actions.length&&actions[nextAction].timeUs<=time){const action=actions[nextAction++];scene.advanceTo(action.timeUs);scene.render();executeAction(scene,action,study);}scene.advanceTo(time);const before=scene.snapshot();scene.render();checkCharacterCells(scene,study,time);for(const check of study.flowThicknessChecks||[]){let settings=check;for(const change of check.settingsTimeline||[])if(change.timeUs<=time)settings=change;const values=scene.flowThickness(check.surfaceId),geometry=scene.surfaceTriangles(check.surfaceId);assert.ok(values&&Math.abs(values[1]-values[0]/(settings.width*settings.speed))<1e-10,`${study.id}: flow depth oracle`);if(geometry.length&&check.direction){const projections=geometry.flatMap(row=>[1,4,7].map(offset=>check.direction.reduce((sum,v,k)=>sum+v*row[offset+k],0)));assert.ok(Math.abs(Math.max(...projections)-Math.min(...projections)-values[1])<1e-10,`${study.id}: sampled geometry thickness`);}assert.equal(geometry.length>0,values[1]>0,`${study.id}: flow geometry lifecycle`);assert.deepEqual(values.slice(3,5),[settings.width,settings.speed]);}assert.deepEqual(scene.snapshot(),before,`${study.id}: render mutation`);samples++;}
  const finish=scene.snapshot();
  for(const [index,check] of (study.textIdentityChecks||[]).entries()){
   const rows=scene.textRunClusters(check.kind,check.id),old=identityBefore[index];assert.equal(rows.length,check.clusters);assert.equal(scene.textRunSource(check.kind,check.id),check.source);
   assert.equal(rows[0][0],old[0][0]);assert.equal(rows.at(-1)[0],old.at(-1)[0]);assert.equal(rows[0][3],old[0][3]);assert.ok(!old.some(row=>row[0]===rows[2][0]));assert.deepEqual(scene.snapshot(),finish);
  }

  if(study.foamTransportChecks){
   const check=study.foamTransportChecks,rows=scene.surfaceFoamTransport(check.surfaceId);
   for(const r of rows)assert.ok(Math.abs(r[2]+r[5]-r[1]-r[3]-r[4]-r[6])<=1e-8*(1+r[2]+r[5]+r[6]),`${study.id}: foam cell balance`);
   assert.ok(Math.abs(rows.reduce((n,r)=>n+r[5]-r[6],0))<=1e-8*(1+rows.reduce((n,r)=>n+r[5]+r[6],0)),`${study.id}: foam transport conservation`);
   assert.equal(rows.reduce((n,r)=>n+r[5],0)>0,check.mustTransfer,`${study.id}: foam transport motion`);
   assert.deepEqual(scene.snapshot(),finish,`${study.id}: foam query mutation`);
  }
if(study.ledgerChecks?.length){checkLedgers(scene.info(),study.ledgerChecks);assert.deepEqual(scene.snapshot(),finish);}
  if(study.expectedPrompt!==undefined)assert.equal(scene.info().prompt.text,study.expectedPrompt);
  if(study.expectedValuePaths)assert.deepEqual(Object.keys(scene.info().values).sort(),study.expectedValuePaths,`${study.id}: value lifetime`);
  if(study.expectedCounts)for(const [field,count] of Object.entries(study.expectedCounts))assert.equal(scene.info()[field].length,count,`${study.id}: consumer lifetime`);
  if(study.expectedIntentIds?.length)assert.deepEqual(scene.info().intents.map(i=>i.id),study.expectedIntentIds,`${study.id}: intention retention`);
  if(study.expectedColors){const frame=scene.render();for(const expected of study.expectedColors)assert.equal(frame.cells[(expected.y*frame.width+expected.x)*4+1],expected.foreground,`${study.id}: bound color`);}
  if(study.expectedValues)for(const [path,value] of Object.entries(study.expectedValues)){const values=scene.info().values;assert.ok(Object.hasOwn(values,path),`${study.id}: missing value`);const actual=values[path];if(value!==null&&typeof value==='object')assert.deepEqual(actual,value,`${study.id}: structured value`);else assert.ok(equal(actual,value),`${study.id}: bound value`);}
  if(study.expectedCamera)for(const [field,value] of Object.entries(study.expectedCamera))assert.deepEqual(scene.info().camera[field],value,`${study.id}: bound camera`);
  for(const collection of ['Widgets','Windows','Areas'])if(study['expected'+collection]){
   const subset=(actual,expected)=>actual!==null&&typeof actual==='object'&&(!Array.isArray(expected)||(Array.isArray(actual)&&actual.length===expected.length))&&Object.entries(expected).every(([key,value])=>Object.hasOwn(actual,key)&&(value&&typeof value==='object'?subset(actual[key],value):equal(actual[key],value)));
   for(const expected of study['expected'+collection])assert.ok(scene.info()[collection.toLowerCase()].some(entry=>subset(entry,expected)),`${study.id}: retained ${collection.toLowerCase()} update`);
   assert.deepEqual(scene.snapshot(),finish);
  }
  if(study.expectedOwners){const frame=scene.render();for(const expected of study.expectedOwners){let count=0;for(let at=3;at<frame.cells.length;at+=4)if(frame.cells[at]===expected.semanticId)count++;assert.ok(count>=expected.minCells,`${study.id}: missing rendered component owner`);}}
  if(study.expectedCells){const frame=scene.render();for(const expected of study.expectedCells){const at=(expected.y*frame.width+expected.x)*4;assert.equal(frame.cells[at],expected.glyph);assert.equal(frame.cells[at+3],expected.semanticId);}}
  scene.restore(start);for(const action of actions)if(action.timeUs<=study.sampleTimesUs.at(-1)){scene.advanceTo(action.timeUs);scene.render();executeAction(scene,action,study);}scene.advanceTo(study.sampleTimesUs.at(-1));assert.deepEqual(scene.snapshot(),finish,`${study.id}: partition replay`);
}
parentPort.on('message',({index,study})=>{
 const started=performance.now(),before=samples;let row;
 try{executeStudy(study);row={id:study.id,status:'PASS',renderPure:true,partitionReplay:true};}
 catch(error){row={id:study.id,status:'FAIL',renderPure:false,partitionReplay:false,errorType:error.name,error:String(error.message)};}
 row.seconds=(performance.now()-started)/1000;row.samples=samples-before;
 parentPort.postMessage({kind:'result',index,row,samples:samples-before});
});
parentPort.postMessage({kind:'ready',threadId,wasmSha256:createHash('sha256').update(workerData.wasm).digest('hex')});
