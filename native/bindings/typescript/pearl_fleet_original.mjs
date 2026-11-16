/** Original Fleet host data/controller/composition, with explicit initial/later presentation revision and operator-required unbounded Unicode message/draft capacity. No renderer. */
export const PearlFleetOriginal=(()=>{
// Original model 5c3b239932f29055e937bc57af4cdbbb5646b581a3554e56e8e132f3b8945369; module syntax removed; document capacity and strict Unicode validation follow the operator extension documented in HOST-SOURCE-PROVENANCE.json.
const FLEET_LIMITS = Object.freeze({ agents: 32, messages: 256, messageScalars: null, eventLog: 8192, history: 96, chunkRuns: 256, outbox: 64 });
const ROLES = ['agent', 'operator', 'tool', 'system'];
const STATUSES = ['running', 'waiting', 'idle', 'offline', 'error'];
/** Reject invalid scalar values before mutation. */
function checkedInt(value, min, max, name) {
    if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < min || value > max)
        throw new RangeError(`${name}: integer ${min}..${max} required`);
    return value;
}
function checkedText(value, name, max = null) {
    if (typeof value !== 'string' || (max !== null && Array.from(value).length > max))
        throw new RangeError(`${name}: text up to ${max} scalars required`);
    for (const scalar of value) if (scalar.codePointAt(0) >= 0xd800 && scalar.codePointAt(0) <= 0xdfff) throw new RangeError(name + ': valid Unicode scalar text required');
    return value;
}
function record(value, name) { if (value === null || typeof value !== 'object' || Array.isArray(value))
    throw new TypeError(`${name}: object required`); return value; }
function id(value, name) { const text = checkedText(value, name, 96); if (!/^[a-zA-Z0-9_.:-]+$/.test(text))
    throw new RangeError(`${name}: nonempty stable ASCII ID required`); return text; }
function pick(value, allowed, name) { if (typeof value !== 'string' || !allowed.includes(value))
    throw new RangeError(`Invalid ${name}`); return value; }
function clone(value) { return JSON.parse(JSON.stringify(value)); }
/** Bounded authoritative state. `ingest` validates an entire event before committing.
 * Sequence numbers are increasing PER AGENT; duplicates/older events return false.
 * Arrival motionMs is supplied by the host and is recorded for deterministic replay.
 * Text is retained unchanged; unsupported terminal glyphs are a presentation concern.
 */
class FleetModel {
    constructor(specs) {
        this.eventLog = [];
        this.revision = 0;
        this.droppedEvents = 0;
        this.demo = false;
        this.nextMessageKey = 1;
        if (!Array.isArray(specs) || specs.length < 1 || specs.length > FLEET_LIMITS.agents)
            throw new RangeError('1..32 agents required');
        const seen = new Set();
        this.agents = specs.map(s => {
            const agentId = id(s.id, 'agent id');
            if (seen.has(agentId))
                throw new RangeError('duplicate agent id');
            seen.add(agentId);
            return { id: agentId, name: checkedText(s.name, 'agent name', 32), role: checkedText(s.role, 'agent role', 64), description: checkedText(s.description ?? '', 'description', 256), status: 'idle', lastSeq: 0, lastAtMs: 0, metrics: null, history: [], messages: [], droppedMessages: 0, unread: 0 };
        });
    }
    /** Find an existing agent; throws for unknown IDs. Never auto-creates identities. */
    agent(agentId) { const a = this.agents.find(a => a.id === agentId); if (!a)
        throw new RangeError(`Unknown agent ${agentId}`); return a; }
    appendMessage(a, message) { a.messages.push(message); if (a.messages.length > FLEET_LIMITS.messages) {
        a.messages.shift();
        a.droppedMessages++;
    } }
    /** Validate/commit one version-1 Fleet event. Returns false for stale sequence numbers.
     * Throws TypeError/RangeError for malformed, unknown-agent/message or oversized data.
     * Example: model.ingest({version:1,seq:1,agentId:'atlas',type:'status',atMs:0,payload:{status:'running'}},0).
     */
    ingest(input, motionMs) {
        checkedInt(motionMs, 0, Number.MAX_SAFE_INTEGER, 'motionMs');
        const e = record(input, 'event');
        if (e.version !== 1)
            throw new RangeError('Fleet event version must be 1');
        const a = this.agent(id(e.agentId, 'agentId'));
        const seq = checkedInt(e.seq, 1, Number.MAX_SAFE_INTEGER, 'seq'), atMs = checkedInt(e.atMs, 0, Number.MAX_SAFE_INTEGER, 'atMs');
        const type = pick(e.type, ['telemetry', 'status', 'message.start', 'message.delta', 'message.end'], 'event type');
        const p = record(e.payload, 'payload');
        // Duplicates carry no authority and cannot alter timestamps or reveal timing.
        if (seq <= a.lastSeq)
            return false;
        let commit;
        let payload;
        if (type === 'telemetry') {
            const m = { tokenRate: checkedInt(p.tokenRate, 0, 1000000, 'tokenRate'), latencyMs: checkedInt(p.latencyMs, 0, 1000000, 'latencyMs'), contextPermille: checkedInt(p.contextPermille, 0, 1000, 'contextPermille'), queue: checkedInt(p.queue, 0, 1000000, 'queue'), tools: checkedInt(p.tools, 0, 1000000, 'tools'), progressPermille: checkedInt(p.progressPermille, 0, 1000, 'progressPermille') };
            payload = { ...m };
            commit = () => { a.metrics = m; a.history.push({ ...m }); if (a.history.length > FLEET_LIMITS.history)
                a.history.shift(); };
        }
        else if (type === 'status') {
            const status = pick(p.status, STATUSES, 'status');
            payload = { status };
            commit = () => { a.status = status; };
        }
        else if (type === 'message.start') {
            const messageId = id(p.messageId, 'messageId');
            if (a.messages.some(m => m.id === messageId))
                throw new RangeError('duplicate message ID');
            const text = checkedText(p.text ?? '', 'text'), role = pick(p.role, ROLES, 'role'), severity = pick(p.severity ?? 'normal', ['normal', 'warning', 'error'], 'severity');
            payload = { messageId, role, severity, text };
            commit = () => { this.appendMessage(a, { id: messageId, key: this.nextMessageKey++, role, severity, text, chunks: text ? [{ text, bornMs: motionMs }] : [], atMs, complete: false, local: false }); a.unread++; };
        }
        else {
            const messageId = id(p.messageId, 'messageId'), m = a.messages.find(m => m.id === messageId);
            if (!m)
                throw new RangeError('unknown message ID');
            if (type === 'message.end') {
                payload = { messageId };
                commit = () => { m.complete = true; };
            }
            else {
                if (m.complete)
                    throw new RangeError('cannot append to a completed message');
                const text = checkedText(p.text, 'text');
                if (FLEET_LIMITS.messageScalars !== null && Array.from(m.text).length + Array.from(text).length > FLEET_LIMITS.messageScalars)
                    throw new RangeError('message capacity');
                payload = { messageId, text };
                commit = () => { m.text += text; if (text)
                    m.chunks.push({ text, bornMs: motionMs }); if (m.chunks.length > FLEET_LIMITS.chunkRuns) {
                    const old = m.chunks.splice(0, 128);
                    m.chunks.unshift({ text: old.map(c => c.text).join(''), bornMs: old[0].bornMs });
                } };
            }
        }
        // Only normalized scalar payloads enter the replay log. Unknown/cyclic extra
        // properties cannot cause a post-commit JSON serialization failure.
        const normalized = { version: 1, seq, agentId: a.id, type, atMs, payload };
        // All validation above; domain state and replay log commit together.
        commit();
        a.lastSeq = seq;
        a.lastAtMs = atMs;
        this.revision++;
        this.eventLog.push({ event: normalized, motionMs });
        if (this.eventLog.length > FLEET_LIMITS.eventLog) {
            this.eventLog.shift();
            this.droppedEvents++;
        }
        return true;
    }
    /** Append a LOCAL operator message. This does not consume an upstream sequence or
     * claim network delivery; only the host's explicit command adapter can send it.
     */
    localMessage(agentId, messageId, text, motionMs) {
        const a = this.agent(agentId);
        checkedText(text, 'text');
        checkedInt(motionMs, 0, Number.MAX_SAFE_INTEGER, 'motionMs');
        this.appendMessage(a, { id: messageId, key: this.nextMessageKey++, role: 'operator', severity: 'normal', text, chunks: [{ text, bornMs: motionMs }], atMs: a.lastAtMs, complete: true, local: true });
        this.revision++;
    }
    /** JSON-safe diagnostic snapshot. No credentials or runtime functions are included. */
    snapshot() { return { version: 1, demo: this.demo, revision: this.revision, droppedEvents: this.droppedEvents, agents: clone(this.agents) }; }
    /** Lossless retained text. Display fading never changes exported transcript data. */
    transcript(agentId) { return this.agent(agentId).messages.map(m => `${m.role.toUpperCase()}${m.local ? ' [local/outbound]' : ''}${m.severity !== 'normal' ? ' [' + m.severity + ']' : ''}\n${m.text}`).join('\n\n'); }
}
/** Stateless wrapping/viewport helper. All lengths are Unicode scalars, matching
 * the renderer's documented narrow glyph profile, not full grapheme layout.
 */
class TranscriptViewport {
    /** Wrap text without losing content or resetting arrival timestamps. Blank
     * separators and role labels are explicit rows. Width <=0 returns an empty list.
     */
    static wrap(messages, width) {
        if (width <= 0)
            return [];
        checkedInt(width, 1, 512, 'transcript width');
        const lines = [];
        for (const m of messages) {
            let index = 0;
            const base = { messageKey: m.key, messageId: m.id, role: m.role, severity: m.severity };
            lines.push({ ...base, label: true, runs: [{ text: `${m.role.toUpperCase()}${m.local ? ' / LOCAL OUTBOUND' : ''}${m.severity !== 'normal' ? ' / ' + m.severity.toUpperCase() : ''}`, bornMs: m.chunks[0]?.bornMs ?? 0 }], lineIndex: index++ });
            // Word boundaries are presentation breaks; preserve each scalar's birth time.
            const chars = [];
            for (const chunk of m.chunks)
                for (const glyph of Array.from(chunk.text))
                    if (glyph !== '\r')
                        chars.push({ glyph: glyph === '\t' ? ' ' : glyph, bornMs: chunk.bornMs });
            let cursor = 0;
            while (cursor < chars.length) {
                let end = Math.min(chars.length, cursor + width), newline = -1;
                for (let i = cursor; i < end; i++)
                    if (chars[i].glyph === '\n') {
                        newline = i;
                        break;
                    }
                if (newline >= 0)
                    end = newline;
                else if (end < chars.length && chars[end].glyph !== ' ' && chars[end].glyph !== '\n') {
                    for (let i = end - 1; i > cursor; i--)
                        if (chars[i].glyph === ' ') {
                            end = i + 1;
                            break;
                        }
                }
                const runs = [];
                for (let i = cursor; i < end; i++) {
                    const ch = chars[i], last = runs[runs.length - 1];
                    if (last && last.bornMs === ch.bornMs)
                        last.text += ch.glyph;
                    else
                        runs.push({ text: ch.glyph, bornMs: ch.bornMs });
                }
                lines.push({ ...base, label: false, runs, lineIndex: index++ });
                cursor = end;
                if (cursor < chars.length && chars[cursor].glyph === '\n')
                    cursor++;
            }
            if (!chars.length)
                lines.push({ ...base, label: false, runs: [], lineIndex: index++ });
            lines.push({ ...base, label: false, runs: [], lineIndex: index });
        }
        return lines;
    }
    /** Return the bottom-anchored window, or a history window offset in whole rows. */
    static visible(lines, height, offset) { if (height <= 0)
        return []; const end = Math.max(0, lines.length - Math.max(0, offset)); return lines.slice(Math.max(0, end - height), end); }
}
const DEMO_AGENTS = [
    { id: 'atlas', name: 'ATLAS', role: 'Coordinator', description: 'Task graph, routing, synthesis' },
    { id: 'prism', name: 'PRISM', role: 'Research', description: 'Sources, alternatives, evidence' },
    { id: 'forge', name: 'FORGE', role: 'Implementation', description: 'Worktree, patches, tests' },
    { id: 'quill', name: 'QUILL', role: 'Review', description: 'Correctness, docs, edge cases' },
    { id: 'sentinel', name: 'SENTINEL', role: 'Policy', description: 'Approval gates, bounded actions' },
    { id: 'relay', name: 'RELAY', role: 'Routing', description: 'Provider health, queue pressure' },
    { id: 'scribe', name: 'SCRIBE', role: 'Archive', description: 'Provenance, artifacts, indexing' },
    { id: 'echo', name: 'ECHO', role: 'Communication', description: 'Agent party line, operator notes' }
];
const DEMO_NOTES = [
    'The route map is stable. I am comparing two capacity profiles before moving the build queue.',
    'Research and implementation share the same task. PRISM owns the evidence; FORGE owns the patch. Both feed the review node.',
    'A newer telemetry sample is available. The values below are committed immediately, even while the decorative clock is held.',
    'The context envelope is approaching its soft limit. I have marked a handoff point without discarding the current transcript.',
    'One dependency needs a separate review.',
    'Synthetic samples received.',
    'The checkpoint contains the task identity, remaining work, and the current evidence list. No command has been executed by this preview.',
    'I will keep collecting updates while you read earlier messages. Live-tail following resumes only when you request it.',
    'The visual contract is simple: data now, light in motion. Neither a transition nor a fade delays the underlying event.',
    'Review complete for this simulated work unit. The next step remains visible in the activity stream.'
];
/** Deterministic example telemetry, not a measurement of a real system. */
function demoMetrics(agentIndex, tick) {
    const wave = (phase) => .7 * Math.sin(tick * .10) + .55 * Math.sin(tick * .14 + phase) + .35 * Math.sin(tick * .27 + phase * .7);
    return { tokenRate: Math.max(0, Math.round(45 + agentIndex * 5 + wave(agentIndex) * 32)), latencyMs: Math.round(180 + agentIndex * 17 + wave(agentIndex + 2) * 65), contextPermille: Math.round(360 + agentIndex * 48 + wave(agentIndex + 5) * 100), queue: Math.max(0, Math.round(2 + wave(agentIndex + 8) * 2)), tools: 12 + agentIndex * 3 + Math.floor(tick / 30), progressPermille: Math.min(980, 420 + agentIndex * 43 + Math.floor(tick / 8) % 100) };
}
/** Create a clearly labeled offline fixture fleet, with a seeded sample history.
 * This factory never contacts endpoints or claims to represent the user's agents.
 */
function createDemoFleet() {
    const m = new FleetModel(DEMO_AGENTS);
    m.demo = true;
    m.agents.forEach((a, i) => {
        for (let t = 0; t < 96; t++)
            m.ingest({ version: 1, agentId: a.id, seq: a.lastSeq + 1, type: 'telemetry', atMs: t * 100, payload: { ...demoMetrics(i, t) } }, 0);
        m.ingest({ version: 1, agentId: a.id, seq: a.lastSeq + 1, type: 'status', atMs: 9600, payload: { status: i === 4 ? 'waiting' : i === 6 ? 'idle' : 'running' } }, 0);
        for (let j = 0; j < 9; j++)
            m.ingest({ version: 1, agentId: a.id, seq: a.lastSeq + 1, type: 'message.start', atMs: 9600 + j * 20, payload: { messageId: `seed-${j}`, role: j % 4 === 0 ? 'operator' : j % 4 === 2 ? 'tool' : 'agent', text: DEMO_NOTES[(j + i) % DEMO_NOTES.length], severity: 'normal' } }, 0);
        a.unread = 0;
    });
    return m;
}
// Exact original view a3ab8091f8a873aef864f81c9a6fb711e7a9ac9c7b652fc20d1fcbe4ba4823db; module syntax removed; explicit sourceRevision selects the retained initial/later presentation, and document capacity follows the operator extension in HOST-SOURCE-PROVENANCE.json.
const rgb = (r, g, b) => (r << 16) | (g << 8) | b;
function blend(a, b, p) { return rgb(Math.round((a >> 16) * (1 - p) + (b >> 16) * p), Math.round(((a >> 8) & 255) * (1 - p) + ((b >> 8) & 255) * p), Math.round((a & 255) * (1 - p) + (b & 255) * p)); }
const fit = (text, width) => Array.from(text).slice(0, Math.max(0, width)).join('');
const fmt = (n) => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
/** Compose a bounded, replayable FleetScene. Input state is never mutated. */
function composeFleet(c) {
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
    text(2, 2, W - 4, `${String(list.length).padStart(2, '0')} AGENTS    ${fmt(total)} tok/s    ${queue} QUEUED    ${worst} ms WORST    ${fmt(c.model.revision)} EVENTS    ${c.paused ? 'MOTION HELD' : c.options.readMode ? 'READ MODE' : (c.sourceRevision === 'initial' ? 30 : c.presentationFps) + ' Hz MOTION TARGET'}`, MUTED);
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
    if (c.sourceRevision !== 'initial' && c.draft && (!c.hasWorkspace || c.transitionProgress() < 1000)) {
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
// Exact original controller f53e85c61b851a06031f6f4a73aa2f06b4e68ec5a9ffaf1b518db8d0946b4007; module syntax removed; explicit sourceRevision selects the retained initial/later presentation, and document capacity follows the operator extension in HOST-SOURCE-PROVENANCE.json.
const DEFAULT_FLEET_OPTIONS = Object.freeze({ expandMs: 560, arrivalMs: 520, horizonRows: 6, horizonMinimum: 760, reducedMotion: false, readMode: false, dense: false, backgroundBrightness: 110, scopeColorSpeed: 8 });
/** Deterministic, explicit-time controller for the shared browser/terminal experience.
 * It emits command records, never shell commands or provider requests. Hosts call
 * ingest immediately on data, setTime on the host-selected decorative deadline, and paint.
 */
class FleetController {
    constructor(engine, model, options = {}) {
        this.presentationFps = 30;
        this.width = 144;
        this.height = 48;
        this.motionMs = 0;
        this.paused = false;
        this.opened = false;
        /** Arrival runs already revealed by pause/read policy must never fade backward. */
        this.revealThroughMs = -1;
        this.impulses = [];
        this.inspection = '';
        this.views = new Map();
        this.transitionAt = 0;
        this.fromRect = null;
        this.toRect = null;
        this.commands = [];
        this.commandSerial = 0;
        this.demoTick = 96;
        this.nextDemoMessage = 0;
        this.replies = [];
        this.engine = engine;
        this.model = model;
        this.selectedId = model.agents[0].id;
        this.options = { ...DEFAULT_FLEET_OPTIONS };
        this.configure(options);
        for (const a of model.agents)
            this.views.set(a.id, { draft: '', scrollOffset: 0, historyUnread: 0, readKey: 0 });
        this.config = engine.defaults({ width: this.width, height: this.height, pattern: 3, brightness: this.options.backgroundBrightness, saturation: 470, stars: 1, starDensity: 8, novaChance: 4, periodMs: 12000, pixelMode: 1, focusMode: 1, focusY: 40 * 256, baseColor: 0x101218, inkColor: 0xe2d9cb });
        this.config.palette = ['#34354d', '#566c73', '#736382', '#4b7872', '#997f68'];
    }
    /** Atomically validate configurable visual policy. Unknown keys are rejected. */
    configure(options) {
        const next = { ...this.options, ...options };
        const limits = { expandMs: [0, 4000], arrivalMs: [0, 4000], horizonRows: [0, 32], horizonMinimum: [0, 1000], backgroundBrightness: [0, 1000], scopeColorSpeed: [-120, 120] };
        for (const [k, v] of Object.entries(options)) {
            if (['reducedMotion', 'readMode', 'dense'].includes(k)) {
                if (typeof v !== 'boolean')
                    throw new TypeError(k + ' must be boolean');
            }
            else if (limits[k])
                checkedInt(v, ...limits[k], k);
            else
                throw new RangeError('Unknown Fleet option ' + k);
        }
        this.options = next;
        if (next.readMode || next.reducedMotion)
            this.revealThroughMs = Math.max(this.revealThroughMs, this.motionMs);
    }
    view(agentId = this.selectedId) { return this.views.get(agentId); }
    /** Presentation metadata only; changing this never changes motion time. */
    setPresentationFps(fps) { checkedInt(fps, 1, 120, 'presentationFps'); this.presentationFps = fps; }
    /** Current draft is agent-local and preserved when switching workspaces. */
    get draft() { return this.view().draft; }
    get scrollOffset() { return this.view().scrollOffset; }
    get historyUnread() { return this.view().historyUnread; }
    get readKey() { return this.view().readKey; }
    get immediateVisuals() { return this.paused || this.options.reducedMotion || this.options.readMode; }
    /** Input changes never advance decorative time or wait for a frame callback. */
    setDraft(text) { checkedText(text, 'draft'); this.view().draft = text; }
    /** Set a sampled decorative time in milliseconds; pause retains its current value. */
    setTime(timeMs) { checkedInt(timeMs, 0, Number.MAX_SAFE_INTEGER, 'motionMs'); if (!this.paused)
        this.motionMs = timeMs; }
    /** Pause settles an unfinished workspace transition and reveals arriving text;
     * authoritative data is still accepted. Resume does not change message identity.
     */
    setPaused(paused) { this.paused = paused; if (paused) {
        this.revealThroughMs = Math.max(this.revealThroughMs, this.motionMs);
        if (this.toRect)
            this.fromRect = { ...this.toRect };
    } }
    /** Resize is a layout event: apply now and retarget from the currently visible
     * rectangle, not from its obsolete origin. Empty viewports are valid.
     */
    resize(width, height) { checkedInt(width, 0, 512, 'width'); checkedInt(height, 0, 256, 'height'); const previous = this.activeRect(); this.width = width; this.height = height; if (this.toRect) {
        this.fromRect = previous;
        this.toRect = this.opened ? this.workspaceRect() : this.cardRect(this.selectedId);
        this.transitionAt = this.motionMs;
        if (this.immediateVisuals)
            this.fromRect = { ...this.toRect };
    } }
    /** Final maximized application region. Does not invoke browser/terminal fullscreen. */
    workspaceRect() { return { x: 1, y: 6, width: Math.max(0, this.width - 2), height: Math.max(0, this.height - 8) }; }
    /** Overview source geometry. Dense/narrow views expand from the selected row. */
    cardRect(agentId) {
        const absolute = this.model.agents.findIndex(a => a.id === agentId), i = absolute % 8, count = Math.min(8, this.model.agents.length - Math.floor(absolute / 8) * 8);
        if (this.options.dense || this.width < 112 || this.height < 36)
            return { x: 2, y: 9 + (absolute % Math.max(1, this.height - 16)), width: Math.max(0, this.width - 4), height: 1 };
        const columns = this.width >= 132 ? 4 : 3, rows = Math.ceil(count / columns), cw = Math.floor((this.width - 2 - (columns - 1) * 2) / columns), ch = Math.min(10, Math.max(5, Math.floor((this.height - 21) / rows)));
        return { x: 1 + (i % columns) * (cw + 2), y: 7 + Math.floor(i / columns) * (ch + 1), width: cw, height: ch };
    }
    /** Current eased rectangle; interrupted transitions begin at this exact value. */
    activeRect() {
        if (!this.toRect || !this.fromRect)
            return this.cardRect(this.selectedId);
        if (this.immediateVisuals)
            return { ...this.toRect };
        const t = Math.max(0, this.motionMs - this.transitionAt), out = {};
        for (const key of ['x', 'y', 'width', 'height'])
            out[key] = this.engine.tween(this.fromRect[key], this.toRect[key], t, this.options.expandMs, 1);
        return out;
    }
    /** Fraction of the current transition, in thousandths. */
    transitionProgress() { return this.immediateVisuals ? 1000 : this.engine.tween(0, 1000, Math.max(0, this.motionMs - this.transitionAt), this.options.expandMs, 1); }
    /** Active overlay includes the closing transition until it reaches the deck. */
    get hasWorkspace() { return this.opened || (this.toRect !== null && this.transitionProgress() < 1000); }
    /** Select only (keyboard focus), without triggering an action. */
    selectAgent(agentId) { this.model.agent(agentId); this.selectedId = agentId; }
    /** Expand a tab/card into its agent workspace. No data stream is paused. */
    openAgent(agentId) {
        this.model.agent(agentId);
        const same = agentId === this.selectedId, source = this.hasWorkspace && same ? this.activeRect() : this.cardRect(agentId);
        this.selectedId = agentId;
        this.opened = true;
        this.fromRect = source;
        this.toRect = this.workspaceRect();
        this.transitionAt = this.motionMs;
        this.model.agent(agentId).unread = 0;
        if (this.immediateVisuals)
            this.fromRect = { ...this.toRect };
    }
    /** Return the active workspace to its tile/row; reverse safely mid-animation. */
    closeAgent() { if (!this.hasWorkspace)
        return; this.fromRect = this.activeRect(); this.toRect = this.cardRect(this.selectedId); this.transitionAt = this.motionMs; this.opened = false; if (this.immediateVisuals)
        this.fromRect = { ...this.toRect }; }
    /** Cycle tabs. With an open workspace this switches agents; otherwise only focus. */
    nextAgent(step = 1) { const agents = this.model.agents, i = agents.findIndex(a => a.id === this.selectedId), next = agents[(i + step % agents.length + agents.length) % agents.length].id; if (this.hasWorkspace)
        this.openAgent(next);
    else
        this.selectAgent(next); }
    /** Logical transcript dimensions, excluding metadata and composer. */
    transcriptRect() { const r = this.workspaceRect(), side = r.width >= 108 && r.height >= 28 ? 34 : 0, width = Math.max(1, r.width - side - 6); return { x: r.x + 3, y: r.y + 5, width, height: Math.min(Math.max(1, r.height - 10), Math.max(1, Math.floor(24000 / width))) }; }
    transcriptLines() { return TranscriptViewport.wrap(this.model.agent(this.selectedId).messages, this.transcriptRect().width); }
    /** Pure logical rows in the current history/live-tail window. */
    visibleTranscript() { return TranscriptViewport.visible(this.transcriptLines(), this.transcriptRect().height, this.view().scrollOffset); }
    /** Scroll upward by positive rows. A history window is never dragged by data. */
    scroll(rows) { checkedInt(rows, -100000, 100000, 'rows'); const v = this.view(); v.scrollOffset = Math.max(0, Math.min(Math.max(0, this.transcriptLines().length - this.transcriptRect().height), v.scrollOffset + rows)); if (!v.scrollOffset)
        v.historyUnread = 0; }
    /** Explicitly resume following the newest messages. */
    liveTail() { this.view().scrollOffset = 0; this.view().historyUnread = 0; this.view().readKey = 0; }
    /** Ingest independently of the render cadence; maintain the visible history anchor.
     * Event payload is validated by FleetModel. Returns whether state changed.
     */
    ingest(event) {
        const v = this.view(), e = event, anchoring = v.scrollOffset > 0 && e?.agentId === this.selectedId && typeof e?.type === 'string' && e.type.startsWith('message.');
        const oldLines = anchoring ? this.transcriptLines().length : 0;
        const changed = this.model.ingest(event, this.motionMs);
        if (changed && this.immediateVisuals)
            this.revealThroughMs = Math.max(this.revealThroughMs, this.motionMs);
        if (changed && anchoring) {
            v.scrollOffset = Math.max(0, v.scrollOffset + this.transcriptLines().length - oldLines);
            if (e?.type === 'message.start')
                v.historyUnread++;
        }
        return changed;
    }
    /** Queue a message for an explicit adapter. Returns its record, not an ACK.
     * A full outbox throws; it never silently drops commands. Blank input is rejected.
     */
    send(text = this.draft) {
        checkedText(text, 'message');
        if (!text.trim()) throw new RangeError('message requires nonblank text');
        if (this.commands.length >= FLEET_LIMITS.outbox)
            throw new RangeError('outbox full; attach/drain a command adapter');
        const command = { version: 1, commandId: `local-${++this.commandSerial}`, type: 'agent.message', agentId: this.selectedId, text };
        this.model.localMessage(this.selectedId, command.commandId, text, this.motionMs);
        if (this.immediateVisuals)
            this.revealThroughMs = Math.max(this.revealThroughMs, this.motionMs);
        this.commands.push(command);
        this.view().draft = '';
        this.liveTail();
        this.impulses.push({ x: 8, y: Math.max(0, this.height - 5), atMs: this.motionMs, strength: 500 });
        this.impulses = this.impulses.slice(-32);
        return { ...command };
    }
    /** Drain outbound records. The embedding host is solely responsible for delivery. */
    drainCommands() { const out = this.commands.map(c => ({ ...c })); this.commands = []; return out; }
    /** Click native cell hit areas. Returns a semantic action for the host composer. */
    click(x, y) {
        const scene = this.compose(), hit = this.engine.hit(scene.nodes, x, y);
        if (!hit)
            return '';
        const agentIndex = hit.id >= 1000 && hit.id < 1032 ? hit.id - 1000 : hit.id >= 100 && hit.id < 132 ? hit.id - 100 : -1;
        if (agentIndex >= 0 && this.model.agents[agentIndex]) {
            this.openAgent(this.model.agents[agentIndex].id);
            return 'open';
        }
        if (hit.id === 9000) {
            this.closeAgent();
            return 'close';
        }
        if (hit.id === 9001) {
            this.liveTail();
            return 'tail';
        }
        if (hit.id === 9100)
            return 'compose';
        if (hit.id >= 100000) {
            const key = hit.id - 100000;
            this.view().readKey = this.view().readKey === key ? 0 : key;
            return 'read';
        }
        if (hit.id >= 20000 && hit.id < 20032) {
            const a = this.model.agents[hit.id - 20000], m = a.history[Math.min(hit.item, a.history.length - 1)];
            if (m)
                this.inspection = `${a.name} / sample ${hit.item + 1}: ${m.tokenRate} tok/s | ${m.latencyMs} ms | context ${(m.contextPermille / 10).toFixed(1)}%`;
            return 'inspect';
        }
        return '';
    }
    /** Export a pure native-renderable scene. Render calls do not advance state. */
    compose() { return composeFleet(this); }
    /** Demo driver only. An embedding with model.demo=false never synthesizes events,
     * drains commands, or runs a reply. Input dataMs is explicit source time.
     */
    advanceDemo(dataMs) {
        checkedInt(dataMs, 0, Number.MAX_SAFE_INTEGER, 'dataMs');
        if (!this.model.demo)
            return;
        this.demoTick++;
        const emit = (agentId, type, payload) => { const a = this.model.agent(agentId); this.ingest({ version: 1, seq: a.lastSeq + 1, agentId, type, atMs: dataMs, payload }); };
        this.model.agents.forEach((a, i) => emit(a.id, 'telemetry', { ...demoMetrics(i, this.demoTick) }));
        for (const cmd of this.drainCommands()) {
            const messageId = `reply-${++this.nextDemoMessage}`;
            emit(cmd.agentId, 'message.start', { messageId, role: 'agent' });
            this.replies.push({ agentId: cmd.agentId, messageId, position: 0, text: 'Received your note in the offline demo. ' + DEMO_NOTES[(this.nextDemoMessage + 2) % DEMO_NOTES.length] });
        }
        if (this.demoTick % 42 === 0) {
            const a = this.model.agents[Math.floor(this.demoTick / 42) % this.model.agents.length], messageId = `stream-${++this.nextDemoMessage}`;
            emit(a.id, 'message.start', { messageId, role: 'agent' });
            this.replies.push({ agentId: a.id, messageId, position: 0, text: DEMO_NOTES[this.nextDemoMessage % DEMO_NOTES.length] });
        }
        for (const reply of this.replies) {
            const text = Array.from(reply.text).slice(reply.position, reply.position + 7).join('');
            if (text) {
                emit(reply.agentId, 'message.delta', { messageId: reply.messageId, text });
                reply.position += 7;
            }
            if (reply.position >= Array.from(reply.text).length)
                emit(reply.agentId, 'message.end', { messageId: reply.messageId });
        }
        this.replies = this.replies.filter(r => r.position < Array.from(r.text).length);
    }
}

return {FleetModel,FleetController,createDemoFleet,composeFleet,TranscriptViewport,DEFAULT_FLEET_OPTIONS,FLEET_LIMITS,demoMetrics};
})();
