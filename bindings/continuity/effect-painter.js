import {mixColor,flattened,putCell,drawSegment,ObservatoryRenderer} from './observatory.js';
import {sampleAtelierBurst} from './atelier-particles.js';
import {sampleThermal} from './effect-catalog.js';
import {KineticRenderer} from './kinetic-renderer.js';
import {Projector,sampleWorldEvent} from './black-hole-space.js';
export class EffectPainter {
    constructor(engine) {
        this.engine = engine;
        this.kinetic = new KineticRenderer(engine);
        this.original = new ObservatoryRenderer(engine);
    }
    /** At most 24 live effects; 2400 total point budget for native volumetric
     * effects. Small 80×44 local layers bound older full-surface samplers. */
    paint(frame, m, color) {
        const active = m.effectShelf.events.filter(e => m.motionMs >= e.atMs && m.motionMs - e.atMs < e.lifeMs);
        const p = new Projector(m.camera.snapshot(), frame.width, frame.height), count = Math.min(160, Math.floor(2400 / Math.max(1, active.length)));
        for (const e of active) {
            if (e.backend === 'thermal')
                this.thermal(frame, p, e, m.motionMs, color);
            else if (e.backend === 'world' && e.kind !== 'ripples') {
                const points = sampleWorldEvent({ id: e.id, kind: e.kind, atMs: e.atMs, position: e.space === 'world' ? e.origin : { x: 0, y: 0, z: 0 }, seed: e.seed, lifeMs: e.lifeMs, scale: .65 }, m.motionMs, count, e.particles.gravity);
                for (const q of points) {
                    const a = e.space === 'world' ? p.project(q) : { x: e.origin.x + q.x, y: e.origin.y - q.y * .5, z: 40 };
                    if (!a)
                        continue;
                    const c = color(q.hue);
                    if (q.previous) {
                        const b = e.space === 'world' ? p.project(q.previous) : { x: e.origin.x + q.previous.x, y: e.origin.y - q.previous.y * .5 };
                        if (b)
                            drawSegment(frame, a.x, a.y, b.x, b.y, c, q.opacity * .65);
                    }
                    putCell(frame, a.x, a.y, q.glyph, c, q.opacity * .9);
                }
            }
            else
                this.local(frame, m, p, e, color);
        }
        return active.length;
    }
    thermal(frame, p, e, now, color) {
        const geometry = sampleThermal(e.kind, e.seed, now - e.atMs, e.lifeMs);
        // New thermals use WORLD +Y for rise, not the camera-up vector. Screen mode
        // keeps the same local trajectory with an explicit 2:1 terminal cell aspect.
        const project = (v) => e.space === 'world' ? p.project({ x: e.origin.x + v.x, y: e.origin.y + v.y, z: e.origin.z + v.z }) : { x: e.origin.x + v.x, y: e.origin.y - v.y * .5, z: 45 };
        for (const line of geometry.segments) {
            const a = project(line.a), b = project(line.b);
            if (a && b)
                drawSegment(frame, a.x, a.y, b.x, b.y, color(line.hue), line.opacity);
        }
        for (const point of geometry.points) {
            const a = project(point);
            if (a)
                putCell(frame, a.x, a.y, point.glyph.codePointAt(0), color(point.hue), point.opacity);
        }
    }
    local(dest, m, p, e, color) {
        const w = 80, h = 44, cx = 40, cy = 22;
        let f = { width: w, height: h, cells: new Uint32Array(w * h * 4) };
        for (let i = 0; i < w * h; i++)
            f.cells[i * 4] = 32;
        const proxy = Object.create(m);
        proxy.width = w;
        proxy.height = h;
        proxy.motionMs = m.motionMs;
        proxy.particles = { ...e.particles, seed: e.seed };
        proxy.events = [{ id: e.id, x: cx, y: cy, atMs: e.atMs, kind: e.kind, glyph: '*' }];
        const o = { ...m.effective(), novaRegularity: 0, weatherLifeMs: e.lifeMs, weatherIntensity: .6, novaStrength: .85 };
        if (e.backend === 'studio') {
            const cfg = this.engine.defaults({ width: w, height: h, stars: 0, pattern: 0, brightness: 0, novaChance: 0, baseColor: 0, rippleLifeMs: e.lifeMs, rippleOpacity: 700, rippleRings: 3, rippleSpeed: 2304, novaDurationMs: e.lifeMs });
            f = this.engine.render(cfg, m.motionMs, [], [{ x: cx, y: cy, atMs: e.atMs, id: e.id, kind: e.kind === 'nova' ? 1 : 0, strength: 1000 }]);
        }
        else if (e.backend === 'observatory')
            this.original.paintWeatherLayer(f, proxy, o);
        else if (e.backend === 'kinetic')
            this.kinetic.paintWeatherLayer(f, proxy, o);
        else if (e.backend === 'atelier') {
            const burst = sampleAtelierBurst({ id: e.seed, x: cx, y: cy, atMs: e.atMs, kind: e.kind }, m.motionMs, { lifeMs: e.lifeMs, seed: e.seed });
            for (const s of burst.segments)
                drawSegment(f, s.x1, s.y1, s.x2, s.y2, color(30 + s.heat * 70), s.alpha);
            for (const g of burst.glows)
                for (let y = Math.max(0, Math.floor(g.y - g.radius)); y < Math.min(h, g.y + g.radius + 1); y++)
                    for (let x = Math.max(0, Math.floor(g.x - g.radius * 2)); x < Math.min(w, g.x + g.radius * 2 + 1); x++) {
                        const d = Math.hypot((x - g.x), (y - g.y) * 2), alpha = (g.ring ? Math.max(0, 1 - Math.abs(d - g.radius) / 1.2) : Math.max(0, 1 - d / Math.max(.2, g.radius * 2))) * g.alpha;
                        if (alpha > .004) {
                            const k = (y * w + x) * 4;
                            f.cells[k + 2] = mixColor(f.cells[k + 2], color(40 + g.heat * 30), alpha);
                        }
                    }
            for (const q of burst.points)
                putCell(f, q.x, q.y, q.glyph.codePointAt(0), color(35 + q.heat * 75), q.alpha);
        }
        else { // Rich world ripple, represented on its immutable emitter plane.
            const cfg = this.engine.defaults({ width: w, height: h, stars: 0, pattern: 0, brightness: 0, novaChance: 0, baseColor: 0, rippleLifeMs: e.lifeMs, rippleOpacity: 600, rippleRings: 4, rippleSpeed: 2048 });
            f = this.engine.render(cfg, m.motionMs, [], [{ x: cx, y: cy, atMs: e.atMs, id: e.id, kind: 0 }]);
        }
        for (let y = 0; y < h; y++)
            for (let x = 0; x < w; x++) {
                const k = (y * w + x) * 4, g = f.cells[k], fg = f.cells[k + 1], bg = f.cells[k + 2];
                if (!bg && (g === 32 || !fg))
                    continue;
                const dx = x - cx, dy = -(y - cy) * 2, u = e.unitsPerCell;
                const q = e.space === 'screen' ? { x: e.origin.x + dx, y: e.origin.y + (y - cy), z: 45 } : p.project({ x: e.origin.x + (e.right.x * dx + e.up.x * dy) * u, y: e.origin.y + (e.right.y * dx + e.up.y * dy) * u, z: e.origin.z + (e.right.z * dx + e.up.z * dy) * u });
                if (!q)
                    continue;
                const xx = Math.round(q.x), yy = Math.round(q.y);
                if (xx < 0 || yy < 0 || xx >= dest.width || yy >= dest.height)
                    continue;
                const at = (yy * dest.width + xx) * 4;
                if (bg)
                    dest.cells[at + 2] = mixColor(flattened(dest, at), bg, .7);
                if (g !== 32 && fg)
                    putCell(dest, xx, yy, g, fg, .95);
            }
    }
}

