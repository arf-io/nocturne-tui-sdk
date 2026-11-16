import fs from 'node:fs';

const [wasmPath, requestPath] = process.argv.slice(2);
if (!wasmPath || !requestPath) throw new Error('usage: runner.mjs module.wasm request.json');
const request=JSON.parse(fs.readFileSync(requestPath,'utf8'));
const bytes=fs.readFileSync(wasmPath);
const compiled=await WebAssembly.compile(bytes);
const imports=WebAssembly.Module.imports(compiled);
if(imports.length) throw new Error(`unexpected WASM imports: ${JSON.stringify(imports)}`);
const instance=await WebAssembly.instantiate(compiled,{});
const e=instance.exports, memory=e.memory;
if (!memory || !e.nrWindowContentSourceProbe || !e.nrAlloc) throw new Error('missing import-free probe exports');
function putArray(values, type='u32') {
  const size=type==='f64'?8:4, ptr=e.nrAlloc(Math.max(size,values.length*size));
  if(!ptr) throw new Error('WASM allocation failed');
  const view=type==='f64'?new Float64Array(memory.buffer,ptr,values.length):new Uint32Array(memory.buffer,ptr,values.length);
  view.set(values); return ptr;
}
const title=putArray(request.title), body=putArray(request.body), label=putArray(request.label);
const ramp=putArray(request.ramp), waveform=putArray(request.waveform,'f64');
const initial=request.initial || Array(request.width*request.height*4).fill(0xdeadbeef);
const cells=putArray(initial);
const status=e.nrWindowContentSourceProbe(request.width,request.height,request.shape,
  title,request.title.length,body,request.body.length,label,request.label.length,
  request.clockMs,request.ink,request.background,request.accent,ramp,request.stopTotal,
  waveform,request.waveform.length,cells);
const actual=Array.from(new Uint32Array(memory.buffer,cells,initial.length));
process.stdout.write(JSON.stringify({status,cells:actual}));
