import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdtempSync,rmSync,mkdirSync,copyFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const checker=new URL('../scripts/check_gallery_cases.mjs',import.meta.url);
let runIndex=0;
const cases=JSON.parse(readFileSync(new URL('./fixtures/gallery-parallel-three.json',import.meta.url)));
function run(input,workers){const dir=mkdtempSync(join(tmpdir(),'nocturne-parallel-'));try{
 const source=join(dir,'cases.json'),output=join(dir,'report.json');writeFileSync(source,JSON.stringify(input));
 const result=spawnSync(process.execPath,[checker.pathname,source,output],{env:{...process.env,NOCTURNE_GALLERY_WORKERS:String(workers)},encoding:'utf8',timeout:120000});
 assert.ifError(result.error);const report=JSON.parse(readFileSync(output,'utf8'));assert.equal(report.casesSha256,createHash('sha256').update(readFileSync(source)).digest('hex'));
 const value={code:result.status,report,summary:JSON.parse(result.stdout)};if(process.env.NOCTURNE_PARALLEL_EVIDENCE)writeFileSync(join(process.env.NOCTURNE_PARALLEL_EVIDENCE,`run-${++runIndex}-workers${workers}.json`),JSON.stringify(value,null,2)+'\n');return value;
 }finally{rmSync(dir,{recursive:true,force:true});}}
const semantic=r=>({expectedCaseIds:r.report.expectedCaseIds,cases:r.report.cases.map(({seconds,...row})=>row),complete:r.report.complete,passed:r.report.passed,status:r.report.status,samples:r.summary.samples});
test('actual three original cases serial and four workers are equivalent',()=>{
 const serial=run(cases,1),parallel=run(cases,4);assert.equal(serial.code,0);assert.equal(parallel.code,0);assert.deepEqual(semantic(serial),semantic(parallel));assert.equal(parallel.report.workers,4);assert.equal(new Set(parallel.report.workerThreadIds).size,4);
 for(const key of ['wasmSha256','checkerSha256','workerSha256','bindingSha256','casesSha256'])assert.equal(serial.report[key],parallel.report[key],key);
 assert.equal(parallel.report.cases.length,3);assert.equal(parallel.summary.samples,9);
});
test('invalid middle case remains failed and all other actual cases execute',()=>{
 const invalid=structuredClone(cases);invalid[1].commands.push({op:'deliberately-invalid-native-command'});
 const serial=run(invalid,1),parallel=run(invalid,4);assert.equal(serial.code,1);assert.equal(parallel.code,1);assert.deepEqual(semantic(serial),semantic(parallel));assert.equal(parallel.report.complete,true);assert.equal(parallel.report.passed,false);assert.deepEqual(parallel.report.cases.map(x=>x.status),['PASS','FAIL','PASS']);assert.ok(parallel.report.cases[1].error.length);
});

test('actual worker startup error fails incomplete and terminates the pool',()=>{
 const dir=mkdtempSync(join(tmpdir(),'nocturne-bad-worker-'));try{
  for(const folder of ['scripts','bindings/typescript','dist'])mkdirSync(join(dir,folder),{recursive:true});
  for(const file of ['scripts/check_gallery_cases.mjs','scripts/gallery_case_worker.mjs','bindings/typescript/native_scene.mjs','bindings/typescript/gallery_resources.mjs'])copyFileSync(new URL('../'+file,import.meta.url),join(dir,file));
  writeFileSync(join(dir,'dist/nocturne_native.wasm'),Buffer.from('invalid actual WASM bytes'));
  const source=join(dir,'cases.json'),output=join(dir,'report.json');writeFileSync(source,JSON.stringify(cases));
  const result=spawnSync(process.execPath,[join(dir,'scripts/check_gallery_cases.mjs'),source,output],{env:{...process.env,NOCTURNE_GALLERY_WORKERS:'4'},encoding:'utf8',timeout:15000});assert.ifError(result.error);assert.equal(result.status,1);
  const report=JSON.parse(readFileSync(output,'utf8'));assert.equal(report.complete,false);assert.equal(report.passed,false);assert.equal(report.status,'FAIL');assert.match(report.infrastructureError.error,/WebAssembly|CompileError/);assert.equal(report.resourceHelperSha256,createHash('sha256').update(readFileSync(join(dir,'bindings/typescript/gallery_resources.mjs'))).digest('hex'));assert.deepEqual(report.expectedCaseIds,cases.map(x=>x.id));assert.equal(report.cases.length,0);
  if(process.env.NOCTURNE_PARALLEL_EVIDENCE)writeFileSync(join(process.env.NOCTURNE_PARALLEL_EVIDENCE,'actual-worker-startup-failure.json'),JSON.stringify(report,null,2)+'\n');
 }finally{rmSync(dir,{recursive:true,force:true});}
});

test('worker configuration above four is rejected before execution',()=>{
 const result=spawnSync(process.execPath,[checker.pathname,new URL('./fixtures/gallery-parallel-three.json',import.meta.url).pathname],{env:{...process.env,NOCTURNE_GALLERY_WORKERS:'5'},encoding:'utf8',timeout:15000});assert.ifError(result.error);assert.equal(result.status,1);assert.match(result.stderr,/integer in1\.\.4/);
});
