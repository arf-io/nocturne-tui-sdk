import {clamp,fract,hex,rgb,putDot,drawSegment} from './observatory.js';
import {draftView,transitEase} from './continuity-input.js';
import {paintInkWeather} from './continuity-ink.js';
import {BlackHoleRenderer} from './black-hole-renderer.js';
import {graphViewport,graphFocusPositions} from './restoration-graph.js';
import {SCENIC_WORLD,RestorationModel} from './restoration-model.js';
import {EffectPainter} from './effect-painter.js';
export class RestorationRenderer extends BlackHoleRenderer {
    constructor(engine, world) {
        super(engine);
        this.world = world;
        this.effectPainter = new EffectPainter(engine);
    }
    background(model, o) {
        if (!(model instanceof RestorationModel) || model.scenicMode !== 'world' || !(model.scene in SCENIC_WORLD || model.scene === 'model-viewer'))
            return super.background(model, o);
        const start = performance.now(), m = model, c = m.camera.snapshot(), bh = m.effectiveBH();
        this.base.prepare(m.palette, o);
        const waterTime = m.scene === 'waterfall' ? Math.max(0, Math.round(m.waterfallPhase.at(m.motionMs) * 1000)) : m.motionMs;
        const opts = { scene: SCENIC_WORLD[m.scene] ?? 0, width: m.width, height: m.height, cameraX: c.x, cameraY: c.y, cameraZ: c.z, yaw: c.yaw, pitch: c.pitch, roll: c.roll, fov: c.fov, ...m.worldView,
            flow: m.scene === 'waterfall' ? (bh.waterFlow === 0 ? 0 : 1) : 1, travel: m.surfaceDistance.at(m.motionMs) % 12000, seed: bh.worldSeed & 0x7fffffff, discTilt: Math.min(85, bh.discTilt - 58), background: rgb(m.palette.background) };
        const f = m.scene === 'model-viewer' ? this.world.renderMesh(m.mesh?.triangles ?? [], opts, waterTime) : this.world.render(opts, waterTime, m.worldDetail);
        // Native coverage is not an application hit ID.
        for (let i = 3; i < f.cells.length; i += 4)
            f.cells[i] = 0;
        this.timing.backgroundMs = performance.now() - start;
        return f;
    }
    sky(f, m, o) {
        if (m instanceof RestorationModel && m.scenicMode === 'world' && m.scene in SCENIC_WORLD)
            return 0;
        return super.sky(f, m, o);
    }
    weather(f, m, o) {
        const start = performance.now();
        let n = super.weather(f, m, o);
        if (m instanceof RestorationModel && m.weatherSpace === 'world' && m.events.length)
            n += this.classicWeather(f, m, { ...o, novaRegularity: 0 });
        this.timing.eventCount = n;
        this.timing.weatherMs = performance.now() - start;
        return n;
    }
    render(model, atMs = model.dataMs) {
        let m = model;
        if (model instanceof RestorationModel && ['dag', 'spatial-menu'].includes(model.scene)) {
            m = Object.create(model);
            m.scene = 'graph-explorer';
        }
        const view = model instanceof RestorationModel && model.scene === 'model-viewer' ? this.custom(model) : super.render(m, atMs);
        if (model instanceof RestorationModel && model.atelierTextEnabled && model.scene === 'text' && !model.modalStack.peek() && !model.showPalette) {
            const f = this.background(model, model.effective()), x = Math.max(3, (f.width - model.atelierPlayer.text.length) / 2), y = Math.floor(f.height / 2), ns = [];
            this.weather(f, model, model.effective());
            const age = model.motionMs;
            for (const g of model.atelierPlayer.sample(age)) {
                for (const tail of g.trail)
                    if (tail.opacity > .01)
                        ns.push({ kind: 'text', x: Math.round(x + tail.x), y: Math.round(y + tail.y), width: 1, height: 1, text: '·', fg: this.ink(200 + g.hueDelta), fgOpacity: Math.round(tail.opacity * 650) });
                if (g.opacity > .005)
                    ns.push({ kind: 'text', x: Math.round(x + g.x), y: Math.round(y + g.y), width: 1, height: 1, text: g.glyph, fg: this.ink(g.index * model.options.hueStep + g.hueDelta), fgOpacity: Math.round(g.opacity * 1000) });
            }
            ns.push({ kind: 'text', x: 4, y: 5, width: f.width - 8, height: 1, text: 'PRESERVED ATELIER / ' + model.atelierPlayer.options.effect, fg: 0xd8bfa7 }, { kind: 'text', x: 3, y: f.height - 4, width: f.width - 6, height: 1, text: '› ' + model.draft, fg: rgb(model.palette.ink), bg: rgb(model.palette.background), bgOpacity: 1000 }, { kind: 'text', x: 3, y: f.height - 2, width: f.width - 6, height: 1, text: '18 original entrance/exit families · full settings below · local ink never waits', fg: 0x9eb3c2 });
            view.frame = this.engine.paint(f, model.motionMs, model.managedPrompt ? ns.filter(n => n.y !== f.height - 4) : ns);
            view.nodes = ns;
            view.actions = {};
            view.semantics = [];
        }
        if (model instanceof RestorationModel) {
            const title = model.scene === 'waterfall' ? 'PEARL CASCADE / basalt, falling water, mist' : model.scene === 'tarmac' ? 'COPPER CAUSEWAY / suspended curves' : model.scene === 'ocean' ? 'TIDAL GLASS / a moonlit crossing' : model.scene === 'dunes' ? 'SILT / cut terrain and river' : model.scene === 'black-hole' ? 'RED SHIFT / orbital accretion' : model.scene.toUpperCase();
            const nodes = [{ kind: 'text', x: 2, y: 1, width: view.frame.width - 4, height: 1, text: 'NOCTURNE · CONTINUITY  v0.9.0-rc.1    ' + title, fg: rgb(model.palette.ink), bg: rgb(model.palette.background), bgOpacity: 1000 }];
            view.frame = this.engine.paint(view.frame, model.motionMs, nodes);
        }
        if (model instanceof RestorationModel) {
            view.activeWeather += this.effectPainter.paint(view.frame, model, h => this.ink(h));
            view.activeWeather += paintInkWeather(view.frame, model.inkEvents, model.motionMs, h => this.ink(h));
            if (!model.managedPrompt) {
            const draft = model.draftView();
            view.frame = this.engine.paint(view.frame, model.motionMs, [{ kind: 'text', x: 2, y: draft.row, width: Math.max(1, view.frame.width - 4), height: 1, text: '> ' + draft.text + ' '.repeat(Math.max(0, view.frame.width - draft.text.length - 6)), fg: rgb(model.palette.ink), bg: rgb(model.palette.background), bgOpacity: 1000, fgOpacity: 1000 }]);
            }
        }
        return view;
    }
    custom(m) {
        if (!(m instanceof RestorationModel) || m.scenicMode !== 'world' || !(m.scene in SCENIC_WORLD || m.scene === 'model-viewer'))
            return super.custom(m);
        const o = m.effective(), frame = this.background(m, o), activeWeather = this.weather(frame, m, o);
        const nodes = [{ kind: 'text', x: 3, y: frame.height - 2, width: frame.width - 6, height: 1, text: (m.worldView.projection ? 'ISOMETRIC' : 'PERSPECTIVE') + ' · drag to orbit · shift-drag to pan · wheel to zoom · controls below', fg: 0x9eb5c3, fgOpacity: 900 }];
        return { frame: this.engine.paint(frame, m.motionMs, nodes), nodes, semantics: [], actions: {}, drawnStars: 0, activeWeather };
    }
    graph(f, base, nodes, semantics, actions) {
        if (!(base instanceof RestorationModel))
            return super.graph(f, base, nodes, semantics, actions);
        const m = base, viewport = graphViewport(m, f.width, f.height), positions = graphFocusPositions(m, f.width, f.height), hood = m.graphFocus ? m.richGraph.neighborhood(m.graphFocus) : null, near = new Set(hood?.related ?? []);
        for (const edge of m.richGraph.edges) {
            const a = positions.get(edge.source), b = positions.get(edge.target);
            if (!a || !b)
                continue;
            const prominent = !hood || edge.source === m.graphFocus || edge.target === m.graphFocus;
            if (a.x > viewport.right && b.x > viewport.right)
                continue;
            drawSegment(f, a.x, a.y, b.x, b.y, this.ink(edge.kind === 'approved' ? 130 : 210), prominent ? .58 : .12);
            if (prominent) {
                const t = fract(m.motionMs / 3000 + edge.source.length * .19);
                putDot(f, (a.x + (b.x - a.x) * t) * 2, (a.y + (b.y - a.y) * t) * 4, this.ink(170), .85);
            }
        }
        const nodesByDepth = m.layout.nodes.map((n, i) => ({ n, i, p: positions.get(n.id) })).filter(v => v.p).sort((a, b) => b.p.z - a.p.z);
        const focusProgress = m.options.motion ? (m.graphTransitMs === 0 ? 1 : transitEase((m.motionMs - m.graphFocusAt) / m.graphTransitMs)) : 1;
        for (const { n, i, p } of nodesByDepth) {
            const a = p, selected = n.id === m.graphFocus, important = !hood || near.has(n.id), width = Math.round(clamp(Math.max(selected ? Math.min(30, m.hashLength + 9) : 9, (n.label.length + 5) * clamp(65 / Math.max(12, a.z), .5, 1.4) * m.bh.nodeScale), 9, selected ? 30 : 23)), height = selected ? 3 + Math.round(2 * focusProgress) : important ? 3 : 1, x = Math.round(a.x - width / 2), y = Math.round(a.y - height / 2);
            if (x < 1 || x + width >= viewport.right || y < 8 || y + height > f.height - 7)
                continue;
            const node = m.richGraph.node(n.id), type = String(node.metadata?.type ?? 'unspecified');
            const mapped = (m.graphColorField === 'auto' || m.graphColorField === 'type') ? m.graphTypeColors[type] : undefined;
            const fg = mapped ?? this.ink(m.richGraph.color(n.id, m.graphColorField === 'auto' ? 'type' : m.graphColorField, m.graphColorField === 'date' ? Date.parse('2026-01-01') : 0, m.graphColorField === 'date' ? Date.parse('2027-01-01') : 100));
            const alpha = selected ? 1 : important ? .9 : clamp(1 / (1 + a.z * m.bh.nodeDepthFade), .2, .5), id = 41000 + i;
            nodes.push({ kind: height > 1 ? 'button' : 'item', id, x, y, width, height, text: (selected ? '◆ ' : important ? '◇ ' : '· ') + (n.label.length > width - 5 ? n.label.slice(0, width - 6) + '…' : n.label), fg, bg: selected ? 0x23343e : 0x151e28, bgOpacity: Math.round(900 * alpha), fgOpacity: Math.round(1000 * alpha), state: selected ? 2 : 0 });
            if (selected && focusProgress > .6)
                nodes.push({ kind: 'text', id, x: x + 1, y: y + height - 2, width: width - 2, height: 1, text: 'sha256 ' + m.nodeHash(n.id).hex.slice(0, Math.min(m.hashLength, width - 9)), fg: 0xb7b3c8, fgOpacity: 950 });
            semantics.push({ id, label: n.label + ' · ' + type });
            actions[id] = { kind: 'rich-node', value: n.id };
        }
        nodes.push({ kind: 'text', x: 3, y: 6, width: Math.max(1, Math.floor(viewport.right) - 5), height: 1, text: hood ? 'PARENTS ↑   ◆ SELECTED   ↓ CHILDREN   ↔ SIBLINGS' : `${m.layoutOptions.mode} · ${m.richGraph.nodes.length} nodes · choose a node to inspect`, fg: this.ink(250), fgOpacity: 850 });
    }
    modal(view, base) {
        if (!(base instanceof RestorationModel) || base.modalContext !== 'node' || !base.modalStack.peek())
            return super.modal(view, base);
        const m = base, w = view.frame.width, h = view.frame.height, v = graphViewport(m, w, h), width = v.drawerWidth, x = Math.round(w - width - 1 + (1 - v.progress) * width), y = 6, height = Math.max(8, h - 12), n = m.richGraph.node(m.modalNode), hood = m.richGraph.neighborhood(n.id), hash = m.nodeHash(n.id);
        const ns = [{ kind: 'box', id: 49999, x, y, width, height, text: ' ' + (n.label ?? n.id) + ' ', fg: this.ink(180), bg: 0x121a25, bgOpacity: 950, style: 0 }];
        const text = (yy, s, color = 0xc6c3d5) => {
            if (yy < y + height - 2)
                ns.push({ kind: 'text', x: x + 2, y: yy, width: width - 4, height: 1, text: s, fg: color });
        };
        text(y + 2, hash.kind);
        text(y + 3, hash.hex.slice(0, m.hashLength), 0xa8d2c4);
        let yy = y + 5;
        for (const [key, value] of Object.entries(n.metadata ?? {}).filter(([k]) => !['sha256', 'description'].includes(k)).slice(0, 3))
            text(yy++, key + ': ' + value);
        for (const [label, ids] of [['PARENTS', hood.parents], ['SIBLINGS', hood.siblings], ['CHILDREN', hood.children]]) {
            text(++yy, label + '  ' + ids.length, 0xd6b899);
            for (const id of ids) {
                if (yy >= y + height - 4)
                    break;
                const hit = 47000 + yy;
                const name = m.richGraph.node(id).label ?? id;
                ns.push({ kind: 'item', id: hit, x: x + 2, y: ++yy, width: width - 4, height: 1, text: '↳ ' + name, fg: 0xafd3ce, bg: 0x22333f, bgOpacity: 700 });
                view.semantics.push({ id: hit, label: label + ': ' + name });
                view.actions[hit] = { kind: 'rich-node', value: id };
            }
        }
        ns.push({ kind: 'item', id: 47999, x: x + 2, y: y + height - 2, width: width - 4, height: 1, text: '× Close / Escape', fg: 0xd5ada5, bg: 0x29323d, bgOpacity: 900 });
        view.semantics.push({ id: 47999, label: 'Close node inspector' });
        view.actions[47999] = { kind: 'dismiss', value: '' };
        view.frame = this.engine.paint(view.frame, m.motionMs, ns);
        view.nodes.push(...ns);
    }
}

