import {clamp,fract,rgb,mixColor,flattened,putCell,putDot,drawSegment} from './observatory.js';
import {KineticRenderer,activateKinetic} from './kinetic-renderer.js';
import {softStep,distanceInk,Projector,WorldStarfield,sampleWorldEvent} from './black-hole-space.js';
import {BLACK_HOLE_SCENES,BlackHoleModel} from './black-hole-model.js';
export const BLACK_HOLE_CUSTOM_SCENES = ['black-hole', 'infinite', 'graph-explorer', 'git-history', 'world-weather', 'waterfall', 'ocean', 'tarmac', 'dunes', 'impossible', 'forms', 'dashboard', 'code-review'];
const WORLD_SKY_SCENES = ['warp', 'black-hole', 'infinite', 'world-weather', 'fleet-room', 'windows', 'shapes', 'graph-explorer', 'git-history', 'impossible'];
const stamp = () => typeof performance !== 'undefined' ? performance.now() : 0;
const freshTiming = () => ({ backgroundMs: 0, starsMs: 0, weatherMs: 0, compositionMs: 0, totalMs: 0, candidateStars: 0, visibleStars: 0, eventCount: 0, particlePoints: 0, cacheTiles: 0 });
function rawText(f, x, y, text, fg, alpha = 1) { for (const c of text) {
    putCell(f, x++, y, c.codePointAt(0), fg, alpha);
} }
/** Segments are original geometric strokes, not distributed font assets. */
export function segmentedGlyph(frame, char, x, y, w, h, segments, colors, opacity = 1) {
    const lines = [[0, 0, 1, 0], [1, 0, 1, .5], [1, .5, 1, 1], [0, 1, 1, 1], [0, .5, 0, 1], [0, 0, 0, .5], [0, .5, 1, .5], [0, 0, .5, .5], [1, 0, .5, .5], [.5, .5, 1, 1], [.5, .5, 0, 1], [.5, 0, .5, .5], [.5, .5, .5, 1], [0, .25, 1, .25], [0, .75, 1, .75], [0, 0, 1, 1]];
    const maps = { '0': [0, 1, 2, 3, 4, 5], '1': [1, 2], '2': [0, 1, 6, 4, 3], '3': [0, 1, 6, 2, 3], '4': [5, 6, 1, 2], '5': [0, 5, 6, 2, 3], '6': [0, 5, 6, 2, 3, 4], '7': [0, 1, 2], '8': [0, 1, 2, 3, 4, 5, 6], '9': [0, 1, 2, 3, 5, 6], A: [0, 1, 2, 4, 5, 6], B: [0, 1, 2, 3, 6, 11, 12], C: [0, 3, 4, 5], D: [0, 1, 2, 3, 11, 12], E: [0, 3, 4, 5, 6], F: [0, 4, 5, 6], G: [0, 2, 3, 4, 5, 6], H: [1, 2, 4, 5, 6], I: [0, 3, 11, 12], J: [1, 2, 3, 4], K: [4, 5, 8, 9], L: [3, 4, 5], M: [1, 2, 4, 5, 7, 8], N: [1, 2, 4, 5, 7, 9], O: [0, 1, 2, 3, 4, 5], P: [0, 1, 4, 5, 6], Q: [0, 1, 2, 3, 4, 5, 9], R: [0, 1, 4, 5, 6, 9], S: [0, 2, 3, 5, 6], T: [0, 11, 12], U: [1, 2, 3, 4, 5], V: [5, 1, 10, 9], W: [1, 2, 4, 5, 9, 10], X: [7, 8, 9, 10], Y: [7, 8, 12], Z: [0, 8, 10, 3], '-': [6] };
    const active = new Set(maps[char.toUpperCase()] ?? []);
    lines.slice(0, segments).forEach(([ax, ay, bx, by], i) => drawSegment(frame, x + ax * w, y + ay * h, x + bx * w, y + by * h, colors(i), opacity * (active.has(i) ? 1 : .085)));
}
export class BlackHoleRenderer extends KineticRenderer {
    constructor(engine) {
        super(engine);
        this.timing = freshTiming();
        this.starfield = new WorldStarfield();
        this.skyKey = '';
        this.scratch = new Float64Array(3);
        this.trailScratch = new Float64Array(3);
        this.halo = null;
    }
    windowPose(model, id, atMs) {
        const pose = super.windowPose(model, id, atMs);
        if (!(model instanceof BlackHoleModel))
            return pose;
        const c = model.camera.snapshot(), distance = Math.hypot(pose.x - c.x, pose.y - c.y, pose.z - c.z), options = model.spaceWindows.options;
        return { ...pose, opacity: options.opacity / (1 + Math.max(0, distance - 25) * options.depthFade) };
    }
    background(model, o) {
        if (!(model instanceof BlackHoleModel))
            return super.background(model, o);
        const m = model, t0 = stamp(), w = m.width, h = m.height, f = { width: w, height: h, cells: new Uint32Array(w * h * 4) };
        this.base.prepare(m.palette, o);
        const bg = rgb(m.palette.background), ink = rgb(m.palette.ink), t = m.motionMs / 1000, bh = m.effectiveBH();
        const angle = (o.gradientAngle + m.orbit.at(m.motionMs)) * Math.PI / 180, second = (o.axisPitch + m.orbit2.at(m.motionMs)) * Math.PI / 180, ca = Math.cos(angle), sa = Math.sin(angle), cs = Math.cos(second), ss = Math.sin(second), travel = m.travel.at(m.motionMs), scale = 1 / o.gradientScreens;
        const cosmic = WORLD_SKY_SCENES.includes(m.scene), land = ['waterfall', 'ocean', 'tarmac', 'dunes'].includes(m.scene);
        const cx = o.pivotX, cy = o.pivotY;
        this.halo = null;
        if (m.scene === 'black-hole') {
            const p = new Projector(m.camera.snapshot(), w, h), center = p.project({ x: 0, y: 0, z: 140 });
            if (center) {
                this.halo = { x: center.x, y: center.y, radius: p.focal * 13 / center.z, depth: center.z };
            }
        }
        const sample = (x, y) => {
            const u = x / w - cx, v = (y / h - cy) * h * 2 / w;
            if (m.scene === 'black-hole' && this.halo) {
                const H = this.halo, dx = (x - H.x) / H.radius, dy = (y - H.y) * 2 / H.radius, r = Math.hypot(dx, dy), rot = .17, xx = dx * Math.cos(rot) + dy * Math.sin(rot), yy = -dx * Math.sin(rot) + dy * Math.cos(rot), tilt = Math.max(.08, Math.cos(bh.discTilt * Math.PI / 180)), disc = Math.hypot(xx, yy / tilt), a = Math.atan2(yy / tilt, xx), flow = Math.sin(disc * 13 + a * 6 - t * 2.5) * .5 + .5;
                if (r < 1)
                    return 0x06070b;
                const ring = Math.exp(-Math.pow((r - 1.16) / .1, 2)), disk = disc > 1.5 && disc < 4.5 ? softStep((disc - 1.5) * 3) * softStep((4.5 - disc) * 1.8) * (.38 + .62 * flow) : 0, arc = Math.exp(-Math.pow((r - 1.36) / .12, 2)) * (.5 + .5 * Math.sin(a - t)), intensity = Math.min(1, ring * .9 + disk * .85 + arc * .42);
                return mixColor(bg, this.ink(20 + disc * 18 + t * 7), intensity);
            }
            if (m.scene === 'infinite') {
                const rad = Math.max(.045, Math.hypot(u, v)), a = Math.atan2(v, u), pulse = .5 + .5 * Math.sin(13 / rad + a * 7 - t * 4.5), phase = (a / Math.PI + 1 / rad * .12 - t * .4);
                return mixColor(bg, this.base.colorAt(phase), .2 + .8 * pulse);
            }
            if (land)
                return this.landColor(m, x, y, bg, t, bh);
            if (cosmic)
                return mixColor(bg, this.base.colorAt(u * .4 + v * .5 + t * .012), .035);
            let field = u * ca + v * sa;
            switch (o.backgroundStyle) {
                case 'double-axis':
                    field = (u * ca + v * sa) * cs + Math.hypot(u, v) * ss;
                    break;
                case 'wave':
                    field += Math.sin(v * 14 + u * 3 + t * .8) * .22;
                    break;
                case 'plasma':
                    field = (Math.sin(u * 11 + t) + Math.sin(v * 13 - t * .7) + Math.sin((u + v) * 9 + t * .5) + Math.sin(Math.hypot(u + .2, v - .1) * 17 - t * .9)) * .25;
                    break;
                case 'aurora':
                    field = Math.sin(u * 8 + t * .3 + Math.sin(v * 8 - t * .25) * .4) + v * .7;
                    break;
                case 'caustics':
                    field = Math.sin(u * 18 + t * .7) * Math.cos(v * 21 - t * .9) + Math.sin((u - v) * 23 + t * .4) * .45;
                    break;
                case 'moire':
                    field = Math.sin((u * ca + v * sa) * 45) + Math.sin((u * cs + v * ss) * 46);
                    break;
                case 'vortex':
                    field = Math.atan2(v, u) / Math.PI + Math.hypot(u, v) * 4;
                    break;
                case 'tunnel':
                    field = 1 / Math.max(.08, Math.hypot(u, v)) * .08;
                    break;
                case 'diamond':
                    field = Math.abs(u * ca + v * sa) + Math.abs(-u * sa + v * ca);
                    break;
                case 'checker':
                    field = (Math.floor(u * 14) + Math.floor(v * 14)) % 2;
                    break;
                case 'woven':
                    field = Math.sin(u * 16 + t) + Math.cos(v * 18 - t);
                    break;
                case 'contours':
                    field = Math.floor((Math.sin(u * 6) + Math.cos(v * 8)) * 8) / 8;
                    break;
            }
            return this.base.colorAt(field * scale + travel + o.gradientPhase);
        };
        for (let y = 0; y < h; y++)
            for (let x = 0; x < w; x++) {
                const k = (y * w + x) * 4;
                f.cells[k + 3] = 0;
                if (o.sampling === 'half') {
                    f.cells[k] = 0x2580;
                    f.cells[k + 1] = sample(x + .5, y + .25);
                    f.cells[k + 2] = sample(x + .5, y + .75);
                }
                else if (o.sampling === 'vertical') {
                    f.cells[k] = 0x258c;
                    f.cells[k + 1] = sample(x + .25, y + .5);
                    f.cells[k + 2] = sample(x + .75, y + .5);
                }
                else if (o.sampling === 'braille' && !cosmic && !land) {
                    const bits = [1, 8, 2, 16, 4, 32, 64, 128];
                    let mask = 0;
                    for (let j = 0; j < 8; j++) {
                        const c = sample(x + (j % 2 ? .75 : .25), y + (Math.floor(j / 2) + .5) / 4), l = ((c >>> 16) + ((c >>> 8) & 255) + (c & 255)) / 765;
                        if (l > (j + .5) / 32)
                            mask |= bits[j];
                    }
                    f.cells[k] = 0x2800 + mask;
                    f.cells[k + 1] = sample(x + .5, y + .5);
                    f.cells[k + 2] = bg;
                }
                else {
                    f.cells[k] = 32;
                    f.cells[k + 1] = ink;
                    f.cells[k + 2] = sample(x + .5, y + .5);
                }
            }
        this.timing.backgroundMs = stamp() - t0;
        return f;
    }
    landColor(m, x, y, bg, t, bh) {
        const w = m.width, h = m.height, u = x / w, v = y / h, amp = bh.terrainHeight;
        if (m.scene === 'tarmac') {
            const horizon = .35;
            if (v < horizon) {
                const sun = Math.hypot((u - .72) * w, (v - .19) * h * 2);
                return mixColor(0x101725, this.ink(30), Math.exp(-sun * sun / 85) * .8);
            }
            const z = 14 / (v - horizon), worldX = (u - .5) * z * 2.2, phase = z - m.surfaceDistance.at(m.motionMs);
            const lane = Math.abs(worldX) < 14, edge = Math.abs(Math.abs(worldX) - 13) < .32, center = Math.abs(worldX) < .28 && fract(phase / 16) < .55;
            return edge || center ? mixColor(bg, this.ink(center ? 55 : 190), .8) : lane ? mixColor(0x11151c, 0x61717e, .12 + .08 * Math.sin(worldX * 83 + z * 27)) : mixColor(bg, this.ink(65), .14 + .04 * Math.sin(worldX + z * .15));
        }
        if (m.scene === 'waterfall') {
            const cliff = u > .21 && u < .79 && v > .18 && v < .8, flow = bh.waterFlow;
            if (cliff && flow > 0) {
                const strands = Math.sin(u * 267 + Math.sin(u * 33) * 4) + Math.sin(u * 163 + v * 32 - m.waterfallPhase.at(m.motionMs) * 10);
                const alpha = Math.max(0, strands * .25 + .35) * softStep(flow * 3);
                return mixColor(bg, this.ink(175 + v * 75), alpha);
            }
            if (v > .78) {
                const rings = .5 + .5 * Math.sin(Math.hypot((u - .5) * 2, v - .8) * 85 - t * 3);
                return mixColor(bg, this.ink(180), (.1 + .12 * rings) * Math.min(1, flow));
            }
            return mixColor(bg, this.ink(65), .06 + .09 * Math.sin(u * 73 + v * 18) ** 2);
        }
        if (m.scene === 'ocean') {
            if (v < .38) {
                const moon = Math.hypot((u - .73) * w, (v - .2) * h * 2);
                return mixColor(0x101522, 0xc6c8b9, moon < 3.2 ? .85 : Math.exp(-moon * .12) * .1);
            }
            const z = 1 / (v - .32), a = Math.sin(u * 35 + z * 4 + t) + Math.sin(u * 66 - z * 3 + t * .7), foam = Math.pow(Math.max(0, Math.sin(u * 44 + z * 5 - t * 1.6)), 14), mirror = Math.exp(-Math.pow((u - .73) / (.025 + (v - .38) * .15), 2));
            return mixColor(bg, this.ink(182 + a * 20), .18 + foam * .27 * amp + mirror * (.12 + .26 * Math.sin(z * 17 + t) ** 2));
        }
        // Procedural horizon, eroded mountain layers, winding river, dunes and clouds.
        const mountain = .38 + .04 * Math.sin(u * 18) + .025 * Math.sin(u * 53);
        if (v < mountain) {
            const cloud = Math.pow(Math.max(0, Math.sin(u * 15 + t * .06) + Math.sin(u * 8 - v * 29) - 1.1), 2);
            return mixColor(0x17202e, this.ink(235), Math.min(.25, cloud * .14));
        }
        const river = .5 + .2 * Math.sin(v * 8 + t * .02), bank = .006 + (v - .38) * .055;
        if (Math.abs(u - river) < bank)
            return mixColor(bg, this.ink(183), .5 + .2 * Math.sin(v * 58 - t));
        const dune = Math.sin(u * 23 + v * 24 + Math.sin(v * 8) * 2) * .5 + .5;
        return mixColor(bg, this.ink(35 + v * 55), .2 + dune * .35 * amp);
    }
    sky(f, model, o) {
        if (!(model instanceof BlackHoleModel))
            return super.sky(f, model, o);
        const m = model, t0 = stamp();
        if (!WORLD_SKY_SCENES.includes(m.scene)) {
            const n = super.sky(f, m, o);
            this.timing.starsMs = stamp() - t0;
            return n;
        }
        const bh = m.effectiveBH(), key = bh.worldSeed + '/' + bh.skyDensity;
        if (key !== this.skyKey) {
            this.starfield = new WorldStarfield(bh.worldSeed, 80, bh.skyDensity);
            this.skyKey = key;
        }
        const c = m.camera.snapshot(), p = new Projector(c, f.width, f.height), previousCamera = m.flight.mode === 'manual' ? c : m.flight.sample(Math.max(0, m.motionMs - o.trailMs)), previous = new Projector(previousCamera, f.width, f.height), q = this.scratch, b = this.trailScratch;
        let visible = 0, candidates = 0;
        for (const tile of this.starfield.around(c, bh.skyRadius))
            for (const star of tile) {
                candidates++;
                const dx = star.x - c.x, dy = star.y - c.y, dz = star.z - c.z, d = Math.hypot(dx, dy, dz), alpha = distanceInk(d, star.luminosity, bh.skyRadius, bh.skyExposure);
                if (alpha < .008 || !p.write(star.x, star.y, star.z, q))
                    continue;
                if (this.halo && q[2] > this.halo.depth) {
                    const H = this.halo, x = q[0] - H.x, y = (q[1] - H.y) * 2, r = Math.hypot(x, y);
                    if (r < H.radius)
                        continue;
                    const lens = bh.lensStrength * H.radius * H.radius / (r * r + 1);
                    q[0] += x * lens * .3;
                    q[1] += y * lens * .15;
                }
                if (q[0] < 0 || q[1] < 0 || q[0] >= f.width || q[1] >= f.height)
                    continue;
                const color = this.ink(star.hue);
                if (o.trailMs > 0 && previous.write(star.x, star.y, star.z, b) && Math.hypot(q[0] - b[0], (q[1] - b[1]) * 2) < 30)
                    drawSegment(f, q[0], q[1], b[0], b[1], color, alpha * .5);
                putCell(f, q[0], q[1], d < 18 ? 0x22c6 : d < 55 ? 0x2219 : 0x00b7, color, alpha);
                visible++;
            }
        this.timing.candidateStars = candidates;
        this.timing.visibleStars = visible;
        this.timing.cacheTiles = this.starfield.cachedTiles;
        this.timing.starsMs = stamp() - t0;
        return visible;
    }
    ripple(f, m, event, p) {
        const age = (m.motionMs - event.atMs) / 1000, life = event.lifeMs / 1000;
        if (age < 0 || age >= life)
            return;
        const center = p.project(event.position);
        if (!center)
            return;
        const bh = m.effectiveBH(), rs = event.ripple ?? { speed: bh.rippleSpeed, width: bh.rippleWidth, rings: bh.rippleRings, gain: bh.rippleGain, intensity: m.options.weatherIntensity }, radius = age * rs.speed * event.scale, fade = softStep(age / .12) * softStep((life - age) / Math.max(.5, life * .4)), factor = p.focal / center.z, rad = radius * factor;
        const x0 = Math.max(0, Math.floor(center.x - rad - factor * 5)), x1 = Math.min(f.width - 1, Math.ceil(center.x + rad + factor * 5)), y0 = Math.max(0, Math.floor(center.y - rad / 2 - factor * 3)), y1 = Math.min(f.height - 1, Math.ceil(center.y + rad / 2 + factor * 3));
        const ringColors = Array.from({ length: rs.rings }, (_, i) => this.ink(i * 65 + age * 45 + event.seed % 360));
        const value = (x, y) => { const distance = Math.hypot((x - center.x) / factor, (y - center.y) * 2 / factor); let amplitude = 0, phase = 0; for (let ring = 0; ring < rs.rings; ring++) {
            const r = radius - ring * 2.8 * event.scale;
            if (r < 0)
                continue;
            const a = Math.exp(-Math.pow((distance - r) / rs.width, 2)) * (.9 ** ring);
            if (a > amplitude) {
                amplitude = a;
                phase = ring;
            }
        } return [amplitude * fade * rs.gain * rs.intensity, ringColors[phase]]; };
        for (let y = y0; y <= y1; y++)
            for (let x = x0; x <= x1; x++) {
                const k = (y * f.width + x) * 4, [a, col] = value(x + .5, y + .25), [b, col2] = value(x + .5, y + .75);
                if (Math.max(a, b) < .008)
                    continue;
                const bg = flattened(f, k);
                if (f.cells[k] === 32 || f.cells[k] === 0x2580) {
                    f.cells[k] = 0x2580;
                    f.cells[k + 1] = mixColor(bg, col, a);
                    f.cells[k + 2] = mixColor(bg, col2, b);
                }
                else
                    f.cells[k + 2] = mixColor(bg, col, (a + b) * .5);
            }
    }
    classicWeather(f, m, o) { return super.weather(f, m, o); }
    weather(f, model, o) {
        if (!(model instanceof BlackHoleModel))
            return super.weather(f, model, o);
        const m = model, t0 = stamp();
        if (o.weatherIntensity <= 0) {
            this.timing.weatherMs = stamp() - t0;
            return 0;
        }
        if (m.weatherSpace === 'screen') {
            const n = super.weather(f, m, { ...o, novaRegularity: m.autoNovas ? o.novaRegularity : 0 });
            this.timing.eventCount = n;
            this.timing.weatherMs = stamp() - t0;
            return n;
        }
        const events = m.worldEvents.filter(e => e.atMs <= m.motionMs && m.motionMs - e.atMs < e.lifeMs), p = new Projector(m.camera.snapshot(), f.width, f.height), q = this.scratch, b = this.trailScratch, count = Math.min(m.bh.particleCount, Math.floor(2400 / Math.max(1, events.length)));
        let points = 0, ripples = 0;
        for (const event of events) {
            if (event.kind === 'ripples') {
                if (ripples++ < 4)
                    this.ripple(f, m, event, p);
                continue;
            }
            const cloud = sampleWorldEvent(event, m.motionMs, count, m.particles.gravity);
            points += cloud.length;
            for (const point of cloud) {
                if (point.opacity < .006 || !p.write(point.x, point.y, point.z, q))
                    continue;
                const alpha = point.opacity * o.weatherIntensity * (event.kind === 'nova' ? o.novaStrength : 1), color = this.ink(point.hue);
                if (point.previous && p.write(point.previous.x, point.previous.y, point.previous.z, b))
                    drawSegment(f, q[0], q[1], b[0], b[1], color, alpha);
                if (event.kind === 'nova')
                    putDot(f, q[0] * 2, q[1] * 4, color, alpha);
                else
                    putCell(f, q[0], q[1], point.glyph, color, alpha);
            }
            if (event.kind === 'nova') {
                const age = m.motionMs - event.atMs, alpha = Math.max(0, 1 - age / 550) * o.novaStrength * o.weatherIntensity;
                if (alpha > 0 && p.write(event.position.x, event.position.y, event.position.z, q))
                    putCell(f, q[0], q[1], age < 120 ? 0x2219 : age < 280 ? 0x2736 : 0x22c6, 0xf7eadf, alpha);
            }
        }
        this.timing.eventCount = events.length;
        this.timing.particlePoints = points;
        this.timing.weatherMs = stamp() - t0;
        return events.length;
    }
    renderSurface(model) { const o = model.effective(), f = this.background(model, o); this.sky(f, model, o); this.weather(f, model, o); return f; }
    render(model, atMs = model.dataMs) {
        if (!(model instanceof BlackHoleModel))
            return super.render(model, atMs);
        const m = model, t0 = stamp();
        this.timing = freshTiming();
        let view;
        if (BLACK_HOLE_CUSTOM_SCENES.includes(m.scene))
            view = this.custom(m);
        else if (m.scene === 'fleet-room') {
            const proxy = Object.create(m);
            proxy.scene = 'windows';
            view = super.render(proxy, atMs);
            this.promptBands(view.frame, m);
        }
        else
            view = super.render(m, atMs);
        const f = view.frame, w = f.width, h = f.height, nodes = [{ kind: 'text', x: 2, y: 1, width: w - 4, height: 1, text: `NOCTURNE / BLACK HOLE     v0.7.0     ${m.scene.toUpperCase()}     CPU CELLS · OKLCh`, fg: rgb(m.palette.ink), bg: rgb(m.palette.background), bgOpacity: 1000, fgOpacity: 1000 }];
        // Authoritative draft always has its own opaque, final plane.
        if (!m.managedPrompt) nodes.push({ kind: 'text', x: 2, y: h - 4, width: w - 4, height: 1, text: '› ' + m.draft, fg: rgb(m.palette.ink), bg: rgb(m.palette.background), bgOpacity: 1000, fgOpacity: 1000 });
        view.frame = this.engine.paint(f, m.motionMs, nodes);
        view.nodes.push(...nodes);
        this.modal(view, m);
        this.timing.totalMs = stamp() - t0;
        this.timing.compositionMs = Math.max(0, this.timing.totalMs - this.timing.backgroundMs - this.timing.starsMs - this.timing.weatherMs);
        return view;
    }
    promptBands(f, m) { const y0 = f.height - 4, bh = m.effectiveBH(), time = m.motionMs / 1000; for (let y = Math.max(5, y0 - 9); y <= y0; y++) {
        const d = Math.abs(y - y0), rate = Math.pow(bh.promptSpeedFalloff, d), gain = .55 * Math.pow(bh.promptColorFalloff, d);
        for (let x = 0; x < f.width; x++) {
            const k = (y * f.width + x) * 4, c = this.base.colorAt(x / f.width + time * rate * .5);
            f.cells[k + 2] = mixColor(flattened(f, k), c, gain);
        }
    } }
    custom(m) {
        const o = m.effective(), f = this.background(m, o), drawnStars = this.sky(f, m, o), activeWeather = this.weather(f, m, o), nodes = [], semantics = [], actions = {}, w = f.width, h = f.height;
        const text = (x, y, s, fg = rgb(m.palette.ink), opacity = 1000) => nodes.push({ kind: 'text', x: Math.round(x), y: Math.round(y), width: Math.max(1, w - Math.round(x) - 2), height: 1, text: s, fg, fgOpacity: opacity });
        const button = (id, x, y, width, label, kind, value, extra) => { nodes.push({ kind: 'button', id, x: Math.round(x), y: Math.round(y), width: Math.max(1, Math.round(width)), height: 3, text: label, fg: this.ink(180), bg: 0x12202b, bgOpacity: 850, fgOpacity: 1000 }); semantics.push({ id, label }); actions[id] = { kind, value, extra }; };
        const title = BLACK_HOLE_SCENES.find(s => s.id === m.scene)?.name ?? m.scene;
        text(3, 4, title, this.ink(190));
        if (m.scene === 'black-hole') {
            text(3, 6, 'LENSED STARLIGHT / CLUMPED ACCRETION / AN ART-DIRECTED HORIZON', this.ink(45), 650);
            text(3, h - 9, `LENS ${m.bh.lensStrength.toFixed(2)}    DISC ${m.bh.discTilt}°    ${drawnStars} visible stars`, this.ink(45));
            text(3, h - 7, 'Orbit, fly, or cross the field. This is a visual model, not general relativity.', this.ink(250), 800);
        }
        else if (['graph-explorer', 'git-history'].includes(m.scene)) {
            this.graph(f, m, nodes, semantics, actions);
        }
        else if (m.scene === 'world-weather') {
            ['ripples', 'nova', 'firework', 'sparks', 'embers', 'rain', 'snow', 'leaves'].forEach((kind, i) => { const xx = 3 + (i % 4) * Math.floor((w - 6) / 4), yy = h - 14 + Math.floor(i / 4) * 4; button(44000 + i, xx, yy, Math.floor((w - 9) / 4), kind.toUpperCase(), 'world-burst', kind); });
            text(3, 7, 'Click space to plant an event. Move the camera: its world position stays fixed.', this.ink(240), 850);
        }
        else if (m.scene === 'dashboard') {
            const v = Math.round(m.effectiveBH().segmentValue), str = String(v).padStart(3, '0'), sw = Math.min(16, (w - 18) / 4), x0 = (w - str.length * (sw + 4)) / 2;
            [...str].forEach((ch, i) => segmentedGlyph(f, ch, x0 + i * (sw + 4), 10, sw, Math.min(12, h - 24), 16, j => this.ink(j * 24 + m.motionMs * .02), .4 + .6 * v / 100));
            text(5, h - 12, 'AUTHORITATIVE VALUE / ' + v + ' %', this.ink(190));
            nodes.push({ kind: 'progress', id: 45100, x: 5, y: h - 10, width: w - 10, height: 2, value: v * 10, fg: this.ink(m.motionMs * .025), bg: 0x1a202a, bgOpacity: 1000, fgOpacity: Math.round(350 + v * 6.5) });
            semantics.push({ id: 45100, label: 'Advance gauge by ten percent' });
            actions[45100] = { kind: 'gauge', value: 'next' };
        }
        else if (m.scene === 'forms') {
            text(4, 7, 'AVAILABLE → SELECTED / SAFE NUMERIC FORMULAS / SIMPLE OR DECORATED', this.ink(240), 750);
            m.form.list().forEach((s, i) => { const y = 10 + i * 3; if (y > h - 10)
                return; const value = Array.isArray(s.value) ? s.value.join(' + ') : typeof s.value === 'boolean' ? (s.value ? '☑' : '☐') : String(s.value); text(5, y, s.label, this.ink(190)); button(45000 + i, Math.floor(w * .35), y - 1, Math.floor(w * .61), value, 'form', s.id); });
            text(4, h - 7, 'Click a field; the companion controls provide full text and multi-select editing.', this.ink(250), 800);
        }
        else if (m.scene === 'code-review') {
            const lines = ['diff --git a/flight.ts b/flight.ts', '@@ immediate input remains independent @@', '- position += velocity / fps;', '+ position = flight.sample(explicitTimeMs);', '  const camera = projector.prepare(view);', '  // Retain every data event; coalesce only presentation.', '  const visible = stars.filter(distanceEnvelope);', '  if (source.stale) showStaleIndicator();', '  return compose(cells, selectedNode, liveDraft);'];
            lines.forEach((line, i) => { text(4, 9 + i, String(i + 1).padStart(3) + ' │', this.ink(250), 550); text(11, 9 + i, line, line.startsWith('+') ? this.ink(150) : line.startsWith('-') ? this.ink(30) : line.includes('//') ? this.ink(250) : this.ink(190)); });
            text(4, 23, 'HEX / BYTE CLASSES', this.ink(45));
            for (let row = 0; row < Math.min(7, h - 30); row++) {
                text(4, 25 + row, (row * 16).toString(16).padStart(8, '0'), this.ink(250), 600);
                for (let i = 0; i < 16; i++) {
                    const v = (row * 39 + i * 17) % 256;
                    rawText(f, 16 + i * 3, 25 + row, v.toString(16).padStart(2, '0'), this.ink(v === 0 ? 0 : v < 32 ? 45 : v < 127 ? 185 : 290));
                }
            }
        }
        else if (m.scene === 'impossible') {
            this.tesseract(f, m);
            text(3, h - 8, 'FOUR-DIMENSIONAL ROTATION PROJECTED INTO THREE, THEN TERMINAL CELLS', this.ink(250), 800);
        }
        else if (m.scene === 'waterfall')
            text(3, h - 8, m.bh.waterFlow === 0 ? 'FLOW GATE CLOSED / no falling water' : 'FLOW ' + m.bh.waterFlow.toFixed(2) + ' / route a sensor to waterFlow', this.ink(185));
        else if (m.scene === 'tarmac')
            text(3, h - 8, `${m.bh.landscapeSpeed.toFixed(0)} MPH / perspective lane markings`, this.ink(55));
        else if (m.scene === 'infinite')
            text(3, h - 8, 'INFINITE TRANSIT / rotary color corridors, not film footage', this.ink(m.motionMs * .04));
        text(3, h - 2, m.notice, this.ink(250), 850);
        return { frame: this.engine.paint(f, m.motionMs, nodes), nodes, semantics, actions, drawnStars, activeWeather };
    }
    graph(f, m, nodes, semantics, actions) {
        const p = new Projector(m.camera.snapshot(), f.width, f.height), nhood = m.graphFocus ? m.richGraph.neighborhood(m.graphFocus) : null, related = new Set(nhood?.related ?? []), u = softStep((m.motionMs - m.graphFocusAt) / 650), positions = new Map();
        const arrange = (id, base) => {
            if (!nhood)
                return base;
            let target = base;
            const index = (list) => list.indexOf(id), parent = index(nhood.parents), child = index(nhood.children), sibling = index(nhood.siblings);
            if (id === m.graphFocus)
                target = { x: 0, y: 0, z: -6 };
            else if (parent >= 0)
                target = { x: (parent - (nhood.parents.length - 1) / 2) * 22, y: 18, z: 0 };
            else if (child >= 0)
                target = { x: (child - (nhood.children.length - 1) / 2) * 22, y: -18, z: 0 };
            else if (sibling >= 0)
                target = { x: 30, y: (sibling - (nhood.siblings.length - 1) / 2) * 13, z: 8 };
            return { x: base.x + (target.x - base.x) * u, y: base.y + (target.y - base.y) * u, z: base.z + (target.z - base.z) * u };
        };
        for (const n of m.layout.nodes)
            positions.set(n.id, arrange(n.id, n));
        for (const edge of m.richGraph.edges) {
            const aa = positions.get(edge.source), bb = positions.get(edge.target);
            if (!aa || !bb)
                continue;
            const a = p.project(aa), b = p.project(bb);
            if (!a || !b)
                continue;
            const focused = !nhood || edge.source === m.graphFocus || edge.target === m.graphFocus, alpha = focused ? .55 : .13;
            drawSegment(f, a.x, a.y, b.x, b.y, this.ink(edge.kind === 'approved' ? 140 : 260), alpha);
            const phase = fract(m.motionMs / 2600 + edge.source.length * .21);
            putDot(f, (a.x + (b.x - a.x) * phase) * 2, (a.y + (b.y - a.y) * phase) * 4, this.ink(175), alpha * 1.6);
        }
        const order = m.layout.nodes.map((n, i) => ({ n, i, p: p.project(positions.get(n.id)) })).filter(v => v.p).sort((a, b) => b.p.z - a.p.z);
        for (const { n, i, p: projected } of order) {
            const a = projected, scale = clamp(65 / a.z, .45, 1.5) * m.bh.nodeScale, width = Math.round(clamp((n.label.length + 5) * scale, 7, 27)), height = scale > .9 ? 3 : 1, x = Math.round(a.x - width / 2), y = Math.round(a.y - height / 2);
            if (x >= f.width || x + width <= 0 || y < 7 || y + height >= f.height - 7)
                continue;
            const alpha = clamp(1 / (1 + a.z * m.bh.nodeDepthFade), .2, 1) * (nhood && !related.has(n.id) ? .3 : 1), fg = this.ink(m.richGraph.color(n.id, m.graphColorField, m.graphColorField === 'date' ? Date.parse('2026-09-01') : 0, m.graphColorField === 'date' ? Date.parse('2026-10-01') : 100)), id = 41000 + i;
            nodes.push({ kind: height === 3 ? 'button' : 'item', id, x, y, width, height, text: (n.id === m.graphFocus ? '◆ ' : '◇ ') + n.label, fg, bg: 0x131d28, bgOpacity: Math.round(850 * alpha), fgOpacity: Math.round(1000 * alpha), state: n.id === m.graphFocus ? 2 : 0 });
            semantics.push({ id, label: n.label });
            actions[id] = { kind: 'rich-node', value: n.id };
        }
        nodes.push({ kind: 'text', x: 3, y: 6, width: f.width - 6, height: 1, text: `${m.layoutOptions.mode} · ${m.richGraph.nodes.length} identities · ${m.richGraph.edges.length} typed edges · color: ${m.graphColorField}`, fg: this.ink(250), fgOpacity: 850 });
    }
    tesseract(f, m) {
        const t = m.motionMs / 1000 * .17, p = new Projector({ ...m.camera.snapshot(), z: m.camera.snapshot().z - 48 }, f.width, f.height), pts = [];
        for (let i = 0; i < 16; i++) {
            let x = i & 1 ? 1 : -1, y = i & 2 ? 1 : -1, z = i & 4 ? 1 : -1, q = i & 8 ? 1 : -1;
            const xx = x * Math.cos(t) - q * Math.sin(t), qq = x * Math.sin(t) + q * Math.cos(t), yy = y * Math.cos(t * .73) - z * Math.sin(t * .73), zz = y * Math.sin(t * .73) + z * Math.cos(t * .73), k = 17 / (2.8 - qq);
            pts.push({ x: xx * k, y: yy * k, z: zz * k });
        }
        for (let i = 0; i < 16; i++)
            for (let bit = 0; bit < 4; bit++) {
                const j = i ^ (1 << bit);
                if (j < i)
                    continue;
                const a = p.project(pts[i]), b = p.project(pts[j]);
                if (a && b)
                    drawSegment(f, a.x, a.y, b.x, b.y, this.ink(bit * 85 + t * 100), .85);
            }
    }
    modal(view, m) {
        const entry = m.modalStack.peek();
        if (!entry)
            return;
        const w = view.frame.width, h = view.frame.height, isDrawer = entry.kind.startsWith('drawer'), width = entry.kind === 'fullscreen' ? w - 4 : isDrawer ? Math.min(62, Math.floor(w * .55)) : Math.min(76, w - 8), height = entry.kind === 'toast' ? 6 : entry.kind === 'dropdown' ? 12 : Math.min(28, h - 8);
        let x = Math.floor((w - width) / 2), y = Math.floor((h - height) / 2);
        if (entry.kind === 'drawer-right')
            x = w - width - 2;
        if (entry.kind === 'drawer-left')
            x = 2;
        if (entry.kind === 'drawer-top')
            y = 4;
        if (entry.kind === 'drawer-bottom')
            y = h - height - 5;
        if (entry.kind === 'corner') {
            x = w - width - 2;
            y = h - height - 5;
        }
        const progress = m.options.motion ? softStep((m.motionMs - entry.atMs) / 280) : 1;
        if (entry.kind === 'drawer-right')
            x += Math.round((1 - progress) * (width - 5));
        if (entry.kind === 'drawer-left')
            x -= Math.round((1 - progress) * (width - 5));
        if (entry.kind === 'drawer-top')
            y -= Math.round((1 - progress) * (height - 3));
        if (entry.kind === 'drawer-bottom')
            y += Math.round((1 - progress) * (height - 3));
        const ns = [{ kind: 'box', id: 49999, x, y, width, height, fg: this.ink(250), bg: 0x101721, bgOpacity: Math.round(m.bh.modalOpacity * 1000), fgOpacity: 1000, text: ' ' + entry.title + ' ', style: 0 }], sem = [], actions = {};
        const row = (id, yy, label, kind, value, extra) => { ns.push({ kind: 'item', id, x: x + 2, y: yy, width: width - 4, height: 1, text: label, fg: this.ink(180), bg: 0x223845, bgOpacity: 900, fgOpacity: 1000, state: sem.length === m.modalSelected ? 2 : 0 }); sem.push({ id, label }); actions[id] = { kind, value, extra }; };
        if (m.modalContext === 'node') {
            const n = m.richGraph.node(m.modalNode), hood = m.richGraph.neighborhood(n.id);
            let yy = y + 2;
            for (const [k, v] of Object.entries(n.metadata ?? {}).slice(0, 6)) {
                ns.push({ kind: 'text', x: x + 2, y: yy++, width: width - 4, height: 1, text: k + ': ' + v, fg: this.ink(250), fgOpacity: 900 });
            }
            yy++;
            for (const [group, ids] of Object.entries({ Parents: hood.parents, Children: hood.children, Siblings: hood.siblings })) {
                if (yy >= y + height - 4)
                    break;
                ns.push({ kind: 'text', x: x + 2, y: yy++, width: width - 4, height: 1, text: group.toUpperCase(), fg: this.ink(50), fgOpacity: 850 });
                for (const id of ids) {
                    if (yy >= y + height - 3)
                        break;
                    row(47000 + sem.length, yy++, '↳ ' + (m.richGraph.node(id).label ?? id), 'rich-node', id);
                }
            }
        }
        else if (m.modalContext === 'windows') {
            m.spaceWindows.list().filter(w => `${w.id} ${w.title}`.toLowerCase().includes(m.modalQuery.toLowerCase())).slice(0, height - 5).forEach((win, i) => row(47100 + i, y + 3 + i, `${win.state.padEnd(10)} ${win.title}`, 'focus-window', win.id, m.windowMode));
        }
        else if (m.modalContext === 'commands') {
            m.keymap.search(m.modalQuery).slice(0, height - 5).forEach((b, i) => row(47200 + i, y + 3 + i, `${b.chord.padEnd(17)} ${b.label ?? b.id}`, 'shortcut', b.id));
        }
        else {
            ns.push({ kind: 'text', x: x + 3, y: y + 3, width: width - 6, height: 4, text: entry.kind === 'confirmation' ? 'This specimen does not authorize an external action. Confirm applies only to the local demonstration.' : entry.body, fg: rgb(m.palette.ink), fgOpacity: 1000 });
            if (entry.kind === 'confirmation')
                row(47800, y + height - 4, '✓ Confirm local demonstration', 'confirm', 'local');
        }
        row(47999, y + height - 2, '× Close / Escape', 'dismiss', '');
        view.frame = this.engine.paint(view.frame, m.motionMs, ns);
        view.nodes.push(...ns);
        view.semantics = sem;
        view.actions = actions;
    }
}
/** Resolve semantic actions without eval, provider calls or terminal ownership. */
export function activateBlackHole(m, id, view) {
    const a = view?.actions[id];
    if (!a) {
        if (m.modalStack.peek())
            return;
        activateKinetic(m, id, view);
        return;
    }
    if (a.kind === 'world-burst')
        m.emit(m.width * .5, m.height * .45, '·', a.value);
    else if (a.kind === 'rich-node')
        m.selectGraph(a.value);
    else if (a.kind === 'focus-window')
        m.focusWindow(a.value, a.extra ?? m.windowMode);
    else if (a.kind === 'dismiss')
        (m.dismissModal ? m.dismissModal() : m.modalStack.dismiss());
    else if (a.kind === 'shortcut')
        runBlackHoleAction(m, a.value);
    else if (a.kind === 'gauge')
        m.configureBH({ segmentValue: m.bh.segmentValue >= 90 ? 0 : m.bh.segmentValue + 10 });
    else if (a.kind === 'form') {
        const s = m.form.list().find(f => f.id === a.value);
        if (s.kind === 'checkbox')
            m.form.set(s.id, !s.value);
        else if (['radio', 'select'].includes(s.kind)) {
            const list = s.choices;
            m.form.set(s.id, list[(list.indexOf(String(s.value)) + 1) % list.length]);
        }
        m.notice = 'Selected field ' + s.label + ' / edit in companion form';
    }
    else if (a.kind === 'confirm') {
        (m.dismissModal ? m.dismissModal() : m.modalStack.dismiss());
        m.notice = 'Confirmed local demonstration only.';
    }
    else
        activateKinetic(m, id, view);
    m.revision++;
}
export function runBlackHoleAction(m, id) {
    if (id === 'help' || id === 'commands')
        m.openModal('center', 'commands');
    else if (id === 'windows')
        m.openModal('center', 'windows');
    else if (id === 'escape') {
        if (!(m.dismissModal ? m.dismissModal() : m.modalStack.dismiss()))
            m.openModal('center', 'commands');
    }
    else if (id === 'hold')
        m.configure({ motion: !m.options.motion });
    else if (id === 'brake')
        m.pilot('stop');
    else if (id === 'gather')
        m.gatherWindows();
    else if (id === 'summon' || id === 'visit')
        m.focusWindow(m.spaceWindows.selected, id);
    else if (id === 'new-window')
        m.newWindow();
    else if (id === 'new-tab') {
        const wins = m.spaceWindows.list(), i = wins.findIndex(w => w.id === m.spaceWindows.selected);
        m.spaceWindows.select(wins[(i + 1) % wins.length].id);
    }
    m.revision++;
}

