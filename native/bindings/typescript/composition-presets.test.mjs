/**
 * RC2 preset design (scaled TDD, before implementation).
 * Authority: operator request for new composited applications; parent assigns
 * only preset module/declaration/tests. Shared model/UI/native renderers stay owned
 * by their workers. Three authored layouts reuse exact native world painters,
 * widgets, flight/sky, windows, graphs, prompt weather and source rule motion.
 * Named factories return independent editable projects. Real WASM validates every
 * command/timeline/button before adoption; no DOM artwork or static animation claims.
 * Tests below require visible retained art/components, exact snapshot+project
 * roundtrips, seed/time preservation and measured component-region animation.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
import {prepareProject,importProject,exportProject,projectPlan,projectActivation,advanceProject,componentOwner} from './composition_project.mjs';
import {PROJECT_PRESETS,createPreset} from './composition_presets.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const hash=b=>createHash('sha256').update(b).digest('hex');
let scene,replay;
test.before(async()=>{scene=await NativeScene.create(wasm);replay=await NativeScene.create(wasm);});
test.after(()=>{scene?.close();replay?.close();});
function equalBytes(a,b,label){assert.equal(a.length,b.length,label+' length');assert.equal(hash(a),hash(b),label+' bytes');}
function crop(frame,g){const parts=[];for(let y=g.y;y<g.y+g.height;y++)parts.push(frame.bytes.slice((y*frame.width+g.x)*16,(y*frame.width+g.x+g.width)*16));return Buffer.concat(parts);}
function advance(p,to){const plan=projectPlan(p);advanceProject(scene,plan.timeline,{next:0},to);}
test('three named factories produce independent editable documents',()=>{
 assert.deepEqual(PROJECT_PRESETS.map(x=>x.id),['signal-desk','flight-deck','tidal-console']);
 for(const row of PROJECT_PRESETS){const p=createPreset(row.id);assert.equal(p.name,row.name);assert.deepEqual(row.create(),p);p.elements[0].props.text='changed';assert.notDeepEqual(createPreset(row.id),p);}
 assert.throws(()=>createPreset('missing'),/Unknown/);
});
test('all presets execute native art/components and preserve full project, seed and time',()=>{
 const frameHashes=new Set();
 for(const row of PROJECT_PRESETS){
  const p=createPreset(row.id);const a=prepareProject(scene,p);const text=exportProject(p),roundtrip=importProject(text);assert.deepEqual(roundtrip,p);assert.equal(a.info.clock.timeUs,p.timeUs);assert.equal(a.info.prompt.text,p.prompt.text);
  const b=prepareProject(replay,roundtrip);equalBytes(a.snapshot,b.snapshot,row.id+' snapshot');equalBytes(a.frame.bytes,b.frame.bytes,row.id+' frame');
  const stable=scene.snapshot();scene.render();equalBytes(scene.snapshot(),stable,row.id+' render purity');
  assert(a.info.sceneArt,row.id+' retained world painter');
  const owners=new Set([...a.frame.cells].filter((v,i)=>i%4===3&&v));
  const visible=p.elements.filter(e=>owners.has(componentOwner(e.kind,e.id)));assert(visible.length>=6,row.id+' has '+visible.length+' visible owned components');for(const window of p.elements.filter(e=>e.kind==='window'))assert(owners.has(componentOwner(window.kind,window.id)),row.id+' world window is visible');
  scene.command({op:'remove-scene-art'});const noArt=scene.render();let changed=0;for(let at=0;at<a.frame.cells.length;at+=4)if(a.frame.cells[at]!==noArt.cells[at]||a.frame.cells[at+1]!==noArt.cells[at+1]||a.frame.cells[at+2]!==noArt.cells[at+2])changed++;assert(changed>120,row.id+' original artwork visibly contributes');
  const different=structuredClone(p);different.seed++;assert.notEqual(hash(prepareProject(replay,different).snapshot),hash(a.snapshot),row.id+' seed reaches actual native state');
  frameHashes.add(hash(a.frame.bytes));
 }
 assert.equal(frameHashes.size,3,'Three materially distinct native frames');
});
test('Signal Desk chart and waiting rule animate beyond cursor changes',()=>{
 const p=createPreset('signal-desk');prepareProject(scene,p);const before=scene.render(),chart=p.elements.find(e=>e.name==='Signal history'),waiting=p.elements.find(e=>e.name==='Reception');
 advance(p,1800000);const after=scene.render();assert.notEqual(hash(crop(before,chart.geometry)),hash(crop(after,chart.geometry)));assert.notEqual(hash(crop(before,waiting.geometry)),hash(crop(after,waiting.geometry)));
 assert.notDeepEqual(scene.infoComplete().widgets.find(w=>w.id===chart.id).data,chart.props.data);
});
test('Flight Deck retains moving camera, visible world window and source sky trails',()=>{
 const p=createPreset('flight-deck');const initial=prepareProject(scene,p);const before=initial.info.camera.position;advance(p,2300000);const after=scene.infoComplete();
 assert.notDeepEqual(after.camera.position,before);assert.notEqual(hash(scene.render().bytes),hash(initial.frame.bytes));
 assert(after.windows.some(w=>w.id===p.elements.find(e=>e.kind==='window').id));
 const sky=scene.render().bytes.slice();scene.command({op:'environment',starProfile:'default',stars:0});assert.notEqual(hash(scene.render().bytes),hash(sky),'Source sky contributes visible pixels');
});
test('Tidal Console keeps the original water animated under its panels and graph',()=>{
 const p=createPreset('tidal-console');const a=prepareProject(scene,p);assert.equal(a.info.sceneArt.scene,'tidal-glass');assert(a.info.nodes.length>=2);assert(a.info.windows.length);
 advance(p,2400000);const b=scene.render();assert.notEqual(hash(a.frame.bytes),hash(b.bytes));
 const same=structuredClone(p);same.timeUs=2400000;equalBytes(prepareProject(replay,same).frame.bytes,b.bytes,'timeline seek equals forward replay');
});
test('every application button executes real native commands with visible pressed state',()=>{
 for(const row of PROJECT_PRESETS){const p=createPreset(row.id);prepareProject(scene,p);const button=p.elements.find(e=>e.kind==='button');assert(button?.events.activate.length);const before=scene.render().bytes.slice();scene.command(projectActivation(p,button.id));const info=scene.infoComplete();assert.equal(info.widgets.find(w=>w.id===button.id).active,true);assert.notEqual(hash(scene.render().bytes),hash(before),row.id+' activation changes native frame');}
});
test('configured prompt typing weather actually changes the composed output',()=>{
 const p=createPreset('flight-deck');prepareProject(scene,p);const off=structuredClone(p);off.prompt.appearance.weather.style='off';prepareProject(replay,off);
 for(const s of [scene,replay]){s.command({op:'input',text:'READY 文'});while(s.advanceTo(p.timeUs+150000)){}}
 assert.equal(scene.infoComplete().prompt.text,replay.infoComplete().prompt.text);assert.notEqual(hash(scene.render().bytes),hash(replay.render().bytes));
});

test('application controls and both survey nodes retain visible labels',()=>{
 for(const row of PROJECT_PRESETS){const p=createPreset(row.id),frame=prepareProject(scene,p).frame;const button=p.elements.find(e=>e.kind==='button');const glyphs=[...frame.cells].filter((v,i)=>i%4===0&&frame.cells[i+3]===componentOwner(button.kind,button.id));const label=String.fromCodePoint(...glyphs);assert(label.includes(button.props.text),row.id+' visible button label: '+label);if(row.id==='tidal-console')for(const node of p.elements.filter(e=>e.kind==='graph-node')){const text=String.fromCodePoint(...[...frame.cells].filter((v,i)=>i%4===0&&frame.cells[i+3]===componentOwner(node.kind,node.id)));assert(text.includes(node.props.label),node.name+' visible label: '+text);}}
});
