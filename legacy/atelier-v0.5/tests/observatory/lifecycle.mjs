import assert from 'node:assert/strict';
import {ObservatoryModel,editScratch,ModulationBus} from '../../dist/typescript/observatory.js';
const m=new ObservatoryModel();m.setTime(1000);m.configure({motion:false});m.receive('held ink');const watermark=m.revealThroughMs;m.configure({motion:true});m.setTime(1001);assert.equal(m.revealThroughMs,watermark);
const snapshot=JSON.stringify(m.exportState());assert.throws(()=>m.receive(null));assert.equal(JSON.stringify(m.exportState()),snapshot);
m.editor='A🌌B\nsecond';m.editorCursor=3;editScratch(m,'backspace');assert.equal(m.editor,'AB\nsecond');assert.equal(m.editorCursor,1);editScratch(m,'insert','🌌');assert.equal(m.editor,'A🌌B\nsecond');editScratch(m,'left');assert.equal(m.editorCursor,1);editScratch(m,'delete');assert.equal(m.editor,'AB\nsecond');editScratch(m,'end');assert.equal(m.editorCursor,2);editScratch(m,'down');assert.equal(m.editorCursor,5);editScratch(m,'home');assert.equal(m.editorCursor,3);
const b=new ModulationBus();b.ingest({source:'user.supplied',value:2,atMs:0,seq:1});assert.equal(b.samples.get('user.supplied').quality,'external');
console.log('Lifecycle: 12 assertions passed (reveal watermark, atomic rejection, scalar editing, source quality)');
