import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),42);
try{
 for(const [path,value] of [['/task',{title:'NOC 日本',done:3,total:4,items:[true,null],'a/b':7}],['/title',''],['/number',0],['/items',[]]])s.command({op:'define',path,value});
 for(const [path,pointer,expected] of [['/title','/title','NOC 日本'],['/number','/a~1b',7],['/items','/items',[true,null]]]){s.command({op:'set',path,expression:{path:'/task',pointer}});assert.deepEqual(s.info().values[path],expected);}
 s.command({op:'set',path:'/number',expression:{divide:[{path:'/task',pointer:'/done'},{path:'/task',pointer:'/total'}]}});assert.equal(s.info().values['/number'],.75);
 for(const pointer of ['/missing','relative','/items/01']){const before=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/title',expression:{path:'/task',pointer}}));assert.deepEqual(s.snapshot(),before);}
 s.command({op:'define',path:'/go',value:0});
 s.command({op:'trigger',id:1,source:'/go',target:'/task',expression:{literal:{title:'after'}}});
 s.command({op:'trigger',id:2,source:'/go',target:'/title',expression:{path:'/task',pointer:'/title'}});
 const before=s.snapshot();assert.throws(()=>s.command({op:'remove-value',path:'/task'}));assert.deepEqual(s.snapshot(),before);
 s.command({op:'set',path:'/go',value:1});assert.equal(s.info().values['/title'],'NOC 日本');
 const finish=s.snapshot();s.render();assert.deepEqual(s.snapshot(),finish);s.restore(finish);assert.deepEqual(s.snapshot(),finish);
 console.log(JSON.stringify({runtime:'actual WASM',valueSubtrees:true,numericComposition:true,strictPointers:true,prewriteEpoch:true,lifetimeProtection:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
