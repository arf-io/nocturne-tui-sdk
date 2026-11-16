import {clamp,finite} from './observatory.js';
import {cameraBasis,EditableRateTimeline} from './kinetic-camera.js';
import {KINETIC_SCENES,KineticModel} from './kinetic-model.js';
import {SKY_LIMITS,seededUnit,softStep,Projector,WORLD_WEATHER} from './black-hole-space.js';
import {FlightDirector} from './black-hole-flight.js';
import {Keymap,DEFAULT_BLACK_HOLE_KEYS} from './black-hole-keys.js';
import {GraphIndex,demoWorkgraph} from './black-hole-graph.js';
import {FormState,ModalStack} from './black-hole-controls.js';
/** Black Hole v0.7 application state. Kinetic remains the compatibility base.
 * New state uses explicit motion time; typed data bypasses decorative clocks. */
export const BLACK_HOLE_SCENES = [
    { id: 'black-hole', name: 'BLACK HOLE / lensing observatory' }, { id: 'warp', name: 'OBLIQUE STARFIELD / continuous world' },
    { id: 'infinite', name: 'INFINITE / chromatic transit' }, { id: 'fleet-room', name: 'FLEET ROOM / luminous prompt + glass' },
    { id: 'graph-explorer', name: 'WORKGRAPH / metadata constellation' }, { id: 'git-history', name: 'GIT / typed history model' },
    { id: 'world-weather', name: 'WEATHER / ripples, shell, fireworks' }, { id: 'waterfall', name: 'WATERFALL / flow gate' },
    { id: 'ocean', name: 'OCEAN / moonlit caustics' }, { id: 'tarmac', name: 'TARMAC / speed corridor' },
    { id: 'dunes', name: 'DUNES / river, mountain and sky' }, { id: 'impossible', name: 'IMPOSSIBLE / folded tesseract' },
    { id: 'forms', name: 'CONTROL ROOM / semantic inputs' }, { id: 'dashboard', name: 'TEN FOOT / segmented signal' },
    { id: 'code-review', name: 'REVIEW / source, diff, hex' },
    ...KINETIC_SCENES.filter(s => s.id !== 'warp')
];
export const BLACK_HOLE_CONTROLS = {
    skyRadius: { label: 'Star visibility radius', min: 80, max: 360, step: 10, default: 280, unit: 'world units' },
    skyExposure: { label: 'Starlight exposure', min: 100, max: 30000, step: 100, default: 6500, unit: 'art exposure' },
    skyDensity: { label: 'Stars per fixed sector', min: 1, max: 18, step: 1, default: 9, unit: 'stars' },
    worldSeed: { label: 'World seed', min: 0, max: 4294967295, step: 1, default: 2030, unit: 'integer' },
    particleCount: { label: 'Particles per event', min: 16, max: 1000, step: 16, default: 256, unit: 'points' },
    eventDepth: { label: 'Weather placement depth', min: 8, max: 160, step: 1, default: 48, unit: 'world units' },
    eventLifeMs: { label: 'World event lifetime', min: 400, max: 12000, step: 100, default: 5400, unit: 'ms' },
    eventScale: { label: 'World event scale', min: .1, max: 4, step: .1, default: 1, unit: 'multiplier' },
    rippleRings: { label: 'Ripple wavefronts', min: 1, max: 5, step: 1, default: 3, unit: 'rings' },
    rippleSpeed: { label: 'Ripple propagation', min: 1, max: 20, step: .5, default: 7, unit: 'units/s' },
    rippleWidth: { label: 'Ripple softness', min: .2, max: 6, step: .1, default: 1.4, unit: 'units' },
    rippleGain: { label: 'Ripple background color', min: 0, max: 1, step: .05, default: .65, unit: 'blend' },
    flightSpeed: { label: 'Signed flight velocity', min: -40, max: 40, step: .5, default: 8, unit: 'units/s' },
    orbitPeriod: { label: 'Orbit period', min: 2, max: 180, step: 1, default: 35, unit: 'seconds' },
    orbitRadius: { label: 'Orbit target distance', min: 3, max: 200, step: 1, default: 60, unit: 'units' },
    orbitRadialRate: { label: 'Escape / falling rate', min: 0, max: 15, step: .5, default: 3, unit: 'units/s' },
    turnAngle: { label: 'Turn angle', min: -180, max: 180, step: 5, default: -90, unit: 'degrees' },
    turnSeconds: { label: 'Manoeuvre duration', min: 1, max: 120, step: 1, default: 45, unit: 'seconds' },
    bankAngle: { label: 'Coordinated bank', min: 0, max: 65, step: 1, default: 28, unit: 'degrees' },
    lensStrength: { label: 'Black-hole lensing', min: 0, max: 3, step: .05, default: 1.15, unit: 'artistic' },
    discTilt: { label: 'Accretion disc inclination', min: 5, max: 85, step: 1, default: 70, unit: 'degrees' },
    waterFlow: { label: 'Waterfall flow gate', min: 0, max: 2, step: .05, default: 1, unit: '0 = off' },
    landscapeSpeed: { label: 'Surface travel', min: 0, max: 160, step: 1, default: 100, unit: 'mph / tarmac' },
    terrainHeight: { label: 'Terrain / ocean amplitude', min: .1, max: 3, step: .1, default: 1, unit: 'multiplier' },
    promptSpeedFalloff: { label: 'Prompt band speed falloff', min: .05, max: 1, step: .05, default: .5, unit: 'per row' },
    promptColorFalloff: { label: 'Prompt band color falloff', min: .05, max: 1, step: .05, default: .68, unit: 'per row' },
    nodeDepthFade: { label: 'Graph distance attenuation', min: 0, max: .05, step: .001, default: .01, unit: 'per unit' },
    nodeScale: { label: 'Graph projected label scale', min: .5, max: 2, step: .1, default: 1, unit: 'multiplier' },
    segmentValue: { label: 'Dashboard authoritative value', min: 0, max: 100, step: 1, default: 67, unit: 'percent' },
    modalOpacity: { label: 'Overlay background opacity', min: 0, max: 1, step: .05, default: .9, unit: 'blend' },
};
export function validateBlackHoleOptions(input, base) {
    const out = base ? { ...base } : Object.fromEntries(Object.entries(BLACK_HOLE_CONTROLS).map(([k, v]) => [k, v.default]));
    for (const [k, v] of Object.entries(input)) {
        const spec = BLACK_HOLE_CONTROLS[k];
        if (!spec)
            throw new Error('Unknown Black Hole option ' + k);
        out[k] = finite(v, spec.min, spec.max, k);
        if (['worldSeed', 'skyDensity', 'particleCount', 'rippleRings'].includes(k) && !Number.isInteger(out[k]))
            throw new RangeError(k + ' must be integer');
    }
    return out;
}
export class BlackHoleModel extends KineticModel {
    constructor() {
        super();
        this.surfaceDistance = new EditableRateTimeline(100 * .44704);
        this.waterfallPhase = new EditableRateTimeline(1);
        this.bh = validateBlackHoleOptions({});
        this.flight = new FlightDirector(this.camera.snapshot());
        this.worldEvents = [];
        this.selectedWeather = 'ripples';
        this.weatherSpace = 'world';
        this.autoNovas = false;
        this.worldSerial = 0;
        this.lastAutoIndex = 0;
        this.lastRouteKey = '';
        this.lastSurfaceRate = 100;
        this.lastWaterRate = 1;
        this.richGraph = new GraphIndex(demoWorkgraph());
        this.graphColorField = 'type';
        this.graphFocus = '';
        this.graphFocusAt = 0;
        this.graphWas = '';
        this.keymap = new Keymap(DEFAULT_BLACK_HOLE_KEYS, 'browser');
        this.modalStack = new ModalStack();
        this.modalQuery = '';
        this.modalSelected = 0;
        this.modalContext = 'commands';
        this.modalNode = '';
        this.worldGroups = {};
        this.windowMode = 'summon';
        this.groupSelection = 'all';
        this.coordinated = true;
        this.visualRoutes = [];
        this.form = new FormState([{ id: 'name', kind: 'text', label: 'Fleet label', value: 'Black Hole laboratory', required: true }, { id: 'armed', kind: 'checkbox', label: 'Enable demonstration output', value: false }, { id: 'mode', kind: 'radio', label: 'Presentation', value: 'decorated', choices: ['simple', 'decorated'] }, { id: 'quality', kind: 'select', label: 'Motion budget', value: 'balanced', choices: ['quiet', 'balanced', 'spectacle'] }, { id: 'channels', kind: 'transfer', label: 'Selected instruments', value: ['signal', 'network'], choices: ['signal', 'network', 'power', 'heat', 'motion'] }, { id: 'notes', kind: 'textarea', label: 'Operator notes', value: 'No provider connected. Measurements are synthetic until explicitly attached.' }]);
        this.cameraTransition = null;
        this.configure({ novaRegularity: 0, novaStrength: .85, starDensity: .035, brightness: .22, sampling: 'half' });
        this.setScene('black-hole');
    }
    configure(patch) { super.configure(patch); if (this.flight && ['starSpeed', 'travelYaw', 'travelPitch'].some(k => k in patch)) {
        const c = this.camera.snapshot();
        this.flight.cruise(this.motionMs, c, this.options.starSpeed, { yaw: this.options.travelYaw, pitch: this.options.travelPitch });
        if (this.bh)
            this.bh.flightSpeed = this.options.starSpeed;
    } }
    configureBH(patch) { const next = validateBlackHoleOptions(patch, this.bh); if ('landscapeSpeed' in patch)
        this.surfaceDistance.set(this.motionMs, next.landscapeSpeed * .44704); if ('waterFlow' in patch)
        this.waterfallPhase.set(this.motionMs, next.waterFlow); this.bh = next; if ('flightSpeed' in patch)
        this.flight.cruise(this.motionMs, this.camera.snapshot(), next.flightSpeed, this.flight.travelHeading() ?? undefined); this.revision++; }
    effectiveBH() { const out = { ...this.bh }; for (const route of this.visualRoutes) {
        const source = this.bus.samples.get(route.source);
        if (!source || this.dataMs - source.atMs > route.ttlMs)
            continue;
        const u = clamp((source.value - route.inputMin) / (route.inputMax - route.inputMin), 0, 1), s = BLACK_HOLE_CONTROLS[route.target];
        out[route.target] = clamp(route.outputMin + (route.outputMax - route.outputMin) * u, s.min, s.max);
        if (['worldSeed', 'skyDensity', 'particleCount', 'rippleRings'].includes(route.target))
            out[route.target] = Math.round(out[route.target]);
    } return out; }
    bindVisual(route) { if (!route || !/^[\w.-]{1,64}$/.test(route.source) || !BLACK_HOLE_CONTROLS[route.target])
        throw new RangeError('Visual route source/target'); for (const k of ['inputMin', 'inputMax', 'outputMin', 'outputMax', 'ttlMs'])
        finite(route[k], k === 'ttlMs' ? 1 : -1e9, 1e9, k); if (route.inputMax <= route.inputMin)
        throw new RangeError('Input range must increase'); const next = this.visualRoutes.filter(r => r.target !== route.target); if (next.length >= 16)
        throw new RangeError('16 visual routes max'); this.visualRoutes = [...next, { ...route }]; }
    routeRates(atMs) { super.routeRates(atMs); if (!this.bh)
        return; const o = this.effectiveBH(), key = String(o.flightSpeed); if (this.visualRoutes.some(r => r.target === 'flightSpeed') && this.lastRouteKey !== key) {
        this.flight.cruise(this.motionMs, this.camera.snapshot(), o.flightSpeed);
        this.lastRouteKey = key;
    } if (o.landscapeSpeed !== this.lastSurfaceRate) {
        this.surfaceDistance.set(this.motionMs, o.landscapeSpeed * .44704);
        this.lastSurfaceRate = o.landscapeSpeed;
    } if (o.waterFlow !== this.lastWaterRate) {
        this.waterfallPhase.set(this.motionMs, o.waterFlow);
        this.lastWaterRate = o.waterFlow;
    } }
    setTime(ms) {
        const before = this.motionMs;
        super.setTime(ms);
        if (!this.flight)
            return;
        if (this.flight.mode !== 'manual') {
            const c = this.flight.sample(ms);
            this.camera.configure({ ...c, x: clamp(c.x, -100000, 100000), y: clamp(c.y, -100000, 100000), z: clamp(c.z, -100000, 100000), pitch: clamp(c.pitch, -89, 89) });
        }
        if (this.cameraTransition) {
            const a = this.cameraTransition, u = softStep(a.duration ? (ms - a.atMs) / a.duration : 1), v = {};
            for (const k of ['x', 'y', 'z', 'pitch', 'fov'])
                v[k] = a.from[k] + (a.to[k] - a.from[k]) * u;
            for (const k of ['yaw', 'roll'])
                v[k] = a.from[k] + (((a.to[k] - a.from[k] + 540) % 360) - 180) * u;
            this.camera.configure(v);
            if (u >= 1)
                this.cameraTransition = null;
        }
        if (this.weatherSpace === 'world' && this.autoNovas && this.options.novaRegularity > 0) {
            const period = 60000 / this.options.novaRegularity, k = Math.floor(ms / period);
            if (ms < before)
                this.lastAutoIndex = k;
            else {
                for (let i = Math.max(this.lastAutoIndex + 1, k - 2); i <= k; i++) {
                    const c = this.flight.mode === 'manual' ? this.camera.snapshot() : this.flight.sample(i * period), p = new Projector(c, this.width, this.height).unproject(this.width * (.15 + .7 * seededUnit(917, i)), this.height * (.2 + .5 * seededUnit(319, i)), this.bh.eventDepth);
                    this.addWorld('nova', p, i * period, i + 70000);
                }
                this.lastAutoIndex = k;
            }
        }
    }
    setAutomatic(enabled) { this.autoNovas = enabled; this.lastAutoIndex = Math.floor(this.motionMs / (60000 / Math.max(.01, this.options.novaRegularity))); if (enabled && this.options.novaRegularity === 0)
        super.configure({ novaRegularity: 3 }); this.revision++; }
    addWorld(kind, position, atMs = this.motionMs, seed) {
        if (!WORLD_WEATHER.includes(kind))
            throw new Error('Unknown world weather');
        for (const k of ['x', 'y', 'z'])
            finite(position?.[k], -100000, 100000, 'position.' + k);
        if (seed !== undefined)
            finite(seed, 0, 4294967295, 'event seed');
        finite(atMs, 0, Number.MAX_SAFE_INTEGER, 'event time');
        const id = ++this.worldSerial;
        this.worldEvents.push({ id, kind, position: { ...position }, atMs, seed: seed ?? this.bh.worldSeed + id * 997, lifeMs: this.bh.eventLifeMs, scale: this.bh.eventScale, ripple: Object.freeze({ speed: this.bh.rippleSpeed, width: this.bh.rippleWidth, rings: this.bh.rippleRings, gain: this.bh.rippleGain, intensity: this.options.weatherIntensity }) });
        if (this.worldEvents.length > SKY_LIMITS.maxEvents)
            this.worldEvents.shift();
        this.revision++;
    }
    emit(x, y, glyph = '·', kind) { if (!this.bh || this.weatherSpace === 'screen') {
        super.emit(x, y, glyph, kind === 'firework' ? 'nova' : kind === 'leaves' ? 'snow' : kind);
        return;
    } const k = (kind ?? this.selectedWeather); const p = new Projector(this.camera.snapshot(), this.width, this.height).unproject(x, y, this.bh.eventDepth); this.addWorld(WORLD_WEATHER.includes(k) ? k : 'ripples', p); }
    setScene(id) {
        if (!BLACK_HOLE_SCENES.some(s => s.id === id))
            throw new Error('Unknown scene');
        this.cameraTransition = null;
        if (this.flight)
            this.flight.anchor(this.camera.snapshot());
        if (KINETIC_SCENES.some(s => s.id === id))
            super.setScene(id);
        else {
            this.scene = id;
            this.selected = 0;
            this.scroll = 0;
            this.camera.reset();
            this.camera.configure({ z: 0, mode: 'fly' });
            this.navEnabled = true;
        }
        this.worldEvents = [];
        if (this.modalStack)
            this.modalStack.clear();
        if (['warp', 'black-hole', 'infinite', 'world-weather'].includes(id)) {
            this.camera.configure({ x: 0, y: 0, z: 0, yaw: id === 'warp' ? 20 : 0, pitch: id === 'warp' ? 8 : 0, roll: id === 'warp' ? 10 : 0, mode: 'fly' });
            if (this.flight) {
                this.flight.anchor(this.camera.snapshot());
                if (id === 'warp')
                    this.flight.cruise(this.motionMs, this.camera.snapshot(), this.bh.flightSpeed);
            }
        }
        if (['graph-explorer', 'git-history'].includes(id)) {
            this.graph = this.richGraph.graph;
            this.startLayout(this.graph, { mode: this.layoutOptions.mode });
            if (!this.layoutJob)
                this.fitCamera();
        }
        if (id === 'fleet-room') {
            this.camera.configure({ x: 0, y: 0, z: -65, mode: 'orbit' });
            this.camera.target = { x: 0, y: 0, z: 0 };
        }
        this.notice = (BLACK_HOLE_SCENES.find(s => s.id === id)?.name ?? id) + ' / v0.7.0';
        this.revision++;
    }
    fitCamera() { if (['graph-explorer', 'git-history'].includes(this.scene))
        this.camera.fit(this.layout.nodes, this.width, this.height - 12);
    else
        super.fitCamera(); }
    pilot(action) { this.flight.anchor(this.camera.snapshot()); this.cameraTransition = null; if (action === 'stop') {
        this.bh.flightSpeed = 0;
        super.configure({ starSpeed: 0 });
    }
    else if (action === 'faster' || action === 'slower') {
        this.bh.flightSpeed = clamp(this.bh.flightSpeed + (action === 'faster' ? 1 : -1), -40, 40);
        this.flight.cruise(this.motionMs, this.camera.snapshot(), this.bh.flightSpeed);
    }
    else if (action === 'align')
        this.flight.cruise(this.motionMs, this.camera.snapshot(), this.bh.flightSpeed);
    else
        super.navigate(action); this.revision++; }
    navigate(action) { if (this.flight)
        this.pilot(action);
    else
        super.navigate(action); }
    startManeuver(kind) { this.flight.plan(this.motionMs, this.camera.snapshot(), [{ kind, seconds: this.bh.turnSeconds, degrees: kind === 'turn' || kind === 'roll' ? this.bh.turnAngle : Math.min(35, Math.abs(this.bh.turnAngle)), speed: this.bh.flightSpeed, coordinated: this.coordinated, bank: this.bh.bankAngle }]); this.notice = 'Scripted ' + kind + ' / ' + this.bh.turnSeconds + ' seconds'; }
    startOrbit(mode) { const c = this.camera.snapshot(), b = cameraBasis(c), r = this.bh.orbitRadius, target = { x: c.x + b.forward.x * r, y: c.y + b.forward.y * r, z: c.z + b.forward.z * r }; this.camera.target = target; this.flight.orbit(this.motionMs, c, target, { mode, periodSeconds: this.bh.orbitPeriod, radialRate: this.bh.orbitRadialRate, bank: this.coordinated ? this.bh.bankAngle : 0 }); this.notice = mode + ' orbit / target is ahead of the current camera'; }
    runScript(commands) { this.flight.plan(this.motionMs, this.camera.snapshot(), commands); this.notice = 'Flight script accepted / ' + commands.length + ' manoeuvres'; }
    loadGraph(input) { const next = new GraphIndex(input); this.startLayout(next.graph); this.richGraph = next; this.graphFocus = ''; this.graphWas = ''; this.revision++; }
    selectGraph(id) { this.richGraph.node(id); this.graphWas = this.graphFocus; this.graphFocus = id; this.graphSelection = id; this.graphFocusAt = this.motionMs; this.modalNode = id; this.modalContext = 'node'; this.modalStack.clear(); this.modalStack.push({ id: 'node', kind: 'drawer-right', title: this.richGraph.node(id).label ?? id, body: 'Inspect graph relationships', atMs: this.motionMs, dismissible: true }); this.revision++; }
    openModal(kind = 'center', context = 'commands') { this.modalContext = context; this.modalQuery = ''; this.modalSelected = 0; this.modalStack.push({ id: 'modal-' + this.revision, kind, title: context === 'windows' ? 'WINDOW SWITCHER' : context === 'commands' ? 'COMMANDS & SHORTCUTS' : 'INTERFACE / ' + kind.toUpperCase(), body: 'Every action also has a visible control. Escape dismisses one layer.', atMs: this.motionMs, dismissible: true }); this.revision++; }
    /** Gather preserves identities and data; restore intentionally recovers hidden surfaces. */
    gatherWindows(ids = this.spaceWindows.list().map(w => w.id)) {
        const c = this.camera.snapshot(), b = cameraBasis(c), orientation = this.frontAngles(c);
        ids.forEach((id, i) => { const col = (i % 3) - (Math.min(3, ids.length) - 1) / 2, row = Math.floor(i / 3); this.spaceWindows.move(id, { x: c.x + b.forward.x * 65 + b.right.x * col * 35 - b.up.x * row * 23, y: c.y + b.forward.y * 65 + b.right.y * col * 35 - b.up.y * row * 23, z: c.z + b.forward.z * 65 + b.right.z * col * 35 - b.up.z * row * 23, ...orientation }); this.spaceWindows.act(id, 'restore', this.motionMs); });
        this.notice = 'Gathered ' + ids.length + ' windows, front aligned';
        this.revision++;
    }
    groupWindows(name, ids) { if (!/^[\w.-]{1,64}$/.test(name) || new Set(ids).size !== ids.length || ids.some(id => !this.spaceWindows.list().some(w => w.id === id)))
        throw new RangeError('Group identities'); this.worldGroups[name] = [...ids]; }
    frontAngles(c) { const b = cameraBasis(c), d = 180 / Math.PI; return { pitch: Math.asin(clamp(b.up.z, -1, 1)) * d, yaw: Math.atan2(-b.right.z, b.forward.z) * d, roll: Math.atan2(-b.up.x, b.up.y) * d }; }
    focusWindow(id, mode = this.windowMode) {
        const w = this.spaceWindows.list().find(x => x.id === id);
        if (!w)
            throw new Error('Unknown window');
        this.flight.anchor(this.camera.snapshot());
        this.spaceWindows.act(id, 'restore', this.motionMs);
        this.spaceWindows.select(id);
        const c = this.camera.snapshot();
        if (mode === 'summon') {
            const b = cameraBasis(c);
            this.spaceWindows.move(id, { x: c.x + b.forward.x * 40, y: c.y + b.forward.y * 40, z: c.z + b.forward.z * 40, ...this.frontAngles(c) });
        }
        else {
            const y = w.yaw * Math.PI / 180, p = w.pitch * Math.PI / 180, r = w.roll * Math.PI / 180, normal = { x: Math.sin(y) * Math.cos(r) + Math.cos(y) * Math.sin(p) * Math.sin(r), y: Math.sin(y) * Math.sin(r) - Math.cos(y) * Math.sin(p) * Math.cos(r), z: Math.cos(y) * Math.cos(p) };
            const yaw = Math.atan2(normal.x, normal.z) * 180 / Math.PI, pitch = Math.asin(clamp(normal.y, -1, 1)) * 180 / Math.PI;
            const right = { x: Math.cos(y) * Math.cos(r) - Math.sin(y) * Math.sin(p) * Math.sin(r), y: Math.cos(y) * Math.sin(r) + Math.sin(y) * Math.sin(p) * Math.cos(r), z: -Math.sin(y) * Math.cos(p) }, basis = cameraBasis({ yaw, pitch, roll: 0 }), roll = Math.atan2(right.x * basis.up.x + right.y * basis.up.y + right.z * basis.up.z, right.x * basis.right.x + right.y * basis.right.y + right.z * basis.right.z) * 180 / Math.PI;
            const to = { ...c, x: w.x - normal.x * 42, y: w.y - normal.y * 42, z: w.z - normal.z * 42, yaw, pitch, roll };
            this.cameraTransition = { atMs: this.motionMs, from: c, to, duration: this.options.motion ? 650 : 0 };
            this.setTime(this.motionMs);
        }
        this.modalStack.clear();
        this.notice = mode + ' ' + id;
        this.revision++;
    }
    newWindow() { let n = 1; while (this.spaceWindows.list().some(w => w.id === 'window-' + n))
        n++; const c = this.camera.snapshot(), b = cameraBasis(c); this.spaceWindows.add({ id: 'window-' + n, title: 'WINDOW ' + n, content: 'Application-owned content\nA new independent surface.', x: c.x + b.forward.x * 42, y: c.y + b.forward.y * 42, z: c.z + b.forward.z * 42, ...this.frontAngles(c) }); this.spaceWindows.select('window-' + n); this.revision++; }
}

