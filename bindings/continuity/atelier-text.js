import {clamp,smooth,finite,randomAt} from './observatory.js';
/** Preserved parallel Atelier v0.5 implementation; namespaced, not replaced. */
/** Pure per-character reveal/hide choreography. Local user input always bypasses
 * choreography. Stored text is immutable; glyph substitutions are display only.
 * This module keeps the SDK's one-cell scalar profile, not general shaping/IME.
 */
export const ATELIER_TEXT_EFFECTS = ['instant', 'fade', 'rain', 'scramble', 'flipboard', 'sweep-left', 'sweep-right', 'lift', 'fall', 'marquee', 'iris', 'constellation', 'prism-weave', 'ink-tide', 'comet-stitch', 'orbit', 'fold', 'zipper'];
export const ATELIER_TEXT_DEFAULTS = { effect: 'rain', durationMs: 1200, delayMs: 0, staggerMs: 28, batchSize: 1, seed: 6137, travelRows: 13, spreadColumns: 8, drift: 2, speedJitter: .55, alphabet: ' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!?+-*/', cycleHz: 18, easing: 'smooth', reverseOrder: false, randomOrder: false, trailLength: 2, overshoot: 1.2, turns: 1.5, hueSpread: 110, local: false };
export const ATELIER_TEXT_RANGES = { durationMs: [0, 10000, 25], delayMs: [0, 5000, 25], staggerMs: [0, 500, 5], batchSize: [1, 64, 1], seed: [0, 4294967295, 1], travelRows: [0, 80, .5], spreadColumns: [0, 80, .5], drift: [-30, 30, .25], speedJitter: [0, .95, .05], cycleHz: [1, 60, 1], trailLength: [0, 8, 1], overshoot: [0, 3, .1], turns: [0, 8, .1], hueSpread: [0, 360, 5] };
/** Normalize all options atomically. Durations are per character; total length
 * adds start delay, duration jitter and ceil(characters / batchSize) staggering.
 * Throws RangeError on unsupported fields, invalid scalars or control glyphs.
 */
export function atelierTextOptions(patch = {}) {
    const o = { ...ATELIER_TEXT_DEFAULTS, ...patch };
    for (const key of Object.keys(patch))
        if (!(key in ATELIER_TEXT_DEFAULTS))
            throw new RangeError('Unknown text option ' + key);
    for (const [key, [lo, hi]] of Object.entries(ATELIER_TEXT_RANGES))
        finite(o[key], lo, hi, key);
    for (const k of ['batchSize', 'seed', 'trailLength'])
        if (!Number.isInteger(o[k]))
            throw new RangeError(k + ' must be integer');
    if (!ATELIER_TEXT_EFFECTS.includes(o.effect) || !['linear', 'smooth', 'cubic', 'back', 'bounce'].includes(o.easing))
        throw new RangeError('Unknown text effect/easing');
    for (const k of ['local', 'randomOrder', 'reverseOrder'])
        if (typeof o[k] !== 'boolean')
            throw new RangeError(k);
    if (typeof o.alphabet !== 'string' || [...o.alphabet].length < 1 || [...o.alphabet].length > 256 || /[\x00-\x1f\x7f-\x9f]/.test(o.alphabet))
        throw new RangeError('Alphabet requires 1..256 printable scalars');
    return o;
}
export function atelierEase(p, kind = 'smooth', overshoot = 1.2) {
    p = clamp(p, 0, 1);
    if (kind === 'linear')
        return p;
    if (kind === 'cubic')
        return p < .5 ? 4 * p * p * p : 1 - (-2 * p + 2) ** 3 / 2;
    if (kind === 'back')
        return 1 + (overshoot + 1) * (p - 1) ** 3 + overshoot * (p - 1) ** 2;
    if (kind === 'bounce') {
        const a = 7.5625, b = 2.75;
        if (p < 1 / b)
            return a * p * p;
        if (p < 2 / b) {
            p -= 1.5 / b;
            return a * p * p + .75;
        }
        if (p < 2.5 / b) {
            p -= 2.25 / b;
            return a * p * p + .9375;
        }
        p -= 2.625 / b;
        return a * p * p + .984375;
    }
    return smooth(p);
}
function charsOf(text) {
    if (typeof text !== 'string' || [...text].length > 2048)
        throw new RangeError('Text limit: 2048 scalars');
    return [...text].map(c => /[\x00-\x1f\x7f-\x9f]/.test(c) ? ' ' : c);
}
function timing(chars, o) {
    const indices = chars.map((_, i) => i);
    if (o.randomOrder)
        indices.sort((a, b) => randomAt(o.seed, a) - randomAt(o.seed, b) || a - b);
    else if (o.effect === 'sweep-right' || o.effect === 'comet-stitch' && o.reverseOrder)
        indices.reverse();
    if (o.reverseOrder && o.effect !== 'comet-stitch')
        indices.reverse();
    const rank = new Map(indices.map((id, i) => [id, i]));
    return chars.map((_, i) => ({ start: o.delayMs + Math.floor(rank.get(i) / o.batchSize) * o.staggerMs, duration: o.durationMs * (1 + o.speedJitter * (randomAt(o.seed, i * 7 + 3) * 2 - 1)) }));
}
/** Exact completion bound, including all delays. Does not round by frame rate. */
export function atelierTextDuration(text, patch = {}) {
    const o = atelierTextOptions(patch), c = charsOf(text);
    if (o.local || o.effect === 'instant')
        return 0;
    return Math.ceil(Math.max(0, ...timing(c, o).map(t => t.start + t.duration)));
}
/** Evaluate per-glyph poses at explicit ageMs. Endpoints are exact: show ->
 * original scalars at original columns, hide -> zero opacity. Calling twice
 * never advances a clock or RNG. Text remains available to semantic readers.
 * Example: sampleAtelierText('HELLO','show',400,{effect:'flipboard',batchSize:2}). */
export function sampleAtelierText(text, phase, ageMs, patch = {}) {
    finite(ageMs, 0, Number.MAX_SAFE_INTEGER, 'text age');
    if (!['show', 'hide'].includes(phase))
        throw new RangeError('Text phase');
    const o = atelierTextOptions(patch), chars = charsOf(text), times = timing(chars, o), alphabet = [...o.alphabet];
    return chars.map((glyph, index) => {
        const instant = o.local || o.effect === 'instant', localAge = ageMs - times[index].start, p = instant ? 1 : times[index].duration === 0 ? (localAge >= 0 ? 1 : 0) : clamp(localAge / times[index].duration, 0, 1), q = atelierEase(p, o.easing, o.overshoot), visibility = phase === 'show' ? p : 1 - p, away = phase === 'show' ? 1 - q : q;
        const pose = { index, glyph, x: index, y: 0, opacity: visibility, hueDelta: 0, settled: p === 1, trail: [] };
        if (o.local || o.effect === 'instant') {
            pose.opacity = phase === 'show' || o.local ? 1 : 0;
            return pose;
        }
        if (p === 1) {
            pose.opacity = phase === 'show' ? 1 : 0;
            return pose;
        }
        const r = randomAt(o.seed, index * 7), r2 = randomAt(o.seed, index * 7 + 1), sign = phase === 'show' ? -1 : 1;
        if (o.effect === 'fade')
            pose.opacity = smooth(visibility);
        if (o.effect === 'rain') {
            pose.x = index + (r - .5) * o.spreadColumns * away + Math.sin(p * Math.PI) * (r2 - .5) * o.drift;
            pose.y = sign * o.travelRows * (.4 + r2 * .6) * away;
            pose.opacity = phase === 'show' ? Math.min(1, p * 3) : Math.min(1, (1 - p) * 2);
        }
        if (o.effect === 'scramble') {
            if (localAge >= 0 && p < 1) {
                const n = Math.floor(localAge * o.cycleHz / 1000);
                pose.glyph = alphabet[Math.floor(randomAt(o.seed ^ index, n) * alphabet.length)];
            }
            pose.opacity = phase === 'show' ? Math.min(1, p * 5) : 1 - p;
        }
        if (o.effect === 'flipboard') {
            const targetGlyph = phase === 'show' ? glyph : ' ', board = alphabet.includes(targetGlyph) ? alphabet : [...alphabet, targetGlyph], target = board.indexOf(targetGlyph), steps = Math.floor(Math.max(0, localAge) * o.cycleHz / 1000), totalSteps = Math.max(1, Math.ceil(times[index].duration * o.cycleHz / 1000)), start = ((target - totalSteps) % board.length + board.length) % board.length;
            pose.glyph = localAge < 0 ? (phase === 'show' ? ' ' : glyph) : board[(start + Math.min(totalSteps, steps)) % board.length];
            pose.y = Math.sin(Math.max(0, localAge) * o.cycleHz * Math.PI / 1000) * away * .35;
            pose.opacity = phase === 'show' ? Math.min(1, p * 7) : 1 - p;
        }
        if (o.effect === 'sweep-left' || o.effect === 'sweep-right') {
            pose.x = index + (o.effect === 'sweep-left' ? -1 : 1) * o.spreadColumns * away;
            pose.opacity = smooth(visibility);
        }
        if (o.effect === 'lift' || o.effect === 'fall') {
            pose.y = (o.effect === 'lift' ? 1 : -1) * o.travelRows * away * (phase === 'hide' ? -1 : 1);
            pose.opacity = smooth(visibility);
        }
        if (o.effect === 'marquee') {
            pose.x = index + (phase === 'show' ? 1 : -1) * (chars.length + o.spreadColumns) * away;
            pose.opacity = visibility;
        }
        if (o.effect === 'iris') {
            pose.x = (chars.length - 1) / 2 + (index - (chars.length - 1) / 2) * (1 - away);
            pose.opacity = visibility;
        }
        if (o.effect === 'constellation') {
            const angle = r * Math.PI * 2 + away * o.turns * Math.PI * 2;
            pose.x = index + Math.cos(angle) * o.spreadColumns * away;
            pose.y = Math.sin(angle) * o.travelRows * away;
            pose.hueDelta = o.hueSpread * away;
            pose.opacity = visibility;
        }
        if (o.effect === 'prism-weave') {
            pose.x = index + Math.sin((index % 3) * Math.PI * 2 / 3 + away * Math.PI * 2) * o.spreadColumns * away;
            pose.y = (index % 2 ? 1 : -1) * o.travelRows * away;
            pose.hueDelta = (index % 3 - 1) * o.hueSpread * away;
            pose.opacity = visibility;
        }
        if (o.effect === 'ink-tide') {
            pose.y = Math.sin(index * .55 - away * Math.PI * 2) * o.travelRows * away;
            pose.x = index + o.drift * away;
            pose.opacity = visibility;
        }
        if (o.effect === 'comet-stitch') {
            pose.x = index - o.spreadColumns * away;
            pose.y = -Math.sin(p * Math.PI) * o.travelRows * (.4 + r * .6);
            pose.hueDelta = away * o.hueSpread;
            pose.opacity = visibility;
        }
        if (o.effect === 'orbit') {
            const a = away * o.turns * Math.PI * 2;
            pose.x = index + Math.sin(a) * o.spreadColumns * away;
            pose.y = Math.cos(a) * o.travelRows * away;
            pose.opacity = visibility;
        }
        if (o.effect === 'fold') {
            pose.x = index + (index % 2 ? 1 : -1) * o.spreadColumns * away;
            pose.y = -o.travelRows * Math.sin(away * Math.PI / 2);
            pose.opacity = visibility;
        }
        if (o.effect === 'zipper') {
            pose.x = index + (index % 2 ? 1 : -1) * o.spreadColumns * away * .4;
            pose.y = (index % 2 ? 1 : -1) * o.travelRows * away;
            pose.opacity = visibility;
        }
        if (localAge < 0) {
            if (phase === 'show')
                pose.opacity = 0;
            else
                Object.assign(pose, { x: index, y: 0, glyph, opacity: 1, hueDelta: 0 });
        }
        if (o.trailLength && ['rain', 'comet-stitch', 'constellation', 'orbit', 'prism-weave'].includes(o.effect))
            for (let j = 1; j <= o.trailLength; j++)
                pose.trail.push({ x: pose.x - o.drift * j * .15, y: pose.y - sign * j * .45, opacity: clamp(pose.opacity * away / (j + 2), 0, 1) });
        pose.opacity = clamp(pose.opacity, 0, 1);
        return pose;
    });
}
/** Retargetable choreography with continuity of glyph position and opacity.
 * show()/hide() capture the current visual state. Reversal starts there instead
 * of snapping to a canned endpoint. Text modifications belong to a new player;
 * local draft editing must never be fed into a delayed reveal player. */
export class AtelierTextPlayer {
    constructor(text, options = {}) {
        this.phase = 'show';
        this.started = 0;
        this.initial = null;
        this.active = false;
        charsOf(text);
        this.text = text;
        this.options = atelierTextOptions(options);
    }
    start(phase, timeMs) { finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'text time'); const before = this.active ? this.sample(timeMs) : null; this.phase = phase; this.started = timeMs; this.initial = before; this.active = true; }
    show(timeMs) { this.start('show', timeMs); }
    hide(timeMs) { this.start('hide', timeMs); }
    configure(patch, timeMs) {
        const next = atelierTextOptions({ ...this.options, ...patch });
        if (timeMs !== undefined) {
            finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'text time');
            const before = this.sample(timeMs);
            this.initial = before;
            this.started = timeMs;
            this.active = true;
        }
        this.options = next;
    }
    sample(timeMs) {
        finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'text time');
        const age = Math.max(0, timeMs - this.started), base = sampleAtelierText(this.text, this.phase, age, this.options);
        if (!this.initial)
            return base;
        const total = atelierTextDuration(this.text, this.options), p = smooth(total === 0 ? 1 : age / total);
        if (p === 0)
            return this.initial.map(g => ({ ...g, trail: g.trail.map(t => ({ ...t })) }));
        if (p === 1)
            return base;
        const initialDefault = sampleAtelierText(this.text, this.phase, 0, this.options);
        return base.map((g, i) => { const from = this.initial[i], canonical = initialDefault[i]; return { ...g, x: g.x + (from.x - canonical.x) * (1 - p), y: g.y + (from.y - canonical.y) * (1 - p), opacity: clamp(g.opacity + (from.opacity - canonical.opacity) * (1 - p), 0, 1) }; });
    }
}

