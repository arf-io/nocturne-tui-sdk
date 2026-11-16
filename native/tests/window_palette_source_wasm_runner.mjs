import fs from 'node:fs';

const [wasmPath, casesPath] = process.argv.slice(2);
const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
const bytes = fs.readFileSync(wasmPath);
const module = await WebAssembly.compile(bytes);
const imports = WebAssembly.Module.imports(module);
if (imports.length !== 0) throw new Error(`unexpected Wasm imports: ${JSON.stringify(imports)}`);
const instance = await WebAssembly.instantiate(module, {});
const e = instance.exports;
const layoutPtr = 2097152, configPtr = 2098176, preparedPtr = 2100000, wordPtr = 2120000;
const layout = new Uint32Array(e.memory.buffer, layoutPtr, 19);
e.nrWindowPaletteSourceProbeLayout(layoutPtr);
const configBytes = layout[0], preparedBytes = layout[16];
const numberValue = value => value === "__nan__" ? Number.NaN :
  value === "__inf__" ? Number.POSITIVE_INFINITY :
  value === "__-inf__" ? Number.NEGATIVE_INFINITY : value;

const results = [];
for (const value of cases) {
  const config = new Uint8Array(e.memory.buffer, configPtr, configBytes);
  config.set(Uint8Array.from(value.configBytes));
  const valid = e.nrWindowPaletteSourceValidate(configPtr);
  new Uint8Array(e.memory.buffer, preparedPtr, preparedBytes).fill(0xa5);
  const status = e.nrWindowPaletteSourcePrepare(configPtr, preparedPtr);
  const out = { valid, status };
  if (status === 0) {
    const words = new Uint32Array(e.memory.buffer);
    const rampStart = preparedPtr / 4;
    const wheelStart = (preparedPtr + layout[17]) / 4;
    out.ramp = Array.from(words.slice(rampStart, rampStart + 2048));
    out.wheel = Array.from(words.slice(wheelStart, wheelStart + 360));
    out.stopTotal = new DataView(e.memory.buffer).getFloat64(preparedPtr + layout[18], true);
    out.colorsAt = value.phases.map(rawPhase => {
      const phase = numberValue(rawPhase);
      new DataView(e.memory.buffer).setUint32(wordPtr, 0xdeadbeef, true);
      const lookupStatus = e.nrWindowPaletteSourceColorAt(preparedPtr, phase, wordPtr);
      return { status: lookupStatus,
        rgb: new DataView(e.memory.buffer).getUint32(wordPtr, true) };
    });
    out.inks = value.hues.map(rawHue => {
      const hue = numberValue(rawHue);
      new DataView(e.memory.buffer).setUint32(wordPtr, 0xdeadbeef, true);
      const lookupStatus = e.nrWindowPaletteSourceInk(preparedPtr, hue, wordPtr);
      return { status: lookupStatus,
        rgb: new DataView(e.memory.buffer).getUint32(wordPtr, true) };
    });
  } else {
    out.preparedBytes = Array.from(new Uint8Array(e.memory.buffer, preparedPtr, preparedBytes));
  }
  results.push(out);
}
process.stdout.write(JSON.stringify({ imports, layout: Array.from(layout), results }));
