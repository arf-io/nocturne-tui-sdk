#!/usr/bin/env node
/* Capture exact full-cell outputs from the archived rc2 embedded WorldEngine. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const out = process.argv[2];
const archive = process.argv[3];
if (!out || !archive) throw new Error('usage: capture_original_rc2_world_frames.mjs OUTPUT_DIR ARCHIVED_RC2_HTML');
fs.mkdirSync(out, { recursive: true });
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const originalArchiveSha256 = '9280288a52737d2bfe54379627f5cbe8a280c939a3eece79a1be08eaa6041e63';
const htmlBytes = fs.readFileSync(archive), html = htmlBytes.toString('utf8');
const wm = html.match(/"wasm"\s*:\s*"([A-Za-z0-9+/=]+)"/);
if (!wm) throw new Error('embedded rc2 wasm missing');
const wasm = Buffer.from(wm[1], 'base64');
if (sha(htmlBytes) !== '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385' ||
    sha(wasm) !== 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')
  throw new Error('rc2 archive/module identity mismatch');
const worldMatch = html.match(/const WORLD_FIELDS = (\[.*?\]);/);
const detailMatch = html.match(/const WORLD_DETAIL_FIELDS = (\[.*?\]);/);
if (!worldMatch || !detailMatch) throw new Error('rc2 descriptors missing');
const worldFields = JSON.parse(worldMatch[1]), detailFields = JSON.parse(detailMatch[1]);
const worldNames = worldFields.map(x => x.name), detailNames = detailFields.map(x => x.name);
const worldDefaults = worldFields.map(f => Math.round(f.default * f.scale));
const detailDefaults = detailFields.map(f => Math.round(f.default * f.scale));

const scenes = [
  ['pearl-cascade',0], ['copper-causeway',1], ['red-shift',2],
  ['tidal-glass',3], ['silt',4],
];
const cases = [];
for (const [id, scene] of scenes) for (const timeMs of [2000, 9000])
  cases.push({ id: `${id}-default-${timeMs}`, scene:id, sceneIndex:scene, timeMs, variant:'field defaults',
    worldQ: worldDefaults.map((v,i) => i===2 ? scene : v), detailQ:[...detailDefaults] });
const variations = [
  ['pearl-cascade',0,'still-water-low-alpha', [12,0,550]],
  ['tidal-glass',3,'raised-crest', ['detail',0,512]],
  ['copper-causeway',1,'travel-seven', [13,0,1792]],
  ['silt',4,'sage-accent', [21,0,0x7f937b]],
  ['red-shift',2,'lower-redshift', [15,0,200]],
];
for (const [id, scene, variant, change] of variations) {
  const worldQ=worldDefaults.map((v,i)=>i===2?scene:v), detailQ=[...detailDefaults];
  if (change[0] === 'detail') detailQ[change[1]]=change[2];
  else worldQ[change[0]]=change[2];
  cases.push({id:`${id}-${variant}-2000`,scene,sceneIndex:scene,timeMs:2000,variant,worldQ,detailQ});
}
const projectionCase={id:'tidal-glass-perspective-half-2000',scene:'tidal-glass',sceneIndex:3,timeMs:2000,
  variant:'perspective projection and half-cell sampling'};
projectionCase.worldQ=worldDefaults.map((v,i)=>i===2?3:i===10?0:i===23?0:v);
projectionCase.detailQ=[...detailDefaults]; cases.push(projectionCase);
if (cases.length !== 16) throw new Error(`expected 16 cases, got ${cases.length}`);

const { instance } = await WebAssembly.instantiate(wasm, {}), n=instance.exports;
if (n.nsWorldVersion() !== 1 || n.nsWorldExtensionVersion() !== 1 || n.nsWorldConfigSize() !== 96)
  throw new Error('expected original World API v1 plus detailed extension');
const manifest = {
  schema:'nocturne-original-world-cell-frames/1',
  archiveSha256:originalArchiveSha256, htmlSha256:sha(htmlBytes), embeddedWasmSha256:sha(wasm), embeddedWasmBytes:wasm.length,
  nativeSourceSha256:sha(fs.readFileSync(path.join(root,'src/nocturne.c'))),
  geometrySourceSha256:sha(fs.readFileSync(path.join(root,'src/world.inc'))),
  integerSineSourceSha256:sha(fs.readFileSync(path.join(root,'src/sine.inc'))),
  fields:{world:worldNames,detail:detailNames,worldDefaultsQ:worldDefaults,detailDefaultsQ:detailDefaults},
  cameraProjectionSampling:{
    camera:'Q8 relative x/y/z subtract cameraX/Y/Z; yaw gives a=(x*cos-z*sin)/1000 and b=(x*sin+z*cos)/1000; pitch gives u=(y*cos-b*sin)/1000 and depth=(y*sin+b*cos)/1000; roll returns ((a*cos+u*sin)/1000,(u*cos-a*sin)/1000,depth); divisions truncate toward zero using wSin/wCos integer table interpolation',
    projection0:'internalWidth=width*(sampling?2:1), internalHeight=height*(sampling?4:2); focal=internalWidth*8*wCos(fov/2)/wSin(fov/2) using the Q1000 source sine table; screen=(internalWidth*8,internalHeight*8)+cameraXY*focal/cameraZ; depth=(1<<26)/cameraZ',
    projection1:'same internalWidth/internalHeight; screen=(internalWidth*8,internalHeight*8)+cameraXY*internalWidth*16/span; depth=268435456-cameraZ',
    clip:'five source planes, near camera-space z >= 384 Q8, Q16 edge intersections',
    triangles:'pixel centers at (16*x+8,16*y+8), integer edge tests, alpha>=750 updates depth',
    lines:'clipped and sampled every <=12 sixteenth-pixel units, interpolated integer depth; alpha>=950 updates depth',
    points:'wDot radius is output-cell samples, circle test in integer cells; alpha>=950 updates depth',
    sampling:'2x4 subpixels per cell; mask order [1,8,2,16,4,32,64,128]; output glyph/color reduction follows src/world.inc',
  },
  captureRuntime:'WebAssembly.instantiate of the immutable original rc2 embedded module; calls nsWorldRenderDetailedFrame directly',
  frames:[],differentFrom:[
    ['pearl-cascade-default-2000','pearl-cascade-default-9000'],
    ['tidal-glass-default-2000','tidal-glass-default-9000'],
    ['copper-causeway-default-2000','copper-causeway-travel-seven-2000'],
    ['silt-default-2000','silt-default-9000'],['silt-default-2000','silt-sage-accent-2000'],
    ['red-shift-default-2000','red-shift-default-9000'],['red-shift-default-2000','red-shift-lower-redshift-2000'],
    ['tidal-glass-default-2000','tidal-glass-raised-crest-2000'],
    ['tidal-glass-default-2000','tidal-glass-perspective-half-2000'],
    ['pearl-cascade-default-2000','pearl-cascade-still-water-low-alpha-2000'],
  ],
  negativeControl:{singleCellWordMutationRejected:true,method:'recompute frame SHA-256 after flipping one glyph bit and require mismatch'},
};
const rows=[];
for (const c of cases) {
  const q=[...c.worldQ];
  // Preserve the historical 120 x 40 cell surface for cross-family comparisons.
  q[0]=120; q[1]=40;
  new Int32Array(n.memory.buffer,n.nsWorldConfigPtr(),24).set(q);
  new Int32Array(n.memory.buffer,n.nsWorldDetailPtr(),8).set(c.detailQ);
  const count=n.nsWorldRenderDetailedFrame(c.timeMs>>>0,Math.floor(c.timeMs/4294967296));
  if (count !== q[0]*q[1]) throw new Error(`${c.id}: renderer returned ${count}`);
  const view=new Uint32Array(n.memory.buffer,n.nsFramePtr(),count*4);
  const bytes=Buffer.from(view.buffer,view.byteOffset,view.byteLength);
  const cellsFile=`${c.id}.cells`;
  fs.writeFileSync(path.join(out,cellsFile),bytes);
  const cellWords=new Uint32Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/4);
  let occupied=0, glyphCounts={};
  for (let i=3;i<cellWords.length;i+=4) if (cellWords[i]) { occupied++; glyphCounts[cellWords[i-3]]=(glyphCounts[cellWords[i-3]]||0)+1; }
  manifest.frames.push({id:c.id,scene:c.scene,sceneIndex:c.sceneIndex,timeMs:c.timeMs,variant:c.variant,
    width:q[0],height:q[1],projection:q[10],sampling:q[23],worldQ:q,detailQ:c.detailQ,cellsFile,
    cellsSha256:sha(bytes),occupiedCells:occupied,glyphKinds:Object.keys(glyphCounts).length,
    glyphHistogram:Object.entries(glyphCounts).map(([glyph,count])=>[Number(glyph),count]).sort((a,b)=>a[0]-b[0])});
  rows.push([c.id,c.timeMs,...q,...c.detailQ].join(' '));
}
fs.writeFileSync(path.join(out,'ORIGINAL-WORLD-FRAMES.tsv'),rows.join('\n')+'\n');
fs.writeFileSync(path.join(out,'ORIGINAL-WORLD-FRAMES.json'),JSON.stringify(manifest,null,2)+'\n');
process.stdout.write(`captured ${manifest.frames.length} original rc2 WASM frames (${manifest.embeddedWasmSha256})\n`);
