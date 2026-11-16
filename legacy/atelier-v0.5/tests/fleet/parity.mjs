/** Check accepted normalized scenes and scalar opacity, without updating fixtures. */
import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import {StudioEngine} from '../../dist/typescript/studio.js';
const engine=await StudioEngine.create(fs.readFileSync('dist/nocturne.wasm'),JSON.parse(fs.readFileSync('studio.schema.json'))),corpus=JSON.parse(fs.readFileSync('tests/fleet/fixtures.json'));
for(const f of corpus.fixtures){const s=f.scene,frame=engine.render(s.config,s.timeMs,s.nodes,s.events);assert.equal(crypto.createHash('sha256').update(Buffer.from(frame.cells.buffer)).digest('hex'),f.sha256,f.name);}
for(const c of corpus.fades)assert.equal(engine.inkOpacity(...c.args),c.value);
console.log(JSON.stringify({suite:'Fleet WASM canonical parity',status:'PASS',frames:corpus.fixtures.length,opacityCases:corpus.fades.length}));
