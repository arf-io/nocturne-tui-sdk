// The v0.1 page itself as the oracle: its embedded WebAssembly kernel, its
// NocturneEngine class, SCHEMA, PRESETS and presetConfig, evaluated verbatim
// from legacy/editions/0.1-Nocturne-Gallery.html. The page's control handlers
// are applied exactly as written there:
//   modal:     config.values.layout=2;config.values.modalOpen=1-config.values.modalOpen
//   selection: config.values.layout=2;config.values.selection=(config.values.selection+1)%6
//   feed:      config.values.valuePermille=Math.round(500+470*Math.sin(now/750))
// Usage: node v01_page_wasm_oracle.mjs PAGE CASES.json OUT.json
// CASES: [{preset, width, height, text, timeMs, actions:[ 'modal' | 'selection' | {feedMs} | {valuePermille} ]}]
// OUT:   [{values:{...final page config values}, palette, starPalette, frame: base64 cell words}]
import { readFileSync, writeFileSync } from 'node:fs';

const [page, casesPath, outPath] = process.argv.slice(2);
const html = readFileSync(page, 'utf8');
const between = (open, close) => {
  const start = html.indexOf(open);
  if (start < 0) throw new Error('page lacks ' + open);
  const end = html.indexOf(close, start + open.length);
  if (end < 0) throw new Error('page lacks ' + close);
  return html.slice(start + open.length, end);
};
const json = marker => {
  const start = html.indexOf(marker);
  if (start < 0) throw new Error('page lacks ' + marker);
  // The literal ends at the first top-level ';' after a balanced value.
  let depth = 0, i = start + marker.length, inString = false;
  for (; i < html.length; i++) {
    const c = html[i];
    if (inString) { if (c === '\\') i++; else if (c === '"') inString = false; continue; }
    if (c === '"') inString = true; else if (c === '{' || c === '[') depth++; else if (c === '}' || c === ']') { depth--; if (!depth) break; }
  }
  return JSON.parse(html.slice(start + marker.length, i + 1));
};
const engineSource = between('<script type="module">', '\nfunction toAnsi');
const NocturneEngine = new Function(engineSource + '\nreturn NocturneEngine;')();
const SCHEMA = json('const SCHEMA=');
const PRESETS = json('const PRESETS=');
const wasm = Buffer.from(between("const WASM_BASE64='", "'"), 'base64');
const engine = await NocturneEngine.create(wasm, SCHEMA);
const presetConfig = new Function('engine', 'return ' + 'function presetConfig' + between('\nfunction presetConfig', '\n}') + '\n}')(engine);

const out = [];
for (const item of JSON.parse(readFileSync(casesPath, 'utf8'))) {
  const preset = PRESETS.find(p => p.id === item.preset);
  if (!preset) throw new Error('unknown preset ' + item.preset);
  const config = presetConfig(preset, item.width, item.height);
  for (const action of item.actions || []) {
    if (action === 'modal') { config.values.layout = 2; config.values.modalOpen = 1 - config.values.modalOpen; }
    else if (action === 'selection') { config.values.layout = 2; config.values.selection = (config.values.selection + 1) % 6; }
    else if (action && Number.isFinite(action.feedMs)) config.values.valuePermille = Math.round(500 + 470 * Math.sin(action.feedMs / 750));
    else if (action && Number.isInteger(action.valuePermille)) config.values.valuePermille = action.valuePermille;
    else throw new Error('unknown action ' + JSON.stringify(action));
  }
  const frame = engine.render(config, item.timeMs, item.text);
  out.push({ values: config.values, palette: config.palette, starPalette: config.starPalette,
    frame: Buffer.from(frame.cells.buffer, frame.cells.byteOffset, frame.cells.byteLength).toString('base64') });
}
writeFileSync(outPath, JSON.stringify(out));
