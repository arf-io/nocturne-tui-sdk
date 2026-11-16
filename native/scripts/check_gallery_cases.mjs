import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,renameSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';
// Each worker executes the unchanged assertions against its own real WASM context.
const source=readFileSync(process.argv[2]),cases=JSON.parse(source),ids=cases.map(study=>study.id);
if(!ids.length||ids.some(id=>typeof id!=='string'||!id)||new Set(ids).size!==ids.length)throw Error('Gallery requires nonempty unique case identities');
const setting=process.env.NOCTURNE_GALLERY_WORKERS??'4';
if(!/^[1-9]\d*$/.test(setting)||Number(setting)>4)throw Error('NOCTURNE_GALLERY_WORKERS must be an integer in1..4');
const workers=Number(setting),wasmURL=new URL('../dist/nocturne_native.wasm',import.meta.url),wasm=readFileSync(wasmURL);
const workerURL=new URL('./gallery_case_worker.mjs',import.meta.url),hash=value=>createHash('sha256').update(value).digest('hex');
const identity={runtime:'actual WASM',wasmSha256:hash(wasm),casesSha256:hash(source),checkerSha256:hash(readFileSync(new URL(import.meta.url))),workerSha256:hash(readFileSync(workerURL)),bindingSha256:hash(readFileSync(new URL('../bindings/typescript/native_scene.mjs',import.meta.url))),resourceHelperSha256:hash(readFileSync(new URL('../bindings/typescript/gallery_resources.mjs',import.meta.url))),scope:'Authored gallery runtime assertions; not complete option or artistic acceptance',workers,executionBackend:'node:worker_threads',workerThreadIds:[]};
const report={expectedCaseIds:ids,cases:[],complete:false,passed:false,status:'RUNNING'},rows=Array(cases.length),pool=[];
let samples=0,next=0,completed=0,stopping=false,abort;
const interrupt=()=>abort?.(Error('Gallery qualification interrupted'));
function persist(){if(!process.argv[3])return;writeFileSync(process.argv[3]+'.tmp',JSON.stringify({...report,...identity},null,2)+'\n');renameSync(process.argv[3]+'.tmp',process.argv[3]);}
persist();
try{
 await new Promise((resolve,reject)=>{
  let ready=0;
  const fail=error=>{if(!stopping){stopping=true;reject(error);}};abort=fail;process.once('SIGINT',interrupt);process.once('SIGTERM',interrupt);
  const dispatch=entry=>{if(stopping||next>=cases.length)return;entry.index=next++;entry.worker.postMessage({index:entry.index,study:cases[entry.index]});};
  for(let n=0;n<workers;n++){
   const worker=new Worker(workerURL,{workerData:{wasm}}),entry={worker,index:null,ready:false};pool.push(entry);
   worker.on('error',fail);worker.on('exit',code=>{if(!stopping)fail(Error(`Gallery worker exited unexpectedly (${code})`));});
   worker.on('message',message=>{try{
    if(message.kind==='ready'){
     assert.equal(entry.ready,false,'Duplicate worker readiness');assert.equal(message.wasmSha256,identity.wasmSha256,'Worker runtime identity mismatch');entry.ready=true;identity.workerThreadIds.push(message.threadId);ready++;
     if(ready===workers){identity.workerThreadIds.sort((a,b)=>a-b);persist();pool.forEach(dispatch);}
     return;
    }
    assert.equal(message.kind,'result','Unknown worker response');assert.equal(message.index,entry.index,'Worker case identity mismatch');assert.ok(!rows[message.index],'Duplicate worker result');assert.equal(message.row.id,ids[message.index]);assert.ok(['PASS','FAIL'].includes(message.row.status));assert.equal(message.row.renderPure,message.row.status==='PASS');assert.equal(message.row.partitionReplay,message.row.status==='PASS');assert.ok(Number.isInteger(message.samples)&&message.samples>=0);assert.equal(message.row.samples,message.samples);if(message.row.status==='PASS')assert.equal(message.row.samples,cases[message.index].sampleTimesUs.length);
    rows[message.index]=message.row;entry.index=null;completed++;samples+=message.samples;report.cases=rows.filter(Boolean);persist();
    if(completed===cases.length){stopping=true;resolve();}else dispatch(entry);
   }catch(error){fail(error);}});
  }
 });
 identity.wasmSha256After=hash(readFileSync(wasmURL));assert.equal(identity.wasmSha256After,identity.wasmSha256,'Runtime changed during qualification');
 report.complete=completed===ids.length;report.passed=report.complete&&report.cases.every(row=>row.status==='PASS');report.status=report.passed?'PASS':'FAIL';persist();
}catch(error){report.status='FAIL';report.infrastructureError={errorType:error.name,error:String(error.message)};persist();process.exitCode=1;}
finally{stopping=true;await Promise.all(pool.map(({worker})=>worker.terminate()));process.removeListener('SIGINT',interrupt);process.removeListener('SIGTERM',interrupt);}
console.log(JSON.stringify({runtime:'actual WASM',cases:cases.length,samples,passed:report.passed,failed:report.cases.filter(row=>row.status==='FAIL'),...(report.infrastructureError?{infrastructureError:report.infrastructureError}:{}),renderPure:report.passed,partitionReplay:report.passed}));
if(!report.passed)process.exitCode=1;
