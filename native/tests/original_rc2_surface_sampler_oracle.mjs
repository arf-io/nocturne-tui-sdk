import fs from 'node:fs';
import crypto from 'node:crypto';

const htmlPath = process.argv[2];
if (!htmlPath) throw new Error('exact rc.2 HTML path required');
const html = fs.readFileSync(htmlPath, 'utf8');
const editionSha256 = crypto.createHash('sha256').update(html).digest('hex');
const expectedEdition = '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385';
if (editionSha256 !== expectedEdition) throw new Error(`original edition SHA mismatch: ${editionSha256}`);
const match = html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s);
if (!match) throw new Error('original DATA record is missing');
const data = JSON.parse(match[1]);
if (data.version !== '0.9.0-rc.2' || data.schema?.configBytes !== 704) {
  throw new Error('unexpected original sampler edition/schema');
}
const wasmBytes = Buffer.from(data.wasm, 'base64');
const wasmSha256 = crypto.createHash('sha256').update(wasmBytes).digest('hex');
const instance = new WebAssembly.Instance(new WebAssembly.Module(wasmBytes), {});
const e = instance.exports;
if (e.nsStageConfigSize() !== 704 || e.nsCellSize() !== 16) throw new Error('original Wasm ABI mismatch');

const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
const memory = new DataView(e.memory.buffer);
const config = e.nsStageConfigPtr();
const output = config + 32768;
const nodesPtr = config + 65536;
const textPtr = config + 131072;
const dataPtr = config + 262144;
const fields = new Int32Array(e.memory.buffer, config, 64);
const palette = new Uint32Array(e.memory.buffer, config + 256, 32);
const starPalette = new Uint32Array(e.memory.buffer, config + 384, 32);
const glyphs = new Uint32Array(e.memory.buffer, config + 512, 32);
const novaGlyphs = new Uint32Array(e.memory.buffer, config + 640, 16);

const results = requests.map((request) => {
  e.nsStageDefaults(config);
  const values = new Int32Array(e.memory.buffer, config, 64);
  for (const [key, value] of Object.entries(request.values ?? {})) values[Number(key)] = value;
  const stops = request.palette ?? [0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565];
  values[25] = stops.length;
  const colors = new Uint32Array(e.memory.buffer, config + 256, 32);
  colors.fill(0);
  stops.forEach((color, i) => { colors[i] = color; });
  values[30] = 0; // stars off: this oracle isolates the authored surface sampler.
  values[38] = 0; // automatic novae off.
  values[21] = 0; // one center sample per terminal cell.
  values[0] = request.width;
  values[1] = request.height;
  const validation = e.nsStageValidate(config);
  if (validation !== 0) throw new Error(`original rejects oracle config at field ${validation}`);
  const nodeRows = request.nodes ?? [];
  const textValues = request.text ?? [];
  const dataValues = request.data ?? [];
  if (nodeRows.length > 512 || textValues.length > 32768 || dataValues.length > 16384)
    throw new Error('oracle scene exceeds original bounded capacities');
  const nodes = new Int32Array(e.memory.buffer, nodesPtr, nodeRows.length * 32);
  nodes.fill(0);
  nodeRows.forEach((row, index) => {
    const values = Array.isArray(row) ? row : row.values;
    if (!Array.isArray(values) || values.length !== 32)
      throw new Error('each original node must provide exactly 32 int32 fields');
    values.forEach((value, field) => { nodes[index * 32 + field] = value; });
  });
  const textData = new Uint32Array(e.memory.buffer, textPtr, textValues.length);
  textValues.forEach((value, index) => { textData[index] = value; });
  const scalarData = new Int32Array(e.memory.buffer, dataPtr, dataValues.length);
  dataValues.forEach((value, index) => { scalarData[index] = value; });
  const capacity = request.width * request.height;
  const result = e.nsStageRender(config, BigInt(request.timeMs), 0, 0,
    nodeRows.length ? nodesPtr : 0, nodeRows.length,
    textValues.length ? textPtr : 0, textValues.length,
    dataValues.length ? dataPtr : 0, dataValues.length, output, capacity);
  if (result !== capacity) throw new Error(`original render failed: ${result}`);
  const cells = new DataView(e.memory.buffer, output, capacity * 16);
  const rgb = [];
  const rendered = [];
  for (let i = 0; i < capacity; i++) {
    rgb.push(cells.getUint32(i * 16 + 8, true));
    rendered.push([cells.getUint32(i * 16, true), cells.getUint32(i * 16 + 4, true),
      cells.getUint32(i * 16 + 8, true), cells.getUint32(i * 16 + 12, true)]);
  }
  return { rgb, cells: rendered };
});

e.nsStageDefaults(config);
const sourceDefaults = Array.from(new Int32Array(e.memory.buffer, config, 64));
const sourcePalette = Array.from(new Uint32Array(e.memory.buffer, config + 256, 32));

process.stdout.write(JSON.stringify({ editionSha256, wasmSha256, sourceDefaults, sourcePalette, results }));
