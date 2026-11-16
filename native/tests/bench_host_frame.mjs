// Per-frame host work of the Gallery live loop (native/web/template.html), measured in node on the composite screens:
// the commands a frame sends (time, the screen's own updates) and the reads the template makes every frame
// (render, promptVisualLayout, textRunSource, the source-modal controller's infoComplete calls) and every 240 ms
// (info). Usage: node tests/bench_host_frame.mjs <nocturne_native.wasm> [frames] [stream.jsonl: entries, setup, then frames each led by time]
import {readFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
import {SourceModalController} from '../bindings/typescript/source_modal.mjs';

const args = process.argv.slice(2);
const wasm = readFileSync(args[0]);
const frames = Number(args[1] ?? 240);
const lines = readFileSync(args[2] ?? 'tests/fixtures/transactions/streams/composite.jsonl', 'utf8').split('\n').filter(Boolean);
const scenes = [];
for (const line of lines) { if (line.startsWith('{"entry":')) scenes.push({name: JSON.parse(line).entry, setup: [], frames: []}); else { const s = scenes.at(-1); const c = JSON.parse(line); if (c.op === 'time') s.frames.push([c]); else if (s.frames.length) s.frames.at(-1).push(c); else s.setup.push(c); } }
const t = () => Number(process.hrtime.bigint()) / 1e6;
const pct = (v, p) => { const w = [...v].sort((a, b) => a - b); return w[Math.floor(p * (w.length - 1))]; };
for (const s of scenes) {
    const scene = await NativeScene.create(wasm, 2030);
    const modal = new SourceModalController(scene, {timeMs: () => scene.infoComplete().clock.timeUs / 1000, workspace: () => s.name,
        windows: () => scene.infoComplete().windows.map(w => ({...w, state: w.reader ? 'reader' : 'open'})), commands: () => []});
    const run = c => { try { while (scene.command(c) === 1) {} } catch {} };
    for (const c of s.setup) run(c);
    const cost = {commands: [], compose: [], modalState: [], render: [], promptLayout: [], textRunSource: [], info: []};
    let commandCount = 0;
    for (let f = 0; f < Math.min(frames, s.frames.length); f++) {
        let a = t(); for (const c of s.frames[f]) { run(c); commandCount++; } cost.commands.push(t() - a);
        a = t(); modal.compose(); cost.compose.push(t() - a);
        a = t(); modal.current(); cost.modalState.push(t() - a);
        a = t(); scene.render(); cost.render.push(t() - a);
        a = t(); const spans = scene.promptVisualLayout(); cost.promptLayout.push(t() - a);
        a = t(); if (spans.length) Array.from(scene.textRunSource(0, 0)); cost.textRunSource.push(t() - a);
        if (f % 15 === 0) { a = t(); scene.info(); cost.info.push(t() - a); }
    }
    console.log(`${s.name}: ${Math.min(frames, s.frames.length)} frames, ${(commandCount / Math.min(frames, s.frames.length)).toFixed(2)} commands/frame`);
    for (const [k, v] of Object.entries(cost)) console.log(`  ${k.padEnd(14)} p50 ${pct(v, .5).toFixed(3)} ms  p99 ${pct(v, .99).toFixed(3)} ms  (n ${v.length})`);
}
