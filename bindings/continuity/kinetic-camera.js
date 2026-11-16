import {clamp,finite,RateTimeline} from './observatory.js';
/** Explicit camera and travel math. No browser or terminal ownership. */
export const DEFAULT_CAMERA = { x: 0, y: 0, z: -40, yaw: 0, pitch: 0, roll: 0, fov: 70, near: .1, far: 100000, mode: 'orbit', moveSpeed: 12, turnSpeed: 75, sensitivity: .32 };
const radians = (v) => v * Math.PI / 180;
export const wrapAngle = (v) => ((v + 180) % 360 + 360) % 360 - 180;
const dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;
/** Right-handed basis with forward along +Z at zero angles, Y up. */
export function cameraBasis(c) {
    const y = radians(c.yaw), p = radians(c.pitch), r = radians(c.roll), cy = Math.cos(y), sy = Math.sin(y), cp = Math.cos(p), sp = Math.sin(p);
    const right = { x: cy, y: 0, z: -sy }, up = { x: -sy * sp, y: cp, z: -cy * sp };
    return { forward: { x: sy * cp, y: sp, z: cy * cp }, right: { x: right.x * Math.cos(r) + up.x * Math.sin(r), y: up.y * Math.sin(r), z: right.z * Math.cos(r) + up.z * Math.sin(r) }, up: { x: up.x * Math.cos(r) - right.x * Math.sin(r), y: up.y * Math.cos(r), z: up.z * Math.cos(r) - right.z * Math.sin(r) } };
}
/** Project to terminal cells with a configurable physical cell aspect. Returns
 * null behind clipping planes; the caller clips visible segments to its viewport.
 */
export function projectSpatial(p, c, width, height, cellAspect = 2) {
    const d = { x: p.x - c.x, y: p.y - c.y, z: p.z - c.z }, b = cameraBasis(c), z = dot(d, b.forward);
    if (!Number.isFinite(z) || z < c.near || z > c.far)
        return null;
    const f = width / (2 * Math.tan(radians(c.fov) / 2));
    return { x: width / 2 + dot(d, b.right) * f / z, y: height / 2 - dot(d, b.up) * f / (z * cellAspect), z };
}
/** Camera-space line clip includes the near plane, so a crossing edge is not
 * discarded just because one endpoint is behind the viewer. */
export function clipSpatialSegment(a, b, c) {
    const basis = cameraBasis(c), depth = (p) => dot({ x: p.x - c.x, y: p.y - c.y, z: p.z - c.z }, basis.forward), az = depth(a), bz = depth(b);
    let lo = 0, hi = 1;
    if (az < c.near && bz < c.near || az > c.far && bz > c.far)
        return null;
    const dz = bz - az;
    if (dz !== 0) {
        const near = (c.near - az) / dz, far = (c.far - az) / dz;
        if (dz > 0) {
            lo = Math.max(lo, near);
            hi = Math.min(hi, far);
        }
        else {
            lo = Math.max(lo, far);
            hi = Math.min(hi, near);
        }
    }
    if (lo > hi)
        return null;
    const lerp = (t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t });
    return [lerp(clamp(lo, 0, 1)), lerp(clamp(hi, 0, 1))];
}
/** A user-operated camera. Angles are degrees, translation is world units.
 * Configure is atomic; mode changes never move the camera. Fit/reset are explicit.
 * Example: rig.rotate(8,-3); rig.moveLocal(1,0,0); render(rig.snapshot()).
 */
export class CameraRig {
    constructor(options = {}) {
        this.state = { ...DEFAULT_CAMERA };
        this.target = { x: 0, y: 0, z: 0 };
        this.configure(options);
    }
    snapshot() { return { ...this.state }; }
    configure(patch) {
        const out = { ...this.state };
        for (const [k, v] of Object.entries(patch)) {
            if (k === 'mode') {
                if (!['orbit', 'fly', 'pan'].includes(v))
                    throw new RangeError('camera mode');
                out.mode = v;
                continue;
            }
            const ranges = { x: [-100000, 100000], y: [-100000, 100000], z: [-100000, 100000], yaw: [-36000, 36000], pitch: [-89, 89], roll: [-36000, 36000], fov: [15, 130], near: [.001, 100], far: [1, 1000000], moveSpeed: [.1, 1000], turnSpeed: [1, 360], sensitivity: [.01, 5] };
            if (!ranges[k])
                throw new RangeError('Unknown camera option ' + k);
            const n = finite(v, ...ranges[k], k);
            out[k] = n;
        }
        if (out.far <= out.near)
            throw new RangeError('Camera far plane must exceed near plane');
        out.yaw = wrapAngle(out.yaw);
        out.roll = wrapAngle(out.roll);
        this.state = out;
    }
    reset() { this.state = { ...DEFAULT_CAMERA }; this.target = { x: 0, y: 0, z: 0 }; }
    /** Translate in view-local right/up/forward axes. Both the camera and orbital
     * target translate, preserving view direction. No inertial drift is implicit. */
    moveLocal(right, up, forward) {
        [right, up, forward].forEach(v => finite(v, -100000, 100000, 'camera translation'));
        const b = cameraBasis(this.state), d = { x: b.right.x * right + b.up.x * up + b.forward.x * forward, y: b.right.y * right + b.up.y * up + b.forward.y * forward, z: b.right.z * right + b.up.z * up + b.forward.z * forward };
        const next = { x: clamp(this.state.x + d.x, -100000, 100000), y: clamp(this.state.y + d.y, -100000, 100000), z: clamp(this.state.z + d.z, -100000, 100000) };
        const actual = { x: next.x - this.state.x, y: next.y - this.state.y, z: next.z - this.state.z };
        this.configure(next);
        for (const a of ['x', 'y', 'z'])
            this.target[a] += actual[a];
    }
    /** Orbit around the explicit target, or rotate in place in fly/pan mode. */
    rotate(yawDegrees, pitchDegrees) {
        finite(yawDegrees, -36000, 36000, 'yaw delta');
        finite(pitchDegrees, -36000, 36000, 'pitch delta');
        const distance = Math.max(.2, Math.hypot(this.state.x - this.target.x, this.state.y - this.target.y, this.state.z - this.target.z));
        this.configure({ yaw: this.state.yaw + yawDegrees, pitch: clamp(this.state.pitch + pitchDegrees, -89, 89) });
        if (this.state.mode === 'orbit') {
            const f = cameraBasis(this.state).forward;
            this.configure({ x: this.target.x - f.x * distance, y: this.target.y - f.y * distance, z: this.target.z - f.z * distance });
        }
    }
    dolly(units) {
        finite(units, -100000, 100000, 'dolly');
        if (this.state.mode !== 'orbit') {
            this.moveLocal(0, 0, units);
            return;
        }
        const f = cameraBasis(this.state).forward, d = clamp(Math.hypot(this.state.x - this.target.x, this.state.y - this.target.y, this.state.z - this.target.z) - units, .25, 90000);
        this.configure({ x: this.target.x - f.x * d, y: this.target.y - f.y * d, z: this.target.z - f.z * d });
    }
    /** Six axis-aligned views. 'iso' provides a useful oblique scene overview. */
    view(name) {
        const views = { front: [0, 0], back: [180, 0], left: [-90, 0], right: [90, 0], top: [0, -89], bottom: [0, 89], iso: [-28, -18] };
        if (!views[name])
            throw new RangeError('Unknown camera view');
        const mode = this.state.mode;
        this.configure({ mode: 'orbit' });
        this.rotate(wrapAngle(views[name][0] - this.state.yaw), views[name][1] - this.state.pitch);
        this.configure({ mode });
    }
    /** Fit view-space extents, including terminal aspect and padding. All supplied
     * points remain reachable; empty input restores the origin view. */
    fit(points, width, height, padding = 1.24) {
        finite(width, 1, 10000, 'width');
        finite(height, 1, 10000, 'height');
        finite(padding, 1, 10, 'padding');
        if (!points.length) {
            this.reset();
            return;
        }
        for (const p of points)
            for (const a of ['x', 'y', 'z'])
                finite(p[a], -100000, 100000, 'point');
        const min = { x: Math.min(...points.map(p => p.x)), y: Math.min(...points.map(p => p.y)), z: Math.min(...points.map(p => p.z)) }, max = { x: Math.max(...points.map(p => p.x)), y: Math.max(...points.map(p => p.y)), z: Math.max(...points.map(p => p.z)) };
        this.target = { x: (min.x + max.x) / 2, y: (min.y + max.y) / 2, z: (min.z + max.z) / 2 };
        const horizontal = radians(this.state.fov) / 2, vertical = Math.atan(Math.tan(horizontal) * height * 2 / width), basis = cameraBasis(this.state);
        const distance = Math.max(8, ...points.map(p => { const d = { x: p.x - this.target.x, y: p.y - this.target.y, z: p.z - this.target.z }, z = dot(d, basis.forward); return Math.max(Math.abs(dot(d, basis.right)) * padding / Math.tan(horizontal) - z, Math.abs(dot(d, basis.up)) * padding / Math.tan(vertical) - z, 1 - z); }));
        this.configure({ x: this.target.x - basis.forward.x * distance, y: this.target.y - basis.forward.y * distance, z: this.target.z - basis.forward.z * distance });
    }
    /** Integrate held navigation commands over elapsed milliseconds, independent of
     * presentation rate. Hosts must release held keys on blur/pointer cancellation. */
    integrate(axes, elapsedMs) {
        finite(elapsedMs, 0, 10000, 'elapsedMs');
        const t = elapsedMs / 1000, boost = finite(axes.boost ?? 1, .1, 10, 'boost');
        for (const k of ['right', 'up', 'forward', 'yaw', 'pitch', 'roll'])
            finite(axes[k] ?? 0, -1, 1, k);
        const move = this.state.moveSpeed * t * boost, turn = this.state.turnSpeed * t;
        this.moveLocal((axes.right ?? 0) * move, (axes.up ?? 0) * move, (axes.forward ?? 0) * move);
        if (axes.yaw || axes.pitch)
            this.rotate((axes.yaw ?? 0) * turn, (axes.pitch ?? 0) * turn);
        if (axes.roll)
            this.configure({ roll: this.state.roll + axes.roll * turn });
    }
}
/** Changing the travel vector preserves already-travelled XYZ position. Each
 * component has the same explicit-time checkpoint bound as RateTimeline. */
/** Editable motion timeline. A control edit in retained history truncates its
 * future rate events, preserving the sampled position at the edit timestamp.
 * Data histories are not modified. Retains 256 checkpoints; earlier seeks reject.
 */
export class EditableRateTimeline extends RateTimeline {
    constructor(rate) { super(rate); this.history = [{ atMs: 0, position: 0, rate }]; }
    at(timeMs) { finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'timeMs'); let s = this.history[0]; if (timeMs < s.atMs)
        throw new RangeError('Time precedes retained motion checkpoint'); for (const v of this.history) {
        if (v.atMs > timeMs)
            break;
        s = v;
    } return s.position + (timeMs - s.atMs) * s.rate / 1000; }
    set(atMs, rate) { finite(rate, -10000, 10000, 'rate'); const position = this.at(atMs); this.history = this.history.filter(s => s.atMs < atMs); this.history.push({ atMs, position, rate }); if (this.history.length > 256)
        this.history.shift(); }
}
export class VectorTravel {
    constructor() {
        this.x = new EditableRateTimeline(0);
        this.y = new EditableRateTimeline(0);
        this.z = new EditableRateTimeline(0);
    }
    set(atMs, speed, yaw, pitch) { finite(speed, -1000, 1000, 'speed'); finite(yaw, -36000, 36000, 'yaw'); finite(pitch, -90, 90, 'pitch'); const y = radians(yaw), p = radians(pitch); this.x.set(atMs, speed * Math.sin(y) * Math.cos(p)); this.y.set(atMs, speed * Math.sin(p)); this.z.set(atMs, speed * Math.cos(y) * Math.cos(p)); }
    at(timeMs) { return { x: this.x.at(timeMs), y: this.y.at(timeMs), z: this.z.at(timeMs) }; }
}

