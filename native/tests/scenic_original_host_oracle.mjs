// Independent original Workbench model + original embedded WorldEngine WASM.
// No current painter is imported into the expected result. All comparisons are in memory.
import fs from 'node:fs';import zlib from 'node:zlib';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {RestorationModel,SCENIC_WORLD} from '../../bindings/continuity/restoration-model.js';
import {WorldEngine} from '../../bindings/continuity/world.js';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
import {ScenicOriginalSession} from '../bindings/typescript/scenic_original.mjs';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const html=zlib.gunzipSync(fs.readFileSync(new URL('./fixtures/original-rc2-workbench-docs.html.gz',import.meta.url))).toString();
const wasm=Buffer.from(html.match(/"wasm"\s*:\s*"([A-Za-z0-9+/=]+)"/)[1],'base64');assert.equal(hash(wasm),'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09');const world=await WorldEngine.create(wasm);
const recipes=JSON.parse(fs.readFileSync(0,'utf8')),rows=[];
for(const recipe of recipes){
 const model=new RestorationModel();model.resize(160,52);model.setScene(recipe.provenance.sourceIdentity.slice(6));
 const native=await NativeScene.create(fs.readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)));try{for(const c of recipe.commands)native.command(c);const controller=new ScenicOriginalSession(native,recipe.originalScenic),steps=[];
 for(const [at,patch,view] of [[0,{}],[425,{}],[1700,{landscapeSpeed:37,waterFlow:1.6}],[1901,{}],[2301,{waterFlow:0}],[3000,{}],[3501,{waterFlow:.35,landscapeSpeed:0}],[4600,{}],[5000,{landscapeSpeed:160,waterFlow:2}],[9999,{}],[11000,{}, {cameraX:0,cameraY:18,cameraZ:-110,yaw:0,pitch:-8,roll:0,projection:0}],[12000,{}, {cameraX:-95,cameraY:10,cameraZ:-45,yaw:62,pitch:-4,roll:3,projection:0}]]){
  model.setTime(at);model.configureBH(patch);controller.advanceTo(at*1000);controller.configure(patch);if(view){model.camera.configure({x:view.cameraX,y:view.cameraY,z:view.cameraZ,yaw:view.yaw,pitch:view.pitch,roll:view.roll});model.worldView.projection=view.projection;native.command({op:'scene-art',controls:view});}
  const c=model.camera.snapshot(),bh=model.effectiveBH();
  const options={scene:SCENIC_WORLD[model.scene],width:model.width,height:model.height,cameraX:c.x,cameraY:c.y,cameraZ:c.z,yaw:c.yaw,pitch:c.pitch,roll:c.roll,fov:c.fov,...model.worldView,flow:model.scene==='waterfall'?(bh.waterFlow===0?0:1):1,travel:model.surfaceDistance.at(model.motionMs)%12000,seed:bh.worldSeed&0x7fffffff,discTilt:Math.min(85,bh.discTilt-58),background:parseInt(model.palette.background.slice(1),16)};
  const waterTime=model.scene==='waterfall'?Math.max(0,Math.round(model.waterfallPhase.at(model.motionMs)*1000)):model.motionMs;
  const expected=world.render(options,waterTime,model.worldDetail).cells;for(let i=3;i<expected.length;i+=4)expected[i]=0;const actual=native.render().cells;assert.equal(actual.length,expected.length);let bad=0,first=-1;for(let i=0;i<expected.length;i++)if(actual[i]!==expected[i]){bad++;if(first<0)first=i;}assert.equal(bad,0,recipe.originalScenic+' at '+at+' first word '+first+' actual '+actual[first]+' expected '+expected[first]+' clock '+JSON.stringify({time:native.info().clock,source:waterTime,native:native.info().sceneArt.timeMs,expectedControls:options,nativeControls:native.info().sceneArt.effective.controls}));
  const command=controller.clock.sample(at);steps.push({timeUs:at*1000,command,...(view?{view}:{}),frameSha256:hash(Buffer.from(expected.buffer,expected.byteOffset,expected.byteLength)),cells:expected.length/4});
 }
 const saved=controller.checkpoint(),before=native.render().cells.slice();controller.advanceTo(13000000);controller.restore(saved);assert.deepEqual(native.render().cells,before);rows.push({id:recipe.id,commands:recipe.commands,steps});
 }finally{native.close();}
}
console.log(JSON.stringify({originalWasmSha256:hash(wasm),cases:rows}));
