import {clamp,smooth,finite,randomAt} from './observatory.js';
/** Explicit-time, per-glyph reveal/hide choreography. Stored text is never
 * scrambled or destroyed; the returned glyphs are only a visual presentation.
 * Local editing bypasses every reveal/hide policy by contract.
 */
export const TEXT_REVEALS = ['immediate', 'fade', 'rain', 'scramble', 'flipboard', 'sweep-left', 'sweep-right', 'marquee', 'orbit', 'constellation', 'prism-stitch', 'gravity-loom', 'scanline', 'elastic', 'typewriter', 'curtain'];
export const TEXT_HIDES = ['immediate', 'fade', 'fall', 'scramble', 'flipboard', 'sweep-left', 'sweep-right', 'marquee', 'orbit', 'ash', 'prism-stitch', 'gravity-loom', 'scanline', 'elastic', 'typewriter', 'curtain'];
export const DEFAULT_TEXT_OPTIONS = {
    effect: 'rain', phase: 'reveal', local: false, durationMs: 1200, staggerMs: 24, jitterMs: 360, batchSize: 1,
    distanceRows: 18, scatterCols: 5, speedVariation: .4, scrambleHz: 24,
    alphabet: ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/!?', cycles: 3, wind: 1.3, overshoot: .2,
    seed: 2030, easing: 'smooth', originX: 0, originY: 0, width: 120, hueSpread: 10,
};
export const TEXT_CONTROLS = {
    durationMs: [0, 12000, 20], staggerMs: [0, 1000, 5], jitterMs: [0, 4000, 20], batchSize: [1, 128, 1],
    distanceRows: [0, 100, 1], scatterCols: [0, 120, 1], speedVariation: [0, .9, .05], scrambleHz: [1, 120, 1],
    cycles: [0, 20, 1], wind: [-20, 20, .25], overshoot: [0, 2, .05], seed: [0, 4294967295, 1],
    originX: [-4096, 4096, 1], originY: [-4096, 4096, 1], width: [1, 4096, 1], hueSpread: [-180, 180, 1],
};
const ALL_EFFECTS = new Set([...TEXT_REVEALS, ...TEXT_HIDES]);
/** Validate and own options. Invalid duration, alphabet, enums and nonfinite
 * numbers throw before a caller's live actor changes. Units are cells and ms. */
export function validateTextOptions(patch = {}, base = DEFAULT_TEXT_OPTIONS) {
    const o = { ...base };
    for (const [k, v] of Object.entries(patch)) {
        if (Object.prototype.hasOwnProperty.call(TEXT_CONTROLS, k)) {
            const r = TEXT_CONTROLS[k];
            const n = finite(v, r[0], r[1], k);
            if (['batchSize', 'seed', 'width'].includes(k) && !Number.isInteger(n))
                throw new RangeError(k + ' requires integer');
            o[k] = n;
        }
        else if (k === 'effect') {
            if (!ALL_EFFECTS.has(v))
                throw new RangeError('Unknown text effect');
            o.effect = v;
        }
        else if (k === 'phase') {
            if (v !== 'reveal' && v !== 'hide')
                throw new RangeError('text phase');
            o.phase = v;
        }
        else if (k === 'local') {
            if (typeof v !== 'boolean')
                throw new RangeError('local must be boolean');
            o.local = v;
        }
        else if (k === 'easing') {
            if (!['linear', 'smooth', 'sine', 'cubic'].includes(v))
                throw new RangeError('easing');
            o.easing = v;
        }
        else if (k === 'alphabet') {
            if (typeof v !== 'string' || [...v].length < 1 || [...v].length > 256 || /[\x00-\x1f\x7f-\x9f]/.test(v))
                throw new RangeError('Alphabet requires 1..256 printable scalars');
            o.alphabet = v;
        }
        else
            throw new RangeError('Unknown text option ' + k);
    }
    return o;
}
function easing(p, kind) { p = clamp(p, 0, 1); return kind === 'linear' ? p : kind === 'sine' ? (1 - Math.cos(Math.PI * p)) / 2 : kind === 'cubic' ? p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2 : smooth(p); }
function checkText(text) { if (typeof text !== 'string' || [...text].length > 4096)
    throw new RangeError('Text requires at most 4096 scalars'); return [...text]; }
function timing(index, length, o) {
    const order = o.effect === 'sweep-right' ? length - 1 - index : index;
    const ordered = ['sweep-left', 'sweep-right', 'typewriter'].includes(o.effect);
    const group = Math.floor(order / o.batchSize), delay = group * o.staggerMs + (ordered ? 0 : randomAt(o.seed, index + 171) * o.jitterMs);
    const speed = ordered ? 1 : 1 + (randomAt(o.seed, index + 227) - .5) * 2 * o.speedVariation;
    return { delay, duration: o.durationMs / Math.max(.1, speed) };
}
/** Last glyph completion time, including group staggering and seeded speed
 * variation. This is the actual bound, not nominal duration times frame count.
 */
export function textDuration(text, options = {}) {
    const chars = checkText(text), o = validateTextOptions(options);
    if (o.local || o.effect === 'immediate')
        return 0;
    return chars.reduce((last, _, i) => { const t = timing(i, chars.length, o); return Math.max(last, t.delay + t.duration); }, 0);
}
/** Sample presentation glyphs without modifying input text or reading a clock.
 * phase='hide' runs an exit choreography; local=true always returns settled ink.
 * Newlines affect layout and are returned as invisible spaces at line breaks.
 * General grapheme layout is outside the SDK's single-cell glyph profile.
 * Example: sampleText('CONNECTED',elapsedMs,{effect:'flipboard',batchSize:2}).
 */
export function sampleText(text, timeMs, options = {}) {
    const chars = checkText(text), o = validateTextOptions(options);
    finite(timeMs, -Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER, 'text time');
    const alphabet = [...o.alphabet], hide = o.phase === 'hide';
    let col = 0, row = 0;
    return chars.map((source, index) => {
        if (col >= o.width) {
            col = 0;
            row++;
        }
        const newline = source === '\n';
        const glyph = newline ? ' ' : /[\x00-\x1f\x7f-\x9f]/.test(source) ? '?' : source;
        const tx = o.originX + col, ty = o.originY + row;
        col++;
        if (newline) {
            col = 0;
            row++;
        }
        const out = { index, glyph, x: tx, y: ty, targetX: tx, targetY: ty, opacity: 1, hue: index * o.hueSpread, flip: 1 };
        if (o.local)
            return out;
        if (o.effect === 'immediate') {
            out.opacity = hide ? 0 : timeMs >= 0 ? 1 : 0;
            return out;
        }
        const t = timing(index, chars.length, o), raw = timeMs < t.delay ? 0 : t.duration === 0 ? 1 : clamp((timeMs - t.delay) / t.duration, 0, 1), p = easing(raw, o.easing), u = hide ? p : 1 - p;
        if (raw >= 1) {
            out.opacity = hide ? 0 : 1;
            return out;
        }
        if (timeMs < t.delay) {
            out.opacity = hide ? 1 : 0;
        }
        else
            out.opacity = hide ? 1 - p : p;
        const a = randomAt(o.seed, index + 811), b = randomAt(o.seed, index + 1901), angle = a * Math.PI * 2;
        switch (o.effect) {
            case 'fade': break;
            case 'rain': {
                const distance = o.distanceRows * (.4 + .6 * b);
                out.x = tx + (a - .5) * o.scatterCols * 2 * u + Math.sin(raw * Math.PI) * o.wind * (b - .5);
                out.y = ty - distance * u;
                out.opacity = hide ? 1 - p : Math.min(1, p * 2);
                break;
            }
            case 'fall':
                out.x = tx + (a - .5) * o.scatterCols * p + o.wind * p * p;
                out.y = ty + o.distanceRows * (.45 + b * .55) * p * p;
                out.opacity = 1 - p;
                break;
            case 'scramble': {
                const tick = Math.floor(Math.max(0, timeMs - t.delay) * o.scrambleHz / 1000);
                out.glyph = alphabet[Math.floor(randomAt(o.seed ^ Math.imul(index + 1, 919), tick) * alphabet.length)];
                out.opacity = hide ? 1 - p : Math.min(1, p * 4);
                break;
            }
            case 'flipboard': {
                const start = Math.floor(a * alphabet.length), target = hide ? Math.max(0, alphabet.indexOf(' ')) : Math.max(0, alphabet.indexOf(glyph)), steps = alphabet.length * o.cycles + (target - start + alphabet.length) % alphabet.length, pos = start + raw * steps;
                out.glyph = alphabet[Math.floor(pos) % alphabet.length];
                out.flip = .18 + .82 * Math.abs(Math.cos((pos % 1) * Math.PI));
                out.opacity = (hide ? 1 - p : Math.min(1, p * 4)) * (.65 + .35 * out.flip);
                break;
            }
            case 'sweep-left':
            case 'sweep-right':
            case 'typewriter':
                out.opacity = timeMs >= t.delay ? (hide ? 0 : 1) : (hide ? 1 : 0);
                break;
            case 'marquee':
                out.x = tx + (hide ? -1 : 1) * (o.width + o.scatterCols) * u;
                out.opacity = hide ? 1 - p : Math.min(1, p * 3);
                break;
            case 'orbit': {
                const phase = angle + raw * Math.PI * 2 * o.cycles;
                out.x = tx + Math.cos(phase) * o.scatterCols * u;
                out.y = ty + Math.sin(phase) * o.distanceRows * u / 2;
                out.opacity = hide ? 1 - p : Math.min(1, p * 2);
                break;
            }
            case 'constellation': {
                out.x = tx + (Math.cos(angle) * o.width * .7 + o.width * .5 - (tx - o.originX)) * u;
                out.y = ty + Math.sin(angle) * o.distanceRows * u;
                out.opacity = hide ? 1 - p : Math.min(1, p * 3);
                break;
            }
            case 'ash':
                out.x = tx + (a - .5) * o.scatterCols * p + Math.sin(p * 7 + b * 5) * p;
                out.y = ty - o.distanceRows * p * (.3 + b * .7) + o.distanceRows * p * p * .8;
                out.glyph = p > .3 ? ['·', '∙', '⠁', '⠈'][index % 4] : glyph;
                out.opacity = 1 - p;
                break;
            case 'prism-stitch':
                out.x = tx + (index % 2 ? -1 : 1) * o.scatterCols * u;
                out.y = ty + (index % 2 ? 1 : -1) * o.distanceRows * u * .3;
                out.hue += Math.sin(raw * Math.PI) * 80;
                break;
            case 'gravity-loom': {
                const travel = o.distanceRows * (.5 + .5 * b);
                out.x = tx + Math.sin(raw * Math.PI * (2 + o.cycles) + angle) * o.scatterCols * u + o.wind * u;
                out.y = ty + (hide ? 1 : -1) * travel * (hide ? p * p : 1 - p);
                out.opacity = hide ? 1 - p : Math.min(1, p * 2.5);
                break;
            }
            case 'scanline':
                out.x = tx + (index % 2 ? 1 : -1) * 2 * u;
                out.glyph = raw < .18 ? '─' : glyph;
                out.opacity = hide ? 1 - p : Math.min(1, p * 5);
                break;
            case 'elastic':
                out.y = ty + (hide ? 1 : -1) * o.distanceRows * u + Math.sin(raw * Math.PI * 3) * o.overshoot * o.distanceRows * (1 - raw);
                break;
            case 'curtain':
                out.x = tx + ((index % o.width) < o.width / 2 ? -1 : 1) * o.scatterCols * u;
                out.opacity = hide ? 1 - p : Math.min(1, p * 2);
                break;
        }
        if (timeMs < t.delay && !hide)
            out.opacity = 0;
        out.opacity = clamp(out.opacity, 0, 1);
        return out;
    });
}
/** An interruptible text actor with explicit transition timestamps. Retargeting
 * snapshots only visual glyphs; source text remains intact. A caller can use the
 * pure sampleText function instead when transitions never interrupt one another.
 */
export class TextActor {
    constructor(text, options = {}) {
        this.atMs = 0;
        this.started = false;
        this.from = null;
        checkText(text);
        this.text = text;
        this.options = validateTextOptions(options);
    }
    begin(phase, atMs, patch) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        const next = validateTextOptions({ ...patch, phase }, this.options);
        const old = this.started ? this.sample(atMs) : null;
        this.from = old;
        this.options = next;
        this.atMs = atMs;
        this.started = true;
    }
    show(atMs, options = {}) { this.begin('reveal', atMs, options); }
    hide(atMs, options = {}) { this.begin('hide', atMs, options); }
    sample(atMs, layout = {}) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        const opts = { ...this.options, ...layout }, elapsed = atMs - this.atMs;
        if (this.from && elapsed === 0)
            return this.from.map(c => ({ ...c }));
        const result = sampleText(this.text, elapsed, opts);
        if (!this.from)
            return result;
        const p = smooth(elapsed / Math.max(1, textDuration(this.text, opts)));
        return result.map((c, i) => { const a = this.from[i]; if (!a)
            return c; return { ...c, x: c.x + (a.x - a.targetX) * (1 - p), y: c.y + (a.y - a.targetY) * (1 - p), opacity: this.options.phase === 'hide' ? c.opacity * a.opacity : a.opacity + (c.opacity - a.opacity) * p }; });
    }
    get endsAtMs() { return this.atMs + textDuration(this.text, this.options); }
}

