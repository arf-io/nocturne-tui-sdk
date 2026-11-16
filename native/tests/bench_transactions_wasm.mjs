// Per-op nrCommand wall time in WASM (node V8) for a command stream (native/docs/TRANSACTIONS.md, "Measurement").
// Usage: node tests/bench_transactions_wasm.mjs <nocturne_native.wasm> [stream.jsonl] [--warm N]
// Replays the stream through bindings/typescript/native_scene.mjs (the binding the Gallery uses), warms each entry for
// N frames, renders after every `time`, and prints per-op medians and 99th percentiles of NativeScene.command().
import {readFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';

const args = process.argv.slice(2);
let warm = 120, wasmPath = null, streamPath = 'tests/fixtures/transactions/streams/composite.jsonl';
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--warm') warm = Number(args[++i]);
    else if (!wasmPath) wasmPath = args[i];
    else streamPath = args[i];
}
if (!wasmPath) { console.error('usage: bench_transactions_wasm.mjs <wasm> [stream] [--warm N]'); process.exit(2); }
const bytes = readFileSync(wasmPath);
const lines = readFileSync(streamPath, 'utf8').split('\n').filter(Boolean);
const ops = new Map();
let scene = null, frame = 0;
const send = text => { let code; do { try { code = scene.command(JSON.parse(text)); } catch { code = -1; } } while (code === 1); return code; };
for (const line of lines) {
    if (line.startsWith('{"entry":')) { scene?.close?.(); scene = await NativeScene.create(bytes, 2030); frame = 0; continue; }
    if (!scene) continue;
    const tick = line.startsWith('{"op":"time"');
    if (tick) frame++;
    if (frame <= warm) { send(line); if (tick) scene.render(); continue; }
    let command; try { command = JSON.parse(line); } catch { continue; }
    const op = typeof command.op === 'string' ? command.op : '?';
    const t0 = process.hrtime.bigint();
    try { scene.command(command); } catch { /* a rejected command throws in the binding */ }
    const ms = Number(process.hrtime.bigint() - t0) / 1e6;
    if (!ops.has(op)) ops.set(op, []);
    ops.get(op).push(ms);
    if (tick) scene.render();
}
const pct = (v, p) => { const w = [...v].sort((a, b) => a - b); return w[Math.floor(p * (w.length - 1))]; };
console.log(`wasm ${wasmPath}, stream ${streamPath}, ${warm} warm frames per entry`);
console.log('op'.padEnd(14) + 'n'.padStart(6) + '   p50 ms'.padStart(10) + '   p99 ms'.padStart(10));
for (const [op, v] of ops) console.log(op.padEnd(14) + String(v.length).padStart(6) + pct(v, .5).toFixed(4).padStart(10) + pct(v, .99).toFixed(4).padStart(10));
