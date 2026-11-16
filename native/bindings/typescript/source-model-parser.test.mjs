import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {parseOBJ,modelRecordsFromTriangles} from './obj_model.mjs';
import {EXAMPLE_OBJ} from '../../tests/fixtures/source-model/continuity-example-mesh.mjs';
const require=createRequire(import.meta.url);const original=require('../../tests/fixtures/source-model/mesh-obj.cjs');
const a=parseOBJ(EXAMPLE_OBJ),b=original.parseOBJ(EXAMPLE_OBJ);assert.deepEqual(a,b);assert.equal(a.triangles.length,4608);
assert.deepEqual(Buffer.from(modelRecordsFromTriangles(a.triangles)),fs.readFileSync(new URL('../../tests/fixtures/source-model/model-records.bin',import.meta.url)));
const base='v 0 0 0\nv 2 0 0\nv 0 2 0\n';
for(const text of [base+'f -3 -2 -1',base+'f 1/2/3 2/4/5 3/6/7',base+'mtllib private.mtl\nf 1 2 3'])for(const upAxis of ['Y','Z'])assert.deepEqual(parseOBJ(text,{upAxis}),original.parseOBJ(text,{upAxis}));
const large=base+('f 1 2 3\n'.repeat(16002));assert.throws(()=>original.parseOBJ(large));assert.equal(parseOBJ(large).triangles.length,16002);
const largeText='#'+('x'.repeat(4*1024*1024))+'\n'+base+'f 1 2 3';assert.throws(()=>original.parseOBJ(largeText));assert.equal(parseOBJ(largeText).triangles.length,1);
const vertices=base+('v 0 0 0\n'.repeat(32000))+'f 1 2 3';assert.throws(()=>original.parseOBJ(vertices));assert.equal(parseOBJ(vertices).vertexCount,32003);
const polygon=Array.from({length:100},(_,i)=>`v ${Math.cos(i*Math.PI/50)} ${Math.sin(i*Math.PI/50)} 0`).join('\n')+'\nf '+Array.from({length:100},(_,i)=>i+1).join(' ');assert.throws(()=>original.parseOBJ(polygon));assert.equal(parseOBJ(polygon).triangles.length,98);
for(const text of [base+'f 1 1 3',base+'f 1 2 99','v 0 0 0\nv 1 1 0\nv 0 1 0\nv 1 0 0\nf 1 2 3 4','v 0 0 0\nv 2 0 0\nv 2 2 1\nv 0 2 0\nf 1 2 3 4']){assert.throws(()=>original.parseOBJ(text));assert.throws(()=>parseOBJ(text));}
console.log(JSON.stringify({status:'PASS',originalSampleTriangles:4608,originalRecordBytes:184320,largeTriangles:16002,largeVertices:32003,largePolygonVertices:100,largeTextBytes:largeText.length}));
