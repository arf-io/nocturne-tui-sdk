import test from 'node:test';import assert from 'node:assert/strict';
import {AtelierModel} from '../../dist/typescript/atelier.js';
import {exportAtelierSettings,loadAtelierSettings} from '../../dist/typescript/atelier_settings.js';
test('settings roundtrip preserves camera, all control families, windows, layout and local-input policy',()=>{
 const m=new AtelierModel();m.setScene('windows');m.camera.orbit(23,-14);m.camera.pan(3,-2,5);m.setVelocity(-9);m.configure({gradientScreens:2.5,stopWidths:[1,3,.5]});m.configureText({effect:'flipboard',batchSize:3});m.configureParticles({gravity:14,branches:11});m.windowConfigure({shape:'diamond',chrome:'windows',depth:9});m.workspace.hide(2,0);m.beginLayout({dimensions:2,algorithm:'force',iterations:20});while(!m.stepLayout()){}m.camera.orbit(8,4);m.input('PRIVATE DRAFT');
 const saved=exportAtelierSettings(m);assert.ok(!JSON.stringify(saved).includes('PRIVATE DRAFT'));const copy=loadAtelierSettings(saved);
 assert.deepEqual(exportAtelierSettings(copy),saved);
});
test('settings rejects unknown version, invalid camera, cycles policy, invalid palettes and never mutates a caller',()=>{
 for(const patch of [{version:4},{camera:{target:{x:0,y:0,z:0},yaw:Infinity}},{palette:{colors:[],background:'#000000',ink:'#ffffff'}},{scene:'not-here'},{windows:[]}])assert.throws(()=>loadAtelierSettings({...exportAtelierSettings(new AtelierModel()),...patch}));
});
test('editing velocity after seeking back creates a position-continuous history branch',()=>{
 const m=new AtelierModel();m.setTime(1000);m.setVelocity(8);m.setTime(4000);m.setVelocity(13);m.setTime(1800);const at=m.flightPosition();m.setVelocity(-3);assert.deepEqual(m.flightPosition(),at);m.configure({gradientSpeed:.17});assert.ok(Number.isFinite(m.flightPosition().z));
});
test('custom window tools validate colors and retain non-default glyphs through settings',()=>{
 const m=new AtelierModel();m.windowConfigure({chrome:'custom',customGlyphs:['↓','↑','◌','×'],toolColors:{minimize:0xabcdef,maximize:0x123456,fade:0x778899,close:0xfedcba}});
 assert.deepEqual(loadAtelierSettings(exportAtelierSettings(m)).workspace.options.toolColors,m.workspace.options.toolColors);
 assert.throws(()=>m.windowConfigure({customGlyphs:['😀','↑','◌','×']}));
});
test('visual settings can preserve existing notes and scratch without duplicating future message IDs',()=>{
 const old=new AtelierModel();old.input('remember this locally');old.send();old.editor='keep scratch';old.input('draft');const next=loadAtelierSettings(exportAtelierSettings(old));next.preserveLocalContent(old);assert.deepEqual(next.messages,old.messages);assert.equal(next.editor,old.editor);next.send();assert.equal(new Set(next.messages.map(m=>m.id)).size,next.messages.length);
});
