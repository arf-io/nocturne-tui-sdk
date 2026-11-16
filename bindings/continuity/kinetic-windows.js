import {clamp,smooth,finite} from './observatory.js';
/** Host-neutral, reversible spatial windows and shape masks. No terminal or wall clock ownership. */
export const WINDOW_SHAPES = ['rectangle', 'rounded', 'ellipse', 'hexagon', 'diamond', 'capsule', 'ticket', 'squircle', 'petal', 'wave'];
export const WINDOW_EFFECTS = ['fade', 'bounce', 'genie', 'roll-up', 'roll-down', 'drawer-left', 'drawer-right', 'drawer-top', 'drawer-bottom', 'center', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'iris', 'explosion', 'accordion', 'portal', 'orbital-bloom', 'venetian', 'ribbon-unfurl'];
export const DEFAULT_WINDOW_OPTIONS = { effect: 'genie', durationMs: 850, chrome: 'mac', shape: 'rounded', opacity: .85, depthFade: .008, overshoot: .18, folds: 6, explosionDistance: 32, anchorX: .5, anchorY: 1.15, controlWidth: 10, controlHeight: 3, customSide: 'right', customOrder: 'minimize,maximize,background,close', customGlyphs: '−,□,◇,×', seed: 2030 };
export const WINDOW_CONTROLS = { durationMs: [0, 5000, 25, 'ms'], opacity: [0, 1, .01, 'mix'], depthFade: [0, .08, .001, 'per world unit'], overshoot: [0, .7, .01, 'fraction'], folds: [1, 20, 1, 'folds'], explosionDistance: [0, 100, 1, 'world units'], anchorX: [-2, 3, .05, 'window widths'], anchorY: [-2, 3, .05, 'window heights'], controlWidth: [5, 15, 1, 'cells'], controlHeight: [3, 6, 1, 'rows'], seed: [0, 4294967295, 1, 'integer'] };
/** Unit-square coverage masks; a false result must also reject pointer hits. */
export function shapeContains(shape, u, v) {
    if (!WINDOW_SHAPES.includes(shape))
        throw new Error(`Unknown window shape ${shape}`);
    if (!Number.isFinite(u + v) || u < 0 || u > 1 || v < 0 || v > 1)
        return false;
    const x = Math.abs(u - .5) * 2, y = Math.abs(v - .5) * 2;
    switch (shape) {
        case 'rectangle': return true;
        case 'rounded': return Math.pow(Math.max(0, x - .78) / .22, 2) + Math.pow(Math.max(0, y - .65) / .35, 2) <= 1;
        case 'ellipse': return x * x + y * y <= 1;
        case 'hexagon': return x <= 1 - y * .32;
        case 'diamond': return x + y <= 1;
        case 'capsule': return x < .5 || Math.pow((x - .5) * 2, 2) + y * y <= 1;
        case 'ticket': return !((u < .075 || u > .925) && Math.abs(v - .5) < .14);
        case 'squircle': return Math.pow(x, 4) + Math.pow(y, 4) <= 1;
        case 'petal': return x * x + y * y <= .78 + .22 * Math.cos(Math.atan2(v - .5, u - .5) * 6);
        case 'wave': return v > .04 + .04 * Math.sin(u * 13) && v < .94 + .035 * Math.cos(u * 15);
        default: return true;
    }
}
export function validateWindowOptions(input = {}) {
    const o = { ...DEFAULT_WINDOW_OPTIONS, ...input };
    for (const k of Object.keys(input))
        if (!(k in DEFAULT_WINDOW_OPTIONS))
            throw new Error(`Unknown window option ${k}`);
    for (const [k, [lo, hi]] of Object.entries(WINDOW_CONTROLS)) {
        finite(o[k], lo, hi, k);
        if (['folds', 'controlWidth', 'controlHeight', 'seed'].includes(k) && !Number.isInteger(o[k]))
            throw new Error(`${k} must be integer`);
    }
    if (!WINDOW_EFFECTS.includes(o.effect) || !WINDOW_SHAPES.includes(o.shape))
        throw new Error('Unknown window shape/effect');
    if (!['mac', 'windows', 'gnome', 'custom'].includes(o.chrome) || !['left', 'right'].includes(o.customSide))
        throw new Error('Invalid chrome profile/side');
    const actions = o.customOrder.split(',');
    if (actions.length !== 4 || new Set(actions).size !== 4 || actions.some(a => !['minimize', 'maximize', 'background', 'close'].includes(a)))
        throw new Error('customOrder must contain each of minimize,maximize,background,close once');
    const glyphs = o.customGlyphs.split(',');
    if (glyphs.length !== 4 || glyphs.some(g => [...g].length !== 1 || /[\u0000-\u001f\u007f-\u009f]/.test(g)))
        throw new Error('customGlyphs: four comma-separated single glyphs');
    return o;
}
export class WindowManager {
    constructor() {
        this.windows = [];
        this.options = { ...DEFAULT_WINDOW_OPTIONS };
        this.selected = '';
        this.order = 0;
    }
    /** Add an owned, uniquely identified window. Bounds are world units, not fixed screen pixels. */
    add(input) {
        if (this.windows.length >= 32 || typeof input.id !== 'string' || !/^[\w.-]{1,64}$/.test(input.id) || this.windows.some(w => w.id === input.id))
            throw new Error('Window ID invalid/duplicate, or capacity reached');
        if (typeof input.title !== 'string' || input.title.length > 160)
            throw new Error('Window title too long');
        const w = { id: input.id, title: input.title, x: 0, y: 0, z: 0, width: 30, height: 16, yaw: 0, pitch: 0, roll: 0, state: 'normal', content: input.content ?? 'A surface for your application.', order: ++this.order, transition: { atMs: 0, from: 1, to: 1, durationMs: 0, effect: 'fade' }, maxAtMs: 0, maxFrom: 0, maxTo: 0 };
        for (const k of ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'width', 'height'])
            if (input[k] !== undefined)
                w[k] = finite(input[k], ['width', 'height'].includes(k) ? 2 : -1000, ['width', 'height'].includes(k) ? 100 : 1000, k);
        if (input.shape !== undefined) {
            if (!WINDOW_SHAPES.includes(input.shape))
                throw new Error('Unknown shape');
            w.shape = input.shape;
        }
        if (typeof w.content !== 'string' || w.content.length > 4096)
            throw new Error('Window content bounded at 4096 characters');
        this.windows.push(w);
        if (!this.selected)
            this.selected = w.id;
    }
    /** Override one window's mask; undefined restores the manager's default shape. */
    setShape(id, shape) { if (shape !== undefined && !WINDOW_SHAPES.includes(shape))
        throw new Error('Unknown window shape'); const w = this.get(id); if (shape === undefined)
        delete w.shape;
    else
        w.shape = shape; }
    configure(input) { this.options = validateWindowOptions({ ...this.options, ...input }); }
    list() { return this.windows.map(w => ({ ...w, transition: { ...w.transition } })); }
    get(id) { const w = this.windows.find(w => w.id === id); if (!w)
        throw new Error(`Unknown window ${id}`); return w; }
    select(id) { const w = this.get(id); this.selected = id; w.order = ++this.order; }
    move(id, values) {
        const w = this.get(id), copy = { ...w };
        for (const [k, v] of Object.entries(values)) {
            if (!['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'width', 'height'].includes(k))
                throw new Error(`Invalid pose field ${k}`);
            copy[k] = finite(v, ['width', 'height'].includes(k) ? 2 : -1000, ['width', 'height'].includes(k) ? 100 : 1000, k);
        }
        Object.assign(w, copy);
    }
    /** Non-destructive minimize/close. Restore retains content, pose and identity. */
    act(id, action, atMs) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        const w = this.get(id), pose = this.pose(id, atMs);
        if (action === 'background') {
            w.order = Math.min(...this.windows.map(v => v.order)) - 1;
            w.z = Math.max(...this.windows.filter(v => v.id !== id).map(v => v.z), w.z) + 3;
            return;
        }
        if (action === 'maximize') {
            if (pose.visibility < 1)
                w.transition = { atMs, from: pose.visibility, to: 1, durationMs: this.options.durationMs * (1 - pose.visibility), effect: this.options.effect };
            w.maxFrom = pose.maximized;
            w.maxTo = w.state === 'maximized' ? 0 : 1;
            w.maxAtMs = atMs;
            w.state = w.maxTo ? 'maximized' : 'normal';
            this.select(id);
            return;
        }
        let to;
        if (action === 'restore') {
            to = 1;
            w.state = 'normal';
            w.maxFrom = pose.maximized;
            w.maxTo = 0;
            w.maxAtMs = atMs;
            this.select(id);
        }
        else if (action === 'minimize' || action === 'close') {
            to = 0;
            w.state = action === 'minimize' ? 'minimized' : 'closed';
        }
        else if (action === 'roll') {
            to = w.state === 'rolled' ? 1 : .16;
            w.state = w.state === 'rolled' ? 'normal' : 'rolled';
        }
        else
            throw new Error('Unknown window action');
        w.transition = { atMs, from: pose.visibility, to, durationMs: this.options.durationMs * Math.max(.1, Math.abs(to - pose.visibility)), effect: action === 'roll' ? 'roll-up' : this.options.effect };
    }
    /** Sample a transition; repeat evaluation is pure and does not change the manager. */
    pose(id, atMs) {
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        const w = this.get(id), t = w.transition, p = t.durationMs ? smooth(clamp((atMs - t.atMs) / t.durationMs, 0, 1)) : 1;
        const visibility = t.from + (t.to - t.from) * p, mp = this.options.durationMs ? smooth(clamp((atMs - w.maxAtMs) / this.options.durationMs, 0, 1)) : 1;
        return { ...w, transition: { ...t }, visibility, maximized: w.maxFrom + (w.maxTo - w.maxFrom) * mp, opacity: this.options.opacity * Math.max(.2, 1 - Math.max(0, w.z) * this.options.depthFade), effect: t.effect };
    }
    /** Chrome controls use large hit targets independently of the decoration glyph. */
    controls(id) {
        this.get(id);
        const o = this.options;
        const actions = o.chrome === 'mac' ? ['close', 'minimize', 'maximize', 'background'] : o.chrome === 'gnome' ? ['background', 'minimize', 'maximize', 'close'] : o.chrome === 'custom' ? o.customOrder.split(',') : ['minimize', 'maximize', 'background', 'close'];
        const icons = o.chrome === 'mac' ? { close: '●', minimize: '−', maximize: '+', background: '◇' } : o.chrome === 'gnome' ? { close: '×', minimize: '⌄', maximize: '□', background: '▱' } : { close: '×', minimize: '_', maximize: '□', background: '◇' };
        const colors = { close: 0xf18c8c, minimize: 0xd7be7a, maximize: 0x8bcdb5, background: 0xb7a8e0 };
        return actions.map((action, index) => ({ action, glyph: o.chrome === 'custom' ? o.customGlyphs.split(',')[index] : icons[action], label: action === 'background' ? 'Back' : action === 'maximize' ? 'Max' : action === 'minimize' ? 'Min' : 'Close', color: colors[action], width: o.controlWidth, height: o.controlHeight, side: o.chrome === 'custom' ? o.customSide : o.chrome === 'mac' ? 'left' : 'right', index }));
    }
}
/** A deformable material plane. u/v retain source coordinates for exact masked hit testing. */
export function windowVertex(w, u, v, o) {
    const p = clamp(w.visibility, 0, 1), q = 1 - p, W = w.width, H = w.height;
    let x = (u - .5) * W, y = (.5 - v) * H, z = 0, alpha = 1;
    switch (w.effect) {
        case 'fade':
            alpha = p;
            break;
        case 'bounce': {
            const scale = p + o.overshoot * Math.sin(p * Math.PI * 3) * Math.sin(p * Math.PI);
            x *= scale;
            y *= scale;
            alpha = Math.min(1, p * 4);
            break;
        }
        case 'genie': {
            const pinch = p + (1 - p) * Math.pow(v, 2) * .07;
            x = x * (p + (1 - p) * Math.pow(1 - v, 3) * .18) + (o.anchorX - .5) * W * q * (.2 + .8 * v);
            y = y * p + (.5 - o.anchorY) * H * q;
            z = Math.sin(v * Math.PI) * q * W * .3;
            alpha = Math.min(1, p * 5);
            break;
        }
        case 'roll-up':
            y = H * .5 - v * H * p;
            z = Math.sin(v * Math.PI * 2) * q * 2;
            alpha = Math.min(1, p * 8);
            break;
        case 'roll-down':
            y = -H * .5 + (1 - v) * H * p;
            z = Math.sin(v * Math.PI * 2) * q * 2;
            alpha = Math.min(1, p * 8);
            break;
        case 'drawer-left':
            x = -W * .5 + u * W * p;
            alpha = Math.min(1, p * 6);
            break;
        case 'drawer-right':
            x = W * .5 - (1 - u) * W * p;
            alpha = Math.min(1, p * 6);
            break;
        case 'drawer-top':
            y = H * .5 - v * H * p;
            alpha = Math.min(1, p * 6);
            break;
        case 'drawer-bottom':
            y = -H * .5 + (1 - v) * H * p;
            alpha = Math.min(1, p * 6);
            break;
        case 'top-left':
            x = -W * .5 + u * W * p;
            y = H * .5 - v * H * p;
            break;
        case 'top-right':
            x = W * .5 - (1 - u) * W * p;
            y = H * .5 - v * H * p;
            break;
        case 'bottom-left':
            x = -W * .5 + u * W * p;
            y = -H * .5 + (1 - v) * H * p;
            break;
        case 'bottom-right':
            x = W * .5 - (1 - u) * W * p;
            y = -H * .5 + (1 - v) * H * p;
            break;
        case 'center':
            x *= p;
            y *= p;
            break;
        case 'iris':
            alpha = p;
            break;
        case 'explosion': {
            const fu = Math.floor(u * 6), fv = Math.floor(v * 4), a = ((fu * 71 + fv * 113 + o.seed) % 360) * Math.PI / 180;
            x += Math.cos(a) * q * o.explosionDistance;
            y += Math.sin(a) * q * o.explosionDistance * .7;
            z += q * ((fu + fv) % 3 - 1) * 12;
            alpha = p * p;
            break;
        }
        case 'accordion':
            y *= p;
            z = Math.sin(v * Math.PI * o.folds) * q * W * .13;
            alpha = Math.min(1, p * 5);
            break;
        case 'portal': {
            const a = q * Math.PI * 2, c = Math.cos(a), s = Math.sin(a), ox = x;
            x = (x * c - y * s) * p;
            y = (ox * s + y * c) * p;
            z = q * 30;
            alpha = Math.min(1, p * 3);
            break;
        }
        case 'orbital-bloom': {
            const a = q * Math.PI, c = Math.cos(a), s = Math.sin(a), ox = x;
            x = (x * c - y * s) * p;
            y = (ox * s + y * c) * p + Math.sin(q * Math.PI) * H;
            z = Math.sin(q * Math.PI) * W;
            alpha = Math.sqrt(p);
            break;
        }
        case 'venetian': {
            const stripe = Math.floor(v * o.folds), mid = (stripe + .5) / o.folds;
            y = (.5 - mid) * H + (mid - v) * H * p;
            z = Math.sin(q * Math.PI / 2) * (v - mid) * H * 2;
            alpha = p;
            break;
        }
        case 'ribbon-unfurl': {
            const a = q * (u - .5) * Math.PI * 4;
            x *= p;
            y = y * p + Math.sin(a) * H * q * .5;
            z = Math.cos(a) * q * W * .3;
            alpha = Math.min(1, p * 4);
            break;
        }
    }
    const rad = Math.PI / 180, cy = Math.cos(w.yaw * rad), sy = Math.sin(w.yaw * rad), cp = Math.cos(w.pitch * rad), sp = Math.sin(w.pitch * rad), cr = Math.cos(w.roll * rad), sr = Math.sin(w.roll * rad);
    let a = x * cy + z * sy, b = -x * sy + z * cy, c = y * cp - b * sp;
    z = y * sp + b * cp;
    x = a * cr - c * sr;
    y = a * sr + c * cr;
    return { x: x + w.x, y: y + w.y, z: z + w.z, u, v, opacity: alpha * w.opacity };
}

