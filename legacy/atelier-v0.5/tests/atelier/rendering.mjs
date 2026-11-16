import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
import {StudioEngine} from '../../dist/typescript/studio.js';
import {AtelierModel,AtelierRenderer,ATELIER_SCENES,activateAtelier} from '../../dist/typescript/atelier.js';
import {WINDOW_EFFECTS,WINDOW_SHAPES} from '../../dist/typescript/window_fx.js';
import {TEXT_EFFECTS} from '../../dist/typescript/text_fx.js';
import {safeCellCodepoint} from '../../dist/typescript/cell_profile.js';
const engine=await StudioEngine.create(fs.readFileSync(new URL('../../dist/nocturne.wasm',import.meta.url)),JSON.parse(fs.readFileSync(new URL('../../studio.schema.json',import.meta.url))));const renderer=new AtelierRenderer(engine);
const hash=f=>crypto.createHash('sha256').update(new Uint8Array(f.cells.buffer,f.cells.byteOffset,f.cells.byteLength)).digest('hex');
const row=(f,y)=>Array.from({length:f.width},(_,x)=>String.fromCodePoint(f.cells[(y*f.width+x)*4])).join('');
for(const scene of ATELIER_SCENES)test('real WASM composition / '+scene.id,()=>{
 const m=new AtelierModel();m.setScene(scene.id);m.setTime(3300);m.configure({motion:false});m.input('IMMEDIATE');const a=renderer.render(m),b=renderer.render(m);assert.equal(hash(a.frame),hash(b.frame));assert.equal(a.frame.cells.length,m.width*m.height*4);
 for(let i=0;i<a.frame.cells.length;i+=4){assert.ok(a.frame.cells[i+1]<=0xffffff&&a.frame.cells[i+2]<=0xffffff);assert.equal(a.frame.cells[i],safeCellCodepoint(a.frame.cells[i]));}
 if(['warp','dag','text','weather','windows','museum','spatial-menu'].includes(scene.id))assert.ok(row(a.frame,m.height-4).includes('IMMEDIATE'));
});
test('every window effect / shape pair has finite frames and a permanent dock',()=>{
 const m=new AtelierModel();m.setScene('windows');for(const effect of WINDOW_EFFECTS)for(const shape of WINDOW_SHAPES){m.setTime(0);m.windowConfigure({effect,shape});m.workspace.show(1,0);m.workspace.hide(1,0);m.setTime(350);const out=renderer.render(m);assert.ok(out.semantics.some(s=>s.id===19001));assert.ok(out.frame.cells.some((v,i)=>i%4===3&&v===19001));}assert.equal(WINDOW_EFFECTS.length*WINDOW_SHAPES.length,198);
});
test('visible six-by-two mac control pads activate, then restore from persistent dock',()=>{
 const m=new AtelierModel();m.setScene('windows');m.setTime(2000);m.workspace.hide(2,0);m.workspace.hide(3,0);const f=renderer.render(m).frame;for(let action=1;action<=4;action++){const cells=Array.from(f.cells).filter((v,i)=>i%4===3&&v===10010+action);assert.ok(cells.length>=10,'tool '+action+' has generous hit area');}
 activateAtelier(m,10011);assert.equal(m.workspace.get(1).mode,'minimized');m.setTime(5000);assert.ok(renderer.render(m).frame.cells.some((v,i)=>i%4===3&&v===19001));activateAtelier(m,19001);assert.equal(m.workspace.get(1).mode,'normal');
});
test('30 and 60 presentation paths reach the identical motion sample and full local text',()=>{
 function run(fps){const m=new AtelierModel();m.setScene('text');m.configure({fps});m.playText('show',true);for(let t=0;t<1000;t+=1000/fps)m.setTime(t);m.setTime(1000);m.input('X');return renderer.render(m).frame;}
 const a=run(30),b=run(60);/* header deliberately reports FPS; compare the material region */
 assert.deepEqual(a.cells.slice(4*a.width*4),b.cells.slice(4*b.width*4));
});
test('all text treatments preserve original semantic text and immediate draft plane',()=>{
 const m=new AtelierModel();m.setScene('text');for(const effect of TEXT_EFFECTS){m.configureText({effect});m.setDisplayText('UNMODIFIED');m.playText('show',true);m.setTime(m.motionMs+250);m.replaceDraft('LOCAL');const out=renderer.render(m);assert.equal(m.textValue,'UNMODIFIED');assert.ok(row(out.frame,m.height-4).includes('LOCAL'));}
});
test('new spatial menu camera affects pixels and stable IDs still activate',()=>{
 const m=new AtelierModel();m.setScene('spatial-menu');m.setTime(1500);const a=renderer.render(m);assert.equal(a.semantics.length,6);m.cameraCommand('right',3);const b=renderer.render(m);assert.notEqual(hash(a.frame),hash(b.frame));activateAtelier(m,23002);assert.equal(m.scene,'dag');
});
test('geometry extremes and wide/control input are bounded without mutating content',()=>{
 for(const [w,h] of [[36,18],[80,32],[240,100]])for(const scene of ['windows','dag','warp','text']){const m=new AtelierModel();m.resize(w,h);m.setScene(scene);m.input('abc😀\u009b');m.setTime(1000);const f=renderer.render(m).frame;assert.equal(f.cells.length,w*h*4);assert.ok(m.draft.includes('😀'));for(let i=0;i<f.cells.length;i+=4)assert.equal(safeCellCodepoint(f.cells[i]),f.cells[i]);}
});
test('application window painter supplies owned content without terminal ownership',()=>{
 const r=new AtelierRenderer(engine),m=new AtelierModel();m.setScene('windows');m.setTime(1000);m.workspace.hide(2,0);m.workspace.hide(3,0);let retained;
 r.setWindowPainter(1,(body,time)=>{retained=body;for(let x=0;x<6;x++){body.cells[x*4]='CUSTOM'.codePointAt(x);body.cells[x*4+1]=0xffddaa;body.cells[x*4+3]=100001;}});
 const result=r.render(m);assert.ok(result.frame.cells.some((v,i)=>i%4===3&&v===100001));const before=hash(result.frame);retained.cells.fill(0);assert.equal(hash(result.frame),before);
 r.setWindowPainter(1,body=>{body.width=900;});assert.throws(()=>r.render(m),/geometry/);
});
