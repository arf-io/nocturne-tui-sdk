/** Explicit reference acceptance; never called by tests/CI. Review changed hashes. */
import fs from 'node:fs';import crypto from 'node:crypto';
import {StudioEngine} from '../dist/typescript/studio.js';
import {FleetController,createDemoFleet} from '../dist/typescript/fleet.js';
if(!process.argv.includes('--accept'))throw new Error('Explicit --accept required');
const engine=await StudioEngine.create(fs.readFileSync('dist/nocturne.wasm'),JSON.parse(fs.readFileSync('studio.schema.json')));
const c=new FleetController(engine,createDemoFleet()),fixtures=[];
function save(name){const scene=c.compose(),frame=engine.render(scene.config,scene.timeMs,scene.nodes,scene.events),bytes=Buffer.from(frame.cells.buffer);fixtures.push({name,scene,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});}
c.setTime(6000);save('overview');c.openAgent('atlas');c.setTime(6280);save('half-expansion');c.setTime(6560);save('workspace');
c.send('New text emerges from the background.');save('arrival-zero');c.setTime(6820);save('arrival-half');c.setTime(7080);save('arrival-complete');c.scroll(8);save('historical-window');c.setPaused(true);c.send('Visible even while motion is held.');save('paused-data');c.setPaused(false);save('resume-keeps-ink');c.configure({readMode:true});save('reading-mode');
const fades=[];for(const age of [0,1,120,260,519,520,700,4294967295])for(const row of [-256,0,256,768,1536,2048])for(const floor of [760,1000])fades.push({args:[age,520,row,1536,floor],value:engine.inkOpacity(age,520,row,1536,floor)});
fs.writeFileSync('tests/fleet/fixtures.json',JSON.stringify({version:1,fixtures,fades},null,2)+'\n');console.log('Accepted '+fixtures.length+' scenes and '+fades.length+' opacity cases');
