import {clamp,fract,hash32,randomAt,rgb,mixColor,flattened,putCell,putDot,drawSegment,ObservatoryRenderer,composeObservatory,activateObservatory} from './observatory.js';
import {cameraBasis,projectSpatial,clipSpatialSegment} from './kinetic-camera.js';
import {sampleWeather} from './kinetic-particles.js';
import {shapeContains,windowVertex} from './kinetic-windows.js';
import {KINETIC_SCENES} from './kinetic-model.js';
export class KineticRenderer {
    constructor(engine) { this.engine = engine; this.base = new ObservatoryRenderer(engine); }
    ink(h) { return this.base.ink(h); }
    background(m, o) { return this.base.background(m, o); }
    sky(f, m, o) {
        if (m.scene !== 'warp' && o.backgroundStyle !== 'warp') {
            const glyphs = [...o.starGlyphs];
            for (let y = 0; y < f.height; y++)
                for (let x = 0; x < f.width; x++) {
                    const n = hash32(41041 ^ x * 1973 ^ y * 9277);
                    if (n / 4294967296 > o.starDensity)
                        continue;
                    const period = 2600 + n % 5800, phase = fract((m.motionMs + n % period) / period), a = Math.pow(Math.max(0, Math.sin(phase * Math.PI)), 8) * .7;
                    putCell(f, x, y, glyphs[n % glyphs.length].codePointAt(0), this.ink(n % 360), a);
                }
            return 0;
        }
        const camera = m.camera.snapshot(), travel = m.vectorTravel.at(m.motionMs), previous = m.vectorTravel.at(Math.max(0, m.motionMs - o.trailMs)), wrap = (x) => fract(x / 100 + .5) * 100 - 50;
        let drawn = 0;
        // Wrap a world-aligned volume around the viewer; drawing history never seeds points.
        for (let i = 0; i < o.starCount; i++) {
            const p = { x: camera.x + wrap((randomAt(7331, i * 3) - .5) * 100 - travel.x - camera.x), y: camera.y + wrap((randomAt(7331, i * 3 + 1) - .5) * 100 - travel.y - camera.y), z: camera.z + wrap((randomAt(7331, i * 3 + 2) - .5) * 100 - travel.z - camera.z) };
            const a = projectSpatial(p, camera, f.width, f.height);
            if (!a || a.x < 0 || a.x >= f.width || a.y < 0 || a.y >= f.height)
                continue;
            const color = this.ink(170 + randomAt(2941, i) * 160), alpha = clamp(1 - a.z / 70, .18, 1), q = { x: p.x + travel.x - previous.x, y: p.y + travel.y - previous.y, z: p.z + travel.z - previous.z }, b = projectSpatial(q, camera, f.width, f.height);
            if (b && o.trailMs > 0)
                drawSegment(f, a.x, a.y, b.x, b.y, color, alpha);
            putCell(f, a.x, a.y, a.z < 8 ? '*'.codePointAt(0) : a.z < 20 ? 0x2219 : 0xb7, color, alpha);
            drawn++;
        }
        return drawn;
    }
    weather(f, m, o) {
        if (o.weatherIntensity === 0)
            return 0;
        const events = m.events.filter(e => e.atMs <= m.motionMs && m.motionMs - e.atMs < m.particles.lifeMs).slice(-24), period = o.novaRegularity ? 60000 / o.novaRegularity : Infinity;
        if (Number.isFinite(period)) {
            const k = Math.floor(m.motionMs / period);
            for (let n = Math.max(1, k - 1); n <= k; n++)
                if (m.motionMs - n * period < m.particles.lifeMs)
                    events.push({ id: 900000 + n, x: randomAt(53, n) * f.width, y: 5 + randomAt(79, n) * (f.height - 12), atMs: n * period, kind: 'nova', glyph: '*' });
        }
        for (const e of events) {
            const burst = sampleWeather(e, m.motionMs, m.particles), weight = clamp(o.weatherIntensity * 2.6 * (e.kind === 'nova' ? o.novaStrength : 1), 0, 1);
            for (const s of burst.segments)
                drawSegment(f, s.x1, s.y1, s.x2, s.y2, this.ink(e.kind === 'embers' ? 40 + s.heat * 35 : e.kind === 'sparks' ? 210 + s.heat * 80 : 285 + s.heat * 90), s.opacity * weight);
            for (const p of burst.points)
                putCell(f, p.x, p.y, p.glyph.codePointAt(0), this.ink(e.kind === 'embers' ? 35 + p.heat * 40 : e.kind === 'sparks' ? 215 + p.heat * 60 : 285 + p.heat * 85), p.opacity * weight);
            if (burst.core > .01) {
                const radius = 1 + burst.core * 3;
                for (let y = Math.floor(e.y - radius); y <= e.y + radius; y++)
                    for (let x = Math.floor(e.x - radius * 2); x <= e.x + radius * 2; x++) {
                        if (x < 0 || y < 0 || x >= f.width || y >= f.height)
                            continue;
                        const dist = Math.hypot(x - e.x, (y - e.y) * 2), alpha = Math.max(0, 1 - dist / (radius * 2)) * burst.core * weight;
                        const idx = (y * f.width + x) * 4;
                        if (alpha > .02) {
                            const bg = flattened(f, idx);
                            f.cells[idx + 2] = mixColor(bg, 0xece2f4, alpha * .5);
                            putCell(f, x, y, dist < 1 ? 0x2736 : dist < 3 ? 0x2733 : 0x22c6, 0xf2eaf3, alpha);
                        }
                    }
            }
            if (burst.shockwave > .005) {
                const r = burst.radius;
                for (let j = 0; j < 96; j++) {
                    const a = j * Math.PI / 48;
                    putDot(f, (e.x + Math.cos(a) * r) * 2, (e.y + Math.sin(a) * r * .5) * 4, this.ink(290), burst.shockwave * weight);
                }
            }
        }
        return events.length;
    }
    /** Public layer adapter; same historical sampler, no new event or timer. */
    paintWeatherLayer(f, m, o) { this.base.prepare(m.palette, o); return this.weather(f, m, o); }
    renderSurface(m) { const o = m.effective(), f = this.background(m, o); this.sky(f, m, o); this.weather(f, m, o); return f; }
    /** Pure evaluation: no graph solving, time advancement, input consumption or window mutation. */
    render(m, atMs = m.dataMs) {
        const o = m.effective(atMs);
        let frame = this.background(m, o);
        const drawnStars = this.sky(frame, m, o), activeWeather = this.weather(frame, m, o);
        const special = ['warp', 'dag', 'spatial-menu', 'windows', 'shapes', 'text', 'weather-lab'].includes(m.scene), actions = {};
        if (!special) {
            const c = composeObservatory(m, o, this.base, frame);
            c.nodes.push({ kind: 'text', x: 2, y: 1, width: Math.min(130, m.width - 4), height: 1, text: 'NOCTURNE / KINETIC     VOL V · v0.5      OKLCh · 60 FPS / immediate ink', fg: rgb(m.palette.ink), fgOpacity: 1000 });
            frame = this.engine.paint(frame, m.motionMs, c.nodes);
            return { frame, nodes: c.nodes, semantics: c.semantics, drawnStars, activeWeather, actions };
        }
        const nodes = [], semantics = [], w = m.width, h = m.height, ink = rgb(m.palette.ink), base = rgb(m.palette.background), muted = this.ink(250), accent = this.ink(180), lilac = this.ink(305);
        const text = (x, y, width, value, fg = ink) => { if (width > 0 && y >= 0 && y < h)
            nodes.push({ kind: 'text', x: Math.round(x), y: Math.round(y), width: Math.round(width), height: 1, text: value, fg, fgOpacity: 1000 }); };
        const button = (id, x, y, width, height, label, kind, value, extra, color = accent) => { if (width <= 0 || height <= 0)
            return; nodes.push({ kind: 'button', id, x: Math.round(x), y: Math.round(y), width: Math.round(width), height: Math.round(height), text: label, fg: color, bg: 0x1e2938, bgOpacity: 880, fgOpacity: 1000, state: m.focusId === id ? 2 : 0 }); semantics.push({ id, label }); actions[id] = { kind, value, extra }; };
        const c = m.camera.snapshot();
        text(2, 1, w - 4, `NOCTURNE / KINETIC       VOL V · 0.5       ${Math.round(o.fps)} FPS · OKLCh`);
        nodes.push({ kind: 'rule', x: 2, y: 3, width: w - 4, height: 1, fg: lilac, fgOpacity: 600, style: 2 });
        if (m.scene === 'warp') {
            text(3, 5, w - 6, 'OBLIQUE HYPERLANE / THE CAMERA AND THE FLIGHT VECTOR ARE DIFFERENT', accent);
            text(3, 7, w - 6, `CAMERA  X ${c.x.toFixed(1)}  Y ${c.y.toFixed(1)}  Z ${c.z.toFixed(1)}  |  yaw ${c.yaw.toFixed(0)} pitch ${c.pitch.toFixed(0)} roll ${c.roll.toFixed(0)}`, muted);
            text(3, 8, w - 6, `TRAVEL  ${o.starSpeed.toFixed(1)} units/s  ·  heading ${o.travelYaw.toFixed(0)}°  elevation ${o.travelPitch.toFixed(0)}°  ·  ${drawnStars} visible stars`, muted);
            [['◀ PAN', 'left'], ['PAN ▶', 'right'], ['↑ UP', 'up'], ['↓ DOWN', 'down'], ['FORWARD', 'forward'], ['BACK', 'back'], ['BRAKE', 'stop'], ['ALIGN', 'align']].forEach(([label, action], i) => { if (3 + i * 12 + 11 < w)
                button(13000 + i, 3 + i * 12, h - 11, 11, 3, label, 'nav', action); });
            text(3, h - 7, w - 6, `${m.navEnabled ? 'NAV ON' : 'TYPE MODE'}  Drag: orbit/look · Shift-drag: pan · Wheel: dolly · WASD/RF: move · QE: roll`, accent);
        }
        else if (m.scene === 'dag' || m.scene === 'spatial-menu') {
            const visible = new Map(), height = Math.max(8, h - 17);
            for (const n of m.layout.nodes) {
                const p = projectSpatial(n, c, w, height);
                if (p)
                    visible.set(n.id, { ...p, y: p.y + 7 });
            }
            // Separate label placement from world layout. Bounded screen-space decluttering
            // prevents projection overlap from hiding identities; world XYZ stays unchanged.
            const slots = new Map(), rects = [];
            const nearFirst = m.layout.nodes.map((n, index) => ({ n, index, p: visible.get(n.id) })).filter(v => v.p).sort((a, b) => (a.n.id === m.graphSelection ? -1 : b.n.id === m.graphSelection ? 1 : a.p.z - b.p.z));
            for (const { n, p } of nearFirst) {
                if (rects.length >= 300 || p.x < -20 || p.x > w + 20 || p.y < 0 || p.y > h)
                    continue;
                const width = Math.min(w - 8, 24, Math.max(11, n.label.length + 7)), desired = { x: clamp(Math.round(p.x - width / 2), 3, w - width - 3), y: clamp(Math.round(p.y - 1), 8, h - 12) };
                let best, bestCost = Infinity;
                for (let dy = -16; dy <= 16; dy += 4)
                    for (let dx = -40; dx <= 40; dx += 4) {
                        const q = { x: Math.round(clamp(desired.x + dx, 3, w - width - 3)), y: Math.round(clamp(desired.y + dy, 8, h - 12)), width };
                        if (rects.some(a => q.x < a.x + a.width + 1 && q.x + q.width + 1 > a.x && q.y < a.y + 4 && q.y + 4 > a.y))
                            continue;
                        const cost = (q.x - desired.x) ** 2 + (q.y - desired.y) ** 2 * 4;
                        if (cost < bestCost) {
                            bestCost = cost;
                            best = q;
                        }
                    }
                if (best) {
                    slots.set(n.id, best);
                    rects.push(best);
                }
            }
            for (const e of m.layout.edges) {
                const an = m.layout.nodes.find(n => n.id === e.source), bn = m.layout.nodes.find(n => n.id === e.target), clipped = clipSpatialSegment(an, bn, c);
                if (!clipped)
                    continue;
                const pa = projectSpatial(clipped[0], c, w, height), pb = projectSpatial(clipped[1], c, w, height);
                if (!pa || !pb)
                    continue;
                const sa = slots.get(e.source), sb = slots.get(e.target), a = sa ? { x: sa.x + sa.width / 2, y: sa.y + 1.5 } : { x: pa.x, y: pa.y + 7 }, b = sb ? { x: sb.x + sb.width / 2, y: sb.y + 1.5 } : { x: pb.x, y: pb.y + 7 };
                const focus = e.source === m.graphSelection || e.target === m.graphSelection, col = e.feedback ? 0xe39c85 : focus ? accent : lilac;
                drawSegment(frame, a.x, a.y, b.x, b.y, col, focus ? .85 : .4);
                const phase = fract(m.motionMs / 2200 + randomAt(91, hash32(e.source.length * 37 + e.target.length)));
                putCell(frame, a.x + (b.x - a.x) * phase, a.y + (b.y - a.y) * phase, 0x2219, col, focus ? .95 : .6);
            }
            for (const { n, index, p } of nearFirst) {
                const slot = slots.get(n.id);
                if (!slot)
                    continue;
                button(11000 + index, slot.x, slot.y, slot.width, 3, (n.id === m.graphSelection ? '◆ ' : '◇ ') + n.label, 'node', n.id, undefined, n.id === m.graphSelection ? accent : lilac);
            }
            text(3, 5, w - 6, `${m.layoutOptions.mode.toUpperCase()} / ${m.layout.nodes.length} identities · ${m.layout.edges.length} edges · ${m.layout.cycles.length} cyclic groups`, accent);
            const parents = m.layout.edges.filter(e => e.target === m.graphSelection).map(e => e.source).join(', ') || '(root)', selected = m.layout.nodes.find(n => n.id === m.graphSelection);
            text(3, h - 8, w - 6, `${m.graphSelection}  ←  ${parents}`, accent);
            text(3, h - 7, w - 6, selected ? `XYZ ${selected.x.toFixed(2)}, ${selected.y.toFixed(2)}, ${selected.z.toFixed(2)} · ${selected.pinned ? 'PINNED' : 'automatic'} · Tab/Enter reaches nodes hidden in depth` : 'Empty graph', muted);
            // Offscreen nodes still have semantic/keyboard entries, with the same stable IDs.
            m.layout.nodes.forEach((n, i) => { if (!actions[11000 + i]) {
                semantics.push({ id: 11000 + i, label: `Inspect ${n.label}` });
                actions[11000 + i] = { kind: 'node', value: n.id };
            } });
        }
        else if (m.scene === 'windows' || m.scene === 'shapes') {
            frame = this.windows(frame, m, o);
            const selected = m.spaceWindows.list().find(v => v.id === m.spaceWindows.selected);
            text(3, 5, w - 6, `WINDOW THEATRE / ${selected.title} / ${m.spaceWindows.options.effect} / ${m.spaceWindows.options.chrome}`, accent);
            const controls = m.spaceWindows.controls(selected.id), total = controls.reduce((a, b) => a + b.width + 1, 0), start = controls[0].side === 'left' ? 3 : Math.max(3, w - total - 3);
            controls.forEach((ctrl, i) => button(12000 + i, start + i * (ctrl.width + 1), 6, ctrl.width, ctrl.height, `${ctrl.glyph} ${ctrl.label}`, 'window', selected.id, ctrl.action, ctrl.color));
            text(3, h - 11, w - 6, `SELECTED ${selected.id}  X ${selected.x.toFixed(1)} Y ${selected.y.toFixed(1)} Z ${selected.z.toFixed(1)}  ·  drag body: move · Alt-drag: rotate · Shift-wheel: depth`, muted);
            const list = m.spaceWindows.list(), tabW = Math.max(8, Math.min(28, Math.floor((w - 6) / list.length) - 1));
            list.forEach((win, i) => { button(14000 + i, 3 + i * (tabW + 1), h - 9, tabW, 3, `${({pearl:'Signal',atlas:'Flight',iris:'Materials'}[win.id]??win.title.split(' / ').at(-1)).slice(0,Math.max(1,tabW-12))} · ${{normal:'Open',minimized:'Restore',closed:'Restore',rolled:'Unfold',maximized:'Full'}[win.state]??win.state}`, 'dock', win.id, undefined, win.state === 'normal' ? accent : 0xd5b682); actions[15000 + i] = { kind: 'select-window', value: win.id }; semantics.push({ id: 15000 + i, label: 'Select ' + win.title }); });
        }
        else if (m.scene === 'text') {
            text(3, 5, w - 6, `TEXT CHOREOGRAPHY / ${m.textOptions.effect} IN · ${m.hideEffect} OUT`, accent);
            const sampled = m.textActor.sample(m.motionMs), width = Math.min(w - 10, m.textOptions.width), originX = 5, originY = Math.max(12, Math.floor(h * .44));
            for (const g of sampled) {
                const x = originX + g.x, y = originY + g.y;
                if (y < 7 || y >= h - 11 || x < 2 || x >= w - 2 || g.opacity <= 0)
                    continue;
                putCell(frame, x, y, g.glyph.codePointAt(0), this.ink(o.hueOffset + g.index * o.hueStep + m.motionMs * o.textHueSpeed / 1000 + g.hue), g.opacity);
            }
            text(5, originY + 5, w - 10, `PHASE ${m.textPhase} / ${Math.max(0, m.motionMs - m.textAtMs).toFixed(0)} ms / stagger ${m.textOptions.staggerMs} ms / group ${m.textOptions.batchSize}`, muted);
            const labels = [['[R] Replay', 'restart'], ['[+] Show / reverse', 'reveal'], ['[-] Hide / reverse', 'hide']];
            const buttonWidth = Math.max(8, Math.min(24, Math.floor((w - 10) / 3)));
            labels.forEach(([label, value], i) => { const id = 16000 + i, x = 3 + i * (buttonWidth + 2); nodes.push({ kind: 'box', id, x, y: h - 10, width: buttonWidth, height: 3, fg: accent, bg: 0x1e2938, bgOpacity: 900 }, { kind: 'text', id, x: x + 2, y: h - 9, width: buttonWidth - 4, height: 1, text: label.slice(0, buttonWidth - 4), fg: accent }); semantics.push({ id, label }); actions[id] = { kind: 'text', value }; });
            text(3, h - 6, w - 6, 'Data stays intact. Only presentation glyphs travel, flip or dissolve.', muted);
        }
        else if (m.scene === 'weather-lab') {
            text(3, 5, w - 6, 'WEATHER ATELIER / NOVA IS EJECTA, SPARKS ARE ARCS, EMBERS HAVE GRAVITY', accent);
            ['nova', 'sparks', 'embers', 'rain', 'snow', 'ripples'].forEach((kind, i) => { const x = 3 + i * 20; if (x + 18 < w)
                button(17000 + i, x, h - 10, 18, 3, kind.toUpperCase(), 'burst', kind); });
            text(3, 7, w - 6, `particles ${m.particles.count} · lifetime ${m.particles.lifeMs}ms · gravity ${m.particles.gravity} · arc branches ${m.particles.branches} · seed ${m.particles.seed}`, muted);
            text(3, h - 6, w - 6, 'Click to emit; choose the weather type in the desk. Bursts remain bounded and local.', muted);
        }
        // Always paint authoritative local input AFTER spatial shapes/weather/reveals.
        nodes.push({ kind: 'rule', x: 2, y: h - 5, width: w - 4, height: 1, fg: accent, fgOpacity: 450, style: 0 });
        if (!m.managedPrompt) text(3, h - 4, w - 6, '› ' + m.draft, ink);
        text(3, h - 2, w - 6, m.notice.slice(0, w - 6), muted);
        if (m.showPalette) {
            const bw = Math.min(68, w - 6), bx = Math.floor((w - bw) / 2), results = KINETIC_SCENES.filter(s => s.name.toLowerCase().includes(m.paletteQuery.toLowerCase())).slice(0, Math.min(12, h - 10));
            nodes.push({ kind: 'box', x: bx, y: 5, width: bw, height: Math.min(h - 7, results.length + 5), text: ' COMMAND PALETTE ', fg: accent, bg: base, bgOpacity: 1000, fgOpacity: 1000 });
            text(bx + 2, 7, bw - 4, '> ' + m.paletteQuery, ink);
            semantics.splice(0, semantics.length);
            results.forEach((s, i) => { nodes.push({ kind: 'item', id: 18000 + i, x: bx + 2, y: 9 + i, width: bw - 4, height: 1, text: s.name, fg: ink, bg: 0x263d41, bgOpacity: 1000, fgOpacity: 1000, state: i === m.selected ? 2 : 0 }); semantics.push({ id: 18000 + i, label: s.name }); actions[18000 + i] = { kind: 'scene', value: s.id }; });
        }
        frame = this.engine.paint(frame, m.motionMs, nodes);
        return { frame, nodes, semantics, drawnStars, activeWeather, actions };
    }
    /** Perspective-correct texture triangles, bounded to the viewport and tested
     * against the SAME coverage mask used for hits. No CSS transformations involved. */
    windowPose(model, id, atMs) { return model.spaceWindows.pose(id, atMs); }
    windows(frame, m, o) {
        const w = frame.width, h = frame.height, zbuffer = new Float64Array(w * h).fill(Infinity), camera = m.camera.snapshot(), opts = m.spaceWindows.options;
        const basis = cameraBasis(camera), distance = (a) => (a.x - camera.x) * basis.forward.x + (a.y - camera.y) * basis.forward.y + (a.z - camera.z) * basis.forward.z;
        const list = m.spaceWindows.list().sort((a, b) => distance(b) - distance(a) || a.order - b.order);
        for (const item of list) {
            let pose = this.windowPose(m, item.id, m.motionMs);
            if (pose.visibility < .001)
                continue;
            const originalIndex = m.spaceWindows.list().findIndex(v => v.id === item.id), id = 15000 + originalIndex, shape = item.shape ?? opts.shape;
            if (pose.maximized > 0) {
                const t = pose.maximized, b = cameraBasis(camera), dist = 34, ww = 2 * dist * Math.tan(camera.fov * Math.PI / 360) * .9, hh = ww * (h - 17) * 2 / w;
                pose = { ...pose, x: pose.x * (1 - t) + (camera.x + b.forward.x * dist) * t, y: pose.y * (1 - t) + (camera.y + b.forward.y * dist) * t, z: pose.z * (1 - t) + (camera.z + b.forward.z * dist) * t, width: pose.width * (1 - t) + ww * t, height: pose.height * (1 - t) + hh * t, yaw: pose.yaw * (1 - t), pitch: pose.pitch * (1 - t), roll: pose.roll * (1 - t) };
            }
            const corners = [{ x: pose.x - pose.width / 2, y: pose.y - pose.height / 2, z: pose.z }, { x: pose.x + pose.width / 2, y: pose.y + pose.height / 2, z: pose.z }].map(p => projectSpatial(p, camera, w, h));
            const tw = Math.max(24, Math.min(100, Math.round(Math.abs((corners[1]?.x ?? 60) - (corners[0]?.x ?? 0))))), th = Math.max(12, Math.min(40, Math.round(Math.abs((corners[1]?.y ?? 23) - (corners[0]?.y ?? 0))))), texture = { width: tw, height: th, cells: new Uint32Array(tw * th * 4) }, col = this.ink(originalIndex * 80 + 180);
            for (let y = 0; y < th; y++)
                for (let x = 0; x < tw; x++) {
                    const k = (y * tw + x) * 4;
                    texture.cells[k] = 32;
                    texture.cells[k + 1] = rgb(m.palette.ink);
                    texture.cells[k + 2] = mixColor(rgb(m.palette.background), this.base.colorAt(x / tw + y / th + m.motionMs / 18000), .72);
                }
            // Nonrectangular masks get an inscribed content area instead of chopping
            // the first letters off every line. Full content remains in the text view.
            const shaped = !['rectangle', 'rounded', 'wave', 'ticket'].includes(shape), tight = ['diamond', 'petal'].includes(shape), px = shaped ? Math.ceil(tw * (tight ? .25 : shape === 'hexagon' ? .15 : .2)) : 4, py = shaped ? Math.ceil(th * (tight ? .25 : .18)) : 3, innerW = Math.max(4, tw - px * 2), scopeY = Math.max(py + 3, th - py - 3);
            const content = shaped ? [{ kind: 'text', x: px, y: py, width: innerW, height: 1, text: item.title, fg: col, fgOpacity: 1000 }] : [{ kind: 'box', x: 1, y: 1, width: tw - 2, height: th - 2, fg: col, bgOpacity: 0, fgOpacity: 900, text: ' ' + item.title + ' ', style: 0 }];
            const startY = shaped ? py + 2 : 3, rowsOfText = [];
            for (const line of item.content.split('\n')) {
                if (!line) {
                    rowsOfText.push('');
                    continue;
                }
                for (let at = 0; at < line.length; at += innerW)
                    rowsOfText.push(line.slice(at, at + innerW));
            }
            rowsOfText.slice(0, Math.max(1, scopeY - startY - 1)).forEach((line, i) => content.push({ kind: 'text', x: px, y: startY + i, width: innerW, height: 1, fg: rgb(m.palette.ink), fgOpacity: 1000, text: line }));
            content.push({ kind: 'line', x: px, y: scopeY, width: innerW, height: Math.min(3, Math.max(1, th - py - scopeY)), data: m.waveform.map(v => Math.round(clamp(.5 + v * .4, 0, 1) * 1000)), fg: col, fgOpacity: 900 });
            if (!shaped)
                content.push({ kind: 'text', x: 4, y: th - 2, width: tw - 8, height: 1, text: `${item.id.toUpperCase()} / ${shape}`, fg: col, fgOpacity: 1000 });
            const painted = this.engine.paint(texture, m.motionMs, content), cols = pose.effect === 'explosion' ? 6 : 8, rows = pose.effect === 'explosion' ? 4 : Math.max(12, opts.folds * 2);
            const vertex = (u, v) => { const a = windowVertex(pose, u, v, opts), p = projectSpatial(a, camera, w, h); return p ? { ...p, u, v, opacity: a.opacity } : null; };
            for (let iy = 0; iy < rows; iy++)
                for (let ix = 0; ix < cols; ix++) {
                    const epsilon = pose.effect === 'explosion' ? 1e-6 : 0, u = ix / cols, v = iy / rows, u2 = (ix + 1) / cols - epsilon, v2 = (iy + 1) / rows - epsilon;
                    const a = vertex(u, v), b = vertex(u2, v), c = vertex(u2, v2), d = vertex(u, v2);
                    if (!a || !b || !c || !d)
                        continue;
                    this.triangle(frame, painted, zbuffer, [a, b, c], shape, pose, id);
                    this.triangle(frame, painted, zbuffer, [a, c, d], shape, pose, id);
                }
        }
        return frame;
    }
    triangle(out, tex, depth, t, shape, pose, id) {
        const [a, b, c] = t, den = (b.y - c.y) * (a.x - c.x) + (c.x - b.x) * (a.y - c.y);
        if (Math.abs(den) < 1e-8)
            return;
        const x0 = Math.max(0, Math.floor(Math.min(a.x, b.x, c.x))), x1 = Math.min(out.width - 1, Math.ceil(Math.max(a.x, b.x, c.x))), y0 = Math.max(9, Math.floor(Math.min(a.y, b.y, c.y))), y1 = Math.min(out.height - 12, Math.ceil(Math.max(a.y, b.y, c.y)));
        for (let y = y0; y <= y1; y++)
            for (let x = x0; x <= x1; x++) {
                const aa = ((b.y - c.y) * (x + .5 - c.x) + (c.x - b.x) * (y + .5 - c.y)) / den, bb = ((c.y - a.y) * (x + .5 - c.x) + (a.x - c.x) * (y + .5 - c.y)) / den, cc = 1 - aa - bb;
                if (aa < -.0001 || bb < -.0001 || cc < -.0001)
                    continue;
                const inv = aa / a.z + bb / b.z + cc / c.z, z = 1 / inv, u = (aa * a.u / a.z + bb * b.u / b.z + cc * c.u / c.z) / inv, v = (aa * a.v / a.z + bb * b.v / b.z + cc * c.v / c.z) / inv;
                if (!shapeContains(shape, u, v) || pose.effect === 'iris' && Math.hypot((u - .5) * 2, (v - .5) * 2) > pose.visibility * Math.SQRT2)
                    continue;
                const dest = y * out.width + x;
                if (z > depth[dest] + .001)
                    continue;
                const src = (clamp(Math.floor(v * tex.height), 0, tex.height - 1) * tex.width + clamp(Math.floor(u * tex.width), 0, tex.width - 1)) * 4, k = dest * 4, opacity = clamp((aa * a.opacity + bb * b.opacity + cc * c.opacity), 0, 1);
                if (opacity < .005)
                    continue;
                depth[dest] = z;
                const oldGlyph = out.cells[k], oldFg = out.cells[k + 1], bg = flattened(out, k);
                out.cells[k + 2] = mixColor(bg, tex.cells[src + 2], opacity);
                out.cells[k] = tex.cells[src];
                out.cells[k + 1] = mixColor(out.cells[k + 2], tex.cells[src + 1], Math.min(1, opacity * 1.2));
                out.cells[k + 3] = id;
                if (tex.cells[src] === 32 && opacity < .995 && oldGlyph > 32) {
                    out.cells[k] = oldGlyph;
                    out.cells[k + 1] = mixColor(out.cells[k + 2], oldFg, 1 - opacity);
                }
                if (shape !== 'rectangle' && shape !== 'rounded' && (!shapeContains(shape, u - 1 / tex.width, v) || !shapeContains(shape, u + 1 / tex.width, v) || !shapeContains(shape, u, v - 1 / tex.height) || !shapeContains(shape, u, v + 1 / tex.height))) {
                    out.cells[k] = 0x2219;
                    out.cells[k + 1] = mixColor(out.cells[k + 2], tex.cells[src + 1], Math.min(1, opacity * 1.6));
                }
            }
    }
}
/** Pixel/cell hit resolution is authoritative for nonrectangular transformed planes. */
export function hitKinetic(frame, x, y) { if (x < 0 || y < 0 || x >= frame.frame.width || y >= frame.frame.height)
    return 0; return frame.frame.cells[(Math.floor(y) * frame.frame.width + Math.floor(x)) * 4 + 3] || 0; }
/** Semantic actions and pointer actions use identical IDs. Offscreen graph nodes
 * stay keyboard-reachable through their semantic entries. */
export function activateKinetic(m, id, view) {
    const a = view?.actions[id];
    if (!a) {
        activateObservatory(m, id);
        return;
    }
    if (a.kind === 'scene') {
        m.setScene(a.value);
        m.showPalette = false;
        m.paletteQuery = '';
    }
    else if (a.kind === 'nav')
        m.navigate(a.value);
    else if (a.kind === 'node') {
        m.graphSelection = a.value;
        m.notice = 'Inspect ' + a.value + ' / parents: ' + m.layout.edges.filter(e => e.target === a.value).map(e => e.source).join(', ');
    }
    else if (a.kind === 'window')
        m.windowAction(a.value, a.extra);
    else if (a.kind === 'dock') {
        const win = m.spaceWindows.list().find(w => w.id === a.value);
        if (['minimized', 'closed', 'rolled'].includes(win.state))
            m.windowAction(a.value, 'restore');
        else
            m.spaceWindows.select(a.value);
    }
    else if (a.kind === 'select-window')
        m.spaceWindows.select(a.value);
    else if (a.kind === 'text') {
        if (a.value === 'restart')
            m.hardReplayText();
        else
            m.replayText(a.value);
    }
    else if (a.kind === 'burst')
        m.emit(m.width * .5, m.height * .53, '*', a.value);
    m.focusId = id;
    m.revision++;
}

