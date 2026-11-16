import fs from 'node:fs';
import assert from 'node:assert/strict';
const binary=fs.readFileSync(process.argv[2]),module=await WebAssembly.compile(binary);
assert.equal(WebAssembly.Module.imports(module).length,0);
const {exports:e}=await WebAssembly.instantiate(module,{});
const source=Array.from('Aé👩‍🔧🇺🇸\t\r\n'.repeat(30001),c=>c.codePointAt(0));
assert.equal(source.length,330011);
const src=e.nrAlloc(source.length*4),n=180006;
new Uint32Array(e.memory.buffer,src,source.length).set(source);
assert.equal(e.nrGraphemeBreaks(src,source.length,0,0),n+1);
const boundaries=e.nrAlloc((n+1)*4);
assert.equal(e.nrGraphemeBreaks(src,source.length,boundaries,n+1),n+1);
const b=new Uint32Array(e.memory.buffer,boundaries,n+1);
for(let k=0;k<30001;k++)for(let j=0;j<6;j++)assert.equal(b[k*6+j],k*11+[0,1,3,6,8,9][j]);
assert.equal(b[n],source.length);
const rows=e.nrAlloc(n*20);
assert.equal(e.nrDocumentGraphemeLayout(src,source.length,1,10,rows,n),n);
const out=new Uint32Array(e.memory.buffer,rows,n*5),patterns=[[0,1,0,1],[1,3,1,1],[3,6,2,2],[6,8,4,2],[8,9,6,2],[9,11,8,0]];
for(let k=0;k<30001;k++)for(let j=0;j<6;j++){
 const [a,z,x,w]=patterns[j],i=(k*6+j)*5;
 assert.deepEqual(Array.from(out.subarray(i,i+5)),[11*k+a,11*k+z,x,k,w]);
}
for(const [name,want]of [['Before',330003],['After',330006],['Floor',330003]])assert.equal(e['nrGrapheme'+name](src,source.length,330005),want);
const reject=e.nrAlloc(30*4),sentinel=new Uint32Array(e.memory.buffer,reject,30);sentinel.fill(0xdeadbeef);
assert.equal(e.nrDocumentGraphemeLayout(src,source.length,1,10,reject,6),-1);
new Uint32Array(e.memory.buffer,src,source.length)[source.length-1]=0xd800;
assert.equal(e.nrGraphemeBreaks(src,source.length,reject,30),-1);
assert.deepEqual(Array.from(sentinel),Array(30).fill(0xdeadbeef));
console.log(JSON.stringify({status:'PASS',sourceScalars:source.length,exactClusters:n,exactLayoutWords:n*5,imports:0}));
