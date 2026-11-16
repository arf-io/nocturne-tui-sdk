import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const operators={lessThan:(a,b)=>a<b,lessOrEqual:(a,b)=>a<=b,greaterThan:(a,b)=>a>b,greaterOrEqual:(a,b)=>a>=b};
const s=await NativeScene.create(wasm);
try{
 s.command({op:'define',path:'/truth',value:false});
 for(const [operator,oracle] of Object.entries(operators)){
  for(const [left,right] of [[1,2],[2,2],[3,2],[-1,0],[.1,.2]]){
   s.command({op:'set',path:'/truth',expression:{[operator]:[left,right]}});assert.equal(s.info().values['/truth'],oracle(left,right));
  }
  for(const operand of [true,null,'2',{literal:[]},{literal:{}}]){
   const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/truth',expression:{[operator]:[operand,2]}}));assert.deepEqual(s.snapshot(),before);
  }
 }
 s.command({op:'define',path:'/out',value:0});s.command({op:'define',path:'/threshold',value:3});
 s.command({op:'trigger',id:1,target:'/out',event:'/host/metric',debounceMs:500,whenExpression:{greaterOrEqual:[{intentPath:'/metric'},{path:'/threshold'}]},value:7});
 s.command({op:'emit-intent',event:'/host/metric',payload:{metric:4}});
 const start=s.snapshot();s.advanceTo(500000);assert.equal(s.info().values['/out'],7);assert.equal(s.info().intents.length,1);
 const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(start);s.advanceTo(500000);assert.deepEqual(s.snapshot(),finish);
 console.log(JSON.stringify({runtime:'actual WASM',orderedPredicates:4,boundaries:true,strictNumericTypes:true,retainedPayloadGuard:true,purity:true,replay:true}));
}finally{s.close();}
