// RC4-026 mirror of test_status_notifications_acceptance.py through the
// import-free WASM build of the same C core. Each case repeats the native
// assertions; the recorded parity script is replayed natively by the Python
// test, which compares exact snapshot and frame bytes.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),wasm=readFileSync(process.argv[2]?resolve(process.argv[2]):resolve(root,'dist/nocturne_native.wasm'));
const imports=WebAssembly.Module.imports(await WebAssembly.compile(wasm)).length;
assert.equal(imports,0,'WASM must be import-free');
const sha=b=>createHash('sha256').update(b).digest('hex');
const same=(a,b)=>a.length===b.length&&Buffer.from(a).equals(Buffer.from(b));
const hitId=(message,slot=0)=>((0x63<<24)|(message<<2)|slot)>>>0;
let open=[];
const closeAll=()=>{for(const s of open)s.close();open=[];};
async function baseline(seed=18){const s=await NativeScene.create(wasm,seed);open.push(s);s.command({op:'environment',stars:0});s.command({op:'prompt',active:false});return s;}
const area=(s,id=1,f={})=>s.command({op:'area',id,x:2,y:3,width:30,height:6,border:'none',padding:0,alpha:0,layout:'ordered',gapMs:0,...f});
function status(s,id,f={}){const o={op:'status',area:1,text:'Notice',durationMs:0};if(id!=null)o.id=id;if('dwellPerCharacterMs' in f)delete o.durationMs;return s.command({...o,...f});}
const action=(id=1,f={})=>({id,label:'Go',event:'/task/go',...f});
const info=s=>s.infoComplete(),record=(s,id)=>info(s).messages.find(m=>m.id===id);
const states=s=>Object.fromEntries(info(s).messages.map(m=>[m.id,m.state]));
const activate=(s,id,actionId=1)=>s.command({op:'notification-action',id,actionId});
function rejects(s,command){const before=s.snapshot();assert.throws(()=>s.command(command),RangeError,JSON.stringify(command));assert.ok(same(before,s.snapshot()),'atomic '+JSON.stringify(command));}
function cells(frame,predicate){const out=[];for(let i=0;i<frame.width*frame.height;i++){const w=frame.cells.subarray(i*4,i*4+4);if(predicate(w))out.push([i%frame.width,Math.floor(i/frame.width)]);}return out;}
const word=(frame,x,y)=>frame.cells.subarray((y*frame.width+x)*4,(y*frame.width+x)*4+4);
const cases={};

cases['documented-intent-shape']=async()=>{const s=await baseline();area(s,2);
  s.command({op:'status',id:40,area:2,text:'Build requires review',important:true,mode:'pop',durationMs:0,actions:[{id:1,label:'Inspect',event:'/build/inspect',value:40}]});
  activate(s,40);assert.deepEqual(info(s).intents,[{id:1,messageId:40,actionId:1,messageSequence:1,event:'/build/inspect',value:40,atUs:0}]);};

cases['consumed-action-owns-press']=async()=>{const s=await baseline();area(s,1,{x:4,y:4,width:40,height:8,layout:'queue'});
  status(s,1,{text:'Build needs review',actions:[action(1,{label:'Review',event:'/build/review'})]});
  const frame=s.render(),letters=new Set([...'Review'].map(c=>c.codePointAt(0)));
  const label=cells(frame,w=>w[3]===hitId(1)&&letters.has(w[0]));assert.equal(label.length,6);
  activate(s,1);const consumed=s.render();
  assert.deepEqual(label.map(([x,y])=>word(consumed,x,y)[0]),label.map(([x,y])=>word(frame,x,y)[0]));
  const before=info(s),[x,y]=label[3];
  for(const [phase,dx,dy] of [['down',0,0],['move',6,1],['up',6,1]])s.command({op:'pointer',phase,x:x+dx,y:y+dy});
  const after=info(s);for(const k of ['intents','messages','camera','fieldCount'])assert.deepEqual(after[k],before[k],k);};

cases['content-overflow-reported']=async()=>{const long='Too long for the area to show';
  async function needs(texts,{mode='static',height=2,width=12,border='none',actions=[]}={}){const s=await baseline();area(s,1,{width,height,border});
    texts.forEach((text,i)=>status(s,i+1,{text,mode,actions}));s.render();const m=info(s);s.close();
    assert.deepEqual(m.messages.sort((a,b)=>a.id-b.id).map(r=>r.text),texts);return m.render.contentNeedsReader;}
  assert.equal(await needs(['Fits'],{height:4,actions:[action(1,{label:'Inspect'})]}),0);
  assert.ok(await needs(['Fits'],{actions:[action(1,{label:'Inspect'})]})>=1);
  for(const mode of ['static','pop','fade','horizontal','vertical','horizontal-fade','vertical-fade'])assert.ok(await needs([long+'\n'+long],{mode})>=1,mode);
  assert.ok(await needs(['first','second'],{height:1})>=1);assert.ok(await needs(['x'],{width:2,border:'square'})>=1);};

cases['scheduled-activation-boundary']=async()=>{const command={op:'notification-action',id:1,actionId:1};
  for(const chunks of [[1000000],[996000,1000000],[500000,999999,1000000]]){const s=await baseline();
    status(s,1,{area:0,durationMs:1000,actions:[action()]});s.schedule(9,1000000,command);
    assert.throws(()=>{for(const t of chunks)s.advanceTo(t);},RangeError);assert.deepEqual(info(s).intents,[]);}
  const s=await baseline();status(s,1,{area:0,durationMs:1000,actions:[action()]});s.advanceTo(1000000);rejects(s,command);};

cases['scheduled-status-chunk-invariance']=async()=>{const r={op:'status',area:0,text:'tick',key:'k',coalesce:'count',durationMs:995};
  async function run(chunks){const s=await baseline();s.command({...r,id:1});s.schedule(9,1000000,r);for(const t of chunks)s.advanceTo(t);return s;}
  const frames=[];for(let t=16667;t<2000000;t+=16667)frames.push(t);frames.push(2000000);
  const runs=[await run([2000000]),await run([996000,2000000]),await run(frames)];
  for(const s of runs){assert.deepEqual(info(s).messages.map(m=>[m.id,m.state,m.occurrences,m.startUs]).sort((a,b)=>a[0]-b[0]),[[1,'expired',1,0],[2,'expired',1,1000000]]);
    assert.ok(same(s.snapshot(),runs[0].snapshot()),'chunking changed the snapshot');}};

cases['nonpreemptive-priority-queue']=async()=>{const s=await baseline();area(s,1,{layout:'queue'});
  for(const [id,priority] of [[1,0],[2,0],[3,50],[4,50]])status(s,id,{text:'m'+id,durationMs:1000,priority});
  s.advanceTo(1500000);assert.equal(states(s)[3],'active');status(s,5,{text:'urgent',durationMs:1000,priority:100});
  assert.deepEqual([states(s)[3],states(s)[5]],['active','queued']);s.advanceTo(4000000);
  assert.deepEqual([1,3,5,4,2].map(i=>record(s,i).startUs),[0,1000000,2000000,3000000,4000000]);};

cases['history-capacity']=async()=>{const s=await baseline();area(s);status(s,1,{text:'Warning',important:true});
  for(let id=2;id<=48;id++)status(s,id,{text:'m'+id});
  rejects(s,{op:'status',id:49,area:1,text:'overflow',durationMs:0});rejects(s,{op:'status',area:1,text:'overflow',durationMs:0});
  s.command({op:'dismiss',id:3});s.command({op:'purge-status',id:3});status(s,49,{text:'after purge'});
  assert.equal(info(s).messages.length,48);assert.deepEqual([record(s,1).important,record(s,1).acknowledged],[true,false]);};

cases['same-event-watermark-debounce']=async()=>{const s=await baseline();s.command({op:'define',path:'/enabled',value:1});s.command({op:'define',path:'/out',value:0});
  const rule=f=>s.command({op:'trigger',id:1,event:'/task/approved',target:'/out',when:{path:'/enabled',comparison:'equal',value:1},action:'increment',value:1,...f});
  const approve=id=>{status(s,id,{area:0,actions:[action(1,{event:'/task/approved'})]});activate(s,id);};
  const t=()=>info(s).triggers[0],out=()=>info(s).values['/out'];
  rule({debounceMs:100});approve(1);s.advanceTo(100000);assert.deepEqual([out(),t().lastIntent,t().fireCount],[1,1,1]);
  approve(2);s.advanceTo(150000);rule({debounceMs:100,value:10});assert.deepEqual([t().lastIntent,t().fireCount],[1,1]);
  s.advanceTo(200000);assert.equal(out(),1);s.advanceTo(300000);assert.deepEqual([out(),t().lastIntent,t().fireCount],[11,2,2]);
  s.advanceTo(600000);assert.equal(out(),11);};

cases['snapshot-round-trip']=async()=>{const s=await baseline();area(s,1,{layout:'queue',gapMs:100});
  status(s,null,{text:'first',durationMs:1000,actions:[action(1),action(2,{label:'Two'})]});status(s,null,{text:'second',durationMs:1000,priority:5});
  status(s,null,{text:'third',durationMs:1000,key:'k',coalesce:'replace-queued'});status(s,null,{text:'third v2',durationMs:1000,key:'k',coalesce:'replace-queued'});
  status(s,10,{area:0,text:'important',important:true});for(let i=0;i<2;i++)status(s,null,{area:0,text:'tele',key:'t',coalesce:'count',durationMs:5000});
  activate(s,1,1);const saved=s.snapshot(),r=await baseline(99);r.restore(saved);assert.ok(same(r.snapshot(),saved));
  for(const q of [s,r]){status(q,null,{area:0,text:'after restore'});activate(q,1,1);activate(q,1,2);q.advanceTo(2500000);}
  assert.ok(same(r.snapshot(),s.snapshot()));assert.equal(record(r,5).text,'after restore');
  assert.deepEqual(info(r).intents.map(q=>[q.id,q.actionId]),[[1,1],[2,2]]);assert.deepEqual([record(r,3).text,record(r,3).startUs,record(r,3).state],['third v2',2200000,'active']);};

cases['render-and-read-purity']=async()=>{const s=await baseline();area(s,1,{layout:'queue'});
  status(s,1,{text:'first',durationMs:1000,actions:[action()]});status(s,2,{text:'second',durationMs:1000});activate(s,1);s.advanceTo(999999);
  const saved=s.snapshot();for(let i=0;i<3;i++){s.render();s.info();s.infoComplete();s.inspectCharacterCell(2,3);}
  assert.ok(same(s.snapshot(),saved));assert.deepEqual(states(s),{1:'active',2:'queued'});s.advanceTo(1000000);assert.deepEqual(states(s),{1:'expired',2:'active'});};

cases['intent-order-and-ack']=async()=>{const s=await baseline();area(s);
  for(const id of [1,2,3]){status(s,id,{actions:[action()]});activate(s,id);}s.command({op:'ack-intent',id:1});
  status(s,4,{actions:[action()]});activate(s,4);assert.deepEqual(info(s).intents.map(q=>q.id),[2,3,4]);
  const saved=s.snapshot();s.command({op:'ack-intent',id:1});assert.ok(same(saved,s.snapshot()));};

cases['count-coalescing-live-only']=async()=>{const s=await baseline();area(s);const base={text:'Compile',key:'k',coalesce:'count',durationMs:1000,actions:[action()]};
  status(s,1,base);s.advanceTo(300000);status(s,null,base);assert.deepEqual([record(s,1).occurrences,record(s,1).startUs],[2,0]);
  rejects(s,{op:'status',area:1,...base,priority:5});s.advanceTo(1000000);status(s,null,base);
  assert.deepEqual(info(s).messages.map(m=>[m.id,m.state,m.occurrences]).sort((a,b)=>a[0]-b[0]),[[1,'expired',2],[2,'active',1]]);};

cases['replace-queued-identity']=async()=>{const s=await baseline();area(s,1,{layout:'queue'});const p={key:'progress',coalesce:'replace-queued',durationMs:1000};
  status(s,null,{text:'10%',...p});status(s,null,{text:'20%',...p});const queued=record(s,2);status(s,null,{text:'30%',...p});
  assert.deepEqual([record(s,2).text,record(s,2).sequence,record(s,2).replacements,record(s,1).text],['30%',queued.sequence,1,'10%']);};

cases['important-guard']=async()=>{const s=await baseline();area(s);status(s,9,{text:'Warning',important:true});
  rejects(s,{op:'status',id:9,area:1,text:'Overwrite',durationMs:0});s.command({op:'dismiss',id:9});
  rejects(s,{op:'purge-status',id:9});rejects(s,{op:'clear',scope:'status'});s.command({op:'ack-status',id:9});
  s.command({op:'clear',scope:'status'});assert.deepEqual(info(s).messages,[]);};

// Parity script: executed here, recorded with the coordinates the WASM frame
// produced, replayed natively by the Python test.
async function parity(){const s=await baseline(),script=[];
  const step=entry=>{script.push(entry);if(entry.command)return s.command(entry.command);if(entry.render)return s.render();return s.advanceTo(entry.advanceTo);};
  for(const command of [
    {op:'area',id:1,x:2,y:3,width:24,height:8,border:'rounded',padding:1,layout:'queue',gapMs:250},
    {op:'area',id:2,x:30,y:3,width:12,height:2,border:'none',padding:0,alpha:0},
    {op:'status',id:1,area:1,text:'Build needs review',durationMs:1000,actions:[{id:1,label:'Review',event:'/build/review',value:7}]},
    {op:'status',id:2,area:1,text:'Queued later',durationMs:1000,priority:5},
    {op:'status',area:2,text:'Too long for the area to show',durationMs:0},
    {op:'status',area:2,text:'tick',key:'t',coalesce:'count',durationMs:995},
    {op:'schedule',id:9,atUs:1000000,command:{op:'status',area:2,text:'tick',key:'t',coalesce:'count',durationMs:995}}])step({command});
  const frame=step({render:true}),[[x,y]]=cells(frame,w=>w[3]===hitId(1)&&w[0]==='v'.codePointAt(0));
  for(const phase of ['down','up'])step({command:{op:'pointer',phase,x,y}});
  step({command:{op:'notification-action',id:1,actionId:1}});step({render:true});
  for(const [phase,dx] of [['down',0],['move',5],['up',5]])step({command:{op:'pointer',phase,x:x+dx,y}});
  step({advanceTo:2000000});const last=step({render:true}),m=info(s);
  assert.equal(m.intents.length,1);assert.ok(m.render.contentNeedsReader>=1);
  return {script,snapshotSha256:sha(s.snapshot()),frameSha256:sha(last.bytes),contentNeedsReader:m.render.contentNeedsReader,messages:m.messages,intents:m.intents};}

// Every case runs; a failure is reported with its message instead of hiding later cases.
const passed=[],failures=[];
for(const [name,run] of Object.entries(cases)){try{await run();passed.push(name);}catch(error){failures.push({case:name,error:String(error.message).split('\n')[0]});}finally{closeAll();}}
let report={passed:false,imports,cases:passed,failures};
if(!failures.length){try{report={passed:true,imports,cases:passed,failures,parity:await parity()};}finally{closeAll();}}
console.log(JSON.stringify(report));
if(!report.passed)process.exitCode=1;
