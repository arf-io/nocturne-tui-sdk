import {rgb} from './observatory.js';
const cross2 = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
function triangulate(ids, vertices) {
    if (ids.length === 3) {
        const [a, b, c] = ids.map(i => vertices[i]), u = b.map((v, i) => v - a[i]), v = c.map((n, i) => n - a[i]);
        if (Math.hypot(u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]) < 1e-10)
            throw new Error('Degenerate triangle');
        return [ids];
    }
    const normal = [0, 0, 0];
    for (let i = 0; i < ids.length; i++) {
        const a = vertices[ids[i]], b = vertices[ids[(i + 1) % ids.length]];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }
    const length = Math.hypot(...normal);
    if (length < 1e-9)
        throw new Error('Degenerate or self-crossing polygon');
    const unit = normal.map(v => v / length), origin = vertices[ids[0]], extent = Math.max(1, ...ids.flatMap(id => vertices[id].map((v, i) => Math.abs(v - origin[i]))));
    for (const id of ids) {
        if (Math.abs(vertices[id].reduce((a, v, i) => a + (v - origin[i]) * unit[i], 0)) > extent * 1e-5)
            throw new Error('Nonplanar polygon: triangulate in authoring tool');
    }
    const drop = normal.map(Math.abs).indexOf(Math.max(...normal.map(Math.abs))), points = ids.map(id => vertices[id].filter((_, k) => k !== drop));
    for (let i = 0; i < ids.length; i++)
        for (let j = i + 1; j < ids.length; j++) {
            const i2 = (i + 1) % ids.length, j2 = (j + 1) % ids.length;
            if (i === j || i2 === j || j2 === i)
                continue;
            const a = points[i], b = points[i2], c = points[j], d = points[j2];
            if (cross2(a, b, c) * cross2(a, b, d) < -1e-12 && cross2(c, d, a) * cross2(c, d, b) < -1e-12)
                throw new Error('Self-crossing polygon');
        }
    const area = points.reduce((sum, p, i) => sum + p[0] * points[(i + 1) % points.length][1] - points[(i + 1) % points.length][0] * p[1], 0), sign = Math.sign(area), remaining = ids.map((_, i) => i), out = [];
    let budget = ids.length * ids.length;
    while (remaining.length > 3 && budget-- > 0) {
        let removed = false;
        for (let k = 0; k < remaining.length; k++) {
            const a = remaining[(k + remaining.length - 1) % remaining.length], b = remaining[k], c = remaining[(k + 1) % remaining.length];
            if (cross2(points[a], points[b], points[c]) * sign <= 1e-10)
                continue;
            const inside = remaining.some(i => i !== a && i !== b && i !== c && cross2(points[a], points[b], points[i]) * sign >= -1e-10 && cross2(points[b], points[c], points[i]) * sign >= -1e-10 && cross2(points[c], points[a], points[i]) * sign >= -1e-10);
            if (inside)
                continue;
            out.push([ids[a], ids[b], ids[c]]);
            remaining.splice(k, 1);
            removed = true;
            break;
        }
        if (!removed)
            throw new Error('Polygon could not be triangulated safely');
    }
    if (remaining.length !== 3)
        throw new Error('Polygon budget exceeded');
    out.push(remaining.map(i => ids[i]));
    return out;
}
/** Parse Wavefront OBJ geometry with optional vertex RGB, positive/negative
 * indices, and simple planar polygons (ear-clipped, not naive fan triangulation).
 * Normalizes a centered asset to size (default 60 world units), converts Z-up
 * when requested. Limits: 4 MiB text, 32000 vertices, 16000 triangles, 64/face.
 * Texture coordinates/normals/material files are not imported; warnings say so.
 * Throws with a source line for invalid geometry. No caller state is mutated. */
export function parseOBJ(text, options = {}) {
    if (typeof text !== 'string' || text.length > 4 * 1024 * 1024)
        throw new RangeError('OBJ limit 4 MiB');
    const size = options.size ?? 60;
    if (!Number.isFinite(size) || size < .1 || size > 1000)
        throw new RangeError('Mesh size .1..1000');
    if (options.upAxis && !['Y', 'Z'].includes(options.upAxis))
        throw new RangeError('upAxis Y or Z');
    const vertices = [], colors = [], faces = [], warnings = new Set();
    const lines = text.split(/\r?\n/);
    if (lines.length > 100000)
        throw new RangeError('OBJ line limit');
    lines.forEach((line, index) => {
        const words = line.split('#')[0].trim().split(/\s+/);
        if (!words[0])
            return;
        const kind = words.shift();
        if (kind === 'v') {
            if (vertices.length >= 32000)
                throw new RangeError('OBJ vertex limit');
            const xyz = words.slice(0, 3).map(Number);
            if (xyz.length !== 3 || xyz.some(v => !Number.isFinite(v) || Math.abs(v) > 1e8))
                throw new Error(`Invalid vertex at line ${index + 1}`);
            vertices.push(options.upAxis === 'Z' ? [xyz[0], xyz[2], -xyz[1]] : xyz);
            const rgb = words.length >= 6 ? words.slice(3, 6).map(Number) : [.51, .75, .71];
            if (rgb.some(v => !Number.isFinite(v) || v < 0 || v > 1))
                throw new Error('Vertex RGB must be 0..1');
            colors.push(rgb);
        }
        else if (kind === 'f') {
            if (words.length < 3 || words.length > 64 || faces.length >= 16000)
                throw new RangeError('OBJ face size/count limit');
            faces.push({ line: index + 1, ids: words.map(word => { const n = Number(word.split('/')[0]); if (!Number.isSafeInteger(n) || n === 0)
                    throw new Error(`Invalid index at line ${index + 1}`); return n < 0 ? vertices.length + n : n - 1; }) });
        }
        else if (['mtllib', 'usemtl', 'vt'].includes(kind ?? ''))
            warnings.add('External materials and textures are not loaded; vertex colors or the default material are used.');
        else if (!['vn', 'g', 'o', 's'].includes(kind ?? ''))
            warnings.add('Unsupported OBJ records were ignored; only polygon geometry is imported.');
    });
    if (!vertices.length || !faces.length)
        throw new Error('OBJ contains no polygon mesh');
    const min = [0, 1, 2].map(k => Math.min(...vertices.map(v => v[k]))), max = [0, 1, 2].map(k => Math.max(...vertices.map(v => v[k]))), span = Math.max(...max.map((v, i) => v - min[i]));
    if (span < 1e-10)
        throw new Error('Mesh has no extent');
    const scale = size / span, center = min.map((v, i) => (v + max[i]) / 2), normalized = vertices.map(v => v.map((x, i) => (x - center[i]) * scale)), triangles = [];
    for (const face of faces) {
        if (face.ids.some(i => i < 0 || i >= vertices.length) || new Set(face.ids).size !== face.ids.length)
            throw new Error(`Missing/duplicate vertex at line ${face.line}`);
        for (const ids of triangulate(face.ids, normalized)) {
            if (triangles.length >= 16000)
                throw new RangeError('OBJ triangulated limit 16000');
            const p = ids.map(i => normalized[i]), a = p[1].map((v, i) => v - p[0][i]), b = p[2].map((v, i) => v - p[0][i]), n = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]], len = Math.hypot(...n), light = .32 + .68 * Math.abs((n[0] * -.35 + n[1] * .8 + n[2] * -.48) / Math.max(1e-10, len));
            const color = [0, 1, 2].map(k => Math.round(ids.reduce((s, id) => s + colors[id][k], 0) / 3 * 255 * Math.min(1, light)));
            triangles.push({ vertices: p.flat(), color: (color[0] << 16) | (color[1] << 8) | color[2] });
        }
    }
    return { version: 1, name: (options.name ?? 'Imported model').slice(0, 128), vertexCount: vertices.length, triangles, warnings: [...warnings], originalBounds: { min, max } };
}

