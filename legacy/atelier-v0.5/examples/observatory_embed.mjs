/** Runnable host-neutral composition. Own the event loop outside the library.
 * Run: node examples/observatory_embed.mjs > /tmp/observatory-frame.json
 */
import fs from 'node:fs';
import {StudioEngine} from '../dist/typescript/studio.js';
import {ObservatoryModel,ObservatoryRenderer} from '../dist/typescript/observatory.js';
const engine=await StudioEngine.create(
 fs.readFileSync(new URL('../dist/nocturne.wasm',import.meta.url)),
 JSON.parse(fs.readFileSync(new URL('../studio.schema.json',import.meta.url),'utf8'))
);
const model=new ObservatoryModel(),renderer=new ObservatoryRenderer(engine);
model.simulation=false;
model.configure({fps:60,lightness:.62,chroma:.14,gradientScreens:1.5,backgroundStyle:'double-axis'});
model.resize(100,34);
model.setTime(4000);
model.input('This text is visible now.'); // No time advancement or queued tick.
const first=renderer.render(model);
model.bus.bind({source:'audio.rms',target:'brightness',inputMin:0,inputMax:1,outputMin:.12,outputMax:.35,attackMs:60,releaseMs:400,ttlMs:2000});
model.ingest({source:'audio.rms',value:.3,atMs:1000,seq:1,unit:'FS',quality:'external'});
model.routeRates(1060); // Host-supplied data heartbeat, independent of FPS.
const second=renderer.render(model);
if(model.motionMs!==4000||!first.nodes.some(n=>n.text===model.draft))throw Error('Immediate-input contract failed');
process.stdout.write(JSON.stringify({version:4,width:second.frame.width,height:second.frame.height,cells:Array.from(second.frame.cells),semantics:second.semantics})+'\n');
