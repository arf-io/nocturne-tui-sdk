import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(process.argv[2]??new URL('../../dist/nocturne_native.wasm',import.meta.url));
async function scene(){const s=await NativeScene.create(wasm,42);s.command({op:'resize',width:96,height:40});s.command({op:'environment',stars:0,style:'solid',background:0x101010});return s;}
function words(s){const a=s.render().cells;return Array.from({length:a.length/4},(_,i)=>Array.from(a.slice(i*4,i*4+4)));}
function leaf(s,sampling){s.command({op:'camera',position:[0,6,30],yaw:0,pitch:0,orthographic:true,span:32});s.advanceTo(500000);const before=words(s);s.command({op:'emitter',id:1,effect:'weather/autumn-drift',count:1,runningTimeMs:0,position:[0,6,0],extent:[0,0,0],velocity:[0,0,0],spread:[0,0,0],gravity:[0,0,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,tumble:[0,0,0],flutterHz:0,flutterAmount:0,sizeMin:6,sizeMax:6,deposit:false,collision:false,lifetimeMinMs:10000,lifetimeMaxMs:10000,birthFadeMs:0,veinContrast:0,surfaceAlpha:1,sampling});s.advanceTo(1000000);return words(s).filter((b,i)=>i/96>=2&&i/96<34&&b.some((v,k)=>v!==before[i][k]));}
for(const sampling of ['braille','cell','half']){const s=await scene();try{const changed=leaf(s,sampling);assert.ok(changed.length>80);if(sampling==='braille'){assert.ok(changed.some(b=>b[0]===0x28ff),'actual WASM filled blade must contain U+28FF');assert.ok(changed.every(b=>b[0]>0x2800&&b[0]<=0x28ff),'actual WASM blade must not collapse to flat cells');}else assert.ok(changed.some(b=>b[0]===(sampling==='cell'?32:0x2580)));}finally{s.close();}}
const s=await scene();try{s.command({op:'camera',position:[0,18,35],yaw:0,pitch:-25});s.command({op:'floor',visible:true,alpha:.4,sampling:'braille'});const state=s.snapshot(),before=s.infoComplete(),w=words(s),inner=[];for(let y=18;y<29;y++)for(let x=20;x<76;x++)inner.push(w[y*96+x][0]);assert.ok(inner.filter(g=>g>0x2800&&g<0x28ff).length>20,'actual WASM grid keeps partial subcell masks');assert.ok(inner.every(g=>g>0x2800&&g<=0x28ff));assert.deepEqual(s.snapshot(),state,'render remains observational');s.command({op:'floor',sampling:'half'});const half=words(s);for(let y=18;y<29;y++)for(let x=20;x<76;x++)assert.equal(half[y*96+x][0],0x2580);assert.deepEqual(s.infoComplete().camera,before.camera);assert.deepEqual(s.infoComplete().clock,before.clock);}finally{s.close();}
// Actual current WASM colors and occlusion, not only glyph-family membership.
const gapScene=await scene();try{const changed=leaf(gapScene,'braille');assert.ok(changed.every(w=>w[2]===0x101010),'leaf detail must not paint its own fill into braille gaps');gapScene.command({op:'camera',position:[0,18,35],pitch:-25,yaw:0});gapScene.command({op:'floor',visible:false});const before=words(gapScene);gapScene.command({op:'floor',visible:true,alpha:.4,sampling:'braille'});const saved=gapScene.snapshot(),after=words(gapScene),interior=before.flatMap((w,i)=>i/96>=2&&i/96<34&&w[0]===0x28ff?[i]:[]);assert.ok(interior.length>10);for(const i of interior){assert.equal(after[i][0],0x28ff,'farther floor grid must not replace leaf mask');assert.ok(Math.max(...[0,8,16].map(k=>Math.abs((after[i][1]>>>k&255)-(after[i][2]>>>k&255))))>20,'full braille must retain foreground/background gap contrast');}assert.deepEqual(gapScene.snapshot(),saved);}finally{gapScene.close();}
const landed=await scene();try{
 landed.command({op:'camera',position:[0,18,35],pitch:-25,yaw:0,orthographic:true,span:32});landed.command({op:'floor',enabled:true,visible:false,sampling:'braille'});landed.advanceTo(500000);
 landed.command({op:'emitter',id:2,effect:'weather/autumn-drift',count:1,runningTimeMs:0,position:[0,1,0],extent:[0,0,0],velocity:[0,-10,0],spread:[0,0,0],gravity:[0,-20,0],wind:[0,0,0],windVariation:[0,0,0],drag:0,lift:0,tumble:[0,0,0],flutterHz:0,flutterAmount:0,sizeMin:6,sizeMax:6,deposit:true,collision:true,lifetimeMinMs:10000,lifetimeMaxMs:10000,birthFadeMs:0,veinContrast:1,surfaceAlpha:1,sampling:'braille'});landed.advanceTo(1500000);
 const deposits=landed.infoComplete().deposits;assert.equal(deposits.length,1);assert.deepEqual(deposits[0].normal,[0,1,0]);assert.equal(deposits[0].position[1],.02);
 const before=words(landed);landed.command({op:'floor',visible:true,alpha:.4});const saved=landed.snapshot(),after=words(landed),marked=before.flatMap((w,i)=>i/96>=2&&i/96<34&&w[0]>0x2800&&w[0]<=0x28ff?[i]:[]);assert.ok(marked.length>80);for(const i of marked)assert.equal(after[i][0],before[i][0],'settled leaf silhouette must survive the floor grid');assert.deepEqual(landed.infoComplete().deposits,deposits);assert.deepEqual(landed.snapshot(),saved);
}finally{landed.close();}
const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/braille-nonbraille-preservation.json',import.meta.url),'utf8'));
const retained=gunzipSync(readFileSync(new URL('../../tests/fixtures/braille-nonbraille-preservation.frames.gz',import.meta.url)));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
async function caseFrame(kind,sampling){const q=await scene();try{if(kind==='leaf')leaf(q,sampling);else{q.command({op:'camera',position:[0,18,35],yaw:0,pitch:-25});q.command({op:'floor',visible:true,alpha:.4,sampling});}return q.render().bytes;}finally{q.close();}}
// The hybrid pins here are SUPERSEDED by the 2026-11-01 operator directive (docs/MIXED-LAYERS.md "Hybrid dictation", docs/BRAILLE.md):
// a hybrid object is encoded as its dictated class and never mixed, so a hybrid floor is the half floor and a hybrid leaf the braille leaf.
// The retained hybrid hashes and frames stay in the fixtures as evidence, unchanged, and no longer render. The hybrid cases assert that
// and the dictated class instead, as the Python twin test_braille_floor_regressions does; no hybrid hash is pinned here any more.
// This file stops at its first case, leaf/cell, on a drift that predates the directive (the RC2 Stage caption moved row 0 and the
// cell/half pins were never regenerated). The hybrid branches below and in the dense loop therefore run in the full file only once that
// separate repair lands. They have run alone against the current WASM; the repair must bring the cell/half cases up to date and keep the hybrid branches passing.
for(const [index,item] of fixture.cases.entries()){const frame=await caseFrame(item.kind,item.sampling);
 if(item.sampling!=='hybrid'){assert.equal(sha(frame),item.sha256,`${item.kind}/${item.sampling} matches retained original frame`);continue;}
 const original=retained.subarray(index*frame.length,(index+1)*frame.length),row=96*16,dictated=item.kind==='floor'?'half':'braille';
 assert.equal(sha(original),item.sha256,`${item.kind}/hybrid retained frame is intact evidence`);
 assert.notEqual(Buffer.compare(frame.subarray(2*row),original.subarray(2*row)),0,`${item.kind}/hybrid superseded frame still renders below the caption rows`);
 assert.equal(sha(frame),sha(await caseFrame(item.kind,dictated)),`${item.kind}/hybrid renders as its dictated ${dictated} frame`);}
const dense=JSON.parse(readFileSync(new URL('../../tests/fixtures/birth-sampling-historical.json',import.meta.url),'utf8'));
async function denseRun(sampling){const q=await NativeScene.create(wasm,dense.seed);try{for(const command of dense.commands)q.command({...command,sampling});q.advanceTo(dense.timeUs);return{bytes:q.render().bytes,overflow:q.info().render.fragmentOverflow};}finally{q.close();}}
for(const item of dense.cases){const q=await NativeScene.create(wasm,dense.seed);try{
 for(const command of dense.commands)q.command({...command,sampling:item.sampling});q.advanceTo(dense.timeUs);
 const saved=q.snapshot(),frame=q.render();let overflow=item.fragmentOverflow;
 if(item.sampling==='hybrid'){
  // Superseded like the fixture frames above, and like test_birth_saturation in Python: dense hybrid particles are braille objects, so the
  // frame and the render diagnostic are the braille render's (docs/BRAILLE.md records 715). The retained hash and 1199 stay in the fixture.
  const braille=await denseRun('braille');
  assert.notEqual(sha(frame.bytes),item.frameSha256,'dense hybrid superseded frame still renders');
  assert.equal(sha(frame.bytes),sha(braille.bytes),'dense hybrid renders as braille');assert.equal(braille.overflow,715);overflow=braille.overflow;
 }else assert.equal(sha(frame.bytes),item.frameSha256,`dense ${item.sampling} matches actual historical C writer`);
 assert.equal(q.info().render.fragmentOverflow,overflow);assert.deepEqual(q.info().particles,item.particles);assert.deepEqual(q.snapshot(),saved);
 assert.deepEqual(q.render().bytes,frame.bytes);assert.equal(q.info().render.fragmentOverflow,overflow);
}finally{q.close();}}
console.log('PASS actual WASM full braille leaf, dense historical cell/half frames and superseded hybrid frames and overflow, detailed floor and render purity');
