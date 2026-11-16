import fs from 'node:fs';

const [wasmPath, casePath] = process.argv.slice(2);
const value = JSON.parse(fs.readFileSync(casePath, 'utf8'));
const { instance } = await WebAssembly.instantiate(fs.readFileSync(wasmPath), {});
const e = instance.exports;
const memory = new DataView(e.memory.buffer);
const cells = new Uint32Array(e.memory.buffer);
const depths = new Float64Array(e.memory.buffer);
const vertexPtr = 2097152, texturePtr = 2098000, surfacePtr = 2100000, depthPtr = 2200000;
for (let i = 0; i < value.vertices.length; ++i) {
  const v = value.vertices[i], base = vertexPtr / 8 + i * 6;
  [v.x, v.y, v.z, v.u, v.v, v.opacity].forEach((n, j) => memory.setFloat64((base + j) * 8, n, true));
}
value.texture.forEach((n, i) => { cells[texturePtr / 4 + i] = n >>> 0; });
value.surface.forEach((n, i) => { cells[surfacePtr / 4 + i] = n >>> 0; });
value.depth.forEach((n, i) => { depths[depthPtr / 8 + i] = n; });
const status = e.nrWindowTextureTriangle(vertexPtr, value.shape, value.iris,
  value.visibility, value.hitId, value.textureWidth, value.textureHeight,
  texturePtr, value.surfaceWidth, value.surfaceHeight, value.clip[0],
  value.clip[1], value.clip[2], value.clip[3], surfacePtr, depthPtr);
const out = {
  status,
  surface: status === 0 ? Array.from(cells.slice(surfacePtr / 4,
    surfacePtr / 4 + value.surfaceWidth * value.surfaceHeight * 4)) : value.surface,
  depth: status === 0 ? Array.from(depths.slice(depthPtr / 8,
    depthPtr / 8 + value.surfaceWidth * value.surfaceHeight)) : value.depth,
  shapes: value.shapeQueries.map(([shape, u, v]) => e.nrWindowTextureShapeContains(shape,
    u === '__nan__' ? Number.NaN : u, v === '__nan__' ? Number.NaN : v)),
};
process.stdout.write(JSON.stringify(out));
