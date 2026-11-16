// The transaction differential in WASM (native/docs/TRANSACTIONS.md, "Verification"): two builds of
// nocturne_native.wasm, side by side in node through bindings/typescript/native_scene.mjs, fed the same stream.
// After every command it compares the result (return code or thrown error text) and the rendered frame; every
// --snapshots N commands, and at {"frame":...} checkpoints, it also compares the complete snapshot bytes.
// Usage: node tests/transaction_differential_wasm.mjs <reference.wasm> <candidate.wasm> [--snapshots N] stream.jsonl...
// Exit status 0 when no divergence was found, 1 otherwise.
import {readFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';

const args = process.argv.slice(2);
if (args.length < 3) { console.error('usage: transaction_differential_wasm.mjs ref.wasm cand.wasm [--snapshots N] stream...'); process.exit(2); }
const refBytes = readFileSync(args[0]), candBytes = readFileSync(args[1]);
let snapEvery = 10; const streams = [];
for (let i = 2; i < args.length; i++) { if (args[i] === '--snapshots') snapEvery = Number(args[++i]); else streams.push(args[i]); }
let commands = 0, rejected = 0, frames = 0, snapshots = 0, divergences = 0, entries = 0, entry = '';
const same = (a, b) => a.length === b.length && Buffer.compare(Buffer.from(a.buffer, a.byteOffset, a.length), Buffer.from(b.buffer, b.byteOffset, b.length)) === 0;
const report = (what, line) => { divergences++; if (divergences <= 40) console.error(`DIVERGENCE [${entry}] ${what} after ${line.slice(0, 200)}`); };
const run = (scene, command) => { let code; try { do code = scene.command(command); while (code === 1); return String(code); } catch (e) { return 'throw ' + e.message; } };
let a = null, b = null;
const open = async () => { a?.close?.(); b?.close?.(); a = await NativeScene.create(refBytes, 2030); b = await NativeScene.create(candBytes, 2030); entries++; };
for (const path of streams) {
    for (const line of readFileSync(path, 'utf8').split('\n')) {
        if (!line) continue;
        if (line.startsWith('{"entry":')) { entry = JSON.parse(line).entry; await open(); continue; }
        if (!a) { entry = path; await open(); }
        const checkpoint = line.startsWith('{"frame":');
        if (!checkpoint) {
            let command; try { command = JSON.parse(line); } catch { continue; } // malformed JSON never reaches the binding
            const ra = run(a, command), rb = run(b, command); commands++;
            if (ra.startsWith('throw')) rejected++;
            if (ra !== rb) { report(`result (${ra} | ${rb})`, line); continue; }
        }
        if (checkpoint || (snapEvery > 0 && commands % snapEvery === 0)) {
            snapshots++; if (!same(a.snapshot(), b.snapshot())) { report('snapshot', line); continue; }
        }
        let fa, fb; try { fa = a.render().bytes; } catch { fa = new Uint8Array(0); } try { fb = b.render().bytes; } catch { fb = new Uint8Array(0); }
        frames++; if (!same(fa, fb)) report('frame', line);
    }
}
console.log(`transaction-differential-wasm: ${entries} entries, ${commands} commands (${rejected} rejected), ${snapshots} snapshots and ${frames} frames compared, ${divergences} divergences`);
process.exit(divergences ? 1 : 0);
