import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const groups=process.argv[2]==='regression'?[]:process.argv[2]?[process.argv[2]]:['selection','ownership'];
const cases=groups.flatMap(name=>JSON.parse(readFileSync(new URL('../../examples/'+name+'-gallery-scenes.json',import.meta.url))));
const matches=(a,e)=>e&&typeof e==='object'&&!Array.isArray(e)?a&&typeof a==='object'&&Object.entries(e).every(([k,v])=>matches(a[k],v)):Array.isArray(e)?Array.isArray(a)&&a.length===e.length&&e.every((v,i)=>matches(a[i],v)):a===e;
for(const recipe of cases){
 const s=await NativeScene.create(wasm),oracle=recipe.demonstrates.feature==='selection-gallery'?await NativeScene.create(wasm):null;
 try{
  for(const c of recipe.commands){s.command(c);if(oracle&&c.op!=='character-rule')oracle.command(c);}
  const start=s.snapshot();
  const run=()=>{for(const a of recipe.actions){
   s.advanceTo(a.timeUs);const before=s.snapshot();
   if(a.expectedError){assert.throws(()=>s.command(a.command),e=>e.message.includes(a.expectedError));assert.deepEqual(s.snapshot(),before);}else s.command(a.command);
   const info=s.infoComplete();assert.equal(info.prompt.text,recipe.expectedPrompt);
   if(a.expectedInfo)assert.ok(matches(info,a.expectedInfo),recipe.id+' expected info');
   for(const [name,expected] of Object.entries(a.expectedCollections||{})){
    assert.equal(info[name].length,expected.length);
    for(const row of expected){const actual=info[name].find(r=>r.id===row.id);assert.ok(matches(actual,row));if('payload' in row)assert.deepEqual(actual.payload,row.payload);}
   }
   const pure=s.snapshot();s.render();
   for(const cell of a.expectedCharacterCells||[]){const actual=s.inspectCharacterCell(cell.x,cell.y);for(const [k,v] of Object.entries(cell))if(k!=='x'&&k!=='y')assert.equal(actual[k],v);}
   assert.deepEqual(s.snapshot(),pure);
  }};
  run();const final=s.snapshot(),frame=s.render();s.restore(start);run();assert.deepEqual(s.snapshot(),final);assert.deepEqual(s.render(),frame);
  if(oracle){s.restore(start);for(const a of recipe.actions){
   s.advanceTo(a.timeUs);oracle.advanceTo(a.timeUs);if(!a.expectedError)s.command(a.command);
   if(!['character-rule','remove-character-rule'].includes(a.command.op))oracle.command(a.command);
   const baseline=oracle.render(),expected=baseline.cells.slice();
   if(a.paintExpected)for(let x=3;x<6;x++)expected[(3*baseline.width+x)*4+2]^=0xffffff;
   assert.deepEqual(s.render().cells,expected,recipe.id+' independent background bytes');
  }}
 }finally{s.close();oracle?.close();}
}
const s=await NativeScene.create(wasm);
try{for(const c of [{op:'define',path:'/out',value:0},{op:'trigger',id:1,target:'/out',event:'/host/approved',valueFrom:'intentValue',when:{intentValue:{comparison:'above',value:5}}},{op:'emit-intent',event:'/host/approved',value:4},{op:'emit-intent',event:'/host/approved',value:7}])s.command(c);
 assert.equal(s.infoComplete().values['/out'],0);assert.deepEqual(s.infoComplete().intents.map(i=>i.id),[1,2]);
 s.command({op:'ack-intent',id:1});assert.equal(s.infoComplete().values['/out'],0);s.advanceTo(1);assert.equal(s.infoComplete().values['/out'],7);assert.deepEqual(s.infoComplete().intents.map(i=>i.id),[2]);
}finally{s.close();}
console.log('PASS actual WASM'+cases.length+' '+groups.join('/')+' workflows: exact collections, rollback, replay and oldest candidate acknowledgement');
