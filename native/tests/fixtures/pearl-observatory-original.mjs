
export const TAU = Math.PI * 2;
export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export const fract = (v) => v - Math.floor(v);
export const smooth = (v) => { const p = clamp(v, 0, 1); return p * p * (3 - 2 * p); };
export function finite(v, lo, hi, label) { if (typeof v !== 'number' || !Number.isFinite(v) || v < lo || v > hi)
    throw new RangeError(`${label}: ${lo}..${hi}`); return v; }
export function hash32(v) { v |= 0; v = Math.imul(v ^ (v >>> 16), 0x7feb352d); v = Math.imul(v ^ (v >>> 15), 0x846ca68b); return (v ^ (v >>> 16)) >>> 0; }
export const randomAt = (seed, index) => hash32(seed ^ Math.imul(index + 1, 0x9e3779b9)) / 4294967296;
export const hex = (c) => '#' + (c >>> 0).toString(16).padStart(6, '0');
export const rgb = (s) => { if (!/^#[0-9a-f]{6}$/i.test(s))
    throw new RangeError('Expected #RRGGBB'); return parseInt(s.slice(1), 16); };
export function mixColor(a, b, t) { t = clamp(t, 0, 1); return (Math.round((a >>> 16) * (1 - t) + (b >>> 16) * t) << 16) | (Math.round(((a >>> 8) & 255) * (1 - t) + ((b >>> 8) & 255) * t) << 8) | Math.round((a & 255) * (1 - t) + (b & 255) * t); }
/** An explicit monotonic clock. sample() advances elapsed time, not frame count.
 * Call shouldPaint() only for decorative work. Input must call present directly.
 * Changing fps never changes timeMs. setPaused needs the current host timestamp.
 */
export class MotionClock {
    constructor(fps = 60) {
        this.timeMs = 0;
        this.paused = false;
        this.exact = 0;
        this.last = null;
        this.paintAt = 0;
        this.fps = finite(fps, 1, 120, 'fps');
    }
    setFps(fps) { this.fps = finite(fps, 1, 120, 'fps'); }
    sample(wallMs) { finite(wallMs, 0, Number.MAX_SAFE_INTEGER, 'wallMs'); if (this.last !== null && wallMs < this.last)
        throw new RangeError('monotonic clock moved backward'); if (this.last !== null && !this.paused)
        this.exact += wallMs - this.last; this.last = wallMs; this.timeMs = Math.floor(this.exact); return this.timeMs; }
    shouldPaint(wallMs) { this.sample(wallMs); const step = 1000 / this.fps; if (this.paused || wallMs - this.paintAt + 1e-6 < step)
        return false; this.paintAt = wallMs - ((wallMs - this.paintAt) % step); return true; }
    setPaused(paused, wallMs) { this.sample(wallMs); this.paused = paused; }
    seek(timeMs, wallMs) { finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'timeMs'); this.exact = timeMs; this.timeMs = Math.floor(timeMs); this.last = wallMs; this.paintAt = wallMs; }
}
/** Piecewise constant rate integration. Changing speed preserves position.
 * Units: rate units/second, times milliseconds. Retains 256 rate boundaries.
 * Old checkpoints must be retained externally for unlimited backwards replay.
 */
export class RateTimeline {
    constructor(rate) { this.segments = [{ atMs: 0, position: 0, rate: finite(rate, -10000, 10000, 'rate') }]; }
    at(timeMs) { finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'timeMs'); let s = this.segments[0]; if (timeMs < s.atMs)
        throw new RangeError('time precedes retained rate checkpoint'); for (const v of this.segments) {
        if (v.atMs > timeMs)
            break;
        s = v;
    } return s.position + (timeMs - s.atMs) * s.rate / 1000; }
    set(atMs, rate) { finite(rate, -10000, 10000, 'rate'); if (atMs < this.segments[this.segments.length - 1].atMs)
        throw new RangeError('unordered rate event'); const position = this.at(atMs); if (atMs === this.segments[this.segments.length - 1].atMs)
        this.segments.pop(); this.segments.push({ atMs, position, rate }); if (this.segments.length > 256)
        this.segments.shift(); }
}
export const MODULATION_TARGETS = ['brightness', 'lightness', 'chroma', 'hueOffset', 'gradientSpeed', 'rotationSpeed', 'secondAxisSpeed', 'starCount', 'starSpeed', 'starDensity', 'novaRegularity', 'weatherIntensity', 'scopeGain', 'windowOpacity', 'gradientScreens', 'gradientAngle', 'axisPitch', 'pivotX', 'pivotY', 'cameraYaw', 'cameraPitch', 'cameraRoll', 'cameraX', 'cameraY', 'cameraZ', 'travelYaw', 'travelPitch', 'trailMs', 'weatherSpeed', 'tickerSpeed', 'hueStep', 'textHueSpeed'];
/** Bounded sensor-to-style routing with analytical attack/release envelopes.
 * The caller supplies all timestamps in ONE monotonic domain. No device access.
 * Stale samples restore the caller's baseline, never a fabricated zero sample.
 */
export class ModulationBus {
    constructor() {
        this.samples = new Map();
        this.bindings = [];
        this.envelopes = new Map();
    }
    bind(binding) {
        const b = { curve: 1, deadband: 0, ...binding };
        if (!/^[a-zA-Z0-9_.-]{1,64}$/.test(b.source) || !MODULATION_TARGETS.includes(b.target))
            throw new RangeError('unknown source or modulation target');
        for (const k of ['inputMin', 'inputMax', 'outputMin', 'outputMax'])
            finite(b[k], -1e12, 1e12, k);
        if (b.inputMax <= b.inputMin)
            throw new RangeError('input range must increase');
        for (const k of ['attackMs', 'releaseMs'])
            finite(b[k], 0, 60000, k);
        finite(b.ttlMs, 1, 3600000, 'ttlMs');
        finite(b.curve, 0.05, 10, 'curve');
        finite(b.deadband, 0, 1, 'deadband');
        const i = this.bindings.findIndex(v => v.target === b.target);
        if (i >= 0)
            this.bindings.splice(i, 1, b);
        else {
            if (this.bindings.length >= 16)
                throw new RangeError('16 binding limit');
            this.bindings.push(b);
        }
        this.envelopes.delete(b.target);
    }
    unbind(target) { const i = this.bindings.findIndex(b => b.target === target); if (i >= 0)
        this.bindings.splice(i, 1); this.envelopes.delete(target); }
    valueAt(target, time) { const e = this.envelopes.get(target); return e ? e.tau === 0 ? e.to : e.to + (e.from - e.to) * Math.exp(-Math.max(0, time - e.atMs) / e.tau) : undefined; }
    ingest(sample) {
        if (!sample || !/^[a-zA-Z0-9_.-]{1,64}$/.test(sample.source))
            throw new RangeError('invalid sensor source');
        finite(sample.value, -1e12, 1e12, 'sensor value');
        finite(sample.atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        finite(sample.seq, 1, Number.MAX_SAFE_INTEGER, 'seq');
        if (!Number.isInteger(sample.seq))
            throw new RangeError('seq integer required');
        const prev = this.samples.get(sample.source);
        if (prev && sample.seq <= prev.seq)
            return false;
        if (prev && sample.atMs < prev.atMs)
            throw new RangeError('sensor clock moved backward');
        if (!prev && this.samples.size >= 128)
            throw new RangeError('128 sensor limit');
        const clean = { source: sample.source, value: sample.value, atMs: sample.atMs, seq: sample.seq, unit: String(sample.unit ?? '').slice(0, 24), quality: String(sample.quality ?? 'external').slice(0, 24) };
        for (const b of this.bindings.filter(b => b.source === sample.source)) {
            const n = Math.pow(clamp((sample.value - b.inputMin) / (b.inputMax - b.inputMin), 0, 1), b.curve ?? 1), to = b.outputMin + (b.outputMax - b.outputMin) * n, old = this.valueAt(b.target, sample.atMs) ?? b.outputMin;
            if (Math.abs(to - old) < (b.deadband ?? 0) * Math.abs(b.outputMax - b.outputMin) && this.envelopes.has(b.target))
                continue;
            this.envelopes.set(b.target, { atMs: sample.atMs, from: old, to, tau: to > old ? b.attackMs : b.releaseMs });
        }
        this.samples.set(sample.source, clean);
        return true;
    }
    resolve(base, atMs) { const out = { ...base }; for (const b of this.bindings) {
        const s = this.samples.get(b.source), v = this.valueAt(b.target, atMs);
        if (s && v !== undefined && atMs >= s.atMs && atMs - s.atMs <= b.ttlMs)
            out[b.target] = v;
    } return out; }
}
const nc = (label, group, min, max, step, d, unit = '') => ({ label, group, min, max, step, default: d, unit });
export const OBSERVATORY_CONTROLS = {
    fps: nc('Presentation ceiling', 'Timing', 1, 120, 1, 60, 'fps'),
    gradientScreens: nc('Distance between adjacent stops', 'Gradient', .05, 8, .05, .75, 'screens'), gradientAngle: nc('Primary angle', 'Gradient', -360, 360, 1, -18, 'degrees'), gradientSpeed: nc('Gradient travel', 'Gradient', -2, 2, .01, .06, 'screens/s'), gradientPhase: nc('Phase', 'Gradient', -8, 8, .05, 0, 'screens'), feather: nc('Transition feather', 'Gradient', 0, 1, .01, 1),
    pivotX: nc('Pivot X / outside is allowed', 'Axes', -3, 4, .05, .5, 'screens'), pivotY: nc('Pivot Y', 'Axes', -3, 4, .05, .5, 'screens'), axisPitch: nc('Second-axis starting tilt', 'Axes', -180, 180, 1, 20, 'degrees'), rotationSpeed: nc('Primary-axis rotation', 'Axes', -90, 90, .5, 4, 'degrees/s'), secondAxisSpeed: nc('Second-axis rotation', 'Axes', -90, 90, .5, 2, 'degrees/s'), swingAngle: nc('Pendulum half-swing', 'Axes', 0, 180, 1, 60, 'degrees'), swingSeconds: nc('Pendulum full cycle', 'Axes', .5, 90, .5, 16, 'seconds'),
    lightness: nc('Oklab lightness L', 'Color', .05, .95, .01, .62), chroma: nc('OKLCh chroma ceiling', 'Color', 0, .4, .005, .14), brightness: nc('Background mix', 'Color', 0, 1, .01, .28), hueOffset: nc('Hue offset', 'Color', -360, 360, 1, 0, 'degrees'), textLightness: nc('Text lightness', 'Typography', .35, .95, .01, .83), textChroma: nc('Text chroma', 'Typography', 0, .3, .005, .10), hueStep: nc('Adjacent character hue distance', 'Typography', -90, 90, 1, 13, 'degrees'), textHueSpeed: nc('Text hue sweep', 'Typography', -90, 90, 1, 12, 'degrees/s'), arrivalMs: nc('Remote text arrival', 'Typography', 0, 2500, 20, 520, 'ms'), topFade: nc('Top-edge attenuation', 'Typography', 0, .65, .01, .18), fallMs: nc('Falling glyph travel', 'Typography', 0, 4000, 20, 1100, 'ms'), tickerSpeed: nc('Ticker velocity', 'Typography', 0, 30, .5, 7, 'cells/s'),
    starDensity: nc('Twinkle occupation', 'Stars', 0, .3, .002, .035), starCount: nc('Warp points', 'Stars', 0, 1200, 10, 420), starSpeed: nc('Travel velocity', 'Stars', 0, 40, .25, 5, 'units/s'), trailMs: nc('Trail exposure', 'Stars', 0, 250, 5, 65, 'ms'), novaRegularity: nc('Automatic nova cadence', 'Stars', 0, 60, .5, 3, 'per minute'), novaStrength: nc('Nova glow', 'Stars', 0, 1, .01, .28),
    cameraYaw: nc('Camera yaw', '3D', -180, 180, 1, 0, 'degrees'), cameraPitch: nc('Camera pitch', '3D', -89, 89, 1, 0, 'degrees'), cameraRoll: nc('Camera roll', '3D', -180, 180, 1, 0, 'degrees'), cameraX: nc('Camera X', '3D', -30, 30, .25, 0), cameraY: nc('Camera Y', '3D', -30, 30, .25, 0), cameraZ: nc('Camera Z', '3D', -30, 30, .25, 0), travelYaw: nc('Travel heading', '3D', -180, 180, 1, 0, 'degrees'), travelPitch: nc('Travel elevation', '3D', -89, 89, 1, 0, 'degrees'), fov: nc('Horizontal field of view', '3D', 25, 120, 1, 70, 'degrees'),
    weatherIntensity: nc('Keystroke / pointer weather', 'Weather', 0, 1, .01, .38), weatherLifeMs: nc('Weather lifetime', 'Weather', 200, 8000, 100, 2400, 'ms'), weatherSpeed: nc('Weather propagation', 'Weather', 1, 50, .5, 12, 'cells/s'),
    windowOpacity: nc('Window background opacity', 'Windows', 0, 1, .01, .78), transitionMs: nc('Window transition', 'Windows', 0, 2000, 20, 560, 'ms'), ruleSpeed: nc('Rule motion', 'Windows', 0, 30, .5, 6, 'cells/s'), scopeGain: nc('Scope gain', 'Sensors', .1, 10, .1, 1), sensorAttack: nc('Routing attack', 'Sensors', 0, 2000, 10, 60, 'ms'), sensorRelease: nc('Routing release', 'Sensors', 0, 5000, 20, 420, 'ms')
};
export const BACKGROUND_STYLES = ['linear', 'double-axis', 'wave', 'plasma', 'caustics', 'vortex', 'contours', 'aurora', 'woven', 'moire', 'tunnel', 'diamond', 'bilinear', 'checker', 'warp'];
export const WEATHER_STYLES = ['ripples', 'rain', 'snow', 'embers', 'sparks', 'nova'];
export const DEFAULT_OBSERVATORY_OPTIONS = { ...Object.fromEntries(Object.entries(OBSERVATORY_CONTROLS).map(([k, c]) => [k, c.default])), backgroundStyle: 'double-axis', weatherStyle: 'ripples', orbitMode: 'spin', sampling: 'half', lockLightness: true, flatNavigation: false, typedColor: true, motion: true, stopWidths: [], starGlyphs: '.·∙⋅⠁⠂⠄⡀⠈⠐⠠⢀' };
/** Atomic options normalization. Unknown fields, NaN, infinities, wrong types,
 * unsupported glyphs, and unbounded arrays throw before callers commit state. */
export function validateOptions(patch, base = DEFAULT_OBSERVATORY_OPTIONS) {
    const out = { ...base, stopWidths: [...base.stopWidths] };
    for (const [k, v] of Object.entries(patch)) {
        const rule = OBSERVATORY_CONTROLS[k];
        if (rule) {
            out[k] = finite(v, rule.min, rule.max, k);
            continue;
        }
        const enums = { backgroundStyle: BACKGROUND_STYLES, weatherStyle: WEATHER_STYLES, orbitMode: ['spin', 'pendulum'], sampling: ['cell', 'half', 'vertical', 'braille'] };
        if (enums[k]) {
            if (typeof v !== 'string' || !enums[k].includes(v))
                throw new RangeError(k);
            out[k] = v;
            continue;
        }
        if (['lockLightness', 'flatNavigation', 'typedColor', 'motion'].includes(k)) {
            if (typeof v !== 'boolean')
                throw new RangeError(k);
            out[k] = v;
            continue;
        }
        if (k === 'stopWidths') {
            if (!Array.isArray(v) || v.length > 32)
                throw new RangeError('0..32 stop intervals');
            out[k] = v.map(n => finite(n, .05, 16, 'stop width'));
            continue;
        }
        if (k === 'starGlyphs') {
            if (typeof v !== 'string' || [...v].length < 1 || [...v].length > 32 || [...v].some(ch => { const n = ch.codePointAt(0); return !((n >= 33 && n <= 126) || (n >= 0x2801 && n <= 0x28ff) || [0xb7, 0x2219, 0x22c5, 0x22c6, 0x2726, 0x2727].includes(n)); }))
                throw new RangeError('star glyphs must be 1..32 supported single-cell scalars');
            out[k] = v;
            continue;
        }
        throw new RangeError('Unknown option ' + k);
    }
    return out;
}
/** Camera-space perspective. Glyph cell aspect is 1:2. Near plane 0.2, far 150.
 * Returns a floating cell coordinate/depth, or null behind/outside depth range. */
export function projectPoint(point, camera, width, height) {
    let x = point.x - camera.x, y = point.y - camera.y, z = point.z - camera.z;
    const yaw = -camera.yaw * Math.PI / 180, pitch = -camera.pitch * Math.PI / 180, roll = -camera.roll * Math.PI / 180;
    [x, z] = [x * Math.cos(yaw) + z * Math.sin(yaw), -x * Math.sin(yaw) + z * Math.cos(yaw)];
    [y, z] = [y * Math.cos(pitch) - z * Math.sin(pitch), y * Math.sin(pitch) + z * Math.cos(pitch)];
    [x, y] = [x * Math.cos(roll) - y * Math.sin(roll), x * Math.sin(roll) + y * Math.cos(roll)];
    if (!Number.isFinite(x + y + z) || z < .2 || z > 150)
        return null;
    const f = width / (2 * Math.tan(camera.fov * Math.PI / 360));
    return { x: width / 2 + x * f / z, y: height / 2 - y * f / z / 2, z };
}
/** Signed distance in adjacent-stop units. One horizontal/vertical screen is
 * respectively width/height cells. Double-axis input is handled by fieldPhase. */
export function gradientPosition(x, y, width, height, o) { const a = o.gradientAngle * Math.PI / 180; return (x / Math.max(1, width) * Math.cos(a) + y / Math.max(1, height) * Math.sin(a)) / o.gradientScreens; }
export const OBSERVATORY_SCENES = [
    ['chat', 'AI CHAT / Pearl conversation'], ['scope', 'PEARL / reactive signal'], ['warp', 'WARP / free-vector starflight'], ['dag', 'DAG / orbital knowledge'], ['spatial-menu', 'MENU / spatial constellation'], ['bbs', 'BBS / Starfall exchange'], ['bbs-config', 'BBS / configuration desk'], ['windows', 'WINDOWS / glass workspaces'], ['lynx', 'LYNX / text browser study'], ['nano', 'NANO / editor study'], ['pico', 'PICO / correspondence study'], ['tmux', 'TMUX / pane composition'], ['controls', 'ATELIER / controls + rules'], ['sensors', 'SENSORS / modulation routing'], ['logs', 'LOG WATCH / observability'], ['text', 'TYPOGRAPHY / falling light']
].map(([id, name]) => ({ id, name }));
/** Bounded interaction state. All domain writes are synchronous; input never
 * advances motion time or waits for animation. save/export is explicit. */
export class ObservatoryModel {
    constructor() {
        this.options = validateOptions({});
        this.motionMs = 0;
        this.dataMs = 0;
        this.revealThroughMs = -1;
        this.revision = 0;
        this.scene = 'chat';
        this.draft = '';
        this.selected = 0;
        this.focusId = 0;
        this.hover = -1;
        this.events = [];
        this.messages = [];
        this.bus = new ModulationBus();
        this.palette = { id: 'smart-dark', name: 'Smart Dark / Velvet Circuitry', colors: ['#647795', '#af88bb', '#69a9a5', '#b89477', '#73709f'], background: '#101319', ink: '#dfd8cc' };
        this.travel = new RateTimeline(DEFAULT_OBSERVATORY_OPTIONS.gradientSpeed);
        this.warpTravel = new RateTimeline(DEFAULT_OBSERVATORY_OPTIONS.starSpeed);
        this.orbit = new RateTimeline(DEFAULT_OBSERVATORY_OPTIONS.rotationSpeed);
        this.orbit2 = new RateTimeline(DEFAULT_OBSERVATORY_OPTIONS.secondAxisSpeed);
        this.width = 136;
        this.height = 44;
        this.notice = 'Local demonstration. No providers or shell connected.';
        this.showPalette = false;
        this.paletteQuery = '';
        this.page = 0;
        this.scroll = 0;
        this.windowSelected = 0;
        this.drag = null;
        this.simulation = true;
        this.editor = '// observatory.ts\n// This editable buffer never runs as code.\n\nconst palette = "smart-dark";\nconst motion = { fps: 60, durationMs: 560 };\n\n// Local ink bypasses arrival fades.\nrenderOnInput();\nrenderMotionAt(explicitTimeMs);';
        this.editorCursor = 0;
        this.waveform = Array(128).fill(0);
        this.sourceLabel = 'SYNTHETIC / opt in to microphone or system sensors';
        this.sensorSeq = 0;
        this.waveStates = new Map();
        this.serial = 0;
        this.routedRates = new Map();
        this.windows = [{ id: 1, title: 'PEARL / signal', x: 3, y: 7, width: 57, height: 17, mode: 'normal', from: 0, target: 0, changedMs: 0, fadeFrom: 1, fadeTarget: 1, fadeAt: 0 }, { id: 2, title: 'FLEET / atlas', x: 63, y: 9, width: 48, height: 14, mode: 'normal', from: 0, target: 0, changedMs: 0, fadeFrom: 1, fadeTarget: 1, fadeAt: 0 }, { id: 3, title: 'INSPECTOR / styles', x: 28, y: 26, width: 72, height: 11, mode: 'normal', from: 0, target: 0, changedMs: 0, fadeFrom: 1, fadeTarget: 1, fadeAt: 0 }];
        this.messages = [{ id: ++this.serial, text: 'PEARL: The fleet is awake. Every trace has a source; every action has a place.', atMs: 0, local: false }, { id: ++this.serial, text: 'ATLAS: Select an agent, inspect a signal, or type here. Your ink never waits for the weather.', atMs: 0, local: false }];
        this.receive('IRIS: Evidence lane / 12 sources indexed, 3 cross-checks queued. Shared parents remain one node in the graph.');
        this.receive('ONYX: Tool lane / build artifacts are local. Approval is required before a real adapter can dispatch a command.');
        this.receive('PEARL: Signal lane / these traces are explicitly synthetic until you connect a measurement source.');
        this.receive('ATLAS: There is no animation queue between your keyboard and the composer. Arrival fades apply to remote prose, not to your own keystrokes.');
    }
    configure(patch) { const next = validateOptions(patch, this.options); for (const [key, timeline] of [['gradientSpeed', this.travel], ['starSpeed', this.warpTravel], ['rotationSpeed', this.orbit], ['secondAxisSpeed', this.orbit2]])
        if (next[key] !== this.options[key])
            timeline.set(this.motionMs, next[key]); this.options = next; if (!next.motion)
        this.revealThroughMs = Math.max(this.revealThroughMs, this.motionMs); this.routedRates.clear(); this.revision++; }
    resize(width, height) { finite(width, 36, 240, 'width'); finite(height, 18, 100, 'height'); if (!Number.isInteger(width) || !Number.isInteger(height))
        throw new RangeError('whole cells'); this.width = width; this.height = height; this.revision++; }
    setScene(scene) { if (!OBSERVATORY_SCENES.some(s => s.id === scene))
        throw new RangeError('unknown scene'); this.scene = scene; this.selected = 0; this.scroll = 0; this.notice = OBSERVATORY_SCENES.find(s => s.id === scene).name + ' / interactive study'; this.revision++; }
    setTime(timeMs) { finite(timeMs, 0, Number.MAX_SAFE_INTEGER, 'timeMs'); this.motionMs = Math.floor(timeMs); }
    input(text) { if (typeof text !== 'string')
        throw new TypeError('text required'); const scalar = [...text]; if ([...this.draft].length + scalar.length > 4096)
        throw new RangeError('4096 scalar draft limit'); const start = [...this.draft].length; this.draft += text; for (let i = 0; i < Math.min(32, scalar.length); i++)
        this.emit(5 + (start + i) % Math.max(1, this.width - 12), this.height - 4, scalar[i]); this.revision++; }
    replaceDraft(text) { if ([...text].length > 4096)
        throw new RangeError('draft limit'); const old = this.draft; this.draft = text; const common = [...old].findIndex((ch, i) => ch !== [...text][i]); if (text.length >= old.length)
        this.emit(5 + [...text].length % (this.width - 12), this.height - 4, [...text].slice(-1)[0] ?? '·');
    else if (common >= 0)
        this.emit(5 + common % (this.width - 12), this.height - 4, '·'); this.revision++; }
    backspace() { this.draft = [...this.draft].slice(0, -1).join(''); this.revision++; }
    send() { if (!this.draft.trim())
        return; this.messages.push({ id: ++this.serial, text: 'YOU: ' + this.draft, atMs: this.motionMs, local: true }); this.draft = ''; if (this.messages.length > 256)
        this.messages.shift(); this.notice = 'Note stored in this mockup, not sent to a provider.'; this.revision++; }
    receive(text) { if (typeof text !== 'string' || [...text].length > 4096)
        throw new RangeError('message size'); if (!this.options.motion)
        this.revealThroughMs = Math.max(this.revealThroughMs, this.motionMs); this.messages.push({ id: ++this.serial, text, atMs: this.motionMs, local: false }); if (this.messages.length > 256)
        this.messages.shift(); this.revision++; }
    emit(x, y, glyph = '·', kind = this.options.weatherStyle) { finite(x, -4096, 4096, 'x'); finite(y, -4096, 4096, 'y'); if (!WEATHER_STYLES.includes(kind))
        throw new RangeError('weather kind'); if (!glyph || /[\x00-\x1f\x7f-\x9f]/.test(glyph))
        glyph = '·'; this.events.push({ id: ++this.serial, x, y, atMs: this.motionMs, kind, glyph: [...glyph][0] ?? '·' }); if (this.events.length > 128)
        this.events.shift(); }
    ingest(sample) { const changed = this.bus.ingest(sample); if (changed) {
        this.dataMs = Math.max(this.dataMs, sample.atMs);
        this.routeRates(this.dataMs);
        this.revision++;
    } return changed; }
    demoData(timeMs) { if (!this.simulation)
        return; this.dataMs = timeMs; const t = timeMs / 1000; this.waveform = Array.from({ length: 128 }, (_, i) => (Math.sin(i * .12 + t * 1.6) * .42 + Math.sin(i * .32 - t * .9) * .19) * (.75 + .15 * Math.sin(t))); const seq = ++this.sensorSeq; for (const [source, value] of [['demo.audio', .3 + .24 * Math.sin(t * 1.8)], ['demo.heat', 51 + 7 * Math.sin(t * .12)], ['demo.network', 18 + 12 * Math.sin(t * .6)]])
        this.bus.ingest({ source, value, atMs: timeMs, seq, quality: 'synthetic' }); this.revision++; }
    /** Validate and commit one bounded waveform block. Never fabricates samples.
     * Hardware access remains in the host; this accepts normalized telemetry only. */
    ingestWaveform(row) {
        if (!row || !/^[a-zA-Z0-9_.-]{1,64}$/.test(row.source) || !Array.isArray(row.samples) || row.samples.length < 2 || row.samples.length > 1024)
            throw new RangeError('invalid waveform record');
        finite(row.seq, 1, Number.MAX_SAFE_INTEGER, 'seq');
        finite(row.atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        if (!Number.isInteger(row.seq))
            throw new RangeError('integer sequence required');
        for (const v of row.samples)
            finite(v, -32, 32, 'waveform sample');
        const old = this.waveStates.get(row.source);
        if (old && row.seq <= old.seq)
            return false;
        if (old && row.atMs < old.atMs)
            throw new RangeError('unordered waveform time');
        if (!old && this.waveStates.size >= 128)
            throw new RangeError('waveform source limit');
        this.waveStates.set(row.source, { seq: row.seq, atMs: row.atMs });
        this.waveform = Array.from({ length: 128 }, (_, i) => row.samples[Math.floor(i * row.samples.length / 128)]);
        this.sourceLabel = (row.quality === 'synthetic' ? 'SYNTHETIC' : row.quality === 'measured' ? 'MEASURED' : 'EXTERNAL') + ' / ' + row.source;
        this.simulation = false;
        this.revision++;
        return true;
    }
    /** Commit sensor-rate targets on explicit DATA heartbeats, never in render().
     * This makes phase changes replayable and independent of presentation FPS.
     * Record these heartbeat timestamps alongside source samples for exact replay. */
    routeRates(atMs) { this.dataMs = finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'dataMs'); const o = this.effective(atMs); for (const [key, timeline] of [['gradientSpeed', this.travel], ['starSpeed', this.warpTravel], ['rotationSpeed', this.orbit], ['secondAxisSpeed', this.orbit2]]) {
        const v = o[key];
        if (this.routedRates.get(key) !== v) {
            timeline.set(this.motionMs, v);
            this.routedRates.set(key, v);
        }
    } }
    effective(atMs = this.dataMs) { const resolved = this.bus.resolve(this.options, atMs), patch = {}; for (const target of MODULATION_TARGETS) {
        const v = resolved[target], rule = OBSERVATORY_CONTROLS[target];
        if (typeof v === 'number' && rule)
            patch[target] = clamp(v, rule.min, rule.max);
    } return validateOptions(patch, this.options); }
    windowProgress(w) { return w.from + (w.target - w.from) * smooth((this.motionMs - w.changedMs) / Math.max(1, this.options.transitionMs)); }
    windowAlpha(w) { return w.fadeFrom + (w.fadeTarget - w.fadeFrom) * smooth((this.motionMs - w.fadeAt) / Math.max(1, this.options.transitionMs)); }
    toggleWindow(index, mode) { const w = this.windows[index]; if (!w)
        return; if (mode === 'fade') {
        w.fadeFrom = this.windowAlpha(w);
        w.fadeTarget = w.fadeTarget > .5 ? .10 : 1;
        w.fadeAt = this.motionMs;
    }
    else {
        w.from = this.windowProgress(w);
        w.target = w.mode === mode ? 0 : mode === 'maximized' ? 1 : -1;
        w.mode = w.mode === mode ? 'normal' : mode;
        w.changedMs = this.motionMs;
    } this.windowSelected = index; this.revision++; }
    exportState() { return { version: 4, scene: this.scene, motionMs: this.motionMs, dataMs: this.dataMs, width: this.width, height: this.height, options: this.options, palette: this.palette, events: this.events, messages: this.messages, draft: this.draft, bindings: this.bus.bindings, samples: [...this.bus.samples.values()] }; }
}
/** Convert authored sRGB palette stops to Oklch for interpolation. The final
 * gamut map is performed by the shared integer C/WASM converter, not CSS/HSV. */
export function rgbToOklch(color) {
    const linear = (v) => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; };
    const r = linear(color >>> 16), g = linear((color >>> 8) & 255), b = linear(color & 255);
    const l = Math.cbrt(.4122214708 * r + .5363325363 * g + .0514459929 * b), m = Math.cbrt(.2119034982 * r + .6806995451 * g + .1073969566 * b), s = Math.cbrt(.0883024619 * r + .2817188376 * g + .6299787005 * b);
    const L = .2104542553 * l + .793617785 * m - .0040720468 * s, a = 1.9779984951 * l - 2.428592205 * m + .4505937099 * s, bb = .0259040371 * l + .7827717662 * m - .808675766 * s;
    return [L, Math.hypot(a, bb), ((Math.atan2(bb, a) * 180 / Math.PI) % 360 + 360) % 360];
}
const BRAILLE_BITS = [1, 8, 2, 16, 4, 32, 64, 128];
export function flattened(frame, i) { const glyph = frame.cells[i]; return [0x2580, 0x2584, 0x258c, 0x2590].includes(glyph) ? mixColor(frame.cells[i + 1], frame.cells[i + 2], .5) : frame.cells[i + 2]; }
export function putCell(frame, x, y, glyph, fg, alpha = 1, id = 0) { x = Math.floor(x); y = Math.floor(y); if (x < 0 || y < 0 || x >= frame.width || y >= frame.height)
    return; const i = (y * frame.width + x) * 4, bg = flattened(frame, i); frame.cells[i] = glyph; frame.cells[i + 1] = mixColor(bg, fg, alpha); frame.cells[i + 2] = bg; frame.cells[i + 3] = id; }
/** Eight addressable braille bits share one foreground colour, as on a terminal. */
export function putDot(frame, px, py, color, alpha = 1, id = 0) {
    px = Math.round(px);
    py = Math.round(py);
    if (px < 0 || py < 0 || px >= frame.width * 2 || py >= frame.height * 4)
        return;
    const x = px >> 1, y = py >> 2, i = (y * frame.width + x) * 4;
    if (frame.cells[i] < 0x2800 || frame.cells[i] > 0x28ff) {
        frame.cells[i + 2] = flattened(frame, i);
        frame.cells[i] = 0x2800;
    }
    frame.cells[i] |= BRAILLE_BITS[(py % 4) * 2 + (px % 2)];
    frame.cells[i + 1] = mixColor(frame.cells[i + 2], color, alpha);
    if (id)
        frame.cells[i + 3] = id;
}
/** Clipped braille segment; avoids unbounded loops for near-plane projections. */
export function drawSegment(frame, x0, y0, x1, y1, color, alpha = 1, id = 0) {
    x0 *= 2;
    x1 *= 2;
    y0 *= 4;
    y1 *= 4;
    const dx = x1 - x0, dy = y1 - y0;
    let lo = 0, hi = 1;
    for (const [p, q] of [[-dx, x0], [dx, frame.width * 2 - 1 - x0], [-dy, y0], [dy, frame.height * 4 - 1 - y0]]) {
        if (!p && q < 0)
            return;
        if (!p)
            continue;
        const v = q / p;
        if (p < 0)
            lo = Math.max(lo, v);
        else
            hi = Math.min(hi, v);
        if (lo > hi)
            return;
    }
    const ax = Math.round(x0 + lo * dx), ay = Math.round(y0 + lo * dy), bx = Math.round(x0 + hi * dx), by = Math.round(y0 + hi * dy), n = Math.max(Math.abs(bx - ax), Math.abs(by - ay), 1);
    for (let j = 0; j <= n; j++)
        putDot(frame, ax + (bx - ax) * j / n, ay + (by - ay) * j / n, color, alpha, id);
}
function createCamera(o) { return { x: o.cameraX, y: o.cameraY, z: o.cameraZ, yaw: o.cameraYaw, pitch: o.cameraPitch, roll: o.cameraRoll, fov: o.fov }; }
/** CPU material renderer, exporting ordinary terminal cells. Colors use the
 * shared OKLCh kernel; projection/scene composition is the TS high-level layer.
 * render() never owns a clock and never mutates the application's event log. */
export class ObservatoryRenderer {
    constructor(engine) {
        this.engine = engine;
        this.rampKey = '';
        this.ramp = new Uint32Array(2048);
        this.stopTotal = 1;
        this.wheel = new Uint32Array(360);
        this.wheelKey = '';
    }
    prepare(palette, o) {
        const key = JSON.stringify([palette.colors, palette.background, o.lightness, o.chroma, o.brightness, o.hueOffset, o.lockLightness, o.feather, o.stopWidths]);
        if (key !== this.rampKey) {
            if (!Array.isArray(palette.colors) || palette.colors.length < 1 || palette.colors.length > 32)
                throw new RangeError('One to 32 palette stops');
            palette.colors.forEach(rgb);
            rgb(palette.background);
            rgb(palette.ink);
            this.rampKey = key;
            const stops = palette.colors.map(s => rgbToOklch(rgb(s)));
            const weights = stops.map((_, i) => o.stopWidths[i] ?? 1);
            this.stopTotal = weights.reduce((a, b) => a + b, 0);
            const cumulative = [0];
            for (const w of weights)
                cumulative.push(cumulative[cumulative.length - 1] + w);
            const baseL = rgbToOklch(rgb(palette.background))[0];
            for (let i = 0; i < this.ramp.length; i++) {
                const p = i / this.ramp.length * this.stopTotal;
                let index = 0;
                while (index + 1 < stops.length && cumulative[index + 1] <= p)
                    index++;
                const a = stops[index], b = stops[(index + 1) % stops.length];
                let f = (p - cumulative[index]) / weights[index];
                f = o.feather === 0 ? 0 : smooth(clamp((f - (1 - o.feather) / 2) / o.feather, 0, 1));
                let h1 = a[2], h2 = b[2];
                if (a[1] < .005)
                    h1 = h2;
                if (b[1] < .005)
                    h2 = h1;
                const delta = ((h2 - h1 + 540) % 360) - 180, h = h1 + delta * f + o.hueOffset;
                const L = o.lockLightness ? o.lightness : a[0] * (1 - f) + b[0] * f, C = Math.min(o.chroma, a[1] * (1 - f) + b[1] * f + .025);
                this.ramp[i] = this.engine.oklch(Math.round(clamp(baseL + (L - baseL) * o.brightness, 0, 1) * 1000), Math.round(clamp(C * o.brightness, 0, .4) * 10000), Math.round(h * 1000));
            }
        }
        const wk = JSON.stringify([o.textLightness, o.textChroma]);
        if (wk !== this.wheelKey) {
            this.wheelKey = wk;
            for (let h = 0; h < 360; h++)
                this.wheel[h] = this.engine.oklch(Math.round(o.textLightness * 1000), Math.round(o.textChroma * 10000), h * 1000);
        }
    }
    colorAt(phase) { return this.ramp[Math.floor(fract(phase / this.stopTotal) * this.ramp.length)]; }
    ink(hue) { return this.wheel[((Math.round(hue) % 360) + 360) % 360]; }
    field(nx, ny, m, o) {
        const t = m.motionMs / 1000;
        let a = (o.gradientAngle + m.orbit.at(m.motionMs)) * Math.PI / 180, b = (o.axisPitch + m.orbit2.at(m.motionMs)) * Math.PI / 180;
        if (o.orbitMode === 'pendulum') {
            a = (o.gradientAngle + Math.sin(t * TAU / o.swingSeconds) * o.swingAngle) * Math.PI / 180;
            b = (o.axisPitch + Math.sin(t * TAU / o.swingSeconds + .7) * o.swingAngle * .5) * Math.PI / 180;
        }
        let x = nx - o.pivotX, y = ny - o.pivotY;
        const xr = x * Math.cos(a) - y * Math.sin(a), yr = x * Math.sin(a) + y * Math.cos(a), z = yr * Math.sin(b), v = yr * Math.cos(b), r = Math.hypot(xr, v), ang = Math.atan2(v, xr);
        let p = xr;
        switch (o.backgroundStyle) {
            case 'linear':
                p = (nx * Math.cos(o.gradientAngle * Math.PI / 180) + ny * Math.sin(o.gradientAngle * Math.PI / 180));
                break;
            case 'double-axis':
                p = xr + z * .6;
                break;
            case 'wave':
                p = xr + Math.sin(v * 8 + t * .5) * .16;
                break;
            case 'plasma':
                p = (Math.sin(xr * 6 + t * .4) + Math.sin(v * 8 - t * .6) + Math.sin((xr + v) * 5 + t * .3) + Math.sin(r * 9 - t * .4)) * .18;
                break;
            case 'caustics':
                p = Math.abs(Math.sin(xr * 8 + t * .23) + Math.sin(v * 10 - t * .36)) * .22 + Math.sin((xr + v) * 12 + t * .5) * .1;
                break;
            case 'vortex':
                p = r * .6 + Math.sin(ang * 3 + r * 14 - t * .9) * .22;
                break;
            case 'contours':
                p = Math.sin(xr * 3 + t * .17) * .3 + Math.sin(v * 4 - t * .21) * .3;
                break;
            case 'aurora':
                p = v + .2 * Math.sin(xr * 6 + t * .3) + .08 * Math.sin(xr * 17 - t * .6);
                break;
            case 'woven':
                p = Math.sin(xr * 18 + t * .4) * Math.cos(v * 15 - t * .3) * .3;
                break;
            case 'moire':
                p = (Math.sin(xr * 25 + t * .2) + Math.sin((xr * Math.cos(b) - v * Math.sin(b)) * 26 - t * .15)) * .17;
                break;
            case 'tunnel':
                p = -Math.log(Math.max(.025, r)) * .3 + ang * .06;
                break;
            case 'diamond':
                p = Math.abs(xr) + Math.abs(v);
                break;
            case 'bilinear':
                p = xr * v * 2 + xr * .4 + v * .6;
                break;
            case 'checker':
                p = Math.sin(xr * 12) * Math.sin(v * 12);
                break;
            case 'warp':
                p = r * .5 + Math.sin(ang * 3 + t * .12) * .07;
                break;
        }
        return (p + m.travel.at(m.motionMs) + o.gradientPhase) / o.gradientScreens;
    }
    background(m, o = m.effective()) {
        this.prepare(m.palette, o);
        const w = m.width, h = m.height, cells = new Uint32Array(w * h * 4), f = { width: w, height: h, cells };
        const sample = (x, y) => this.colorAt(this.field(x / w, y / h, m, o));
        const base = rgb(m.palette.background);
        for (let y = 0; y < h; y++)
            for (let x = 0; x < w; x++) {
                const i = (y * w + x) * 4;
                cells[i + 3] = 0;
                if (o.sampling === 'half') {
                    cells[i] = 0x2580;
                    cells[i + 1] = sample(x + .5, y + .25);
                    cells[i + 2] = sample(x + .5, y + .75);
                }
                else if (o.sampling === 'vertical') {
                    cells[i] = 0x258c;
                    cells[i + 1] = sample(x + .25, y + .5);
                    cells[i + 2] = sample(x + .75, y + .5);
                }
                else if (o.sampling === 'braille') {
                    let mask = 0;
                    for (let k = 0; k < 8; k++) {
                        const p = this.field((x + (k % 2 + .5) / 2) / w, (y + (Math.floor(k / 2) + .5) / 4) / h, m, o);
                        if (fract(p) > (hash32(x * 33 + y * 977 + k * 71) % 997) / 997)
                            mask |= BRAILLE_BITS[k];
                    }
                    cells[i] = 0x2800 + mask;
                    cells[i + 1] = sample(x + .5, y + .5);
                    cells[i + 2] = base;
                }
                else {
                    cells[i] = 32;
                    cells[i + 1] = rgb(m.palette.ink);
                    cells[i + 2] = sample(x + .5, y + .5);
                }
            }
        return f;
    }
    twinkle(frame, m, o) {
        const glyphs = [...o.starGlyphs], w = frame.width, h = frame.height;
        for (let y = 0; y < h; y++)
            for (let x = 0; x < w; x++) {
                const n = hash32(41041 ^ x * 1973 ^ y * 9277);
                if (n / 4294967296 > o.starDensity)
                    continue;
                const period = 2600 + n % 5800, phase = fract((m.motionMs + (n % period)) / period), amplitude = Math.pow(Math.max(0, Math.sin(phase * Math.PI)), 8) * .65;
                putCell(frame, x, y, glyphs[n % glyphs.length].codePointAt(0), this.ink(n % 360), amplitude);
            }
    }
    warp(frame, m, o) {
        const count = Math.floor(o.starCount), camera = createCamera({ ...o, cameraX: 0, cameraY: 0, cameraZ: 0 }), yaw = o.travelYaw * Math.PI / 180, pitch = o.travelPitch * Math.PI / 180, velocity = { x: Math.sin(yaw) * Math.cos(pitch), y: Math.sin(pitch), z: Math.cos(yaw) * Math.cos(pitch) }, travel = m.warpTravel.at(m.motionMs);
        let drawn = 0;
        for (let i = 0; i < count; i++) {
            const wrap = (v) => fract(v / 80 + .5) * 80 - 40;
            const p = { x: wrap((randomAt(7331, i * 3) - .5) * 80 - velocity.x * travel - o.cameraX), y: wrap((randomAt(7331, i * 3 + 1) - .5) * 80 - velocity.y * travel - o.cameraY), z: wrap((randomAt(7331, i * 3 + 2) - .5) * 80 - velocity.z * travel - o.cameraZ) };
            const a = projectPoint(p, camera, frame.width, frame.height);
            if (!a || a.x < 0 || a.y < 0 || a.x >= frame.width || a.y >= frame.height)
                continue;
            const color = this.ink(190 + randomAt(2941, i) * 130), alpha = clamp(1 - a.z / 55, .15, 1), exposure = o.starSpeed * o.trailMs / 1000;
            const b = projectPoint({ x: p.x + velocity.x * exposure, y: p.y + velocity.y * exposure, z: p.z + velocity.z * exposure }, camera, frame.width, frame.height);
            if (b && o.trailMs > 0)
                drawSegment(frame, a.x, a.y, b.x, b.y, color, alpha);
            else
                putDot(frame, a.x * 2, a.y * 4, color, alpha);
            drawn++;
        }
        return drawn;
    }
    weather(frame, m, o) {
        if (o.weatherIntensity === 0)
            return 0;
        const events = m.events.filter(e => e.atMs <= m.motionMs && m.motionMs - e.atMs < o.weatherLifeMs).slice(-24);
        const period = o.novaRegularity > 0 ? 60000 / o.novaRegularity : Infinity;
        if (Number.isFinite(period)) {
            const k = Math.floor(m.motionMs / period);
            for (let i = Math.max(1, k - 1); i <= k; i++) {
                const atMs = i * period;
                if (m.motionMs - atMs < o.weatherLifeMs)
                    events.push({ id: i + 900000, x: randomAt(53, i) * frame.width, y: randomAt(79, i) * frame.height, atMs, kind: 'nova', glyph: '✦' });
            }
        }
        for (const e of events) {
            const age = m.motionMs - e.atMs, p = age / o.weatherLifeMs, envelope = (1 - p) ** 2, color = this.ink(e.id * 53 + age * .02), strength = o.weatherIntensity * envelope * (e.kind === 'nova' ? o.novaStrength : 1);
            if (e.kind === 'ripples' || e.kind === 'nova') {
                const radius = age / 1000 * o.weatherSpeed, waveWidth = 1.7, max = radius + waveWidth * 3;
                for (let y = Math.max(0, Math.floor(e.y - max / 2)); y < Math.min(frame.height, e.y + max / 2); y++)
                    for (let x = Math.max(0, Math.floor(e.x - max)); x < Math.min(frame.width, e.x + max); x++) {
                        const i = (y * frame.width + x) * 4;
                        const pulse = (yy) => { const d = Math.hypot(x - e.x, (yy - e.y) * 2), ring = Math.abs(d - radius); return Math.exp(-ring * ring / (waveWidth * waveWidth)) * strength * .65; };
                        if (frame.cells[i] === 0x2580) {
                            frame.cells[i + 1] = mixColor(frame.cells[i + 1], color, pulse(y + .25));
                            frame.cells[i + 2] = mixColor(frame.cells[i + 2], color, pulse(y + .75));
                        }
                        else {
                            const bg = frame.cells[i + 2];
                            frame.cells[i + 2] = mixColor(bg, color, pulse(y + .5));
                        }
                    }
                if (e.kind === 'nova' && age < 650)
                    putCell(frame, e.x, e.y, age < 200 ? 0x2219 : age < 430 ? 0x2726 : 0x2727, color, strength);
            }
            else {
                const particleCount = Math.round(16 + o.weatherIntensity * 24);
                for (let j = 0; j < particleCount; j++) {
                    const r = randomAt(e.id, j), r2 = randomAt(e.id + 7919, j), seconds = age / 1000;
                    let x = e.x, y = e.y, glyph = 0xb7;
                    if (e.kind === 'rain') {
                        x += (r - .5) * 20;
                        y -= r2 * 14;
                        y += seconds * o.weatherSpeed;
                        glyph = j % 2 ? 0x2571 : 0x2502;
                    }
                    if (e.kind === 'snow') {
                        x += (r - .5) * 24 + Math.sin(seconds * 2 + r2 * TAU) * 2;
                        y = y - 12 - r2 * 8 + seconds * o.weatherSpeed * .4;
                        glyph = [0xb7, 0x2219, 0x22c5][j % 3];
                    }
                    if (e.kind === 'embers') {
                        x += (r - .5) * seconds * 8;
                        y -= seconds * o.weatherSpeed * (.2 + r2 * .4);
                        glyph = 0x2219;
                    }
                    if (e.kind === 'sparks') {
                        const angle = r * TAU;
                        x += Math.cos(angle) * seconds * o.weatherSpeed * r2;
                        y += Math.sin(angle) * seconds * o.weatherSpeed * r2 / 2 + seconds * seconds * 2;
                        glyph = 0xb7;
                    }
                    putCell(frame, x, y, glyph, color, strength * (.5 + r * .5));
                }
            }
        }
        return events.length;
    }
    /** Paint local/remote text effects without touching stored content. Local input
     * is laid out last and never receives arrival or fall opacity. */
    /** Public adapter for the preserved v0.4 screen-space weather. */
    paintWeatherLayer(frame, m, o) { this.prepare(m.palette, o); return this.weather(frame, m, o); }
    skyText(frame, m, o) {
        const line = 'THE TERMINAL IS A PLACE, NOT A PRINT OUT';
        const age = m.motionMs % 9000;
        const x0 = Math.max(2, Math.floor((frame.width - line.length) / 2));
        for (let i = 0; i < line.length; i++) {
            const born = i * 35, p = smooth((age - born) / Math.max(1, o.fallMs)), y = 2 + (frame.height * .4 - 2) * p;
            putCell(frame, x0 + i, y, line.codePointAt(i), this.ink(o.hueOffset + i * o.hueStep + m.motionMs * o.textHueSpeed / 1000), age < born ? 0 : Math.min(1, p * 1.8));
        }
    }
    /** Render one immutable frame. No mutation to m.options/events/domain data. */
    /** Material plane without UI nodes, suitable below a terminal emulator buffer.
     * Caller still owns the child terminal's text, styles, cursor and presentation. */
    renderSurface(m) { const o = m.effective(); const frame = this.background(m, o); if (o.backgroundStyle === 'warp' || m.scene === 'warp')
        this.warp(frame, m, o);
    else
        this.twinkle(frame, m, o); this.weather(frame, m, o); return frame; }
    render(m, atMs = m.dataMs) {
        const o = m.effective(atMs);
        let frame = this.background(m, o);
        let drawnStars = 0;
        if (m.scene === 'warp' || o.backgroundStyle === 'warp')
            drawnStars = this.warp(frame, m, o);
        else
            this.twinkle(frame, m, o);
        const activeWeather = this.weather(frame, m, o);
        if (m.scene === 'text')
            this.skyText(frame, m, o);
        const composed = composeObservatory(m, o, this, frame);
        frame = this.engine.paint(frame, m.motionMs, composed.nodes);
        return { frame, nodes: composed.nodes, semantics: composed.semantics, drawnStars, activeWeather };
    }
}
export const ORBITAL_NODES = [
    { id: 'operator', label: 'OPERATOR', x: 0, y: 5, z: 17, parents: [] },
    { id: 'planner', label: 'PLANNER', x: -7, y: 1.8, z: 22, parents: ['operator'] },
    { id: 'research', label: 'RESEARCH', x: 7, y: 1.8, z: 22, parents: ['operator'] },
    { id: 'memory', label: 'MEMORY', x: -11, y: -2, z: 32, parents: ['planner'] },
    { id: 'tools', label: 'TOOLS', x: 0, y: -1, z: 27, parents: ['planner', 'research'] },
    { id: 'evidence', label: 'EVIDENCE', x: 11, y: -2, z: 32, parents: ['research'] },
    { id: 'synthesis', label: 'SYNTHESIS', x: 0, y: -6, z: 34, parents: ['memory', 'tools', 'evidence'] },
    { id: 'archive', label: 'ARCHIVE', x: 0, y: -9, z: 42, parents: ['synthesis', 'memory'] }
];
function wrapped(text, width) { const chars = [...text], lines = []; let line = ''; for (const c of chars) {
    if (c === '\n' || [...line].length >= width) {
        lines.push(line);
        line = '';
        if (c === '\n')
            continue;
    }
    line += c;
} lines.push(line); return lines; }
/** Shared composition of gallery/terminal scenes. Synthetic product mockups are
 * explicitly labeled. All drawing is cell output; no pixel shaders or CSS glow. */
export function composeObservatory(m, o, r, under) {
    const nodes = [], semantics = [], w = m.width, h = m.height, INK = rgb(m.palette.ink), TEAL = r.ink(185), LILAC = r.ink(300), COPPER = r.ink(65), MUTED = r.engine.oklch(620, 180, 240000), BG = rgb(m.palette.background);
    const add = (n) => { if (n.width <= 0 || n.height <= 0)
        return; nodes.push(n); };
    const text = (x, y, width, value, fg = INK, extra = {}) => add({ kind: 'text', x: Math.round(x), y: Math.round(y), width: Math.max(0, Math.round(width)), height: 1, text: value, fg, fgOpacity: 1000, ...extra });
    const line = (x, y, width, style = 0) => add({ kind: 'rule', x: Math.round(x), y: Math.round(y), width: Math.max(0, Math.round(width)), height: 1, style, fg: LILAC, fgOpacity: 480, colorAnimation: 3, hueBrightness: Math.round(o.textLightness * 1000), hueSaturation: Math.round(o.textChroma * 2500), hueStep: 4, hueSpeed: Math.round(o.textHueSpeed) });
    const box = (x, y, width, height, title, extra = {}) => add({ kind: 'box', x: Math.round(x), y: Math.round(y), width: Math.max(0, Math.round(width)), height: Math.max(0, Math.round(height)), text: title, fg: TEAL, bg: BG, bgOpacity: Math.round(o.windowOpacity * 1000), fgOpacity: 900, style: 0, ...extra });
    const button = (id, x, y, width, label, selected = false, disabled = false) => { add({ kind: 'item', id, x: Math.round(x), y: Math.round(y), width: Math.max(0, Math.round(width)), height: 1, text: label, state: disabled ? 3 : (selected || m.focusId === id) ? 2 : 0, fg: (selected || m.focusId === id) ? TEAL : INK, bg: 0x24353e, bgOpacity: (selected || m.focusId === id) ? 850 : 100, fgOpacity: 1000 }); semantics.push({ id, label, disabled }); };
    const trace = (x, y, width, height, data, fg = TEAL, id = 0) => add({ kind: 'line', id, x: Math.round(x), y: Math.round(y), width: Math.max(1, Math.round(width)), height: Math.max(1, Math.round(height)), data: data.map(v => Math.round(clamp(v, 0, 1) * 1000)), fg, fgOpacity: 950 });
    const progress = (x, y, width, value, fg = TEAL) => add({ kind: 'progress', x: Math.round(x), y: Math.round(y), width: Math.max(1, Math.round(width)), height: 1, value: Math.round(clamp(value, 0, 1) * 1000), fg, bg: 0x212631, bgOpacity: 900, style: 0 });
    const colorText = { colorAnimation: 3, hueBase: Math.round(o.hueOffset), hueStep: Math.round(o.hueStep), hueSpeed: Math.round(o.textHueSpeed), hueBrightness: Math.round(o.textLightness * 1000), hueSaturation: Math.round(o.textChroma * 2500) };
    text(2, 1, Math.max(1, w - 4), 'NOCTURNE / OBSERVATORY', INK, { ...colorText, hueStep: 6 });
    if (w >= 92)
        text(Math.max(35, w - 48), 1, 46, `${String(Math.round(o.fps)).padStart(3)} FPS CEILING   |   OKLCh   |   VOL IV`, MUTED);
    line(2, 3, w - 4);
    const noNav = ['warp', 'windows', 'dag', 'spatial-menu', 'tmux'].includes(m.scene), nav = w >= 114 && !noNav, x = nav ? 25 : 3, y = 6, cw = w - x - 3, bh = h - y - 8;
    if (nav) {
        text(2, 5, 20, 'WORKSPACES', MUTED);
        const available = Math.min(OBSERVATORY_SCENES.length, h - 14);
        for (let i = 0; i < available; i++) {
            const s = OBSERVATORY_SCENES[i];
            button(100 + i, 2, 7 + i, 20, s.name.split(' / ')[0], s.id === m.scene);
        }
        text(2, h - 6, 20, '[ CTRL+K / FIND ]', LILAC, { id: 8801 });
        semantics.push({ id: 8801, label: 'Open command palette' });
    }
    const waveform = m.waveform.map(v => clamp(.5 + v * o.scopeGain * .42, 0, 1));
    const caption = (title, subtitle) => { text(x, y - 1, cw, title, TEAL); text(x, y + 1, cw, subtitle, MUTED); };
    if (m.scene === 'chat') {
        const side = cw >= 96 ? 26 : 0, tw = cw - side - 1;
        box(x, y, tw, bh, ' PEARL / AI CHAT AGENT ');
        const chatRows = bh - 4, lines = [];
        for (const msg of m.messages)
            for (const value of wrapped(msg.text, Math.max(1, tw - 6)))
                lines.push({ value, at: msg.atMs, local: msg.local });
        const end = Math.max(0, lines.length - m.scroll), visible = lines.slice(Math.max(0, end - chatRows), end), top = y + 2 + Math.max(0, chatRows - visible.length);
        visible.forEach((v, i) => { const age = Math.max(0, m.motionMs - v.at), opacity = v.local ? 1000 : r.engine.inkOpacity(Math.min(4294967295, age), (!o.motion || v.at <= m.revealThroughMs) ? 0 : o.arrivalMs, Math.round((top + i - y - 2) * 256), 6 * 256, Math.round((1 - o.topFade) * 1000)); text(x + 3, top + i, tw - 6, v.value, v.local ? COPPER : INK, { fgOpacity: opacity }); });
        if (side) {
            const sx = x + tw + 1;
            box(sx, y, side, bh, ' AGENTS ');
            for (const [i, label] of ['ATLAS / orchestrator', 'IRIS / evidence', 'PEARL / synthesis', 'ONYX / tools'].entries())
                button(200 + i, sx + 2, y + 3 + i * 2, side - 4, label, i === m.selected);
            trace(sx + 2, y + 13, side - 4, Math.max(3, bh - 19), waveform, TEAL);
            text(sx + 2, y + bh - 3, side - 4, 'DEMO / LOCAL ONLY', MUTED);
        }
    }
    else if (m.scene === 'scope') {
        caption('PEARL SIGNAL / REACTIVE INSTRUMENT', m.simulation ? 'Synthetic reference + synthetic signal / connect audio for a measured trace.' : 'Measured or supplied waveform / no decorative signal is mixed into it.');
        box(x, y + 3, cw, bh - 3, ' TIME DOMAIN ');
        const tx = x + 3, ty = y + 6, tw = cw - 6, th = Math.max(3, bh - 13);
        if (m.simulation)
            trace(tx, ty, tw, th, m.waveform.map((v, i) => clamp(.5 + Math.sin(i * .075 + m.dataMs * .0003) * .3, 0, 1)), LILAC);
        trace(tx, ty, tw, th, waveform, TEAL, 7000);
        line(tx, ty + Math.floor(th / 2), tw, 3);
        const rms = [...m.bus.samples.values()].filter(s => s.source.endsWith('.rms')).sort((a, b) => b.atMs - a.atMs)[0]?.value, peak = [...m.bus.samples.values()].filter(s => s.source.endsWith('.peak')).sort((a, b) => b.atMs - a.atMs)[0]?.value;
        text(tx, y + bh - 4, tw, `RMS ${rms === undefined ? '--' : rms.toFixed(3)}     PEAK ${peak === undefined ? '--' : peak.toFixed(3)}     GAIN ${o.scopeGain.toFixed(1)}     ${m.sourceLabel}`, MUTED);
        semantics.push({ id: 7000, label: 'Inspect waveform' });
    }
    else if (m.scene === 'warp') {
        text(4, 6, w - 8, 'WARP FIELD / XYZ STARFLIGHT', TEAL, { ...colorText, hueStep: 4 });
        text(4, 8, w - 8, 'Independent camera orientation and travel vector. Drag the camera controls; trails use exposure time.', MUTED);
        const metrics = [['CAMERA', `${o.cameraYaw.toFixed(0)} / ${o.cameraPitch.toFixed(0)} / ${o.cameraRoll.toFixed(0)} deg`], ['TRAVEL', `${o.travelYaw.toFixed(0)} / ${o.travelPitch.toFixed(0)} deg`], ['VELOCITY', `${o.starSpeed.toFixed(2)} world units/s`], ['EXPOSURE', `${o.trailMs.toFixed(0)} ms / independent of FPS`]];
        metrics.forEach(([k, v], i) => text(4, h - 13 + i * 2, w - 8, `${k.padEnd(12)} ${v}`, i === 2 ? COPPER : MUTED));
    }
    else if (m.scene === 'dag' || m.scene === 'spatial-menu') {
        caption(m.scene === 'dag' ? 'ORBITAL DAG / SHARED IDENTITY' : 'SPATIAL MENU / FOCUS CONSTELLATION', 'Tab selects stable IDs. Enter inspects. Camera controls orbit; flatten to a conventional graph.');
        const gw = cw, gh = bh - 5, camera = createCamera(o), projected = ORBITAL_NODES.map((n, i) => { const p = o.flatNavigation ? { x: (i === 0 ? .5 : i === 1 ? .25 : i === 2 ? .75 : i === 3 ? .13 : i === 4 ? .5 : i === 5 ? .87 : .5) * gw, y: [1, 6, 6, 12, 12, 12, 18, 22][i] / 24 * gh, z: 20 } : projectPoint(n, camera, gw, gh); return { n, i, p: p ? { x: p.x + x, y: p.y + y + 4, z: p.z } : null }; });
        for (const item of projected)
            for (const parent of item.n.parents) {
                const start = projected.find(p => p.n.id === parent)?.p;
                if (start && item.p)
                    drawSegment(under, start.x, start.y, item.p.x, item.p.y, r.ink(170 + item.i * 18), .52);
            }
        for (const item of [...projected].sort((a, b) => (b.p?.z ?? 0) - (a.p?.z ?? 0))) {
            const selected = item.i === m.selected, label = m.scene === 'spatial-menu' ? ['AGENTS', 'MESSAGES', 'KNOWLEDGE', 'STORAGE', 'TOOLS', 'METRICS', 'SETTINGS', 'ARCHIVE'][item.i] : item.n.label;
            semantics.push({ id: 5000 + item.i, label });
            if (!item.p)
                continue;
            const px = Math.round(item.p.x - 8), py = Math.round(item.p.y - 1);
            if (px < x - 16 || py < y + 2 || px > x + cw || py > y + bh - 3)
                continue;
            box(px, py, 17, 3, label, { id: 5000 + item.i, fg: selected ? TEAL : MUTED, bgOpacity: selected ? 940 : 650, style: selected ? 1 : 0 });
        }
        const n = ORBITAL_NODES[m.selected % ORBITAL_NODES.length];
        text(x, y + bh - 1, cw, `${n.id.toUpperCase()}   parents: ${n.parents.join(' + ') || 'root'}   /   ${o.flatNavigation ? '2D fallback' : 'XYZ projection'}`, COPPER);
    }
    else if (m.scene === 'bbs') {
        box(x, y, cw, bh, ' STARFALL BBS / SINCE TOMORROW ', { style: 2, fg: LILAC });
        text(x + 4, y + 2, cw - 8, 'S T A R F A L L   /   T H E   P A R T Y   L I N E', LILAC, { ...colorText, hueStep: 5 });
        line(x + 3, y + 4, cw - 6, 9);
        const menu = ['Message boards', 'Live party line', 'Agent directory', 'Files / knowledge', 'Personal settings', 'Disconnect (demo)'];
        menu.forEach((s, i) => button(3000 + i, x + 4, y + 6 + i * 2, Math.min(33, cw - 8), s, m.selected === i));
        if (cw > 75) {
            const sx = x + 42;
            box(sx, y + 6, cw - 46, Math.max(6, bh - 10), ' NOW CONNECTED ');
            ['ATLAS   + synth / running', 'IRIS    + research / waiting', 'PEARL   + scope / listening', 'YOU     + local console'].forEach((s, i) => text(sx + 2, y + 8 + i * 2, cw - 50, s, INK));
            text(sx + 2, y + bh - 6, cw - 50, 'NO MODEM REQUIRED.', COPPER);
        }
    }
    else if (m.scene === 'bbs-config') {
        box(x, y, cw, bh, ' CONFIGURATION / LOCAL PREVIEW ');
        const choices = [['Keystroke weather', o.weatherIntensity > 0], ['Per-character OKLCh ink', o.typedColor], ['Flatten spatial navigation', o.flatNavigation], ['Lock gradient lightness', o.lockLightness], ['Decorative motion', o.motion], ['Immediate local echo (locked)', true]];
        choices.forEach(([label, value], i) => button(4000 + i, x + 3, y + 3 + i * 3, cw - 6, `[${value ? 'x' : ' '}] ${label}`, m.selected === i, i === 5));
        text(x + 3, y + bh - 3, cw - 6, 'Changes apply immediately. Export configuration explicitly to retain it.', MUTED);
    }
    else if (m.scene === 'windows') {
        text(4, 5, w - 8, 'GLASS WORKSPACES / drag a title, collapse, expand or fade', TEAL);
        const ordered = m.windows.map((win, i) => ({ win, i })).sort((a, b) => (a.i === m.windowSelected ? 1 : 0) - (b.i === m.windowSelected ? 1 : 0));
        for (const { win, i } of ordered) {
            const p = m.windowProgress(win), a = m.windowAlpha(win), normal = { x: win.x, y: win.y, width: Math.min(win.width, w - 6), height: Math.min(win.height, h - 14) }, rect = p >= 0 ? { x: normal.x + (3 - normal.x) * p, y: normal.y + (7 - normal.y) * p, width: normal.width + (w - 6 - normal.width) * p, height: normal.height + (h - 16 - normal.height) * p } : { ...normal, height: normal.height + (3 - normal.height) * (-p) };
            const xx = Math.round(rect.x), yy = Math.round(rect.y), ww = Math.round(rect.width), hh = Math.round(rect.height);
            const windowNodeStart = nodes.length;
            box(xx, yy, ww, hh, win.title, { id: 2100 + i, fgOpacity: Math.round(a * 950), bgOpacity: Math.round(a * o.windowOpacity * 1000), fg: i === m.windowSelected ? TEAL : LILAC });
            semantics.push({ id: 2100 + i, label: 'Focus ' + win.title });
            for (const [j, g] of ['_', '+', '~'].entries()) {
                text(xx + ww - 10 + j * 3, yy, 2, g, COPPER, { id: 2200 + i * 10 + j, fgOpacity: Math.round(a * 1000) });
                semantics.push({ id: 2200 + i * 10 + j, label: (j === 0 ? 'Collapse ' : j === 1 ? 'Expand ' : 'Fade ') + win.title });
            }
            if (hh > 6) {
                if (i === 0) {
                    trace(xx + 3, yy + 3, ww - 6, hh - 6, waveform, TEAL);
                    if (nodes.length)
                        nodes[nodes.length - 1].fgOpacity = Math.round(a * 950);
                }
                if (i === 1) {
                    ['queue  03 / inference  67 tok/s', 'latency  184 ms / context  52%', 'ATLAS -> IRIS -> PEARL', 'Synthetic operational data'].forEach((s, j) => { if (j < hh - 4)
                        text(xx + 3, yy + 3 + j, ww - 6, s, j === 3 ? MUTED : INK, { fgOpacity: Math.round(a * 1000) }); });
                }
                if (i === 2) {
                    text(xx + 3, yy + 3, ww - 6, `L ${o.lightness.toFixed(2)}  C ${o.chroma.toFixed(3)}  ${o.gradientScreens.toFixed(2)} screens/stop`, LILAC, { fgOpacity: Math.round(a * 1000) });
                    text(xx + 3, yy + 5, ww - 6, 'Foreground and background opacity are separate.', MUTED, { fgOpacity: Math.round(a * 1000) });
                }
            }
        }
    }
    else if (m.scene === 'lynx') {
        const pages = [{ name: 'Nocturne / home', title: 'THE QUIET WEB', body: 'A text-first knowledge browser. These links navigate local example pages. No network access is performed by this mockup.', links: ['[1] Material catalogue', '[2] Agent playbook', '[3] Return to home'] }, { name: 'Nocturne / materials', title: 'MATERIALS / A CELL IS A CANVAS', body: 'Braille supplies eight spatial bits. Half blocks supply two colors in one cell. Text remains selectable, meaningful and authoritative.', links: ['[1] Home', '[2] Agent playbook', '[3] Surface controls'] }, { name: 'Nocturne / agents', title: 'AGENT PLAYBOOK', body: 'Keep data updates independent of animation. Own one event loop. Bind sensors through bounded declared mappings. Preserve semantic status colors.', links: ['[1] Home', '[2] Material catalogue', '[3] Open command palette'] }];
        const p = pages[m.page % 3];
        box(x, y, cw, bh, ' LYNX-INSPIRED / INTERNAL PAGES ');
        text(x + 3, y + 2, cw - 6, 'Location: local://' + p.name, MUTED);
        text(x + 3, y + 5, cw - 6, p.title, TEAL);
        wrapped(p.body, cw - 8).forEach((s, i) => text(x + 4, y + 8 + i, cw - 8, s));
        p.links.forEach((s, i) => button(6000 + i, x + 4, y + 14 + i * 2, cw - 8, s, m.selected === i));
        text(x + 3, y + bh - 3, cw - 6, 'Tab: link   Enter: open   [B]: back in companion controls', MUTED);
    }
    else if (m.scene === 'nano' || m.scene === 'pico') {
        box(x, y, cw, bh, m.scene === 'nano' ? ' NANO-INSPIRED / EDITABLE SCRATCH BUFFER ' : ' PICO-INSPIRED / COMPOSE A NOTE ', { style: 1 });
        text(x + 2, y + 1, cw - 4, `${m.scene === 'nano' ? 'observatory.ts' : 'message.txt'}  [modified in memory / export only]`, MUTED);
        const lines = m.editor.split('\n').slice(m.scroll, m.scroll + bh - 6);
        lines.forEach((s, i) => { text(x + 2, y + 3 + i, 4, String(i + m.scroll + 1).padStart(3), MUTED); text(x + 7, y + 3 + i, cw - 10, s, s.startsWith('//') ? MUTED : INK, o.typedColor ? { ...colorText, hueStep: 3, hueSpeed: 3 } : {}); });
        line(x + 2, y + bh - 3, cw - 4);
        text(x + 2, y + bh - 2, cw - 4, '^F Find     ^S Export     ^K Commands     ESC Leave     No disk writes', COPPER);
    }
    else if (m.scene === 'tmux') {
        text(3, 5, w - 6, 'TMUX / ANIMATED PANE STUDY (not a multiplexer inside the browser)', TEAL);
        const pw = Math.floor((w - 9) / 2), ph = Math.floor((h - 17) / 2);
        ['AGENT / codex-style study', 'RESEARCH / conversation', 'LOGS / event stream', 'SYSTEM / signal'].forEach((title, i) => { const px = 3 + (i % 2) * (pw + 3), py = 7 + Math.floor(i / 2) * (ph + 1); box(px, py, pw, ph, title, { id: 8000 + i, fg: i === m.selected ? TEAL : MUTED }); semantics.push({ id: 8000 + i, label: title }); if (i === 3)
            trace(px + 2, py + 3, pw - 4, Math.max(1, ph - 5), waveform, TEAL);
        else
            for (let j = 0; j < Math.min(6, ph - 4); j++)
                text(px + 2, py + 3 + j, pw - 4, i === 2 ? `[${String(1034 + j).padStart(5, '0')}] event ${j % 2 ? 'commit' : 'sample'} / accepted` : i === 0 ? ['> build the agent interface', 'reading context ...', 'tests: 27 / 27 passed', 'scope -> geometry -> cells', 'No process is running here.'][j % 5] : ['IRIS: evidence is indexed.', 'ATLAS: preparing the plan.', 'PEARL: listening.'][j % 3], j === 0 ? LILAC : MUTED); });
    }
    else if (m.scene === 'controls') {
        caption('ATELIER / INFORMATION HAS A SHAPE', 'Keyboard focus, disabled state, breadcrumbs, segmented controls, bars and seeded rules.');
        const half = Math.floor((cw - 3) / 2);
        box(x, y + 3, half, bh - 3, ' RULES / SEEDED MOTION ');
        const glyphSets = ['─', '━', '═', '·⋅∙·', '⠁⠈⠐⠂', '▁▂▃▂', '››› ', '▀▄▀▄', '╴ ╶ ', '╱╲╱╲', ' ∙•∙', '○·○·'];
        for (let j = 0; j < Math.min(12, bh - 7); j++) {
            const gs = [...glyphSets[j]], count = Math.max(1, half - 8), phase = Math.floor(m.motionMs * o.ruleSpeed / 1000), str = Array.from({ length: count }, (_, i) => gs[j === 11 ? hash32(i * 197 + j * 13 + phase) % gs.length : ((i + phase) % gs.length)]).join('');
            text(x + 2, y + 5 + j, 3, String(j + 1).padStart(2, '0'), MUTED);
            text(x + 5, y + 5 + j, count, str, TEAL, { ...colorText, hueStep: 4 });
        }
        const sx = x + half + 2;
        box(sx, y + 3, cw - half - 2, bh - 3, ' COMPONENT STATES ');
        ['Selectable / ready', 'Selected / active', 'Disabled / read-only'].forEach((s, i) => button(7001 + i, sx + 2, y + 6 + i * 3, cw - half - 6, s, i === 1, i === 2));
        text(sx + 2, y + 16, cw - half - 6, 'Fleet > ATLAS > tools > inference', MUTED);
        progress(sx + 2, y + 18, cw - half - 6, .67);
        text(sx + 2, y + 20, cw - half - 6, '67% / authoritative value first', TEAL);
        if (bh > 25)
            text(sx + 2, y + 24, cw - half - 6, '[ success ] [ warning ] [ error ]', COPPER);
    }
    else if (m.scene === 'sensors') {
        caption('SENSOR ROUTING / PATCH BAY', 'Sensors are opt-in. Missing hardware stays unavailable, never replaced by fabricated measurements.');
        box(x, y + 3, cw, bh - 3, ' LIVE SOURCES -> BOUNDED STYLE TARGETS ');
        let row = y + 5;
        const entries = [...m.bus.samples.values()].slice(-Math.max(1, bh - 16));
        if (!entries.length)
            text(x + 3, row++, cw - 6, 'No connected sources. Enable a collector or use an explicitly labeled demo.', MUTED);
        for (const sample of entries) {
            const stale = m.dataMs - sample.atMs > 2500;
            text(x + 3, row++, cw - 6, `${sample.source.padEnd(22)} ${sample.value.toFixed(3).padStart(10)}  ${(sample.unit ?? '').padEnd(10)} ${stale ? 'STALE' : sample.quality ?? 'measured'}`, stale ? MUTED : TEAL);
        }
        row = Math.max(row + 2, y + 13);
        for (const b of m.bus.bindings.slice(0, 5))
            text(x + 3, row++, cw - 6, `${b.source}  ->  ${b.target}  [${b.outputMin}..${b.outputMax}]  A${b.attackMs}/R${b.releaseMs}ms`, LILAC);
        button(7100, x + 3, y + bh - 5, cw - 6, 'Demo audio -> brightness / explicit synthetic source', false);
        button(7101, x + 3, y + bh - 3, cw - 6, 'Clear mappings / return to baseline', false);
    }
    else if (m.scene === 'logs') {
        box(x, y, cw, bh, ' OBSERVABILITY / SYNTHETIC STREAM ');
        text(x + 2, y + 2, cw - 4, 'TIME        SEVERITY    SOURCE           EVENT', MUTED);
        line(x + 2, y + 3, cw - 4);
        const count = Math.max(1, bh - 7), tick = Math.floor(m.dataMs / 650);
        for (let i = 0; i < count; i++) {
            const n = Math.max(0, tick - count + 1 + i), severity = n % 11 === 0 ? 'WARN' : n % 7 === 0 ? 'TRACE' : 'INFO', label = `${String(n * 650).padStart(8, '0')}ms  ${severity.padEnd(10)}${['ATLAS', 'IRIS', 'PEARL'][n % 3].padEnd(17)}${['sample accepted', 'token delta / committed', 'checkpoint verified', 'dependency resolved'][n % 4]}`;
            text(x + 2, y + 5 + i, cw - 4, label, severity === 'WARN' ? COPPER : severity === 'TRACE' ? MUTED : INK, { fgOpacity: i < 4 ? Math.round((.70 + i * .07) * 1000) : 1000 });
        }
    }
    else if (m.scene === 'text') {
        text(x, y - 1, cw, 'TYPOGRAPHY / INK, GRAVITY AND HUE', LILAC);
        text(x, y + 1, cw, 'New local text stays put. Falling copies and distant arrivals are decoration.', MUTED);
        const words = 'BRAILLE / HALF BLOCKS / OKLCh / TIME-BASED MOTION / ZERO ARTIFICIAL INPUT WAIT / ';
        const shift = Math.floor(m.motionMs * o.tickerSpeed / 1000) % words.length;
        const ticker = (words + words + words).slice(shift, shift + cw - 4);
        box(x, y + bh - 9, cw, 8, ' SCROLL / CONTINUOUS MARQUEE ');
        text(x + 2, y + bh - 6, cw - 4, ticker, TEAL, { ...colorText, hueStep: 6 });
        text(x + 2, y + bh - 3, cw - 4, 'Per-character hue changes never use HSV in this scene.', MUTED);
    }
    line(2, h - 7, w - 4, 8);
    text(3, h - 6, w - 6, m.notice, MUTED);
    // Persistent local input plane. It is never hidden by a window or an entrance.
    if (!m.managedPrompt) {
    add({ kind: 'text', x: 2, y: h - 4, width: w - 4, height: 2, bg: BG, bgOpacity: 970, text: '', fg: INK });
    text(3, h - 4, 2, '>', TEAL);
    const draft = [...m.draft].slice(-Math.max(1, w - 12)).join('');
    text(6, h - 4, w - 12, draft, INK, o.typedColor ? { ...colorText, hueSpeed: 0 } : {});
    add({ kind: 'cursor', x: Math.min(w - 5, 6 + [...draft].length), y: h - 4, width: 1, height: 1, fg: TEAL, style: 2 });
    }
    text(3, h - 2, w - 6, 'ENTER note   TAB select   CTRL+K commands   ESC back   input commits independently of animation', MUTED);
    if (m.showPalette) {
        add({ kind: 'text', id: 8899, x: 0, y: 0, width: w, height: h, bg: BG, bgOpacity: 650, text: '' });
        const pw = Math.min(70, w - 8), px = Math.floor((w - pw) / 2), py = 7;
        box(px, py, pw, Math.min(h - 12, 22), ' COMMAND PALETTE ', { id: 8898, bgOpacity: 990, fg: TEAL });
        text(px + 3, py + 2, pw - 6, '> ' + m.paletteQuery, INK);
        const matches = OBSERVATORY_SCENES.filter(s => s.name.toLowerCase().includes(m.paletteQuery.toLowerCase())).slice(0, Math.min(14, h - 18));
        semantics.length = 0;
        matches.forEach((s, i) => button(9000 + OBSERVATORY_SCENES.indexOf(s), px + 3, py + 5 + i, pw - 6, s.name, i === m.selected % Math.max(1, matches.length)));
    }
    return { nodes: nodes.slice(0, 512), semantics };
}
/** Activate semantic IDs from pointer or keyboard through one path. Local study
 * actions never dispatch shell commands, agents, or network requests. */
export function activateObservatory(m, id) {
    if (id >= 100 && id < 100 + OBSERVATORY_SCENES.length)
        m.setScene(OBSERVATORY_SCENES[id - 100].id);
    else if (id >= 200 && id < 204) {
        m.selected = id - 200;
        m.notice = ['ATLAS', 'IRIS', 'PEARL', 'ONYX'][m.selected] + ' selected / local chat mockup';
    }
    else if (id >= 3000 && id < 3006) {
        m.selected = id - 3000;
        if (id === 3004)
            m.setScene('bbs-config');
        else if (id === 3001)
            m.setScene('chat');
        else if (id === 3002)
            m.setScene('dag');
        else if (id === 3003)
            m.setScene('lynx');
        else
            m.notice = id === 3005 ? 'Disconnected from the imaginary modem.' : 'Message board selected. No remote service is connected.';
    }
    else if (id >= 4000 && id < 4005) {
        m.selected = id - 4000;
        const key = ['weatherIntensity', 'typedColor', 'flatNavigation', 'lockLightness', 'motion'][id - 4000];
        m.configure({ [key]: key === 'weatherIntensity' ? m.options.weatherIntensity > 0 ? 0 : .38 : !m.options[key] });
    }
    else if (id >= 5000 && id < 5008) {
        m.selected = id - 5000;
        const n = ORBITAL_NODES[m.selected];
        m.notice = n.id + ' / parents: ' + (n.parents.join(' + ') || 'none') + ' / stable shared identity';
    }
    else if (id >= 6000 && id < 6003) {
        m.page = (m.page + id - 6000 + 1) % 3;
        m.selected = 0;
    }
    else if (id >= 2100 && id < 2103) {
        m.windowSelected = id - 2100;
    }
    else if (id >= 2200 && id < 2230) {
        const index = Math.floor((id - 2200) / 10), kind = (id - 2200) % 10;
        if (index < 3 && kind < 3)
            m.toggleWindow(index, ['collapsed', 'maximized', 'fade'][kind]);
    }
    else if (id >= 8000 && id < 8004) {
        m.selected = id - 8000;
        m.notice = 'Pane ' + (m.selected + 1) + ' selected. This is a layout mockup, not a running multiplexer.';
    }
    else if (id === 7100) {
        m.bus.bind({ source: 'demo.audio', target: 'brightness', inputMin: 0, inputMax: .7, outputMin: .1, outputMax: .55, attackMs: m.options.sensorAttack, releaseMs: m.options.sensorRelease, ttlMs: 2000 });
        m.notice = 'Explicit synthetic modulation enabled.';
    }
    else if (id === 7101) {
        for (const b of [...m.bus.bindings])
            m.bus.unbind(b.target);
        m.notice = 'All modulation routes removed.';
    }
    else if (id === 8801)
        m.showPalette = true;
    else if (id >= 9000 && id < 9000 + OBSERVATORY_SCENES.length) {
        m.setScene(OBSERVATORY_SCENES[id - 9000].id);
        m.showPalette = false;
        m.paletteQuery = '';
    }
    else if (id === 7000)
        m.notice = 'Waveform inspection / ' + m.sourceLabel;
    else if (id === 7001 || id === 7002)
        m.notice = 'Component ' + id + ' activated. Disabled components reject activation.';
    m.revision++;
}
/** Minimal code-point-safe scratch editor, not a full Unicode/grapheme editor.
 * Cursor is a UTF-16 offset so browser textarea selections map directly.
 * No reads/writes/commands; one edit is committed before the host paints. */
export function editScratch(m, action, value = '') {
    const text = m.editor, p = clamp(m.editorCursor, 0, text.length), before = text.slice(0, p), after = text.slice(p), previous = [...before].slice(-1)[0]?.length ?? 0, next = after.codePointAt(0) > 0xffff ? 2 : after.length ? 1 : 0;
    if (action === 'insert') {
        if (text.length + value.length > 32768)
            throw new RangeError('scratch buffer limit');
        m.editor = before + value + after;
        m.editorCursor = p + value.length;
    }
    else if (action === 'backspace') {
        m.editor = before.slice(0, before.length - previous) + after;
        m.editorCursor = p - previous;
    }
    else if (action === 'delete')
        m.editor = before + after.slice(next);
    else if (action === 'left')
        m.editorCursor = p - previous;
    else if (action === 'right')
        m.editorCursor = p + next;
    else if (action === 'home')
        m.editorCursor = before.lastIndexOf('\n') + 1;
    else if (action === 'end') {
        const n = after.indexOf('\n');
        m.editorCursor = n < 0 ? text.length : p + n;
    }
    else if (action === 'up' || action === 'down') {
        const start = before.lastIndexOf('\n') + 1, column = p - start;
        if (action === 'up' && start > 0) {
            const previousEnd = start - 1, previousStart = text.lastIndexOf('\n', previousEnd - 1) + 1;
            m.editorCursor = Math.min(previousEnd, previousStart + column);
        }
        if (action === 'down') {
            const n = text.indexOf('\n', p);
            if (n >= 0) {
                const end = text.indexOf('\n', n + 1);
                m.editorCursor = Math.min(end < 0 ? text.length : end, n + 1 + column);
            }
        }
    }
    else
        throw new RangeError('unknown scratch operation');
    const row = m.editor.slice(0, m.editorCursor).split('\n').length - 1;
    m.scroll = Math.max(0, Math.min(m.scroll, row));
    if (row > m.scroll + Math.max(1, m.height - 20))
        m.scroll = row - Math.max(1, m.height - 20);
    m.revision++;
}

