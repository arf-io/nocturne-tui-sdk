import fs from 'node:fs';
import crypto from 'node:crypto';

const htmlPath = process.argv[2];
if (!htmlPath) throw new Error('exact rc.2 HTML path required');
const html = fs.readFileSync(htmlPath, 'utf8');
const editionSha256 = crypto.createHash('sha256').update(html).digest('hex');
if (editionSha256 !== '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')
  throw new Error(`original edition SHA mismatch: ${editionSha256}`);
const match = html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s);
if (!match) throw new Error('original DATA record is missing');
const data = JSON.parse(match[1]);
const wasmBytes = Buffer.from(data.wasm, 'base64');
const wasmSha256 = crypto.createHash('sha256').update(wasmBytes).digest('hex');
if (wasmSha256 !== 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')
  throw new Error(`original Wasm SHA mismatch: ${wasmSha256}`);
const e = new WebAssembly.Instance(new WebAssembly.Module(wasmBytes), {}).exports;
if (e.nsStageConfigSize() !== 704 || e.nsCellSize() !== 16 || !e.nsStagePaintFrame)
  throw new Error('original paint ABI mismatch');

const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
e.nsStageInit();
const config = e.nsStageConfigPtr();
const framePtr = e.nsFramePtr();
const nodesPtr = e.nsStageNodesPtr();
const textPtr = e.nsStageTextPtr();
const dataPtr = e.nsStageDataPtr();
const cases = requests.map(request => {
  const { width, height, timeMs, cells, nodes = [], text = [], data = [] } = request;
  if (!Number.isSafeInteger(timeMs) || timeMs < 0 || !Number.isInteger(width) ||
      !Number.isInteger(height) || width * height !== cells.length / 4)
    throw new Error('invalid original paint request');
  e.nsStageDefaults(config);
  const fields = new Int32Array(e.memory.buffer, config, 64);
  fields[0] = width; fields[1] = height;
  fields[21] = 0; // center sample, no subcell material in the oracle base
  fields[30] = 0; // stars off
  fields[38] = 0; // automatic novae off
  const palette = new Uint32Array(e.memory.buffer, config + 256, 32);
  palette.fill(0);
  const stops = request.palette ?? [0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565];
  fields[25] = stops.length;
  stops.forEach((rgb, i) => { palette[i] = rgb; });
  const initialized = e.nsStageRenderFrame(timeMs >>> 0, Math.floor(timeMs / 4294967296),
    0, 0, 0, 0);
  if (initialized !== width * height) throw new Error(`original frame init failed: ${initialized}`);
  new Uint32Array(e.memory.buffer, framePtr, cells.length).set(cells);
  const packedNodes = new Int32Array(e.memory.buffer, nodesPtr, nodes.length * 32);
  packedNodes.fill(0);
  nodes.forEach((node, i) => {
    if (!Array.isArray(node) || node.length !== 32) throw new Error('source node must contain 32 words');
    node.forEach((value, k) => { packedNodes[i * 32 + k] = value; });
  });
  new Uint32Array(e.memory.buffer, textPtr, text.length).set(text);
  new Int32Array(e.memory.buffer, dataPtr, data.length).set(data);
  const count = e.nsStagePaintFrame(timeMs >>> 0, Math.floor(timeMs / 4294967296),
    nodes.length, text.length, data.length);
  if (count !== width * height) throw new Error(`original paint failed: ${count}`);
  const rendered = new Uint32Array(e.memory.buffer, framePtr, cells.length).slice();
  return Array.from({ length: width * height }, (_, i) =>
    Array.from(rendered.subarray(i * 4, i * 4 + 4)));
});
process.stdout.write(JSON.stringify({ editionSha256, wasmSha256, cases }));
