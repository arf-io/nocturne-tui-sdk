import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { NativeScene } from '../bindings/typescript/native_scene.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = resolve(root, 'evidence/original-scenic-restoration-20261013/ORIGINAL-WORLD-FRAMES.json');
const evidenceRoot = dirname(manifestPath);
const output = resolve(process.argv[2] ?? resolve(root, 'tests/scenic-wasm-output'));
const wasmPath = resolve(root, 'dist/nocturne_native.wasm');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const worldFields = ['width','height','scene','cameraX','cameraY','cameraZ','yaw','pitch','roll','fov','projection','span','flow','travel','seed','redshift','discTilt','detail','waterAlpha','background','ink','accent','secondary','sampling'];
const worldScale = {cameraX:256,cameraY:256,cameraZ:256,yaw:256,pitch:256,roll:256,fov:256,projection:1,span:256,flow:1000,travel:256,seed:1,redshift:1000,discTilt:256,detail:1,waterAlpha:1000,background:1,ink:1,accent:1,secondary:1,sampling:1};
const detailFields = ['waveHeight','wavelength','windAngle','crossSwell','choppiness','foam','waveSpeed','joinRiver'];
const detailScale = [256,256,256,1000,1000,1000,1000,1];
const sceneNames = ['pearl-cascade','copper-causeway','red-shift','tidal-glass','silt'];
const writerProbe = await NativeScene.create(readFileSync(wasmPath),2030);
const currentSchema = new DataView(writerProbe.snapshot().buffer).getUint32(12,true);writerProbe.close();
assert.ok(currentSchema>=0x20261068,'scenic/canvas writer contract required');

function scenicCommand(frame) {
  const source = Object.fromEntries(worldFields.map((name, index) => [name, frame.worldQ[index]]));
  const controls = Object.fromEntries(Object.entries(worldScale).map(([name, scale]) => [name, source[name] / scale]));
  const detail = Object.fromEntries(detailFields.map((name, index) => [name, frame.detailQ[index] / detailScale[index]]));
  return {op:'scene-art',scene:sceneNames[source.scene],width:frame.width,height:frame.height,controls,detail};
}

function isolate(scene, frame) {
  scene.command({op:'environment',presentation:'canvas',stars:0,background:frame.worldQ[19],sampling:frame.worldQ[23]?'braille':'half',style:'solid'});
  scene.command({op:'prompt',active:false});
  scene.command({op:'floor',enabled:false,visible:false});
}

function packedWords(bytes) { return new Uint32Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/4); }
function rgbTuple(bytes) {
  const words=packedWords(bytes), result=[];
  for(let i=0;i<words.length;i+=4)result.push(words[i],words[i+1],words[i+2]);
  return result;
}
function saveCells(name, bytes) {
  const cellsFile=`${name}.cells`;
  writeFileSync(resolve(output,cellsFile),Buffer.from(bytes));
  return cellsFile;
}
function countRgb(bytes,rgb) {
  const words=packedWords(bytes);let n=0;
  for(let i=0;i<words.length;i+=4)if(words[i+1]===rgb||words[i+2]===rgb)n++;
  return n;
}
function assertSchema(info) {
  assert.equal(info.contract.snapshotSchema,currentSchema,'artifact metadata disagrees with actual writer');
  assert.equal(info.contract.sourceSchema,currentSchema,'state metadata disagrees with actual writer');
}

async function renderOriginalFrames(wasm,errors) {
  const rows=[];
  for(const fixture of manifest.frames){
    let scene;
    try {
      scene=await NativeScene.create(wasm,2030);
      isolate(scene,fixture);
      scene.command(scenicCommand(fixture));
      scene.advanceTo(fixture.timeMs*1000);
      const frame=scene.render();
      const expected=readFileSync(resolve(evidenceRoot,fixture.cellsFile));
      const check=(label,fn)=>{try{fn();}catch(error){errors.push({id:fixture.id,check:label,message:error.message});}};
      check('dimensions',()=>assert.deepEqual([frame.width,frame.height],[fixture.width,fixture.height]));
      check('fixture custody hash',()=>assert.equal(createHash('sha256').update(expected).digest('hex'),fixture.cellsSha256));
      check('RC2 glyph/FG/BG',()=>assert.deepEqual(rgbTuple(frame.bytes),rgbTuple(expected)));
      const words=packedWords(frame.bytes);
      check('source-only hit IDs',()=>{for(let i=3;i<words.length;i+=4)assert.equal(words[i],0);});
      const infoComplete=scene.infoComplete();
      check('current writer schema',()=>assertSchema(infoComplete));
      check('source scene',()=>assert.equal(infoComplete.sceneArt.scene,sceneNames[fixture.worldQ[2]]));
      check('authored source vector',()=>assert.deepEqual(infoComplete.sceneArt.worldQ,fixture.worldQ));
      check('authored detail vector',()=>assert.deepEqual(infoComplete.sceneArt.detailQ,fixture.detailQ));
      const cellsFile=saveCells(`original-${fixture.id}`,frame.bytes);
      rows.push({id:fixture.id,cellsFile,infoComplete});
    } catch(error) {errors.push({id:fixture.id,check:'render',message:error.message});}
    finally {scene?.close();}
  }
  return rows;
}

async function sourceScene(wasm,fixture) {
  const scene=await NativeScene.create(wasm,2030);
  isolate(scene,fixture);
  scene.command(scenicCommand(fixture));
  scene.command({op:'camera',position:[0,0,96],yaw:0,pitch:0,roll:0,fov:62,near:0.1,far:10000,orthographic:true});
  scene.command({op:'material',id:15,space:'rgb',channels:{r:1,g:0,b:1},alpha:1});
  return scene;
}

async function renderMixed(wasm,fixture) {
  const samples=[];
  {
    const scene=await sourceScene(wasm,fixture);
    try {scene.advanceTo(20000);const frame=scene.render();samples.push({id:'mixed-baseline',cellsFile:saveCells('mixed-baseline',frame.bytes)});}
    finally {scene.close();}
  }
  const triangle=(z)=>({a:[-70,-55,z],b:[70,-55,z],c:[0,70,z],color:0xff00ff,alpha:1});
  for(const [id,z] of [['mesh-near',90],['mesh-far',-1000]]){
    const scene=await sourceScene(wasm,fixture);
    try {
      scene.command({op:'mesh',sampling:'braille',triangles:[triangle(z)]});
      const frame=scene.render(),magenta=countRgb(frame.bytes,0xff00ff);
      samples.push({id,cellsFile:saveCells(id,frame.bytes),magentaCells:magenta});
    } finally {scene.close();}
  }

  const emitter=(z)=>({op:'emitter',id:1,effect:'weather/rain-threads',count:1,runningTimeMs:0,
    shape:'point',position:[0,0,z],extent:[0,0,0],velocity:[0,0,0],spread:[0,0,0],
    gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,
    collision:false,deposit:false,sizeMin:3,sizeMax:3,lifetimeMinMs:10000,lifetimeMaxMs:10000,material:15,birthFadeMs:0,deathFadeMs:0,alpha:1});
  for(const [id,z] of [['emitter-near',90],['emitter-far',-1000]]){
    const scene=await sourceScene(wasm,fixture);
    try {
      scene.command(emitter(z));
      scene.advanceTo(20000);
      const frame=scene.render(),info=scene.infoComplete();
      assert.ok(scene.particles().length>0,`${id} must retain the authored particle`);
      const baseline=readFileSync(resolve(output,'mixed-baseline.cells'));
      const before=rgbTuple(baseline),after=rgbTuple(frame.bytes);
      let changedCells=0;for(let i=0;i<before.length;i+=3)if(before[i]!==after[i]||before[i+1]!==after[i+1]||before[i+2]!==after[i+2])changedCells++;
      samples.push({id,cellsFile:saveCells(id,frame.bytes),particles:info.particles,changedCells});
      if(id==='emitter-far'){
        scene.command({op:'remove-scene-art'});
        const exposed=scene.render();
        assert.ok(countRgb(exposed.bytes,0xff00ff)>0,'far particle must render without its source occluder');
        samples.push({id:'emitter-far-exposed',cellsFile:saveCells('emitter-far-exposed',exposed.bytes)});
      }
    } finally {scene.close();}
  }
  return samples;
}

await mkdir(output,{recursive:true});
const wasm=readFileSync(wasmPath);
const errors=[];
const wasmRows=await renderOriginalFrames(wasm,errors);
let mixed=[];
try {
  mixed=await renderMixed(wasm,manifest.frames[0]);
  const meshNear=mixed.find(row=>row.id==='mesh-near').magentaCells;
  const meshFar=mixed.find(row=>row.id==='mesh-far').magentaCells;
  if(!(meshNear>0))errors.push({id:'mesh-near',check:'known foreground projection',message:`magenta cell count ${meshNear}`});
  if(!(meshNear>meshFar))errors.push({id:'mesh-far',check:'source depth occlusion',message:`near=${meshNear} far=${meshFar}`});
  const emitterNear=mixed.find(row=>row.id==='emitter-near').changedCells;
  const emitterFar=mixed.find(row=>row.id==='emitter-far').changedCells;
  if(!(emitterNear>0))errors.push({id:'emitter-near',check:'known foreground projection',message:`changed cell count ${emitterNear}`});
  if(!(emitterNear>emitterFar))errors.push({id:'emitter-far',check:'source depth occlusion',message:`near=${emitterNear} far=${emitterFar}`});
} catch(error) {errors.push({id:'mixed',check:'mixed rendering',message:error.message});}
writeFileSync(resolve(output,'report.json'),JSON.stringify({snapshotSchema:currentSchema,sourceSchema:currentSchema,frames:wasmRows,mixed,errors},null,2));
if(errors.length)throw Error(`Scenic WASM acceptance failed; partial report written to ${resolve(output,'report.json')}: ${errors.map(e=>`${e.id} ${e.check}: ${e.message}`).join('; ')}`);
console.log(`PASS schema-67 scenic WASM: ${wasmRows.length} original frames and ${mixed.length} mixed-source cases`);
