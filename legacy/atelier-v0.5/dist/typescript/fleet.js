import { TranscriptViewport, checkedInt, DEMO_NOTES, demoMetrics, FLEET_LIMITS } from './fleet-model.js';
import { composeFleet } from './fleet-view.js';
export * from './fleet-model.js';
export const DEFAULT_FLEET_OPTIONS = Object.freeze({ expandMs: 560, arrivalMs: 520, horizonRows: 6, horizonMinimum: 760, reducedMotion: false, readMode: false, dense: false, backgroundBrightness: 110, scopeColorSpeed: 8 });
/** Deterministic, explicit-time controller for the shared browser/terminal experience.
 * It emits command records, never shell commands or provider requests. Hosts call
 * ingest immediately on data, setTime on the host-selected decorative deadline, and paint.
 */
export class FleetController {
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
    setDraft(text) { if (typeof text !== 'string' || Array.from(text).length > 4096)
        throw new RangeError('draft limit: 4096 scalars'); this.view().draft = text; }
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
        if (typeof text !== 'string' || !text.trim() || Array.from(text).length > 4096)
            throw new RangeError('message requires 1..4096 scalars');
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
