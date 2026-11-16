import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const lifecycle=await NativeScene.create(wasm);
try{
 lifecycle.command({op:'resize',width:4,height:2});
 for(const [id,path] of [['first','/first'],['second','/second']])
  lifecycle.command({op:'character-region',region:{id,path,cells:[0],indices:[9]}});
 const inspect=()=>{lifecycle.render();return lifecycle.inspectCharacterCell(0,0);};
 assert.equal(inspect().path,'/second');
 lifecycle.command({op:'character-region',region:{id:'first',path:'/replacement',cells:[0],indices:[3]}});
 assert.equal(inspect().path,'/second');
 lifecycle.command({op:'remove-character-region',id:'first'});
 lifecycle.command({op:'character-region',region:{id:'reused',path:'/reused',cells:[0],indices:[4]}});
 const saved=lifecycle.snapshot();assert.equal(inspect().path,'/second');
 lifecycle.command({op:'remove-character-region',id:'second'});
 const cell=inspect();assert.equal(cell.path,'/reused');assert.equal(cell.index,4);
 lifecycle.restore(saved);assert.equal(inspect().path,'/second');
 lifecycle.command({op:'reset'});lifecycle.command({op:'resize',width:4,height:2});
 const region={id:'shape',path:'/shape',rect:{x:0,y:0,width:4,height:2},cells:[],indices:[]};
 lifecycle.command({op:'character-region',region});assert.notEqual(inspect().path,'/shape');
 lifecycle.command({op:'character-region',region:{...region,cells:[0,4294967295,0],indices:[3,7,9]}});
 const duplicate=lifecycle.snapshot(),last=inspect();assert.equal(last.path,'/shape');assert.equal(last.index,9);
 assert.notEqual(lifecycle.inspectCharacterCell(1,0).path,'/shape');assert.deepEqual(lifecycle.snapshot(),duplicate);
}finally{lifecycle.close();}
const scene=await NativeScene.create(wasm),oracle=await NativeScene.create(wasm);
try{
 for(const s of [scene,oracle])s.command({op:'resize',width:8,height:3});
 const region={id:'timed',path:'/app/timed',state:'selected',cells:[0],indices:[7]};
 const rule={id:'timed',selector:{path:'/app/timed',indices:[7]},states:{selected:{foregroundEffects:[{type:'invert'}]}}};
 scene.command({op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[
  {op:'character-region',region},{op:'character-rule',rule}]}});
 scene.command({op:'schedule',id:2,atUs:1000000,command:{op:'character-region',region:{...region,cells:[1]}}});
 scene.command({op:'schedule',id:3,atUs:1500000,command:{op:'batch',commands:[
  {op:'remove-character-rule',id:'timed'},{op:'remove-character-region',id:'timed'}]}});
 const start=scene.snapshot(),samples=[];
 for(const time of [0,499999,500000,999999,1000000,1499999,1500000,2000000]){
  scene.advanceTo(time);oracle.advanceTo(time);
  const expected=new Uint32Array(oracle.render().cells);
  if(time>=500000&&time<1500000)expected[(time<1000000?0:1)*4+1]^=0xffffff;
  const source=scene.snapshot();assert.deepEqual(scene.render().cells,expected,`timeline at ${time}`);
  if(time>=500000&&time<1500000){
   const cell=scene.inspectCharacterCell(time<1000000?0:1,0);
   assert.equal(cell.path,'/app/timed');assert.equal(cell.state,'selected');assert.equal(cell.index,7);
  }
  assert.deepEqual(scene.snapshot(),source,'render and inspection must preserve source');
  samples.push({time,source,expected});
 }
 assert.deepEqual(scene.info().characterRules,[]);assert.deepEqual(scene.info().characterRegions,[]);
 scene.restore(start);
 for(const sample of samples){scene.advanceTo(sample.time);assert.deepEqual(scene.snapshot(),sample.source);assert.deepEqual(scene.render().cells,sample.expected);}
 const final=scene.snapshot();scene.restore(start);scene.advanceTo(2000000);
 assert.deepEqual(scene.snapshot(),final,'one advance and partitioned advances must agree');
 console.log(JSON.stringify({runtime:'actual WASM',independentTimedFrames:samples.length,scheduledBatchCreation:true,regionReplacement:true,scheduledTeardown:true,inspectionPure:true,exactReplay:true}));
}finally{scene.close();oracle.close();}
