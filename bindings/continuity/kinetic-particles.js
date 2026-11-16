import {clamp,finite,randomAt} from './observatory.js';
/** Analytic, seeded terminal weather. All ages are milliseconds; distances are cells. */
export const DEFAULT_PARTICLE_OPTIONS = { count: 52, lifeMs: 5000, launchSpeed: 12, gravity: 8, drag: .65, wind: 1.2, flickerHz: 18, trailMs: 90, branches: 5, arcSegments: 10, arcJitter: 1.2, coreMs: 260, shockwave: 0, explosionForce: 48, seed: 2030, brightness: .85, glyphs: '·∙⋅*+⠁⠂⠄', emberSpread: 5, arcReach: 17 };
export const PARTICLE_CONTROLS = { count: [1, 160, 1, 'particles'], lifeMs: [100, 12000, 50, 'ms'], launchSpeed: [0, 40, .5, 'cells/s'], gravity: [0, 40, .5, 'cells/s²'], drag: [0, 5, .05, '1/s'], wind: [-20, 20, .2, 'cells/s'], flickerHz: [0, 60, 1, 'Hz'], trailMs: [0, 400, 5, 'ms'], branches: [1, 12, 1, 'branches'], arcSegments: [3, 24, 1, 'segments'], arcJitter: [0, 6, .1, 'cells'], coreMs: [0, 1500, 10, 'ms'], shockwave: [0, 1, .02, 'opacity'], explosionForce: [1, 70, .5, 'cells/s'], seed: [0, 4294967295, 1, 'integer'], brightness: [0, 1, .01, 'mix'], emberSpread: [0, 20, .2, 'cells/s'], arcReach: [1, 45, .5, 'cells'] };
/** Validate/own a weather configuration. Invalid input throws without changing a caller's state. */
export function validateParticleOptions(input = {}) {
    const o = { ...DEFAULT_PARTICLE_OPTIONS, ...input };
    for (const k of Object.keys(input))
        if (!(k in o) || (!(k in PARTICLE_CONTROLS) && k !== 'glyphs'))
            throw new Error(`Unknown particle option ${k}`);
    for (const [k, [lo, hi]] of Object.entries(PARTICLE_CONTROLS)) {
        finite(o[k], lo, hi, k);
        if (['count', 'branches', 'arcSegments', 'seed'].includes(k) && !Number.isInteger(o[k]))
            throw new Error(`${k} must be integer`);
    }
    if (typeof o.glyphs !== 'string' || [...o.glyphs].length < 1 || [...o.glyphs].length > 64 || /[\u0000-\u001f\u007f-\u009f]/.test(o.glyphs))
        throw new Error('Particle glyphs must contain 1..64 printable scalar characters');
    return o;
}
function rand(seed, i, salt) { return randomAt((seed ^ (salt * 2246822519)) >>> 0, i); }
/** Ember position has a real apex: upward launch, lateral drift, then gravity-driven descent. */
export function sampleEmber(index, ageMs, seed, input = {}) {
    const o = validateParticleOptions(input), t = Math.max(0, ageMs) / 1000;
    const vy = o.launchSpeed * (.72 + .55 * rand(seed, index, 11)), vx = (rand(seed, index, 12) - .5) * o.emberSpread;
    const decay = o.drag ? (1 - Math.exp(-o.drag * t)) / o.drag : t;
    const x = vx * decay + o.wind * t + .4 * Math.sin(t * 3 + rand(seed, index, 13) * 6) * t;
    const y = -vy * t + .5 * o.gravity * t * t;
    const life = o.lifeMs * (.9 + .1 * rand(seed, index, 14)), fade = clamp(1 - ageMs / life, 0, 1);
    const flicker = .35 + .65 * rand(seed, index, Math.floor(ageMs * o.flickerHz / 1000) + 201);
    const g = [...o.glyphs];
    return { x, y, opacity: Math.pow(fade, .65) * flicker * o.brightness, size: 1, heat: .1 + .4 * fade, glyph: g[Math.floor(rand(seed, index, 16) * g.length)] };
}
/** Evaluate a finite burst without mutable particle accumulators or dependence on frame count. */
export function sampleWeather(event, timeMs, input = {}) {
    const o = validateParticleOptions(input);
    finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'timeMs');
    finite(event.atMs, 0, Number.MAX_SAFE_INTEGER, 'event.atMs');
    finite(event.id, 0, Number.MAX_SAFE_INTEGER, 'event.id');
    finite(event.x, -100000, 100000, 'event.x');
    finite(event.y, -100000, 100000, 'event.y');
    const age = timeMs - event.atMs, t = age / 1000, life = o.lifeMs, seed = (o.seed ^ (event.id * 2654435761)) >>> 0;
    const r = { points: [], segments: [], core: 0, radius: 0, shockwave: 0, kind: event.kind };
    if (age < 0 || age >= life)
        return r;
    const fade = Math.pow(1 - age / life, 1.5), glyphs = [...o.glyphs];
    const point = (x, y, a, heat, glyph, size = 1) => r.points.push({ x: event.x + x, y: event.y + y, opacity: clamp(a, 0, 1), heat, glyph, size });
    const segment = (x1, y1, x2, y2, a, heat, branch = 0) => r.segments.push({ x1: event.x + x1, y1: event.y + y1, x2: event.x + x2, y2: event.y + y2, opacity: clamp(a, 0, 1), heat, branch });
    if (event.kind === 'embers') {
        for (let i = 0; i < o.count; i++) {
            const delay = rand(seed, i, 9) * 180, a = age - delay;
            if (a < 0)
                continue;
            const p = sampleEmber(i, a, seed, o);
            point(p.x, p.y, p.opacity, p.heat, p.glyph);
            if (o.trailMs && p.opacity > .02) {
                const q = sampleEmber(i, Math.max(0, a - o.trailMs), seed, o);
                segment(q.x, q.y, p.x, p.y, p.opacity * .25, p.heat);
            }
        }
    }
    else if (event.kind === 'sparks') {
        const envelope = Math.exp(-age / Math.max(100, life * .22));
        const flicker = .45 + .55 * rand(seed, Math.floor(age * Math.max(1, o.flickerHz) / 1000), 43);
        r.core = Math.exp(-age / Math.max(1, o.coreMs)) * .65 * o.brightness;
        // Shared endpoints make actual connected arcs, not unrelated flying punctuation.
        for (let b = 0; b < o.branches; b++) {
            const angle = rand(seed, b, 44) * Math.PI * 2, reach = o.arcReach * (.5 + .5 * rand(seed, b, 45)) * (.4 + .6 * Math.min(1, age / 90));
            let x = 0, y = 0;
            for (let j = 1; j <= o.arcSegments; j++) {
                const u = j / o.arcSegments, jit = (rand(seed, b * 37 + j, Math.floor(age * Math.max(1, o.flickerHz) / 1000) + 51) - .5) * o.arcJitter;
                const nx = Math.cos(angle) * reach * u - Math.sin(angle) * jit, ny = (Math.sin(angle) * reach * u + Math.cos(angle) * jit) * .5;
                segment(x, y, nx, ny, envelope * flicker * o.brightness, .85, b);
                if (j % 3 === 0) {
                    const a2 = angle + (rand(seed, j, b + 71) - .5) * 2.3, len = reach * .23;
                    segment(nx, ny, nx + Math.cos(a2) * len, ny + Math.sin(a2) * len * .5, envelope * .65 * o.brightness, 1, b + 1);
                    point(nx, ny, envelope * flicker * o.brightness, 1, '*');
                }
                x = nx;
                y = ny;
            }
        }
        for (let i = 0; i < Math.min(o.count, 40); i++) {
            const a = rand(seed, i, 84) * Math.PI * 2, v = o.explosionForce * (.3 + .7 * rand(seed, i, 85));
            point(Math.cos(a) * v * t, Math.sin(a) * v * t * .5 + .6 * t * t, fade * Math.exp(-t * 2) * o.brightness, .75, glyphs[i % glyphs.length]);
        }
    }
    else if (event.kind === 'nova') {
        r.core = o.coreMs ? Math.sqrt(clamp(1 - age / o.coreMs, 0, 1)) * o.brightness : 0;
        r.radius = o.explosionForce * t;
        r.shockwave = o.shockwave * fade;
        for (let i = 0; i < o.count; i++) {
            const a = rand(seed, i, 91) * Math.PI * 2, v = o.explosionForce * (.3 + .9 * rand(seed, i, 92)), d = o.drag ? (1 - Math.exp(-o.drag * t)) / o.drag : t;
            const x = Math.cos(a) * v * d, y = Math.sin(a) * v * d * .5;
            const exposure = Math.max(0, t - o.trailMs / 1000), previous = o.drag ? (1 - Math.exp(-o.drag * exposure)) / o.drag : exposure;
            const flicker = .4 + .6 * rand(seed, i, Math.floor(age * o.flickerHz / 1000) + 100), a0 = fade * flicker * o.brightness;
            point(x, y, a0, .3 + .7 * fade, age < 150 ? '*' : glyphs[i % glyphs.length]);
            segment(Math.cos(a) * v * previous, Math.sin(a) * v * previous * .5, x, y, a0 * .9, .7);
            if (age < o.coreMs * 2 && i < 20)
                segment(x * .15, y * .15, x * 1.4, y * 1.4, Math.exp(-age / 180) * o.brightness, .95);
        }
    }
    else if (event.kind === 'rain' || event.kind === 'snow') {
        for (let i = 0; i < o.count; i++) {
            const delay = rand(seed, i, 120) * life * .6, lt = (age - delay) / 1000;
            if (lt < 0)
                continue;
            const v = o.launchSpeed * (.4 + rand(seed, i, 121));
            const x = (rand(seed, i, 122) - .5) * 24 + o.wind * lt + (event.kind === 'snow' ? Math.sin(lt * 2 + i) * 1.7 : 0), y = -8 + v * lt;
            point(x, y, fade * o.brightness, .6, event.kind === 'snow' ? '·' : '│');
        }
    }
    else if (event.kind === 'ripples') {
        r.radius = o.explosionForce * t;
        r.shockwave = fade * o.brightness;
    }
    else
        throw new Error(`Unknown weather kind ${event.kind}`);
    return r;
}

