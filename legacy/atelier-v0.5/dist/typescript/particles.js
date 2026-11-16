/** Analytic cell-space particle choreography. No clocks, accumulated integration
 * error or mutable random stream. y increases DOWN. Embers have upward impulse
 * then positive gravity; electrical sparks are branching polylines, not rings. */
import { clamp, finite, randomAt, TAU } from './observatory.js';
export const DEFAULT_PARTICLE_OPTIONS = { lifeMs: 4200, count: 64, speed: 20, gravity: 9, rise: 10, drag: .22, turbulence: 1.3, glitterHz: 14, trailMs: 100, branches: 7, jaggedness: 2.2, coreMs: 280, coreRadius: 3, ejecta: 1, shockwave: 0, intensity: .8, seed: 4711, reducedMotion: false };
export const PARTICLE_RANGES = { lifeMs: [200, 10000, 50], count: [0, 256, 1], speed: [0, 70, .5], gravity: [0, 35, .5], rise: [0, 40, .5], drag: [0, 3, .05], turbulence: [0, 8, .1], glitterHz: [1, 30, 1], trailMs: [0, 400, 10], branches: [1, 20, 1], jaggedness: [0, 8, .1], coreMs: [0, 600, 10], coreRadius: [0, 6, .1], ejecta: [0, 2, .05], shockwave: [0, 1, .02], intensity: [0, 1, .02], seed: [0, 4294967295, 1] };
export function particleOptions(patch = {}) { const o = { ...DEFAULT_PARTICLE_OPTIONS, ...patch }; for (const k of Object.keys(patch))
    if (!(k in DEFAULT_PARTICLE_OPTIONS))
        throw new RangeError('Unknown particle option ' + k); for (const [k, [a, b]] of Object.entries(PARTICLE_RANGES))
    finite(o[k], a, b, k); for (const k of ['count', 'branches', 'seed'])
    if (!Number.isInteger(o[k]))
        throw new RangeError(k + ' integer required'); if (typeof o.reducedMotion !== 'boolean')
    throw new RangeError('reducedMotion'); return o; }
/** sampleBurst(event, nowMs, options) returns owned primitives. Heat is a 0..1
 * palette selector, not a temperature reading. Timeline and position units:
 * milliseconds, terminal cells (vertical geometry uses 2:1 cell aspect). */
export function sampleBurst(e, nowMs, patch = {}) {
    const o = particleOptions(patch);
    for (const v of [e.id, e.x, e.y, e.atMs, nowMs])
        finite(v, -1e12, 1e12, 'burst field');
    const out = { points: [], segments: [], glows: [] }, age = nowMs - e.atMs;
    if (age < 0 || age >= o.lifeMs || o.reducedMotion || o.intensity === 0)
        return out;
    const s = age / 1000, p = age / o.lifeMs, seed = (e.id ^ o.seed) >>> 0, fade = (1 - p) ** 1.8;
    const point = (x, y, glyph, alpha, heat) => out.points.push({ x, y, glyph, alpha: clamp(alpha * o.intensity, 0, 1), heat: clamp(heat, 0, 1) });
    const segment = (x1, y1, x2, y2, alpha, heat) => out.segments.push({ x1, y1, x2, y2, alpha: clamp(alpha * o.intensity, 0, 1), heat: clamp(heat, 0, 1) });
    if (e.kind === 'sparks') {
        const strikeLife = Math.min(o.lifeMs, 1100), a = clamp(1 - age / strikeLife, 0, 1);
        if (a === 0)
            return out;
        const flash = Math.floor(age / Math.max(34, 1000 / o.glitterHz)), jitter = .65 + .35 * randomAt(seed, flash + 901);
        for (let branch = 0; branch < o.branches; branch++) {
            const angle = randomAt(seed, branch * 41) * TAU, length = o.speed * (.2 + .8 * randomAt(seed, branch * 41 + 1)) * (.45 + .55 * Math.min(1, s * 8)), n = 8;
            let x = e.x, y = e.y;
            for (let j = 1; j <= n; j++) {
                const q = j / n, kink = (randomAt(seed ^ (branch + 17), flash * 97 + j) - .5) * o.jaggedness * Math.sin(q * Math.PI);
                const xx = e.x + Math.cos(angle) * length * q + Math.sin(angle) * kink, yy = e.y + Math.sin(angle) * length * q * .5 - Math.cos(angle) * kink * .5;
                segment(x, y, xx, yy, a * jitter * (1 - q * .4), .8 + q * .2);
                if (j === 4 || j === 6) {
                    const fork = angle + (j === 4 ? .8 : -.8), len = length * .28;
                    segment(xx, yy, xx + Math.cos(fork) * len, yy + Math.sin(fork) * len * .5, a * .6, .65);
                }
                x = xx;
                y = yy;
            }
            point(x, y, flash % 3 === 0 ? '✧' : '·', a, .98);
        }
        out.glows.push({ x: e.x, y: e.y, radius: 1.2, alpha: a * .3 * o.intensity, heat: 1 });
        return out;
    }
    if (e.kind === 'nova') {
        const core = o.coreMs ? clamp(1 - age / o.coreMs, 0, 1) : 0;
        if (core > 0)
            out.glows.push({ x: e.x, y: e.y, radius: o.coreRadius * (.5 + age / Math.max(1, o.coreMs)), alpha: core * .8 * o.intensity, heat: 1 });
        for (let j = 0; j < Math.floor(o.count * o.ejecta); j++) {
            const a = randomAt(seed, j * 13) * TAU, v = o.speed * (.28 + randomAt(seed, j * 13 + 1)), length = v * (1 - Math.exp(-s * .7)) / .7, r = length;
            const x = e.x + Math.cos(a) * r, y = e.y + Math.sin(a) * r * .5 + .2 * s * s, tail = Math.max(0, s - o.trailMs / 1000), r0 = v * (1 - Math.exp(-tail * .7)) / .7;
            const flicker = randomAt(seed + j, Math.floor(s * o.glitterHz)), alpha = fade * (.25 + .75 * flicker), heat = clamp(1 - p * .8 - j / o.count * .2, 0, 1);
            segment(e.x + Math.cos(a) * r0, e.y + Math.sin(a) * r0 * .5, x, y, alpha, heat);
            point(x, y, flicker > .94 ? '✧' : flicker > .65 ? '∙' : '·', alpha, heat);
        }
        for (let j = 0; j < 12; j++) {
            const a = j * TAU / 12 + randomAt(seed, j) * .2, r = o.speed * s * .7;
            segment(e.x + Math.cos(a) * r * .15, e.y + Math.sin(a) * r * .075, e.x + Math.cos(a) * r, e.y + Math.sin(a) * r * .5, Math.exp(-s * 5) * .75, 1);
        }
        // Core is topmost, not overwritten by ejecta still near the origin.
        if (age < 450)
            point(e.x, e.y, age < 90 ? '✶' : age < 180 ? '✹' : '✧', Math.exp(-age / 220), 1);
        if (age > 180 && o.shockwave > 0)
            out.glows.push({ x: e.x, y: e.y, radius: o.speed * s * 1.1, alpha: fade * o.shockwave * o.intensity, heat: .6, ring: true });
        return out;
    }
    for (let j = 0; j < o.count; j++) {
        const r = randomAt(seed, j * 5), r2 = randomAt(seed, j * 5 + 1), q = randomAt(seed, j * 5 + 2), glint = randomAt(seed + j, Math.floor(s * o.glitterHz));
        let x = e.x, y = e.y, heat = .8, glyph = '·';
        const emberAt = (t) => ({ x: e.x + (r - .5) * o.speed * t / (1 + o.drag * t) + Math.sin(t * 2 + r2 * TAU) * o.turbulence * t, y: e.y - o.rise * (.6 + r2 * .4) * t + o.gravity * t * t / 2 });
        if (e.kind === 'embers') {
            const at = emberAt(s);
            x = at.x;
            y = at.y;
            heat = .25 + .55 * (1 - p);
            glyph = glint > .9 ? '✧' : glint > .5 ? '∙' : '·';
            if (o.trailMs) {
                const prev = emberAt(Math.max(0, s - o.trailMs / 1000));
                segment(prev.x, prev.y, x, y, fade * .3, heat);
            }
        }
        else if (e.kind === 'rain') {
            x += (r - .5) * 24 + o.turbulence * s;
            y -= r2 * 18;
            y += s * o.speed;
            glyph = j % 3 ? '╱' : '│';
            heat = .7;
        }
        else if (e.kind === 'snow') {
            x += (r - .5) * 32 + Math.sin(s * 1.6 + r2 * TAU) * o.turbulence * 2;
            y -= r2 * 20;
            y += s * o.speed * .22;
            glyph = q > .5 ? '·' : '⋅';
            heat = .8;
        }
        else {
            const a = r * TAU;
            x += Math.cos(a) * s * o.speed * q;
            y += Math.sin(a) * s * o.speed * q * .5;
            glyph = '·';
        }
        point(x, y, glyph, fade * (e.kind === 'embers' ? .25 + .75 * glint : .7), heat);
    }
    if (e.kind === 'ripples')
        out.glows.push({ x: e.x, y: e.y, radius: s * o.speed, alpha: fade * .35 * o.intensity, heat: .65, ring: true });
    return out;
}
