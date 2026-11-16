import {clamp,finite,hash32} from './observatory.js';
import {cameraBasis} from './kinetic-camera.js';
/** World-space sampling. No clock, devices, terminal writes, or frame-count state.
 * Cache eviction only affects cost, never positions or canonical cell output. */
export const SKY_LIMITS = { cacheTiles: 2400, maxSamples: 26000, maxEvents: 16, maxEventPoints: 1200 };
export function seededUnit(seed, index) { return hash32(seed ^ Math.imul(index + 1, 0x9e3779b1)) / 4294967296; }
export function softStep(x) { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); }
/** Art-directed inverse-square exposure plus a C1 far shell. Units are arbitrary
 * world units; output is linear blend strength, not astronomical photometry.
 * Zero outside radius ensures newly loaded sectors are invisible at the boundary. */
export function distanceInk(distance, luminosity, farRadius, exposure) {
    if (distance >= farRadius)
        return 0;
    const fade = softStep((farRadius - distance) / (farRadius * .28));
    return (1 - Math.exp(-luminosity * exposure / (16 + Math.max(0, distance) ** 2))) * fade;
}
/** Precompute the view basis and focal lengths ONCE per frame. project() returns
 * cell coordinates or null behind clipping planes. write() avoids point allocation.
 * Example: new Projector(camera,136,44).project({x:0,y:0,z:20}). */
export class Projector {
    constructor(camera, width, height, aspect = 2) {
        this.camera = camera;
        this.width = width;
        this.height = height;
        this.basis = cameraBasis(camera);
        this.focal = width / (2 * Math.tan(camera.fov * Math.PI / 360));
        this.vertical = this.focal / aspect;
    }
    write(x, y, z, out) {
        x -= this.camera.x;
        y -= this.camera.y;
        z -= this.camera.z;
        const b = this.basis;
        const depth = x * b.forward.x + y * b.forward.y + z * b.forward.z;
        if (!Number.isFinite(depth) || depth < this.camera.near || depth > this.camera.far)
            return false;
        out[0] = this.width / 2 + (x * b.right.x + y * b.right.y + z * b.right.z) * this.focal / depth;
        out[1] = this.height / 2 - (x * b.up.x + y * b.up.y + z * b.up.z) * this.vertical / depth;
        out[2] = depth;
        return true;
    }
    project(p) { const out = new Float64Array(3); return this.write(p.x, p.y, p.z, out) ? { x: out[0], y: out[1], z: out[2] } : null; }
    /** Point at a specified view-space depth; weather uses it to anchor a click. */
    unproject(x, y, depth) {
        finite(depth, .01, 100000, 'depth');
        const b = this.basis, rx = (x - this.width / 2) / this.focal, uy = (this.height / 2 - y) / this.vertical, c = this.camera;
        return { x: c.x + depth * (b.forward.x + b.right.x * rx + b.up.x * uy), y: c.y + depth * (b.forward.y + b.right.y * rx + b.up.y * uy), z: c.z + depth * (b.forward.z + b.right.z * rx + b.up.z * uy) };
    }
}
/** Deterministic infinite tiling with stable world-sector identities. Sector size
 * is fixed; resizing the viewport never regenerates the sky. Cache size is bounded.
 * around() selects every sector that could intersect the radial visibility shell. */
export class WorldStarfield {
    constructor(seed = 2030, sectorSize = 80, starsPerSector = 6) {
        this.seed = seed;
        this.sectorSize = sectorSize;
        this.starsPerSector = starsPerSector;
        this.cache = new Map();
        finite(seed, 0, 4294967295, 'seed');
        finite(sectorSize, 16, 256, 'sectorSize');
        finite(starsPerSector, 1, 24, 'starsPerSector');
        if (!Number.isInteger(seed) || !Number.isInteger(starsPerSector))
            throw new RangeError('Integer seed/count required');
    }
    tile(x, y, z) {
        for (const v of [x, y, z])
            if (!Number.isInteger(v) || Math.abs(v) > 1000000)
                throw new RangeError('Sector index bound');
        const key = `${x}/${y}/${z}`;
        const old = this.cache.get(key);
        if (old)
            return old;
        const seed = hash32(this.seed ^ Math.imul(x, 73856093) ^ Math.imul(y, 19349663) ^ Math.imul(z, 83492791)), s = this.sectorSize;
        const stars = Object.freeze(Array.from({ length: this.starsPerSector }, (_, i) => Object.freeze({ id: `${key}/${i}`, x: (x + seededUnit(seed, i * 5)) * s, y: (y + seededUnit(seed, i * 5 + 1)) * s, z: (z + seededUnit(seed, i * 5 + 2)) * s, luminosity: .35 + seededUnit(seed, i * 5 + 3) ** 4 * 24, hue: seededUnit(seed, i * 5 + 4) * 360 })));
        if (this.cache.size >= SKY_LIMITS.cacheTiles)
            this.cache.delete(this.cache.keys().next().value);
        this.cache.set(key, stars);
        return stars;
    }
    around(c, radius) {
        finite(radius, 40, 400, 'radius');
        for (const k of ['x', 'y', 'z'])
            finite(c?.[k], -100000, 100000, 'camera.' + k);
        if (Math.pow(2 * radius / this.sectorSize + 3, 3) * this.starsPerSector > 50000)
            throw new RangeError('Sector/radius configuration exceeds candidate budget');
        const s = this.sectorSize, r2 = radius * radius, out = [];
        for (let z = Math.floor((c.z - radius) / s); z <= Math.floor((c.z + radius) / s); z++)
            for (let y = Math.floor((c.y - radius) / s); y <= Math.floor((c.y + radius) / s); y++)
                for (let x = Math.floor((c.x - radius) / s); x <= Math.floor((c.x + radius) / s); x++) {
                    const dx = Math.max(x * s - c.x, 0, c.x - (x + 1) * s), dy = Math.max(y * s - c.y, 0, c.y - (y + 1) * s), dz = Math.max(z * s - c.z, 0, c.z - (z + 1) * s);
                    if (dx * dx + dy * dy + dz * dz <= r2)
                        out.push(this.tile(x, y, z));
                }
        return out;
    }
    get cachedTiles() { return this.cache.size; }
}
export const WORLD_WEATHER = ['ripples', 'nova', 'firework', 'sparks', 'embers', 'rain', 'snow', 'leaves'];
/** Sample fixed world coordinates for an event, never camera-relative particle
 * positions. Nova is a clumpy Fibonacci shell; firework retains ballistic ejecta.
 * Counts/lifetime are bounded by the host before calling this function. */
export function sampleWorldEvent(event, timeMs, count, gravity = 2.6) {
    const age = (timeMs - event.atMs) / 1000, life = event.lifeMs / 1000;
    if (age < 0 || age >= life)
        return [];
    count = Math.floor(clamp(count, 1, SKY_LIMITS.maxEventPoints));
    const u = age / life, fade = softStep((1 - u) * 2), rise = softStep(age / .12), s = event.scale, p = event.position, out = [];
    for (let i = 0; i < count; i++) {
        const a = seededUnit(event.seed, i * 4), b = seededUnit(event.seed, i * 4 + 1), r = seededUnit(event.seed, i * 4 + 2), flicker = .7 + .3 * Math.sin(age * (9 + 12 * a) + b * 60) ** 2;
        let x = 0, y = 0, z = 0, alpha = fade * rise, hue = 20 + 60 * a, glyph = 0x2219, previous;
        if (event.kind === 'nova') {
            const latitude = 1 - 2 * (i + .5) / count, ring = Math.sqrt(Math.max(0, 1 - latitude * latitude)), angle = i * 2.399963229728653 + event.seed * .0001;
            const radius = s * (1 + age * 4.2) * (1 + .13 * Math.sin(angle * 3 + latitude * 8 + event.seed)), clump = .3 + .7 * Math.sin(angle * 2 + latitude * 9 + event.seed) ** 2;
            x = Math.cos(angle) * ring * radius;
            y = latitude * radius;
            z = Math.sin(angle) * ring * radius;
            alpha *= clump;
            hue = 25 + 260 * u + 60 * a;
            glyph = 0x00b7;
        }
        else if (event.kind === 'firework') {
            const theta = a * Math.PI * 2, lat = b * 2 - 1, rr = Math.sqrt(1 - lat * lat), speed = s * (4 + r * 12);
            const pos = (t) => ({ x: p.x + Math.cos(theta) * rr * speed * t, y: p.y + lat * speed * t - gravity * t * t * .5, z: p.z + Math.sin(theta) * rr * speed * t });
            const q = pos(age);
            x = q.x - p.x;
            y = q.y - p.y;
            z = q.z - p.z;
            previous = pos(Math.max(0, age - .045));
            hue = a * 360;
            alpha *= flicker;
        }
        else if (event.kind === 'embers' || event.kind === 'leaves') {
            const vx = (a - .5) * s * 4, vy = s * (3 + 5 * b), vz = (r - .5) * s * 4;
            const pos = (t) => ({ x: p.x + vx * t + Math.sin(t * 2 + b * 20) * s * .4, y: p.y + vy * t - gravity * t * t * .5, z: p.z + vz * t });
            const q = pos(age);
            x = q.x - p.x;
            y = q.y - p.y;
            z = q.z - p.z;
            previous = pos(Math.max(0, age - .06));
            alpha *= flicker;
            hue = event.kind === 'leaves' ? 35 + b * 95 : 15 + b * 60;
            glyph = event.kind === 'leaves' ? (Math.sin(age * 4 + a * 50) > 0 ? 0x2312 : 0x223c) : 0x2219;
        }
        else if (event.kind === 'sparks') {
            const branches = Math.max(3, Math.floor(count / 14)), branch = i % branches, seg = Math.floor(i / branches), t = seg / Math.ceil(count / branches), ang = seededUnit(event.seed, branch + 800) * Math.PI * 2;
            const point = (v) => ({ x: p.x + Math.cos(ang) * s * 18 * v + Math.sin(v * 45 + branch * 3 + Math.floor(age * 16)) * s * .5, y: p.y + Math.sin(ang) * s * 18 * v + Math.sin(v * 63 + branch * 5) * s * .6, z: p.z + Math.sin(branch * 7) * v * s * 7 });
            const q = point(t);
            x = q.x - p.x;
            y = q.y - p.y;
            z = q.z - p.z;
            previous = point(Math.max(0, t - .1));
            hue = 205 + b * 100;
            alpha *= Math.max(0, 1 - age / Math.min(life, .85)) * flicker;
            glyph = seg % 3 === 0 ? 0x22c6 : 0x00b7;
        }
        else {
            x = (a - .5) * 50 * s;
            y = (b - .5) * 30 * s - age * (event.kind === 'rain' ? 17 : 4);
            z = (r - .5) * 30 * s;
            alpha *= flicker;
            hue = event.kind === 'rain' ? 205 : 240;
            glyph = event.kind === 'rain' ? 0x2571 : 0x00b7;
            if (event.kind === 'snow')
                x += Math.sin(age * 1.6 + b * 22) * 3;
        }
        out.push({ x: p.x + x, y: p.y + y, z: p.z + z, opacity: alpha, hue, glyph, previous });
    }
    return out;
}

