import fs from 'node:fs';import assert from 'node:assert/strict';
const module=await WebAssembly.compile(fs.readFileSync(process.argv[2]));assert.equal(WebAssembly.Module.imports(module).length,0);
const {exports:e}=await WebAssembly.instantiate(module,{});
function layout(text){const scalars=Array.from(text,c=>c.codePointAt(0)),n=scalars.length;
 const source=e.nrAlloc(n*4),out=e.nrAlloc(n*28),scratch=e.nrAlloc(40*(n+1)*4);
 new Uint32Array(e.memory.buffer,source,n).set(scalars);
 const count=e.nrDocumentBidiClusterLayout(source,n,1,0xffffffff,2,out,n,scratch,BigInt(40*(n+1)));
 assert.equal(count,n);return new Uint32Array(e.memory.buffer,out,count*7);}
const text='אב'+' '.repeat(70000)+'Z',rows=layout(text);
for(let x=0;x<70003;x++)assert.deepEqual(Array.from(rows.subarray(x*7,x*7+7)),[70002-x,70003-x,x,0,1,x===0?2:1,text.codePointAt(70002-x)]);
const many=layout('אב\n'.repeat(25001));
for(let k=0;k<25001;k++)for(let j=0;j<3;j++)assert.deepEqual(Array.from(many.subarray((k*3+j)*7,(k*3+j+1)*7)),[[k*3+2,k*3+3,0,k,0,1,10],[k*3+1,k*3+2,0,k,1,1,0x5d1],[k*3,k*3+1,1,k,1,1,0x5d0]][j]);
console.log(JSON.stringify({status:'PASS',singleParagraphScalars:70003,separateParagraphs:25001,imports:0}));
