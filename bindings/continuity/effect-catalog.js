import {clamp,finite,randomAt} from './observatory.js';
import {cameraBasis} from './kinetic-camera.js';
import {validateParticleOptions} from './kinetic-particles.js';
/** One explicit inventory of historic effects and new geometry. Instances freeze
 * their event position, seed, clock and parameter snapshot; later controls never
 * stretch an old ripple or change an existing firework's random arrangement. */
const classicKinds = ['nova', 'sparks', 'embers', 'ripples', 'rain', 'snow'];
export const EFFECT_CATALOG = [
    ...['nova', 'ripples'].map(kind => ({ id: 'studio.' + kind, label: 'Studio / Fleet v0.2–0.3 · ' + kind, backend: 'studio', kind, lifeMs: 3600, note: 'Original shared-C expanding glyph and color-front implementation.' })),
    ...classicKinds.map(kind => ({ id: 'observatory.' + kind, label: 'Observatory v0.4 · ' + kind, backend: 'observatory', kind, lifeMs: 3200, note: 'Preserved first Observatory screen-space sampler.' })),
    ...classicKinds.map(kind => ({ id: 'kinetic.' + kind, label: 'Kinetic v0.5 · ' + (kind === 'nova' ? 'nova ejecta / firework' : kind), backend: 'kinetic', kind, lifeMs: 5000, note: 'Original Kinetic algorithm, including connected electrical arcs.' })),
    ...classicKinds.map(kind => ({ id: 'atelier.' + kind, label: 'Parallel Atelier v0.5 · ' + kind, backend: 'atelier', kind, lifeMs: 4200, note: 'Original parallel-release sampler; newly accessible in the current host.' })),
    ...['nova', 'firework', 'sparks', 'embers', 'leaves', 'rain', 'snow', 'ripples'].map(kind => ({ id: 'world.' + kind, label: 'Black Hole v0.7 · ' + kind, backend: 'world', kind, lifeMs: 5000, note: 'Preserved world-space treatment, independent of the current view.' })),
    ...['embers', 'leaves'].map(kind => ({ id: 'thermal.' + kind, label: 'Continuity v0.9 · ' + (kind === 'embers' ? 'thermal embers & cinders' : 'tumbling leaf silhouettes'), backend: 'thermal', kind, lifeMs: 6500, note: 'New finite lifecycle geometry. Historic versions are still separate entries.' }))
];
/** Bounded presentation events; adding an event may retire oldest decoration,
 * never data, text, outgoing commands or any application record. */
export class EffectShelf {
    constructor() {
        this.serial = 0;
        this.events = [];
    }
    add(effectId, atMs, camera, width, height, space, particles, x = width * .5, y = height * .46) {
        const def = EFFECT_CATALOG.find(e => e.id === effectId);
        if (!def)
            throw new RangeError('Unknown effect ' + effectId);
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'effect time');
        finite(x, -4096, 4096, 'effect x');
        finite(y, -4096, 4096, 'effect y');
        if (space !== 'world' && space !== 'screen')
            throw new RangeError('effect space');
        const basis = cameraBasis(camera), focal = width / (2 * Math.tan(camera.fov * Math.PI / 360)), depth = 45, unit = depth / focal;
        const origin = space === 'screen' ? { x, y, z: 0 } : { x: camera.x + basis.forward.x * depth + basis.right.x * (x - width / 2) * unit - basis.up.x * (y - height / 2) * unit * 2, y: camera.y + basis.forward.y * depth + basis.right.y * (x - width / 2) * unit - basis.up.y * (y - height / 2) * unit * 2, z: camera.z + basis.forward.z * depth + basis.right.z * (x - width / 2) * unit - basis.up.z * (y - height / 2) * unit * 2 };
        const options = validateParticleOptions({ ...particles, lifeMs: def.lifeMs });
        const id = ++this.serial, instance = Object.freeze({ id, effectId, backend: def.backend, kind: def.kind, atMs, seed: (id * 2654435761 ^ particles.seed) >>> 0, lifeMs: def.lifeMs, space, origin: Object.freeze(origin), right: Object.freeze({ ...basis.right }), up: Object.freeze({ ...basis.up }), unitsPerCell: unit, particles: Object.freeze(options) });
        this.events = [...this.events.filter(e => atMs - e.atMs < e.lifeMs), instance].slice(-24);
        return instance;
    }
    clear() { this.events = []; }
}
/** Physical-looking, analytic stages: initial hot ascent, entrainment slowdown,
 * terminal-speed descent, stochastic burnout, then a few ground-level cinders.
 * Geometry is local WORLD space (+Y up), no dependence on a camera or frame rate. */
export function sampleThermal(kind, seed, ageMs, lifeMs = 6500) {
    const out = { points: [], segments: [] };
    if (ageMs < 0 || ageMs >= lifeMs)
        return out;
    const t = ageMs / 1000;
    if (kind === 'embers') {
        const at = (i, t0) => {
            const rise = .5 + randomAt(seed, i * 11) * .45, H = 8 + randomAt(seed, i * 11 + 1) * 13, fall = 2.9 + randomAt(seed, i * 11 + 2) * 1.6;
            const y = t0 < rise ? H * (1 - (1 - t0 / rise) ** 2) : H * (1 - clamp((t0 - rise) / fall, 0, 1) ** 1.6);
            const drift = (randomAt(seed, i * 11 + 3) - .5) * 4, swirl = randomAt(seed, i * 11 + 4) * Math.PI * 2;
            return { x: drift * t0 * .55 + Math.sin(t0 * 2.3 + swirl) * Math.min(2, t0 * .6), y: Math.max(0, y), z: (randomAt(seed, i * 11 + 5) - .5) * t0 * 2 + Math.cos(t0 + swirl) * t0 * .2 };
        };
        for (let i = 0; i < 88; i++) {
            const delay = randomAt(seed, i * 11 + 6) * .23, tt = t - delay;
            if (tt < 0)
                continue;
            const survivor = randomAt(seed, i * 11 + 7) < .12, burnout = survivor ? lifeMs / 1000 : 1.25 + randomAt(seed, i * 11 + 8) * 3.1;
            if (tt > burnout)
                continue;
            const p = at(i, tt), ground = p.y < .02, fade = clamp((burnout - tt) / .65, 0, 1), flicker = .5 + .5 * randomAt(seed + i, Math.floor(tt * 12));
            const alpha = fade * flicker * (ground ? .35 : clamp(1 - tt * .075, .3, 1)), heat = clamp(1 - tt / 6, 0, 1);
            out.points.push({ ...p, opacity: alpha, hue: 18 + heat * 38, glyph: ground ? '·' : flicker > .92 ? '✧' : flicker > .75 ? '∙' : '·' });
            if (!ground)
                out.segments.push({ a: at(i, Math.max(0, tt - .055)), b: p, opacity: alpha * .45, hue: 28 + heat * 30 });
        }
    }
    else {
        for (let i = 0; i < 20; i++) {
            const delay = randomAt(seed, i * 9) * .45, tt = t - delay;
            if (tt < 0)
                continue;
            const phase = randomAt(seed, i * 9 + 1) * Math.PI * 2, h = 12 + randomAt(seed, i * 9 + 2) * 10, s = 1.1 + randomAt(seed, i * 9 + 3) * 1.1;
            const center = { x: (randomAt(seed, i * 9 + 4) - .5) * 28 + tt * 1.5 + Math.sin(tt * 1.7 + phase) * 2, y: Math.max(0, h - tt * (2.8 + randomAt(seed, i * 9 + 5))), z: (randomAt(seed, i * 9 + 6) - .5) * 17 + Math.sin(tt * .8 + phase) * 3 };
            const yaw = phase + tt * (.7 + randomAt(seed, i * 9 + 7)), roll = Math.sin(tt * 2 + phase) * 1.15, ca = Math.cos(yaw), sa = Math.sin(yaw), cr = Math.cos(roll), sr = Math.sin(roll);
            const vertex = (x, y) => ({ x: center.x + (x * ca - y * sa) * s, y: center.y + (x * sa + y * ca) * s * cr, z: center.z + (x * sa + y * ca) * s * sr });
            const alpha = clamp((lifeMs / 1000 - tt) / 1.1, 0, 1) * (center.y < .1 ? .65 : 1), hue = 28 + randomAt(seed, i * 9 + 8) * 60;
            const outline = [];
            for (let k = 0; k < 17; k++) {
                const a = k * Math.PI * 2 / 16;
                outline.push(vertex(Math.sin(a) * .48 * Math.sin(a / 2), Math.cos(a)));
            }
            for (let j = 1; j < outline.length; j++)
                out.segments.push({ a: outline[j - 1], b: outline[j], opacity: alpha * .85, hue });
            out.segments.push({ a: vertex(0, -1.25), b: vertex(0, .85), opacity: alpha * .9, hue: hue + 12 });
            for (const v of [-.4, .15, .6])
                out.segments.push({ a: vertex(0, v - .2), b: vertex(.3, v + .05), opacity: alpha * .45, hue: hue + 6 });
        }
    }
    return out;
}

