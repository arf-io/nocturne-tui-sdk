import {clamp,finite} from './observatory.js';
import {cameraBasis} from './kinetic-camera.js';
/** Canonical input coordinates and impulse records. Hosts normalize once at the
 * boundary; models never inspect DOM events or guess which legacy scene is live. */
/** Signed wheel displacement in pixels, preferring the dominant device axis.
 * Shift-wheel may arrive on X. Zero stays zero; fractional trackpad deltas stay
 * fractional. mode 0=pixels, 1=lines (16 px), 2=pages (viewport height).
 * Example: signedWheel({deltaX:-80,deltaY:0,shiftKey:true}) === -80. */
export function signedWheel(sample, pagePixels = 640) {
    if (!sample || typeof sample !== 'object') throw new RangeError('wheel sample');
    finite(pagePixels, 1, 100000, 'pagePixels');
    const x = finite(sample.deltaX ?? 0, -1e7, 1e7, 'deltaX'), y = finite(sample.deltaY ?? 0, -1e7, 1e7, 'deltaY');
    const mode = sample.deltaMode ?? 0;
    if (![0, 1, 2].includes(mode))
        throw new RangeError('wheel deltaMode');
    const v = Math.abs(y) >= Math.abs(x) ? y : x;
    return clamp(v * (mode === 1 ? 16 : mode === 2 ? pagePixels : 1), -4000, 4000);
}
/** Camera-local world displacement. up is positive upward (screen dy is negative).
 * Translation does not depend on an object's yaw or on a global XY plane. */
export function viewDisplacement(camera, right, up, forward = 0) {
    for (const v of [right, up, forward])
        finite(v, -100000, 100000, 'translation');
    const b = cameraBasis(camera);
    return { x: b.right.x * right + b.up.x * up + b.forward.x * forward, y: b.right.y * right + b.up.y * up + b.forward.y * forward, z: b.right.z * right + b.up.z * up + b.forward.z * forward };
}
/** Scalar-indexed insertions for one replacement. Shared by typing, paste and IME
 * commit. Deletions produce no insertion weather. Caller bounds both strings. */
export function textInsertions(previous, next) {
    const a = [...previous], b = [...next];
    let prefix = 0, suffix = 0;
    while (prefix < a.length && prefix < b.length && a[prefix] === b[prefix])
        prefix++;
    while (suffix < a.length - prefix && suffix < b.length - prefix && a[a.length - 1 - suffix] === b[b.length - 1 - suffix])
        suffix++;
    return b.slice(prefix, b.length - suffix).map((glyph, i) => ({ index: prefix + i, glyph }));
}
/** Single-line terminal composer. UTF-16 DOM selection is converted at the host.
 * Keep the caret in view and give rendering/weather the exact same origin. */
export function draftView(text, caret, width, height) {
    const chars = [...text], capacity = Math.max(1, width - 9), cursor = Math.round(clamp(caret, 0, chars.length));
    const offset = Math.max(0, cursor - capacity + 1), originX = 4;
    return { text: chars.slice(offset, offset + capacity).map(c => /[\x00-\x1f\x7f]/.test(c) ? ' ' : c).join(''), offset, originX, row: height - 4, cursorX: originX + cursor - offset, capacity };
}
/** Deduplicates one event identity, NOT nearby legitimate user clicks. */
export class DispatchGate {
    constructor() {
        this.ids = new Set();
    }
    accept(id) { if (typeof id !== 'string' || !id || id.length > 128)
        throw new RangeError('dispatch ID'); if (this.ids.has(id))
        return false; this.ids.add(id); if (this.ids.size > 256)
        this.ids.delete(this.ids.values().next().value); return true; }
    clear() { this.ids.clear(); }
}
/** Quintic ease: zero velocity and acceleration at both endpoints. */
export function transitEase(t) { t = clamp(t, 0, 1); return t * t * t * (10 + t * (-15 + 6 * t)); }

