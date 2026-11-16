import {clamp,finite} from './observatory.js';
import {cameraBasis} from './kinetic-camera.js';
/** Frame-rate-independent flight choreography. Constant angular-rate manoeuvres
 * use analytic integrals, not step-by-frame Euler integration. Orbit modes are
 * art-directed trajectories, not a celestial mechanics simulation. */
const FLIGHT_RAD = Math.PI / 180;
const intSin = (a, k, t) => Math.abs(k) < 1e-10 ? Math.sin(a) * t : (Math.cos(a) - Math.cos(a + k * t)) / k;
const intCos = (a, k, t) => Math.abs(k) < 1e-10 ? Math.cos(a) * t : (Math.sin(a + k * t) - Math.sin(a)) / k;
/** Calculate a complete pose at elapsed seconds within a manoeuvre. */
export function maneuverPose(c, cmd, seconds) {
    const t = clamp(seconds, 0, cmd.seconds), u = t / cmd.seconds, d = cmd.degrees ?? 0;
    const y0 = c.yaw * FLIGHT_RAD, p0 = c.pitch * FLIGHT_RAD;
    const ky = (cmd.kind === 'turn' ? d : 0) * FLIGHT_RAD / cmd.seconds;
    const kp = (cmd.kind === 'climb' ? Math.abs(d) : cmd.kind === 'dive' ? -Math.abs(d) : 0) * FLIGHT_RAD / cmd.seconds;
    const dx = .5 * (intSin(y0 + p0, ky + kp, t) + intSin(y0 - p0, ky - kp, t)) * cmd.speed;
    const dz = .5 * (intCos(y0 + p0, ky + kp, t) + intCos(y0 - p0, ky - kp, t)) * cmd.speed;
    const dy = intSin(p0, kp, t) * cmd.speed;
    const bank = cmd.kind === 'turn' && cmd.coordinated !== false ? Math.sign(d) * (cmd.bank ?? 28) * Math.sin(Math.PI * u) : 0;
    return { ...c, x: c.x + dx, y: c.y + dy, z: c.z + dz, yaw: c.yaw + ky * t / FLIGHT_RAD, pitch: c.pitch + kp * t / FLIGHT_RAD, roll: c.roll + (cmd.kind === 'roll' ? d * u : bank) };
}
/** Explicit-time camera director. Plan validation is atomic. sample() is pure.
 * At the end of a script the pose holds; call cruise() to continue from there.
 * Example: flight.plan(now,camera,[{kind:'turn',seconds:45,degrees:-90,speed:8}]). */
export class FlightDirector {
    constructor(camera) {
        this.legs = [];
        this.cruiseData = null;
        this.orbitData = null;
        this.mode = 'manual';
        this.initial = { ...camera };
    }
    stop(timeMs) { const c = this.sample(timeMs); this.initial = c; this.legs = []; this.orbitData = null; this.cruiseData = null; this.mode = 'manual'; return { ...c }; }
    anchor(camera) { this.initial = { ...camera }; this.legs = []; this.orbitData = null; this.cruiseData = null; this.mode = 'manual'; }
    plan(atMs, camera, commands) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'time');
        if (!Array.isArray(commands) || commands.length < 1 || commands.length > 64)
            throw new RangeError('1..64 manoeuvres required');
        let c = { ...camera }, at = atMs;
        const legs = [];
        for (const raw of commands) {
            if (!raw || !['turn', 'climb', 'dive', 'cruise', 'roll'].includes(raw.kind))
                throw new RangeError('Unknown manoeuvre');
            const cmd = { ...raw };
            finite(cmd.seconds, .01, 600, 'seconds');
            finite(cmd.speed, -100, 100, 'speed');
            finite(cmd.degrees ?? 0, -720, 720, 'degrees');
            finite(cmd.bank ?? 28, 0, 70, 'bank');
            const end = maneuverPose(c, cmd, cmd.seconds);
            if (Math.abs(end.pitch) > 85)
                throw new RangeError('Pitch outside -85..85 degrees');
            legs.push({ start: c, atMs: at, command: cmd });
            c = end;
            at += cmd.seconds * 1000;
        }
        if (at - atMs > 3600000)
            throw new RangeError('Flight script limited to one hour');
        this.initial = { ...camera };
        this.legs = legs;
        this.orbitData = null;
        this.cruiseData = null;
        this.mode = 'script';
    }
    /** Continue travel without changing the viewing orientation. A supplied heading
     * is independent of camera yaw/pitch; omitted heading travels where we look. */
    cruise(atMs, camera, speed, heading) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'time');
        finite(speed, -100, 100, 'speed');
        if (heading) {
            finite(heading.yaw, -720, 720, 'heading');
            finite(heading.pitch, -89, 89, 'elevation');
        }
        const travel = heading ? {yaw:heading.yaw,pitch:heading.pitch} : {yaw:camera.yaw,pitch:camera.pitch};
        const direction = cameraBasis({ ...camera, ...travel }).forward;
        this.anchor(camera);
        this.cruiseData = { atMs, start: { ...camera }, speed, direction, heading: travel };
        this.mode = 'cruise';
    }
    travelHeading() { return this.cruiseData ? {...this.cruiseData.heading} : null; }
    orbit(atMs, camera, target, options) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'time');
        finite(options.periodSeconds, 2, 600, 'orbit period');
        finite(options.radialRate, 0, 30, 'radial rate');
        finite(options.bank, -70, 70, 'bank');
        if (!['stable', 'escape', 'falling'].includes(options.mode))
            throw new RangeError('orbit mode');
        for (const v of Object.values(target))
            finite(v, -100000, 100000, 'target');
        const d = { x: camera.x - target.x, y: camera.y - target.y, z: camera.z - target.z }, r = Math.hypot(d.x, d.y, d.z);
        if (r < .1)
            throw new RangeError('Orbit target must differ from camera');
        const radial = { x: d.x / r, y: d.y / r, z: d.z / r };
        let tangent = { x: -radial.z, y: 0, z: radial.x };
        let n = Math.hypot(tangent.x, tangent.z);
        if (n < .01) {
            tangent = { x: 1, y: 0, z: 0 };
            n = 1;
        }
        tangent = { x: tangent.x / n, y: 0, z: tangent.z / n };
        this.initial = { ...camera };
        this.legs = [];
        this.cruiseData = null;
        this.orbitData = { atMs, start: { ...camera }, target: { ...target }, options: { ...options }, r, radial, tangent };
        this.mode = 'orbit:' + options.mode;
    }
    sample(timeMs) {
        finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'time');
        const q = this.cruiseData;
        if (q) {
            const t = Math.max(0, (timeMs - q.atMs) / 1000), b = q.direction;
            return { ...q.start, x: q.start.x + b.x * q.speed * t, y: q.start.y + b.y * q.speed * t, z: q.start.z + b.z * q.speed * t };
        }
        const o = this.orbitData;
        if (o) {
            if (timeMs < o.atMs)
                return { ...o.start };
            const t = (timeMs - o.atMs) / 1000, a = t * 2 * Math.PI / o.options.periodSeconds, r = o.options.mode === 'stable' ? o.r : o.options.mode === 'escape' ? o.r + o.options.radialRate * t : Math.max(2, o.r * Math.exp(-o.options.radialRate * t / o.r));
            const x = o.target.x + r * (o.radial.x * Math.cos(a) + o.tangent.x * Math.sin(a)), y = o.target.y + r * o.radial.y * Math.cos(a), z = o.target.z + r * (o.radial.z * Math.cos(a) + o.tangent.z * Math.sin(a));
            const dx = o.target.x - x, dy = o.target.y - y, dz = o.target.z - z;
            return { ...o.start, x, y, z, yaw: Math.atan2(dx, dz) / FLIGHT_RAD, pitch: Math.atan2(dy, Math.hypot(dx, dz)) / FLIGHT_RAD, roll: o.start.roll + (o.options.bank - o.start.roll) * Math.sin(Math.min(1, t) * Math.PI / 2) };
        }
        let pose = { ...this.initial };
        for (const leg of this.legs) {
            if (timeMs < leg.atMs)
                break;
            pose = maneuverPose(leg.start, leg.command, (timeMs - leg.atMs) / 1000);
        }
        return pose;
    }
}

