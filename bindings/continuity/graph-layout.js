import {clamp,finite,hash32,randomAt} from './observatory.js';
/** Deterministic bounded graph layout, independent of a renderer or frame clock.
 * Directed cycles are condensed for ranking, never deleted from the data graph.
 * Force jobs expose fixed-iteration chunks so a host can yield between batches.
 */
export const LAYOUT_MODES = ['layered-2d', 'layered-3d', 'force-2d', 'force-3d', 'radial-2d', 'radial-3d'];
export const DEFAULT_LAYOUT_OPTIONS = {
    mode: 'layered-3d', seed: 2030, iterations: 180, nodeGap: 5, layerGap: 9,
    depthGap: 5, repulsion: 65, spring: .04, linkLength: 13,
    damping: .76, timeStep: .3, sweeps: 8, collision: 1, orientation: 'TB',
};
export const LAYOUT_CONTROLS = {
    seed: [0, 4294967295, 1], iterations: [0, 800, 1], nodeGap: [.5, 80, .5],
    layerGap: [1, 80, .5], depthGap: [0, 80, .5], repulsion: [0, 500, 1],
    spring: [0, 1, .01], linkLength: [1, 100, 1], damping: [0, .99, .01],
    timeStep: [.01, 1, .01], sweeps: [0, 24, 1], collision: [0, 1, .1],
};
const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;
function idHash(id) { let h = 2166136261; for (const ch of id)
    h = Math.imul(h ^ ch.codePointAt(0), 16777619); return hash32(h); }
/** Normalize an independent copy. Unknown options, bad endpoints, duplicate IDs,
 * excessive sizes and nonfinite coordinates reject before a job is constructed.
 * Limits: 512 nodes, 4096 edges. Labels do not execute terminal controls.
 */
export function validateGraph(input) {
    if (!input || !Array.isArray(input.nodes) || !Array.isArray(input.edges) || input.nodes.length > 512 || input.edges.length > 4096)
        throw new RangeError('Graph requires at most 512 nodes / 4096 edges');
    const ids = new Set();
    const nodes = input.nodes.map(n => {
        if (!n || typeof n.id !== 'string' || !/^[A-Za-z0-9_.:/-]{1,64}$/.test(n.id) || ids.has(n.id))
            throw new RangeError('Unique, bounded graph IDs required');
        ids.add(n.id);
        if (n.label !== undefined && (typeof n.label !== 'string' || [...n.label].length > 160))
            throw new RangeError('Graph labels: at most 160 scalars');
        const out = { id: n.id, label: n.label ?? n.id, width: finite(n.width ?? 5, .1, 80, 'node width'), height: finite(n.height ?? 3, .1, 80, 'node height') };
        if (n.pin !== undefined) {
            if (!n.pin)
                throw new RangeError('pin requires XYZ');
            out.pin = { x: finite(n.pin.x, -10000, 10000, 'pin x'), y: finite(n.pin.y, -10000, 10000, 'pin y'), z: finite(n.pin.z, -10000, 10000, 'pin z') };
        }
        return out;
    }).sort((a, b) => compare(a.id, b.id));
    const edges = input.edges.map(e => {
        if (!e || !ids.has(e.source) || !ids.has(e.target))
            throw new RangeError('Every edge endpoint must exist');
        return { source: e.source, target: e.target, weight: finite(e.weight ?? 1, .01, 100, 'edge weight') };
    }).sort((a, b) => compare(a.source, b.source) || compare(a.target, b.target) || a.weight - b.weight);
    return { nodes, edges };
}
export function validateLayoutOptions(patch = {}) {
    const o = { ...DEFAULT_LAYOUT_OPTIONS };
    for (const [k, v] of Object.entries(patch)) {
        if (k === 'mode') {
            if (!LAYOUT_MODES.includes(v))
                throw new RangeError('Unknown layout mode');
            o.mode = v;
        }
        else if (k === 'orientation') {
            if (v !== 'TB' && v !== 'LR')
                throw new RangeError('orientation: TB / LR');
            o.orientation = v;
        }
        else if (Object.prototype.hasOwnProperty.call(LAYOUT_CONTROLS, k)) {
            const bounds = LAYOUT_CONTROLS[k];
            const n = finite(v, bounds[0], bounds[1], k);
            if (['seed', 'iterations', 'sweeps'].includes(k) && !Number.isInteger(n))
                throw new RangeError(k + ' requires an integer');
            o[k] = n;
        }
        else
            throw new RangeError('Unknown layout option ' + k);
    }
    return o;
}
function analyze(g) {
    const n = g.nodes.length, index = new Map(g.nodes.map((v, i) => [v.id, i]));
    const adj = Array.from({ length: n }, () => []), und = Array.from({ length: n }, () => []);
    for (const e of g.edges) {
        const a = index.get(e.source), b = index.get(e.target);
        adj[a].push(b);
        und[a].push(b);
        und[b].push(a);
    }
    const low = new Array(n).fill(-1), discovered = new Array(n).fill(-1), stack = [], on = new Set(), groups = [];
    let serial = 0;
    function visit(v) { discovered[v] = low[v] = serial++; stack.push(v); on.add(v); for (const w of adj[v]) {
        if (discovered[w] < 0) {
            visit(w);
            low[v] = Math.min(low[v], low[w]);
        }
        else if (on.has(w))
            low[v] = Math.min(low[v], discovered[w]);
    } if (low[v] === discovered[v]) {
        const group = [];
        let w;
        do {
            w = stack.pop();
            on.delete(w);
            group.push(w);
        } while (w !== v);
        groups.push(group.sort((a, b) => a - b));
    } }
    for (let i = 0; i < n; i++)
        if (discovered[i] < 0)
            visit(i);
    groups.sort((a, b) => a[0] - b[0]);
    const scc = new Array(n).fill(0);
    groups.forEach((vs, k) => vs.forEach(v => scc[v] = k));
    const incoming = new Array(groups.length).fill(0), out = Array.from({ length: groups.length }, () => new Set()), grank = new Array(groups.length).fill(0);
    for (let a = 0; a < n; a++)
        for (const b of adj[a])
            if (scc[a] !== scc[b] && !out[scc[a]].has(scc[b])) {
                out[scc[a]].add(scc[b]);
                incoming[scc[b]]++;
            }
    const ready = incoming.map((v, i) => v === 0 ? i : -1).filter(i => i >= 0);
    while (ready.length) {
        ready.sort((a, b) => a - b);
        const a = ready.shift();
        for (const b of [...out[a]].sort((a, b) => a - b)) {
            grank[b] = Math.max(grank[b], grank[a] + 1);
            if (--incoming[b] === 0)
                ready.push(b);
        }
    }
    const cycles = groups.filter(vs => vs.length > 1 || adj[vs[0]].includes(vs[0])).map(vs => vs.map(i => g.nodes[i].id));
    const component = new Array(n).fill(-1);
    let ci = 0;
    for (let i = 0; i < n; i++)
        if (component[i] < 0) {
            const q = [i];
            component[i] = ci;
            while (q.length) {
                const a = q.shift();
                for (const b of und[a])
                    if (component[b] < 0) {
                        component[b] = ci;
                        q.push(b);
                    }
            }
            ci++;
        }
    return { groups, scc, cycles, ranks: scc.map(c => grank[c]), component };
}
/** A cancellable fixed-iteration solve. step(batch) never reads time or randomness
 * from a host. Yield via a worker or setTimeout between batches for large graphs.
 * result() is an owned snapshot and throws until the requested iterations finish.
 * Example: const j=new LayoutJob(graph,{mode:'force-3d'}); while(!j.done) j.step(8).
 */
export class LayoutJob {
    constructor(graph, options = {}) {
        this.iteration = 0;
        this.cancelled = false;
        this.completed = false;
        this.graph = validateGraph(graph);
        this.options = validateLayoutOptions(options);
        this.analysis = analyze(this.graph);
        const o = this.options, g = this.graph, index = new Map(g.nodes.map((v, i) => [v.id, i]));
        this.points = g.nodes.map((n, i) => ({ id: n.id, label: n.label, width: n.width, height: n.height, x: 0, y: 0, z: 0, rank: this.analysis.ranks[i], component: this.analysis.component[i], pinned: !!n.pin }));
        this.links = g.edges.map(e => [index.get(e.source), index.get(e.target), e.weight]);
        this.velocities = this.points.map(() => ({ x: 0, y: 0, z: 0 }));
        this.initialize();
        if (!o.mode.startsWith('force') || o.iterations === 0 || !this.points.length) {
            this.finish();
            this.completed = true;
        }
    }
    get done() { return this.completed; }
    get progress() { return this.completed ? 1 : this.iteration / Math.max(1, this.options.iterations); }
    cancel() { this.cancelled = true; }
    initialize() {
        const o = this.options, dim3 = o.mode.endsWith('3d'), n = this.points.length;
        if (o.mode.startsWith('force')) {
            this.points.forEach((p, i) => { const seed = o.seed ^ idHash(p.id), r = o.linkLength * Math.max(1, Math.cbrt(n) * .7); p.x = (randomAt(seed, 0) - .5) * r * 2; p.y = (randomAt(seed, 1) - .5) * r * 2; p.z = dim3 ? (randomAt(seed, 2) - .5) * r * 2 : 0; });
        }
        else {
            const components = new Set(this.points.map(p => p.component));
            for (const component of components) {
                const indices = this.points.map((p, i) => p.component === component ? i : -1).filter(i => i >= 0), maxRank = Math.max(0, ...indices.map(i => this.points[i].rank));
                const layers = Array.from({ length: maxRank + 1 }, (_, rank) => indices.filter(i => this.points[i].rank === rank));
                const neighbors = (i, forward) => this.links.filter(e => forward ? e[1] === i : e[0] === i).map(e => forward ? e[0] : e[1]);
                // Barycentric rank-order sweeps, with stable ID order to break equal scores.
                for (let pass = 0; pass < o.sweeps; pass++) {
                    const forward = pass % 2 === 0, order = Array.from({ length: layers.length }, (_, i) => i);
                    if (!forward)
                        order.reverse();
                    const positions = new Map();
                    layers.forEach(vs => vs.forEach((v, j) => positions.set(v, j)));
                    for (const r of order)
                        layers[r].sort((a, b) => { const score = (v) => { const ns = neighbors(v, forward); return ns.length ? ns.reduce((s, k) => s + (positions.get(k) ?? 0), 0) / ns.length : positions.get(v) ?? 0; }; return score(a) - score(b) || compare(this.points[a].id, this.points[b].id); });
                }
                layers.forEach((vs, rank) => {
                    const total = vs.reduce((s, i) => s + this.points[i].width + o.nodeGap, 0) - o.nodeGap;
                    let x = -total / 2;
                    vs.forEach((i, j) => {
                        const p = this.points[i];
                        if (o.mode.startsWith('radial')) {
                            const angle = (j / vs.length + rank * .11) * Math.PI * 2, rad = (rank + 1) * (o.layerGap + Math.max(...vs.map(k => this.points[k].width)) / 2);
                            p.x = Math.cos(angle) * rad;
                            p.y = Math.sin(angle) * rad;
                            p.z = dim3 ? (rank - maxRank / 2) * o.depthGap : 0;
                        }
                        else {
                            p.x = x + p.width / 2;
                            p.y = (maxRank / 2 - rank) * (o.layerGap + Math.max(...indices.map(k => this.points[k].height)));
                            p.z = dim3 ? (rank - maxRank / 2) * o.depthGap + (j % 2 - .5) * o.depthGap * .7 : 0;
                            x += p.width + o.nodeGap;
                        }
                    });
                });
            }
        }
        this.applyPins();
    }
    applyPins() { this.points.forEach((p, i) => { const pin = this.graph.nodes[i].pin; if (pin) {
        p.x = pin.x;
        p.y = pin.y;
        p.z = this.options.mode.endsWith('2d') ? 0 : pin.z;
        this.velocities[i] = { x: 0, y: 0, z: 0 };
    } }); }
    /** Perform at most batch fixed solver iterations. Throws after cancellation. */
    step(batch = 8) {
        if (this.cancelled)
            throw new Error('Layout cancelled');
        finite(batch, 1, 800, 'batch');
        if (!Number.isInteger(batch))
            throw new RangeError('integer batch required');
        if (this.completed)
            return;
        const o = this.options, dim3 = o.mode.endsWith('3d');
        for (let step = 0; step < batch && this.iteration < o.iterations; step++, this.iteration++) {
            const forces = this.points.map(() => ({ x: 0, y: 0, z: 0 }));
            for (let i = 0; i < this.points.length; i++)
                for (let j = i + 1; j < this.points.length; j++) {
                    const a = this.points[i], b = this.points[j];
                    let dx = a.x - b.x, dy = a.y - b.y, dz = dim3 ? a.z - b.z : 0;
                    let d = Math.hypot(dx, dy, dz);
                    if (d < 1e-6) {
                        dx = (randomAt(o.seed, i * 701 + j) - .5) || .01;
                        dy = (randomAt(o.seed ^ 177, i * 701 + j) - .5) || .01;
                        dz = dim3 ? (randomAt(o.seed ^ 921, i * 701 + j) - .5) : 0;
                        d = Math.hypot(dx, dy, dz);
                    }
                    const separation = (Math.max(a.width, a.height) + Math.max(b.width, b.height)) / 2 + o.nodeGap * .35;
                    const f = o.repulsion / (d * d + .5) + Math.max(0, separation - d) * o.collision * .8;
                    const fx = dx / d * f, fy = dy / d * f, fz = dz / d * f;
                    forces[i].x += fx;
                    forces[i].y += fy;
                    forces[i].z += fz;
                    forces[j].x -= fx;
                    forces[j].y -= fy;
                    forces[j].z -= fz;
                }
            for (const [a, b, weight] of this.links) {
                if (a === b)
                    continue;
                const p = this.points[a], q = this.points[b], dx = q.x - p.x, dy = q.y - p.y, dz = dim3 ? q.z - p.z : 0, d = Math.max(.001, Math.hypot(dx, dy, dz)), f = (d - o.linkLength) * o.spring * Math.sqrt(weight);
                for (const [axis, v] of [['x', dx], ['y', dy], ['z', dz]]) {
                    forces[a][axis] += v / d * f;
                    forces[b][axis] -= v / d * f;
                }
            }
            const cooling = .12 + .88 * (1 - this.iteration / Math.max(1, o.iterations));
            this.points.forEach((p, i) => { if (p.pinned)
                return; const v = this.velocities[i]; for (const axis of ['x', 'y', 'z']) {
                if (axis === 'z' && !dim3) {
                    p.z = 0;
                    continue;
                }
                const f = forces[i][axis] - p[axis] * .004;
                v[axis] = (v[axis] + f * o.timeStep) * o.damping;
                p[axis] += clamp(v[axis], -2, 2) * cooling;
            } });
            this.applyPins();
        }
        if (this.iteration >= o.iterations) {
            this.finish();
            this.completed = true;
        }
    }
    finish() {
        const o = this.options;
        // Pack disconnected components into deterministic side-by-side regions. Pins
        // are absolute constraints, so a pinned graph is never silently re-centred.
        if (!this.points.some(p => p.pinned)) {
            let offset = 0;
            const groups = [...new Set(this.points.map(p => p.component))].sort((a, b) => a - b);
            for (const group of groups) {
                const ps = this.points.filter(p => p.component === group);
                const minX = Math.min(...ps.map(p => p.x - p.width / 2)), maxX = Math.max(...ps.map(p => p.x + p.width / 2));
                const minY = Math.min(...ps.map(p => p.y)), maxY = Math.max(...ps.map(p => p.y)), minZ = Math.min(...ps.map(p => p.z)), maxZ = Math.max(...ps.map(p => p.z));
                for (const p of ps) {
                    p.x += offset - minX;
                    p.y -= (minY + maxY) / 2;
                    p.z -= (minZ + maxZ) / 2;
                }
                offset += maxX - minX + o.nodeGap * 3;
            }
            const center = (offset - (groups.length ? o.nodeGap * 3 : 0)) / 2;
            for (const p of this.points)
                p.x -= center;
        }
        if (o.orientation === 'LR')
            for (const p of this.points)
                if (!p.pinned) {
                    const x = p.x;
                    p.x = -p.y;
                    p.y = x;
                }
        for (const p of this.points)
            for (const a of ['x', 'y', 'z'])
                p[a] = Math.round(p[a] * 1e6) / 1e6;
    }
    /** Return an owned JSON-serializable layout. Identical input + options gives
     * identical coordinates in the JS implementation, regardless of step grouping.
     */
    result() {
        if (this.cancelled)
            throw new Error('Layout cancelled');
        if (!this.completed)
            throw new Error('Layout is not finished');
        const map = new Map(this.points.map((n, i) => [n.id, i])), edges = this.graph.edges.map(e => ({ ...e, weight: e.weight, feedback: this.analysis.scc[map.get(e.source)] === this.analysis.scc[map.get(e.target)] }));
        const bound = (op) => ({ x: this.points.length ? op(...this.points.map(p => p.x)) : 0, y: this.points.length ? op(...this.points.map(p => p.y)) : 0, z: this.points.length ? op(...this.points.map(p => p.z)) : 0 });
        return { version: 1, mode: this.options.mode, nodes: this.points.map(p => ({ ...p })), edges, cycles: this.analysis.cycles.map(c => [...c]), bounds: { min: bound(Math.min), max: bound(Math.max) } };
    }
}
/** Synchronous convenience solve. For interactive large graphs use LayoutJob and
 * yield between step() calls; never solve a graph inside a render() method.
 */
export function layoutGraph(graph, options = {}) { const job = new LayoutJob(graph, options); while (!job.done)
    job.step(32); return job.result(); }

