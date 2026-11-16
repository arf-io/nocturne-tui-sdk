import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 for(const id of [1,2])s.command({op:'widget',id,kind:'progress',text:'original'});
 s.command({op:'define',path:'/number',value:7});
 s.command({op:'define',path:'/ready',value:true,readonly:true});
 s.command({op:'define',path:'/title',value:'Title',binding:{family:'widget',id:1,field:'text'}});
 s.command({op:'define',path:'/task',type:'json',value:{done:false}});
 const saved=s.snapshot(), descriptors=s.info().valueDescriptors;
 assert.deepEqual(descriptors['/number'],{type:'number',readonly:false,binding:null});
 assert.deepEqual(descriptors['/ready'],{type:'boolean',readonly:true,binding:null});
 assert.deepEqual(descriptors['/title'],{type:'string',readonly:false,binding:{family:'widget',id:1,field:'text'}});
 assert.equal(descriptors['/task'].type,'json');
 s.render();assert.deepEqual(s.snapshot(),saved);
 s.command({op:'bind',path:'/title',binding:{family:'widget',id:2,field:'text'}});
 assert.equal(s.info().valueDescriptors['/title'].binding.id,2);
 s.command({op:'bind',path:'/title',binding:null});
 assert.equal(s.info().valueDescriptors['/title'].binding,null);
 s.command({op:'remove-value',path:'/title'});
 assert.equal(Object.hasOwn(s.info().valueDescriptors,'/title'),false);
 s.restore(saved);assert.deepEqual(s.info().valueDescriptors,descriptors);
 assert.deepEqual(s.snapshot(),saved);
 console.log(JSON.stringify({runtime:'actual WASM',types:true,readonly:true,bindingOwnership:true,detach:true,removal:true,renderPure:true,restore:true}));
}finally{s.close();}
