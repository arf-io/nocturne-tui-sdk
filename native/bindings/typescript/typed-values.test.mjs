import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const bytes=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const shapes=await NativeScene.create(bytes,42);
try{
 shapes.command({op:'define',path:'/alpha',value:.5,binding:{family:'material',field:'alpha'}});
 const before=shapes.snapshot();
 for(const binding of [{id:0,field:'alpha'},{family:null,field:'alpha'},{family:1,field:'alpha'},{family:'material'},{family:'material',field:null}]){
  assert.throws(()=>shapes.command({op:'define',path:'/bad',value:.5,binding}));assert.deepEqual(shapes.snapshot(),before);
  assert.throws(()=>shapes.command({op:'bind',path:'/alpha',binding}));assert.deepEqual(shapes.snapshot(),before);
 }
}finally{shapes.close();}
const preferences=await NativeScene.create(bytes,42),publicPreferences=await NativeScene.create(bytes,42);
try{
 for(const field of ['reducedMotion','screenReader'])preferences.command({op:'define',path:`/${field}`,value:false,binding:{family:'accessibility',id:0,field}});
 for(const enabled of [true,false]){
  preferences.command({op:'batch',commands:['reducedMotion','screenReader'].map(field=>({op:'set',path:`/${field}`,value:enabled}))});
  publicPreferences.command({op:'accessibility',reducedMotion:enabled,screenReader:enabled});
  assert.deepEqual(preferences.info().accessibility,publicPreferences.info().accessibility);
  assert.deepEqual(preferences.render().bytes,publicPreferences.render().bytes);
  const saved=preferences.snapshot();preferences.restore(saved);assert.deepEqual(preferences.snapshot(),saved);
  for(const field of ['reducedMotion','screenReader'])assert.deepEqual(preferences.info().valueDescriptors[`/${field}`].binding,{family:'accessibility',id:0,field});
 }
 const before=preferences.snapshot();
 for(const binding of [{family:'accessibility',id:1,field:'reducedMotion'},{family:'accessibility',id:0,field:'unknown'}]){
  assert.throws(()=>preferences.command({op:'define',path:'/bad',value:true,binding}));assert.deepEqual(preferences.snapshot(),before);
 }
 preferences.command({op:'define',path:'/preference',value:true,binding:{family:'accessibility',field:'reducedMotion'}});
 preferences.command({op:'bind',path:'/preference',binding:{family:'accessibility',field:'screenReader'}});
 assert.deepEqual(preferences.info().accessibility,{reducedMotion:true,screenReader:true});
 preferences.command({op:'set',path:'/preference',value:false});
 assert.deepEqual(preferences.info().accessibility,{reducedMotion:true,screenReader:false});
 preferences.command({op:'bind',path:'/preference',binding:null});preferences.command({op:'set',path:'/preference',value:true});
 assert.equal(preferences.info().accessibility.screenReader,false);assert.equal(preferences.info().valueDescriptors['/preference'].binding,null);
 preferences.command({op:'define',path:'/numeric',value:0,binding:{family:'accessibility',field:'screenReader'}});
 preferences.command({op:'set',path:'/numeric',value:1});const numeric=preferences.snapshot();
 for(const value of [-1,.5,2]){assert.throws(()=>preferences.command({op:'set',path:'/numeric',value}));assert.deepEqual(preferences.snapshot(),numeric);}
}finally{preferences.close();publicPreferences.close();}
const hostWeather=await NativeScene.create(bytes,42);
try{
 hostWeather.command({op:'emitter',id:1,effect:'weather/autumn-drift',collision:true,deposit:false});
 hostWeather.command({op:'define',path:'/collision',value:true,binding:{family:'emitter',id:1,field:'collision'}});
 hostWeather.command({op:'trigger',id:1,target:'/collision',event:'/host/weather',whenExpression:true,expression:{intentPath:'/collision'}});
 hostWeather.command({op:'emit-intent',event:'/host/weather',payload:{collision:false}});
 assert.equal(hostWeather.info().values['/collision'],false);assert.deepEqual(hostWeather.info().intents[0].payload,{collision:false});
 const before=hostWeather.snapshot();assert.throws(()=>hostWeather.command({op:'emit-intent',event:'/host/weather',payload:{collision:0}}));
 assert.deepEqual(hostWeather.snapshot(),before);
}finally{hostWeather.close();}
const boundEmitter=await NativeScene.create(bytes,42),authoredEmitter=await NativeScene.create(bytes,42);
try{
 const base={op:'emitter',id:1,effect:'weather/autumn-drift',count:8,runningTimeMs:100,
  position:[0,1,0],extent:[0,0,0],velocity:[0,-2,0],spread:[0,0,0],gravity:[0,-4,0],collision:true,deposit:true};
 for(const scene of [boundEmitter,authoredEmitter])scene.command({op:'floor',height:0,enabled:true,visible:true});
 boundEmitter.command(base);authoredEmitter.command({...base,collision:false,deposit:false});
 for(const field of ['deposit','collision'])boundEmitter.command({op:'define',path:`/${field}`,value:false,binding:{family:'emitter',id:1,field}});
 for(const time of [0,250000,1000000]){
  boundEmitter.advanceTo(time);authoredEmitter.advanceTo(time);
  assert.deepEqual(boundEmitter.render().bytes,authoredEmitter.render().bytes);
  assert.deepEqual(boundEmitter.particles(),authoredEmitter.particles());
  assert.deepEqual(boundEmitter.info().deposits,authoredEmitter.info().deposits);
 }
}finally{boundEmitter.close();authoredEmitter.close();}
const emitter=await NativeScene.create(bytes,42);
try{
 emitter.command({op:'emitter',id:1,effect:'weather/autumn-drift',count:3,collision:true,deposit:true});
 for(const field of ['deposit','collision'])emitter.command({op:'define',path:`/${field}`,value:true,binding:{family:'emitter',id:1,field}});
 const before=emitter.snapshot();assert.throws(()=>emitter.command({op:'set',path:'/collision',value:false}));assert.deepEqual(emitter.snapshot(),before);
 emitter.command({op:'set',path:'/deposit',value:false});emitter.command({op:'set',path:'/collision',value:false});
 assert.equal(emitter.info().values['/collision'],false);assert.equal(emitter.info().values['/deposit'],false);
 const disabled=emitter.snapshot();assert.throws(()=>emitter.command({op:'set',path:'/deposit',value:true}));assert.deepEqual(emitter.snapshot(),disabled);
 emitter.command({op:'set',path:'/collision',value:true});emitter.command({op:'set',path:'/deposit',value:true});
 const saved=emitter.snapshot();emitter.render();assert.deepEqual(emitter.snapshot(),saved);emitter.restore(saved);assert.deepEqual(emitter.snapshot(),saved);
}finally{emitter.close();}
const s=await NativeScene.create(bytes,42);
try{
 for(const [path,value] of [['/ready',true],['/name','NOC 日本'],['/task',{id:'noc-1',items:[1,null,false]}],['/nil',null]])s.command({op:'define',path,value});
 s.command({op:'define',path:'/json',type:'json',value:7});s.command({op:'set',path:'/json',value:[1,true]});
 s.command({op:'set',path:'/task',expression:{path:'/json'}});assert.deepEqual(s.info().values['/task'],[1,true]);assert.equal(s.info().valueTypes['/json'],'json');
 s.command({op:'define',path:'/out',value:0});s.command({op:'define',path:'/locked',value:'locked',readonly:true});
 for(const command of [
  {op:'set',path:'/ready',value:1},{op:'set',path:'/locked',value:'changed'},
  {op:'set',path:'/out',expression:{path:'/ready'}},{op:'trigger',id:1,source:'/ready',target:'/out'},
  {op:'trigger',id:1,source:'/out',target:'/ready'},
 ]){const before=s.snapshot();assert.throws(()=>s.command(command));assert.deepEqual(s.snapshot(),before);}
 s.command({op:'emit-intent',event:'/host/task',payload:{task:{id:'noc-1',ready:false,items:[1,2]}}});
 for(const [path,intentPath,expected] of [['/task','/task',{id:'noc-1',ready:false,items:[1,2]}],['/name','/task/id','noc-1'],['/ready','/task/ready',false]]){
  s.command({op:'set',path,intentId:1,expression:{intentPath}});assert.deepEqual(s.info().values[path],expected);
 }
 s.command({op:'set',path:'/task',expression:{literal:{b:2,a:[true,null,'日']}}});assert.deepEqual(s.info().values['/task'],{b:2,a:[true,null,'日']});
 s.command({op:'define',path:'/copy',value:''});
 s.command({op:'schedule',id:1,atUs:500000,command:{op:'set',path:'/copy',expression:{path:'/name'}}});
 const start=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/name'}));assert.deepEqual(s.snapshot(),start);
 s.advanceTo(500000);assert.equal(s.info().values['/copy'],'noc-1');const finish=s.snapshot();
 s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 s.command({op:'ack-intent',id:1});const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/name',intentId:1,expression:{intentPath:'/task/id'}}));assert.deepEqual(s.snapshot(),before);
 for(const [family,field,initial,value,base] of [
  ['widget','enabled',true,false,{op:'widget',id:1,kind:'button',text:'Inspect'}],
  ['widget','text','Inspect','NOC 日本',{op:'widget',id:1,kind:'button',text:'Inspect'}],
  ['node','label','old','new 日本',{op:'node',id:1,label:'old'}],
  ['node','status','queued','done',{op:'node',id:1,label:'task',status:'queued'}],
  ['text','text','old','new 日本',{op:'text',id:1,text:'old'}],
 ]){
  const actual=await NativeScene.create(bytes,42),oracle=await NativeScene.create(bytes,42);
  try{
   for(const scene of [actual,oracle]){scene.command(base);scene.advanceTo(250000);}
   actual.command({op:'define',path:'/x',value:initial,binding:{family,id:1,field}});
   actual.command({op:'set',path:'/x',value});actual.command({op:'remove-value',path:'/x'});
   oracle.command({op:family,id:1,[field]:initial});oracle.command({op:family,id:1,[field]:value});
   assert.deepEqual(actual.snapshot(),oracle.snapshot());assert.deepEqual(actual.render().cells,oracle.render().cells);
  }finally{actual.close();oracle.close();}
 }
 console.log(JSON.stringify({runtime:'actual WASM',typedStorage:true,strictTypes:true,payloadSubtrees:true,publicBindingOracles:5,scheduledOwnership:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
