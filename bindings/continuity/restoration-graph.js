import {transitEase} from './continuity-input.js';
import {Projector} from './black-hole-space.js';
/** Reserve the inspector before laying out the selected neighbourhood. Small
 * terminals use a compact inspector; full metadata remains in the companion. */
export function graphViewport(model, width, height) {
    const entry = model.modalStack.peek(), show = entry && model.modalContext === 'node';
    const progress = show ? (model.graphTransitMs === 0 ? 1 : transitEase((model.motionMs - entry.atMs) / model.graphTransitMs)) : 0;
    const drawerWidth = width >= 85 ? Math.min(44, Math.floor(width * .36)) : Math.max(16, Math.floor(width * .40));
    const right = width - 2 - (drawerWidth + 2) * progress;
    return { right, centerX: Math.max(5, right / 2), centerY: (7 + height - 7) / 2, top: 8, bottom: height - 8, drawerWidth, progress };
}
/** Compute target WORLD positions once at selection, using the final inspector
 * viewport. Later camera movement reprojects them normally; no screen pinning. */
export function graphTargets(model, width, height) {
    const view = graphViewport(model, width, height), right = width - 2 - view.drawerWidth - 2, cx = Math.max(5, right / 2), cy = height / 2;
    const p = new Projector(model.camera.snapshot(), width, height), hood = model.richGraph.neighborhood(model.graphFocus), targets = new Map();
    const put = (id, x, y, z) => targets.set(id, p.unproject(x, y, z));
    put(model.graphFocus, cx, cy, 40);
    const rows = (ids, y, dir) => { const columns = Math.max(1, Math.min(3, Math.floor(right / 23))); ids.forEach((id, i) => { const row = Math.floor(i / columns), col = i % columns, len = Math.min(columns, ids.length - row * columns); put(id, cx + (col - (len - 1) / 2) * Math.min(25, (right - 8) / len), y + dir * row * 4, 48 + row * 4); }); };
    rows(hood.parents, 11, 1);
    rows(hood.children, height - 10, -1);
    hood.siblings.forEach((id, i) => { if (!targets.has(id))
        put(id, i % 2 === 0 ? Math.max(10, cx - 25) : Math.min(right - 10, cx + 25), cy + (Math.floor(i / 2) - .5) * 4, 55); });
    return targets;
}
/** Sample the explicit-time transition in a single world coordinate system.
 * Rendering is pure. Retargeting uses these current poses, including mid-flight. */
export function graphWorldPositions(model) {
    const out = new Map(), u = model.graphTransitMs === 0 ? 1 : transitEase((model.motionMs - model.graphFocusAt) / model.graphTransitMs);
    for (const n of model.layout.nodes) {
        const a = model.graphFrom?.get(n.id) ?? n, b = model.graphTo?.get(n.id) ?? n;
        out.set(n.id, { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u, z: a.z + (b.z - a.z) * u });
    }
    return out;
}
export function graphFocusPositions(model, width, height) {
    const projector = new Projector(model.camera.snapshot(), width, height), out = new Map();
    for (const [id, point] of graphWorldPositions(model)) {
        const screen = projector.project(point);
        if (screen)
            out.set(id, screen);
    }
    return out;
}
function canonical(value) {
    if (value === null || typeof value !== 'object') {
        const text = JSON.stringify(value);
        if (text === undefined)
            throw new RangeError('Hash value is not JSON data');
        return text;
    }
    if (Array.isArray(value))
        return '[' + value.map(canonical).join(',') + ']';
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
}
const SHA256_K = new Uint32Array([0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
const rotr = (x, n) => (x >>> n) | (x << (32 - n));
/** Hash recursively key-sorted JSON as UTF-8 using SHA-256. This is a record
 * fingerprint, NOT a source-provided Git object ID or a provenance signature.
 * Example: graphRecordHash({id:'commit',metadata:{objectFormat:'sha1'}}).
 * Caller must pass bounded acyclic JSON; graphs already validate that boundary. */
export function graphRecordHash(value) {
    const bytes = new TextEncoder().encode(canonical(value));
    if (bytes.length > 1048576)
        throw new RangeError('Fingerprint input exceeds 1 MiB');
    const padded = new Uint8Array(Math.ceil((bytes.length + 9) / 64) * 64);
    padded.set(bytes);
    padded[bytes.length] = 128;
    const v = new DataView(padded.buffer);
    v.setUint32(padded.length - 8, Math.floor(bytes.length / 536870912));
    v.setUint32(padded.length - 4, bytes.length * 8);
    const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]), w = new Uint32Array(64);
    for (let offset = 0; offset < padded.length; offset += 64) {
        for (let i = 0; i < 16; i++)
            w[i] = v.getUint32(offset + i * 4);
        for (let i = 16; i < 64; i++) {
            const a = w[i - 15], b = w[i - 2];
            w[i] = (w[i - 16] + (rotr(a, 7) ^ rotr(a, 18) ^ (a >>> 3)) + w[i - 7] + (rotr(b, 17) ^ rotr(b, 19) ^ (b >>> 10))) >>> 0;
        }
        let [a, b, c, d, e, f, g, z] = h;
        for (let i = 0; i < 64; i++) {
            const s = (z + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + SHA256_K[i] + w[i]) >>> 0, t = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
            z = g;
            g = f;
            f = e;
            e = (d + s) >>> 0;
            d = c;
            c = b;
            b = a;
            a = (s + t) >>> 0;
        }
        [a, b, c, d, e, f, g, z].forEach((n, i) => h[i] = (h[i] + n) >>> 0);
    }
    return [...h].map(n => n.toString(16).padStart(8, '0')).join('');
}

