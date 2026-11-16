import {hash32} from './observatory.js';
import {validateGraph} from './graph-layout.js';
/** Typed graph metadata and explicit federation. Display labels never create
 * identity; edges preserve their kind/source. No external service connection. */
function idHue(text) { let n = 2166136261; for (const c of text)
    n = Math.imul(n ^ c.charCodeAt(0), 16777619); return hash32(n) % 360; }
/** Validate and retain owned scalar metadata; indexes make repeated inspection
 * independent of an O(N*E) edge scan in the rendering loop. */
export class GraphIndex {
    constructor(input) {
        this.byId = new Map();
        this.parents = new Map();
        this.children = new Map();
        if (!input || !Array.isArray(input.nodes))
            throw new RangeError('Graph nodes required');
        for (const node of input.nodes)
            for (const value of Object.values(node.metadata ?? {}))
                if (typeof value === 'number' && !Number.isFinite(value))
                    throw new RangeError('Metadata must be finite');
        const text = JSON.stringify(input);
        if (text.length > 1048576)
            throw new RangeError('Graph metadata exceeds 1 MiB');
        const owned = JSON.parse(text);
        this.graph = validateGraph(owned);
        this.nodes = this.graph.nodes.map(n => {
            const src = owned.nodes.find(v => v.id === n.id), metadata = {};
            if (src.metadata) {
                if (typeof src.metadata !== 'object' || Array.isArray(src.metadata) || Object.keys(src.metadata).length > 64)
                    throw new RangeError('64 scalar metadata fields per node');
                for (const [k, v] of Object.entries(src.metadata)) {
                    if (['__proto__', 'constructor', 'prototype'].includes(k) || k.length > 64 || !['string', 'number', 'boolean'].includes(typeof v) && v !== null || typeof v === 'number' && !Number.isFinite(v) || typeof v === 'string' && v.length > 8192)
                        throw new RangeError('Invalid metadata');
                    metadata[k] = v;
                }
            }
            const out = { ...n, metadata };
            this.byId.set(n.id, out);
            this.parents.set(n.id, new Set());
            this.children.set(n.id, new Set());
            return out;
        });
        this.edges = owned.edges.map(e => { if (e.kind !== undefined && (typeof e.kind !== 'string' || e.kind.length > 64))
            throw new RangeError('edge kind'); this.parents.get(e.target).add(e.source); this.children.get(e.source).add(e.target); return { ...e, kind: e.kind ?? 'relates' }; }).sort((a, b) => (a.source < b.source ? -1 : a.source > b.source ? 1 : 0) || (a.target < b.target ? -1 : a.target > b.target ? 1 : 0) || (a.kind < b.kind ? -1 : a.kind > b.kind ? 1 : 0));
    }
    node(id) { const n = this.byId.get(id); if (!n)
        throw new RangeError('Unknown graph node ' + id); return { ...n, metadata: { ...n.metadata } }; }
    neighborhood(id) {
        this.node(id);
        const parents = [...this.parents.get(id)].sort(), children = [...this.children.get(id)].sort(), s = new Set();
        for (const p of parents)
            for (const c of this.children.get(p))
                if (c !== id)
                    s.add(c);
        const siblings = [...s].sort();
        return { parents, children, siblings, related: [...new Set([id, ...parents, ...children, ...siblings])].sort() };
    }
    search(query) { const q = query.toLowerCase(); return this.nodes.filter(n => `${n.id} ${n.label} ${Object.values(n.metadata ?? {}).join(' ')}`.toLowerCase().includes(q)).map(n => this.node(n.id)); }
    /** Numeric/date scales are explicit; category colors are keyed by field value. */
    color(id, field, min = 0, max = 100) { const n = this.node(id), v = field === 'degree' ? this.parents.get(id).size + this.children.get(id).size : n.metadata?.[field]; if (typeof v === 'number')
        return 255 - 220 * Math.max(0, Math.min(1, (v - min) / Math.max(.0001, max - min))); if (field === 'date' && typeof v === 'string') {
        const t = Date.parse(v);
        return Number.isFinite(t) ? 255 - 220 * Math.max(0, Math.min(1, (t - min) / Math.max(1, max - min))) : idHue(v);
    } return idHue(String(v ?? 'unspecified')); }
}
/** Prefix every identity by graph ID, then add ONLY caller-specified link edges.
 * Nodes with equal labels in separate graphs remain separate. */
export function mergeGraphs(inputs, links = []) {
    if (!Array.isArray(inputs) || inputs.length > 16)
        throw new RangeError('At most 16 graphs');
    const seen = new Set(), nodes = [], edges = [];
    for (const entry of inputs) {
        if (!/^[\w.-]{1,16}$/.test(entry.id) || seen.has(entry.id))
            throw new RangeError('Unique graph namespaces');
        seen.add(entry.id);
        const g = new GraphIndex(entry.graph);
        nodes.push(...g.nodes.map(n => ({ ...n, id: entry.id + '/' + n.id, metadata: { ...n.metadata, graph: entry.id } })));
        edges.push(...g.edges.map(e => ({ ...e, source: entry.id + '/' + e.source, target: entry.id + '/' + e.target })));
    }
    const merged = { nodes, edges: [...edges, ...links] };
    new GraphIndex(merged);
    return merged;
}
export function demoWorkgraph() {
    const entries = [['operator', 'OPERATOR', 'human'], ['planner', 'PLANNER', 'agent'], ['research', 'RESEARCH', 'agent'], ['memory', 'MEMORY', 'store'], ['tools', 'TOOLS', 'tool'], ['evidence', 'EVIDENCE', 'record'], ['synthesis', 'SYNTHESIS', 'agent'], ['review', 'REVIEW', 'approval'], ['commit', 'COMMIT 8f2d', 'commit'], ['pr', 'PR #42', 'pull-request'], ['merge', 'MERGE', 'commit'], ['ledger', 'LEDGER', 'record'], ['release', 'RELEASE', 'artifact'], ['remote', 'ORIGIN / MAIN', 'reference']];
    const pairs = [['operator', 'planner'], ['operator', 'research'], ['planner', 'tools'], ['research', 'tools'], ['research', 'evidence'], ['memory', 'synthesis'], ['tools', 'synthesis'], ['evidence', 'synthesis'], ['synthesis', 'review'], ['review', 'commit'], ['commit', 'pr'], ['pr', 'merge'], ['merge', 'release'], ['merge', 'remote'], ['review', 'ledger'], ['release', 'ledger']];
    return { nodes: entries.map(([id, label, type], i) => ({ id, label, metadata: { type, status: i % 4 === 0 ? 'waiting' : 'ready', date: `2026-09-${String(i + 1).padStart(2, '0')}`, score: 20 + i * 5, source: 'synthetic example', description: 'Select parent, child or sibling to traverse without losing identity.' } })), edges: pairs.map(([source, target]) => ({ source, target, kind: source === 'review' ? 'approved' : 'depends-on' })) };
}

