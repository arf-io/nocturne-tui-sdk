import {WORLD_FIELDS} from './world-fields.js';
import {WORLD_DETAIL_FIELDS} from './world-detail-fields.js';
const roundWorld = (x) => Math.sign(x) * Math.floor(Math.abs(x) + .5);
export class WorldEngine {
    constructor(native) {
        this.native = native;
    }
    /** Caller owns the bytes. Throws for a missing/mismatched native core. */
    static async create(bytes) { const r = await WebAssembly.instantiate(bytes, {}), n = r.instance.exports; if (!n.nsWorldVersion || n.nsWorldVersion() !== 1 || n.nsWorldConfigSize() !== 96)
        throw new Error('World ABI v1 required'); return new WorldEngine(n); }
    pack(options, timeMs) {
        if (!Number.isSafeInteger(timeMs) || timeMs < 0)
            throw new RangeError('nonnegative safe timeMs required');
        if (!options || typeof options !== 'object' || Array.isArray(options))
            throw new RangeError('World options object');
        const words = new Int32Array(24);
        for (const key of Object.keys(options))
            if (!WORLD_FIELDS.some(f => f.name === key))
                throw new RangeError('Unknown world field ' + key);
        for (const f of WORLD_FIELDS) {
            const v = Object.prototype.hasOwnProperty.call(options, f.name) ? options[f.name] : f.default;
            if (typeof v !== 'number' || !Number.isFinite(v) || v < f.min || v > f.max || (f.scale === 1 && !Number.isInteger(v)))
                throw new RangeError('Invalid World ' + f.name);
            words[f.index] = roundWorld(v * f.scale);
        }
        new Int32Array(this.native.memory.buffer, this.native.nsWorldConfigPtr(), 24).set(words);
        return words;
    }
    frame(words, n) { if (n < 0)
        throw new RangeError('World native validation failed'); return { width: words[0], height: words[1], cells: new Uint32Array(this.native.memory.buffer, this.native.nsFramePtr(), n * 4).slice() }; }
    /** With no detail argument, render exactly the v0.8 scene. A detail object opts
     * into a joined waterfall lip and directional/choppy/crossing ocean spectrum.
     * Times are ms; coordinates world units; angles degrees. No I/O or clock. */
    render(options = {}, timeMs = 0, detail) {
        const w = this.pack(options, timeMs);
        if (detail === undefined)
            return this.frame(w, this.native.nsWorldRenderFrame(timeMs >>> 0, Math.floor(timeMs / 4294967296)));
        if (!detail || typeof detail !== 'object' || Array.isArray(detail))
            throw new RangeError('World detail object');
        const data = new Int32Array(8);
        for (const key of Object.keys(detail))
            if (!WORLD_DETAIL_FIELDS.some(f => f.name === key))
                throw new RangeError('Unknown world detail ' + key);
        for (const f of WORLD_DETAIL_FIELDS) {
            const v = Object.prototype.hasOwnProperty.call(detail, f.name) ? detail[f.name] : f.default;
            if (typeof v !== 'number' || !Number.isFinite(v) || v < f.min || v > f.max || (f.scale === 1 && !Number.isInteger(v)))
                throw new RangeError('Invalid world detail ' + f.name);
            data[f.index] = roundWorld(v * f.scale);
        }
        if (!this.native.nsWorldDetailPtr)
            throw new Error('Detailed World extension missing');
        new Int32Array(this.native.memory.buffer, this.native.nsWorldDetailPtr(), 8).set(data);
        return this.frame(w, this.native.nsWorldRenderDetailedFrame(timeMs >>> 0, Math.floor(timeMs / 4294967296)));
    }
    /** Draw an owned bounded triangle set through the SAME clipping/depth/cell
     * pipeline. Vertices are nine XYZ world-unit values, color is packed sRGB.
     * No textures, file/network access or retained pointers. Invalid input throws.
     * Example: renderMesh([{vertices:[-2,0,0,2,0,0,0,3,0],color:0x83beb2}]). */
    renderMesh(triangles, options = {}, timeMs = 0) {
        if (!Array.isArray(triangles) || triangles.length > 16000)
            throw new RangeError('Mesh limit 16000 triangles');
        const records = new Int32Array(triangles.length * 10);
        triangles.forEach((tri, i) => { if (!tri || !Array.isArray(tri.vertices) || tri.vertices.length !== 9 || !Number.isInteger(tri.color) || tri.color < 0 || tri.color > 0xffffff)
            throw new RangeError('Mesh triangle shape/color'); tri.vertices.forEach((v, k) => { if (typeof v !== 'number' || !Number.isFinite(v) || Math.abs(v) > 32768)
            throw new RangeError('Mesh vertex range'); records[i * 10 + k] = roundWorld(v * 256); }); records[i * 10 + 9] = tri.color; });
        const w = this.pack(options, timeMs);
        if (!this.native.nsWorldMeshPtr)
            throw new Error('World mesh extension missing');
        new Int32Array(this.native.memory.buffer, this.native.nsWorldMeshPtr(), records.length).set(records);
        return this.frame(w, this.native.nsWorldRenderMeshFrame(timeMs >>> 0, Math.floor(timeMs / 4294967296), triangles.length));
    }
}

