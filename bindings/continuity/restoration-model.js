import {clamp,finite,hex} from './observatory.js';
import {AtelierTextPlayer} from './atelier-text.js';
import {signedWheel,viewDisplacement,textInsertions,draftView,DispatchGate} from './continuity-input.js';
import {parseOBJ} from './mesh-obj.js';
import {EffectShelf} from './effect-catalog.js';
import {Projector} from './black-hole-space.js';
import {GraphIndex} from './black-hole-graph.js';
import {BLACK_HOLE_SCENES,BlackHoleModel} from './black-hole-model.js';
import {graphTargets,graphWorldPositions,graphRecordHash} from './restoration-graph.js';
/** Restoration controller: additive discoverability, not another replacement of
 * old effects. High-level model uses the existing TypeScript core. */
export const SCENIC_WORLD = { waterfall: 0, tarmac: 1, 'black-hole': 2, ocean: 3, dunes: 4 };
const RESTORED_NAMES = { waterfall: 'PEARL CASCADE / spatial water & basalt', tarmac: 'COPPER CAUSEWAY / suspended roadway', 'black-hole': 'RED SHIFT / orbital accretion', ocean: 'TIDAL GLASS / wave geometry', dunes: 'SILT / cut terrain & river' };
export const RESTORATION_SCENES = BLACK_HOLE_SCENES.map(s => ({ ...s, name: RESTORED_NAMES[s.id] ?? s.name })).concat([{ id: "model-viewer", name: "ORBITAL WORKSHOP / import a 3D object", description: "Original polygon models, native cell depth buffer" }]);
export class RestorationModel extends BlackHoleModel {
    replayAtelier(phase, patch = {}) {
        this.atelierPlayer.configure(patch);
        this.atelierTextEnabled = true;
        if (phase === 'show')
            this.atelierPlayer.show(this.motionMs);
        else
            this.atelierPlayer.hide(this.motionMs);
        this.revision++;
    }
    replayText(phase) {
        if (this.atelierTextEnabled)
            this.replayAtelier(phase === 'reveal' ? 'show' : 'hide');
        else
            super.replayText(phase);
    }
    hardReplayText() {
        if (this.atelierTextEnabled) {
            this.atelierPlayer = new AtelierTextPlayer(this.textSource.slice(0, 2048), this.atelierPlayer.options);
            this.atelierPlayer.show(this.motionMs);
        }
        else
            super.hardReplayText();
    }
    setText(text) {
        super.setText(text);
        if (this.atelierPlayer) {
            this.atelierPlayer = new AtelierTextPlayer(text.slice(0, 2048), this.atelierPlayer.options);
            this.atelierPlayer.show(this.motionMs);
        }
    }
    playEffect(id = this.selectedEffect, space = this.effectSpace, x = this.width * .5, y = this.height * .46) { const e = this.effectShelf.add(id, this.motionMs, this.camera.snapshot(), this.width, this.height, space, this.particles, x, y); this.notice = e.effectId + ' · ' + space + ' space · seed ' + e.seed; this.revision++; return e; }
    loadMesh(text, name = 'Imported mesh', upAxis = 'Y') { const asset = parseOBJ(text, { name, upAxis, size: 60 }); this.mesh = asset; this.setScene('model-viewer'); this.notice = asset.name + ' · ' + asset.triangles.length + ' triangles' + (asset.warnings.length ? ' · ' + asset.warnings.join('; ') : ''); }
    /** A single input path shared by the browser, native terminal and SceneBridge. */
    input(text) {
        if(typeof text !== 'string') throw new RangeError('input text');
        const a=[...this.draft], b=[...text], caret=this.draftCaret;
        this.replaceDraft(a.slice(0,caret).join('')+text+a.slice(caret).join(''),caret+b.length);
    }
    replaceDraft(text, caret = [...text].length) {
        if (typeof text !== 'string' || [...text].length > 4096)
            throw new RangeError('Draft limit 4096 scalars');
        finite(caret, 0, 4096, 'caret');
        if (!Number.isInteger(caret))
            throw new RangeError('Integer scalar caret required');
        const insertions = textInsertions(this.draft, text);
        this.draft = text;
        this.draftCaret = Math.max(0, Math.min([...text].length, Math.floor(caret)));
        const view = this.draftView();
        if (this.inputWeather.enabled && this.options.weatherIntensity > 0) {
            for (const g of insertions) {
                const x = view.originX + g.index - view.offset;
                if (x < view.originX || x >= view.originX + view.capacity || /\s/.test(g.glyph))
                    continue;
                this.inkEvents.push(Object.freeze({ id: ++this.inkSerial, space: 'screen', x, y: view.row, glyph: g.glyph, atMs: this.motionMs, ...this.inputWeather, hue: (this.inkSerial * 137.508) % 360 }));
            }
            this.inkEvents = this.inkEvents.filter(e => this.motionMs - e.atMs < e.lifeMs).slice(-96);
        }
        this.revision++;
    }
    backspace() {
        if(this.draftCaret===0)return;
        const a=[...this.draft], c=this.draftCaret;
        this.replaceDraft(a.slice(0,c-1).join('')+a.slice(c).join(''),c-1);
    }
    send() { super.send(); if (!this.draft) this.draftCaret = 0; }
    draftView() { return draftView(this.draft, this.draftCaret, this.width, this.height); }
    setDraftCaret(caret) { finite(caret, 0, 4096, 'caret'); if (!Number.isInteger(caret))
        throw new RangeError('Integer caret'); this.draftCaret = Math.max(0, Math.min([...this.draft].length, Math.floor(caret))); this.revision++; }
    /** Duplicate DOM reports sharing one gesture ID cannot emit twice. */
    emit(x, y, glyph = '·', kind) {
        const style = kind ?? this.selectedWeather;
        if (this.effectShelf && ['embers', 'leaves'].includes(style)) {
            this.playEffect('thermal.' + style, this.weatherSpace, x, y);
            return;
        }
        super.emit(x, y, glyph, kind);
    }
    emitPointer(dispatchId, x, y, kind = this.selectedWeather) {
        finite(x,-4096,4096,'pointer x');finite(y,-4096,4096,'pointer y');
        if(!['nova','firework','sparks','embers','leaves','rain','snow','ripples'].includes(kind)) throw new RangeError('weather kind');
        if (!this.pointerGate.accept(dispatchId))
            return false;
        this.emit(x, y, '*', kind);
        return true;
    }
    /** Screen-cell drag converted to world distance at the object's view depth. */
    moveWindowByScreen(id, dx, dy, forward = 0) {
        const win = this.spaceWindows.list().find(w => w.id === id);
        if (!win)
            throw new Error('Unknown window');
        const c = this.camera.snapshot(), p = new Projector(c, this.width, this.height), q = p.project(win), depth = Math.max(1, q?.z ?? 40);
        const delta = viewDisplacement(c, dx * depth / p.focal, -dy * 2 * depth / p.focal, forward);
        this.spaceWindows.move(id, { x: win.x + delta.x, y: win.y + delta.y, z: win.z + delta.z });
        this.revision++;
    }
    wheel(sample) {
        const pixels = signedWheel(sample);
        if (!pixels)
            return;
        const amount = clamp(pixels / 100, -4, 4);
        if (sample.shiftKey && ['windows', 'shapes', 'fleet-room'].includes(this.scene))
            this.moveWindowByScreen(this.spaceWindows.selected, 0, 0, amount * 2);
        else if (this.scenicMode === 'world' && (this.scene in SCENIC_WORLD || this.scene === 'model-viewer') && this.worldView.projection === 1)
            this.worldView.span = clamp(this.worldView.span * Math.exp(amount * .08), 16, 400);
        else if (this.navEnabled) {
            this.editCamera(()=>this.camera.dolly(-amount*2));
        }
        else
            this.scroll = Math.max(0, this.scroll + Math.sign(amount) * 3);
        this.revision++;
    }
    /** A manual view edit preserves a cruise's independent travel vector. A
     * scripted flight is deliberately anchored when the user takes control. */
    editCamera(edit) {
        const moving=this.flight.mode==='cruise', heading=this.flight.travelHeading();
        this.flight.anchor(this.camera.snapshot()); this.cameraTransition=null;
        edit();
        if(moving)this.flight.cruise(this.motionMs,this.camera.snapshot(),this.bh.flightSpeed,heading??undefined);
        this.revision++;
    }
    lookBy(yaw,pitch,roll=0) {
        for(const v of [yaw,pitch,roll])finite(v,-720,720,'look degrees');
        this.editCamera(()=>this.camera.rotate(yaw,pitch,roll));
    }
    panBy(right,up,forward=0) {
        for(const v of [right,up,forward])finite(v,-100000,100000,'pan world units');
        this.editCamera(()=>this.camera.moveLocal(right,up,forward));
    }
    pilot(action) {
        const moving=this.flight.mode==='cruise', heading=this.flight.travelHeading();
        super.pilot(action);
        if(moving&&['yaw-left','yaw-right','pitch-up','pitch-down','roll-left','roll-right',
          'left','right','up','down','forward','back','faster','slower'].includes(action))
            this.flight.cruise(this.motionMs,this.camera.snapshot(),this.bh.flightSpeed,heading??undefined);
    }
    dismissModal() {
        if(this.modalContext==='node'&&this.graphFocus){this.clearGraphFocus();return true;}
        return this.modalStack.dismiss();
    }
    /** Explicitly starts motion as well as selecting a visual recipe. */
    launchHyperlane() {
        this.setScene('warp');
        this.configure({ motion: true, backgroundStyle: 'warp', starCount: 900, trailMs: 100, brightness: .16 });
        this.camera.configure({ x: 0, y: 0, z: 0, yaw: -18, pitch: 8, roll: 12, mode: 'fly' });
        this.configure({ starSpeed: 14, travelYaw: 28, travelPitch: 12 });
        this.notice = 'OBLIQUE HYPERLANE · travelling at 14 units/s · drag to look; Brake stops travel';
    }
    clearGraphFocus() {
        this.graphFrom = graphWorldPositions(this);
        this.graphTo = new Map(this.layout.nodes.map(n => [n.id, { x: n.x, y: n.y, z: n.z }]));
        this.graphFocusAt = this.motionMs;
        this.graphFocus = '';
        this.modalStack.clear();
        this.revision++;
    }
    constructor() {
        super();
        this.atelierTextEnabled = false;
        this.atelierPlayer = new AtelierTextPlayer('EVERY LETTER HAS A WAY HOME', { effect: 'comet-stitch' });
        this.scenicMode = 'world';
        this.worldView = { projection: 1, span: 145, redshift: .8, detail: 1, sampling: 1, waterAlpha: .94, accent: 0, secondary: 0 };
        this.worldDetail = { waveHeight: 358 / 256, wavelength: 34, windAngle: 22, crossSwell: .48, choppiness: .43, foam: .62, waveSpeed: 1, joinRiver: 1 };
        this.mesh = null;
        this.effectShelf = new EffectShelf();
        this.selectedEffect = 'kinetic.sparks';
        this.effectSpace = 'world';
        this.hashLength = 12;
        // All graph positions are world-space; only the final projection is screen-space.
        this.graphFrom = new Map();
        this.graphTo = new Map();
        this.graphTransitMs = 1000;
        this.draftCaret = 0;
        this.inkEvents = [];
        this.inkSerial = 0;
        this.pointerGate = new DispatchGate();
        this.inputWeather = { enabled: true, lifeMs: 1600, speed: 16, width: .85, gain: .24, rings: 2 };
        this.graphTypeColors = { human: 0xdacb9d, agent: 0x98c9c4, store: 0xafa3d4, tool: 0xcbb48f, record: 0xabc1d1, approval: 0xb9ca88, commit: 0x96badc, 'pull-request': 0xcf9cac, reference: 0xc4b18a, artifact: 0xdcb28b };
        this.hashOwner = null;
        this.hashes = new Map();
        this.resize(160, 52);
        this.setScene('waterfall');
    }
    /** Original burst and connected electrical arcs remain separate, explicit
     * launchable effects. They may coexist with world-space events in one frame. */
    emitClassic(kind, x = this.width / 2, y = this.height / 2) {
        const previous = this.weatherSpace;
        try {
            this.weatherSpace = 'screen';
            super.emit(x, y, '*', kind);
        }
        finally {
            this.weatherSpace = previous;
        }
        this.notice = 'Classic ' + (kind === 'nova' ? 'Nova burst' : kind === 'sparks' ? 'electrical arc' : kind) + ' / preserved Kinetic sampler';
    }
    setScene(id) {
        if (id === 'model-viewer') {
            super.setScene('black-hole');
            this.scene = id;
        }
        else
            super.setScene(id);
        if (!this.worldView)
            return; // Base constructor legitimately calls this override.
        this.graphFrom.clear();
        this.graphTo.clear();
        if (['dag', 'spatial-menu'].includes(id)) {
            const known = new Map(this.richGraph.nodes.map(n => [n.id, n]));
            this.richGraph = new GraphIndex({ nodes: this.graph.nodes.map(n => ({ ...n, metadata: known.get(n.id)?.metadata ?? {} })), edges: this.graph.edges.map(e => ({ ...e, kind: this.richGraph.edges.find(old => old.source === e.source && old.target === e.target)?.kind ?? 'relates' })) });
            this.graphFocus = '';
        }
        if ((id in SCENIC_WORLD || id === 'model-viewer') && this.scenicMode === 'world')
            this.frameScenery();
        this.notice = (RESTORED_NAMES[id] ?? id) + ' / v0.9.0-rc.1';
    }
    /** Isometric initial composition, with perspective as an explicit alternative. */
    frameScenery() {
        this.camera.configure({ x: -68, y: 48, z: -96, yaw: 35, pitch: -22, roll: 0, fov: 62, mode: 'orbit' });
        if (this.scene === 'waterfall')
            this.camera.configure({ y: 58 });
        this.camera.target = { x: 0, y: this.scene === 'waterfall' ? 10 : 0, z: 0 };
        this.flight.anchor(this.camera.snapshot());
        this.worldView.span = this.scene === 'model-viewer' ? 100 : this.scene === 'black-hole' ? 124 : this.scene === 'waterfall' ? 170 : 220;
        this.navEnabled = true;
        this.revision++;
    }
    fitCamera() {
        if (this.worldView && (this.scene in SCENIC_WORLD || this.scene === 'model-viewer') && this.scenicMode === 'world')
            this.frameScenery();
        else
            super.fitCamera();
    }
    selectGraph(id) {
        this.richGraph.node(id);
        this.graphFrom = graphWorldPositions(this);
        super.selectGraph(id);
        this.graphTo = graphTargets(this, this.width, this.height);
    }
    loadGraph(input) { super.loadGraph(input); this.graphFrom.clear(); this.graphTo.clear(); }
    /** Supplied SHA256 is labelled as source data, never as independently verified.
     * Otherwise compute the content record fingerprint once per graph identity. */
    nodeHash(id) {
        const n = this.richGraph.node(id), provided = n.metadata?.sha256;
        if (typeof provided === 'string' && /^[0-9a-f]{64}$/i.test(provided))
            return { kind: 'source SHA-256', hex: provided.toLowerCase() };
        if (this.hashOwner !== this.richGraph) {
            this.hashOwner = this.richGraph;
            this.hashes.clear();
        }
        if (!this.hashes.has(id))
            this.hashes.set(id, graphRecordHash({ id: n.id, label: n.label ?? n.id, metadata: n.metadata ?? {} }));
        return { kind: 'record SHA-256', hex: this.hashes.get(id) };
    }
}

