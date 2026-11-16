/** Run with node tests/wasm-parity.mjs. No npm dependencies. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import crypto from 'node:crypto';
import {NocturneEngine,toAnsi} from '../dist/typescript/nocturne.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const schema=JSON.parse(fs.readFileSync(path.join(root,'schema.json'),'utf8'));
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures.json'),'utf8'));
const engine=await NocturneEngine.create(fs.readFileSync(path.join(root,'dist/nocturne.wasm')),schema);
for(const fixture of fixtures){
  const config=engine.defaults(fixture.values);
  if(fixture.palette)config.palette=fixture.palette;
  if(fixture.starPalette)config.starPalette=fixture.starPalette;
  if(fixture.glyphs){config.glyphs=fixture.glyphs;config.values.glyphSet=4;}
  const frame=engine.render(config,fixture.timeMs,fixture.text);
  // Canonical bytes are explicitly little-endian, not Buffer's host layout.
  const bytes=Buffer.alloc(frame.cells.length*4);
  frame.cells.forEach((word,index)=>bytes.writeUInt32LE(word,index*4));
  const hash=crypto.createHash('sha256').update(bytes).digest('hex');
  assert.equal(hash,fixture.sha256,fixture.name);
}
const config=engine.defaults({layout:1});
const first=engine.render(config,5000,'same');
engine.render(config,7000,'other');
assert.deepEqual(first,engine.render(config,5000,'same'));
assert.notDeepEqual(first,engine.render(config,5000,'changed data'));
assert.throws(()=>engine.defaults({width:-1}));
assert.throws(()=>engine.defaults({width:999}));
assert.throws(()=>engine.defaults({width:1.25}));
assert.throws(()=>engine.defaults({unknown:123}));
assert.throws(()=>engine.render(config,NaN,'x'));
assert.throws(()=>engine.render(config,-1,'x'));
assert.throws(()=>engine.render(config,10,'x'.repeat(513)));
const bad=engine.defaults();bad.palette=['#wrong'];assert.throws(()=>engine.render(bad,0,''));
assert(!toAnsi(first).includes('?2026'));
assert(toAnsi(first,true).startsWith('\x1b[?2026h'));
console.log(JSON.stringify({passed:true,canonicalParityFixtures:fixtures.length,additionalAssertions:12},null,2));
