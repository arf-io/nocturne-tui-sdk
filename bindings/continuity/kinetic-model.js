import {clamp,finite,rgb,OBSERVATORY_SCENES,ObservatoryModel} from './observatory.js';
import {DEFAULT_LAYOUT_OPTIONS,validateGraph,LayoutJob} from './graph-layout.js';
import {CameraRig,EditableRateTimeline,VectorTravel} from './kinetic-camera.js';
import {TEXT_HIDES,DEFAULT_TEXT_OPTIONS,validateTextOptions,TextActor} from './kinetic-text.js';
import {DEFAULT_PARTICLE_OPTIONS,validateParticleOptions} from './kinetic-particles.js';
import {WindowManager} from './kinetic-windows.js';
/** Kinetic application state: camera, graph jobs, text choreography, spatial windows.
 * Mutations happen on input/data events. Rendering only samples this state. */
export const KINETIC_SCENES = [...OBSERVATORY_SCENES.map(s => ({ ...s, name: s.id === 'warp' ? 'OBLIQUE HYPERLANE / flight deck' : s.id === 'dag' ? 'GRAPH / automatic 2D + 3D' : s.id === 'windows' ? 'WINDOW THEATRE / spatial glass' : s.id === 'text' ? 'TEXT / reveal and disappear' : s.name })), { id: 'weather-lab', name: 'WEATHER / arcs, ejecta & embers' }, { id: 'shapes', name: 'SHAPES / beyond the rectangle' }];
export const DEFAULT_KINETIC_GRAPH = { nodes: [{ id: 'operator', label: 'OPERATOR' }, { id: 'planner', label: 'PLANNER' }, { id: 'research', label: 'RESEARCH' }, { id: 'memory', label: 'MEMORY' }, { id: 'tools', label: 'TOOLS' }, { id: 'evidence', label: 'EVIDENCE' }, { id: 'synthesis', label: 'SYNTHESIS' }, { id: 'archive', label: 'ARCHIVE' }, { id: 'review', label: 'REVIEW' }, { id: 'release', label: 'RELEASE' }, { id: 'witness', label: 'WITNESS' }, { id: 'metrics', label: 'METRICS' }], edges: [['operator', 'planner'], ['operator', 'research'], ['planner', 'memory'], ['planner', 'tools'], ['research', 'tools'], ['research', 'evidence'], ['memory', 'synthesis'], ['tools', 'synthesis'], ['evidence', 'synthesis'], ['synthesis', 'review'], ['review', 'release'], ['synthesis', 'archive'], ['archive', 'witness'], ['review', 'witness'], ['release', 'metrics']].map(([source, target]) => ({ source, target })) };
export class KineticModel extends ObservatoryModel {
    constructor() {
        super();
        this.travel = new EditableRateTimeline(.06);
        this.warpTravel = new EditableRateTimeline(5);
        this.orbit = new EditableRateTimeline(4);
        this.orbit2 = new EditableRateTimeline(2);
        this.camera = new CameraRig();
        this.vectorTravel = new VectorTravel();
        this.spaceWindows = new WindowManager();
        this.graph = validateGraph(DEFAULT_KINETIC_GRAPH);
        this.layoutOptions = { ...DEFAULT_LAYOUT_OPTIONS, nodeGap: 14, layerGap: 17, depthGap: 4, orientation: 'LR' };
        this.layoutJob = null;
        this.layoutVersion = 0;
        this.layoutFitOnCommit = true;
        this.graphSelection = 'operator';
        this.navEnabled = true;
        this.particles = { ...DEFAULT_PARTICLE_OPTIONS };
        this.textOptions = { ...DEFAULT_TEXT_OPTIONS, effect: 'rain', durationMs: 1000, staggerMs: 28, jitterMs: 450 };
        this.hideEffect = 'ash';
        this.textSource = 'EVERY LETTER HAS A WAY HOME';
        this.textAtMs = 0;
        this.textPhase = 'reveal';
        this.activeAction = '';
        this.flightKey = '';
        this.configure({ novaStrength: .85, weatherIntensity: .65 });
        const j = new LayoutJob(this.graph, this.layoutOptions);
        while (!j.done)
            j.step(32);
        this.layout = j.result();
        this.textActor = new TextActor(this.textSource, this.textOptions);
        this.textActor.show(0);
        this.vectorTravel.set(0, this.options.starSpeed, this.options.travelYaw, this.options.travelPitch);
        this.spaceWindows.add({ id: 'pearl', title: 'PEARL / signal laboratory', x: -16, y: 0, z: 0, width: 34, height: 18, content: 'SIGNAL IS A MATERIAL\n\n128 samples / live source\nLayers retain their data\nwhile their surfaces move.' });
        this.spaceWindows.add({ id: 'atlas', title: 'ATLAS / flight notebook', x: 18, y: -2, z: 9, width: 31, height: 20, yaw: -10, content: 'TOPOLOGY WITHOUT DUPLICATES\n\nPlanner + research\nshare tools and synthesis.\n\nA window is a place,\nnot a rectangle.' });
        this.spaceWindows.add({ id: 'iris', title: 'IRIS / material inspector', x: 0, y: -12, z: 17, width: 37, height: 17, roll: 3, content: 'OPEN / CLOSE / TRANSFORM\n\nChoose an effect, shape,\nchrome profile or depth.\nThe dock remembers all.' });
    }
    configure(patch) {
        super.configure(patch);
        if (this.vectorTravel && ['starSpeed', 'travelYaw', 'travelPitch'].some(k => k in patch)) {
            this.vectorTravel.set(this.motionMs, this.options.starSpeed, this.options.travelYaw, this.options.travelPitch);
            this.flightKey = '';
        }
        if (this.camera) {
            const map = { cameraX: 'x', cameraY: 'y', cameraZ: 'z', cameraYaw: 'yaw', cameraPitch: 'pitch', cameraRoll: 'roll', fov: 'fov' }, cp = {};
            for (const [k, d] of Object.entries(map))
                if (k in patch)
                    cp[d] = this.options[k];
            if (Object.keys(cp).length)
                this.camera.configure(cp);
        }
        if (this.layout && 'flatNavigation' in patch && ['dag', 'spatial-menu'].includes(this.scene)) {
            const mode = this.layoutOptions.mode.replace(/-[23]d$/, this.options.flatNavigation ? '-2d' : '-3d');
            this.startLayout(this.graph, { mode });
        }
    }
    routeRates(atMs) {
        super.routeRates(atMs);
        if (!this.vectorTravel)
            return;
        const o = this.effective(atMs), key = [o.starSpeed, o.travelYaw, o.travelPitch].join(':');
        if (key !== this.flightKey) {
            this.vectorTravel.set(this.motionMs, o.starSpeed, o.travelYaw, o.travelPitch);
            this.flightKey = key;
        }
        const map = { cameraX: 'x', cameraY: 'y', cameraZ: 'z', cameraYaw: 'yaw', cameraPitch: 'pitch', cameraRoll: 'roll', fov: 'fov' }, cp = {};
        for (const b of this.bus.bindings)
            if (map[b.target])
                cp[map[b.target]] = o[b.target];
        if (Object.keys(cp).length)
            this.camera.configure(cp);
    }
    setScene(scene) {
        if (!KINETIC_SCENES.some(s => s.id === scene))
            throw new Error('Unknown Kinetic scene');
        this.scene = scene;
        this.selected = 0;
        this.scroll = 0;
        this.navEnabled = ['warp', 'dag', 'spatial-menu', 'windows', 'shapes'].includes(scene);
        this.notice = KINETIC_SCENES.find(s => s.id === scene).name + ' / v0.5';
        if (scene === 'warp') {
            this.camera.reset();
            this.camera.configure({ z: 0, mode: 'fly' });
        }
        else if (['dag', 'spatial-menu'].includes(scene)) {
            this.camera.reset();
            this.camera.view(this.layoutOptions.mode.endsWith('2d') ? 'front' : 'iso');
            this.fitCamera();
        }
        else if (['windows', 'shapes'].includes(scene)) {
            if (scene === 'shapes')
                this.spaceWindows.list().forEach((w, i) => { if (!w.shape)
                    this.spaceWindows.setShape(w.id, ['ellipse', 'hexagon', 'diamond'][i % 3]); });
            this.camera.reset();
            this.camera.configure({ z: -62, fov: 67 });
        }
        if (scene === 'text')
            this.replayText('reveal');
        this.revision++;
    }
    fitCamera() {
        if (['dag', 'spatial-menu'].includes(this.scene)) {
            const points = this.layout.nodes.flatMap(n => [{ x: n.x - n.width, y: n.y - n.height, z: n.z }, { x: n.x + n.width, y: n.y + n.height, z: n.z }]);
            this.camera.fit(points, this.width, Math.max(12, this.height - 14));
        }
        else if (['windows', 'shapes'].includes(this.scene)) {
            this.camera.fit(this.spaceWindows.list().flatMap(w => [{ x: w.x - w.width / 2, y: w.y - w.height / 2, z: w.z }, { x: w.x + w.width / 2, y: w.y + w.height / 2, z: w.z }]), this.width, this.height - 14);
        }
        else {
            this.camera.reset();
            this.camera.configure({ z: 0, mode: 'fly' });
        }
    }
    /** Start a bounded solve. Host yields between stepLayout calls; stale jobs cancel. */
    startLayout(graph = this.graph, patch = {}) {
        const owned = validateGraph(graph), job = new LayoutJob(owned, { ...this.layoutOptions, ...patch });
        this.layoutJob?.cancel();
        this.graph = owned;
        this.layoutOptions = { ...job.options };
        this.layoutJob = job;
        this.layoutFitOnCommit = true;
        this.layoutVersion++;
        if (job.done)
            this.commitLayout();
        return this.layoutVersion;
    }
    stepLayout(iterations = 8) { if (!this.layoutJob)
        return true; this.layoutJob.step(iterations); if (this.layoutJob.done)
        this.commitLayout(); return !this.layoutJob; }
    commitLayout() { if (!this.layoutJob)
        return; this.layout = this.layoutJob.result(); this.layoutJob = null; if (!this.graph.nodes.some(n => n.id === this.graphSelection))
        this.graphSelection = this.graph.nodes[0]?.id ?? ''; if (this.layoutFitOnCommit)
        this.fitCamera(); this.notice = `${this.layoutOptions.mode} / ${this.layout.nodes.length} nodes / ${this.layout.edges.length} edges / ${this.layout.cycles.length} cyclic groups`; this.revision++; }
    pinSelected(pin) { const n = this.layout.nodes.find(n => n.id === this.graphSelection); if (!n)
        return; const g = JSON.parse(JSON.stringify(this.graph)); const node = g.nodes.find((x) => x.id === n.id); if (pin)
        node.pin = { x: n.x, y: n.y, z: n.z };
    else
        delete node.pin; this.startLayout(g); }
    configureParticles(patch) { this.particles = validateParticleOptions({ ...this.particles, ...patch }); this.revision++; }
    configureText(patch) { this.textOptions = validateTextOptions({ ...this.textOptions, ...patch }); this.replayText(this.textPhase); }
    setText(text) { const actor = new TextActor(text, this.textOptions); this.textSource = text; this.textActor = actor; this.textAtMs = this.motionMs; this.textPhase = 'reveal'; actor.show(this.motionMs); this.revision++; }
    replayText(phase) { this.textPhase = phase; this.textAtMs = this.motionMs; if (phase === 'reveal')
        this.textActor.show(this.motionMs, this.textOptions);
    else
        this.textActor.hide(this.motionMs, { ...this.textOptions, effect: this.hideEffect, phase: 'hide' }); this.revision++; }
    hardReplayText() { this.textActor = new TextActor(this.textSource, this.textOptions); this.textPhase = 'reveal'; this.textAtMs = this.motionMs; this.textActor.show(this.motionMs); this.revision++; }
    /** Input navigation uses explicit user deltas, even with decorative motion held. */
    navigate(action) {
        const c = this.camera.snapshot(), d = c.moveSpeed * .15;
        if (action === 'fit')
            this.fitCamera();
        else if (action === 'reset') {
            this.camera.reset();
            if (this.scene === 'warp')
                this.camera.configure({ z: 0, mode: 'fly' });
        }
        else if (action.startsWith('view:'))
            this.camera.view(action.slice(5));
        else if (action === 'left')
            this.camera.moveLocal(-d, 0, 0);
        else if (action === 'right')
            this.camera.moveLocal(d, 0, 0);
        else if (action === 'up')
            this.camera.moveLocal(0, d, 0);
        else if (action === 'down')
            this.camera.moveLocal(0, -d, 0);
        else if (action === 'forward')
            this.camera.dolly(d);
        else if (action === 'back')
            this.camera.dolly(-d);
        else if (action === 'yaw-left')
            this.camera.rotate(-5, 0);
        else if (action === 'yaw-right')
            this.camera.rotate(5, 0);
        else if (action === 'pitch-up')
            this.camera.rotate(0, 5);
        else if (action === 'pitch-down')
            this.camera.rotate(0, -5);
        else if (action === 'roll-left')
            this.camera.configure({ roll: c.roll - 5 });
        else if (action === 'roll-right')
            this.camera.configure({ roll: c.roll + 5 });
        else if (action === 'stop')
            this.configure({ starSpeed: 0 });
        else if (action === 'faster')
            this.configure({ starSpeed: clamp(this.options.starSpeed + 1, 0, 40) });
        else if (action === 'slower')
            this.configure({ starSpeed: clamp(this.options.starSpeed - 1, 0, 40) });
        else if (action === 'align')
            this.configure({ travelYaw: c.yaw, travelPitch: c.pitch });
        else
            throw new Error('Unknown navigation action');
        this.revision++;
    }
    windowAction(id, action) { this.spaceWindows.act(id, action, this.motionMs); this.notice = `${id}: ${action} / every window remains in the dock`; this.revision++; }
    exportState() { return { ...super.exportState(), kinetic: { version: 5, camera: this.camera.snapshot(), cameraTarget: { ...this.camera.target }, graph: this.graph, layoutOptions: this.layoutOptions, layout: this.layout, particles: { ...this.particles }, text: { source: this.textSource, options: this.textOptions, hideEffect: this.hideEffect }, windows: { options: this.spaceWindows.options, items: this.spaceWindows.list() } } }; }
}
/** Export a complete versioned visual configuration. Contains window content,
 * but no messages, credentials, captured sensor data, or executable code.
 * Source text and JSON must be stored with the privacy policy of the host.
 */
export function exportKineticConfiguration(model) {
    const k = model.exportState().kinetic;
    delete k.layout;
    return JSON.parse(JSON.stringify({ version: 5, scene: model.scene, options: model.options, palette: model.palette, routes: model.bus.bindings, kinetic: { ...k, selectedWindow: model.spaceWindows.selected } }));
}
/** Validate a full recipe before commit. Old v4 theme imports remain supported.
 * Layout solving is scheduled, not performed inside the render loop. Imported
 * camera pose is restored after a pending graph solve only when fit is requested
 * explicitly. Local drafts, messages and external samples are never replaced.
 * Throws on malformed/oversized values. Examples: docs/kinetic/API.md.
 */
export function applyKineticConfiguration(model, input) {
    if (!input || typeof input !== 'object' || Array.isArray(input))
        throw new Error('Configuration object required');
    // Serialization here bounds recursion, rejects cycles, and strips prototypes.
    const serialized = JSON.stringify(input);
    if (serialized.length > 1048576)
        throw new Error('Configuration exceeds 1 MiB');
    const c = JSON.parse(serialized), candidate = new KineticModel();
    if (c.version !== undefined && ![4, 5].includes(c.version))
        throw new Error('Unknown configuration version');
    candidate.configure(c.options ?? c);
    if (c.palette) {
        const p = c.palette;
        if (typeof p.id !== 'string' || p.id.length > 64 || typeof p.name !== 'string' || p.name.length > 160 || !Array.isArray(p.colors) || p.colors.length < 1 || p.colors.length > 32)
            throw new Error('Invalid palette');
        p.colors.forEach(rgb);
        rgb(p.background);
        rgb(p.ink);
        candidate.palette = { id: p.id, name: p.name, colors: [...p.colors], background: p.background, ink: p.ink };
    }
    else
        candidate.palette = JSON.parse(JSON.stringify(model.palette));
    const k = c.kinetic;
    if (k) {
        if (k.version !== 5)
            throw new Error('Kinetic configuration version required');
        candidate.setScene(c.scene ?? model.scene);
        candidate.camera.configure(k.camera);
        if (k.cameraTarget) {
            for (const v of Object.values(k.cameraTarget))
                finite(v, -10000, 10000, 'camera target');
            if (['x', 'y', 'z'].some(x => typeof k.cameraTarget[x] !== 'number'))
                throw new Error('Three target coordinates required');
            candidate.camera.target = { x: k.cameraTarget.x, y: k.cameraTarget.y, z: k.cameraTarget.z };
        }
        candidate.graph = validateGraph(k.graph);
        const job = new LayoutJob(candidate.graph, k.layoutOptions);
        candidate.layoutOptions = { ...job.options };
        candidate.configureParticles(k.particles);
        candidate.configureText(k.text.options);
        if (!TEXT_HIDES.includes(k.text.hideEffect))
            throw new Error('Unknown hide effect');
        candidate.hideEffect = k.text.hideEffect;
        candidate.setText(k.text.source);
        const wm = new WindowManager();
        wm.configure(k.windows.options);
        if (!Array.isArray(k.windows.items) || k.windows.items.length < 1 || k.windows.items.length > 32)
            throw new Error('One to 32 windows required');
        for (const w of k.windows.items) {
            wm.add(w);
            if (!['normal', 'maximized', 'minimized', 'closed', 'rolled'].includes(w.state))
                throw new Error('Unknown window state');
            if (w.state !== 'normal') {
                const ms = wm.options.durationMs;
                wm.configure({ durationMs: 0 });
                wm.act(w.id, { maximized: 'maximize', minimized: 'minimize', closed: 'close', rolled: 'roll' }[w.state], 0);
                wm.configure({ durationMs: ms });
            }
        }
        if (k.selectedWindow)
            wm.select(k.selectedWindow);
        candidate.spaceWindows = wm;
    }
    if (c.routes) {
        if (!Array.isArray(c.routes) || c.routes.length > 16)
            throw new Error('At most 16 routes');
        for (const b of c.routes)
            candidate.bus.bind(b);
    }
    // Every operation that can fail has now been checked on an isolated candidate.
    for (const t of [model.travel, model.orbit, model.orbit2, model.warpTravel])
        t.at(model.motionMs);
    model.configure(candidate.options);
    model.palette = candidate.palette;
    if (k) {
        model.setScene(candidate.scene);
        model.camera.configure(candidate.camera.snapshot());
        model.camera.target = { ...candidate.camera.target };
        model.particles = candidate.particles;
        model.textOptions = candidate.textOptions;
        model.hideEffect = candidate.hideEffect;
        model.setText(candidate.textSource);
        model.spaceWindows = candidate.spaceWindows;
        model.startLayout(candidate.graph, candidate.layoutOptions);
        model.layoutFitOnCommit = false;
        model.camera.configure(candidate.camera.snapshot());
        model.camera.target = { ...candidate.camera.target };
    }
    if (c.routes) {
        for (const b of [...model.bus.bindings])
            model.bus.unbind(b.target);
        for (const b of candidate.bus.bindings)
            model.bus.bind(b);
    }
    model.revision++;
}

