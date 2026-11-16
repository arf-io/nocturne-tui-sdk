import { TranscriptViewport } from './fleet-model.js';
const rgb = (r, g, b) => (r << 16) | (g << 8) | b;
function blend(a, b, p) { return rgb(Math.round((a >> 16) * (1 - p) + (b >> 16) * p), Math.round(((a >> 8) & 255) * (1 - p) + ((b >> 8) & 255) * p), Math.round((a & 255) * (1 - p) + (b & 255) * p)); }
const fit = (text, width) => Array.from(text).slice(0, Math.max(0, width)).join('');
const fmt = (n) => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
/** Compose a bounded, replayable FleetScene. Input state is never mutated. */
export function composeFleet(c) {
    const W = c.width, H = c.height, nodes = [], INK = c.config.values.inkColor, BASE = c.config.values.baseColor;
    const PALE = c.config.palette.map(s => parseInt(s.slice(1), 16));
    const TEAL = blend(PALE[2 % PALE.length], 0xcce9dd, .55), LILAC = blend(PALE[1 % PALE.length], 0xe6d5ef, .57), COPPER = blend(PALE[3 % PALE.length], 0xf3d3b2, .52), MUTED = blend(INK, BASE, .34), DIM = blend(INK, BASE, .56), ERROR = 0xebaaa9;
    const text = (x, y, width, value, fg = INK, extra = {}) => { if (width > 0 && y >= 0 && y < H)
        nodes.push({ kind: 'text', x, y, width: Math.min(512, width), height: 1, text: fit(value, width), fg, fgOpacity: 1000, ...extra }); };
    const box = (r, title, fg = LILAC, extra = {}) => { if (r.width > 0 && r.height > 0)
        nodes.push({ kind: 'box', ...r, text: fit(title, Math.max(0, r.width - 4)), fg, bg: BASE, fgOpacity: 670, bgOpacity: 915, ...extra }); };
    const rule = (x, y, width, style = 0, fg = DIM) => { if (width > 0 && y >= 0 && y < H)
        nodes.push({ kind: 'rule', x, y, width, height: 1, style, fg, fgOpacity: 550, colorAnimation: c.options.readMode ? 0 : 2, hueSpeed: c.options.scopeColorSpeed }); };
    const trace = (r, values, fg, extra = {}) => { if (r.width > 0 && r.height > 0 && values.length)
        nodes.push({ kind: 'line', ...r, data: values.map(v => Math.max(0, Math.min(1000, Math.round(v)))), fg, fgOpacity: 900, colorAnimation: 0, ...extra }); };
    const series = (a, key, maximum) => a.history.map(m => m[key] * 1000 / maximum);
    const progress = (x, y, width, value, fg) => { if (width > 0 && y < H)
        nodes.push({ kind: 'progress', x, y, width, height: 1, value, fg, fgOpacity: 750, bg: BASE, style: 1 }); };
    const statusColor = (a) => a.status === 'error' ? ERROR : a.status === 'waiting' ? COPPER : a.status === 'offline' ? DIM : TEAL;
    const frameConfig = { ...c.config, values: { ...c.config.values, width: W, height: H, brightness: c.options.readMode ? 0 : c.options.backgroundBrightness, stars: c.options.readMode ? 0 : 1, focusY: Math.max(0, H - 5) * 256 }, palette: [...c.config.palette], starPalette: [...c.config.starPalette], glyphs: [...c.config.glyphs], novaGlyphs: [...c.config.novaGlyphs] };
    const active = c.model.agent(c.selectedId), metrics = active.metrics;
    const scene = () => ({ version: 1, kind: 'nocturne.fleet.scene', timeMs: c.options.readMode || c.options.reducedMotion ? 0 : c.motionMs, config: frameConfig, nodes, events: c.options.readMode ? [] : c.impulses.filter(e => c.motionMs >= e.atMs && c.motionMs - e.atMs < 4000), semantics: { title: 'Nocturne / Pearl Fleet', agentId: c.selectedId, transcript: c.model.transcript(c.selectedId), metrics: metrics ? { ...metrics } : null, demo: c.model.demo, revision: c.model.revision } });
    if (W < 38 || H < 16) {
        text(1, 1, W - 2, 'NOCTURNE / PEARL FLEET', LILAC);
        text(1, 3, W - 2, 'Resize to at least 38 x 16.');
        text(1, 5, W - 2, `Data revision ${c.model.revision} retained.`, TEAL);
        return scene();
    }
    const list = c.model.agents, measured = list.filter(a => a.metrics), total = measured.reduce((s, a) => s + a.metrics.tokenRate, 0), queue = measured.reduce((s, a) => s + a.metrics.queue, 0), worst = Math.max(0, ...measured.map(a => a.metrics.latencyMs));
    text(2, 0, Math.max(20, W - 40), 'N O C T U R N E   /   P E A R L   F L E E T', INK);
    text(Math.max(2, W - 36), 0, 34, c.model.demo ? 'OFFLINE DEMO / SYNTHETIC SOURCE' : 'HOST DATA / EXPLICIT ADAPTER', COPPER);
    rule(1, 1, W - 2, 0);
    text(2, 2, W - 4, `${String(list.length).padStart(2, '0')} AGENTS    ${fmt(total)} tok/s    ${queue} QUEUED    ${worst} ms WORST    ${fmt(c.model.revision)} EVENTS    ${c.paused ? 'MOTION HELD' : c.options.readMode ? 'READ MODE' : c.presentationFps + ' Hz MOTION TARGET'}`, MUTED);
    const tabWidth = Math.max(8, Math.floor((W - 4) / Math.min(list.length, 8))), tabStart = Math.floor(list.findIndex(a => a.id === c.selectedId) / 8) * 8;
    for (let i = tabStart; i < Math.min(list.length, tabStart + 8); i++) {
        const a = list[i], selected = a.id === c.selectedId, x = 2 + (i - tabStart) * tabWidth;
        nodes.push({ kind: 'item', id: 100 + i, x, y: 4, width: Math.max(1, tabWidth - 1), height: 1, text: fit(`${i + 1} ${a.name}${a.unread ? ' +' + a.unread : ''}`, tabWidth - 3), fg: selected ? INK : MUTED, bg: PALE[i % PALE.length], bgOpacity: selected ? 230 : 0, state: selected ? 2 : 0, fgOpacity: 1000 });
    }
    rule(1, 5, W - 2, 0);
    // Overview remains live beneath a maximized workspace.
    if (c.options.dense || W < 112 || H < 36) {
        text(3, 7, W - 6, 'AGENT       STATE       TOK/S   LATENCY    CONTEXT    QUEUE   SIGNAL', DIM);
        const capacity = Math.max(1, H - 16), start = Math.floor(list.findIndex(a => a.id === c.selectedId) / capacity) * capacity;
        for (let i = start; i < Math.min(list.length, start + capacity); i++) {
            const a = list[i], m = a.metrics, y = 9 + i - start, selected = a.id === c.selectedId;
            nodes.push({ kind: 'text', id: 1000 + i, x: 2, y, width: W - 4, height: 1, text: '', bg: PALE[i % PALE.length], bgOpacity: selected ? 150 : 0 });
            text(3, y, 12, `${selected ? '›' : ' '} ${a.name}`, selected ? INK : MUTED);
            text(16, y, 11, a.status, statusColor(a));
            if (m) {
                text(28, y, 8, String(m.tokenRate), TEAL);
                text(36, y, 10, m.latencyMs + ' ms', MUTED);
                text(47, y, 10, (m.contextPermille / 10).toFixed(1) + '%', LILAC);
                text(59, y, 6, String(m.queue), MUTED);
                trace({ x: 67, y, width: Math.max(0, W - 72), height: 1 }, series(a, 'tokenRate', 140), TEAL);
            }
            else
                text(28, y, W - 32, 'NO TELEMETRY / waiting for source', DIM);
        }
        const y = H - 7;
        rule(2, y, W - 4, 0);
        text(3, y + 1, W - 6, `${active.name} / ${active.description ?? active.role}`, LILAC);
        trace({ x: 3, y: y + 2, width: Math.max(1, W - 6), height: 2 }, series(active, 'tokenRate', 140), TEAL, { id: 20000 + list.indexOf(active) });
    }
    else {
        for (let i = tabStart; i < Math.min(list.length, tabStart + 8); i++) {
            const a = list[i], m = a.metrics, r = c.cardRect(a.id);
            if (r.y + r.height > H - 8)
                continue;
            const chosen = a.id === c.selectedId;
            box(r, `${String(i + 1).padStart(2, '0')} / ${a.name}`, chosen ? TEAL : LILAC, { id: 1000 + i, fgOpacity: chosen ? 1000 : 590, bgOpacity: chosen ? 940 : 880 });
            text(r.x + 2, r.y + 1, r.width - 4, a.role.toUpperCase(), chosen ? INK : MUTED);
            text(r.x + 2, r.y + 2, r.width - 4, `${a.status.toUpperCase()}${m ? '  ' + m.tokenRate + ' tok/s' : ''}`, statusColor(a));
            if (m) {
                trace({ x: r.x + 2, y: r.y + 3, width: r.width - 4, height: Math.max(1, r.height - 6) }, series(a, 'tokenRate', 140), TEAL, { fgOpacity: chosen ? 950 : 660 });
                if (r.height >= 8) {
                    text(r.x + 2, r.y + r.height - 3, r.width - 4, `${m.latencyMs}ms  CTX ${(m.contextPermille / 10).toFixed(0)}%  Q ${m.queue}`, MUTED);
                    progress(r.x + 2, r.y + r.height - 2, r.width - 4, m.contextPermille, LILAC);
                }
            }
        }
        const last = c.cardRect(list[Math.min(list.length, tabStart + 8) - 1].id), plotY = Math.min(H - 12, last.y + last.height + 2), plotH = Math.max(6, H - plotY - 3), plotW = Math.floor(W * .67) - 2;
        box({ x: 1, y: plotY, width: plotW, height: plotH }, 'PEARL SIGNAL / FLEET ENVELOPE', TEAL);
        text(3, plotY + 1, plotW - 4, 'TOKEN RATE 0..140 / LATENCY 0..600ms / CONTEXT 0..100%', DIM);
        const histories = list.filter(a => a.history.length), count = Math.min(96, ...histories.map(a => a.history.length));
        if (histories.length) {
            const aggregate = (key, max) => Array.from({ length: count }, (_, i) => histories.reduce((s, a) => s + a.history[a.history.length - count + i][key], 0) / histories.length * 1000 / max);
            const r = { x: 3, y: plotY + 3, width: plotW - 4, height: Math.max(1, plotH - 6) };
            trace(r, aggregate('contextPermille', 1000), LILAC, { fgOpacity: 560 });
            trace(r, aggregate('latencyMs', 600), COPPER, { fgOpacity: 720 });
            trace(r, aggregate('tokenRate', 140), TEAL, { fgOpacity: 1000 });
        }
        text(3, plotY + plotH - 2, plotW - 4, '∙ pearl throughput     ∙ copper latency     ∙ lilac context', MUTED);
        const x = plotW + 3, fw = W - x - 1;
        box({ x, y: plotY, width: fw, height: plotH }, 'PARTY LINE / LATEST', LILAC);
        const messages = list.map(a => ({ a, m: a.messages[a.messages.length - 1] })).filter(v => v.m).slice(0, Math.max(0, Math.floor((plotH - 3) / 2)));
        messages.forEach(({ a, m }, i) => { const y = plotY + 2 + i * 2; text(x + 2, y, fw - 4, `${a.name}  /  ${a.status}`, statusColor(a)); text(x + 2, y + 1, fw - 4, m.text || 'Receiving stream...', MUTED); });
    }
    // Expand/collapse an agent-specific surface. Its latest data is always used.
    if (c.hasWorkspace) {
        const r = c.activeRect();
        if (r.width >= 4 && r.height >= 3) {
            box(r, `${active.name} / ${active.role.toUpperCase()}`, TEAL, { id: 8900, fgOpacity: 1000, bgOpacity: 1000 });
            if (r.width > 25)
                text(r.x + 2, r.y + 1, r.width > 60 ? r.width - 22 : r.width - 4, `${active.name}  /  ${active.description ?? active.role}`, INK);
            if (r.width > 60) {
                text(r.x + r.width - 18, r.y + 1, 15, '[ ESC / FLEET ]', LILAC, { id: 9000 });
            }
            const enough = r.width >= 64 && r.height >= 15;
            if (enough) {
                const side = r.width >= 108 && r.height >= 28 ? 34 : 0, tw = Math.max(1, r.width - side - 6), ty = r.y + 5, th = Math.min(Math.max(1, r.height - 10), Math.max(1, Math.floor(24000 / tw))), tx = r.x + 3;
                text(tx, r.y + 3, tw, c.scrollOffset ? `CONVERSATION / HISTORY +${c.historyUnread} NEW` : 'CONVERSATION / FOLLOWING LIVE', c.scrollOffset ? COPPER : TEAL);
                if (c.scrollOffset)
                    text(tx + Math.max(0, tw - 15), r.y + 3, 15, '[ END / LIVE ]', TEAL, { id: 9001 });
                const full = TranscriptViewport.wrap(active.messages, tw), lines = TranscriptViewport.visible(full, th, c.scrollOffset);
                const baseline = ty + Math.max(0, th - lines.length);
                lines.forEach((line, row) => {
                    const y = baseline + row, protectedInk = line.severity !== 'normal' || line.messageKey === c.readKey;
                    const fg = line.severity === 'error' ? ERROR : line.severity === 'warning' ? COPPER : line.label ? (line.role === 'operator' ? COPPER : line.role === 'tool' ? LILAC : TEAL) : INK;
                    let x = tx;
                    if (line.runs.length === 0)
                        return;
                    // Mature runs share ink: merge by effective opacity, not delivery packet.
                    // At extreme fragmentation use one line fade, preserving content and bounds.
                    const inkRuns = [];
                    for (const run of line.runs) {
                        if (!run.text)
                            continue;
                        const age = Math.max(0, Math.min(4294967295, c.motionMs - run.bornMs));
                        const opacity = c.engine.inkOpacity(age, c.immediateVisuals || protectedInk || run.bornMs <= c.revealThroughMs ? 0 : c.options.arrivalMs, (y - ty) * 256, c.options.readMode || protectedInk ? 0 : c.options.horizonRows * 256, c.options.horizonMinimum);
                        const previous = inkRuns[inkRuns.length - 1];
                        if (previous && previous.opacity === opacity)
                            previous.text += run.text;
                        else
                            inkRuns.push({ text: run.text, opacity });
                    }
                    // Reserve one node per remaining row and 45 for sidebar/footer. This fallback
                    // only merges decoration; no authoritative message characters are dropped.
                    if (nodes.length + inkRuns.length + (lines.length - row) + 45 > 510) {
                        const joined = inkRuns.map(v => v.text).join(''), opacity = Math.max(...inkRuns.map(v => v.opacity));
                        inkRuns.splice(0, inkRuns.length, { text: joined, opacity });
                    }
                    for (const run of inkRuns) {
                        const length = Array.from(run.text).length;
                        text(x, y, Math.min(length, tx + tw - x), run.text, fg, { id: 100000 + line.messageKey, fgOpacity: run.opacity });
                        x += length;
                    }
                });
                if (!active.messages.length)
                    text(tx, ty, tw, 'No messages yet. Source events appear here without an animation gate.', MUTED);
                if (side) {
                    const sx = r.x + r.width - side, sw = side - 3;
                    rule(sx, r.y + 3, sw, 0);
                    text(sx, r.y + 4, sw, 'PEARL SIGNAL / ' + active.name, TEAL);
                    const sr = { x: sx, y: r.y + 6, width: sw, height: Math.max(3, Math.min(7, r.height - 23)) };
                    trace(sr, series(active, 'contextPermille', 1000), LILAC, { fgOpacity: 480 });
                    trace(sr, series(active, 'latencyMs', 600), COPPER, { fgOpacity: 640 });
                    trace(sr, series(active, 'tokenRate', 140), TEAL, { fgOpacity: 1000, id: 20000 + list.indexOf(active) });
                    const sy = sr.y + sr.height + 1;
                    text(sx, sy, sw, 'THROUGHPUT / tok per second', DIM);
                    if (metrics) {
                        if (r.height >= 28)
                            nodes.push({ kind: 'digits', x: sx, y: sy + 1, width: sw, height: 5, text: String(metrics.tokenRate), fg: TEAL, fgOpacity: 1000, zoom: 1, colorAnimation: 0 });
                        else
                            text(sx, sy + 1, sw, String(metrics.tokenRate), TEAL);
                        const mY = sy + (r.height >= 28 ? 7 : 3);
                        text(sx, mY, sw, `LATENCY       ${metrics.latencyMs} ms`, MUTED);
                        text(sx, mY + 1, sw, `CONTEXT       ${(metrics.contextPermille / 10).toFixed(1)}%`, LILAC);
                        progress(sx, mY + 2, sw, metrics.contextPermille, LILAC);
                        text(sx, mY + 4, sw, `QUEUE ${metrics.queue}       TOOLS ${metrics.tools}`, MUTED);
                        text(sx, mY + 5, sw, `STATE / ${active.status.toUpperCase()}`, statusColor(active));
                        if (mY + 7 < r.y + r.height - 5)
                            text(sx, mY + 7, sw, c.model.demo ? 'SYNTHETIC / NO PROVIDER LINK' : 'METRICS FROM HOST EVENTS', DIM);
                    }
                }
                const py = r.y + r.height - 4;
                rule(tx, py - 1, Math.max(1, r.width - 6), 7);
                text(tx, py - 0, Math.max(1, r.width - 6), `${c.draft ? '› ' + c.draft : '› Message ' + active.name + '...  (local outbox; never a shell)'}`, c.draft ? INK : MUTED, { id: 9100 });
                nodes.push({ kind: 'cursor', x: Math.min(r.x + r.width - 4, tx + 2 + Array.from(c.draft).length), y: py, width: 1, height: 1, style: 1, fg: TEAL, fgOpacity: 1000 });
                text(tx, py + 1, r.width - 6, 'ENTER send note   PgUp/PgDn history   END live tail   click text: full emphasis', DIM);
            }
        }
    }
    // Local input gets a stable surface before/through workspace expansion.
    // Remote transcript arrival remains animated; input itself never is.
    if (c.draft && (!c.hasWorkspace || c.transitionProgress() < 1000)) {
        nodes.push({ kind: 'text', x: 2, y: H - 4, width: W - 4, height: 2, text: '', bg: BASE, bgOpacity: 1000 });
        text(3, H - 4, W - 6, '› ' + c.draft, INK, { id: 9100, fgOpacity: 1000 });
        nodes.push({ kind: 'cursor', x: Math.min(W - 3, 5 + Array.from(c.draft).length), y: H - 4, width: 1, height: 1, style: 1, fg: TEAL, fgOpacity: 1000 });
    }
    rule(1, H - 2, W - 2, 0);
    text(2, H - 1, W - 4, c.inspection || 'TAB next agent  ·  ENTER expand  ·  ESC fleet  ·  Ctrl+P hold motion  ·  Ctrl+Q exit', MUTED);
    if (nodes.length > 512)
        throw new RangeError('Fleet composition exceeded node budget; reduce viewport or retained chunk fragmentation');
    return scene();
}
