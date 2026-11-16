#!/usr/bin/env node
/** Runnable embedding example. Computes a layout, samples text/weather, injects
 * application-owned window content, then emits an ANSI snapshot. A framework
 * should consume frame.cells instead of writing competing ANSI to stdout. */
import fs from 'node:fs';
import {StudioEngine} from '../dist/typescript/studio.js';
import {AtelierModel,AtelierRenderer} from '../dist/typescript/atelier.js';
import {layoutGraph} from '../dist/typescript/spatial.js';
import {sampleText} from '../dist/typescript/text_fx.js';
import {sampleBurst} from '../dist/typescript/particles.js';
import {CellWriter} from './observatory_writer.mjs';
const engine=await StudioEngine.create(fs.readFileSync('dist/nocturne.wasm'),JSON.parse(fs.readFileSync('studio.schema.json')));
const model=new AtelierModel(),renderer=new AtelierRenderer(engine);
model.setScene('windows');model.workspace.hide(2,0);model.workspace.hide(3,0);
renderer.setWindowPainter(1,(body,timeMs)=>{
 const label='APPLICATION DATA / 67%';
 for(let x=0;x<label.length&&x<body.width;x++){body.cells[x*4]=label.codePointAt(x);body.cells[x*4+1]=0xc5d9d0;}
 const painted=engine.paint(body,timeMs,[{kind:'progress',id:100067,x:1,y:3,width:body.width-2,height:2,value:670,fg:0x9bc7b6,bg:0x283348}]);body.cells.set(painted.cells);
});
// Input/data is committed before rendering, without consulting an FPS gate.
model.setTime(2000);model.input('IMMEDIATE LOCAL INK');
const frame=renderer.render(model).frame,writer=new CellWriter(process.stdout);writer.present(frame);writer.dispose();process.stdout.write('\x1b[0m\n');
// Standalone pure APIs can be used independently of the gallery/model.
const graph=layoutGraph({nodes:[{id:'a'},{id:'b'},{id:'c'}],edges:[{source:'a',target:'c'},{source:'b',target:'c'}]},{dimensions:3});
const reveal=sampleText('HELLO','show',450,{effect:'rain',batchSize:2,staggerMs:50});
const particles=sampleBurst({id:1,x:20,y:10,atMs:0,kind:'sparks'},160);
if(graph.nodes.length!==3||reveal.length!==5||particles.segments.length===0)throw Error('Unexpected sample');
